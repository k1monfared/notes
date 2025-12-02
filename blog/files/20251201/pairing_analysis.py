#!/usr/bin/env python3
"""Analyze probabilities based on pairing structure"""

from itertools import product

def analyze_roll(dice, target_sum):
    """
    For a roll, check all 3 pairings and return info about each.
    Returns (has_exactly_one, has_both, has_at_least_one)
    """
    d1, d2, d3, d4 = dice

    pairings = [
        [(d1, d2), (d3, d4)],
        [(d1, d3), (d2, d4)],
        [(d1, d4), (d2, d3)]
    ]

    has_pairing_with_exactly_one = False
    has_pairing_with_both = False
    has_pairing_with_at_least_one = False

    for pairing in pairings:
        pair1_sum = sum(pairing[0])
        pair2_sum = sum(pairing[1])

        matches = (pair1_sum == target_sum) + (pair2_sum == target_sum)

        if matches == 1:
            has_pairing_with_exactly_one = True
        if matches == 2:
            has_pairing_with_both = True
        if matches >= 1:
            has_pairing_with_at_least_one = True

    return has_pairing_with_exactly_one, has_pairing_with_both, has_pairing_with_at_least_one

# Generate all possible rolls
all_rolls = list(product(range(1, 7), repeat=4))
total = len(all_rolls)

print("Pairing-Based Probability Analysis")
print("=" * 80)
print()
print("For each sum, we compute:")
print("  P(exactly one): exists a pairing where exactly ONE pair sums to target")
print("  P(both pairs):  exists a pairing where BOTH pairs sum to target")
print("  P(at least one): exists a pairing where at least one pair sums to target")
print()
print(f"{'Sum':>3} | {'Exactly One':>12} | {'Both Pairs':>12} | {'At Least One':>14} | {'Verify':>7}")
print("-" * 80)

for target_sum in range(2, 13):
    count_exactly_one = 0
    count_both = 0
    count_at_least_one = 0

    for roll in all_rolls:
        has_exactly, has_both, has_at_least = analyze_roll(roll, target_sum)

        if has_exactly:
            count_exactly_one += 1
        if has_both:
            count_both += 1
        if has_at_least:
            count_at_least_one += 1

    # Verify: at_least_one should equal the union of exactly_one and both
    # But they can overlap! A roll can have BOTH types of pairings
    # So we need to check the actual relationship

    # Count rolls with exactly_one OR both (union)
    count_union = 0
    for roll in all_rolls:
        has_exactly, has_both, has_at_least = analyze_roll(roll, target_sum)
        if has_exactly or has_both:
            count_union += 1

    verify = "✓" if count_union == count_at_least_one else "✗"

    print(f"{target_sum:>3} | {count_exactly_one:>5}/{total:<4} | {count_both:>5}/{total:<4} | {count_at_least_one:>6}/{total:<4} | {verify:>7}")

print()
print("Note: 'Exactly One' and 'Both Pairs' are NOT mutually exclusive!")
print("A single roll can have one pairing with exactly one match AND another pairing with both matches.")
print()

# Show example for sum 7
print("=" * 80)
print("Example: Sum 7")
print("-" * 80)

target = 7
examples = {
    'exactly_only': [],
    'both_only': [],
    'both_types': [],
    'neither': []
}

for roll in all_rolls:
    has_exactly, has_both, has_at_least = analyze_roll(roll, target)

    if has_exactly and has_both:
        if len(examples['both_types']) < 3:
            examples['both_types'].append(roll)
    elif has_exactly:
        if len(examples['exactly_only']) < 3:
            examples['exactly_only'].append(roll)
    elif has_both:
        if len(examples['both_only']) < 3:
            examples['both_only'].append(roll)
    elif not has_at_least:
        if len(examples['neither']) < 3:
            examples['neither'].append(roll)

print("\nRolls with pairing containing EXACTLY ONE sum of 7 (but no pairing with both):")
for roll in examples['exactly_only']:
    d1, d2, d3, d4 = roll
    print(f"  {roll}: ", end="")
    pairings = [
        [(d1, d2), (d3, d4)],
        [(d1, d3), (d2, d4)],
        [(d1, d4), (d2, d3)]
    ]
    for i, pairing in enumerate(pairings):
        s1, s2 = sum(pairing[0]), sum(pairing[1])
        matches = (s1 == 7) + (s2 == 7)
        if matches == 1:
            print(f"P{i+1}:({s1},{s2})* ", end="")
        else:
            print(f"P{i+1}:({s1},{s2}) ", end="")
    print()

print("\nRolls with pairing where BOTH pairs sum to 7 (but no pairing with exactly one):")
for roll in examples['both_only']:
    d1, d2, d3, d4 = roll
    print(f"  {roll}: ", end="")
    pairings = [
        [(d1, d2), (d3, d4)],
        [(d1, d3), (d2, d4)],
        [(d1, d4), (d2, d3)]
    ]
    for i, pairing in enumerate(pairings):
        s1, s2 = sum(pairing[0]), sum(pairing[1])
        matches = (s1 == 7) + (s2 == 7)
        if matches == 2:
            print(f"P{i+1}:({s1},{s2})** ", end="")
        else:
            print(f"P{i+1}:({s1},{s2}) ", end="")
    print()

print("\nRolls with BOTH types (one pairing with exactly one, another pairing with both):")
for roll in examples['both_types']:
    d1, d2, d3, d4 = roll
    print(f"  {roll}: ", end="")
    pairings = [
        [(d1, d2), (d3, d4)],
        [(d1, d3), (d2, d4)],
        [(d1, d4), (d2, d3)]
    ]
    for i, pairing in enumerate(pairings):
        s1, s2 = sum(pairing[0]), sum(pairing[1])
        matches = (s1 == 7) + (s2 == 7)
        if matches == 1:
            print(f"P{i+1}:({s1},{s2})* ", end="")
        elif matches == 2:
            print(f"P{i+1}:({s1},{s2})** ", end="")
        else:
            print(f"P{i+1}:({s1},{s2}) ", end="")
    print()

print("\n* = exactly one pair sums to 7")
print("** = both pairs sum to 7")

# Calculate the overlap
print()
print("=" * 80)
print("Overlap Analysis for Sum 7:")
print("-" * 80)

count_only_exactly = 0
count_only_both = 0
count_both_types = 0

for roll in all_rolls:
    has_exactly, has_both, _ = analyze_roll(roll, 7)
    if has_exactly and has_both:
        count_both_types += 1
    elif has_exactly:
        count_only_exactly += 1
    elif has_both:
        count_only_both += 1

print(f"Rolls with only 'exactly one' pairings: {count_only_exactly}")
print(f"Rolls with only 'both pairs' pairings: {count_only_both}")
print(f"Rolls with both types: {count_both_types}")
print(f"Total (union): {count_only_exactly + count_only_both + count_both_types}")
print(f"This equals P(at least one): 834? {count_only_exactly + count_only_both + count_both_types == 834}")
