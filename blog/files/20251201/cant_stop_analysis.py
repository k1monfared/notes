#!/usr/bin/env python3
"""
Comprehensive Can't Stop probability analysis and game simulation.
Generates all combination probabilities and validates strategies.
"""

from itertools import product, combinations
import random
from typing import List, Tuple, Dict, Set
from collections import defaultdict

# ============================================================================
# Part 1: Probability Calculations
# ============================================================================

def get_pairings(dice: Tuple[int, int, int, int]) -> List[List[Tuple[int, int]]]:
    """Get all 3 possible pairings of 4 dice."""
    d1, d2, d3, d4 = dice
    return [
        [(d1, d2), (d3, d4)],
        [(d1, d3), (d2, d4)],
        [(d1, d4), (d2, d3)]
    ]

def can_make_sum(dice: Tuple[int, int, int, int], target: int) -> bool:
    """Check if 4 dice can be paired to make target sum."""
    for pairing in get_pairings(dice):
        for pair in pairing:
            if sum(pair) == target:
                return True
    return False

def can_make_any_sum(dice: Tuple[int, int, int, int], targets: List[int]) -> bool:
    """Check if we can make any sum from targets."""
    for pairing in get_pairings(dice):
        sums = {sum(pair) for pair in pairing}
        if any(target in sums for target in targets):
            return True
    return False

def can_make_clean_move(dice: Tuple[int, int, int, int], targets: List[int]) -> bool:
    """Check if we can make a move using ONLY target columns (forced-move rule)."""
    for pairing in get_pairings(dice):
        sums = [sum(pair) for pair in pairing]
        # This pairing is clean if all its sums are in targets
        if all(s in targets for s in sums):
            return True
    return False

def expected_markers_advanced(columns: List[int]) -> float:
    """Calculate E[markers advanced | success] for given columns."""
    all_rolls = list(product(range(1, 7), repeat=4))
    successful_rolls = []

    for roll in all_rolls:
        max_markers = 0
        for pairing in get_pairings(roll):
            markers = sum(1 for pair in pairing if sum(pair) in columns)
            max_markers = max(max_markers, markers)

        if max_markers > 0:
            successful_rolls.append(max_markers)

    return sum(successful_rolls) / len(successful_rolls) if successful_rolls else 0

def calculate_combination_stats(columns: Tuple[int, int, int]) -> Dict:
    """Calculate all statistics for a 3-column combination."""
    all_rolls = list(product(range(1, 7), repeat=4))
    total = len(all_rolls)

    # Basic success/bust
    success_count = sum(1 for roll in all_rolls if can_make_any_sum(roll, list(columns)))
    bust_count = total - success_count

    # Clean moves (respecting forced-move rule)
    clean_count = sum(1 for roll in all_rolls if can_make_clean_move(roll, list(columns)))

    # Expected markers advanced
    Q = expected_markers_advanced(list(columns))

    return {
        'columns': columns,
        'success_count': success_count,
        'success_prob': success_count / total,
        'bust_prob': bust_count / total,
        'clean_count': clean_count,
        'clean_prob': clean_count / total,
        'Q': Q
    }

def generate_all_combinations():
    """Generate statistics for all 165 possible 3-column combinations."""
    all_columns = range(2, 13)
    all_combos = list(combinations(all_columns, 3))

    results = []
    for combo in all_combos:
        stats = calculate_combination_stats(combo)
        results.append(stats)

    # Sort by success probability (descending)
    results.sort(key=lambda x: x['success_prob'], reverse=True)

    return results

# ============================================================================
# Part 2: Game Simulation
# ============================================================================

