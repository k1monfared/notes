#!/usr/bin/env python3
"""
Extended Can't Stop analysis with additional strategies and edge cases.
"""

import sys
import random
from itertools import product, combinations
from typing import List, Tuple, Dict
from collections import defaultdict

# Import base functions from original analysis
sys.path.insert(0, '/home/k1/public/notes/blog/files/20251201')
from cant_stop_analysis import (
    get_pairings, calculate_combination_stats, GameState,
    Strategy, GreedyStrategy, simulate_game
)

# ============================================================================
# Extended Strategies
# ============================================================================

class ConservativeStrategy(Strategy):
    """Stops after making some progress. Handles edge cases for short columns."""

    def __init__(self, stop_threshold: int = 2):
        self.stop_threshold = stop_threshold

    def choose_pairing(self, game: GameState, valid_pairings):
        # Prefer clean pairings
        for sums, pairing in valid_pairings:
            if all(s in game.active_columns for s in sums if game.is_column_available(s)):
                return (sums, pairing)
        return GreedyStrategy().choose_pairing(game, valid_pairings)

    def should_stop(self, game: GameState, dice_result):
        if not game.active_columns:
            return False

        total_progress = sum(game.temp_progress.values())

        # Edge case: if all active columns are short (≤3 steps), stop earlier
        max_length = max(game.column_lengths[col] for col in game.active_columns)
        if max_length <= 3 and total_progress >= min(1, self.stop_threshold):
            return True

        return total_progress >= self.stop_threshold

class HeuristicStrategy(Strategy):
    """Uses mathematical heuristic with explicit Q calculation."""

    def __init__(self, risk_tolerance: float = 1.0):
        self.risk_tolerance = risk_tolerance
        self.combo_stats = {}

    def get_combo_stats(self, columns: Tuple[int, ...]) -> Dict:
        key = tuple(sorted(columns))
        if key not in self.combo_stats:
            self.combo_stats[key] = calculate_combination_stats(key)
        return self.combo_stats[key]

    def choose_pairing(self, game: GameState, valid_pairings):
        active = game.active_columns
        for sums, pairing in valid_pairings:
            available_sums = [s for s in sums if game.is_column_available(s)]
            if all(s in active for s in available_sums):
                return (sums, pairing)
        return GreedyStrategy().choose_pairing(game, valid_pairings)

    def should_stop(self, game: GameState, dice_result):
        if not game.active_columns:
            return False

        stats = self.get_combo_stats(tuple(sorted(game.active_columns)))
        P_success = stats['success_prob']
        P_bust = stats['bust_prob']
        Q = stats['Q']

        unsaved = sum(game.temp_progress.values())

        expected_gain = P_success * Q
        expected_loss = P_bust * unsaved * self.risk_tolerance

        return expected_loss > expected_gain

class OpponentAwareStrategy(Strategy):
    """Adjusts risk based on opponent positions with configurable alpha range."""

    def __init__(self, alpha_behind: float = 0.5, alpha_tied: float = 1.0, alpha_ahead: float = 2.0):
        self.alpha_behind = alpha_behind
        self.alpha_tied = alpha_tied
        self.alpha_ahead = alpha_ahead
        self.combo_stats = {}

    def get_combo_stats(self, columns: Tuple[int, ...]) -> Dict:
        key = tuple(sorted(columns))
        if key not in self.combo_stats:
            self.combo_stats[key] = calculate_combination_stats(key)
        return self.combo_stats[key]

    def choose_pairing(self, game: GameState, valid_pairings):
        active = game.active_columns
        for sums, pairing in valid_pairings:
            available_sums = [s for s in sums if game.is_column_available(s)]
            if all(s in active for s in available_sums):
                return (sums, pairing)
        return GreedyStrategy().choose_pairing(game, valid_pairings)

    def should_stop(self, game: GameState, dice_result):
        if not game.active_columns:
            return False

        # Calculate position
        current_player = game.current_player
        my_completed = sum(1 for col, p in game.completed.items() if p == current_player)

        opponent_best = 0
        for opp in range(game.num_players):
            if opp != current_player:
                opp_completed = sum(1 for col, p in game.completed.items() if p == opp)
                opponent_best = max(opponent_best, opp_completed)

        # Choose alpha based on position
        if my_completed < opponent_best:
            risk_tolerance = self.alpha_behind
        elif my_completed > opponent_best:
            risk_tolerance = self.alpha_ahead
        else:
            risk_tolerance = self.alpha_tied

        # Use heuristic with adjusted risk
        stats = self.get_combo_stats(tuple(sorted(game.active_columns)))
        P_success = stats['success_prob']
        P_bust = stats['bust_prob']
        Q = stats['Q']

        unsaved = sum(game.temp_progress.values())

        # Adjust for column value
        column_values = []
        for col in game.active_columns:
            base_value = 1.0
            my_pos = game.positions[current_player][col] + game.temp_progress.get(col, 0)
            for opp in range(game.num_players):
                if opp != current_player:
                    opp_pos = game.positions[opp][col]
                    if opp_pos > my_pos:
                        base_value *= 0.5
            column_values.append(base_value)

        avg_column_value = sum(column_values) / len(column_values) if column_values else 1.0

        expected_gain = P_success * Q * avg_column_value
        expected_loss = P_bust * unsaved * risk_tolerance

        return expected_loss > expected_gain

