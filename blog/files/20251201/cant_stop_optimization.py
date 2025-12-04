#!/usr/bin/env python3
"""
Explore optimal board sizes for Can't Stop to minimize deviation from perfect balance.

Given probabilities for each column, find the best scaling factors that:
1. Minimize deviation from equal expected rolls
2. Keep board sizes practical for gameplay
"""

from itertools import product
import math

# Calculate exact probabilities from the blog post
def can_make_sum(dice, target_sum):
    """Check if 4 dice can be paired to make target_sum"""
    d1, d2, d3, d4 = dice
    pairings = [
        [(d1, d2), (d3, d4)],
        [(d1, d3), (d2, d4)],
        [(d1, d4), (d2, d3)]
    ]
    for pairing in pairings:
        for pair in pairing:
            if sum(pair) == target_sum:
                return True
    return False

# Calculate all probabilities
all_rolls = list(product(range(1, 7), repeat=4))
total = len(all_rolls)  # 1296

probabilities = {}
for target_sum in range(2, 13):
    count = sum(1 for roll in all_rolls if can_make_sum(roll, target_sum))
    probabilities[target_sum] = count / total

print("Column Probabilities:")
print("=" * 60)
for col, prob in probabilities.items():
    print(f"Column {col:2d}: {prob:.6f} ({prob * total:.0f}/1296)")
print()

# Current board design
current_lengths = {2: 3, 3: 5, 4: 7, 5: 9, 6: 11, 7: 13, 8: 11, 9: 9, 10: 7, 11: 5, 12: 3}

print("Current Board Design:")
print("=" * 60)
expected_rolls = {}
for col in range(2, 13):
    expected = current_lengths[col] / probabilities[col]
    expected_rolls[col] = expected
    deviation = (expected / 20 - 1) * 100
    print(f"Column {col:2d}: Length={current_lengths[col]:2d}, E[rolls]={expected:5.2f}, Dev={deviation:+5.1f}%")

mean_expected = sum(expected_rolls.values()) / len(expected_rolls)
print(f"\nMean E[rolls]: {mean_expected:.2f}")
print()

# Find optimal integer lengths for different scaling factors
def find_optimal_lengths(scale_factor, target_expected_rolls=None):
    """
    Find optimal integer column lengths for a given scale factor.
    If target_expected_rolls is None, use the mean that minimizes total deviation.
    """
    if target_expected_rolls is None:
        # Find the target that minimizes total squared deviation
        # Try different targets
        best_target = None
        best_deviation = float('inf')

        for target in range(10, 100):
            total_squared_dev = 0
            for col in range(2, 13):
                optimal_length = target * probabilities[col]
                rounded_length = max(1, round(optimal_length * scale_factor))
                actual_expected = rounded_length / probabilities[col]
                total_squared_dev += (actual_expected - target) ** 2

            if total_squared_dev < best_deviation:
                best_deviation = total_squared_dev
                best_target = target

        target_expected_rolls = best_target

    lengths = {}
    expected = {}

    for col in range(2, 13):
        optimal_length = target_expected_rolls * probabilities[col]
        rounded_length = max(1, round(optimal_length * scale_factor))
        lengths[col] = rounded_length
        expected[col] = rounded_length / probabilities[col]

    return lengths, expected, target_expected_rolls

print("Exploring Different Board Scales:")
print("=" * 80)

scales_to_try = [0.5, 1, 1.5, 2, 3, 5, 10, 20, 50, 100]

results = []

for scale in scales_to_try:
    lengths, expected, target = find_optimal_lengths(scale)

    # Calculate statistics
    max_length = max(lengths.values())
    mean_expected = sum(expected.values()) / len(expected)
    max_deviation = max(abs(expected[col] / mean_expected - 1) * 100 for col in range(2, 13))
    std_dev = (sum((expected[col] - mean_expected) ** 2 for col in range(2, 13)) / 11) ** 0.5

    results.append({
        'scale': scale,
        'max_length': max_length,
        'mean_expected': mean_expected,
        'max_deviation': max_deviation,
        'std_dev': std_dev,
        'lengths': lengths,
        'expected': expected
    })

    print(f"\nScale Factor: {scale:g}x")
    print(f"Max Column Length: {max_length}")
    print(f"Mean E[rolls]: {mean_expected:.2f}")
    print(f"Max Deviation: ±{max_deviation:.2f}%")
    print(f"Std Dev: {std_dev:.3f} rolls")
    print(f"Column lengths: {list(lengths.values())}")

# Find interesting small scales with low deviation
print("\n" + "=" * 80)
print("DETAILED ANALYSIS: Small Boards with Low Deviation")
print("=" * 80)

# Try all small scales from 0.1 to 5.0
detailed_results = []
for scale_100 in range(10, 501):  # 0.1 to 5.0 in steps of 0.01
    scale = scale_100 / 100
    lengths, expected, target = find_optimal_lengths(scale)

    max_length = max(lengths.values())
    if max_length > 50:  # Skip if too tall
        continue

    mean_expected = sum(expected.values()) / len(expected)
    max_deviation = max(abs(expected[col] / mean_expected - 1) * 100 for col in range(2, 13))
    std_dev = (sum((expected[col] - mean_expected) ** 2 for col in range(2, 13)) / 11) ** 0.5

    detailed_results.append({
        'scale': scale,
        'max_length': max_length,
        'mean_expected': mean_expected,
        'max_deviation': max_deviation,
        'std_dev': std_dev,
        'lengths': lengths,
        'expected': expected
    })

# Sort by max_deviation to find best options
detailed_results.sort(key=lambda x: x['max_deviation'])

