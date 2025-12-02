#!/usr/bin/env python3
"""Calculate gameplay probabilities for Can't Stop"""

from itertools import product, combinations

def can_make_sum(dice, target_sum):
    """Check if 4 dice can be paired to make at least one pair with target_sum"""
    d1, d2, d3, d4 = dice

    # Three ways to pair 4 dice
    all_pairings = [
        [(d1, d2), (d3, d4)],
        [(d1, d3), (d2, d4)],
        [(d1, d4), (d2, d3)]
    ]

    for pairing in all_pairings:
        for pair in pairing:
            if sum(pair) == target_sum:
                return True
    return False

def can_make_any_sum(dice, target_sums):
    """Check if 4 dice can be paired to make at least one of the target sums"""
    return any(can_make_sum(dice, target) for target in target_sums)

# Generate all possible rolls of 4 dice
all_rolls = list(product(range(1, 7), repeat=4))
total_outcomes = len(all_rolls)

print("Probability of rolling at least one of your active columns (all 3-column combinations):\n")
print(f"{'Columns':>25} | {'P(Success)':>11} | {'P(Bust)':>9}")
print("-" * 55)

# Calculate all 3-column combinations
all_combinations = {}
for combo in combinations(range(2, 13), 3):
    success = sum(1 for roll in all_rolls if can_make_any_sum(roll, combo))
    p_success = success / total_outcomes
    p_bust = 1 - p_success

    # Create symmetric combo (mirror around 7)
    symmetric = tuple(14 - x for x in reversed(combo))

    # Use canonical form (lower one lexicographically)
    canonical = min(combo, symmetric)

    if canonical not in all_combinations:
        # Store both combos if they're different
        if combo != symmetric:
            all_combinations[canonical] = ([combo, symmetric], success, p_success, p_bust)
        else:
            all_combinations[canonical] = ([combo], success, p_success, p_bust)

# Sort by bust probability (ascending - best to worst)
sorted_combinations = sorted(all_combinations.values(), key=lambda x: x[3])

for combos, success, p_success, p_bust in sorted_combinations:
    if len(combos) == 1:
        label = f"{combos[0][0]}, {combos[0][1]}, {combos[0][2]}"
    else:
        label = f"{combos[0][0]}, {combos[0][1]}, {combos[0][2]} / {combos[1][0]}, {combos[1][1]}, {combos[1][2]}"
    print(f"{label:>25} | {p_success:>10.1%} | {p_bust:>8.1%}")
