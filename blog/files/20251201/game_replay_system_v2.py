#!/usr/bin/env python3
"""
Can't Stop Game Replay System - Clean Architecture
Separates game mechanics (physics/rules) from strategy (AI decisions)
"""

import random
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path
from abc import ABC, abstractmethod


# ============================================================================
# GAME STATE (Immutable data structures)
# ============================================================================

@dataclass(frozen=True)
class ReadOnlyGameState:
    """Immutable game state snapshot for strategy decisions"""
    # Current turn state
    current_roll: List[int]
    temp_progress: Dict[int, int]  # Unsaved progress this turn
    active_runners: Set[int]  # Columns with runners

    # Player permanent state
    permanent_progress: Dict[int, int]  # Saved progress
    completed_columns: Set[int]  # Columns this player owns
    opponent_completed: Set[int]  # Columns opponent owns

    # Board configuration
    column_lengths: Dict[int, int]

    # Derived info (for convenience)
    columns_reached_top: Set[int]  # Columns that reached top this turn
    unsaved_steps: int  # Total unsaved progress


@dataclass
class GameStateHistory:
    """Full game state for recording/replay"""
    turn_number: int
    current_player: str
    roll: List[int]
    available_pairings: List[Tuple[int, int]]
    chosen_pairing: Optional[Tuple[int, int]]
    player1_permanent: Dict[int, int]
    player2_permanent: Dict[int, int]
    player1_temporary: Dict[int, int]
    player2_temporary: Dict[int, int]
    player1_active_columns: Set[int]
    player2_active_columns: Set[int]
    player1_completed: Set[int]
    player2_completed: Set[int]
    busted: bool
    stopped: bool
    decision_reasoning: str
    ev_calculation: Optional[float]


# ============================================================================
# GAME MECHANICS (Pure rule enforcement - strategy agnostic)
# ============================================================================

class GameMechanics:
    """Enforces Can't Stop rules - immutable, testable, strategy-agnostic"""

    # Column configuration
    COLUMN_LENGTHS = {
        2: 3, 3: 5, 4: 7, 5: 9, 6: 11,
        7: 13, 8: 11, 9: 9, 10: 7, 11: 5, 12: 3
    }

    @staticmethod
    def roll_dice() -> List[int]:
        """Roll 4 six-sided dice, return sorted"""
        return sorted([random.randint(1, 6) for _ in range(4)])

    @staticmethod
    def get_all_pairings(dice: List[int]) -> List[Tuple[int, int]]:
        """Get all 3 possible pairings from 4 dice"""
        d1, d2, d3, d4 = dice
        return [
            (d1 + d2, d3 + d4),
            (d1 + d3, d2 + d4),
            (d1 + d4, d2 + d3)
        ]

    @staticmethod
    def is_pairing_valid(pairing: Tuple[int, int],
                        active_runners: Set[int],
                        all_completed: Set[int]) -> bool:
        """Check if a pairing can be legally used

        Rules:
        1. Cannot use completed columns
        2. Cannot exceed 3 active runners
        3. If have runners, must use at least one existing column
           OR have room for new column(s)
        """
        sum1, sum2 = pairing

        # Can't use completed columns
        if sum1 in all_completed or sum2 in all_completed:
            return False

        # Count how many NEW runners this would require
        new_runners_needed = 0
        if sum1 not in active_runners:
            new_runners_needed += 1
        if sum2 not in active_runners and sum1 != sum2:
            new_runners_needed += 1

        # Check 3-runner limit
        if len(active_runners) + new_runners_needed <= 3:
            return True

        return False

    @staticmethod
    def get_valid_pairings(all_pairings: List[Tuple[int, int]],
                          active_runners: Set[int],
                          all_completed: Set[int]) -> List[Tuple[int, int]]:
        """Filter to only valid pairings"""
        return [p for p in all_pairings
                if GameMechanics.is_pairing_valid(p, active_runners, all_completed)]

    @staticmethod
    def is_bust(valid_pairings: List[Tuple[int, int]]) -> bool:
        """Check if player has busted (no valid moves)"""
        return len(valid_pairings) == 0

    @staticmethod
    def apply_pairing(pairing: Tuple[int, int],
                     temp_progress: Dict[int, int],
                     active_runners: Set[int]) -> Tuple[Dict[int, int], Set[int]]:
        """Apply a pairing, return new temp state

        Returns: (new_temp_progress, new_active_runners)
        """
        new_temp = dict(temp_progress)
        new_active = set(active_runners)

        sum1, sum2 = pairing
        for col in [sum1, sum2]:
            new_temp[col] = new_temp.get(col, 0) + 1
            new_active.add(col)

        return new_temp, new_active

    @staticmethod
    def check_reached_tops(temp_progress: Dict[int, int],
                          permanent_progress: Dict[int, int]) -> Set[int]:
        """Check which columns have reached the top (not yet completed!)"""
        reached = set()
        for col, temp_steps in temp_progress.items():
            total = permanent_progress.get(col, 0) + temp_steps
            if total >= GameMechanics.COLUMN_LENGTHS[col]:
                reached.add(col)
        return reached

    @staticmethod
    def commit_progress(temp_progress: Dict[int, int],
                       permanent_progress: Dict[int, int],
                       player_completed: Set[int],
                       all_completed: Set[int]) -> Tuple[Dict[int, int], Set[int]]:
        """Commit temporary progress on voluntary stop

        Returns: (new_permanent_progress, newly_completed_columns)

        CRITICAL: Columns are only completed when committed!
        """
        new_permanent = dict(permanent_progress)
        newly_completed = set()

        for col, steps in temp_progress.items():
            new_permanent[col] = new_permanent.get(col, 0) + steps

            # Check if column is now completed
            if new_permanent[col] >= GameMechanics.COLUMN_LENGTHS[col]:
                if col not in player_completed:
                    newly_completed.add(col)

        return new_permanent, newly_completed

    @staticmethod
    def check_instant_win(newly_completed: Set[int],
                         total_completed: Set[int]) -> bool:
        """Check if player just won (3 columns completed)

        Win condition is AUTOMATIC and IMMEDIATE
        """
        return len(total_completed.union(newly_completed)) >= 3