class RandomStrategy(Strategy):
    """Makes random decisions. Baseline for comparison."""

    def __init__(self, stop_probability: float = 0.3):
        self.stop_probability = stop_probability

    def choose_pairing(self, game: GameState, valid_pairings):
        return random.choice(valid_pairings)

    def should_stop(self, game: GameState, dice_result):
        # Stop randomly with given probability
        return random.random() < self.stop_probability

class GreedyImproved1(Strategy):
    """Greedy but stops after making progress on all 3 columns."""

    def choose_pairing(self, game: GameState, valid_pairings):
        return GreedyStrategy().choose_pairing(game, valid_pairings)

    def should_stop(self, game: GameState, dice_result):
        # Stop once we've advanced all 3 active columns at least once
        if len(game.active_columns) == 3:
            return all(game.temp_progress.get(col, 0) > 0 for col in game.active_columns)
        return False

class GreedyImproved2(Strategy):
    """Greedy but stops once unsaved progress >= 5."""

    def choose_pairing(self, game: GameState, valid_pairings):
        return GreedyStrategy().choose_pairing(game, valid_pairings)

    def should_stop(self, game: GameState, dice_result):
        total_progress = sum(game.temp_progress.values())
        return total_progress >= 5

class AdaptiveThreshold(Strategy):
    """Adjusts stopping threshold based on column combination quality."""

    def __init__(self):
        self.combo_stats = {}

    def get_combo_stats(self, columns: Tuple[int, ...]) -> Dict:
        key = tuple(sorted(columns))
        if key not in self.combo_stats:
            self.combo_stats[key] = calculate_combination_stats(key)
        return self.combo_stats[key]

    def choose_pairing(self, game: GameState, valid_pairings):
        active = game.active_columns
        for sums, pairing in valid_pairings:
            available_sums = [s for s in sums if game.is_column_available(s)]
            if all(s in active for s in available_sums):
                return (sums, pairing)
        return GreedyStrategy().choose_pairing(game, valid_pairings)

    def should_stop(self, game: GameState, dice_result):
        if not game.active_columns:
            return False

        stats = self.get_combo_stats(tuple(sorted(game.active_columns)))
        P_success = stats['success_prob']

        # Higher success rate → higher threshold
        # Good combinations {6,7,8} with 92% success → threshold ~4-5
        # Bad combinations {2,3,12} with 44% success → threshold ~1-2
        threshold = int(1 + P_success * 5)

        total_progress = sum(game.temp_progress.values())
        return total_progress >= threshold

class ProportionalThreshold(Strategy):
    """Stops when progress reaches a fraction of remaining column length."""

    def __init__(self, fraction: float = 0.5):
        """
        fraction: stop when unsaved progress >= fraction * min(remaining steps on active columns)
        fraction=0.5: stop at halfway
        fraction=0.33: stop at one-third
        """
        self.fraction = fraction

    def choose_pairing(self, game: GameState, valid_pairings):
        active = game.active_columns
        for sums, pairing in valid_pairings:
            available_sums = [s for s in sums if game.is_column_available(s)]
            if all(s in active for s in available_sums):
                return (sums, pairing)
        return GreedyStrategy().choose_pairing(game, valid_pairings)

    def should_stop(self, game: GameState, dice_result):
        if not game.active_columns:
            return False

        # Calculate minimum remaining steps across active columns
        min_remaining = float('inf')
        for col in game.active_columns:
            current_pos = game.positions[game.current_player][col]
            column_length = game.column_lengths[col]
            remaining = column_length - current_pos
            min_remaining = min(min_remaining, remaining)

        # Stop when unsaved progress >= fraction * min_remaining
        threshold = max(1, int(self.fraction * min_remaining))
        total_progress = sum(game.temp_progress.values())

        return total_progress >= threshold

