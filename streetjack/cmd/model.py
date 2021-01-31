#!/usr/bin/env python3

import os
import logging
from pathlib import Path

import treys

import streetjack.bot.evaluator as evaluator
import streetjack.bot.cfr as cfr
import streetjack.bot.hulth as hulth

DATA_DIR_PARAM = "DATA_DIR"


def generate_card_bundle() -> hulth.CardBundle:
    hand_evaluator = evaluator.Evaluator()
    deck = treys.Deck()

    return hulth.CardBundle(deck, hand_evaluator)


def load_bot(model_name: str, is_new: bool = False) -> cfr.PokerBot:
    hand_evaluator = evaluator.Evaluator()
    model_path = get_model_path(model_name)

    if is_new:
        logging.info("New model requested at {}. Will override any old model if present.".format(model_path))
        return cfr.PokerBot(hand_evaluator)

    if not os.path.exists(model_path):
        logging.info("Missing model. Creating new at {}".format(model_path))
        return cfr.PokerBot(hand_evaluator)

    logging.info("Model found at {}. Continuing to train it...".format(model_path))
    return cfr.PokerBot.unmarshal(model_path, hand_evaluator)


def get_model_path(model_name: str) -> Path:
    data_dir = _data_dir_path()
    full_model_file_name = "{}.yml".format(model_name)
    return Path(data_dir, full_model_file_name)


def _data_dir_path() -> Path:
    data_dir = os.getenv(DATA_DIR_PARAM)
    data_dir_path = Path(data_dir)

    if not os.path.exists(data_dir_path):
        os.makedirs(data_dir_path)

    return data_dir_path
