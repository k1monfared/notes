#!/usr/bin/env python3
"""Generate complete probability tables for all sums"""

from itertools import product, combinations

def can_make_sum(dice, target_sum):
    """Check if 4 dice can be paired to make at least one pair with target_sum"""
    d1, d2, d3, d4 = dice

    # Three ways to pair 4 dice
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
    """Check if 4 dice can make ALL of the target sums (in possibly different pairings)"""
    return all(can_make_sum(dice, target) for target in target_sums)

# Generate all possible rolls of 4 dice
all_rolls = list(product(range(1, 7), repeat=4))
total_outcomes = len(all_rolls)

print("=" * 80)
print("PROBABILITY REFERENCE TABLES FOR CAN'T STOP")
print("=" * 80)
print()

# Table 1: Individual probabilities P(n)
print("Table 1: P(can make sum n) for n = 2, 3, ..., 12")
print("-" * 80)
print(f"{'Sum':>5} | {'Count':>6} | {'P(n)':>10} | {'Decimal':>10} | {'Pairs needed'}")
print("-" * 80)

individual_counts = {}
for n in range(2, 13):
    count = sum(1 for roll in all_rolls if can_make_sum(roll, n))
    individual_counts[n] = count
    prob = count / total_outcomes

    # Determine pairs needed
    pairs = []
    for a in range(1, 7):
        b = n - a
        if 1 <= b <= 6 and a <= b:
            if a == b:
                pairs.append(f"({a},{b})")
            else:
                pairs.append(f"({a},{b})")
    pairs_str = ", ".join(pairs)

    print(f"{n:>5} | {count:>6} | {count:>4}/{total_outcomes:<4} | {prob:>9.4f} | {pairs_str}")

print()
print("Observations:")
print("  - P(7) = 64.4% is the highest (most pairs work)")
print("  - P(2) = P(12) = 13.2% by symmetry (only one pair each)")
print("  - P(n) = P(14-n) by symmetry around 7")
print()

# Table 2: Pairwise intersections P(n ∩ m)
print("=" * 80)
print("Table 2: P(can make sum n AND sum m) for all pairs (n,m)")
print("-" * 80)
print()

pairwise_counts = {}
print(f"{'n':>3} | {'m':>3} | {'Count':>6} | {'P(n∩m)':>10} | {'Decimal':>10}")
print("-" * 70)

for n, m in combinations(range(2, 13), 2):
    count = sum(1 for roll in all_rolls if can_make_all_sums(roll, [n, m]))
    pairwise_counts[(n, m)] = count
    prob = count / total_outcomes
    print(f"{n:>3} | {m:>3} | {count:>6} | {count:>4}/{total_outcomes:<4} | {prob:>9.4f}")

print()
print(f"Total pairwise combinations: {len(pairwise_counts)}")
print()

# Table 3: Triple intersections P(n ∩ m ∩ q)
print("=" * 80)
print("Table 3: P(can make sum n AND sum m AND sum q) for all triples (n,m,q)")
print("-" * 80)
print()

triple_counts = {}
print(f"{'n':>3} | {'m':>3} | {'q':>3} | {'Count':>6} | {'P(n∩m∩q)':>10} | {'Decimal':>10}")
print("-" * 80)

for n, m, q in combinations(range(2, 13), 3):
    count = sum(1 for roll in all_rolls if can_make_all_sums(roll, [n, m, q]))
    triple_counts[(n, m, q)] = count
    prob = count / total_outcomes
    print(f"{n:>3} | {m:>3} | {q:>3} | {count:>6} | {count:>4}/{total_outcomes:<4} | {prob:>9.4f}")

print()
print(f"Total triple combinations: {len(triple_counts)}")
print()

# Examples of using these tables
print("=" * 80)
print("EXAMPLE: Computing P(at least one of {6, 7, 8}) using the tables")
print("-" * 80)
print()

a, b, c = 6, 7, 8
p_a = individual_counts[a]
p_b = individual_counts[b]
p_c = individual_counts[c]
p_ab = pairwise_counts[(a, b)]
p_ac = pairwise_counts[(a, c)]
p_bc = pairwise_counts[(b, c)]
p_abc = triple_counts[(a, b, c)]

result = p_a + p_b + p_c - p_ab - p_ac - p_bc + p_abc

print(f"P({a}) = {p_a}/{total_outcomes}")
print(f"P({b}) = {p_b}/{total_outcomes}")
print(f"P({c}) = {p_c}/{total_outcomes}")
print(f"P({a}∩{b}) = {p_ab}/{total_outcomes}")
print(f"P({a}∩{c}) = {p_ac}/{total_outcomes}")
print(f"P({b}∩{c}) = {p_bc}/{total_outcomes}")
print(f"P({a}∩{b}∩{c}) = {p_abc}/{total_outcomes}")
print()
print(f"P(at least one) = {p_a} + {p_b} + {p_c} - {p_ab} - {p_ac} - {p_bc} + {p_abc}")
print(f"                = {result}/{total_outcomes}")
print(f"                = {result/total_outcomes:.4f} = {result/total_outcomes:.1%}")
print(f"P(Bust) = {(total_outcomes-result)/total_outcomes:.1%}")
print()

# Save tables to files for easy reference
print("=" * 80)
print("Saving tables to CSV files...")
print("-" * 80)

# Save individual probabilities
with open('/home/k1/public/notes/blog/files/20251201/individual_probabilities.csv', 'w') as f:
    f.write("sum,count,probability\n")
    for n in range(2, 13):
        count = individual_counts[n]
        prob = count / total_outcomes
        f.write(f"{n},{count},{prob:.6f}\n")
print("✓ Saved: individual_probabilities.csv")

# Save pairwise intersections
with open('/home/k1/public/notes/blog/files/20251201/pairwise_probabilities.csv', 'w') as f:
    f.write("sum1,sum2,count,probability\n")
    for (n, m), count in sorted(pairwise_counts.items()):
        prob = count / total_outcomes
        f.write(f"{n},{m},{count},{prob:.6f}\n")
print("✓ Saved: pairwise_probabilities.csv")

# Save triple intersections
with open('/home/k1/public/notes/blog/files/20251201/triple_probabilities.csv', 'w') as f:
    f.write("sum1,sum2,sum3,count,probability\n")
    for (n, m, q), count in sorted(triple_counts.items()):
        prob = count / total_outcomes
        f.write(f"{n},{m},{q},{count},{prob:.6f}\n")
print("✓ Saved: triple_probabilities.csv")

print()
print("Done! You can now use these tables to calculate any 3-column combination.")
