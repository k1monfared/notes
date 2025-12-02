#!/usr/bin/env python3
"""Check the distribution of pair counts"""

from itertools import product
from collections import Counter

def count_pairs_with_sum(dice, target_sum):
    """Count how many pairs with target_sum can be made from 4 dice"""
    d1, d2, d3, d4 = dice

    # Three ways to pair 4 dice
    all_pairings = [
        [(d1, d2), (d3, d4)],
        [(d1, d3), (d2, d4)],
        [(d1, d4), (d2, d3)]
    ]

    count = 0
    for pairing in all_pairings:
        for pair in pairing:
            if sum(pair) == target_sum:
                count += 1
    return count

# Generate all possible rolls of 4 dice
all_rolls = list(product(range(1, 7), repeat=4))

for target_sum in [2, 7]:
    print(f"\nDistribution of pair counts for sum {target_sum}:")
    counts = [count_pairs_with_sum(roll, target_sum) for roll in all_rolls]
    distribution = Counter(counts)
    for count_val in sorted(distribution.keys()):
        freq = distribution[count_val]
        print(f"  Count={count_val}: {freq} rolls ({freq/12.96:.1f}%)")
