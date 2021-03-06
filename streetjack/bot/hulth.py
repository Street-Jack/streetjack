#!/usr/bin/env python3

import random
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict

from treys import Deck

from streetjack.bot.evaluator import Evaluator


MAX_BUCKETS = 8
START_MONEY = 140
SMALL_BLIND_BET = 10
BIG_BLIND_BET = 20
RAISE_AMOUNT = BIG_BLIND_BET
CHANCE_NODE_ENCODING = "."
MAX_RAISES_PER_STAGE = 2

SMALL_BLIND = 0
BIG_BLIND = 1


class InfoSetError(Exception):
    pass


class Action(Enum):
    RAISE = "r"
    CALL = "c"
    FOLD = "f"
    CHANCE = ":"


ACTION_NAMES = {
    Action.RAISE: "raise",
    Action.CALL: "call/check",
    Action.FOLD: "fold",
    Action.CHANCE: "chance",
}


class Stage(Enum):
    PREFLOP = 0
    FLOP = 1
    TURN = 2
    RIVER = 3
    SHOWDOWN = 4


BOARD_CARDS = {
    Stage.PREFLOP: 0,
    Stage.FLOP: 3,
    Stage.TURN: 4,
    Stage.RIVER: 5,
    Stage.SHOWDOWN: 5,
}


class CardBundle:
    def __init__(self, deck: Deck, evaluator: Evaluator):
        self._deck = deck

        self._hands = [deck.draw(2), deck.draw(2)]
        self._board = deck.draw(5)

        self._hand_bucket_indices = []

        for i in range(len(self._hands)):
            bucket_indices = dict()

            for key in BOARD_CARDS:
                if key == Stage.SHOWDOWN:
                    bucket_indices[key] = bucket_indices[Stage.RIVER]
                    continue

                stage_board = self.board(stage=key)
                bucket_indices[key] = evaluator.effective_rank(self._hands[i], stage_board, MAX_BUCKETS)

            self._hand_bucket_indices.append(bucket_indices)

        self._hand_ranks = [
            evaluator.rank(self._hands[SMALL_BLIND], self._board),
            evaluator.rank(self._hands[BIG_BLIND], self._board),
        ]

    def player_hand(self, player_index: int) -> List[int]:
        return self._hands[player_index]

    def board(self, stage: Stage) -> List[int]:
        num_cards = BOARD_CARDS[stage]
        return self._board[:num_cards]

    def bucket_index(self, player_index: int, stage: Stage) -> int:
        return self._hand_bucket_indices[player_index][stage]

    def winner_index(self) -> int:
        if self._hand_ranks[SMALL_BLIND] < self._hand_ranks[BIG_BLIND]:
            return SMALL_BLIND

        return BIG_BLIND


class FakeCardBundle(CardBundle):
    def __init__(self, deck: Deck, evaluator: Evaluator):
        self._deck = deck

        self._hands = [deck.draw(2), deck.draw(2)]
        self._board = deck.draw(5)

        self._hand_bucket_indices = []

        for _ in range(len([SMALL_BLIND, BIG_BLIND])):
            bucket_indices = dict()

            bucket_indices[Stage.PREFLOP] = random.randint(0, MAX_BUCKETS - 1)
            prev_stage = Stage.PREFLOP

            # Apply deviance with normal distribution.
            for key in [Stage.FLOP, Stage.TURN, Stage.RIVER]:
                deviance = FakeCardBundle.rand_deviance()
                bucket_indices[key] = min(max(bucket_indices[prev_stage] + deviance, 0), MAX_BUCKETS - 1)

            bucket_indices[Stage.SHOWDOWN] = bucket_indices[Stage.RIVER]

            self._hand_bucket_indices.append(bucket_indices)

        small_blind_final_bucket = self.bucket_index(SMALL_BLIND, Stage.SHOWDOWN)
        big_blind_final_bucket = self.bucket_index(BIG_BLIND, Stage.SHOWDOWN)

        self._hand_ranks = [0, 0]
        winner = random.randrange(2)

        if small_blind_final_bucket > big_blind_final_bucket:
            winner = SMALL_BLIND

        if small_blind_final_bucket < big_blind_final_bucket:
            winner = BIG_BLIND

        self._hand_ranks[winner] += 1

    @staticmethod
    def rand_deviance():
        # -1: 1/7, 0: 3/7, 1: 2/7, 2: 1/7
        upper_bound = 6
        lower_bound = 0
        uniform_deviance = random.randint(lower_bound, upper_bound)

        if uniform_deviance == 0:
            return -1

        if 1 <= uniform_deviance <= 3:
            return 0

        if 4 <= uniform_deviance <= 5:
            return 1

        return 2


