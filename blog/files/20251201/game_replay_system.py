#!/usr/bin/env python3
"""
Can't Stop Game Replay System
Records full game state for video generation
"""

import random
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path


@dataclass
class GameState:
    """Snapshot of game state at a point in time"""
    turn_number: int
    current_player: str
    roll: List[int]
    available_pairings: List[Tuple[int, int]]
    chosen_pairing: Optional[Tuple[int, int]]
    player1_permanent: Dict[int, int]  # column -> progress
    player2_permanent: Dict[int, int]
    player1_temporary: Dict[int, int]
    player2_temporary: Dict[int, int]
    player1_active_columns: Set[int]
    player2_active_columns: Set[int]
    busted: bool
    stopped: bool
    decision_reasoning: str
    ev_calculation: Optional[float]


class CantStopGame:
    """Can't Stop game with full state recording"""

    def __init__(self, strategy1, strategy2, player1_name, player2_name):
        self.strategy1 = strategy1
        self.strategy2 = strategy2
        self.player1_name = player1_name
        self.player2_name = player2_name

        # Column lengths
        self.column_length = {
            2: 3, 3: 5, 4: 7, 5: 9, 6: 11,
            7: 13, 8: 11, 9: 9, 10: 7, 11: 5, 12: 3
        }

        # Game state
        self.player1_progress = {col: 0 for col in range(2, 13)}
        self.player2_progress = {col: 0 for col in range(2, 13)}
        self.player1_completed = set()
        self.player2_completed = set()

        # Recording
        self.history: List[GameState] = []
        self.turn_number = 0

    def roll_dice(self) -> List[int]:
        """Roll 4 dice"""
        return sorted([random.randint(1, 6) for _ in range(4)])

    def get_pairings(self, dice: List[int]) -> List[Tuple[int, int]]:
        """Get all possible pairings from 4 dice"""
        d1, d2, d3, d4 = dice
        return [
            (d1 + d2, d3 + d4),
            (d1 + d3, d2 + d4),
            (d1 + d4, d2 + d3)
        ]

    def can_use_pairing(self, pairing: Tuple[int, int],
                       active_cols: Set[int], completed: Set[int]) -> bool:
        """Check if a pairing can be used"""
        sum1, sum2 = pairing

        # Can't use completed columns
        if sum1 in completed or sum2 in completed:
            return False

        # If we have active columns, at least one sum must match
        if active_cols:
            return sum1 in active_cols or sum2 in active_cols

        return True

    def play_turn(self, player_num: int) -> bool:
        """Play one player's turn. Returns True if game continues."""
        is_player1 = player_num == 1
        player_name = self.player1_name if is_player1 else self.player2_name
        strategy = self.strategy1 if is_player1 else self.strategy2
        progress = self.player1_progress if is_player1 else self.player2_progress
        completed = self.player1_completed if is_player1 else self.player2_completed

        # Temporary state for this turn
        temp_progress = {}
        active_columns = set()

        roll_count = 0
        while True:
            roll_count += 1
            self.turn_number += 1

            # Roll dice
            dice = self.roll_dice()
            pairings = self.get_pairings(dice)

            # Find valid pairings
            valid_pairings = [
                p for p in pairings
                if self.can_use_pairing(p, active_columns, completed)
            ]

            if not valid_pairings:
                # BUST!
                self.history.append(GameState(
                    turn_number=self.turn_number,
                    current_player=player_name,
                    roll=dice,
                    available_pairings=pairings,
                    chosen_pairing=None,
                    player1_permanent=dict(self.player1_progress),
                    player2_permanent=dict(self.player2_progress),
                    player1_temporary=temp_progress.copy() if is_player1 else {},
                    player2_temporary={} if is_player1 else temp_progress.copy(),
                    player1_active_columns=active_columns.copy() if is_player1 else set(),
                    player2_active_columns=set() if is_player1 else active_columns.copy(),
                    busted=True,
                    stopped=False,
                    decision_reasoning=f"💥 BUST! No valid moves from {dice}. Lost {sum(temp_progress.values())} steps.",
                    ev_calculation=None
                ))
                return True  # Game continues

            # Strategy decides which pairing and whether to continue
            chosen, should_stop, reasoning, ev = strategy.decide(
                dice, valid_pairings, progress, temp_progress,
                active_columns, completed, self.column_length
            )

            # Apply moves
            sum1, sum2 = chosen
            for col in [sum1, sum2]:
                if col not in completed:
                    temp_progress[col] = temp_progress.get(col, 0) + 1
                    active_columns.add(col)

            # Record state
            self.history.append(GameState(
                turn_number=self.turn_number,
                current_player=player_name,
                roll=dice,
                available_pairings=pairings,
                chosen_pairing=chosen,
                player1_permanent=dict(self.player1_progress),
                player2_permanent=dict(self.player2_progress),
                player1_temporary=temp_progress.copy() if is_player1 else {},
                player2_temporary={} if is_player1 else temp_progress.copy(),
                player1_active_columns=active_columns.copy() if is_player1 else set(),
                player2_active_columns=set() if is_player1 else active_columns.copy(),
                busted=False,
                stopped=should_stop,
                decision_reasoning=reasoning,
                ev_calculation=ev
            ))

            if should_stop:
                # Commit progress
                for col, steps in temp_progress.items():
                    progress[col] += steps
                    if progress[col] >= self.column_length[col]:
                        completed.add(col)

                # Check win condition
                if len(completed) >= 3:
                    return False  # Game over

                return True  # Game continues

    def play_game(self) -> str:
        """Play full game, return winner"""
        current_player = 1

        while True:
            game_continues = self.play_turn(current_player)

            if not game_continues:
                winner = self.player1_name if current_player == 1 else self.player2_name
                return winner

            # Switch players
            current_player = 2 if current_player == 1 else 1

    def save_history(self, filename: str):
        """Save game history to JSON"""
        data = {
            'player1': self.player1_name,
            'player2': self.player2_name,
            'winner': None,  # Set externally
            'history': [
                {
                    **asdict(state),
                    'player1_active_columns': list(state.player1_active_columns),
                    'player2_active_columns': list(state.player2_active_columns),
                }
                for state in self.history
            ]
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)


