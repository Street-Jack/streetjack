#!/usr/bin/env python3

import unittest

import treys

from streetjack.bot.evaluator import Evaluator


class TestEvaluator(unittest.TestCase):
    BUCKET_COUNT = 10

    def setUp(self):
        self._eval = Evaluator()

    def test_royal_flush_rank_after_flop(self):
        self._assert_rank_with_board(
            hand=[treys.Card.new("Kh"), treys.Card.new("Ah")],
            board=[treys.Card.new("Qh"), treys.Card.new("Jh"), treys.Card.new("Th")],
            expected_rank=9,
        )

    def test_high_card_rank_after_flop(self):
        self._assert_rank_with_board(
            hand=[treys.Card.new("3d"), treys.Card.new("Jc")],
            board=[treys.Card.new("8s"), treys.Card.new("4h"), treys.Card.new("2s")],
            expected_rank=2,  # obviously because of potential
        )

    def test_royal_flush_rank_after_turn(self):
        self._assert_rank_with_board(
            hand=[treys.Card.new("Kh"), treys.Card.new("Ah")],
            board=[
                treys.Card.new("Qh"),
                treys.Card.new("Jh"),
                treys.Card.new("Th"),
                treys.Card.new("2h"),
            ],
            expected_rank=9,
        )

    def test_high_card_rank_after_turn(self):
        self._assert_rank_with_board(
            hand=[treys.Card.new("3d"), treys.Card.new("Jc")],
            board=[
                treys.Card.new("8s"),
                treys.Card.new("4h"),
                treys.Card.new("2s"),
                treys.Card.new("9c"),
            ],
            expected_rank=1,  # obviously because of potential
        )

    def test_royal_flush_rank_showdown(self):
        self._assert_rank_with_board(
            hand=[treys.Card.new("Kh"), treys.Card.new("Ah")],
            board=[
                treys.Card.new("Qh"),
                treys.Card.new("Jh"),
                treys.Card.new("Th"),
                treys.Card.new("2h"),
                treys.Card.new("7s"),
            ],
            expected_rank=9,
        )

    def test_high_card_rank_showdown(self):
        self._assert_rank_with_board(
            hand=[treys.Card.new("3d"), treys.Card.new("Jc")],
            board=[
                treys.Card.new("8s"),
                treys.Card.new("4h"),
                treys.Card.new("2s"),
                treys.Card.new("9c"),
                treys.Card.new("Kd"),
            ],
            expected_rank=1,
        )

    def test_weakest_hand_rank_during_preflop(self):
        self._assert_rank_with_board(hand=[treys.Card.new("2d"), treys.Card.new("7c")], board=[], expected_rank=0)

    def test_strongest_hand_rank_during_preflop(self):
        self._assert_rank_with_board(hand=[treys.Card.new("Ad"), treys.Card.new("Ac")], board=[], expected_rank=9)

    def test_single_suit_hand_rank_during_preflop(self):
        self._assert_rank_with_board(hand=[treys.Card.new("5h"), treys.Card.new("7h")], board=[], expected_rank=2)

    def test_different_strength_combos_in_single_bucket(self):
        royal_flush_hand = [treys.Card.new("Kh"), treys.Card.new("Ah")]
        straight_flush_hand = [treys.Card.new("9h"), treys.Card.new("8h")]

        board = [
            treys.Card.new("Qh"),
            treys.Card.new("Jh"),
            treys.Card.new("Th"),
            treys.Card.new("2h"),
            treys.Card.new("7s"),
        ]

        royal_flush_rank = self._effective_rank(royal_flush_hand, board)
        straight_flush_rank = self._effective_rank(straight_flush_hand, board)

        self.assertEqual(royal_flush_rank, straight_flush_rank)

        royal_flush_strength = self._eval.effective_hand_strength(royal_flush_hand, board)
        straight_flush_strength = self._eval.effective_hand_strength(straight_flush_hand, board)
        allowable_diff = 0.000001

        self.assertGreater(allowable_diff, abs(royal_flush_strength - straight_flush_strength))

    def _assert_rank_with_board(self, hand, board, expected_rank):
        rank = self._effective_rank(hand, board)
        allowable_diff = 1

        self.assertGreaterEqual(allowable_diff, abs(rank - expected_rank))

    def _effective_rank(self, hand, board):
        return self._eval.effective_rank(hand, board, bucket_count=self.BUCKET_COUNT)
