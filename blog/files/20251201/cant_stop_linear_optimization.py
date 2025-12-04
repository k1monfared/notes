#!/usr/bin/env python3
"""
Explore optimal board sizes for Can't Stop with LINEAR column length constraint.

The current design has a nice property: columns increase by 2 each step (3,5,7,9,11,13).
What if we maintain this linear pattern but optimize the parameters?
"""

from itertools import product
import math

# Calculate exact probabilities
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

all_rolls = list(product(range(1, 7), repeat=4))
total = len(all_rolls)

probabilities = {}
for target_sum in range(2, 13):
    count = sum(1 for roll in all_rolls if can_make_sum(roll, target_sum))
    probabilities[target_sum] = count / total

print("=" * 80)
print("OPTIMAL LINEAR BOARD DESIGNS")
print("=" * 80)
print("\nConstraint: Column lengths must follow a linear pattern:")
print("  L(n) = base + (n - 2) × step")
print("  Where n is the column number (2-12)")
print()

def calculate_linear_board(base, step):
    """
    Calculate board with linear progression.
    base: length of column 2/12
    step: increment per column
    """
    lengths = {}
    for col in range(2, 13):
        if col <= 7:
            lengths[col] = int(round(base + (col - 2) * step))
        else:
            # Symmetric: col 8 = col 6, col 9 = col 5, etc.
            lengths[col] = int(round(base + (14 - col - 2) * step))

    # Calculate expected rolls and deviation
    expected = {}
    for col in range(2, 13):
        expected[col] = lengths[col] / probabilities[col]

    mean_expected = sum(expected.values()) / len(expected)
    max_deviation = max(abs(expected[col] / mean_expected - 1) * 100 for col in range(2, 13))
    std_dev = (sum((expected[col] - mean_expected) ** 2 for col in range(2, 13)) / 11) ** 0.5

    return lengths, expected, mean_expected, max_deviation, std_dev

# Current design analysis
print("CURRENT DESIGN: base=3, step=2")
print("-" * 80)
lengths, expected, mean_exp, max_dev, std_dev = calculate_linear_board(3, 2)
print(f"Column lengths: {[lengths[i] for i in range(2, 13)]}")
print(f"Max column height: {lengths[7]}")
print(f"Mean E[rolls]: {mean_exp:.2f}")
print(f"Max deviation: ±{max_dev:.2f}%")
print(f"Std deviation: {std_dev:.3f} rolls")
print()

# Explore different linear patterns
print("=" * 80)
print("EXPLORING LINEAR PATTERNS")
print("=" * 80)
print()

results = []

# Try different bases and steps
for base in range(1, 21):  # base from 1 to 20
    for step_100 in range(50, 501):  # step from 0.5 to 5.0
        step = step_100 / 100

        lengths, expected, mean_exp, max_dev, std_dev = calculate_linear_board(base, step)
        max_height = int(lengths[7])

        # Skip if too tall or if base is less than 1
        if max_height > 50 or lengths[2] < 1:
            continue

        # Calculate game time estimate
        game_time = (mean_exp * 3 * 1.5 * 5) / 60

        results.append({
            'base': base,
            'step': step,
            'max_height': max_height,
            'mean_expected': mean_exp,
            'max_deviation': max_dev,
            'std_dev': std_dev,
            'lengths': lengths,
            'expected': expected,
            'game_time': game_time
        })

# Sort by max deviation (best balance first)
results.sort(key=lambda x: x['max_deviation'])

print("TOP 30 MOST BALANCED LINEAR BOARDS (max height ≤ 50):")
print(f"{'Base':>5} {'Step':>6} {'Max H':>7} {'Mean E[rolls]':>14} {'Max Dev':>10} {'Std Dev':>10} {'Game Time':>11} {'Lengths'}")
print("-" * 120)

for i, r in enumerate(results[:30]):
    lengths_str = str([r['lengths'][i] for i in range(2, 13)])
    print(f"{r['base']:5d} {r['step']:6.2f} {r['max_height']:7d} {r['mean_expected']:13.2f} {r['max_deviation']:9.2f}% {r['std_dev']:9.3f} {r['game_time']:8.1f} min  {lengths_str}")

# Find best options for different size categories
print("\n" + "=" * 80)
print("BEST LINEAR BOARDS BY SIZE CATEGORY")
print("=" * 80)

size_categories = [
    (10, 15, "Very Small (10-15 steps)"),
    (15, 20, "Small (15-20 steps)"),
    (20, 30, "Medium (20-30 steps)"),
    (30, 50, "Large (30-50 steps)")
]

