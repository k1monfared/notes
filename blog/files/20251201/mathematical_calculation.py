#!/usr/bin/env python3
"""Mathematical calculation of P(at least one of 2, 3, 12) without enumeration"""

from itertools import product
from collections import Counter

print("Mathematical Approach: Computing P(at least one of {2, 3, 12})")
print("=" * 70)
print()

# We'll use inclusion-exclusion principle:
# P(A ∪ B ∪ C) = P(A) + P(B) + P(C) - P(A ∩ B) - P(A ∩ C) - P(B ∩ C) + P(A ∩ B ∩ C)
# where A = can make 2, B = can make 3, C = can make 12

print("Step 1: Calculate P(can make each individual sum)")
print("-" * 70)

def count_rolls_with_sum(target_sum):
    """
    Count rolls where at least one of the 3 pairings can make target_sum.

    For a pairing to make target_sum, at least one of its two pairs must sum to target_sum.
    We need: at least one pair (a,b) where a+b = target_sum
    """
    count = 0
    for roll in product(range(1, 7), repeat=4):
        d1, d2, d3, d4 = roll

        # Check all three pairings
        pairings = [
            [(d1, d2), (d3, d4)],
            [(d1, d3), (d2, d4)],
            [(d1, d4), (d2, d3)]
        ]

        # If ANY pairing has the target sum, count this roll
        for pairing in pairings:
            if any(sum(pair) == target_sum for pair in pairing):
                count += 1
                break

    return count

# To make sum S, we need a pair (a, b) where a + b = S
# The pairs that sum to each target:
print("\nPairs needed:")
print("  Sum 2: (1,1)")
print("  Sum 3: (1,2) or (2,1)")
print("  Sum 12: (6,6)")
print()

# Count rolls for each individual sum
n_can_make_2 = count_rolls_with_sum(2)
n_can_make_3 = count_rolls_with_sum(3)
n_can_make_12 = count_rolls_with_sum(12)

total = 6**4
print(f"P(can make 2)  = {n_can_make_2}/{total} = {n_can_make_2/total:.4f}")
print(f"P(can make 3)  = {n_can_make_3}/{total} = {n_can_make_3/total:.4f}")
print(f"P(can make 12) = {n_can_make_12}/{total} = {n_can_make_12/total:.4f}")

print("\n" + "=" * 70)
print("Step 2: Calculate intersections (can make multiple sums)")
print("-" * 70)

def count_rolls_with_sums(target_sums):
    """Count rolls where we can make ALL of the target sums (maybe in different pairings)"""
    count = 0
    for roll in product(range(1, 7), repeat=4):
        d1, d2, d3, d4 = roll

        # For each target sum, check if ANY pairing can make it
        can_make_all = True
        for target in target_sums:
            # Check all three pairings
            pairings = [
                [(d1, d2), (d3, d4)],
                [(d1, d3), (d2, d4)],
                [(d1, d4), (d2, d3)]
            ]

            can_make_this = False
            for pairing in pairings:
                if any(sum(pair) == target for pair in pairing):
                    can_make_this = True
                    break

            if not can_make_this:
                can_make_all = False
                break

        if can_make_all:
            count += 1

    return count

n_can_make_2_and_3 = count_rolls_with_sums([2, 3])
n_can_make_2_and_12 = count_rolls_with_sums([2, 12])
n_can_make_3_and_12 = count_rolls_with_sums([3, 12])
n_can_make_all = count_rolls_with_sums([2, 3, 12])

print(f"P(can make 2 AND 3)   = {n_can_make_2_and_3}/{total} = {n_can_make_2_and_3/total:.4f}")
print(f"P(can make 2 AND 12)  = {n_can_make_2_and_12}/{total} = {n_can_make_2_and_12/total:.4f}")
print(f"P(can make 3 AND 12)  = {n_can_make_3_and_12}/{total} = {n_can_make_3_and_12/total:.4f}")
print(f"P(can make ALL three) = {n_can_make_all}/{total} = {n_can_make_all/total:.4f}")

print("\n" + "=" * 70)
print("Step 3: Apply Inclusion-Exclusion Principle")
print("-" * 70)
print()
print("P(at least one of {2,3,12}) = ")
print("  P(2) + P(3) + P(12)")
print("  - P(2∩3) - P(2∩12) - P(3∩12)")
print("  + P(2∩3∩12)")
print()

n_at_least_one = (n_can_make_2 + n_can_make_3 + n_can_make_12
                  - n_can_make_2_and_3 - n_can_make_2_and_12 - n_can_make_3_and_12
                  + n_can_make_all)

print(f"= {n_can_make_2} + {n_can_make_3} + {n_can_make_12}")
print(f"  - {n_can_make_2_and_3} - {n_can_make_2_and_12} - {n_can_make_3_and_12}")
print(f"  + {n_can_make_all}")
print(f"= {n_at_least_one}")
print()
print(f"P(Success) = {n_at_least_one}/{total} = {n_at_least_one/total:.4f} = {n_at_least_one/total:.1%}")
print(f"P(Bust) = {total - n_at_least_one}/{total} = {(total-n_at_least_one)/total:.4f} = {(total-n_at_least_one)/total:.1%}")

print("\n" + "=" * 70)
print("Verification: Compare with direct enumeration")
print("-" * 70)

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

def can_make_any_sum(dice, target_sums):
    return any(can_make_sum(dice, target) for target in target_sums)

all_rolls = list(product(range(1, 7), repeat=4))
direct_count = sum(1 for roll in all_rolls if can_make_any_sum(roll, [2, 3, 12]))

print(f"Direct enumeration: {direct_count}/{total} = {direct_count/total:.1%}")
print(f"Inclusion-exclusion: {n_at_least_one}/{total} = {n_at_least_one/total:.1%}")
print()
if direct_count == n_at_least_one:
    print("✓ Results match!")
else:
    print("✗ Results don't match - there's an error in the logic")

print("\n" + "=" * 70)
print("Alternative: Computing P(Bust) directly")
print("-" * 70)
print()
print("P(Bust) = P(can't make 2 AND can't make 3 AND can't make 12)")
print("        = 1 - P(at least one of {2,3,12})")
print()
print("This is easier with inclusion-exclusion than computing P(Bust) directly,")
print("because P(Bust) requires all three conditions to fail simultaneously.")
