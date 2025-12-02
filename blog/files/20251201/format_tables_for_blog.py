#!/usr/bin/env python3
"""Format the probability tables for the blog post"""

from itertools import product, combinations

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

def can_make_all_sums(dice, target_sums):
    return all(can_make_sum(dice, target) for target in target_sums)

all_rolls = list(product(range(1, 7), repeat=4))
total = 1296

# Table 1: Individual probabilities
print("### Table 1: Individual Probabilities P(n)")
print()
print("| Sum | Count | P(n) | Percentage | Pairs Needed |")
print("|----:|------:|-----:|-----------:|:-------------|")

for n in range(2, 13):
    count = sum(1 for roll in all_rolls if can_make_sum(roll, n))
    pct = count / total * 100

    pairs = []
    for a in range(1, 7):
        b = n - a
        if 1 <= b <= 6 and a <= b:
            pairs.append(f"({a},{b})")
    pairs_str = ", ".join(pairs)

    print(f"| {n} | {count} | {count}/{total} | {pct:.1f}% | {pairs_str} |")

print()
print("---")
print()

# Table 2: Pairwise intersections (formatted as a matrix)
print("### Table 2: Pairwise Intersections P(n ∩ m)")
print()
print("This table shows the count (out of 1296) of rolls that can make BOTH sum n AND sum m:")
print()

# Create matrix
pairwise = {}
for n in range(2, 13):
    for m in range(2, 13):
        if n < m:
            count = sum(1 for roll in all_rolls if can_make_all_sums(roll, [n, m]))
            pairwise[(n, m)] = count

# Print as matrix
print("| n\\m |", end="")
for m in range(3, 13):
    print(f" {m} |", end="")
print()

print("|----:|", end="")
for m in range(3, 13):
    print("---:|", end="")
print()

for n in range(2, 12):
    print(f"| {n} |", end="")
    for m in range(3, 13):
        if n < m:
            count = pairwise.get((n, m), 0)
            print(f" {count} |", end="")
        else:
            print(" - |", end="")
    print()

print()
print("Note: Read row n, column m to find P(n ∩ m). Diagonal is omitted (would be P(n ∩ n) = P(n)).")
print()
print("---")
print()

# Table 3: Selected triple intersections
print("### Table 3: Selected Triple Intersections P(n ∩ m ∩ q)")
print()
print("Here are some notable triple intersections:")
print()
print("| Sums | Count | P(n∩m∩q) | Percentage |")
print("|:-----|------:|---------:|-----------:|")

# Show examples
examples = [
    (2, 3, 4),
    (2, 3, 12),
    (3, 4, 5),
    (4, 5, 6),
    (5, 6, 7),
    (6, 7, 8),
    (7, 8, 9),
    (8, 9, 10),
    (9, 10, 11),
    (10, 11, 12),
    (4, 7, 10),
    (5, 7, 9),
    (2, 7, 12),
]

for n, m, q in examples:
    count = sum(1 for roll in all_rolls if can_make_all_sums(roll, [n, m, q]))
    pct = count / total * 100
    print(f"| {{{n}, {m}, {q}}} | {count} | {count}/{total} | {pct:.1f}% |")

print()
print("(Full table available in triple_probabilities.csv)")