class GameState:
    """Represents the state of a Can't Stop game."""

    def __init__(self, num_players: int = 2):
        self.num_players = num_players
        # Column lengths from the actual game
        self.column_lengths = {
            2: 3, 3: 5, 4: 7, 5: 9, 6: 11, 7: 13,
            8: 11, 9: 9, 10: 7, 11: 5, 12: 3
        }
        # Player positions (saved progress)
        self.positions = [{col: 0 for col in range(2, 13)} for _ in range(num_players)]
        # Completed columns (removed from game)
        self.completed = {col: None for col in range(2, 13)}  # None or player_id
        # Current turn state
        self.current_player = 0
        self.active_columns = []  # Up to 3 columns being worked on this turn
        self.temp_progress = {}  # Unsaved progress this turn
        self.free_pegs = 3

    def is_column_available(self, col: int) -> bool:
        """Check if column is still available to play."""
        return self.completed[col] is None

    def get_available_columns(self) -> List[int]:
        """Get list of columns still in play."""
        return [col for col in range(2, 13) if self.is_column_available(col)]

    def roll_dice(self) -> Tuple[int, int, int, int]:
        """Roll 4 dice."""
        return tuple(random.randint(1, 6) for _ in range(4))

    def get_valid_pairings(self, dice: Tuple[int, int, int, int]) -> List[Tuple[List[int], List[Tuple[int, int]]]]:
        """
        Get valid pairings that allow at least one move.
        Returns list of (sums, pairing) tuples.
        """
        valid = []
        for pairing in get_pairings(dice):
            sums = [sum(pair) for pair in pairing]
            # Check if at least one sum can be used
            can_move = False
            for s in sums:
                # Can use this sum if:
                # 1. Column is available
                # 2. Either already active this turn OR we have a free peg
                if self.is_column_available(s):
                    if s in self.active_columns or len(self.active_columns) < 3:
                        can_move = True
                        break
            if can_move:
                valid.append((sums, pairing))
        return valid

    def apply_move(self, sums: List[int]):
        """
        Apply a move (forced to take all valid sums from chosen pairing).
        """
        for s in sums:
            if not self.is_column_available(s):
                continue

            # If not already active, activate it
            if s not in self.active_columns:
                if len(self.active_columns) >= 3:
                    continue  # Can't activate more columns
                self.active_columns.append(s)
                self.temp_progress[s] = 0

            # Advance the marker
            current_pos = self.positions[self.current_player][s] + self.temp_progress[s]
            if current_pos < self.column_lengths[s]:
                self.temp_progress[s] += 1

    def bank_progress(self):
        """Save temporary progress for current player."""
        for col, progress in self.temp_progress.items():
            self.positions[self.current_player][col] += progress
            # Check if column completed
            if self.positions[self.current_player][col] >= self.column_lengths[col]:
                self.completed[col] = self.current_player
        self.temp_progress = {}
        self.active_columns = []

    def bust(self):
        """Lose all temporary progress."""
        self.temp_progress = {}
        self.active_columns = []

    def check_winner(self) -> int:
        """Check if current player has won (completed 3 columns). Returns player_id or -1."""
        completed_count = sum(1 for col, player in self.completed.items() if player == self.current_player)
        if completed_count >= 3:
            return self.current_player
        return -1

    def next_player(self):
        """Move to next player's turn."""
        self.current_player = (self.current_player + 1) % self.num_players

# ============================================================================
# Part 3: Strategies
# ============================================================================

class Strategy:
    """Base class for playing strategies."""

    def choose_pairing(self, game: GameState, valid_pairings: List[Tuple[List[int], List[Tuple[int, int]]]]) -> Tuple[List[int], List[Tuple[int, int]]]:
        """Choose which pairing to use."""
        raise NotImplementedError

    def should_stop(self, game: GameState, dice_result: Tuple[int, int, int, int]) -> bool:
        """Decide whether to stop rolling (before seeing roll result)."""
        raise NotImplementedError

