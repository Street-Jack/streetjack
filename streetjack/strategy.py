#!/usr/bin/env python3

import ast
from enum import Enum
from random import choice
from typing import List, Sequence

MAX_BUCKETS = 10
SMALL_BLIND_BET = 10
BIG_BLIND_BET = 20
RAISE_AMOUNT = BIG_BLIND_BET
START_MONEY = 80
PLAYER_COUNT = 2
DUMMY_RANK = -1

SEPARATOR = ":"
OPENER = "("
CLOSER = ")"


class Action(Enum):
    RAISE = 0
    CALL = 1
    FOLD = 2


class Stage(Enum):
    PREFLOP = 0
    FLOP = 1
    TURN = 2
    RIVER = 3
    SHOWDOWN = 4

    def succ(self) -> "Stage":
        val = self.value + 1

        if val > Stage.SHOWDOWN.value:
            raise ValueError("Enumeration ended")

        return Stage(val)


class Player(Enum):
    DEALER = 0
    REGULAR = 1


def get_action(curr_strategy) -> int:
    return choice(curr_strategy)


class InfoSet:
    def __init__(
        self,
        rank: int,
        cumulative_stategy: List[float] = None,
        cumulative_regrets: List[int] = None,
    ):
        self.rank = rank
        self.cumulative_stategy = cumulative_stategy
        if not self.cumulative_stategy:
            self.cumulative_stategy = [0, 0, 0]

        self.cumulative_regrets = cumulative_regrets
        if not self.cumulative_regrets:
            self.cumulative_regrets = [0, 0, 0]

        self.children = []

    def __repr__(self) -> str:
        return "Rank={}:CumStrat={}:CumRegr={}".format(self.rank, self.cumulative_stategy, self.cumulative_regrets)

    def append_child(self, child: "InfoSet") -> None:
        self.children.append(child)

    def calculate_strategy(self) -> List[float]:
        curr_strategy, normalizing_sum = [0, 0, 0], 0.0
        for i in range(0, len(self.cumulative_regrets) - 1):
            curr_strategy[i] = self.cumulative_regrets[i] if self.cumulative_regrets[i] > 0 else 0.0
            normalizing_sum += curr_strategy[i]

        for i in range(0, len(self.cumulative_regrets) - 1):
            if normalizing_sum > 0:
                curr_strategy[i] /= normalizing_sum
            else:
                curr_strategy[i] = 1 / len(self.cumulative_regrets)
            self.cumulative_stategy[i] += curr_strategy[i]

        return curr_strategy

    # weighted_prob - the reach probability - all other players except the current one always wanted to get to this
    # info set, while the current one was using strategy sigma - count only his contribution for the change to get to
    # this InfoSet
    def update_cumulative_sum(self, curr_strategy: List[float], contribution: float) -> None:
        for i in range(1, len(self.cumulative_stategy)):
            self.cumulative_stategy[i] += contribution * curr_strategy[i]

    def get_avg_strategy(self) -> List[float]:
        avg_strategy, normalization_sum = [0, 0, 0], 0
        for prob in self.cumulative_stategy:
            normalization_sum += prob
        for i in range(1, len(self.cumulative_stategy)):
            if avg_strategy[i] > 0:
                avg_strategy[i] /= normalization_sum
            else:
                avg_strategy[i] = 1 / normalization_sum
        return avg_strategy


def build_subgame_strategies() -> InfoSet:
    small_blind_money = START_MONEY - SMALL_BLIND_BET
    small_blind = InfoSet(DUMMY_RANK)

    big_blind_money = START_MONEY - BIG_BLIND_BET
    big_blind = InfoSet(DUMMY_RANK)

    small_blind.append_child(big_blind)

    build_child_strategies(
        big_blind,
        big_blind_money,
        small_blind_money,
        Stage.PREFLOP,
        Stage.SHOWDOWN,
        stage_history=[],
    )

    return small_blind