# ============================================================================
# STRATEGY INTERFACE (Decision making only)
# ============================================================================

class Strategy(ABC):
    """Abstract strategy - makes decisions, doesn't enforce rules"""

    @abstractmethod
    def choose_pairing(self,
                      available_pairings: List[Tuple[int, int]],
                      game_state: ReadOnlyGameState) -> int:
        """Choose pairing index from available options (0, 1, or 2)

        GameMechanics already filtered to valid pairings
        Strategy cannot cheat - must return valid index
        """
        pass

    @abstractmethod
    def decide_continue(self,
                       game_state: ReadOnlyGameState,
                       just_applied_pairing: Tuple[int, int]) -> Tuple[bool, str, Optional[float]]:
        """Decide whether to roll again or stop

        Returns: (should_continue, reasoning, ev_value)

        NOTE: Cannot continue if would complete 3rd column - game ends automatically
        """
        pass


# ============================================================================
# STRATEGY IMPLEMENTATIONS
# ============================================================================

class GreedyUntil1ColStrategy(Strategy):
    """Conservative: stops after completing column or reaching 3+ unsaved steps"""

    def choose_pairing(self, available_pairings: List[Tuple[int, int]],
                      game_state: ReadOnlyGameState) -> int:
        """Choose pairing closest to completing a column"""
        best_idx = 0
        best_score = -999

        for idx, pairing in enumerate(available_pairings):
            score = 0
            for col in pairing:
                if col not in game_state.opponent_completed:
                    current = game_state.permanent_progress.get(col, 0) + \
                             game_state.temp_progress.get(col, 0)
                    remaining = game_state.column_lengths[col] - current
                    score += 10 - remaining  # Prefer closer to completion

            if score > best_score:
                best_score = score
                best_idx = idx

        return best_idx

    def decide_continue(self, game_state: ReadOnlyGameState,
                       just_applied_pairing: Tuple[int, int]) -> Tuple[bool, str, Optional[float]]:
        """Stop if completed column or have 3+ unsaved steps"""

        # Always stop if completed any column
        if game_state.columns_reached_top:
            cols = sorted(game_state.columns_reached_top)
            return False, f"✓ Reached top of {cols}. Stopping to secure!", None

        # Stop if 3+ unsaved steps (risk management)
        if game_state.unsaved_steps >= 3:
            return False, f"Have {game_state.unsaved_steps} unsaved steps. Stopping to secure progress.", None

        # Otherwise continue
        return True, f"Chose {just_applied_pairing}. {game_state.unsaved_steps} unsaved steps, continuing...", None


