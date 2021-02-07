import argparse
from typing import Tuple

from streetjack.bot.cfr import PokerBot

import streetjack.cmd.util as util
import streetjack.bot.hulth as hulth
import streetjack.cmd.model as model


SUBCMD_NAME = "mortal-kombat"
STATISTICALLY_MEANINGLESS_DIFF = 0.02


def add_parser_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-subzero", help="Name of trained model of fighter one.", required=True, type=str)
    parser.add_argument("-scorpion", help="Name of trained model of fighter two.", required=True, type=str)

    parser.add_argument(
        "-fights", help="Number of games to compare the bots with.", required=True, type=util.check_positive
    )


def run(args: argparse.Namespace) -> None:
    scorpion = model.load_bot(args.scorpion)
    subzero = model.load_bot(args.subzero)
    fights = args.fights

    cum_scorpion_utility = 0
    cum_subzero_utility = 0

    for fight in range(fights):
        percent_complete = (fight / fights) * 100
        print("\033[0;32mProgress {}%\033[0;0m".format(int(percent_complete)), end="\r")

        bundle = model.generate_card_bundle()

        small_blind_utility, big_blind_utility = _play_game(scorpion, subzero, bundle)
        cum_scorpion_utility += small_blind_utility
        cum_subzero_utility += big_blind_utility

        small_blind_utility, big_blind_utility = _play_game(subzero, scorpion, bundle)
        cum_subzero_utility += small_blind_utility
        cum_scorpion_utility += big_blind_utility

    norm_scorpion_utility = _norm_utility(cum_scorpion_utility, fights)
    norm_subzero_utility = _norm_utility(cum_subzero_utility, fights)

    print("Scorpion utility rating {}".format(norm_scorpion_utility))
    print("Subzero utility rating {}".format(norm_subzero_utility))

    if abs(norm_scorpion_utility) > STATISTICALLY_MEANINGLESS_DIFF:
        print("There is a better strategy.")
    else:
        print("There is a meaningful statistical diff between both of the strategies.")


def _play_game(small_blind: PokerBot, big_blind: PokerBot, bundle: hulth.CardBundle) -> Tuple[int, int]:
    info_set = hulth.create_game_root(bundle)

    while True:
        if info_set.is_terminal():
            small_blind_utility = info_set.utility(hulth.SMALL_BLIND)
            big_blind_utility = info_set.utility(hulth.BIG_BLIND)

            return small_blind_utility, big_blind_utility

        if info_set.is_chance():
            info_set = info_set.play(hulth.Action.CHANCE)
            continue

        curr_player = info_set.curr_player()

        if curr_player == hulth.SMALL_BLIND:
            info_set = small_blind.play(info_set)
        else:
            info_set = big_blind.play(info_set)


def _norm_utility(cum_utility: int, fights: int) -> float:
    return cum_utility / (fights * hulth.START_MONEY)