class InfoSet(ABC):
    def __init__(self, history: List[Action], bundle: CardBundle):
        self._history = history
        self._bundle = bundle

        self._parse_stage_history()
        self._player = self._parse_player_index()

    def history(self) -> List[Action]:
        return self._history

    @abstractmethod
    def play(self, action: Action) -> "InfoSet":
        raise NotImplementedError("play method not implemented")

    @abstractmethod
    def actions(self) -> List[Action]:
        raise NotImplementedError("actions method not implemented")

    @abstractmethod
    def encoding(self) -> str:
        raise NotImplementedError("encoding method not implemented")

    @abstractmethod
    def is_terminal(self) -> bool:
        raise NotImplementedError("is_terminal method not implemented")

    @abstractmethod
    def is_chance(self) -> bool:
        raise NotImplementedError("is_chance method not implemented")

    @abstractmethod
    def utility(self, player: int) -> int:
        raise NotImplementedError("play method not implemented")

    @abstractmethod
    def winner(self) -> int:
        raise NotImplementedError("winner method not implemented")

    def curr_player(self) -> int:
        return self._player

    def stage(self) -> Stage:
        return self._stage

    def available_money(self) -> int:
        return START_MONEY - self._player_bet(self._player)

    def available_money_of_players(self) -> List[int]:
        player_bets = self._player_bets()
        available_money = [START_MONEY, START_MONEY]

        for player in [SMALL_BLIND, BIG_BLIND]:
            available_money[player] -= player_bets[player]

        return available_money

    def pot_money(self) -> int:
        player_bets = self._player_bets()
        return player_bets[SMALL_BLIND] + player_bets[BIG_BLIND]

    def last_opponent_action(self) -> int:
        if len(self._history) > 0:
            return self._history[-1]

        raise InfoSetError("Tried to access history of first state")

    def _parse_stage_history(self) -> None:
        self._stage = self._parse_stage()

        last_stage_index = 0

        for i in range(len(self._history)):
            if self._history[i] == Action.CHANCE:
                last_stage_index = i

        self._stage_history = self._history[last_stage_index:]

    def _parse_stage(self) -> Stage:
        subgame_stage = 0
        min_stage_len = 2

        for i in range(min_stage_len, len(self._history)):
            if _players_called(self._history[: i + 1]):
                subgame_stage += 1

        for stage in Stage:
            if subgame_stage == stage.value:
                return stage

        raise InfoSetError("Invalid stage encountered")

    def _parse_player_index(self) -> int:
        return (1 + len(self._stage_history)) % 2

    def _could_raise(self) -> bool:
        if self.available_money() < RAISE_AMOUNT:
            return False

        raises = 0

        for action in self._stage_history:
            if action == Action.RAISE:
                raises += 1

        if raises >= MAX_RAISES_PER_STAGE:
            return False

        return True

    def _player_bet(self, player: int) -> int:
        player_bets = self._player_bets()
        return player_bets[player]

    def _player_bets(self) -> List[int]:
        player_bets = [SMALL_BLIND_BET, BIG_BLIND_BET]
        curr_player = SMALL_BLIND

        # base cases
        # --> c [SMALL_BLIND_BET, BIG_BLIND_BET]
        #: --> 0 [SMALL_BLIND_BET, BIG_BLIND_BET]
        #:r --> 1 [BIG_BLIND_BET+RAISE_AMOUNT, BIG_BLIND_BET]
        #:rf --> 0 [BIG_BLIND_BET+RAISE_AMOUNT, BIG_BLIND_BET] => player 0 profit is BIG_BLIND_BET

        #:rc --> 0 [BIG_BLIND_BET+RAISE_AMOUNT, BIG_BLIND_BET+RAISE_AMOUNT]
        #:rcc --> c [BIG_BLIND_BET+RAISE_AMOUNT, BIG_BLIND_BET+RAISE_AMOUNT]
        #:rcc: --> 0 [BIG_BLIND_BET+RAISE_AMOUNT, BIG_BLIND_BET+RAISE_AMOUNT]
        #:rcc:r -> 1 [BIG_BLIND_BET+2*RAISE_AMOUNT, BIG_BLIND_BET+RAISE_AMOUNT]

        for i in range(len(self._history)):
            if self._history[i] == Action.CHANCE:
                curr_player = SMALL_BLIND
                continue

            opponent = get_opponent(curr_player)

            if self._history[i] == Action.RAISE:
                player_bets[curr_player] = player_bets[opponent] + RAISE_AMOUNT
            elif self._history[i] == Action.CALL:
                player_bets[curr_player] = player_bets[opponent]

            curr_player = opponent

        return player_bets


