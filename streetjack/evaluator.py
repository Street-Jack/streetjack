#!/usr/bin/env python3

import random
import itertools
from typing import List, Set, Tuple

import treys


MAX_CARDS = 52
MAX_COMMUNITY_CARDS = 5


class Evaluator():
    def __init__(self):
        self.evaluator = treys.Evaluator()
    
    def effective_hand_strength(self, hand: List[int], board: List[int], shit) -> float:
        hand_strength = self._hand_strenght(hand, board)
        ppot, npot = self._hand_potential(hand, board, shit)

        ehs = hand_strength * (1 - npot) + (1 - hand_strength) * ppot

        return hand_strength * (1 - npot) + (1 - hand_strength) * ppot

    def _hand_strenght(self, hand: List[int], board: List[int]) -> float:
        ahead = tied = behind = 0.0
        our_rank = self._rank(hand, board)

        possible_opp_hands = self._card_combinations(excluded_cards=board+hand, tuple_size=2)

        for opp_hand in possible_opp_hands:
            opp_rank = self._rank(list(opp_hand), board)

            if our_rank < opp_rank:
                ahead += 1.0
            elif our_rank == opp_rank:
                tied += 1.0
            else:
                behind += 1.0
        
        return (ahead + tied / 2.0) / (ahead + tied + behind)

    def _hand_potential(self, hand: List[int], board: List[int], shit) -> (float, float):
        ahead = 0
        tied = 1
        behind = 2

        hp = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
        hp_totals = [0.0, 0.0, 0.0]

        our_rank = self._rank(hand, board)

        possible_opp_hands = self._card_combinations(excluded_cards=hand + board, tuple_size=2)

        num_undrawn_community_cards = MAX_COMMUNITY_CARDS - len(board)
        community_sample_ratios = [1, shit, 0.1]
        community_sample_ratio = community_sample_ratios[num_undrawn_community_cards]

        for opp_hand in possible_opp_hands:
            opp_rank = self._rank(list(opp_hand), board)

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

                our_best = self._rank(hand, new_board)
                opp_best = self._rank(list(opp_hand), new_board)

                if our_best < opp_best:
                    hp[index][ahead] += 1.0
                elif our_best == opp_best:
                    hp[index][tied] += 1.0
                else:
                    hp[index][behind] += 1.0

        ppot = (hp[behind][ahead] + hp[behind][tied] / 2 + hp[tied][ahead] / 2) / (hp_totals[behind] + hp_totals[tied])
        npot = (hp[ahead][behind] + hp[tied][behind] / 2 + hp[ahead][tied] / 2) / (hp_totals[ahead] + hp_totals[tied])

        return ppot, npot

    def _card_combinations(self, excluded_cards: List[int], tuple_size: int, sample_size_ratio: float = 1.0) -> List[Tuple[int]]:
        deck = treys.Deck()
        cards = deck.draw(MAX_CARDS)
        deck_as_set = set(cards)

        for card in excluded_cards:
            deck_as_set.remove(card)

        combos = list(itertools.combinations(deck_as_set, tuple_size))
        return random.sample(combos, int(len(combos) * sample_size_ratio))

    def _rank(self, hand: List[int], board: List[int]) -> int:
        score = self.evaluator.evaluate(hand, board)
        return self.evaluator.get_rank_class(score)


if __name__ == '__main__':
    eval = Evaluator()
    
    deck = treys.Deck()
    hand = deck.draw(2)
    board = deck.draw(4)

    hand_strength1 = eval.effective_hand_strength(hand, board, 0.1)
    print(hand_strength1)