class ExpectedValueMaxStrategy(Strategy):
    """Aggressive: uses EV calculation to decide when to stop"""

    def choose_pairing(self, available_pairings: List[Tuple[int, int]],
                      game_state: ReadOnlyGameState) -> int:
        """Choose pairing that maximizes progress toward completion"""
        best_idx = 0
        best_score = -999

        for idx, pairing in enumerate(available_pairings):
            score = 0
            for col in pairing:
                if col not in game_state.opponent_completed:
                    current = game_state.permanent_progress.get(col, 0) + \
                             game_state.temp_progress.get(col, 0)
                    remaining = game_state.column_lengths[col] - current
                    score += 10 - remaining

            if score > best_score:
                best_score = score
                best_idx = idx

        return best_idx

    def decide_continue(self, game_state: ReadOnlyGameState,
                       just_applied_pairing: Tuple[int, int]) -> Tuple[bool, str, Optional[float]]:
        """Stop if EV becomes negative or completed column"""

        # Always stop if completed a column
        if game_state.columns_reached_top:
            cols = sorted(game_state.columns_reached_top)
            return False, f"✓ Reached top of {cols}. Stopping to secure!", None

        # Calculate EV
        num_active = len(game_state.active_runners)

        # P(success) depends on number of active runners
        if num_active <= 2:
            p_success = 0.85
        else:
            p_success = 0.75

        q_value = 1.5  # Expected progress per roll
        p_bust = 1 - p_success

        ev = p_success * q_value - p_bust * game_state.unsaved_steps

        if ev <= 0:
            return False, f"EV = {ev:.2f} ≤ 0. Math says STOP ({game_state.unsaved_steps} unsaved steps).", ev

        return True, f"Chose {just_applied_pairing}. EV = {ev:.2f} > 0. Math says ROLL!", ev


# ============================================================================
# GAME ORCHESTRATION
# ============================================================================

