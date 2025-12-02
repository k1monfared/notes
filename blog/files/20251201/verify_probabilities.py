#!/usr/bin/env python3
"""Verify Can't Stop dice probabilities"""

from itertools import product

def can_make_sum(dice, target_sum):
    """Check if 4 dice can be paired to make at least one pair with target_sum"""
    d1, d2, d3, d4 = dice

    # Three ways to pair 4 dice
    pairs = [
        [(d1, d2), (d3, d4)],
        [(d1, d3), (d2, d4)],
        [(d1, d4), (d2, d3)]
    ]

    for pairing in pairs:
        for pair in pairing:
            if sum(pair) == target_sum:
                return True
    return False

def count_pairings_with_sum(dice, target_sum):
    """Count how many of the 3 pairings have at least one pair with target_sum"""
    d1, d2, d3, d4 = dice

    # Three ways to pair 4 dice
    all_pairings = [
        [(d1, d2), (d3, d4)],
        [(d1, d3), (d2, d4)],
        [(d1, d4), (d2, d3)]
    ]

    count = 0
    for pairing in all_pairings:
        if any(sum(pair) == target_sum for pair in pairing):
            count += 1
    return count

def count_pairings_with_both_pairs_sum(dice, target_sum):
    """Count how many of the 3 pairings have BOTH pairs with target_sum"""
    d1, d2, d3, d4 = dice

    # Three ways to pair 4 dice
    all_pairings = [
        [(d1, d2), (d3, d4)],
        [(d1, d3), (d2, d4)],
        [(d1, d4), (d2, d3)]
    ]

    count = 0
    for pairing in all_pairings:
        if all(sum(pair) == target_sum for pair in pairing):
            count += 1
    return count

def exactly_one_pairing_sum(dice, target_sum):
    """Check if exactly one of the 3 pairings has this sum"""
    return count_pairings_with_sum(dice, target_sum) == 1

def both_pairs_in_pairing(dice, target_sum):
    """Check if at least one pairing has both pairs summing to target_sum"""
    return count_pairings_with_both_pairs_sum(dice, target_sum) > 0

# Generate all possible rolls of 4 dice
all_rolls = list(product(range(1, 7), repeat=4))
total_outcomes = len(all_rolls)

print(f"Total possible outcomes: {total_outcomes}")
print()

# Calculate probabilities for all possible sums (2 through 12)
print("Probabilities for each sum:")
print(f"{'Sum':>3} | {'≥1':>5} | {'=1':>5} | {'=2':>5} | {'=1+2':>6} | {'=1+2*2':>8} | {'Col':>4} | {'N(≥1)':>6} | {'N(=1)':>6} | {'N(=2)':>6} | {'N(1+2)':>7} | {'N(1+2*2)':>9} | {'N(Len)':>7}")
print("-" * 140)

for target_sum in range(2, 13):
    at_least_one = sum(1 for roll in all_rolls if can_make_sum(roll, target_sum))
    exactly_one = sum(1 for roll in all_rolls if exactly_one_pairing_sum(roll, target_sum))
    both_pairs = sum(1 for roll in all_rolls if both_pairs_in_pairing(roll, target_sum))
    one_plus_two = exactly_one + both_pairs
    one_plus_two_times_two = exactly_one + 2 * both_pairs

    # Column length formula: 2n-1, but capped (columns beyond 7 mirror back)
    if target_sum <= 7:
        col_length = 2 * target_sum - 1
    else:
        col_length = 2 * (14 - target_sum) - 1

    # Normalize to sum 2 baseline values
    norm_at_least = at_least_one / 171
    norm_exactly_one = exactly_one / 150
    norm_both_pairs = both_pairs / 1  # sum 2 has both_pairs = 1 (when all dice are 1)
    norm_one_plus_two = one_plus_two / 151
    norm_one_plus_two_times_two = one_plus_two_times_two / 152
    norm_len = col_length / 3

    print(f"{target_sum:>3} | {at_least_one:>5} | {exactly_one:>5} | {both_pairs:>5} | {one_plus_two:>6} | {one_plus_two_times_two:>8} | {col_length:>4} | {norm_at_least:>6.2f} | {norm_exactly_one:>6.2f} | {norm_both_pairs:>6.2f} | {norm_one_plus_two:>7.2f} | {norm_one_plus_two_times_two:>9.2f} | {norm_len:>7.2f}")

print()
print("Specific comparisons:")
can_make_2 = sum(1 for roll in all_rolls if can_make_sum(roll, 2))
can_make_7 = sum(1 for roll in all_rolls if can_make_sum(roll, 7))
exactly_2 = sum(1 for roll in all_rolls if exactly_one_pairing_sum(roll, 2))
exactly_7 = sum(1 for roll in all_rolls if exactly_one_pairing_sum(roll, 7))

print(f"At least one sum of 2: {can_make_2}/{total_outcomes} = {can_make_2/total_outcomes:.4f} ({can_make_2/total_outcomes*100:.2f}%)")
print(f"At least one sum of 7: {can_make_7}/{total_outcomes} = {can_make_7/total_outcomes:.4f} ({can_make_7/total_outcomes*100:.2f}%)")
print(f"Ratio (P(≥1 seven)/P(≥1 two)): {can_make_7/can_make_2:.4f}")
print()
print(f"Exactly one sum of 2: {exactly_2}/{total_outcomes} = {exactly_2/total_outcomes:.4f} ({exactly_2/total_outcomes*100:.2f}%)")
print(f"Exactly one sum of 7: {exactly_7}/{total_outcomes} = {exactly_7/total_outcomes:.4f} ({exactly_7/total_outcomes*100:.2f}%)")
print(f"Ratio (P(=1 seven)/P(=1 two)): {exactly_7/exactly_2:.4f}")