class GreedyStrategy(Strategy):
    """Always rolls until bust. Prefers pairings that advance most markers."""

    def choose_pairing(self, game: GameState, valid_pairings: List[Tuple[List[int], List[Tuple[int, int]]]]) -> Tuple[List[int], List[Tuple[int, int]]]:
        # Count how many active columns each pairing hits
        best = None
        best_score = -1

        for sums, pairing in valid_pairings:
            score = sum(1 for s in sums if s in game.active_columns)
            # Tiebreaker: prefer middle columns
            if score == best_score and best is not None:
                score += sum(0.1 / max(1, abs(s - 7)) for s in sums if game.is_column_available(s))
            if score > best_score:
                best_score = score
                best = (sums, pairing)

        return best if best else valid_pairings[0]

    def should_stop(self, game: GameState, dice_result: Tuple[int, int, int, int]) -> bool:
        return False  # Never stop

class ConservativeStrategy(Strategy):
    """Stops after making some progress. Prefers clean moves."""

    def __init__(self, stop_threshold: int = 2):
        self.stop_threshold = stop_threshold

    def choose_pairing(self, game: GameState, valid_pairings: List[Tuple[List[int], List[Tuple[int, int]]]]) -> Tuple[List[int], List[Tuple[int, int]]]:
        # Prefer clean pairings (all sums in active columns)
        for sums, pairing in valid_pairings:
            if all(s in game.active_columns for s in sums if game.is_column_available(s)):
                return (sums, pairing)

        # Otherwise, prefer pairings that hit most active columns
        return GreedyStrategy().choose_pairing(game, valid_pairings)

    def should_stop(self, game: GameState, dice_result: Tuple[int, int, int, int]) -> bool:
        total_progress = sum(game.temp_progress.values())
        return total_progress >= self.stop_threshold

class HeuristicStrategy(Strategy):
    """Uses the mathematical heuristic: keep rolling if (P_success × Q) > (P_bust × unsaved)."""

    def __init__(self, risk_tolerance: float = 1.0):
        self.risk_tolerance = risk_tolerance
        # Precompute combination stats
        self.combo_stats = {}

    def get_combo_stats(self, columns: Tuple[int, ...]) -> Dict:
        """Get or compute stats for this column combination."""
        key = tuple(sorted(columns))
        if key not in self.combo_stats:
            self.combo_stats[key] = calculate_combination_stats(key)
        return self.combo_stats[key]

    def choose_pairing(self, game: GameState, valid_pairings: List[Tuple[List[int], List[Tuple[int, int]]]]) -> Tuple[List[int], List[Tuple[int, int]]]:
        # Prefer clean moves when possible
        active = game.active_columns
        for sums, pairing in valid_pairings:
            available_sums = [s for s in sums if game.is_column_available(s)]
            if all(s in active for s in available_sums):
                return (sums, pairing)

        # Otherwise prefer moves that advance most active columns
        return GreedyStrategy().choose_pairing(game, valid_pairings)

    def should_stop(self, game: GameState, dice_result: Tuple[int, int, int, int]) -> bool:
        if not game.active_columns:
            return False

        # Calculate expected gain vs risk
        stats = self.get_combo_stats(tuple(sorted(game.active_columns)))
        P_success = stats['success_prob']
        P_bust = stats['bust_prob']
        Q = stats['Q']

        unsaved = sum(game.temp_progress.values())

        expected_gain = P_success * Q
        expected_loss = P_bust * unsaved * self.risk_tolerance

        return expected_loss > expected_gain

