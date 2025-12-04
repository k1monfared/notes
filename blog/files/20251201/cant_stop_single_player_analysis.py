#!/usr/bin/env python3
"""
Single-player analysis for Can't Stop strategies.
Analyzes how many turns it takes for each strategy to complete 1 or 3 columns.
This is independent of opponent behavior.
"""

import sys
import random
from itertools import product
from typing import List, Tuple, Dict
from collections import defaultdict

sys.path.insert(0, '/home/k1/public/notes/blog/files/20251201')
from cant_stop_analysis import (
    get_pairings, calculate_combination_stats, GameState,
    Strategy, GreedyStrategy
)

# ============================================================================
# Single-Player Simulation
# ============================================================================

def simulate_single_player(strategy: Strategy, target_columns: int = 3, num_trials: int = 1000) -> Dict:
    """
    Simulate a single player using a strategy until they complete target_columns.

    Returns:
        - avg_turns: average number of turns to complete target_columns
        - avg_rolls: average total number of rolls
        - avg_busts: average number of busts
        - turn_distribution: histogram of turns needed
    """
    results = {
        'turns': [],
        'total_rolls': [],
        'busts': [],
    }

    for trial in range(num_trials):
        game = GameState(num_players=1)
        game.current_player = 0

        turns = 0
        total_rolls = 0
        busts = 0

        while len([c for c in game.completed.values() if c == 0]) < target_columns:
            turns += 1
            turn_rolls = 0
            game.active_columns = []
            game.temp_progress = {}

            while True:
                turn_rolls += 1
                dice = game.roll_dice()
                valid_pairings = game.get_valid_pairings(dice)

                if not valid_pairings:
                    # Bust
                    busts += 1
                    break

                # Strategy chooses pairing
                sums, pairing = strategy.choose_pairing(game, valid_pairings)
                game.apply_move(sums)

                # Check if strategy wants to stop
                if strategy.should_stop(game, dice):
                    # Bank progress
                    for col in game.temp_progress:
                        game.positions[0][col] += game.temp_progress[col]
                        if game.positions[0][col] >= game.column_lengths[col]:
                            game.completed[col] = 0
                    break

            total_rolls += turn_rolls

        results['turns'].append(turns)
        results['total_rolls'].append(total_rolls)
        results['busts'].append(busts)

    return {
        'avg_turns': sum(results['turns']) / len(results['turns']),
        'avg_rolls': sum(results['total_rolls']) / len(results['total_rolls']),
        'avg_busts': sum(results['busts']) / len(results['busts']),
        'median_turns': sorted(results['turns'])[len(results['turns']) // 2],
        'min_turns': min(results['turns']),
        'max_turns': max(results['turns']),
    }


def single_player_analysis_for_specific_columns(strategy: Strategy, target_columns: List[int], num_trials: int = 1000) -> Dict:
    """
    Simulate completing a specific set of columns (e.g., column 7, or columns {6,7,8}).

    Returns average turns and rolls to complete ALL specified columns.
    """
    results = {
        'turns': [],
        'total_rolls': [],
        'busts': [],
    }

    for trial in range(num_trials):
        game = GameState(num_players=1)
        game.current_player = 0

        turns = 0
        total_rolls = 0
        busts = 0

        # Continue until all target columns are completed
        while not all(game.completed[col] == 0 for col in target_columns):
            turns += 1
            turn_rolls = 0
            game.active_columns = []
            game.temp_progress = {}

            while True:
                turn_rolls += 1
                dice = game.roll_dice()
                valid_pairings = game.get_valid_pairings(dice)

                if not valid_pairings:
                    busts += 1
                    break

                sums, pairing = strategy.choose_pairing(game, valid_pairings)
                game.apply_move(sums)

                if strategy.should_stop(game, dice):
                    for col in game.temp_progress:
                        game.positions[0][col] += game.temp_progress[col]
                        if game.positions[0][col] >= game.column_lengths[col]:
                            game.completed[col] = 0
                    break

            total_rolls += turn_rolls

        results['turns'].append(turns)
        results['total_rolls'].append(total_rolls)
        results['busts'].append(busts)

    return {
        'avg_turns': sum(results['turns']) / len(results['turns']),
        'avg_rolls': sum(results['total_rolls']) / len(results['total_rolls']),
        'avg_busts': sum(results['busts']) / len(results['busts']),
        'median_turns': sorted(results['turns'])[len(results['turns']) // 2],
    }


# ============================================================================
# Mathematical Analysis
# ============================================================================

def mathematical_expected_turns_single_column(column: int) -> Dict:
    """
    Calculate expected turns to complete a single column mathematically.

    For a column with length L and probability P:
    - Expected rolls to complete: L / P
    - But this doesn't account for turns (which include busting)

    More accurately: need to model turn structure with dynamic programming.
    This is a simplified approximation.
    """
    # Get probability of hitting this column
    all_rolls = list(product(range(1, 7), repeat=4))
    hits = 0
    for roll in all_rolls:
        for pairing in get_pairings(roll):
            if sum(pairing[0]) == column or sum(pairing[1]) == column:
                hits += 1
                break

    P_hit = hits / len(all_rolls)

    # Column length
    lengths = {2: 3, 3: 5, 4: 7, 5: 9, 6: 11, 7: 13, 8: 11, 9: 9, 10: 7, 11: 5, 12: 3}
    L = lengths[column]

    # Expected rolls to complete (if never busting): L / P_hit
    expected_rolls = L / P_hit

    # For a rough turn estimate, assume a strategy stops after some threshold
    # This is highly strategy-dependent, so we'll report "rolls needed" instead

    return {
        'column': column,
        'length': L,
        'hit_probability': P_hit,
        'expected_rolls': expected_rolls,
    }


def mathematical_expected_turns_three_columns(columns: Tuple[int, int, int]) -> Dict:
    """
    Estimate expected turns to complete three specific columns.

    This is complex because:
    1. You can work on multiple columns per turn
    2. Busting probability depends on which columns you're on
    3. Progress is correlated (hitting one column affects which you work on next)

    We'll use combination statistics and simulation instead for accuracy.
    """
    stats = calculate_combination_stats(columns)

    # Total steps needed
    lengths = {2: 3, 3: 5, 4: 7, 5: 9, 6: 11, 7: 13, 8: 11, 9: 9, 10: 7, 11: 5, 12: 3}
    total_steps = sum(lengths[c] for c in columns)

    # Expected progress per successful roll
    Q = stats['Q']

    # Expected rolls per turn (geometric distribution)
    P_success = stats['success_prob']
    P_bust = stats['bust_prob']
    if P_bust > 0:
        expected_rolls_per_turn = P_success / P_bust
    else:
        expected_rolls_per_turn = float('inf')

    # Expected progress per turn
    expected_progress_per_turn = expected_rolls_per_turn * Q

    # Expected turns
    if expected_progress_per_turn > 0:
        expected_turns = total_steps / expected_progress_per_turn
    else:
        expected_turns = float('inf')

    return {
        'columns': columns,
        'total_steps': total_steps,
        'success_prob': P_success,
        'Q': Q,
        'expected_rolls_per_turn': expected_rolls_per_turn,
        'expected_progress_per_turn': expected_progress_per_turn,
        'expected_turns': expected_turns,
    }


# ============================================================================
# Test Functions
# ============================================================================

def test_single_column_analysis():
    """Test single-player analysis for completing one column."""
    print("=" * 80)
    print("Single Column Completion Analysis")
    print("=" * 80)

    from cant_stop_analysis import ConservativeStrategy

    # Test a few strategies on column 7
    strategies = {
        'Conservative(2)': ConservativeStrategy(stop_threshold=2),
        'Conservative(3)': ConservativeStrategy(stop_threshold=3),
    }

    print("\nMathematical Analysis (Column 7):")
    print("-" * 80)
    math_result = mathematical_expected_turns_single_column(7)
    print(f"Column: {math_result['column']}")
    print(f"Length: {math_result['length']} steps")
    print(f"Hit Probability: {math_result['hit_probability']:.1%}")
    print(f"Expected Rolls Needed: {math_result['expected_rolls']:.2f}")

    print("\n\nSimulation Results (completing column 7 only):")
    print("-" * 80)
    for name, strategy in strategies.items():
        result = single_player_analysis_for_specific_columns(strategy, [7], num_trials=500)
        print(f"\n{name}:")
        print(f"  Avg Turns: {result['avg_turns']:.2f}")
        print(f"  Median Turns: {result['median_turns']:.0f}")
        print(f"  Avg Total Rolls: {result['avg_rolls']:.2f}")
        print(f"  Avg Busts: {result['avg_busts']:.2f}")


def test_three_column_analysis():
    """Test single-player analysis for completing three columns."""
    print("\n\n" + "=" * 80)
    print("Three Column Completion Analysis")
    print("=" * 80)

    from cant_stop_analysis import ConservativeStrategy

    strategies = {
        'Conservative(2)': ConservativeStrategy(stop_threshold=2),
        'Conservative(3)': ConservativeStrategy(stop_threshold=3),
    }

    # Test best combination {6,7,8}
    print("\nMathematical Analysis (Columns {6,7,8}):")
    print("-" * 80)
    math_result = mathematical_expected_turns_three_columns((6, 7, 8))
    print(f"Columns: {math_result['columns']}")
    print(f"Total Steps: {math_result['total_steps']}")
    print(f"Success Probability: {math_result['success_prob']:.1%}")
    print(f"Q (expected markers per roll): {math_result['Q']:.2f}")
    print(f"Expected Rolls per Turn: {math_result['expected_rolls_per_turn']:.2f}")
    print(f"Expected Progress per Turn: {math_result['expected_progress_per_turn']:.2f} steps")
    print(f"Expected Turns to Complete: {math_result['expected_turns']:.2f}")

    print("\n\nSimulation Results:")
    print("-" * 80)
    for name, strategy in strategies.items():
        result = simulate_single_player(strategy, target_columns=3, num_trials=500)
        print(f"\n{name}:")
        print(f"  Avg Turns: {result['avg_turns']:.2f}")
        print(f"  Median Turns: {result['median_turns']:.0f}")
        print(f"  Avg Total Rolls: {result['avg_rolls']:.2f}")
        print(f"  Avg Busts: {result['avg_busts']:.2f}")


if __name__ == "__main__":
    print("Can't Stop: Single-Player Analysis")
    print("=" * 80)

    test_single_column_analysis()
    test_three_column_analysis()

    print("\n" + "=" * 80)
    print("Analysis complete!")
