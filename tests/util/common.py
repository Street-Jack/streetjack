#!/usr/bin/env python3

from unittest.mock import MagicMock

from treys import Card

ROYAL_FLUSH_HAND = [Card.new("Ac"), Card.new("Kc")]
STRAIGHT_FLUSH_HAND = [Card.new("9c"), Card.new("8c")]
BOARD = [Card.new("Qc"), Card.new("Jc"), Card.new("Tc"), Card.new("2c"), Card.new("7c")]

MAX_BUCKET_INDEX = 9


def mock_deck() -> MagicMock:
    deck = MagicMock()

    deck.draw = MagicMock()
    deck.draw.side_effect = [
        ROYAL_FLUSH_HAND,
        STRAIGHT_FLUSH_HAND,
        BOARD,
    ]

    return deck
