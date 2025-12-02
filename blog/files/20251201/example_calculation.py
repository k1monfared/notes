#!/usr/bin/env python3
"""Example calculation: probability of rolling at least one of 2, 3, or 12"""

from itertools import product

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

print("Example: Calculating probability for columns 2, 3, 12")
print("=" * 60)
print()

# Target columns
target_columns = [2, 3, 12]

print(f"Target columns: {target_columns}")
print()
print("To make sum 2: need a pair (1,1)")
print("To make sum 3: need a pair (1,2) or (2,1)")
print("To make sum 12: need a pair (6,6)")
print()

# Let's look at a few example rolls
print("Example rolls:")
print("-" * 60)

examples = [
    (1, 1, 1, 1),  # Can make 2
    (1, 2, 3, 4),  # Can make 3
    (6, 6, 6, 6),  # Can make 12
    (1, 1, 6, 6),  # Can make 2 and 12
    (2, 3, 4, 5),  # Can't make any of them (BUST!)
]

for roll in examples:
    d1, d2, d3, d4 = roll
    print(f"\nRoll: {roll}")

    # Check all three pairings
    pairings = [
        [(d1, d2), (d3, d4)],
        [(d1, d3), (d2, d4)],
        [(d1, d4), (d2, d3)]
    ]

    pairing_names = [
        f"({d1},{d2}) + ({d3},{d4})",
        f"({d1},{d3}) + ({d2},{d4})",
        f"({d1},{d4}) + ({d2},{d3})"
    ]

    can_make = []
    for i, pairing in enumerate(pairings):
        sums = [sum(pair) for pair in pairing]
        hits = [s for s in sums if s in target_columns]
        print(f"  Pairing {i+1}: {pairing_names[i]} = {sums[0]} + {sums[1]}", end="")
        if hits:
            print(f" ✓ (can make {hits})")
            can_make.extend(hits)
        else:
            print(" ✗")

    if can_make:
        print(f"  Result: SUCCESS (can make {sorted(set(can_make))})")
    else:
        print(f"  Result: BUST (can't make any of {target_columns})")

print()
print("=" * 60)
print("Full calculation across all 1296 possible rolls:")
print("-" * 60)

# Count successes
success_count = sum(1 for roll in all_rolls if can_make_any_sum(roll, target_columns))
bust_count = total_outcomes - success_count

p_success = success_count / total_outcomes
p_bust = bust_count / total_outcomes

print(f"Total possible rolls: {total_outcomes}")
print(f"Rolls that can make at least one of {target_columns}: {success_count}")
print(f"Rolls that BUST (can't make any): {bust_count}")
print()
print(f"P(Success) = {success_count}/{total_outcomes} = {p_success:.1%}")
print(f"P(Bust) = {bust_count}/{total_outcomes} = {p_bust:.1%}")
print()
print("This is the WORST combination in the game!")
