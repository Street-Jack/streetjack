#!/usr/bin/env python3

import itertools
import math
import random
from typing import List, Tuple

import treys

MAX_CARDS = 52
MAX_COMMUNITY_CARDS = 5

MAX_CHEN_FORMULA_VALUE = 20
MIN_CHEN_FORMULA_VALUE = -1

CHEN_ACE_RANK = 10
CHEN_KING_RANK = 8
CHEN_QUEEN_RANK = 7
CHEN_JACK_RANK = 6

RANK_OFFSET = 2


class Evaluator:
    def __init__(self):
        self.evaluator = treys.Evaluator()

    def effective_rank(self, hand: List[int], board: List[int], bucket_count: int) -> int:
        if board == []:
            return self._effective_hand_rank(hand, bucket_count)

        return self._effective_rank_with_board(hand, board, bucket_count)

    def rank(self, hand: List[int], board: List[int]) -> int:
        return self.evaluator.evaluate(hand, board)

    def effective_hand_strength(self, hand: List[int], board: List[int]) -> float:
        hand_strength = self._hand_strenght(hand, board)
        ppot, npot = self._hand_potential(hand, board)

        return hand_strength * (1 - npot) + (1 - hand_strength) * ppot

    def _effective_hand_rank(self, hand: List[int], bucket_count: int) -> int:
        # Using Chen formula
        fst_card_score = self._chen_score(hand[0])
        snd_card_score = self._chen_score(hand[1])

        score = max(fst_card_score, snd_card_score)

        if treys.Card.get_suit_int(hand[0]) == treys.Card.get_suit_int(hand[1]):
            score += 2

        fst_card_rank = treys.Card.get_rank_int(hand[0])
        snd_card_rank = treys.Card.get_rank_int(hand[1])

        ranks_diff = abs(fst_card_rank - snd_card_rank)

        if ranks_diff == 0:
            score *= 2
        elif ranks_diff == 1:
            score += 1
        elif ranks_diff == 2:
            score -= 1
        elif ranks_diff == 3:
            score -= 2
        elif ranks_diff == 4:
            score -= 4
        else:
            score -= 5

        score = math.ceil(score)
        norm_score = (score - MIN_CHEN_FORMULA_VALUE) / MAX_CHEN_FORMULA_VALUE

        return math.floor(norm_score * (bucket_count - 1))

    @staticmethod
    def _chen_score(card: int) -> int:
        ace_rank = treys.Card.get_rank_int(treys.Card.new("Ac"))
        king_rank = treys.Card.get_rank_int(treys.Card.new("Kc"))
        queen_rank = treys.Card.get_rank_int(treys.Card.new("Qc"))
        jack_rank = treys.Card.get_rank_int(treys.Card.new("Jc"))

        card_rank = treys.Card.get_rank_int(card)

        if card_rank == ace_rank:
            return CHEN_ACE_RANK

        if card_rank == king_rank:
            return CHEN_KING_RANK

        if card_rank == queen_rank:
            return CHEN_QUEEN_RANK

        if card_rank == jack_rank:
            return CHEN_JACK_RANK

        return (RANK_OFFSET + card_rank) / 2

    def _effective_rank_with_board(self, hand: List[int], board: List[int], bucket_count: int) -> int:
        ehs = self.effective_hand_strength(hand, board)
        return math.floor(ehs * bucket_count)

    def _hand_strenght(self, hand: List[int], board: List[int]) -> float:
        ahead = tied = behind = 0.0
        our_rank = self.rank(hand, board)

        possible_opp_hands = self._card_combinations(excluded_cards=board + hand, tuple_size=2)

        for opp_hand in possible_opp_hands:
            opp_rank = self.rank(list(opp_hand), board)

            if our_rank < opp_rank:
                ahead += 1.0
            elif our_rank == opp_rank:
                tied += 1.0
            else:
                behind += 1.0

        return (ahead + tied / 2.0) / (ahead + tied + behind)

    def _hand_potential(self, hand: List[int], board: List[int]) -> Tuple[float, float]:
        ahead = 0
        tied = 1
        behind = 2

        hand_pot = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
        hp_totals = [0.0, 0.0, 0.0]

        our_rank = self.rank(hand, board)

        possible_opp_hands = self._card_combinations(excluded_cards=hand + board, tuple_size=2)

        num_undrawn_community_cards = MAX_COMMUNITY_CARDS - len(board)
        community_sample_ratios = [1, 0.1, 0.005]
        community_sample_ratio = community_sample_ratios[num_undrawn_community_cards]

        for opp_hand in possible_opp_hands:
            opp_rank = self.rank(list(opp_hand), board)

            index = 0
            if our_rank < opp_rank:
                index = ahead
            elif our_rank == opp_rank:
                index = tied
            else:
                index = behind

            community_combinations = self._card_combinations(
                excluded_cards=hand + board + list(opp_hand),
                tuple_size=num_undrawn_community_cards,
                sample_size_ratio=community_sample_ratio,
            )

            for community_combination in community_combinations:
                hp_totals[index] += 1.0

                new_board = board + list(community_combination)

                our_best = self.rank(hand, new_board)
                opp_best = self.rank(list(opp_hand), new_board)

                if our_best < opp_best:
                    hand_pot[index][ahead] += 1.0
                elif our_best == opp_best:
                    hand_pot[index][tied] += 1.0
                else:
                    hand_pot[index][behind] += 1.0

        ppot_num = hand_pot[behind][ahead] + hand_pot[behind][tied] / 2 + hand_pot[tied][ahead] / 2 + 0.001
        ppot_denom = hp_totals[behind] + hp_totals[tied] + 0.001

        ppot = ppot_num / ppot_denom

        npot_num = hand_pot[ahead][behind] + hand_pot[tied][behind] / 2 + hand_pot[ahead][tied] / 2 + 0.001
        npot_denom = hp_totals[ahead] + hp_totals[tied] + 0.001

        npot = npot_num / npot_denom

        return ppot, npot

    @staticmethod
    def _card_combinations(
        excluded_cards: List[int], tuple_size: int, sample_size_ratio: float = 1.0
    ) -> List[Tuple[int]]:
        deck = treys.Deck()
        cards = deck.draw(MAX_CARDS)
        deck_as_set = set(cards)

        for card in excluded_cards:
            deck_as_set.remove(card)

        combos = list(itertools.combinations(deck_as_set, tuple_size))
        return random.sample(combos, int(len(combos) * sample_size_ratio))