class ChanceInfoSet(InfoSet):
    def __init__(self, history: List[Action], bundle: CardBundle):
        super().__init__(history, bundle)

        self._validate_history()

        self._children = []

    def play(self, action: Action) -> InfoSet:
        if self._children == []:
            self._children = self._generate_children(self._bundle)

        if not action in self._children:
            raise InfoSetError("action not possible")

        return self._children[action]

    def actions(self) -> List[Action]:
        if self.is_terminal():
            return []

        return [Action.CHANCE]

    def encoding(self) -> str:
        return CHANCE_NODE_ENCODING

    def is_terminal(self) -> bool:
        return self._stage == Stage.SHOWDOWN

    def is_chance(self) -> bool:
        return True

    def utility(self, player: int) -> int:
        winner = self.winner()
        loser = get_opponent(winner)

        if player == loser:
            return -self._player_bet(loser)

        return self._player_bet(loser)

    def winner(self) -> int:
        if not self.is_terminal():
            raise InfoSetError("utility cannot be provided by non terminal info set")

        return self._bundle.winner_index()

    def _validate_history(self) -> None:
        if len(self._history) == 0:
            return

        # min is :cc
        if len(self._history) > 2 and self._history[-1] == Action.CALL and self._history[-2] == Action.CALL:
            return

        raise InfoSetError("invalid chance info set history: invalid action {}".format(self._history[-1].value))

    def _generate_children(self, bundle: CardBundle) -> List[InfoSet]:
        actions = self.actions()
        children = dict()

        for action in actions:
            child_history = self._history.copy()
            child_history.append(action)

            children[action] = MoveInfoSet(child_history, bundle)

        return children


class MoveInfoSet(InfoSet):
    def __init__(
        self,
        history: List[Action],
        bundle: CardBundle,
    ):
        super().__init__(history, bundle)

        self._validate_history()

        self._bucket_index = bundle.bucket_index(self._player, self._stage)
        self._children = []

    def play(self, action: Action) -> InfoSet:
        if self._children == []:
            self._children = self._generate_children(self._bundle)

        if not action in self._children:
            raise InfoSetError("action not possible")

        return self._children[action]

    def is_terminal(self) -> bool:
        return len(self._history) >= 1 and self._history[-1] == Action.FOLD

    def encoding(self) -> str:
        actions_prefix = "".join(action.value for action in self._history)
        return actions_prefix + ".{}".format(self._bucket_index)

    def actions(self) -> List[Action]:
        if self.is_terminal():
            return []

        actions = []

        if self._could_raise():
            actions.append(Action.RAISE)

        actions.append(Action.CALL)

        if len(self._history) == 0:
            return actions

        actions.append(Action.FOLD)

        return actions

    def utility(self, player: int) -> int:
        winner = self.winner()

        sign = 1

        if winner != player:
            sign = -sign

        opponent = get_opponent(winner)

        return sign * self._player_bet(opponent)

    def winner(self) -> int:
        if not self.is_terminal():
            raise InfoSetError("utility cannot be provided by non terminal info set")

        return self._player

    def is_chance(self) -> bool:
        return False

    def _validate_history(self):
        if len(self._history) == 0:
            raise InfoSetError("Empty history for Move Info Set not allowed")

        if _players_called(self._history):
            raise InfoSetError("invalid move info set history: invalid action {}".format(self._history[-1].value))

    def _generate_children(self, bundle: CardBundle) -> Dict:
        actions = self.actions()
        children = dict()

        for action in actions:
            child_history = self._history.copy()
            child_history.append(action)

            child = None

            if _players_called(child_history):
                child = ChanceInfoSet(child_history, bundle)
            else:
                child = MoveInfoSet(child_history, bundle)

            children[action] = child

        return children


def create_game_root(bundle: CardBundle):
    return ChanceInfoSet(history=[], bundle=bundle)


def get_opponent(player: int) -> int:
    return 1 - player


def _players_called(history: List[Action]) -> bool:
    if len(history) < 2:
        return False

    return history[-1] == Action.CALL and history[-2] == Action.CALL
