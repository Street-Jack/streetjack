#!/usr/bin/env python3

from abc import ABC
from enum import Enum
from typing import List

from streetjack.evaluator import Evaluator


MAX_BUCKETS = 10


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


class GameState(ABC):
    def __init__(self, parent: 'GameState', history: List[Action]):
        self._parent = parent
        self._history = history

    def encoding(_) -> str:
        raise NotImplementedError("encoding method not implemented")
    
    def is_terminal(_) -> bool:
        raise NotImplementedError("is_terminal method not implemented")

    def is_chance(self) -> bool:
        return len(self._history >= 1) and self._history[-1] == Action.CHANCE


class ChanceGameState(GameState):
    def __init__(self, parent: GameState, history: List[Action]):
        super().__init__(parent, history)
    
    def is_terminal(_) -> bool:
        return False


class MoveGameState(GameState):
    def __init__(
        self,
        parent: GameState,
        history: List[Action],
        evaluator: Evaluator,
        hand: List[int],
        board: List[int]
    ):
        super().__init__(parent, history)

        self._stage = self._parse_stage()
        self._bucket_index = evaluator.effective_rank(hand,board,MAX_BUCKETS)

    # move to abstract class.
    def is_terminal(self) -> bool:
        if self._is_final_stage() and self._players_called():
            return True
        
        if len(self._history) >= 1 and self._history[-1] == Action.FOLD:
            return True

        return False
    
    def encoding(self) -> str:
        actions_prefix = ''.join(action.value for action in self._history) 
        return actions_prefix + '.{}'.format(self._bucket_index)

    def _parse_stage(self) -> Stage:
        chance_nodes = list(filter((lambda action: action == Action.CHANCE), self._history))

        for stage in Stage:
            if len(chance_nodes) == stage.value + 1:
                return stage
    
        raise GameStateError("Invalid stage encountered")

    def _is_final_stage(self) -> bool:
        return self._stage == Stage.SHOWDOWN

    def _players_called(self) -> bool:
        return len(self._history) >= 2 and self._history[-1] == Action.CALL and self._history[-2] == Action.CALL