class GreedyUntilFraction(Strategy):
    """Greedy but stops once any column reaches a fraction of completion."""

    def __init__(self, fraction: float = 0.5):
        """
        Stop when any active column has progressed >= fraction * its total length this turn
        """
        self.fraction = fraction

    def choose_pairing(self, game: GameState, valid_pairings):
        return GreedyStrategy().choose_pairing(game, valid_pairings)

    def should_stop(self, game: GameState, dice_result):
        if not game.active_columns:
            return False

        # Check if any column has reached the fraction
        for col in game.active_columns:
            column_length = game.column_lengths[col]
            progress_this_turn = game.temp_progress.get(col, 0)
            if progress_this_turn >= self.fraction * column_length:
                return True

        return False

class FiftyPercentSurvival(Strategy):
    """Rolls until cumulative survival probability drops below 50%."""

    def __init__(self):
        self.combo_stats = {}
        self.roll_count = 0

    def get_combo_stats(self, columns: Tuple[int, ...]) -> Dict:
        key = tuple(sorted(columns))
        if key not in self.combo_stats:
            self.combo_stats[key] = calculate_combination_stats(key)
        return self.combo_stats[key]

    def choose_pairing(self, game: GameState, valid_pairings):
        active = game.active_columns
        for sums, pairing in valid_pairings:
            available_sums = [s for s in sums if game.is_column_available(s)]
            if all(s in active for s in available_sums):
                return (sums, pairing)
        return GreedyStrategy().choose_pairing(game, valid_pairings)

    def should_stop(self, game: GameState, dice_result):
        if not game.active_columns:
            self.roll_count = 0
            return False

        # Get success probability for current columns
        stats = self.get_combo_stats(tuple(sorted(game.active_columns)))
        P_success = stats['success_prob']

        # Calculate cumulative survival probability after n rolls: P_success^n
        # Stop when P_success^n < 0.5
        # Equivalently: n > log(0.5) / log(P_success)

        if P_success <= 0:
            return True  # Can't continue
        if P_success >= 1.0:
            return False  # Never stop (though this shouldn't happen)

        import math
        # How many rolls until 50% survival?
        target_rolls = math.log(0.5) / math.log(P_success)

        self.roll_count += 1
        should_stop_now = self.roll_count >= target_rolls

        if should_stop_now:
            self.roll_count = 0

        return should_stop_now

class ExpectedValueMaximizer(Strategy):
    """Stops when expected value of continuing becomes negative."""

    def __init__(self):
        self.combo_stats = {}

    def get_combo_stats(self, columns: Tuple[int, ...]) -> Dict:
        key = tuple(sorted(columns))
        if key not in self.combo_stats:
            self.combo_stats[key] = calculate_combination_stats(key)
        return self.combo_stats[key]

    def choose_pairing(self, game: GameState, valid_pairings):
        active = game.active_columns
        for sums, pairing in valid_pairings:
            available_sums = [s for s in sums if game.is_column_available(s)]
            if all(s in active for s in available_sums):
                return (sums, pairing)
        return GreedyStrategy().choose_pairing(game, valid_pairings)

    def should_stop(self, game: GameState, dice_result):
        if not game.active_columns:
            return False

        stats = self.get_combo_stats(tuple(sorted(game.active_columns)))
        P_success = stats['success_prob']
        P_bust = stats['bust_prob']
        Q = stats['Q']

        unsaved = sum(game.temp_progress.values())

        # Expected value of rolling again:
        # EV = P_success * Q (expected gain) - P_bust * unsaved (expected loss)
        # Stop when EV <= 0

        expected_gain = P_success * Q
        expected_loss = P_bust * unsaved

        return expected_loss >= expected_gain

class GreedyUntilOneColumn(Strategy):
    """Rolls until completing at least one column, then stops immediately."""

    def choose_pairing(self, game: GameState, valid_pairings):
        return GreedyStrategy().choose_pairing(game, valid_pairings)

    def should_stop(self, game: GameState, dice_result):
        # Check if we just completed a column this turn
        for col in game.temp_progress:
            current_pos = game.positions[game.current_player][col]
            temp = game.temp_progress[col]
            if current_pos + temp >= game.column_lengths[col]:
                # We've completed a column, stop now
                return True
        return False

class GreedyUntilThreeColumns(Strategy):
    """Rolls until completing three columns total (wins the game), never stops otherwise."""

    def choose_pairing(self, game: GameState, valid_pairings):
        return GreedyStrategy().choose_pairing(game, valid_pairings)

    def should_stop(self, game: GameState, dice_result):
        # Count how many columns this player has completed
        completed_count = sum(1 for col, player in game.completed.items() if player == game.current_player)

        # Check if banking now would complete any additional columns
        about_to_complete = 0
        for col in game.temp_progress:
            current_pos = game.positions[game.current_player][col]
            temp = game.temp_progress[col]
            if current_pos + temp >= game.column_lengths[col]:
                about_to_complete += 1

        # Stop if we would have 3+ completed columns after banking
        return (completed_count + about_to_complete) >= 3

