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
        """Check if a pairing can be used

        A pairing is valid if at least ONE column can be moved:
        - Column can be moved if it's already active OR we have room to add it
        """
        sum1, sum2 = pairing

        # Check if we can move sum1
        can_move_sum1 = False
        if sum1 not in completed:
            if sum1 in active_cols or len(active_cols) < 3:
                can_move_sum1 = True

        # Check if we can move sum2
        can_move_sum2 = False
        if sum2 not in completed:
            if sum2 in active_cols:
                can_move_sum2 = True
            elif len(active_cols) < 3:
                # Can add sum2 if:
                # - sum1 == sum2 (same column), OR
                # - sum1 is already active (not consuming a slot), OR
                # - We have room for 2 new runners
                if sum1 == sum2:
                    can_move_sum2 = can_move_sum1
                elif sum1 in active_cols:
                    can_move_sum2 = True
                elif len(active_cols) < 2:
                    can_move_sum2 = True

        return can_move_sum1 or can_move_sum2

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

            # Apply moves - only move columns that can legally be moved
            sum1, sum2 = chosen
            all_completed = completed.union(self.player2_completed if is_player1 else self.player1_completed)

            # Try to move sum1
            if sum1 not in all_completed:
                if sum1 in active_columns or len(active_columns) < 3:
                    temp_progress[sum1] = temp_progress.get(sum1, 0) + 1
                    active_columns.add(sum1)

            # Try to move sum2 (only if different from sum1)
            if sum2 != sum1 and sum2 not in all_completed:
                if sum2 in active_columns or len(active_columns) < 3:
                    temp_progress[sum2] = temp_progress.get(sum2, 0) + 1
                    active_columns.add(sum2)

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
    """Rolls until completing at least one column, or until 3+ unsaved steps"""

    def decide(self, dice, valid_pairings, progress, temp_progress,
               active_columns, completed, column_length):
        # Choose pairing that makes most progress toward completion
        best_pairing = valid_pairings[0]
        best_score = -1

        for pairing in valid_pairings:
            score = 0
            for col in pairing:
                if col not in completed:
                    # Prefer columns we're already working on
                    current_prog = progress.get(col, 0) + temp_progress.get(col, 0)
                    remaining = column_length[col] - current_prog
                    # Score higher for columns closer to completion
                    score += 10 - remaining
            if score > best_score:
                best_score = score
                best_pairing = pairing

        # Simulate applying the best pairing
        simulated_temp = dict(temp_progress)
        for col in best_pairing:
            if col not in completed:
                simulated_temp[col] = simulated_temp.get(col, 0) + 1

        # Check if we would complete any column AFTER this move
        completed_this_turn = []
        for col, steps in simulated_temp.items():
            total = progress.get(col, 0) + steps
            if total >= column_length[col] and col not in completed:
                completed_this_turn.append(col)

        if completed_this_turn:
            reasoning = f"✓ Completed {completed_this_turn}. Stopping (GreedyUntil1Col rule)."
            return best_pairing, True, reasoning, None

        # Also stop if we have 3+ unsaved steps (risk management)
        unsaved = sum(simulated_temp.values())
        if unsaved >= 3:
            reasoning = f"Have {unsaved} unsaved steps. Stopping to secure progress."
            return best_pairing, True, reasoning, None

        reasoning = f"Chose {best_pairing}. {unsaved} unsaved steps, continuing..."
        return best_pairing, False, reasoning, None


class ExpectedValueMaxStrategy:
    """Stops when expected value becomes negative"""

    def decide(self, dice, valid_pairings, progress, temp_progress,
               active_columns, completed, column_length):
        # Choose pairing that maximizes immediate progress toward completion
        best_pairing = valid_pairings[0]
        best_score = -1

        for pairing in valid_pairings:
            score = 0
            for col in pairing:
                if col not in completed:
                    current_prog = progress.get(col, 0) + temp_progress.get(col, 0)
                    remaining = column_length[col] - current_prog
                    score += 10 - remaining
            if score > best_score:
                best_score = score
                best_pairing = pairing

        # Simulate applying the pairing
        simulated_temp = dict(temp_progress)
        for col in best_pairing:
            if col not in completed:
                simulated_temp[col] = simulated_temp.get(col, 0) + 1

        unsaved_steps = sum(simulated_temp.values())

        # Calculate EV of continuing vs stopping
        # Estimate P(success) based on number of active columns and unsaved steps
        num_active = len(active_columns)

        # With 1-2 active columns, P(success) is high (~85%)
        # With 3 active columns, P(success) drops (~75%)
        if num_active <= 2:
            p_success = 0.85
        else:
            p_success = 0.75

        # Expected progress on next roll ~1.5 steps
        q_value = 1.5
        p_bust = 1 - p_success

        # EV = P(success) * Q - P(bust) * unsaved_steps
        ev = p_success * q_value - p_bust * unsaved_steps

        # Always stop if completing a column
        for col, steps in simulated_temp.items():
            total = progress.get(col, 0) + steps
            if total >= column_length[col] and col not in completed:
                reasoning = f"✓ Completed column {col}. Stopping to secure."
                return best_pairing, True, reasoning, ev

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

        # Only consider games that finish in reasonable time (< 100 turns)
        if game.turn_number < 100:
            # Score based on: dramatic moments (big busts, interesting)
            score = 0

            # Check for big busts and drama
            max_bust_size = 0
            total_busts = 0

            for state in game.history:
                if state.busted:
                    total_busts += 1
                    if state.current_player == "ExpectedValueMax" and state.player2_temporary:
                        bust_size = sum(state.player2_temporary.values())
                        max_bust_size = max(max_bust_size, bust_size)
                    elif state.current_player == "GreedyUntil1Col" and state.player1_temporary:
                        bust_size = sum(state.player1_temporary.values())
                        max_bust_size = max(max_bust_size, bust_size)

            # Score based on drama
            score = max_bust_size * 10 + total_busts

            # Prefer shorter games
            score += (100 - game.turn_number) / 10

            # Prefer games with a big turning point
            if score > best_score and max_bust_size >= 3:
                best_score = score
                best_game = game
                print(f"  ✓ Found better game! Winner: {winner}, Score: {score:.1f}, Turns: {game.turn_number}, Max bust: {max_bust_size}")

    print(f"\n✓ Best game found with score {best_score:.1f}")
    return best_game


if __name__ == '__main__':
    # Find and save a dramatic game
    game = find_dramatic_game(2000)

    if game:
        output_file = Path(__file__).parent / 'dramatic_game.json'
        game.save_history(str(output_file))
        print(f"\n✓ Saved game history to {output_file}")
        print(f"  Total turns: {game.turn_number}")
        print(f"  Winner: {game.player1_name if len(game.player1_completed) >= 3 else game.player2_name}")
        print(f"  {game.player1_name} completed: {game.player1_completed}")
        print(f"  {game.player2_name} completed: {game.player2_completed}")
