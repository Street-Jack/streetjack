#!/usr/bin/env python3

from logging import info
import unittest
from unittest.mock import MagicMock, patch
from typing import List

from treys import Card

from streetjack.hulth import CardBundle, Stage, ChanceInfoSet, MoveInfoSet, Action


class TestCardBundle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._royal_flush_hand = [Card.new('Ac'), Card.new('Kc')]
        cls._straight_flush_hand = [Card.new('9c'), Card.new('8c')]
        cls._board = [Card.new('Qc'), Card.new('Jc'), Card.new('Tc'), Card.new('2c'), Card.new('7c')]

    def test_cards(self):
        bundle = self._bundle()

        plr_0_hand = bundle.player_hand(player_index=0)
        plr_1_hand = bundle.player_hand(player_index=1)

        self.assertEqual(plr_0_hand, self._royal_flush_hand)
        self.assertEqual(plr_1_hand, self._straight_flush_hand)
    
    def test_bucket_index(self):
        bundle = self._bundle()

        expected_rank = 9

        for stage in Stage:
            plr_0_bucket = bundle.bucket_index(player_index=0, stage=stage)
            plr_1_bucket = bundle.bucket_index(player_index=1, stage=stage)

            self.assertEqual(plr_0_bucket, expected_rank)
            self.assertEqual(plr_1_bucket, expected_rank)
    
    def test_winner_plr0(self):
        bundle = self._bundle()
        winner = bundle.winner_index()
        plr_0 = 0

        self.assertEqual(winner, plr_0)

    def test_winner_plr1(self):
        bundle = self._bundle(hand_strengths=[1000, 3])
        winner = bundle.winner_index()
        plr_1 = 1

        self.assertEqual(winner, plr_1)

    def _bundle(self, hand_strengths=None):
        if not hand_strengths:
            hand_strengths = [1, 3]

        deck = self._mock_deck()
        evaluator = self._mock_evaluator(hand_strengths)

        return CardBundle(deck, evaluator)

    def _mock_deck(self) -> MagicMock:
        deck = MagicMock()

        deck.draw = MagicMock()
        deck.draw.side_effect = [self._royal_flush_hand, self._straight_flush_hand, self._board]

        return deck
    
    def _mock_evaluator(self, hand_strengths: List[int]) -> MagicMock:
        mock_evaluator = MagicMock()

        mock_evaluator.effective_rank = MagicMock(return_value=9)

        mock_evaluator.effective_hand_strength = MagicMock()
        mock_evaluator.effective_hand_strength.side_effect = hand_strengths

        return mock_evaluator


class TestChanceInfoSet(unittest.TestCase):
    def setUp(self) -> None:
        self._bundle = MagicMock()
   
    def test_small_blind_start_actions(self) -> None:
        self._assert_available_actions(
            history=[Action.CHANCE],
            expected_actions=[Action.RAISE, Action.CALL, Action.FOLD],
        )
    
    def test_small_blind_fold_forbidden_in_later_game_stage(self) -> None:
        self._assert_available_actions(
            history=[Action.CHANCE, Action.CALL, Action.CALL, Action.CHANCE],
            expected_actions=[Action.RAISE, Action.CALL],
        )
    
    def test_impossible_raise(self) -> None:
        raising_stage = [Action.RAISE, Action.CALL, Action.CALL, Action.CHANCE]

        # raises -> 10, 10+20, 20, 20, 20
        self._assert_available_actions(
            history=[Action.CHANCE] + raising_stage*3,
            expected_actions=[Action.CALL],
        )
    
    def test_play_at_start(self) -> None:
        history = [Action.CHANCE]
        info_set = ChanceInfoSet(history, bundle=self._bundle)

        expected_actions = [Action.RAISE, Action.CALL, Action.FOLD]

        for action in expected_actions:
            child = info_set.play(action)

            expected_child_history = history + [action]
            child_history = child.history()

            self.assertListEqual(child_history, expected_child_history)
    
    def test_is_terminal(self) -> None:
        info_set = ChanceInfoSet(history=[Action.CHANCE], bundle=self._bundle)
        self.assertFalse(info_set.is_terminal())

    def test_is_chance(self) -> None:
        info_set = ChanceInfoSet(history=[Action.CHANCE], bundle=self._bundle)
        self.assertTrue(info_set.is_chance())

    def _assert_available_actions(self, history: List[Action], expected_actions=List[Action]) -> None:
        info_set = ChanceInfoSet(history=history, bundle=self._bundle)

        actions = info_set.actions()
        self.assertListEqual(actions, expected_actions)
     # :r -> c,f
    # :rc -> c,f
    #  -> r,c,f
    # :c -> r,c,f


class TestMoveInfoSet(unittest.TestCase):
    def setUp(self) -> None:
        self._bundle = MagicMock()

    def test_big_blind_actions_after_small_blind_call(self):
        self._assert_available_actions(
            history=[Action.CHANCE, Action.CALL],
            expected_actions=[Action.RAISE, Action.CALL],
        )
    
    def test_big_blind_actions_after_small_blind_raise(self):
        self._assert_available_actions(
            history=[Action.CHANCE, Action.RAISE],
            expected_actions=[Action.CALL, Action.FOLD],
        )
    
    def test_actions_after_players_called(self):
        self._assert_available_actions(
            history=[Action.CHANCE, Action.CALL, Action.CALL],
            expected_actions=[Action.CHANCE],
        )
    
    def test_impossible_raise(self):
        raising_stage = [Action.RAISE, Action.CALL, Action.CALL, Action.CHANCE]

        self._assert_available_actions(
            history=[Action.CHANCE] + raising_stage*3 + [Action.CALL],
            expected_actions=[Action.CALL],
        )
    
    def test_terminal_actions(self):
        self._assert_available_actions(
            history=[Action.CHANCE, Action.RAISE, Action.FOLD],
            expected_actions=[],
        )
    
    def test_encoding(self):
        # TODO: think about this:
        # imperfect recall (or so we guess...)
        #:rcc.5:c.6 vs :rcc:c.6
        #:rcc.1:c.6 vs :rcc:c.6

        history = [Action.CHANCE, Action.RAISE, Action.CALL, Action.CALL, Action.CHANCE, Action.CALL]
        bucket_index = 1
        self._bundle.bucket_index = MagicMock(return_value=bucket_index)

        info_set = MoveInfoSet(history=history, bundle=self._bundle)

        encoding = info_set.encoding()
        expected_encoding = ':rcc:c.{}'.format(bucket_index)

        self.assertEqual(encoding, expected_encoding)

    def _assert_available_actions(self, history: List[Action], expected_actions=List[Action]) -> None:
        info_set = MoveInfoSet(history=history, bundle=self._bundle)

        actions = info_set.actions()
        self.assertListEqual(actions, expected_actions)