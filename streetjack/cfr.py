#!/usr/bin/env python3

import streetjack.hulth as hulth


class PokerBot:
    def __init__(self):
        self._cum_regrets = dict()
        self._cum_strategy = dict()
        self._strategy_profile = dict()

    def _chance_sampling_cfr(
        self, info_set: hulth.InfoSet, training_player: int, plr_0_prob: float, plr_1_prob: float
    ) -> float:
        if info_set.is_terminal():
            return info_set.utility(training_player)

        if info_set.is_chance():
            actions = info_set.actions()

            expected_utility = 0.0

            for action in actions:
                child = info_set.play(action)
                action_prob = 1 / len(actions)

                # .... : r

                # :rcc -> :rcc:r
                # :rcc:
                # :rcc
                # :rcc:

                # : -> should keep strategy [r: 0.2, c: 0.8, f: 0]
                # :rcc -> no need to keep anything since the only child is a chance node

                # alternative
                # "" -> chance info set
                # ":rcc" -> chance info set
                # ":" -> move info set

                # "" -> chance
                #   ":" -> move
                #       ":c" -> move
                #           ":cr" -> move
                #               ":crc" -> move
                #                   ":crcc" -> chance
                #               ":crf" -> chance
                #           ":cc" -> chance
                #       ":r" -> move
                #       ":f" -> move

                # change in history validations
                # change in generate children
                # is_final_stage to chance info set
                # is_chance to implement in each class (should become abstract method)
                # chance info sets could now be terminal, while move info sets should never be terminal except when one folds
                # chance info set has only one possible action -> Action.CHANCE
                # move info sets could have multiple possible actions but could never return a Action.CHANCE
                # money logic stays the same
                # move utility to chance info set

                # TODO: check if don't saving previous bucket indices ruins accuracy.
                # TODO: check if we could create function to train them until a E-nash equilibrium is found.
                # TODO: players against one another for a test. Create metric to check for E-nash equilibrium.

                child_util = self._chance_sampling_cfr(child, training_player, plr_0_prob, plr_1_prob)
