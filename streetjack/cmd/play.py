#!/usr/bin/env python3

from logging import info
import os
import time
import math
import argparse
from typing import List
from enum import Enum

import treys

import streetjack.cmd.model as model
import streetjack.bot.hulth as hulth
from streetjack.bot.cfr import PokerBot


SUBCMD_NAME = "play"
USER_ERROR_WAIT_IN_SECONDS = 2
BOT_TURN_TIME_SECONDS = 1
BOT_REVEALED_ACTION_IN_SECONDS = 4


class Color(Enum):
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[0;33m"
    PUPRLE = "\033[0;35m"
    AZURE = "\033[0;36m"
    WHITE = "\033[0m"


def add_parser_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-model", help="Name of trained model.", required=True, type=str)


def run(args: argparse.Namespace):
    bot = model.load_bot(args.model)

    while True:
        _clear_screen()
        _print_logo()

        _print_empty_lines(1)

        _print_center("[Press Enter to start a game!]", Color.WHITE)
        _print_center("[Press Ctr-D to exit]", Color.WHITE)

        _get_input("")

        player = int(_get_input("Choose player (0 - small blind, 1 - big blind): "))

        if not player in [hulth.SMALL_BLIND, hulth.BIG_BLIND]:
            _print_center("Selected invalid player!")
            _print_center("Returning to start screen in {} seconds...".format(USER_ERROR_WAIT_IN_SECONDS))
            time.sleep(USER_ERROR_WAIT_IN_SECONDS)
            continue

        _print_center("Shuffling cards! Please wait...")
        bundle = model.generate_card_bundle()

        _play_game(bot, bundle, player)


def _play_game(bot: PokerBot, bundle: hulth.CardBundle, user: int) -> None:
    info_set = hulth.create_game_root(bundle)

    while True:
        _clear_screen()

        if info_set.is_terminal():
            if info_set.stage() == hulth.Stage.SHOWDOWN:
                _showdown(bundle, user)

            _print_terminal_state(info_set, user)

            _get_input("[Press Enter to go back to main menu!]")
            return

        if info_set.is_chance():
            _print_center("Revealing cards...")
            time.sleep(USER_ERROR_WAIT_IN_SECONDS)

            info_set = info_set.play(hulth.Action.CHANCE)
            continue

        curr_player = info_set.curr_player()
        _print_center("It is player {}'s turn".format(curr_player))

        _print_hole_cards(bundle, info_set.stage())

        _print_stats(bundle, info_set, user)

        if curr_player == user:
            info_set = _play_as_user(info_set)
        else:
            info_set = _play_as_bot(bot, info_set)


def _play_as_user(info_set: hulth.InfoSet) -> hulth.InfoSet:
    possible_actions_as_str = _possible_actions_as_str(info_set)

    user_action_as_str = _get_input("Pick your action ({}): ".format(possible_actions_as_str))
    user_action = None

    for action in info_set.actions():
        if action.value == user_action_as_str:
            user_action = action

    if not user_action:
        _print_center("You picked an invalid action")
        time.sleep(USER_ERROR_WAIT_IN_SECONDS)
        return _play_as_user(info_set)

    return info_set.play(user_action)


def _play_as_bot(bot: PokerBot, info_set: hulth.InfoSet) -> hulth.InfoSet:
    possible_actions_as_str = _possible_actions_as_str(info_set)
    _print_center("Possible bot actions ({})".format(possible_actions_as_str))

    _print_center("Waiting for opponent to make turn...")
    time.sleep(BOT_TURN_TIME_SECONDS)

    child = bot.play(info_set)

    bot_action = child.last_opponent_action()

    _print_center("Bot played {}.".format(hulth.ACTION_NAMES[bot_action]), Color.YELLOW)
    time.sleep(BOT_REVEALED_ACTION_IN_SECONDS)

    return child


def _possible_actions_as_str(info_set: hulth.InfoSet) -> str:
    actions = info_set.actions()
    possible_actions = []

    for action in actions:
        possible_action = "{} - {}".format(action.value, hulth.ACTION_NAMES[action])
        possible_actions.append(possible_action)

    return ", ".join(possible_actions)


def _clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def _print_logo():
    logo = [
        " _____ ___________ _____ _____ _____  ___  ___  _____  _   __",
        "/  ___|_   _| ___ \  ___|  ___|_   _||_  |/ _ \/  __ \| | / /",
        "\ `--.  | | | |_/ / |__ | |__   | |    | / /_\ \ /  \/| |/ / ",
        " `--. \ | | |    /|  __||  __|  | |    | |  _  | |    |    \ ",
        "/\__/ / | | | |\ \| |___| |___  | |/\__/ / | | | \__/\| |\  \\",
        "\____/  \_/ \_| \_\____/\____/  \_/\____/\_| |_/\____/\_| \_/",
    ]

    for logo_row in logo:
        _print_center(logo_row, Color.PUPRLE)

    _print_empty_lines(2)

    _print_center("The Heads Up Limited Texas Hold'Em Game of Eternal Pain", Color.YELLOW)


def _get_input(msg: str):
    _print_center(msg, Color.WHITE)
    width = os.get_terminal_size().columns
    return input(" ".center(math.floor(width / 2)))


def _print_hole_cards(bundle: hulth.CardBundle, stage: hulth.Stage) -> None:
    board = bundle.board(stage)

    _print_empty_lines(2)
    _print_center("Board cards")
    _print_empty_lines(1)

    if len(board) > 0:
        _print_cards(board)
    else:
        _print_center("No board cards during PREFLOP", Color.AZURE)

    _print_empty_lines(2)


def _print_stats(bundle: hulth.CardBundle, info_set: hulth.InfoSet, user: int) -> None:
    hand = bundle.player_hand(user)
    hand_as_str = _cards_as_pretty_strings(hand)

    stats = "[Hand - {}] ".format(hand_as_str)

    available_money = info_set.available_money_of_players()

    user_money = available_money[user]
    bot = hulth.get_opponent(user)
    bot_money = available_money[bot]

    stats += "[Our Money - {}] [Opponent Money - {}] ".format(user_money, bot_money)

    pot_money = info_set.pot_money()
    stats += "[Pot Money - {}]".format(pot_money)

    _print_center(stats, Color.YELLOW)


def _print_cards(cards: List[int]):
    cards_as_str = _cards_as_pretty_strings(cards)

    _print_center(cards_as_str, Color.AZURE)


def _showdown(bundle: hulth.CardBundle, user: int) -> None:
    bot = hulth.get_opponent(user)

    user_cards = bundle.player_hand(user)
    bot_cards = bundle.player_hand(bot)

    board = bundle.board(hulth.Stage.SHOWDOWN)

    user_showdown_cards = _cards_as_pretty_strings(user_cards + board)
    bot_showdown_cards = _cards_as_pretty_strings(bot_cards + board)

    _print_center("Your cards - {}".format(user_showdown_cards))
    _print_center("Bot cards - {}".format(bot_showdown_cards))


def _print_terminal_state(info_set: hulth.InfoSet, user: int) -> None:
    winner = info_set.winner()
    user_utility = info_set.utility(user)

    if winner == user:
        _print_center("You won {} chips!!!".format(user_utility), Color.GREEN)
    else:
        _print_center("You lost {} chips!!! :(".format(-user_utility), Color.RED)


def _cards_as_pretty_strings(cards: List[int]):
    pretty_cards = []

    for card in cards:
        pretty_card = treys.Card.int_to_pretty_str(card)
        pretty_cards.append(pretty_card)

    return " ".join(pretty_cards)


def _print_center(text: str, color: Color = Color.WHITE) -> None:
    width = os.get_terminal_size().columns
    centered_text = text.center(width)
    print("{}{}{}".format(color.value, centered_text, Color.WHITE.value))


def _print_empty_lines(n: int) -> None:
    print("".join(["\n"] * n))
