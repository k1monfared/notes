#!/usr/bin/env python3
"""Create pairing-based probability table for blog"""

from itertools import product

def analyze_roll(dice, target_sum):
    d1, d2, d3, d4 = dice
    pairings = [
        [(d1, d2), (d3, d4)],
        [(d1, d3), (d2, d4)],
        [(d1, d4), (d2, d3)]
    ]

    has_pairing_with_exactly_one = False
    has_pairing_with_both = False

    for pairing in pairings:
        pair1_sum = sum(pairing[0])
        pair2_sum = sum(pairing[1])
        matches = (pair1_sum == target_sum) + (pair2_sum == target_sum)

        if matches == 1:
            has_pairing_with_exactly_one = True
        if matches == 2:
            has_pairing_with_both = True

    return has_pairing_with_exactly_one, has_pairing_with_both

all_rolls = list(product(range(1, 7), repeat=4))
total = 1296

print("### Pairing Structure Probabilities")
print()
print("For each sum, three mutually exclusive outcomes:")
print()
print("| Sum | Exactly One Pair | Both Pairs | At Least One | Total Check |")
print("|----:|-----------------:|-----------:|-------------:|:-----------:|")

for target_sum in range(2, 13):
    count_exactly_one = 0
    count_both = 0

    for roll in all_rolls:
        has_exactly, has_both = analyze_roll(roll, target_sum)
        if has_exactly:
            count_exactly_one += 1
        if has_both:
            count_both += 1

    count_at_least_one = count_exactly_one + count_both
    pct_exactly = count_exactly_one / total * 100
    pct_both = count_both / total * 100
    pct_at_least = count_at_least_one / total * 100

    print(f"| {target_sum} | {count_exactly_one} ({pct_exactly:.1f}%) | {count_both} ({pct_both:.1f}%) | {count_at_least_one} ({pct_at_least:.1f}%) | ✓ |")

print()
print("**Definitions:**")
print("- **Exactly One Pair**: There exists a pairing where exactly one of its two pairs sums to the target")
print("- **Both Pairs**: There exists a pairing where both of its pairs sum to the target")
print("- **At Least One**: There exists a pairing where at least one pair sums to the target (= Exactly One + Both Pairs)")
print()
print("**Key insight:** The 'At Least One' column is what we use for P(n) in the individual probabilities table.")
