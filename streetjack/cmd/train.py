#!/usr/bin/env python3

import os
import logging
import argparse
from pathlib import Path

import streetjack.bot.evaluator as evaluator
import streetjack.bot.cfr as cfr


SUBCMD_NAME = "train"
DATA_DIR_PARAM = "DATA_DIR"


def add_parser_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-model", help="Name of trained model.", required=True, type=str)

    parser.add_argument("-iter", help="Number of games to train the bot with.", required=True, type=_check_positive)

    parser.add_argument("--new", help="Erase old model if exists and create new.", required=False, action="store_true")


def run(args: argparse.Namespace) -> None:
    hand_evaluator = evaluator.Evaluator()
    bot = _load_bot(args.model, hand_evaluator, is_new=args.new)

    bot.train(num_games=args.iter)

    model_path = _model_path(model_name=args.model)
    bot.marshal(model_path)


def _check_positive(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("%s is an invalid positive int value" % value)
    return ivalue


def _load_bot(model_name: str, hand_evaluator: evaluator.Evaluator, is_new: bool = False) -> cfr.PokerBot:
    model_path = _model_path(model_name)

    if is_new:
        logging.info("New model requested at {}. Will override any old model if present.".format(model_path))
        return cfr.PokerBot(hand_evaluator)

    if not os.path.exists(model_path):
        logging.info("Missing model. Creating new at {}".format(model_path))
        return cfr.PokerBot(hand_evaluator)

    logging.info("Model found at {}. Continuing to train it...".format(model_path))
    return cfr.PokerBot.unmarshal(model_path, hand_evaluator)


def _model_path(model_name: str) -> Path:
    data_dir = _data_dir_path()
    full_model_file_name = "{}.yml".format(model_name)
    return Path(data_dir, full_model_file_name)


def _data_dir_path() -> Path:
    data_dir = os.getenv(DATA_DIR_PARAM)
    data_dir_path = Path(data_dir)

    if not os.path.exists(data_dir_path):
        os.makedirs(data_dir_path)

    return data_dir_path