class GreedyUntil1ColStrategy:
    """Rolls until completing at least one column"""

    def decide(self, dice, valid_pairings, progress, temp_progress,
               active_columns, completed, column_length):
        # Choose pairing that makes most progress
        best_pairing = valid_pairings[0]
        best_score = 0

        for pairing in valid_pairings:
            score = 0
            for col in pairing:
                if col not in completed:
                    score += 1
            if score > best_score:
                best_score = score
                best_pairing = pairing

        # Check if we've completed any column
        completed_this_turn = []
        for col, steps in temp_progress.items():
            total = progress.get(col, 0) + steps
            if total >= column_length[col] and col not in completed:
                completed_this_turn.append(col)

        if completed_this_turn:
            reasoning = f"✓ Completed {completed_this_turn}. Stopping (GreedyUntil1Col rule)."
            return best_pairing, True, reasoning, None

        reasoning = f"Chose {best_pairing}. No column complete yet, continuing..."
        return best_pairing, False, reasoning, None


class ExpectedValueMaxStrategy:
    """Stops when expected value becomes negative"""

    def decide(self, dice, valid_pairings, progress, temp_progress,
               active_columns, completed, column_length):
        # Choose pairing that maximizes immediate progress
        best_pairing = valid_pairings[0]

        # Calculate EV of continuing
        unsaved_steps = sum(temp_progress.values())

        # Simple EV calculation (simplified for demo)
        # P(success) ~= 0.92 for good columns
        # Q (expected progress) ~= 1.4
        # EV = P_success * Q - P_bust * U

        p_success = 0.85  # Simplified
        q_value = 1.4
        p_bust = 1 - p_success

        ev = p_success * q_value - p_bust * unsaved_steps

        if ev <= 0:
            reasoning = f"EV = {ev:.2f} ≤ 0. Math says STOP ({unsaved_steps} unsaved steps)."
            return best_pairing, True, reasoning, ev

        reasoning = f"Chose {best_pairing}. EV = {ev:.2f} > 0. Math says ROLL!"
        return best_pairing, False, reasoning, ev


def find_dramatic_game(num_simulations=1000):
    """Find a game where GreedyUntil1Col wins decisively"""
    print(f"Searching for dramatic game in {num_simulations} simulations...")

    best_game = None
    best_score = 0

    for i in range(num_simulations):
        if i % 100 == 0:
            print(f"  Simulated {i} games...")

        game = CantStopGame(
            GreedyUntil1ColStrategy(),
            ExpectedValueMaxStrategy(),
            "GreedyUntil1Col",
            "ExpectedValueMax"
        )

        winner = game.play_game()

        if winner == "GreedyUntil1Col":
            # Score based on: EV had lead at some point, big bust, decisive win
            score = 0

            # Check for EV lead
            ev_was_ahead = False
            max_ev_bust_size = 0

            for state in game.history:
                if state.current_player == "ExpectedValueMax":
                    if state.busted and state.player2_temporary:
                        bust_size = sum(state.player2_temporary.values())
                        max_ev_bust_size = max(max_ev_bust_size, bust_size)

                    # Check if EV was ever ahead
                    ev_completed = len(game.player2_completed)
                    greedy_completed = len(game.player1_completed)
                    if ev_completed > greedy_completed:
                        ev_was_ahead = True

            score = max_ev_bust_size * 10
            if ev_was_ahead:
                score += 50

            # Prefer games with a big turning point
            if score > best_score:
                best_score = score
                best_game = game
                print(f"  ✓ Found better game! Score: {score}, Bust size: {max_ev_bust_size}")

    print(f"\n✓ Best game found with score {best_score}")
    return best_game


if __name__ == '__main__':
    # Find and save a dramatic game
    game = find_dramatic_game(500)

    if game:
        output_file = Path(__file__).parent / 'dramatic_game.json'
        game.save_history(str(output_file))
        print(f"\n✓ Saved game history to {output_file}")
        print(f"  Total turns: {game.turn_number}")
        print(f"  Winner: {game.player1_name if len(game.player1_completed) >= 3 else game.player2_name}")
        print(f"  {game.player1_name} completed: {game.player1_completed}")
        print(f"  {game.player2_name} completed: {game.player2_completed}")
