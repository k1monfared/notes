"""
Analyze all 165 possible three-column combinations in Can't Stop
Computes success probability, bust probability, clean move percentage, and Q value
"""

from itertools import combinations, product

def get_pairings(dice):
    """Get all 3 possible pairings of 4 dice"""
    d1, d2, d3, d4 = dice
    return [
        [(d1, d2), (d3, d4)],
        [(d1, d3), (d2, d4)],
        [(d1, d4), (d2, d3)]
    ]

def can_make_any_sum(dice, targets):
    """Check if we can make any sum from targets"""
    for pairing in get_pairings(dice):
        sums = {sum(pair) for pair in pairing}
        if any(target in sums for target in targets):
            return True
    return False

def can_make_clean_move(dice, targets):
    """Check if we can make a move using ONLY target columns"""
    for pairing in get_pairings(dice):
        sums = [sum(pair) for pair in pairing]
        # This pairing is clean if all its sums are in targets
        if all(s in targets for s in sums):
            return True
    return False

def expected_markers_advanced(columns):
    """Calculate E[markers advanced | success] for given columns"""
    all_rolls = list(product(range(1, 7), repeat=4))
    successful_rolls = []

    for roll in all_rolls:
        max_markers = 0
        for pairing in get_pairings(roll):
            markers = sum(1 for pair in pairing if sum(pair) in columns)
            max_markers = max(max_markers, markers)

        if max_markers > 0:
            successful_rolls.append(max_markers)

    if len(successful_rolls) == 0:
        return 0.0

    return sum(successful_rolls) / len(successful_rolls)

def analyze_combination(columns):
    """Analyze a specific 3-column combination"""
    all_rolls = list(product(range(1, 7), repeat=4))
    total = len(all_rolls)

    success_count = sum(1 for roll in all_rolls if can_make_any_sum(roll, columns))
    clean_count = sum(1 for roll in all_rolls if can_make_clean_move(roll, columns))

    success_prob = success_count / total
    bust_prob = 1 - success_prob
    clean_prob = clean_count / total
    q_value = expected_markers_advanced(columns)

    return {
        'columns': columns,
        'success_count': success_count,
        'success_prob': success_prob,
        'bust_prob': bust_prob,
        'clean_count': clean_count,
        'clean_prob': clean_prob,
        'q_value': q_value
    }

def analyze_all_combinations():
    """Analyze all 165 possible 3-column combinations"""
    results = []

    for combo in combinations(range(2, 13), 3):
        result = analyze_combination(combo)
        results.append(result)

    # Sort by success probability (best to worst)
    results.sort(key=lambda x: x['success_prob'], reverse=True)

    return results

def print_results_table(results, top_n=20, bottom_n=20):
    """Print formatted table of results"""
    print("Top", top_n, "Best Combinations:")
    print("-" * 80)
    print(f"{'Rank':>4} | {'Columns':>12} | {'Success':>8} | {'Bust':>6} | {'Clean':>6} | {'Q':>5}")
    print("-" * 80)

    for i, r in enumerate(results[:top_n], 1):
        cols = "{" + ",".join(map(str, r['columns'])) + "}"
        print(f"{i:4d} | {cols:>12} | {r['success_prob']:7.1%} | {r['bust_prob']:5.1%} | "
              f"{r['clean_prob']:5.1%} | {r['q_value']:5.2f}")

    print("\n" + "=" * 80 + "\n")
    print("Bottom", bottom_n, "Worst Combinations:")
    print("-" * 80)
    print(f"{'Rank':>4} | {'Columns':>12} | {'Success':>8} | {'Bust':>6} | {'Clean':>6} | {'Q':>5}")
    print("-" * 80)

    for i, r in enumerate(results[-bottom_n:], len(results) - bottom_n + 1):
        cols = "{" + ",".join(map(str, r['columns'])) + "}"
        print(f"{i:4d} | {cols:>12} | {r['success_prob']:7.1%} | {r['bust_prob']:5.1%} | "
              f"{r['clean_prob']:5.1%} | {r['q_value']:5.2f}")

def export_to_csv(results, filename='column_combinations_all.csv'):
    """Export results to CSV file"""
    import csv

    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Rank', 'Columns', 'Success_Prob', 'Bust_Prob',
                        'Clean_Prob', 'Q_Value', 'Success_Count', 'Clean_Count'])

        for i, r in enumerate(results, 1):
            cols = "{" + ",".join(map(str, r['columns'])) + "}"
            writer.writerow([
                i, cols,
                f"{r['success_prob']:.4f}",
                f"{r['bust_prob']:.4f}",
                f"{r['clean_prob']:.4f}",
                f"{r['q_value']:.3f}",
                r['success_count'],
                r['clean_count']
            ])

if __name__ == "__main__":
    print("Analyzing all 165 three-column combinations...")
    print("=" * 80)

    results = analyze_all_combinations()
    print_results_table(results, top_n=20, bottom_n=20)

    print("\n" + "=" * 80)
    print("Exporting full results to CSV...")
    export_to_csv(results)
    print("Done! See column_combinations_all.csv for complete results.")
