#!/usr/bin/env python3

import sys
import logging
import argparse

import streetjack.cmd.train as train
import streetjack.cmd.play as play


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="subparser")
    subparsers.required = True

    train_parser = subparsers.add_parser(name=train.SUBCMD_NAME)
    train.add_parser_args(train_parser)

    play_parser = subparsers.add_parser(name=play.SUBCMD_NAME)
    play.add_parser_args(play_parser)

    return parser.parse_args()


def configure_logging() -> None:
    fmt = "[%(asctime)s][%(levelname)s] %(message)s"
    logging.basicConfig(stream=sys.stdout, format=fmt, level=logging.INFO, datefmt="%H:%M:%S")


if __name__ == "__main__":
    configure_logging()
    args = parse_args()

    if args.subparser == train.SUBCMD_NAME:
        train.run(args)
    elif args.subparser == play.SUBCMD_NAME:
        play.run(args)
