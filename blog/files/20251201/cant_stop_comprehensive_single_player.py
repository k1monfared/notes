#!/usr/bin/env python3
"""
Comprehensive single-player analysis for all Can't Stop strategies.
Tests how many turns each strategy needs to complete 1 or 3 columns independently.
"""

import sys
sys.path.insert(0, '/home/k1/public/notes/blog/files/20251201')

from cant_stop_analysis import (
    GameState, Strategy, GreedyStrategy, ConservativeStrategy,
    get_pairings, calculate_combination_stats
)
from cant_stop_analysis_extended import (
    HeuristicStrategy, OpponentAwareStrategy, RandomStrategy,
    GreedyImproved1, GreedyImproved2, AdaptiveThreshold,
    ProportionalThreshold, GreedyUntilFraction, FiftyPercentSurvival,
    ExpectedValueMaximizer, GreedyUntilOneColumn, GreedyUntilThreeColumns
)

from cant_stop_single_player_analysis import (
    simulate_single_player, single_player_analysis_for_specific_columns,
    mathematical_expected_turns_single_column, mathematical_expected_turns_three_columns
)

# ============================================================================
# Comprehensive Strategy Testing
# ============================================================================

def comprehensive_single_player_test(num_trials: int = 1000):
    """Test all strategies in single-player mode."""

    print("=" * 80)
    print("COMPREHENSIVE SINGLE-PLAYER ANALYSIS")
    print("=" * 80)
    print(f"\nTesting {num_trials} trials per strategy\n")

    strategies = {
        # Skip Greedy and GreedyUntil3Col - they don't make sense for single-player
        # 'Greedy': GreedyStrategy(),
        'Conservative(1)': ConservativeStrategy(stop_threshold=1),
        'Conservative(2)': ConservativeStrategy(stop_threshold=2),
        'Conservative(3)': ConservativeStrategy(stop_threshold=3),
        'Conservative(4)': ConservativeStrategy(stop_threshold=4),
        'Heuristic(0.3)': HeuristicStrategy(risk_tolerance=0.3),
        'Heuristic(0.5)': HeuristicStrategy(risk_tolerance=0.5),
        'Heuristic(1.0)': HeuristicStrategy(risk_tolerance=1.0),
        'Heuristic(1.5)': HeuristicStrategy(risk_tolerance=1.5),
        'Heuristic(2.0)': HeuristicStrategy(risk_tolerance=2.0),
        'OppAware(0.3,1,2)': OpponentAwareStrategy(alpha_behind=0.3, alpha_tied=1.0, alpha_ahead=2.0),
        'OppAware(0.5,1,2)': OpponentAwareStrategy(alpha_behind=0.5, alpha_tied=1.0, alpha_ahead=2.0),
        'OppAware(0.7,1,1.5)': OpponentAwareStrategy(alpha_behind=0.7, alpha_tied=1.0, alpha_ahead=1.5),
        'Random(0.3)': RandomStrategy(stop_probability=0.3),
        'GreedyImproved1': GreedyImproved1(),
        'GreedyImproved2': GreedyImproved2(),
        'AdaptiveThreshold': AdaptiveThreshold(),
        'Proportional(0.33)': ProportionalThreshold(fraction=0.33),
        'Proportional(0.5)': ProportionalThreshold(fraction=0.5),
        'GreedyFraction(0.33)': GreedyUntilFraction(fraction=0.33),
        'GreedyFraction(0.5)': GreedyUntilFraction(fraction=0.5),
        'FiftyPercentSurvival': FiftyPercentSurvival(),
        'ExpectedValueMax': ExpectedValueMaximizer(),
        'GreedyUntil1Col': GreedyUntilOneColumn(),
        # 'GreedyUntil3Col': GreedyUntilThreeColumns(),  # Skip - it's designed for winning games, not single-player
    }

    # ========================================================================
    # Part 1: Mathematical Analysis
    # ========================================================================

    print("=" * 80)
    print("PART 1: MATHEMATICAL ANALYSIS (Column Probabilities)")
    print("=" * 80)

    print("\nSingle Column Expected Rolls:")
    print("-" * 80)
    print(f"{'Column':<10} {'Length':<10} {'P(hit)':<12} {'Expected Rolls':<15}")
    print("-" * 80)

    for col in range(2, 13):
        math_result = mathematical_expected_turns_single_column(col)
        print(f"{math_result['column']:<10} {math_result['length']:<10} "
              f"{math_result['hit_probability']:<12.1%} {math_result['expected_rolls']:<15.2f}")

    print("\n\nThree Column Combinations (Mathematical):")
    print("-" * 80)
    print(f"{'Columns':<15} {'Total Steps':<12} {'P(success)':<12} {'Q':<8} {'Exp Rolls/Turn':<15} {'Exp Turns':<12}")
    print("-" * 80)

    interesting_combos = [
        (6, 7, 8),  # Best
        (5, 7, 9),  # Good
        (4, 6, 8),  # Mixed
        (2, 3, 12), # Worst
    ]

    for combo in interesting_combos:
        math_result = mathematical_expected_turns_three_columns(combo)
        print(f"{str(combo):<15} {math_result['total_steps']:<12} "
              f"{math_result['success_prob']:<12.1%} {math_result['Q']:<8.2f} "
              f"{math_result['expected_rolls_per_turn']:<15.2f} {math_result['expected_turns']:<12.2f}")

    # ========================================================================
    # Part 2: Single-Player Simulation (Complete 3 Columns)
    # ========================================================================

    print("\n\n" + "=" * 80)
    print("PART 2: SINGLE-PLAYER SIMULATION (Complete Any 3 Columns)")
    print("=" * 80)
    print(f"\n{num_trials} trials per strategy\n")

    results_3col = []

    for i, (name, strategy) in enumerate(strategies.items(), 1):
        print(f"[{i}/{len(strategies)}] Testing {name}...", end=" ", flush=True)

        try:
            result = simulate_single_player(strategy, target_columns=3, num_trials=num_trials)
            results_3col.append({
                'name': name,
                'avg_turns': result['avg_turns'],
                'median_turns': result['median_turns'],
                'avg_rolls': result['avg_rolls'],
                'avg_busts': result['avg_busts'],
                'min_turns': result['min_turns'],
                'max_turns': result['max_turns'],
            })
            print(f"✓ (avg: {result['avg_turns']:.1f} turns)")
        except Exception as e:
            print(f"✗ ERROR: {e}")
            results_3col.append({
                'name': name,
                'avg_turns': float('inf'),
                'median_turns': float('inf'),
                'avg_rolls': float('inf'),
                'avg_busts': float('inf'),
                'min_turns': float('inf'),
                'max_turns': float('inf'),
            })

    # Sort by avg_turns
    results_3col.sort(key=lambda x: x['avg_turns'])

    print("\n\nResults (sorted by average turns):")
    print("-" * 80)
    print(f"{'Rank':<6} {'Strategy':<25} {'Avg Turns':<12} {'Median':<10} {'Avg Rolls':<12} {'Avg Busts':<10}")
    print("-" * 80)

    for rank, result in enumerate(results_3col, 1):
        if result['avg_turns'] == float('inf'):
            print(f"{rank:<6} {result['name']:<25} {'FAILED':<12} {'FAILED':<10} {'FAILED':<12} {'FAILED':<10}")
        else:
            print(f"{rank:<6} {result['name']:<25} {result['avg_turns']:<12.2f} {result['median_turns']:<10.0f} "
                  f"{result['avg_rolls']:<12.2f} {result['avg_busts']:<10.2f}")

    # ========================================================================
    # Part 3: Specific Column Analysis (Column 7 only)
    # ========================================================================

    print("\n\n" + "=" * 80)
    print("PART 3: SINGLE COLUMN ANALYSIS (Complete Column 7 Only)")
    print("=" * 80)
    print(f"\n{num_trials} trials per strategy\n")

    results_col7 = []

    for i, (name, strategy) in enumerate(strategies.items(), 1):
        print(f"[{i}/{len(strategies)}] Testing {name}...", end=" ", flush=True)

        try:
            result = single_player_analysis_for_specific_columns(strategy, [7], num_trials=num_trials)
            results_col7.append({
                'name': name,
                'avg_turns': result['avg_turns'],
                'median_turns': result['median_turns'],
                'avg_rolls': result['avg_rolls'],
                'avg_busts': result['avg_busts'],
            })
            print(f"✓ (avg: {result['avg_turns']:.1f} turns)")
        except Exception as e:
            print(f"✗ ERROR: {e}")
            results_col7.append({
                'name': name,
                'avg_turns': float('inf'),
                'median_turns': float('inf'),
                'avg_rolls': float('inf'),
                'avg_busts': float('inf'),
            })

    # Sort by avg_turns
    results_col7.sort(key=lambda x: x['avg_turns'])

    print("\n\nResults (sorted by average turns):")
    print("-" * 80)
    print(f"{'Rank':<6} {'Strategy':<25} {'Avg Turns':<12} {'Median':<10} {'Avg Rolls':<12} {'Avg Busts':<10}")
    print("-" * 80)

    for rank, result in enumerate(results_col7, 1):
        if result['avg_turns'] == float('inf'):
            print(f"{rank:<6} {result['name']:<25} {'FAILED':<12} {'FAILED':<10} {'FAILED':<12} {'FAILED':<10}")
        else:
            print(f"{rank:<6} {result['name']:<25} {result['avg_turns']:<12.2f} {result['median_turns']:<10.0f} "
                  f"{result['avg_rolls']:<12.2f} {result['avg_busts']:<10.2f}")

    # ========================================================================
    # Part 4: Best Combination Analysis ({6,7,8})
    # ========================================================================

    print("\n\n" + "=" * 80)
    print("PART 4: BEST COMBINATION ANALYSIS (Complete Columns {6,7,8} Only)")
    print("=" * 80)
    print(f"\n{num_trials} trials per strategy\n")

    results_678 = []

    for i, (name, strategy) in enumerate(strategies.items(), 1):
        print(f"[{i}/{len(strategies)}] Testing {name}...", end=" ", flush=True)

        try:
            result = single_player_analysis_for_specific_columns(strategy, [6, 7, 8], num_trials=num_trials)
            results_678.append({
                'name': name,
                'avg_turns': result['avg_turns'],
                'median_turns': result['median_turns'],
                'avg_rolls': result['avg_rolls'],
                'avg_busts': result['avg_busts'],
            })
            print(f"✓ (avg: {result['avg_turns']:.1f} turns)")
        except Exception as e:
            print(f"✗ ERROR: {e}")
            results_678.append({
                'name': name,
                'avg_turns': float('inf'),
                'median_turns': float('inf'),
                'avg_rolls': float('inf'),
                'avg_busts': float('inf'),
            })

    # Sort by avg_turns
    results_678.sort(key=lambda x: x['avg_turns'])

    print("\n\nResults (sorted by average turns):")
    print("-" * 80)
    print(f"{'Rank':<6} {'Strategy':<25} {'Avg Turns':<12} {'Median':<10} {'Avg Rolls':<12} {'Avg Busts':<10}")
    print("-" * 80)

    for rank, result in enumerate(results_678, 1):
        if result['avg_turns'] == float('inf'):
            print(f"{rank:<6} {result['name']:<25} {'FAILED':<12} {'FAILED':<10} {'FAILED':<12} {'FAILED':<10}")
        else:
            print(f"{rank:<6} {result['name']:<25} {result['avg_turns']:<12.2f} {result['median_turns']:<10.0f} "
                  f"{result['avg_rolls']:<12.2f} {result['avg_busts']:<10.2f}")

    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)


if __name__ == "__main__":
    comprehensive_single_player_test(num_trials=1000)
