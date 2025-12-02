#!/usr/bin/env python3
"""Debug the column meanings"""

from itertools import product

def can_make_sum(dice, target_sum):
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

def count_pairings_with_sum(dice, target_sum):
    """Count how many of the 3 pairings have at least one pair with target_sum"""
    d1, d2, d3, d4 = dice
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

all_rolls = list(product(range(1, 7), repeat=4))

# Let's categorize rolls for sum 7
target = 7
print(f"Analyzing sum {target}")
print()

# Categorize by number of pairings that work
by_count = {0: [], 1: [], 2: [], 3: []}
for roll in all_rolls:
    count = count_pairings_with_sum(roll, target)
    by_count[count].append(roll)

print(f"Rolls where 0 pairings work: {len(by_count[0])} (these BUST)")
print(f"Rolls where exactly 1 pairing works: {len(by_count[1])}")
print(f"Rolls where exactly 2 pairings work: {len(by_count[2])}")
print(f"Rolls where all 3 pairings work: {len(by_count[3])}")
print()
print(f"Total that can make sum {target}: {len(by_count[1]) + len(by_count[2]) + len(by_count[3])}")
print()

# Show some examples
print("Examples where exactly 1 pairing works:")
for roll in by_count[1][:5]:
    print(f"  {roll}")

print("\nExamples where exactly 2 pairings work:")
for roll in by_count[2][:5]:
    print(f"  {roll}")

print("\nExamples where all 3 pairings work:")
for roll in by_count[3][:5]:
    print(f"  {roll}")

print()
print("="*60)
print()

# Now check: does ≥1 = (exactly 1) + (exactly 2) + (exactly 3)?
at_least_one = sum(1 for roll in all_rolls if can_make_sum(roll, target))
exactly_one = len(by_count[1])
exactly_two = len(by_count[2])
exactly_three = len(by_count[3])

print(f"≥1 (at least one pairing works): {at_least_one}")
print(f"=1 (exactly one pairing works): {exactly_one}")
print(f"=2 (exactly two pairings work): {exactly_two}")
print(f"=3 (all three pairings work): {exactly_three}")
print()
print(f"Sum check: {exactly_one} + {exactly_two} + {exactly_three} = {exactly_one + exactly_two + exactly_three}")
print(f"Does it equal ≥1? {at_least_one == exactly_one + exactly_two + exactly_three}")
