#!/usr/bin/env python3
"""Debug the counting logic"""

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

# Test cases
test_cases = [
    (1, 1, 6, 6),  # Should have 2 ways to make a 2
    (1, 1, 1, 6),  # Should have multiple ways to make a 2
    (3, 4, 3, 4),  # Should have multiple ways to make a 7
    (2, 5, 2, 5),  # Should have multiple ways to make a 7
]

for dice in test_cases:
    print(f"\nDice: {dice}")
    for target in [2, 7]:
        count = count_pairs_with_sum(dice, target)
        print(f"  Count for sum {target}: {count}")

        # Show the pairings
        d1, d2, d3, d4 = dice
        all_pairings = [
            [(d1, d2), (d3, d4)],
            [(d1, d3), (d2, d4)],
            [(d1, d4), (d2, d3)]
        ]
        for i, pairing in enumerate(all_pairings, 1):
            sums = [sum(p) for p in pairing]
            has_target = target in sums
            print(f"    Pairing {i}: {pairing[0]}={sums[0]}, {pairing[1]}={sums[1]} {'✓' if has_target else ''}")
