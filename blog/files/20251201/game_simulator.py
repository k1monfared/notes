#!/usr/bin/env python3
"""
Can't Stop Game Simulator - Using Correct Backend
Simulates games between strategies using correct partial-pairing mechanics
"""

import sys
import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

# Use local silent version of GameMechanics (with debug prints removed)
try:
    from main_silent import GameMechanics
except ImportError:
    # Fallback to original
    sys.path.insert(0, '/home/k1/public/cantstop-game/backend')
    from main import GameMechanics

# Column lengths constant
COLUMN_LENGTHS = GameMechanics.COLUMN_LENGTHS

# Import strategies
from strategies_correct_implementation import Strategy


@dataclass
class GameResult:
    """Results from a single game."""
    winner: int  # 0 or 1
    turns: int
    player1_columns_completed: int
    player2_columns_completed: int
    player1_strategy: str
    player2_strategy: str
    player1_busts: int
    player2_busts: int
    game_history: List[Dict] = field(default_factory=list)


class GameSimulator:
    """Simulates Can't Stop games between two strategies."""

    def __init__(self, strategy1: Strategy, strategy2: Strategy, verbose=False):
        self.strategies = [strategy1, strategy2]
        self.verbose = verbose

    def create_game_state(self, current_player: int) -> Dict:
        """
        Create game state dictionary compatible with strategy interface.

        This bridges the gap between GameMechanics (stateless) and
        our strategy interface.
        """
        return {
            'current_player': current_player,
            'player1_permanent': self.player1_permanent.copy(),
            'player2_permanent': self.player2_permanent.copy(),
            'player1_completed': self.player1_completed.copy(),
            'player2_completed': self.player2_completed.copy(),
            'active_runners': self.active_runners.copy(),
            'temp_progress': self.temp_progress.copy(),
            'current_dice': self.current_dice,
            'valid_pairings': self.valid_pairings
        }

    def reset_game(self):
        """Initialize game state."""
        self.player1_permanent = {col: 0 for col in range(2, 13)}
        self.player2_permanent = {col: 0 for col in range(2, 13)}
        self.player1_completed = set()
        self.player2_completed = set()
        self.active_runners = set()
        self.temp_progress = {}
        self.current_dice = []
        self.valid_pairings = []
        self.turn_count = 0
        self.player1_busts = 0
        self.player2_busts = 0

    def get_all_completed(self) -> set:
        """Get all completed columns (by either player)."""
        return self.player1_completed | self.player2_completed

    def play_turn(self, player_idx: int) -> Tuple[bool, bool]:
        """
        Play one player's turn.

        Returns:
            (won, busted): whether player won the game, whether they busted
        """
        strategy = self.strategies[player_idx]
        self.active_runners = set()
        self.temp_progress = {}
        rolls_this_turn = 0
        max_rolls = 100  # Safety limit

        if player_idx == 0:
            my_permanent = self.player1_permanent
            my_completed = self.player1_completed
        else:
            my_permanent = self.player2_permanent
            my_completed = self.player2_completed

        while rolls_this_turn < max_rolls:
            # Roll dice
            self.current_dice = GameMechanics.roll_dice()
            rolls_this_turn += 1

            # Get all pairings (already returns sums as tuples)
            all_pairings = GameMechanics.get_all_pairings(self.current_dice)

            # Get valid pairings with playability info
            all_completed = self.get_all_completed()
            self.valid_pairings = []

            for idx, sums in enumerate(all_pairings):
                # Check if pairing is valid
                is_valid = GameMechanics.is_pairing_valid(
                    sums,
                    self.active_runners,
                    all_completed,
                    set()  # columns_at_top - we'll track this if needed
                )

                if is_valid:
                    # Get playability info
                    playability = GameMechanics.get_pairing_playability(
                        sums,
                        self.active_runners,
                        all_completed,
                        set()
                    )
                    self.valid_pairings.append((idx, sums, sums, playability))

            # Check for bust
            if not self.valid_pairings:
                if self.verbose:
                    print(f"  Player {player_idx + 1} busted!")
                if player_idx == 0:
                    self.player1_busts += 1
                else:
                    self.player2_busts += 1
                return False, True

            # Let strategy choose pairing
            game_state = self.create_game_state(player_idx)
            chosen_pairing_idx = strategy.choose_pairing(game_state, self.valid_pairings)

            # Find the chosen pairing in valid_pairings
            chosen_sums = None
            chosen_playability = None
            for idx, _, sums, playability in self.valid_pairings:
                if idx == chosen_pairing_idx:
                    chosen_sums = sums
                    chosen_playability = playability
                    break

            if chosen_sums is None:
                # Invalid choice, default to first valid pairing
                chosen_pairing_idx, _, chosen_sums, chosen_playability = self.valid_pairings[0]

            # Handle number choice if needed
            chosen_number = None
            if chosen_playability.get('needs_choice', False):
                playable_numbers = []
                if chosen_playability.get('sum1_playable', False):
                    playable_numbers.append(chosen_sums[0])
                if chosen_playability.get('sum2_playable', False) and chosen_sums[1] != chosen_sums[0]:
                    playable_numbers.append(chosen_sums[1])

                chosen_number = strategy.choose_number(game_state, chosen_pairing_idx, playable_numbers)

            # Apply the pairing
            new_temp, new_active = GameMechanics.apply_pairing(
                chosen_sums,
                self.temp_progress,
                self.active_runners,
                all_completed,
                my_permanent,
                chosen_number
            )

            self.temp_progress = new_temp
            self.active_runners = new_active

            if self.verbose:
                print(f"  Roll {rolls_this_turn}: {self.current_dice} -> {chosen_sums}, temp={self.temp_progress}")

            # Check if should stop
            game_state = self.create_game_state(player_idx)
            if strategy.should_stop(game_state):
                # Commit progress
                completed_this_turn = self.commit_progress(player_idx)

                if self.verbose:
                    print(f"  Player {player_idx + 1} stopped. Completed: {completed_this_turn}")

                # Check for win
                if len(my_completed) >= 3:
                    return True, False

                return False, False

        # Max rolls reached, force stop
        self.commit_progress(player_idx)
        return len(my_completed) >= 3, False

    def commit_progress(self, player_idx: int) -> List[int]:
        """
        Commit temporary progress to permanent.

        Returns:
            List of columns completed this turn
        """
        if player_idx == 0:
            my_permanent = self.player1_permanent
            my_completed = self.player1_completed
        else:
            my_permanent = self.player2_permanent
            my_completed = self.player2_completed

        completed_this_turn = []

        for col, progress in self.temp_progress.items():
            my_permanent[col] += progress

            # Check if column completed
            if my_permanent[col] >= COLUMN_LENGTHS[col]:
                my_completed.add(col)
                completed_this_turn.append(col)

        # Reset turn state
        self.temp_progress = {}
        self.active_runners = set()

        return completed_this_turn

    def simulate_game(self, max_turns=200) -> GameResult:
        """
        Simulate a complete game.

        Args:
            max_turns: Maximum turns to prevent infinite games

        Returns:
            GameResult with outcome
        """
        self.reset_game()

        for turn in range(max_turns):
            self.turn_count = turn + 1
            player = turn % 2

            if self.verbose:
                print(f"\n--- Turn {self.turn_count}: Player {player + 1} ({self.strategies[player].name}) ---")

            won, busted = self.play_turn(player)

            if won:
                return GameResult(
                    winner=player,
                    turns=self.turn_count,
                    player1_columns_completed=len(self.player1_completed),
                    player2_columns_completed=len(self.player2_completed),
                    player1_strategy=self.strategies[0].name,
                    player2_strategy=self.strategies[1].name,
                    player1_busts=self.player1_busts,
                    player2_busts=self.player2_busts
                )

        # Game timeout - declare winner by most columns
        if len(self.player1_completed) > len(self.player2_completed):
            winner = 0
        elif len(self.player2_completed) > len(self.player1_completed):
            winner = 1
        else:
            winner = random.randint(0, 1)  # Tie - random winner

        return GameResult(
            winner=winner,
            turns=max_turns,
            player1_columns_completed=len(self.player1_completed),
            player2_columns_completed=len(self.player2_completed),
            player1_strategy=self.strategies[0].name,
            player2_strategy=self.strategies[1].name,
            player1_busts=self.player1_busts,
            player2_busts=self.player2_busts
        )


