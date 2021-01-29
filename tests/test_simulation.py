#!/usr/bin/env python3

import time
import unittest
from unittest.mock import MagicMock

from treys import Card

from streetjack.evaluator import Evaluator
import streetjack.hulth as hulth
from streetjack.hulth import Action, CardBundle, InfoSet, ChanceInfoSet


class TestMoveInfoSet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._royal_flush_hand = [Card.new("Ac"), Card.new("Kc")]
        cls._straight_flush_hand = [Card.new("9c"), Card.new("8c")]
        cls._board = [Card.new("Qc"), Card.new("Jc"), Card.new("Tc"), Card.new("2c"), Card.new("7c")]

        cls._max_bucket_index = 9

        mock_deck = cls._mock_deck()
        evaluator = Evaluator()

        cls._bundle = CardBundle(mock_deck, evaluator)

    def setUp(self) -> None:
        self._tree = set()

    def test_single_stage(self):
        base_encoding = ":cc:cc:cc:"
        base_history = [Action.CHANCE, Action.CALL, Action.CALL] * 3 + [Action.CHANCE]

        info_set = ChanceInfoSet(history=base_history, bundle=TestMoveInfoSet._bundle)
        self._generate_subgame_tree(info_set)

        info_set_postfixes = ["r", "rc", "rcc", "rf", "c", "cr", "crf", "crc", "crcc", "cc"]

        for postfix in info_set_postfixes:
            encoding = base_encoding + postfix + ".{}".format(TestMoveInfoSet._max_bucket_index)
            self.assertIn(encoding, self._tree)

    def test_whole_game(self):
        info_set = hulth.create_game_root(TestMoveInfoSet._bundle)
        self._generate_subgame_tree(info_set)

    def _generate_subgame_tree(self, info_set: InfoSet) -> None:
        if not info_set.is_chance():
            encoding = info_set.encoding()
            self._tree.add(encoding)

        if info_set.is_terminal():
            return

        for action in info_set.actions():
            child = info_set.play(action)

            self._generate_subgame_tree(child)

    @staticmethod
    def _mock_deck() -> MagicMock:
        deck = MagicMock()

        deck.draw = MagicMock()
        deck.draw.side_effect = [
            TestMoveInfoSet._royal_flush_hand,
            TestMoveInfoSet._straight_flush_hand,
            TestMoveInfoSet._board,
        ]

        return deck