class OpponentAwareStrategy(Strategy):
    """Adjusts risk based on opponent positions."""

    def __init__(self, base_strategy: Strategy = None):
        self.base_strategy = base_strategy or HeuristicStrategy()
        self.combo_stats = {}

    def get_combo_stats(self, columns: Tuple[int, ...]) -> Dict:
        key = tuple(sorted(columns))
        if key not in self.combo_stats:
            self.combo_stats[key] = calculate_combination_stats(key)
        return self.combo_stats[key]

    def choose_pairing(self, game: GameState, valid_pairings: List[Tuple[List[int], List[Tuple[int, int]]]]) -> Tuple[List[int], List[Tuple[int, int]]]:
        return self.base_strategy.choose_pairing(game, valid_pairings)

    def should_stop(self, game: GameState, dice_result: Tuple[int, int, int, int]) -> bool:
        if not game.active_columns:
            return False

        # Calculate how far behind/ahead we are
        current_player = game.current_player
        my_completed = sum(1 for col, p in game.completed.items() if p == current_player)

        # Find opponent's best position
        opponent_best = 0
        for opp in range(game.num_players):
            if opp != current_player:
                opp_completed = sum(1 for col, p in game.completed.items() if p == opp)
                opponent_best = max(opponent_best, opp_completed)

        # Adjust risk tolerance based on position
        if my_completed < opponent_best:
            # Behind: take more risk
            risk_tolerance = 0.5
        elif my_completed > opponent_best:
            # Ahead: be more conservative
            risk_tolerance = 2.0
        else:
            # Tied: normal risk
            risk_tolerance = 1.0

        # Use heuristic with adjusted risk
        stats = self.get_combo_stats(tuple(sorted(game.active_columns)))
        P_success = stats['success_prob']
        P_bust = stats['bust_prob']
        Q = stats['Q']

        unsaved = sum(game.temp_progress.values())

        # Adjust for column value (less valuable if opponent is ahead on that column)
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

def play_turn(game: GameState, strategy: Strategy, max_rolls: int = 100) -> bool:
    """
    Play one player's turn using given strategy.
    Returns True if player won, False otherwise.
    """
    for _ in range(max_rolls):
        dice = game.roll_dice()
        valid_pairings = game.get_valid_pairings(dice)

        if not valid_pairings:
            # Bust!
            game.bust()
            return False

        # Choose pairing and apply move
        sums, pairing = strategy.choose_pairing(game, valid_pairings)
        game.apply_move(sums)

        # Check if won
        if game.check_winner() >= 0:
            game.bank_progress()
            return True

        # Decide whether to stop
        if strategy.should_stop(game, dice):
            game.bank_progress()
            return False

    # Max rolls reached, bank progress
    game.bank_progress()
    return False

def simulate_game(strategies: List[Strategy], verbose: bool = False) -> int:
    """
    Simulate a complete game.
    Returns the winning player's index.
    """
    game = GameState(num_players=len(strategies))
    turn_count = 0
    max_turns = 1000  # Prevent infinite games

    while turn_count < max_turns:
        player = game.current_player
        strategy = strategies[player]

        won = play_turn(game, strategy)

        if won or game.check_winner() >= 0:
            if verbose:
                print(f"Player {player} wins after {turn_count + 1} turns!")
            return player

        game.next_player()
        turn_count += 1

    # Game took too long, declare player with most columns as winner
    best_player = 0
    best_count = 0
    for p in range(game.num_players):
        count = sum(1 for col, player in game.completed.items() if player == p)
        if count > best_count:
            best_count = count
            best_player = p

    return best_player

# ============================================================================
# Part 4: Analysis Functions
# ============================================================================

def print_top_combinations(n: int = 20):
    """Print top N combinations by success probability."""
    results = generate_all_combinations()

    print(f"\nTop {n} Column Combinations (by success probability):")
    print("=" * 80)
    print(f"{'Rank':<6} {'Columns':<15} {'Success':<10} {'Bust':<10} {'Clean':<10} {'Q':<8}")
    print("-" * 80)

    for i, stats in enumerate(results[:n], 1):
        cols = "{" + ",".join(map(str, stats['columns'])) + "}"
        print(f"{i:<6} {cols:<15} {stats['success_prob']:.1%}     "
              f"{stats['bust_prob']:.1%}    {stats['clean_prob']:.1%}    "
              f"{stats['Q']:.2f}")

    print("\n" + "=" * 80)
    print(f"\nBottom {n} Column Combinations (worst by success probability):")
    print("-" * 80)

    for i, stats in enumerate(results[-n:], len(results) - n + 1):
        cols = "{" + ",".join(map(str, stats['columns'])) + "}"
        print(f"{i:<6} {cols:<15} {stats['success_prob']:.1%}     "
              f"{stats['bust_prob']:.1%}    {stats['clean_prob']:.1%}    "
              f"{stats['Q']:.2f}")

