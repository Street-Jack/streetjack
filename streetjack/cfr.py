#!/usr/bin/env python3

from abc import ABC
from enum import Enum
from typing import List, Dict

from treys import Deck

from streetjack.evaluator import Evaluator


MAX_BUCKETS = 10
START_MONEY = 80
SMALL_BLIND_BET = 10
BIG_BLIND_BET = 20
RAISE_AMOUNT = BIG_BLIND_BET
CHANCE_NODE_ENCODING = '.'


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

            for k, v in BOARD_CARDS:
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
    def __init__(self, parent: 'InfoSet', history: List[Action], bundle: CardBundle):
        self._parent = parent
        self._history = history
        self._bundle = bundle

        # TODO: Could be computed by the chance node.
        self._stage = self._parse_stage()
        self._stage_history = self._parse_stage_history()
    
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

    def _could_raise(self) -> bool:
        if self._available_money() < RAISE_AMOUNT:
            return False

        if Action.RAISE in self._stage_history:
            return False

        return True
    
    def _available_money(self) -> int:
        min_player_bet = BIG_BLIND_BET

        for i in range(len(self._history)):
            # We assume that if the first action is a raise then the raise pays the call as well.
            if self._history[i] == Action.RAISE:
                min_player_bet += RAISE_AMOUNT
        
        return START_MONEY - min_player_bet


class ChanceInfoSet(InfoSet):
    def __init__(self, parent: 'MoveInfoSet', history: List[Action], bundle: CardBundle):
        super().__init__(parent, history, bundle)

        self._children = self._generate_children(bundle)

    def play(self, action: Action) -> 'InfoSet':
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

        opp_index = self._parent.opponent_index()

        for action in actions:
            child_history = self._history.copy()
            child_history.append(action)

            children[action] = MoveInfoSet(self, child_history, opp_index, bundle)

        return children


class MoveInfoSet(InfoSet):
    def __init__(
        self,
        parent: InfoSet,
        history: List[Action],
        player_index: int,
        bundle: CardBundle,
    ):
        super().__init__(parent, history, bundle)

        self._player_index = player_index
        self._bucket_index = bundle.bucket_index(player_index, self._stage)

        self._children = self._generate_children(bundle)
    
    def play(self, action: Action) -> 'InfoSet':
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

    def opponent_index(self) -> int:
        return 1 - self._player_index

    def _generate_children(self, bundle: CardBundle) -> Dict:
        actions = self.actions()
        children = dict()

        opp_index = self.opponent_index()

        for action in actions:
            child_history = self._history.copy()
            child_history.append(action)

            if action == Action.CHANCE:
                child = ChanceInfoSet(self, child_history, bundle)
                continue

            child = MoveInfoSet(self, child_history, opp_index, opp_index, bundle)
            children[action] = child

        return children

    def _is_final_stage(self) -> bool:
        return self._stage == Stage.RIVER

    def _players_called(self) -> bool:
        return len(self._history) >= 2 and self._history[-1] == Action.CALL and self._history[-2] == Action.CALL