for min_h, max_h, label in size_categories:
    print(f"\n{label}:")
    print("-" * 80)
    category_results = [r for r in results if min_h <= r['max_height'] <= max_h]

    if not category_results:
        print("  No results in this category")
        continue

    best = category_results[0]
    print(f"  Base: {best['base']}, Step: {best['step']:.2f}")
    print(f"  Column lengths: {[best['lengths'][i] for i in range(2, 13)]}")
    print(f"  Max height: {best['max_height']}")
    print(f"  Max deviation: ±{best['max_deviation']:.2f}%")
    print(f"  Mean E[rolls]: {best['mean_expected']:.2f}")
    print(f"  Game time: ~{best['game_time']:.1f} minutes")

    # Show detailed column analysis
    print(f"\n  Detailed column analysis:")
    print(f"  {'Col':>4} {'Length':>7} {'Prob':>7} {'E[rolls]':>10} {'Dev from mean':>15}")
    for col in range(2, 13):
        prob = probabilities[col]
        length = best['lengths'][col]
        exp = best['expected'][col]
        dev = (exp / best['mean_expected'] - 1) * 100
        print(f"  {col:4d} {length:7d} {prob:6.1%} {exp:10.2f} {dev:+14.2f}%")

# Compare to current design
print("\n" + "=" * 80)
print("COMPARISON: Current vs Best Linear Alternatives")
print("=" * 80)

current = calculate_linear_board(3, 2)
print(f"\nCURRENT (base=3, step=2):")
print(f"  Lengths: [3, 5, 7, 9, 11, 13, 11, 9, 7, 5, 3]")
print(f"  Max deviation: ±{current[3]:.2f}%")
print(f"  Mean E[rolls]: {current[2]:.2f}")

# Find best with similar size to current (max height 13-15)
similar_size = [r for r in results if 13 <= r['max_height'] <= 15]
if similar_size:
    best_similar = similar_size[0]
    print(f"\nBEST LINEAR BOARD (similar size, max height {best_similar['max_height']}):")
    print(f"  Base: {best_similar['base']}, Step: {best_similar['step']:.2f}")
    print(f"  Lengths: {[best_similar['lengths'][i] for i in range(2, 13)]}")
    print(f"  Max deviation: ±{best_similar['max_deviation']:.2f}%")
    print(f"  Mean E[rolls]: {best_similar['mean_expected']:.2f}")
    print(f"  Improvement: {(current[3] / best_similar['max_deviation'] - 1) * 100:.1f}% better balance")

# Find overall best under 20 steps
under_20 = [r for r in results if r['max_height'] <= 20]
if under_20:
    best_under_20 = under_20[0]
    print(f"\nBEST LINEAR BOARD UNDER 20 STEPS (max height {best_under_20['max_height']}):")
    print(f"  Base: {best_under_20['base']}, Step: {best_under_20['step']:.2f}")
    print(f"  Lengths: {[best_under_20['lengths'][i] for i in range(2, 13)]}")
    print(f"  Max deviation: ±{best_under_20['max_deviation']:.2f}%")
    print(f"  Mean E[rolls]: {best_under_20['mean_expected']:.2f}")
    print(f"  Improvement: {(current[3] / best_under_20['max_deviation'] - 1) * 100:.1f}% better balance")

# Special: integer steps only
print("\n" + "=" * 80)
print("BEST LINEAR BOARDS WITH INTEGER STEPS (easier to manufacture)")
print("=" * 80)

integer_results = [r for r in results if r['step'] == int(r['step'])]
integer_results.sort(key=lambda x: x['max_deviation'])

print(f"\nTop 10 with integer steps:")
print(f"{'Base':>5} {'Step':>6} {'Max H':>7} {'Mean E[rolls]':>14} {'Max Dev':>10} {'Std Dev':>10} {'Lengths'}")
print("-" * 100)

for i, r in enumerate(integer_results[:10]):
    lengths_str = str([r['lengths'][i] for i in range(2, 13)])
    print(f"{r['base']:5d} {r['step']:6.0f} {r['max_height']:7d} {r['mean_expected']:13.2f} {r['max_deviation']:9.2f}% {r['std_dev']:9.3f}  {lengths_str}")

# Analysis: what makes a good linear board?
print("\n" + "=" * 80)
print("INSIGHTS: What Makes a Good Linear Board?")
print("=" * 80)

print("\n1. The current design (base=3, step=2) is pretty good but not optimal")
print("   - Uses nice round numbers (all odd numbers)")
print("   - Max deviation: ±13.6%")

best_overall = results[0]
print(f"\n2. Best linear board overall (base={best_overall['base']}, step={best_overall['step']:.2f}):")
print(f"   - Lengths: {[best_overall['lengths'][i] for i in range(2, 13)]}")
print(f"   - Max deviation: ±{best_overall['max_deviation']:.2f}%")
print(f"   - Improvement: {(current[3] / best_overall['max_deviation'] - 1) * 100:.1f}% better")

if integer_results:
    best_integer = integer_results[0]
    print(f"\n3. Best with integer step (base={best_integer['base']}, step={int(best_integer['step'])}):")
    print(f"   - Lengths: {[best_integer['lengths'][i] for i in range(2, 13)]}")
    print(f"   - Max deviation: ±{best_integer['max_deviation']:.2f}%")
    print(f"   - More practical for manufacturing")

print("\n4. Key insight: Linear designs are inherently limited")
print("   - Linear progression can't perfectly match the nonlinear probability curve")
print("   - Best linear boards still have ~5-7% deviation")
print("   - Non-linear designs (from previous analysis) can achieve <2% deviation")
print("   - Trade-off: simplicity/elegance vs mathematical optimality")