def build_child_strategies(
    info_set: InfoSet,
    our_money: int,
    opp_money: int,
    stage: Stage,
    final_stage: Stage,
    stage_history: List[Action],
) -> None:
    if _is_terminal(stage, final_stage, stage_history):
        return

    buckets = [info_set.rank]

    if _players_called(stage_history) or info_set.rank == DUMMY_RANK:
        stage_history = []
        stage = stage.succ()
        buckets = range(MAX_BUCKETS)

    actions = _possible_actions(our_money, stage_history)

    for action in actions:
        our_new_money = our_money

        if action == Action.CALL:
            our_new_money = opp_money
        elif action == Action.RAISE:
            our_new_money -= RAISE_AMOUNT

        opp = InfoSet(rank)  # where we are wrong - for every type of bukcet the opponent has the same info set
        info_set.append_child(opp)

        for rank in buckets:
            new_history = stage_history.copy()
            new_history.append(action)

            build_child_strategies(opp, opp_money, our_new_money, stage, final_stage, new_history)


# def get_information_set(knowledge: str) -> InfoSet:
#    return InfoSet(DUMMY_RANK)

# def cfr(cards: List[str], history: str, reach_probabilities: List[float]) -> int:

#    active_player = 1 - (len(history) % 2)
#    my_card = cards[active_player]
#    info_set = get_information_set(my_card + history)

#    strategy = info_set.get_strategy(reach_probabilities[active_player])
#    opponent = (active_player + 1) % 2
#    counterfactual_values = np.zeros(len(Actions))

#    for ix, action in enumerate(Actions):
#        action_probability = strategy[ix]

#        new_reach_probabilities = reach_probabilities.copy()
#        new_reach_probabilities[active_player] *= action_probability

#        counterfactual_values[ix] = -self.cfr(
#            cards, history + action, new_reach_probabilities, opponent)

#    node_value = counterfactual_values.dot(strategy)
#    for ix, action in enumerate(Actions):
#        counterfactual_regret[ix] = \
#            reach_probabilities[opponent] * (counterfactual_values[ix] - node_value)
#        info_set.cumulative_regrets[ix] += counterfactual_regret[ix]

#    return node_value


def marshal(node: InfoSet) -> str:
    result = OPENER
    result += str(node.rank) + SEPARATOR
    result += str(node.cumulative_stategy) + SEPARATOR
    result += str(node.cumulative_regrets) + SEPARATOR

    for child in node.children:
        result += marshal(child)

    result += CLOSER

    return result


def unmarshal(model: str) -> InfoSet:
    start = 1
    end = start
    ocurrences = 0

    for i in range(len(model)):
        if model[i] == SEPARATOR:
            ocurrences += 1

        if ocurrences == 3:
            end = i
            break

    data = model[start:end].split(SEPARATOR)
    rank = int(data[0])
    cumulative_strategy = ast.literal_eval(data[1])
    cumulative_regrets = ast.literal_eval(data[2])

    node = InfoSet(rank, cumulative_strategy, cumulative_regrets)

    start = end + 1
    balance = 0

    for i in range(start, len(model) - 1):
        if model[i] == OPENER:
            balance += 1

        if model[i] == CLOSER:
            balance -= 1

        if balance < 0:
            raise Exception("Corrupted strategy data file: Expected " + OPENER)

        if balance == 0:
            child_model = model[start : i + 1]
            child = unmarshal(child_model)

            node.append_child(child)
            start = i + 1

    if balance != 0:
        raise Exception("Corrupted strategy data file: Expected " + CLOSER)

    return node


def _is_terminal(stage: Stage, final_stage: Stage, stage_history: List[Action]) -> bool:
    if stage == final_stage and _players_called(stage_history):
        return True

    if len(stage_history) >= 1 and stage_history[-1] == Action.FOLD:
        return True

    return False


def _players_called(stage_history: List[Action]) -> bool:
    return len(stage_history) >= 2 and stage_history[-1] == Action.CALL and stage_history[-2] == Action.CALL


def _possible_actions(money: int, stage_history: List[Action]) -> List[Action]:
    actions = []

    if _could_raise(money, stage_history):
        actions.append(Action.RAISE)

    actions.append(Action.CALL)
    actions.append(Action.FOLD)

    return actions


def _could_raise(money: int, stage_history: List[Action]) -> bool:
    if money < RAISE_AMOUNT:
        return False

    if Action.RAISE in stage_history:
        return False

    return True


if __name__ == "__main__":
    strategy = build_subgame_strategies()

    with open("strategy", "w") as f:
        f.write(marshal(strategy))

    with open("strategy", "r") as f:
        content = f.read()
        node = unmarshal(content)