print("\nTop 20 Most Balanced Board Sizes (max height ≤ 50):")
print(f"{'Scale':>6} {'Max Len':>8} {'Mean E[rolls]':>14} {'Max Dev':>10} {'Std Dev':>10} {'Column Lengths'}")
print("-" * 100)

for i, result in enumerate(detailed_results[:20]):
    lengths_str = str(list(result['lengths'].values()))
    print(f"{result['scale']:6.2f}x {result['max_length']:7d} {result['mean_expected']:13.2f} {result['max_deviation']:9.2f}% {result['std_dev']:9.3f}  {lengths_str}")

# Zero deviation analysis
print("\n" + "=" * 80)
print("PERFECT BALANCE ANALYSIS")
print("=" * 80)

# For perfect balance, we need L(n) = k * P(n) for all n
# The ideal length is k * P(n) where k is the target expected rolls
# To avoid rounding errors, we need a scale where all k * P(n) are integers

# Find LCM-based solution
from math import gcd
from functools import reduce

def lcm(a, b):
    return abs(a * b) // gcd(a, b)

# Get probability numerators (all have denominator 1296)
prob_numerators = {col: round(probabilities[col] * 1296) for col in range(2, 13)}
print("\nProbability numerators (denominator = 1296):")
for col in range(2, 13):
    print(f"  Column {col:2d}: {prob_numerators[col]}/1296")

# To get perfect integer ratios, we need k * (numerator/1296) to be integer for all numerators
# This means k must be a multiple of 1296 / gcd(all numerators)
all_numerators = list(prob_numerators.values())
numerators_gcd = reduce(gcd, all_numerators)
print(f"\nGCD of all numerators: {numerators_gcd}")
print(f"Simplified denominator: {1296 // numerators_gcd}")

# Minimum k that makes all lengths integers
min_k = 1296 // numerators_gcd
print(f"\nMinimum k for perfect integer lengths: {min_k}")

perfect_lengths = {}
for col in range(2, 13):
    perfect_lengths[col] = (min_k * prob_numerators[col]) // 1296

print(f"\nPerfect lengths (all columns have exactly E[rolls] = {min_k}):")
for col in range(2, 13):
    print(f"  Column {col:2d}: {perfect_lengths[col]:4d} steps")

print(f"\nMax column height for perfect balance: {max(perfect_lengths.values())}")

# Calculate how long it would take to play
print("\n" + "=" * 80)
print("GAMEPLAY DURATION ESTIMATES")
print("=" * 80)

def estimate_game_duration(max_length, mean_expected_rolls):
    """
    Estimate how long a game would take.

    Assumptions:
    - Need to complete 3 columns to win
    - Average combination has ~85% success rate (between bad and good combos)
    - Each roll takes ~5 seconds (pick up dice, roll, decide, move markers)
    - Each turn has on average ~6 successful rolls before busting or stopping
    """

    # Rolls needed to complete one column (on average)
    rolls_per_column = mean_expected_rolls

    # In practice, you're working on 3 columns simultaneously
    # But you need to complete 3 specific columns
    # Rough estimate: 1.5x the single column time for all 3
    # (because of parallel progress but also conflicts and strategic choices)
    total_rolls_needed = rolls_per_column * 3 * 1.5

    # Time per roll (including decision time)
    seconds_per_roll = 5

    # Convert to minutes
    total_time_minutes = (total_rolls_needed * seconds_per_roll) / 60

    return total_time_minutes

current_game_time = estimate_game_duration(13, 20)
print(f"\nCurrent board (max length 13):")
print(f"  Estimated game duration: {current_game_time:.1f} minutes ({current_game_time/60:.1f} hours)")

for result in detailed_results[:10]:
    game_time = estimate_game_duration(result['max_length'], result['mean_expected'])
    print(f"\nScale {result['scale']:.2f}x (max length {result['max_length']}):")
    print(f"  Max deviation: ±{result['max_deviation']:.2f}%")
    print(f"  Estimated game duration: {game_time:.1f} minutes ({game_time/60:.2f} hours)")

perfect_game_time = estimate_game_duration(max(perfect_lengths.values()), min_k)
print(f"\nPerfect balance board (max length {max(perfect_lengths.values())}):")
print(f"  Estimated game duration: {perfect_game_time:.1f} minutes ({perfect_game_time/60:.1f} hours)")

# Find "sweet spot" boards
print("\n" + "=" * 80)
print("SWEET SPOT RECOMMENDATIONS")
print("=" * 80)

print("\nBoards with <5% max deviation and reasonable play time (<60 min):")
print(f"{'Scale':>6} {'Max Len':>8} {'Max Dev':>10} {'Game Time':>12} {'Column Lengths'}")
print("-" * 100)

sweet_spots = []
for result in detailed_results:
    game_time = estimate_game_duration(result['max_length'], result['mean_expected'])
    if result['max_deviation'] < 5.0 and game_time < 60:
        sweet_spots.append({**result, 'game_time': game_time})
        lengths_str = str(list(result['lengths'].values()))
        print(f"{result['scale']:6.2f}x {result['max_length']:7d} {result['max_deviation']:9.2f}% {game_time:9.1f} min  {lengths_str}")

if sweet_spots:
    best = sweet_spots[0]
    print(f"\n⭐ RECOMMENDED: Scale {best['scale']:.2f}x")
    print(f"   Max column length: {best['max_length']}")
    print(f"   Max deviation: ±{best['max_deviation']:.2f}%")
    print(f"   Estimated game time: {best['game_time']:.1f} minutes")
    print(f"   Column lengths: {list(best['lengths'].values())}")