def validate_opponent_aware_strategy(num_games: int = 100):
    """Validate that opponent-aware strategy performs better."""
    print(f"\nValidating Opponent-Aware Strategy ({num_games} games):")
    print("=" * 80)

    # Test configurations
    configs = [
        ("Greedy vs Greedy", [GreedyStrategy(), GreedyStrategy()]),
        ("Conservative vs Conservative", [ConservativeStrategy(), ConservativeStrategy()]),
        ("Heuristic vs Heuristic", [HeuristicStrategy(), HeuristicStrategy()]),
        ("OpponentAware vs Greedy", [OpponentAwareStrategy(), GreedyStrategy()]),
        ("OpponentAware vs Conservative", [OpponentAwareStrategy(), ConservativeStrategy()]),
        ("OpponentAware vs Heuristic", [OpponentAwareStrategy(), HeuristicStrategy()]),
    ]

    for name, strategies in configs:
        wins = [0, 0]
        for _ in range(num_games):
            winner = simulate_game(strategies)
            wins[winner] += 1

        print(f"\n{name}:")
        print(f"  Player 0: {wins[0]} wins ({wins[0]/num_games:.1%})")
        print(f"  Player 1: {wins[1]} wins ({wins[1]/num_games:.1%})")

def comprehensive_strategy_comparison(num_games: int = 200):
    """Run comprehensive head-to-head between all strategies."""
    print(f"\nComprehensive Strategy Comparison ({num_games} games each):")
    print("=" * 80)

    strategy_classes = {
        'Greedy': GreedyStrategy(),
        'Conservative': ConservativeStrategy(),
        'Conservative(3)': ConservativeStrategy(stop_threshold=3),
        'Heuristic': HeuristicStrategy(),
        'Heuristic(0.5)': HeuristicStrategy(risk_tolerance=0.5),
        'Heuristic(2.0)': HeuristicStrategy(risk_tolerance=2.0),
        'OpponentAware': OpponentAwareStrategy(),
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
            print(f"\n[{current}/{total_matchups}] {strat1_name} vs {strat2_name}...")

            wins = [0, 0]
            for _ in range(num_games):
                winner = simulate_game([strategy_classes[strat1_name], strategy_classes[strat2_name]])
                wins[winner] += 1

            results[strat1_name][strat2_name] = wins[0]
            results[strat2_name][strat1_name] = wins[1]

            print(f"  {strat1_name}: {wins[0]} wins ({wins[0]/num_games:.1%})")
            print(f"  {strat2_name}: {wins[1]} wins ({wins[1]/num_games:.1%})")

    # Print summary matrix
    print("\n" + "=" * 80)
    print("\nWin Rate Matrix (row player vs column player):")
    print("-" * 80)

    # Header
    print(f"{'Strategy':<20}", end="")
    for name in strategies_list:
        print(f"{name[:8]:>8}", end="")
    print()

    # Rows
    for strat1 in strategies_list:
        print(f"{strat1:<20}", end="")
        for strat2 in strategies_list:
            if strat1 == strat2:
                print(f"{'--':>8}", end="")
            else:
                total = results[strat1][strat2] + results[strat2][strat1]
                win_rate = results[strat1][strat2] / total if total > 0 else 0.5
                print(f"{win_rate:>7.1%}", end=" ")
        print()

    # Overall win rates
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
        print(f"{rank}. {strat:<20} {wins:>4}/{games:<4} games ({win_rate:.1%})")

# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    print("Can't Stop: Comprehensive Analysis")
    print("=" * 80)

    # Part 1: Show top combinations
    print_top_combinations(20)

    # Part 2: Validate opponent-aware strategy
    validate_opponent_aware_strategy(100)

    # Part 3: Comprehensive strategy comparison
    comprehensive_strategy_comparison(200)

    print("\n" + "=" * 80)
    print("Analysis complete!")
