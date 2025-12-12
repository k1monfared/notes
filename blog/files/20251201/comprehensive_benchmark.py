#!/usr/bin/env python3
"""
Comprehensive Benchmark Runner for Can't Stop Strategies

Runs:
1. Single-player benchmarks (measures turns to complete 1, 2, 3 columns)
2. Head-to-head tournaments (all vs all + self-play)
3. Saves all results to JSON files
"""

import json
import sys
import time
import os
from datetime import datetime
from typing import Dict, List
from collections import defaultdict
from dataclasses import asdict

# Use local silent version of GameMechanics
from main_silent import GameMechanics

from strategies_correct_implementation import get_all_strategies
from game_simulator import SinglePlayerSimulator, GameSimulator, GameResult


class BenchmarkRunner:
    """Runs comprehensive benchmarks on all strategies."""

    def __init__(self, output_dir="./results"):
        self.output_dir = output_dir
        self.strategies = get_all_strategies()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def run_single_player_benchmark(self, num_trials=1000):
        """
        Run single-player benchmarks.

        Measures:
        - Turns to complete 1, 2, 3 columns
        - Bust rate
        - Column preferences
        """
        print(f"\n{'='*80}")
        print(f"SINGLE-PLAYER BENCHMARK ({num_trials} trials per strategy)")
        print(f"{'='*80}\n")

        results = {}

        for strategy_name, strategy in sorted(self.strategies.items()):
            print(f"Testing {strategy_name}...", end=" ", flush=True)
            start_time = time.time()

            simulator = SinglePlayerSimulator(strategy, verbose=False)
            trials_data = []

            for trial in range(num_trials):
                result = simulator.simulate_to_completion(target_columns=3, max_turns=500)
                trials_data.append(result)

            # Aggregate statistics
            turns_to_1col = [t['turns_to_1col'] for t in trials_data]
            turns_to_2col = [t['turns_to_2col'] for t in trials_data]
            turns_to_3col = [t['turns_to_3col'] for t in trials_data]
            busts = [t['busts'] for t in trials_data]

            # Column usage aggregation
            column_usage_total = defaultdict(int)
            for t in trials_data:
                for col, count in t['column_usage'].items():
                    column_usage_total[col] += count

            results[strategy_name] = {
                'turns_to_1col': {
                    'avg': sum(turns_to_1col) / len(turns_to_1col),
                    'median': sorted(turns_to_1col)[len(turns_to_1col) // 2],
                    'min': min(turns_to_1col),
                    'max': max(turns_to_1col)
                },
                'turns_to_2col': {
                    'avg': sum(turns_to_2col) / len(turns_to_2col),
                    'median': sorted(turns_to_2col)[len(turns_to_2col) // 2],
                    'min': min(turns_to_2col),
                    'max': max(turns_to_2col)
                },
                'turns_to_3col': {
                    'avg': sum(turns_to_3col) / len(turns_to_3col),
                    'median': sorted(turns_to_3col)[len(turns_to_3col) // 2],
                    'min': min(turns_to_3col),
                    'max': max(turns_to_3col)
                },
                'avg_busts': sum(busts) / len(busts),
                'column_usage': dict(column_usage_total),
                'trials': num_trials
            }

            elapsed = time.time() - start_time
            print(f"Done in {elapsed:.1f}s - Avg turns to win: {results[strategy_name]['turns_to_3col']['avg']:.1f}")

        # Save results
        output_file = f"{self.output_dir}/single_player_{self.timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n✓ Single-player results saved to: {output_file}")
        return results

    def run_head_to_head_tournament(self, games_per_matchup=100):
        """
        Run head-to-head tournament.

        Each strategy plays against:
        - Every other strategy (games_per_matchup games)
        - Itself (self-play to verify ~50% win rate)
        """
        print(f"\n{'='*80}")
        print(f"HEAD-TO-HEAD TOURNAMENT ({games_per_matchup} games per matchup)")
        print(f"{'='*80}\n")

        strategy_names = sorted(self.strategies.keys())
        num_strategies = len(strategy_names)
        total_matchups = num_strategies * num_strategies  # Including self-play

        print(f"Running {total_matchups} matchups ({num_strategies} strategies)...")

        results = {}
        matchup_count = 0

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
                total_turns = 0
                p1_columns = 0
                p2_columns = 0
                p1_busts = 0
                p2_busts = 0

                for game in range(games_per_matchup):
                    simulator = GameSimulator(s1, s2, verbose=False)
                    result = simulator.simulate_game(max_turns=200)

                    if result.winner == 0:
                        p1_wins += 1
                    else:
                        p2_wins += 1

                    total_turns += result.turns
                    p1_columns += result.player1_columns_completed
                    p2_columns += result.player2_columns_completed
                    p1_busts += result.player1_busts
                    p2_busts += result.player2_busts

                results[s1_name][s2_name] = {
                    'p1_wins': p1_wins,
                    'p2_wins': p2_wins,
                    'p1_win_rate': p1_wins / games_per_matchup,
                    'avg_turns': total_turns / games_per_matchup,
                    'avg_p1_columns': p1_columns / games_per_matchup,
                    'avg_p2_columns': p2_columns / games_per_matchup,
                    'avg_p1_busts': p1_busts / games_per_matchup,
                    'avg_p2_busts': p2_busts / games_per_matchup,
                    'games_played': games_per_matchup
                }

                win_pct = (p1_wins / games_per_matchup) * 100
                print(f"{p1_wins}-{p2_wins} ({win_pct:.1f}%)")

        # Save results
        output_file = f"{self.output_dir}/head_to_head_{self.timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n✓ Head-to-head results saved to: {output_file}")

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
        """Generate a summary report in markdown format."""

        print(f"\n{'='*80}")
        print("GENERATING SUMMARY REPORT")
        print(f"{'='*80}\n")

        report_lines = []
        report_lines.append("# Can't Stop Strategy Benchmark Results")
        report_lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"\n## Summary")
        report_lines.append(f"\n- Total strategies tested: {len(self.strategies)}")
        report_lines.append(f"- Single-player trials per strategy: {single_player_results[list(single_player_results.keys())[0]]['trials']}")

        # Top 10 strategies by single-player performance
        report_lines.append(f"\n## Top 10 Strategies (Single-Player - Turns to Win)")
        report_lines.append("\n| Rank | Strategy | Avg Turns | Median | Avg Busts |")
        report_lines.append("|------|----------|-----------|--------|-----------|")

        sorted_strategies = sorted(
            single_player_results.items(),
            key=lambda x: x[1]['turns_to_3col']['avg']
        )

        for rank, (name, data) in enumerate(sorted_strategies[:10], 1):
            avg_turns = data['turns_to_3col']['avg']
            median_turns = data['turns_to_3col']['median']
            avg_busts = data['avg_busts']
            report_lines.append(f"| {rank} | {name} | {avg_turns:.1f} | {median_turns} | {avg_busts:.2f} |")

        # Head-to-head win rates
        report_lines.append(f"\n## Head-to-Head Win Rates (Overall)")
        report_lines.append("\nEach strategy's overall win rate across all matchups:")
        report_lines.append("\n| Rank | Strategy | Overall Win Rate | Total Wins |")
        report_lines.append("|------|----------|------------------|------------|")

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
            report_lines.append(f"| {rank} | {name} | {win_rate:.1f}% | {total_wins} |")

        report_text = "\n".join(report_lines)

        # Save report
        output_file = f"{self.output_dir}/summary_report_{self.timestamp}.md"
        with open(output_file, 'w') as f:
            f.write(report_text)

        print(f"✓ Summary report saved to: {output_file}\n")
        print(report_text)


def main():
    """Run comprehensive benchmarks."""
    import os

    # Create results directory
    os.makedirs("./results", exist_ok=True)

    runner = BenchmarkRunner()

    print("\n" + "="*80)
    print("CAN'T STOP COMPREHENSIVE BENCHMARK SUITE")
    print("="*80)
    print(f"\nTotal strategies: {len(runner.strategies)}")
    print("\nStrategies:")
    for i, name in enumerate(sorted(runner.strategies.keys()), 1):
        print(f"  {i:2d}. {name}")

    # Run benchmarks
    print("\n" + "="*80)
    print("Starting benchmarks...")
    print("="*80)

    # Single-player (1000 trials per strategy)
    single_player_results = runner.run_single_player_benchmark(num_trials=1000)

    # Head-to-head (2500 games per matchup - 38*38 = 1444 matchups)
    head_to_head_results = runner.run_head_to_head_tournament(games_per_matchup=2500)

    # Generate summary
    runner.generate_summary_report(single_player_results, head_to_head_results)

    print("\n" + "="*80)
    print("BENCHMARK COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    main()