# ============================================================================
# Extended Testing
# ============================================================================

def comprehensive_strategy_comparison_extended(num_games: int = 200):
    """Run comprehensive head-to-head with extended strategies."""
    print(f"\nExtended Strategy Comparison ({num_games} games each):")
    print("=" * 80)

    strategy_classes = {
        'Greedy': GreedyStrategy(),
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
        'GreedyUntil3Col': GreedyUntilThreeColumns(),
    }

    # Head-to-head matrix
    results = defaultdict(lambda: defaultdict(int))

    strategies_list = list(strategy_classes.keys())
    total_matchups = len(strategies_list) * (len(strategies_list) - 1) // 2
    current = 0

    for i, strat1_name in enumerate(strategies_list):
        for j, strat2_name in enumerate(strategies_list):
            if i >= j:
                continue

            current += 1
            if current % 10 == 0:
                print(f"[{current}/{total_matchups}] Completed...")

            wins = [0, 0]
            for _ in range(num_games):
                winner = simulate_game([strategy_classes[strat1_name], strategy_classes[strat2_name]])
                wins[winner] += 1

            results[strat1_name][strat2_name] = wins[0]
            results[strat2_name][strat1_name] = wins[1]

    # Print summary
    print("\n" + "=" * 80)
    print("\nOverall Performance (total wins against all opponents):")
    print("-" * 80)

    total_wins = {}
    total_games = {}

    for strat in strategies_list:
        total_wins[strat] = sum(results[strat].values())
        total_games[strat] = sum(results[strat].values()) + sum(results[other][strat] for other in strategies_list if other != strat)

    # Sort by win rate
    sorted_strats = sorted(strategies_list, key=lambda s: total_wins[s] / total_games[s] if total_games[s] > 0 else 0, reverse=True)

    for rank, strat in enumerate(sorted_strats, 1):
        wins = total_wins[strat]
        games = total_games[strat]
        win_rate = wins / games if games > 0 else 0
        print(f"{rank:2}. {strat:<25} {wins:>4}/{games:<4} games ({win_rate:.1%})")

    # Print key matchups
    print("\n" + "=" * 80)
    print("\nKey Matchups:")
    print("-" * 80)

    interesting_pairs = [
        ('Conservative(3)', 'Heuristic(1.0)'),
        ('GreedyImproved2', 'Conservative(3)'),
        ('AdaptiveThreshold', 'Heuristic(1.0)'),
        ('Proportional(0.5)', 'Conservative(3)'),
        ('GreedyFraction(0.5)', 'GreedyImproved2'),
        ('Proportional(0.33)', 'Proportional(0.5)'),
        ('Random(0.3)', 'Greedy'),
        ('FiftyPercentSurvival', 'GreedyImproved2'),
        ('ExpectedValueMax', 'Conservative(3)'),
        ('FiftyPercentSurvival', 'ExpectedValueMax'),
    ]

    for strat1, strat2 in interesting_pairs:
        if strat1 in results and strat2 in results[strat1]:
            total = results[strat1][strat2] + results[strat2][strat1]
            win_rate1 = results[strat1][strat2] / total if total > 0 else 0
            print(f"{strat1:<25} vs {strat2:<25} : {win_rate1:>5.1%} win rate")

    # Print full win-rate matrix
    print("\n" + "=" * 80)
    print("\nFull Win-Rate Matrix (row vs column):")
    print("-" * 80)

    # Header row
    print(f"{'Strategy':<25}", end="")
    for strat in strategies_list:
        # Abbreviate strategy names for column headers
        abbrev = strat[:7]
        print(f"{abbrev:>8}", end="")
    print()
    print("-" * (25 + 8 * len(strategies_list)))

    # Data rows
    for strat1 in strategies_list:
        print(f"{strat1:<25}", end="")
        for strat2 in strategies_list:
            if strat1 == strat2:
                print(f"{'--':>8}", end="")
            elif strat2 in results[strat1]:
                total = results[strat1][strat2] + results[strat2][strat1]
                win_rate = results[strat1][strat2] / total if total > 0 else 0
                print(f"{win_rate:>7.1%} ", end="")
            else:
                print(f"{'N/A':>8}", end="")
        print()

    return results, sorted_strats

if __name__ == "__main__":
    print("Extended Can't Stop Strategy Analysis")
    print("=" * 80)

    results, rankings = comprehensive_strategy_comparison_extended(2500)

    print("\n" + "=" * 80)
    print("Analysis complete!")
