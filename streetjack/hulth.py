#!/usr/bin/env python3

from abc import ABC
from enum import Enum
from typing import List, Dict, Tuple

from treys import Deck

from streetjack.evaluator import Evaluator


MAX_BUCKETS = 10
START_MONEY = 80
SMALL_BLIND_BET = 10
BIG_BLIND_BET = 20
RAISE_AMOUNT = BIG_BLIND_BET
CHANCE_NODE_ENCODING = '.'

SMALL_BLIND = 0
BIG_BLIND = 1


class GameStateError(Exception):
    pass


class Action(Enum):
    RAISE = 'r'
    CALL = 'c'
    FOLD = 'f'
    CHANCE = ':'


class Stage(Enum):
    PREFLOP = 0
    FLOP = 1
    TURN = 2
    RIVER = 3
    SHOWDOWN = 4


BOARD_CARDS = {
    Stage.PREFLOP: 0, # TODO: Improve.
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

            for k, v in BOARD_CARDS.items():
                if v == 0:
                    bucket_indices[k] = evaluator.effective_hand_rank(self._hands[i], MAX_BUCKETS)
                else:
                    bucket_indices[k] = evaluator.effective_rank(self._hands[i], self._board[:v], MAX_BUCKETS)
            
            self._hand_bucket_indices.append(bucket_indices)
        
        self._hand_strengths = [
            evaluator.effective_hand_strength(self._hands[0], self._board),
            evaluator.effective_hand_strength(self._hands[1], self._board),
        ]
    
    def player_hand(self, player_index: int) -> List[int]:
        return self._hands[player_index]
    
    def board(self) -> List[int]:
        return self._board
    
    def bucket_index(self, player_index: int, stage: Stage) -> int:
        return self._hand_bucket_indices[player_index][stage]
    
    def winner_index(self) -> int:
        if self._hand_strengths[0] > self._hand_strengths[1]:
            return 0

        return 1


class InfoSet(ABC):
    def __init__(self, history: List[Action], bundle: CardBundle):
        self._history = history
        self._bundle = bundle

        # TODO: Could be computed by the chance node.
        self._stage = self._parse_stage()
        self._stage_history = self._parse_stage_history()
        self._player = self._parse_player_index()
    
    def play(self, action: Action) -> 'InfoSet':
        raise NotImplementedError("play method not implemented")

    def actions(_) -> List[Action]:
        raise NotImplementedError("actions method not implemented")

    def encoding(_) -> str:
        raise NotImplementedError("encoding method not implemented")
    
    def is_terminal(_) -> bool:
        raise NotImplementedError("is_terminal method not implemented")

    def is_chance(self) -> bool:
        return len(self._history >= 1) and self._history[-1] == Action.CHANCE
    
    def _parse_stage(self) -> Stage:
        chance_nodes = list(filter((lambda action: action == Action.CHANCE), self._history))

        for stage in Stage:
            if len(chance_nodes) == stage.value + 1:
                return stage
    
        raise GameStateError('Invalid stage encountered')

    def _parse_stage_history(self) -> List[Action]:
        stage = 0

        for i in range(len(self._history)):
            if self._history[i] == Action.CHANCE:
                stage += 1
            
            if stage == self._stage.value + 1:
                # Skips the : in the beginning.
                return self._history[i+1:]
        
        raise GameStateError('Out of stages during stage history parsing')
    
    def _parse_player_index(self) -> int:
        return len(self._stage_history) % 2

    def _could_raise(self) -> bool:
        if self._available_money() < RAISE_AMOUNT:
            return False

        if Action.RAISE in self._stage_history:
            return False

        return True
 
    def _available_money(self) -> int:
        return START_MONEY - self._player_bet()
    
    def _player_bet(self) -> int:
        player_bets = [SMALL_BLIND_BET, BIG_BLIND_BET]
        curr_player = SMALL_BLIND

        # base cases
        #: --> 0 [SMALL_BLIND_BET, BIG_BLIND_BET]
        #:r --> 1 [BIG_BLIND_BET+RAISE_AMOUNT, BIG_BLIND_BET]
        #:rf --> 0 [BIG_BLIND_BET+RAISE_AMOUNT, BIG_BLIND_BET] => player 0 profit is BIG_BLIND_BET

        #:rc --> 0 [BIG_BLIND_BET+RAISE_AMOUNT, BIG_BLIND_BET+RAISE_AMOUNT]
        #:rcc: --> 0 [BIG_BLIND_BET+RAISE_AMOUNT, BIG_BLIND_BET+RAISE_AMOUNT]
        #:rcc:r -> 1 [BIG_BLIND_BET+2*RAISE_AMOUNT, BIG_BLIND_BET+RAISE_AMOUNT]

        for i in range(len(self._history)):
            if self._history[i] == Action.CHANCE:
                curr_player = SMALL_BLIND
                continue

            opponent = 1 - curr_player

            if self._history[i] == Action.RAISE:
                player_bets[curr_player] = player_bets[opponent] + RAISE_AMOUNT
            elif self._history[i] == Action.CALL:
                player_bets[curr_player] = player_bets[opponent]

            curr_player = opponent

        return player_bets[self._player]

class ChanceInfoSet(InfoSet):
    def __init__(self, history: List[Action], bundle: CardBundle):
        super().__init__(history, bundle)

        self._children = []

    def play(self, action: Action) -> InfoSet:
        if self._children == []:
            self._children = self._generate_children(bundle)

        if not action in self._children:
            raise GameStateError("action not possible")

        return self._children[action]

    def actions(self) -> List[Action]:
        actions = []

        if self._could_raise():
            actions.append(Action.RAISE)

        actions.append(Action.CALL)

        return actions
    
    def encoding(_) -> str:
        return CHANCE_NODE_ENCODING
    
    def is_terminal(_) -> bool:
        return False
    
    # TODO: Implement
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

        self._bucket_index = bundle.bucket_index(self._player, self._stage)
        self._children = []
    
    def play(self, action: Action) -> InfoSet:
        if self._children == []:
            self._children = self._generate_children(bundle)

        if not action in self._children:
            raise GameStateError("action not possible")

        return self._children[action]

    # TODO: move to abstract class ---> Probably not a good idea since it would affect performance.
    def is_terminal(self) -> bool:
        if self._is_final_stage() and self._players_called():
            return True
        
        if len(self._history) >= 1 and self._history[-1] == Action.FOLD:
            return True

        return False
    
    def encoding(self) -> str:
        actions_prefix = ''.join(action.value for action in self._history)
        return actions_prefix + '.{}'.format(self._bucket_index)
    
    def actions(self) -> List[Action]:
        if self._players_called():
            return [Action.CHANCE]

        actions = []

        if self._could_raise():
            actions.append(Action.RAISE)

        actions.append(Action.CALL)

        if len(self._history) >= 1 and self._history[-1] == Action.RAISE:
            actions.append(Action.FOLD)

        return actions

    def _generate_children(self, bundle: CardBundle) -> Dict:
        actions = self.actions()
        children = dict()

        for action in actions:
            child_history = self._history.copy()
            child_history.append(action)

            child = None

            if action == Action.CHANCE:
                child = ChanceInfoSet(child_history, bundle)
            else:
                child = MoveInfoSet(child_history, bundle)
            
            children[action] = child

        return children

    def _is_final_stage(self) -> bool:
        return self._stage == Stage.RIVER

    def _players_called(self) -> bool:
        return len(self._history) >= 2 and self._history[-1] == Action.CALL and self._history[-2] == Action.CALL


# TODO:
# - evaluation
# - improve speed of effective hand rank
# - look at some other ways for the preflop
# - unit tests
# - some refactoring

if __name__ == '__main__':
    eval = Evaluator()
    deck = Deck()

    bundle = CardBundle(deck, eval)

    #:rcc:r
    history = [Action.CHANCE, Action.RAISE]

    s = MoveInfoSet(history, bundle)

    print(s._player_bet())
