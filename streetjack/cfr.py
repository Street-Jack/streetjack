#!/usr/bin/env python3

from typing import List, Dict

import yaml
import treys

import streetjack.hulth as hulth
from streetjack.evaluator import Evaluator


INITIAL_REACH_PROB = 1.0
CUM_REGRETS_FIELD = "cum_regrets"
CUM_STRATEGY_FIELD = "cum_strategy"


class PokerBot:
    def __init__(self, evaluator: Evaluator):
        self._cum_regrets = dict()
        self._cum_strategy = dict()

        self._evaluator = evaluator

    def train(self, num_games: int) -> None:
        print("Training poker bot with \033[0;32m{}\033[0m games...".format(num_games))

        for _ in range(num_games):
            print("\033[0;33m\u2022\033[0m", end="", flush=True)

            deck = treys.Deck()
            bundle = hulth.CardBundle(deck, self._evaluator)

            root_info_set = hulth.create_game_root(bundle)

            for trainee in [hulth.SMALL_BLIND, hulth.BIG_BLIND]:
                self._chance_sampling_cfr(root_info_set, trainee, INITIAL_REACH_PROB, INITIAL_REACH_PROB)

        print("")

    @staticmethod
    def unmarshal(file_name: str, evaluator: Evaluator) -> "PokerBot":
        with open(file_name, "r") as dump_file:
            bot_as_dict = yaml.load(dump_file, Loader=yaml.Loader)

            bot = PokerBot(evaluator)
            bot.set_cum_regrets(bot_as_dict[CUM_REGRETS_FIELD])
            bot.set_cum_strategy(bot_as_dict[CUM_STRATEGY_FIELD])

            return bot

    def marshal(self, file_name: str) -> None:
        with open(file_name, "w") as dump_file:
            yaml.dump(
                {
                    CUM_REGRETS_FIELD: self._cum_regrets,
                    CUM_STRATEGY_FIELD: self._cum_strategy,
                },
                dump_file,
            )

    def set_cum_regrets(self, cum_regrets: Dict) -> None:
        self._cum_regrets = cum_regrets

    def set_cum_strategy(self, cum_strategy: Dict) -> None:
        self._cum_strategy = cum_strategy

    def _chance_sampling_cfr(
        self, info_set: hulth.InfoSet, trainee: int, small_blind_prob: float, big_blind_prob: float
    ) -> float:
        if info_set.is_terminal():
            return info_set.utility(trainee)

        if info_set.is_chance():
            return self._chance_sampling_cfr(
                info_set.play(hulth.Action.CHANCE), trainee, small_blind_prob, big_blind_prob
            )

        encoding = info_set.encoding()
        actions = info_set.actions()

        expected_utility = 0.0
        action_utilties = dict()

        strategy = self._get_strategy(encoding, actions)
        curr_player = info_set.curr_player()

        for action in actions:
            action_utilties[action] = 0.0

            child = info_set.play(action)

            action_prob = strategy[action]

            if curr_player == hulth.SMALL_BLIND:
                action_utilties[action] = self._chance_sampling_cfr(
                    child, trainee, action_prob * small_blind_prob, big_blind_prob
                )
            else:
                action_utilties[action] = self._chance_sampling_cfr(
                    child, trainee, small_blind_prob, action_prob * big_blind_prob
                )

            expected_utility += action_utilties[action] * action_prob

        if curr_player == trainee:
            cum_regret = self._info_set_cum_regret(encoding, actions)
            cum_strategy = self._info_set_cum_strategy(encoding, actions)

            reach_prob = big_blind_prob
            cfr_reach_prob = small_blind_prob

            if curr_player == hulth.SMALL_BLIND:
                reach_prob, cfr_reach_prob = cfr_reach_prob, reach_prob

            for action in actions:
                cum_regret[action] += cfr_reach_prob * (action_utilties[action] - expected_utility)
                cum_strategy[action] += reach_prob * strategy[action]

        return expected_utility

    def _info_set_cum_regret(self, encoding: str, actions: List[hulth.Action]) -> Dict:
        if encoding in self._cum_regrets:
            return self._cum_regrets[encoding]

        self._cum_regrets[encoding] = dict()

        for action in actions:
            self._cum_regrets[encoding][action] = 0

        return self._cum_regrets[encoding]

    def _info_set_cum_strategy(self, encoding: str, actions: List[hulth.Action]) -> Dict:
        if encoding in self._cum_strategy:
            return self._cum_strategy[encoding]

        self._cum_strategy[encoding] = dict()

        for action in actions:
            self._cum_strategy[encoding][action] = 0

        return self._cum_strategy[encoding]

    def _get_strategy(self, encoding: str, actions: List[hulth.Action]) -> Dict:
        normalising_sum = 0.0
        strategy = dict()
        cum_regret = self._info_set_cum_regret(encoding, actions)

        for action in actions:
            strategy[action] = cum_regret[action] if cum_regret[action] > 0 else 0.0
            normalising_sum += strategy[action]

        for action in actions:
            if normalising_sum > 0.0:
                strategy[action] /= normalising_sum
            else:
                strategy[action] = 1.0 / len(actions)

        return strategy

    def _avg_strategy(self, info_set: hulth.InfoSet) -> Dict:
        actions = info_set.actions()
        encoding = info_set.encoding()

        avg_strategy = dict()
        normalising_sum = 0.0

        cum_strategy = self._info_set_cum_strategy(encoding, actions)

        for action in actions:
            normalising_sum += cum_strategy[action]

        for action in actions:
            if normalising_sum > 0.0:
                avg_strategy[action] = cum_strategy[action] / normalising_sum
            else:
                avg_strategy[action] = 1 / len(actions)

        return avg_strategy


if __name__ == "__main__":
    e = Evaluator()
    b = PokerBot(e)

    b.train(50)
    b.marshal("dump.yml")

    # copy_bot = PokerBot.unmarshal("dump.yml", evaluator)

    # print(copy_bot._cum_strategy)
