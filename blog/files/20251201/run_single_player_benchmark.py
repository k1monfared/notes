#!/usr/bin/env python3
"""
Single-Player Benchmarking - 1,000 trials per strategy
Measures how efficiently each strategy completes columns when playing alone
"""

import os
import sys
import json
import time
from datetime import datetime
from collections import defaultdict
import statistics

# Suppress backend debug output
os.environ['TESTING'] = '1'

from game_simulator import SinglePlayerSimulator
from strategies_correct_implementation import get_all_strategies

def run_single_player_benchmark(num_trials=1000):
    """
    Run single-player benchmark for all strategies.

    Args:
        num_trials: Number of trials per strategy

    Returns:
        Dictionary with results for each strategy
    """
    strategies = get_all_strategies()
    results = {}

    print("=" * 80)
    print("CAN'T STOP - SINGLE-PLAYER BENCHMARKING")
    print("=" * 80)
    print(f"\nRunning {num_trials} trials per strategy...")
    print(f"Total strategies: {len(strategies)}")
    print(f"Total games: {len(strategies) * num_trials:,}")
    print()

    start_time = time.time()

    for idx, (name, strategy) in enumerate(sorted(strategies.items()), 1):
        print(f"[{idx}/{len(strategies)}] Testing {name}...", end=" ", flush=True)

        trial_start = time.time()

        # Run trials
        turns_to_1col = []
        turns_to_2col = []
        turns_to_3col = []
        busts = []
        column_usage = defaultdict(int)

        for trial in range(num_trials):
            sim = SinglePlayerSimulator(strategy, verbose=False)
            result = sim.simulate_to_completion(target_columns=3, max_turns=500)

            turns_to_1col.append(result['turns_to_1col'])
            turns_to_2col.append(result['turns_to_2col'])
            turns_to_3col.append(result['turns_to_3col'])
            busts.append(result['busts'])

            # Aggregate column usage
            for col, count in result['column_usage'].items():
                column_usage[col] += count

        # Calculate statistics
        def calc_stats(data):
            return {
                'mean': statistics.mean(data),
                'median': statistics.median(data),
                'stdev': statistics.stdev(data) if len(data) > 1 else 0,
                'min': min(data),
                'max': max(data)
            }

        results[name] = {
            'strategy_name': name,
            'trials': num_trials,
            'turns_to_1col': calc_stats(turns_to_1col),
            'turns_to_2col': calc_stats(turns_to_2col),
            'turns_to_3col': calc_stats(turns_to_3col),
            'busts': calc_stats(busts),
            'column_usage': dict(column_usage),
            'column_usage_normalized': {
                col: count / num_trials for col, count in column_usage.items()
            }
        }

        trial_time = time.time() - trial_start
        avg_turns = results[name]['turns_to_3col']['mean']

        print(f"✓ (avg: {avg_turns:.1f} turns, {trial_time:.1f}s)")

    elapsed = time.time() - start_time

    print()
    print("=" * 80)
    print(f"BENCHMARK COMPLETE in {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
    print("=" * 80)

    return results


def print_results_summary(results):
    """Print a summary table of results."""
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY - TURNS TO COMPLETE 3 COLUMNS")
    print("=" * 80)
    print(f"{'Rank':<6} {'Strategy':<30} {'Mean':<8} {'Median':<8} {'StdDev':<8}")
    print("-" * 80)

    # Sort by mean turns to complete 3 columns
    sorted_results = sorted(
        results.items(),
        key=lambda x: x[1]['turns_to_3col']['mean']
    )

    for rank, (name, data) in enumerate(sorted_results, 1):
        mean = data['turns_to_3col']['mean']
        median = data['turns_to_3col']['median']
        stdev = data['turns_to_3col']['stdev']

        print(f"{rank:<6} {name:<30} {mean:<8.2f} {median:<8.0f} {stdev:<8.2f}")

    print()


def save_results(results, filename=None):
    """Save results to JSON file."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"single_player_results_{timestamp}.json"

    filepath = f"/home/k1/public/notes/blog/files/20251201/{filename}"

    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to: {filename}")
    return filepath


def save_results_csv(results):
    """Save results to CSV file for easy analysis."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"single_player_results_{timestamp}.csv"
    filepath = f"/home/k1/public/notes/blog/files/20251201/{filename}"

    import csv

    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'Rank', 'Strategy',
            '1Col_Mean', '1Col_Median', '1Col_StdDev',
            '2Col_Mean', '2Col_Median', '2Col_StdDev',
            '3Col_Mean', '3Col_Median', '3Col_StdDev',
            'Busts_Mean', 'Busts_Median',
            'FavoriteColumn', 'FavoriteColumnUsage'
        ])

        # Sort by mean turns to 3 columns
        sorted_results = sorted(
            results.items(),
            key=lambda x: x[1]['turns_to_3col']['mean']
        )

        for rank, (name, data) in enumerate(sorted_results, 1):
            # Find favorite column
            col_usage = data['column_usage_normalized']
            fav_col = max(col_usage.items(), key=lambda x: x[1]) if col_usage else (None, 0)

            writer.writerow([
                rank, name,
                data['turns_to_1col']['mean'],
                data['turns_to_1col']['median'],
                data['turns_to_1col']['stdev'],
                data['turns_to_2col']['mean'],
                data['turns_to_2col']['median'],
                data['turns_to_2col']['stdev'],
                data['turns_to_3col']['mean'],
                data['turns_to_3col']['median'],
                data['turns_to_3col']['stdev'],
                data['busts']['mean'],
                data['busts']['median'],
                fav_col[0],
                f"{fav_col[1]:.2f}"
            ])

    print(f"CSV saved to: {filename}")
    return filepath


if __name__ == "__main__":
    # Parse command line args
    num_trials = 1000
    if len(sys.argv) > 1:
        num_trials = int(sys.argv[1])

    print(f"\nStarting single-player benchmark with {num_trials} trials per strategy...")
    print("(This will take several minutes...)\n")

    # Run benchmark
    results = run_single_player_benchmark(num_trials)

    # Print summary
    print_results_summary(results)

    # Save results
    json_file = save_results(results)
    csv_file = save_results_csv(results)

    print("\n" + "=" * 80)
    print("BENCHMARK COMPLETE!")
    print("=" * 80)
    print(f"\nResults saved:")
    print(f"  - JSON: {json_file}")
    print(f"  - CSV:  {csv_file}")
    print("\nReady for tournament simulations!")