class CantStopGame:
    """Orchestrates game flow using GameMechanics for rule enforcement"""

    def __init__(self, strategy1: Strategy, strategy2: Strategy,
                 player1_name: str, player2_name: str):
        self.strategy1 = strategy1
        self.strategy2 = strategy2
        self.player1_name = player1_name
        self.player2_name = player2_name

        # Player states
        self.player1_progress = {col: 0 for col in range(2, 13)}
        self.player2_progress = {col: 0 for col in range(2, 13)}
        self.player1_completed = set()
        self.player2_completed = set()

        # Recording
        self.history: List[GameStateHistory] = []
        self.turn_number = 0

    def play_turn(self, player_num: int) -> bool:
        """Play one player's turn

        Returns: True if game continues, False if game over
        """
        is_player1 = player_num == 1
        player_name = self.player1_name if is_player1 else self.player2_name
        strategy = self.strategy1 if is_player1 else self.strategy2
        progress = self.player1_progress if is_player1 else self.player2_progress
        completed = self.player1_completed if is_player1 else self.player2_completed
        opponent_completed = self.player2_completed if is_player1 else self.player1_completed

        # Turn state
        temp_progress = {}
        active_runners = set()

        # Roll until bust or voluntary stop
        while True:
            self.turn_number += 1

            # MECHANICS: Roll dice
            dice = GameMechanics.roll_dice()
            all_pairings = GameMechanics.get_all_pairings(dice)

            # MECHANICS: Filter to valid pairings
            all_completed = completed.union(opponent_completed)
            valid_pairings = GameMechanics.get_valid_pairings(
                all_pairings, active_runners, all_completed
            )

            # MECHANICS: Check for bust
            if GameMechanics.is_bust(valid_pairings):
                # BUST! Lose all temp progress
                self.history.append(GameStateHistory(
                    turn_number=self.turn_number,
                    current_player=player_name,
                    roll=dice,
                    available_pairings=all_pairings,
                    chosen_pairing=None,
                    player1_permanent=dict(self.player1_progress),
                    player2_permanent=dict(self.player2_progress),
                    player1_temporary=temp_progress.copy() if is_player1 else {},
                    player2_temporary={} if is_player1 else temp_progress.copy(),
                    player1_active_columns=active_runners.copy() if is_player1 else set(),
                    player2_active_columns=set() if is_player1 else active_runners.copy(),
                    player1_completed=self.player1_completed.copy(),
                    player2_completed=self.player2_completed.copy(),
                    busted=True,
                    stopped=False,
                    decision_reasoning=f"💥 BUST! No valid moves from {dice}. Lost {sum(temp_progress.values())} steps.",
                    ev_calculation=None
                ))
                return True  # Game continues

            # STRATEGY: Choose pairing
            game_state = ReadOnlyGameState(
                current_roll=dice,
                temp_progress=temp_progress.copy(),
                active_runners=active_runners.copy(),
                permanent_progress=progress.copy(),
                completed_columns=completed.copy(),
                opponent_completed=opponent_completed.copy(),
                column_lengths=GameMechanics.COLUMN_LENGTHS,
                columns_reached_top=GameMechanics.check_reached_tops(temp_progress, progress),
                unsaved_steps=sum(temp_progress.values())
            )

            pairing_idx = strategy.choose_pairing(valid_pairings, game_state)
            chosen_pairing = valid_pairings[pairing_idx]

            # MECHANICS: Apply pairing
            temp_progress, active_runners = GameMechanics.apply_pairing(
                chosen_pairing, temp_progress, active_runners
            )

            # Update game state after applying move
            game_state = ReadOnlyGameState(
                current_roll=dice,
                temp_progress=temp_progress.copy(),
                active_runners=active_runners.copy(),
                permanent_progress=progress.copy(),
                completed_columns=completed.copy(),
                opponent_completed=opponent_completed.copy(),
                column_lengths=GameMechanics.COLUMN_LENGTHS,
                columns_reached_top=GameMechanics.check_reached_tops(temp_progress, progress),
                unsaved_steps=sum(temp_progress.values())
            )

            # STRATEGY: Decide continue or stop
            should_continue, reasoning, ev = strategy.decide_continue(game_state, chosen_pairing)

            # Record state
            self.history.append(GameStateHistory(
                turn_number=self.turn_number,
                current_player=player_name,
                roll=dice,
                available_pairings=all_pairings,
                chosen_pairing=chosen_pairing,
                player1_permanent=dict(self.player1_progress),
                player2_permanent=dict(self.player2_progress),
                player1_temporary=temp_progress.copy() if is_player1 else {},
                player2_temporary={} if is_player1 else temp_progress.copy(),
                player1_active_columns=active_runners.copy() if is_player1 else set(),
                player2_active_columns=set() if is_player1 else active_runners.copy(),
                player1_completed=self.player1_completed.copy(),
                player2_completed=self.player2_completed.copy(),
                busted=False,
                stopped=not should_continue,
                decision_reasoning=reasoning,
                ev_calculation=ev
            ))

            if not should_continue:
                # MECHANICS: Commit progress (voluntary stop)
                new_progress, newly_completed = GameMechanics.commit_progress(
                    temp_progress, progress, completed, all_completed
                )

                # Update permanent state
                if is_player1:
                    self.player1_progress = new_progress
                    self.player1_completed.update(newly_completed)
                else:
                    self.player2_progress = new_progress
                    self.player2_completed.update(newly_completed)

                # MECHANICS: Check instant win
                if GameMechanics.check_instant_win(newly_completed, completed):
                    return False  # GAME OVER!

                return True  # Game continues

    def play_game(self) -> str:
        """Play complete game, return winner"""
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
            'winner': None,
            'history': [
                {
                    **{k: v for k, v in asdict(state).items()
                       if k not in ['player1_active_columns', 'player2_active_columns',
                                   'player1_completed', 'player2_completed']},
                    'player1_active_columns': list(state.player1_active_columns),
                    'player2_active_columns': list(state.player2_active_columns),
                    'player1_completed': list(state.player1_completed),
                    'player2_completed': list(state.player2_completed),
                }
                for state in self.history
            ]
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)


# ============================================================================
# GAME FINDER
# ============================================================================

def find_dramatic_game(num_simulations=2000):
    """Find a dramatic game for visualization"""
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

        # Only consider reasonable-length games
        if game.turn_number < 100:
            # Score based on drama
            max_bust_size = 0
            total_busts = 0

            for state in game.history:
                if state.busted:
                    total_busts += 1
                    temp = state.player1_temporary if state.current_player == "GreedyUntil1Col" else state.player2_temporary
                    bust_size = sum(temp.values())
                    max_bust_size = max(max_bust_size, bust_size)

            score = max_bust_size * 10 + total_busts + (100 - game.turn_number) / 10

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
        winner_name = game.player1_name if len(game.player1_completed) >= 3 else game.player2_name
        print(f"  Winner: {winner_name}")
        print(f"  {game.player1_name} completed: {game.player1_completed}")
        print(f"  {game.player2_name} completed: {game.player2_completed}")