# ============================================================================
# Single-Player Simulator
# ============================================================================

class SinglePlayerSimulator:
    """Simulates strategy playing alone to complete columns."""

    def __init__(self, strategy: Strategy, verbose=False):
        self.strategy = strategy
        self.verbose = verbose

    def reset_game(self):
        """Initialize single-player game state."""
        self.permanent = {col: 0 for col in range(2, 13)}
        self.completed = set()
        self.active_runners = set()
        self.temp_progress = {}
        self.current_dice = []
        self.valid_pairings = []
        self.turns = 0
        self.busts = 0
        self.column_usage = {col: 0 for col in range(2, 13)}  # Track which columns used

    def create_game_state(self) -> Dict:
        """Create game state for strategy."""
        return {
            'current_player': 0,
            'player1_permanent': self.permanent.copy(),
            'player2_permanent': {col: 0 for col in range(2, 13)},
            'player1_completed': self.completed.copy(),
            'player2_completed': set(),
            'active_runners': self.active_runners.copy(),
            'temp_progress': self.temp_progress.copy(),
            'current_dice': self.current_dice,
            'valid_pairings': self.valid_pairings
        }

    def play_turn(self) -> Tuple[int, bool]:
        """
        Play one turn.

        Returns:
            (columns_completed, busted)
        """
        self.active_runners = set()
        self.temp_progress = {}
        rolls_this_turn = 0
        max_rolls = 100

        while rolls_this_turn < max_rolls:
            # Roll dice
            self.current_dice = GameMechanics.roll_dice()
            rolls_this_turn += 1

            # Get valid pairings (already returns sums)
            all_pairings = GameMechanics.get_all_pairings(self.current_dice)
            self.valid_pairings = []

            for idx, sums in enumerate(all_pairings):

                is_valid = GameMechanics.is_pairing_valid(
                    sums,
                    self.active_runners,
                    self.completed,
                    set()
                )

                if is_valid:
                    playability = GameMechanics.get_pairing_playability(
                        sums,
                        self.active_runners,
                        self.completed,
                        set()
                    )
                    self.valid_pairings.append((idx, sums, sums, playability))

            # Check for bust
            if not self.valid_pairings:
                self.busts += 1
                return 0, True

            # Choose and apply pairing
            game_state = self.create_game_state()
            chosen_idx = self.strategy.choose_pairing(game_state, self.valid_pairings)

            chosen_sums = None
            chosen_playability = None
            for idx, _, sums, playability in self.valid_pairings:
                if idx == chosen_idx:
                    chosen_sums = sums
                    chosen_playability = playability
                    break

            if chosen_sums is None:
                chosen_idx, _, chosen_sums, chosen_playability = self.valid_pairings[0]

            # Handle number choice
            chosen_number = None
            if chosen_playability.get('needs_choice', False):
                playable_numbers = []
                if chosen_playability.get('sum1_playable', False):
                    playable_numbers.append(chosen_sums[0])
                if chosen_playability.get('sum2_playable', False) and chosen_sums[1] != chosen_sums[0]:
                    playable_numbers.append(chosen_sums[1])
                chosen_number = self.strategy.choose_number(game_state, chosen_idx, playable_numbers)

            # Apply pairing
            new_temp, new_active = GameMechanics.apply_pairing(
                chosen_sums,
                self.temp_progress,
                self.active_runners,
                self.completed,
                self.permanent,
                chosen_number
            )

            self.temp_progress = new_temp
            self.active_runners = new_active

            # Check if should stop
            game_state = self.create_game_state()
            if self.strategy.should_stop(game_state):
                # Commit progress
                completed_count = self.commit_progress()
                return completed_count, False

        # Max rolls - force commit
        completed_count = self.commit_progress()
        return completed_count, False

    def commit_progress(self) -> int:
        """Commit temp progress, return number of columns completed."""
        completed_this_turn = 0

        for col, progress in self.temp_progress.items():
            self.permanent[col] += progress
            self.column_usage[col] += 1  # Track usage

            if self.permanent[col] >= COLUMN_LENGTHS[col] and col not in self.completed:
                self.completed.add(col)
                completed_this_turn += 1

        self.temp_progress = {}
        self.active_runners = set()

        return completed_this_turn

    def simulate_to_completion(self, target_columns=3, max_turns=500) -> Dict:
        """
        Simulate until completing target number of columns.

        Returns:
            Dictionary with statistics
        """
        self.reset_game()

        turns_to_1col = None
        turns_to_2col = None
        turns_to_3col = None

        for turn in range(1, max_turns + 1):
            self.turns = turn
            completed, busted = self.play_turn()

            # Track milestones
            if turns_to_1col is None and len(self.completed) >= 1:
                turns_to_1col = turn
            if turns_to_2col is None and len(self.completed) >= 2:
                turns_to_2col = turn
            if turns_to_3col is None and len(self.completed) >= 3:
                turns_to_3col = turn
                break

        return {
            'turns_to_1col': turns_to_1col or max_turns,
            'turns_to_2col': turns_to_2col or max_turns,
            'turns_to_3col': turns_to_3col or max_turns,
            'busts': self.busts,
            'columns_completed': list(self.completed),
            'column_usage': self.column_usage.copy()
        }


if __name__ == "__main__":
    from strategies_correct_implementation import get_all_strategies

    print("Game Simulator Test")
    print("=" * 80)

    strategies = get_all_strategies()

    # Quick test: Greedy vs Conservative(3)
    print("\nTest: Greedy vs Conservative(3) - 10 games")
    print("-" * 80)

    greedy = strategies['Greedy']
    conservative = strategies['Conservative(3)']

    wins = [0, 0]
    for i in range(10):
        sim = GameSimulator(greedy, conservative, verbose=False)
        result = sim.simulate_game()
        wins[result.winner] += 1
        print(f"Game {i+1}: Winner = Player {result.winner + 1} in {result.turns} turns")

    print(f"\nResults: Greedy {wins[0]}-{wins[1]} Conservative(3)")
    print("\nSimulator ready!")
