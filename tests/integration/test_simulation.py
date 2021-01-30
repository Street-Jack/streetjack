#!/usr/bin/env python3

import unittest

from streetjack.evaluator import Evaluator
import streetjack.hulth as hulth
from streetjack.hulth import Action, CardBundle, InfoSet, ChanceInfoSet

import tests.util.common as common


class TestMoveInfoSet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        mock_deck = common.mock_deck()
        evaluator = Evaluator()

        cls._bundle = CardBundle(mock_deck, evaluator)

    def setUp(self) -> None:
        self._tree = set()

    def test_single_stage(self):
        base_encoding = ":cc:cc:cc:"
        base_history = [Action.CHANCE, Action.CALL, Action.CALL] * 3

        info_set = ChanceInfoSet(history=base_history, bundle=TestMoveInfoSet._bundle)
        self._generate_subgame_tree(info_set)

        info_set_postfixes = ["r", "rc", "rf", "c", "cr", "crf", "crc"]

        for postfix in info_set_postfixes:
            encoding = base_encoding + postfix + ".{}".format(common.MAX_BUCKET_INDEX)
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
