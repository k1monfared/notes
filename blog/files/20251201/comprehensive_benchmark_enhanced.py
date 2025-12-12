#!/usr/bin/env python3
"""
Comprehensive Benchmark Runner for Can't Stop Strategies - Enhanced Version

Features:
1. Single-player benchmarks (measures turns to complete 1, 2, 3 columns)
2. Head-to-head tournaments (all vs all + self-play)
3. Saves aggregated stats to JSON
4. Saves raw trial/game data to compressed JSONL
5. Computes enhanced statistics (stddev, percentiles, etc.)
6. Sends completion notification
"""

import json
import sys
import time
import os
import gzip
import statistics
from datetime import datetime
from typing import Dict, List
from collections import defaultdict
from dataclasses import asdict

# Use local silent version of GameMechanics
from main_silent import GameMechanics

from strategies_correct_implementation import get_all_strategies
from game_simulator import SinglePlayerSimulator, GameSimulator, GameResult


def calculate_percentile(data, percentile):
    """Calculate percentile of a list."""
    if not data:
        return 0
    sorted_data = sorted(data)
    index = (len(sorted_data) - 1) * percentile / 100
    lower = int(index)
    upper = lower + 1
    weight = index - lower

    if upper >= len(sorted_data):
        return sorted_data[lower]
    return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight


class BenchmarkRunner:
    """Runs comprehensive benchmarks on all strategies."""

    def __init__(self, output_dir="./results"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.strategies = get_all_strategies()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = time.time()

    def run_single_player_benchmark(self, num_trials=1000):
        """
        Run single-player benchmarks with enhanced logging.
        """
        print(f"\n{'='*80}")
        print(f"SINGLE-PLAYER BENCHMARK ({num_trials} trials per strategy)")
        print(f"{'='*80}\n")

        results = {}
        raw_file = f"{self.output_dir}/single_player_raw_{self.timestamp}.jsonl.gz"

        with gzip.open(raw_file, 'wt', encoding='utf-8') as raw_out:
            for strategy_name, strategy in sorted(self.strategies.items()):
                print(f"Testing {strategy_name}...", end=" ", flush=True)
                start_time = time.time()

                simulator = SinglePlayerSimulator(strategy, verbose=False)
                trials_data = []

                for trial in range(num_trials):
                    result = simulator.simulate_to_completion(target_columns=3, max_turns=500)
                    trials_data.append(result)

                    # Write raw trial data to JSONL
                    raw_record = {
                        'strategy': strategy_name,
                        'trial': trial,
                        'turns_to_1col': result['turns_to_1col'],
                        'turns_to_2col': result['turns_to_2col'],
                        'turns_to_3col': result['turns_to_3col'],
                        'busts': result['busts'],
                        'columns_completed': result['columns_completed'],
                        'column_usage': result['column_usage']
                    }
                    raw_out.write(json.dumps(raw_record) + '\n')

                # Calculate enhanced statistics
                turns_to_1col = [t['turns_to_1col'] for t in trials_data]
                turns_to_2col = [t['turns_to_2col'] for t in trials_data]
                turns_to_3col = [t['turns_to_3col'] for t in trials_data]
                busts = [t['busts'] for t in trials_data]

                # Column usage aggregation
                column_usage_total = defaultdict(int)
                for t in trials_data:
                    for col, count in t['column_usage'].items():
                        column_usage_total[col] += count

                # Column completion preferences
                column_completions = defaultdict(int)
                for t in trials_data:
                    for col in t['columns_completed']:
                        column_completions[col] += 1

                results[strategy_name] = {
                    'turns_to_1col': {
                        'avg': statistics.mean(turns_to_1col),
                        'median': statistics.median(turns_to_1col),
                        'stddev': statistics.stdev(turns_to_1col) if len(turns_to_1col) > 1 else 0,
                        'min': min(turns_to_1col),
                        'max': max(turns_to_1col),
                        'p25': calculate_percentile(turns_to_1col, 25),
                        'p75': calculate_percentile(turns_to_1col, 75),
                        'p90': calculate_percentile(turns_to_1col, 90)
                    },
                    'turns_to_2col': {
                        'avg': statistics.mean(turns_to_2col),
                        'median': statistics.median(turns_to_2col),
                        'stddev': statistics.stdev(turns_to_2col) if len(turns_to_2col) > 1 else 0,
                        'min': min(turns_to_2col),
                        'max': max(turns_to_2col),
                        'p25': calculate_percentile(turns_to_2col, 25),
                        'p75': calculate_percentile(turns_to_2col, 75),
                        'p90': calculate_percentile(turns_to_2col, 90)
                    },
                    'turns_to_3col': {
                        'avg': statistics.mean(turns_to_3col),
                        'median': statistics.median(turns_to_3col),
                        'stddev': statistics.stdev(turns_to_3col) if len(turns_to_3col) > 1 else 0,
                        'min': min(turns_to_3col),
                        'max': max(turns_to_3col),
                        'p25': calculate_percentile(turns_to_3col, 25),
                        'p75': calculate_percentile(turns_to_3col, 75),
                        'p90': calculate_percentile(turns_to_3col, 90)
                    },
                    'busts': {
                        'avg': statistics.mean(busts),
                        'median': statistics.median(busts),
                        'stddev': statistics.stdev(busts) if len(busts) > 1 else 0,
                        'min': min(busts),
                        'max': max(busts)
                    },
                    'column_usage': dict(column_usage_total),
                    'column_completions': dict(column_completions),
                    'trials': num_trials
                }

                elapsed = time.time() - start_time
                print(f"Done in {elapsed:.1f}s - Avg turns to win: {results[strategy_name]['turns_to_3col']['avg']:.1f}")

        # Save aggregated results
        stats_file = f"{self.output_dir}/single_player_stats_{self.timestamp}.json"
        with open(stats_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n✓ Single-player stats saved to: {stats_file}")
        print(f"✓ Single-player raw data saved to: {raw_file}")
        return results

    def run_head_to_head_tournament(self, games_per_matchup=2500):
        """
        Run head-to-head tournament with enhanced logging.
        """
        print(f"\n{'='*80}")
        print(f"HEAD-TO-HEAD TOURNAMENT ({games_per_matchup} games per matchup)")
        print(f"{'='*80}\n")

        strategy_names = sorted(self.strategies.keys())
        num_strategies = len(strategy_names)
        total_matchups = num_strategies * num_strategies

        print(f"Running {total_matchups} matchups ({num_strategies} strategies)...")

        results = {}
        raw_file = f"{self.output_dir}/head_to_head_raw_{self.timestamp}.jsonl.gz"

        matchup_count = 0

        with gzip.open(raw_file, 'wt', encoding='utf-8') as raw_out:
            for s1_name in strategy_names:
                results[s1_name] = {}

                for s2_name in strategy_names:
                    matchup_count += 1
                    print(f"[{matchup_count}/{total_matchups}] {s1_name} vs {s2_name}...",
                          end=" ", flush=True)

                    s1 = self.strategies[s1_name]
                    s2 = self.strategies[s2_name]

                    p1_wins = 0
                    p2_wins = 0
                    turns_list = []
                    p1_columns_list = []
                    p2_columns_list = []
                    p1_busts_list = []
                    p2_busts_list = []

                    for game in range(games_per_matchup):
                        simulator = GameSimulator(s1, s2, verbose=False)
                        result = simulator.simulate_game(max_turns=200)

                        if result.winner == 0:
                            p1_wins += 1
                        else:
                            p2_wins += 1

                        turns_list.append(result.turns)
                        p1_columns_list.append(result.player1_columns_completed)
                        p2_columns_list.append(result.player2_columns_completed)
                        p1_busts_list.append(result.player1_busts)
                        p2_busts_list.append(result.player2_busts)

                        # Write raw game data to JSONL
                        raw_record = {
                            's1': s1_name,
                            's2': s2_name,
                            'game': game,
                            'winner': result.winner,
                            'turns': result.turns,
                            'p1_cols': result.player1_columns_completed,
                            'p2_cols': result.player2_columns_completed,
                            'p1_busts': result.player1_busts,
                            'p2_busts': result.player2_busts
                        }
                        raw_out.write(json.dumps(raw_record) + '\n')

                    results[s1_name][s2_name] = {
                        'p1_wins': p1_wins,
                        'p2_wins': p2_wins,
                        'p1_win_rate': p1_wins / games_per_matchup,
                        'turns': {
                            'avg': statistics.mean(turns_list),
                            'median': statistics.median(turns_list),
                            'stddev': statistics.stdev(turns_list) if len(turns_list) > 1 else 0,
                            'min': min(turns_list),
                            'max': max(turns_list)
                        },
                        'p1_columns': {
                            'avg': statistics.mean(p1_columns_list),
                            'median': statistics.median(p1_columns_list)
                        },
                        'p2_columns': {
                            'avg': statistics.mean(p2_columns_list),
                            'median': statistics.median(p2_columns_list)
                        },
                        'p1_busts': {
                            'avg': statistics.mean(p1_busts_list),
                            'median': statistics.median(p1_busts_list)
                        },
                        'p2_busts': {
                            'avg': statistics.mean(p2_busts_list),
                            'median': statistics.median(p2_busts_list)
                        },
                        'games_played': games_per_matchup
                    }

                    win_pct = (p1_wins / games_per_matchup) * 100
                    print(f"{p1_wins}-{p2_wins} ({win_pct:.1f}%)")

        # Save aggregated results
        stats_file = f"{self.output_dir}/head_to_head_stats_{self.timestamp}.json"
        with open(stats_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n✓ Head-to-head stats saved to: {stats_file}")
        print(f"✓ Head-to-head raw data saved to: {raw_file}")

        # Print self-play verification
        print(f"\n{'='*80}")
        print("SELF-PLAY VERIFICATION (should be ~50%)")
        print(f"{'='*80}\n")

        for strategy_name in strategy_names:
            self_play = results[strategy_name][strategy_name]
            win_rate = self_play['p1_win_rate'] * 100
            deviation = abs(win_rate - 50.0)
            status = "✓" if deviation < 10 else "⚠"
            print(f"{status} {strategy_name:30s}: {win_rate:.1f}% (deviation: {deviation:.1f}%)")

        return results

    def generate_summary_report(self, single_player_results, head_to_head_results):
        """Generate comprehensive summary report."""

        print(f"\n{'='*80}")
        print("GENERATING SUMMARY REPORT")
        print(f"{'='*80}\n")

        report_lines = []
        report_lines.append("# Can't Stop Strategy Benchmark Results")
        report_lines.append(f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"**Total simulation time**: {(time.time() - self.start_time)/3600:.2f} hours")

        report_lines.append(f"\n## Summary")
        report_lines.append(f"\n- Total strategies tested: {len(self.strategies)}")
        report_lines.append(f"- Single-player trials per strategy: {single_player_results[list(single_player_results.keys())[0]]['trials']}")

        # Top 10 strategies by single-player performance
        report_lines.append(f"\n## Top 10 Strategies (Single-Player - Turns to Win)")
        report_lines.append("\n| Rank | Strategy | Avg Turns | Median | StdDev | P90 | Avg Busts |")
        report_lines.append("|------|----------|-----------|--------|--------|-----|-----------|")

        sorted_strategies = sorted(
            single_player_results.items(),
            key=lambda x: x[1]['turns_to_3col']['avg']
        )

        for rank, (name, data) in enumerate(sorted_strategies[:10], 1):
            avg = data['turns_to_3col']['avg']
            median = data['turns_to_3col']['median']
            stddev = data['turns_to_3col']['stddev']
            p90 = data['turns_to_3col']['p90']
            busts = data['busts']['avg']
            report_lines.append(f"| {rank} | {name} | {avg:.1f} | {median:.0f} | {stddev:.1f} | {p90:.0f} | {busts:.2f} |")

        # Head-to-head win rates
        report_lines.append(f"\n## Top 10 Head-to-Head Performers (Overall Win Rate)")
        report_lines.append("\n| Rank | Strategy | Overall Win Rate | Total Wins | Avg Win Rate |")
        report_lines.append("|------|----------|------------------|------------|--------------|")

        overall_wins = {}
        for s1_name, matchups in head_to_head_results.items():
            total_wins = sum(m['p1_wins'] for m in matchups.values())
            total_games = sum(m['games_played'] for m in matchups.values())
            overall_wins[s1_name] = {
                'win_rate': total_wins / total_games if total_games > 0 else 0,
                'total_wins': total_wins
            }

        sorted_by_wins = sorted(overall_wins.items(), key=lambda x: x[1]['win_rate'], reverse=True)

        for rank, (name, data) in enumerate(sorted_by_wins[:10], 1):
            win_rate = data['win_rate'] * 100
            total_wins = data['total_wins']
            report_lines.append(f"| {rank} | {name} | {win_rate:.1f}% | {total_wins} | {win_rate:.1f}% |")

        report_text = "\n".join(report_lines)

        # Save report
        report_file = f"{self.output_dir}/summary_report_{self.timestamp}.md"
        with open(report_file, 'w') as f:
            f.write(report_text)

        print(f"✓ Summary report saved to: {report_file}\n")
        print(report_text[:2000] + "\n...(truncated)")

    def send_completion_notification(self):
        """Write completion marker file."""
        marker_file = f"{self.output_dir}/SIMULATION_COMPLETE_{self.timestamp}.txt"
        total_time = time.time() - self.start_time

        with open(marker_file, 'w') as f:
            f.write(f"Simulation completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total time: {total_time/3600:.2f} hours\n")
            f.write(f"Timestamp: {self.timestamp}\n")

        print(f"\n✓ Completion marker saved to: {marker_file}")
        print(f"\n🎉 ALL SIMULATIONS COMPLETE! Total time: {total_time/3600:.2f} hours")


def main():
    """Run comprehensive benchmarks."""
    runner = BenchmarkRunner()

    print("\n" + "="*80)
    print("CAN'T STOP COMPREHENSIVE BENCHMARK SUITE - ENHANCED")
    print("="*80)
    print(f"\nTotal strategies: {len(runner.strategies)}")
    print(f"Output directory: {runner.output_dir}")
    print(f"Timestamp: {runner.timestamp}")

    # Run benchmarks
    print("\n" + "="*80)
    print("Starting benchmarks...")
    print("="*80)

    # Single-player (1000 trials)
    single_player_results = runner.run_single_player_benchmark(num_trials=1000)

    # Head-to-head (2500 games per matchup)
    head_to_head_results = runner.run_head_to_head_tournament(games_per_matchup=2500)

    # Generate summary
    runner.generate_summary_report(single_player_results, head_to_head_results)

    # Send completion notification
    runner.send_completion_notification()


if __name__ == "__main__":
    main()
