#!/usr/bin/env python3

import argparse

import streetjack.cmd.model as model
import streetjack.cmd.util as util


SUBCMD_NAME = "train"


def add_parser_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-model", help="Name of trained model.", required=True, type=str)

    parser.add_argument("-iter", help="Number of games to train the bot with.", required=True, type=util.check_positive)

    parser.add_argument("--new", help="Erase old model if exists and create new.", required=False, action="store_true")


def run(args: argparse.Namespace) -> None:
    bot = model.load_bot(args.model, is_new=args.new)

    bot.train(num_games=args.iter)

    model_path = model.get_model_path(model_name=args.model)
    bot.marshal(model_path)
