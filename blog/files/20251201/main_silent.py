"""
Can't Stop Game - FastAPI Backend
Interactive game server with WebSocket support for real-time gameplay
"""

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Set, Tuple, Optional
import random
import uuid
from dataclasses import dataclass, asdict
import json
from pathlib import Path
from datetime import datetime

app = FastAPI(title="Can't Stop Game API")

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# GAME MECHANICS
# ============================================================================

class GameMechanics:
    """Pure game rules implementation"""

    COLUMN_LENGTHS = {
        2: 3, 3: 5, 4: 7, 5: 9, 6: 11,
        7: 13, 8: 11, 9: 9, 10: 7, 11: 5, 12: 3
    }

    @staticmethod
    def roll_dice() -> List[int]:
        """Roll 4 six-sided dice"""
        return sorted([random.randint(1, 6) for _ in range(4)])

    @staticmethod
    def get_all_pairings(dice: List[int]) -> List[Tuple[int, int]]:
        """Get all 3 possible pairings from 4 dice

        Returns pairings in consistent order to match dice pairs:
        - Pairing 0: (d1+d2, d3+d4) - pair1=orange, pair2=green
        - Pairing 1: (d1+d3, d2+d4) - pair1=orange, pair2=green
        - Pairing 2: (d1+d4, d2+d3) - pair1=orange, pair2=green

        This allows the frontend to consistently color-code dice pairs
        """
        d1, d2, d3, d4 = dice

        return [
            (d1 + d2, d3 + d4),  # Pairing 0: dice[0,1] and dice[2,3]
            (d1 + d3, d2 + d4),  # Pairing 1: dice[0,2] and dice[1,3]
            (d1 + d4, d2 + d3)   # Pairing 2: dice[0,3] and dice[1,2]
        ]

    @staticmethod
    def is_pairing_valid(
        pairing: Tuple[int, int],
        active_runners: Set[int],
        all_completed: Set[int],
        columns_at_top: Set[int] = None
    ) -> bool:
        """Check if pairing has at least one playable number

        A pairing is valid if:
        - At least ONE of the two numbers can be played
        - A number can be played if it's either:
          1. Already an active runner, OR
          2. Not completed AND not at top AND we have room for a new runner (< 3 active)

        NOTE: When both numbers are new, we only need room for ONE of them (player chooses)
        NOTE: Columns that reached the top but aren't saved yet cannot be used
        """
        sum1, sum2 = pairing
        if columns_at_top is None:
            columns_at_top = set()

        # Check if sum1 is playable individually
        sum1_playable = False
        if sum1 not in all_completed and sum1 not in columns_at_top:
            if sum1 in active_runners or len(active_runners) < 3:
                sum1_playable = True

        # Check if sum2 is playable individually (if different from sum1)
        sum2_playable = False
        if sum1 != sum2:
            if sum2 not in all_completed and sum2 not in columns_at_top:
                if sum2 in active_runners or len(active_runners) < 3:
                    sum2_playable = True
        else:
            # If both sums are the same, sum2_playable follows sum1_playable
            sum2_playable = sum1_playable

        # At least one must be playable
        return sum1_playable or sum2_playable

    @staticmethod
    def get_valid_pairings(
        all_pairings: List[Tuple[int, int]],
        active_runners: Set[int],
        all_completed: Set[int],
        columns_at_top: Set[int] = None
    ) -> List[Tuple[int, int]]:
        """Filter to only valid pairings"""
        return [
            p for p in all_pairings
            if GameMechanics.is_pairing_valid(p, active_runners, all_completed, columns_at_top)
        ]

    @staticmethod
    def get_pairing_playability(
        pairing: Tuple[int, int],
        active_runners: Set[int],
        all_completed: Set[int],
        columns_at_top: Set[int] = None
    ) -> Dict[str, bool]:
        """Determine which numbers in a pairing are playable

        Returns dict with:
        - sum1_playable: bool - can sum1 be played individually
        - sum2_playable: bool - can sum2 be played individually
        - both_can_apply: bool - can both be applied together
        - needs_choice: bool - both individually playable but can't apply both (player must choose)
        """
        sum1, sum2 = pairing
        if columns_at_top is None:
            columns_at_top = set()

        # DEBUG: print(f"  Checking playability for pairing {pairing}")
        # DEBUG: print(f"    Active runners: {active_runners} (count: {len(active_runners)})")
        # DEBUG: print(f"    All completed: {all_completed}")
        # DEBUG: print(f"    Columns at top: {columns_at_top}")

        # Check if sum1 is playable individually
        sum1_playable = False
        if sum1 not in all_completed and sum1 not in columns_at_top:
            if sum1 in active_runners or len(active_runners) < 3:
                sum1_playable = True
        # DEBUG: print(f"    sum1={sum1}: playable={sum1_playable} (completed={sum1 in all_completed}, at_top={sum1 in columns_at_top}, active={sum1 in active_runners})")

        # Check if sum2 is playable individually
        sum2_playable = False
        if sum1 != sum2:
            if sum2 not in all_completed and sum2 not in columns_at_top:
                if sum2 in active_runners or len(active_runners) < 3:
                    sum2_playable = True
        else:
            sum2_playable = sum1_playable
        # DEBUG: print(f"    sum2={sum2}: playable={sum2_playable} (completed={sum2 in all_completed}, at_top={sum2 in columns_at_top}, active={sum2 in active_runners})")

        # Can both be applied together?
        both_can_apply = False
        if sum1_playable and sum2_playable and sum1 != sum2:
            # Both are playable individually, but can both be applied together?
            new_runners_needed = 0
            if sum1 not in active_runners:
                new_runners_needed += 1
            if sum2 not in active_runners:
                new_runners_needed += 1
            both_can_apply = (len(active_runners) + new_runners_needed) <= 3
            print(f"    Both playable: new_runners_needed={new_runners_needed}, both_can_apply={both_can_apply}")
        elif sum1_playable and sum1 == sum2:
            both_can_apply = True

        # Need choice if both playable individually but can't apply both together
        needs_choice = sum1_playable and sum2_playable and not both_can_apply and sum1 != sum2
        # DEBUG: print(f"    RESULT: needs_choice={needs_choice}, both_can_apply={both_can_apply}")

        return {
            "sum1_playable": sum1_playable,
            "sum2_playable": sum2_playable,
            "both_can_apply": both_can_apply,
            "needs_choice": needs_choice
        }

    @staticmethod
    def apply_pairing(
        pairing: Tuple[int, int],
        temp_progress: Dict[int, int],
        active_runners: Set[int],
        all_completed: Set[int],
        permanent_progress: Dict[int, int],
        chosen_number: Optional[int] = None
    ) -> Tuple[Dict[int, int], Set[int]]:
        """Apply pairing to temporary state

        If chosen_number is specified, only apply that number.
        Otherwise, apply all playable numbers.
        Caps temp progress so total progress doesn't exceed column length.
        """
        new_temp = dict(temp_progress)
        new_active = set(active_runners)

        sum1, sum2 = pairing

        def cap_temp_progress(col: int, steps_to_add: int) -> int:
            """Cap temporary progress at column length"""
            current_perm = permanent_progress.get(col, 0)
            current_temp = new_temp.get(col, 0)
            max_steps = GameMechanics.COLUMN_LENGTHS[col] - current_perm
            return min(current_temp + steps_to_add, max_steps)

        # If a specific number was chosen, only apply that one
        # For doubles (e.g., 7,7), apply it ONCE even though it appears twice in the pairing
        if chosen_number is not None:
            if chosen_number == sum1 or chosen_number == sum2:
                if chosen_number not in all_completed and (chosen_number in active_runners or len(new_active) < 3):
                    # For doubles, add 2 to progress (move twice)
                    steps = 2 if sum1 == sum2 else 1
                    new_temp[chosen_number] = cap_temp_progress(chosen_number, steps)
                    new_active.add(chosen_number)
            return new_temp, new_active

        # Otherwise, try to apply both
        # For doubles (sum1 == sum2), we advance that column by 2
        if sum1 == sum2:
            # Double! Apply the same number twice
            if sum1 not in all_completed:
                if sum1 in active_runners or len(new_active) < 3:
                    print(f"  Applying DOUBLE {sum1} (moves 2 steps)")
                    new_temp[sum1] = cap_temp_progress(sum1, 2)
                    new_active.add(sum1)
                else:
                    print(f"  Skipping double {sum1} (not in active: {sum1 not in active_runners}, no room: {len(new_active) >= 3})")
        else:
            # Different numbers - try to apply both
            sum1_applied = False
            if sum1 not in all_completed:
                if sum1 in active_runners or len(new_active) < 3:
                    print(f"  Applying sum1={sum1} (in active: {sum1 in active_runners}, room: {len(new_active) < 3})")
                    new_temp[sum1] = cap_temp_progress(sum1, 1)
                    new_active.add(sum1)
                    sum1_applied = True
                else:
                    print(f"  Skipping sum1={sum1} (not in active: {sum1 not in active_runners}, no room: {len(new_active) >= 3})")

            sum2_applied = False
            if sum2 not in all_completed:
                if sum2 in active_runners or len(new_active) < 3:
                    print(f"  Applying sum2={sum2} (in active: {sum2 in active_runners}, room: {len(new_active) < 3})")
                    new_temp[sum2] = cap_temp_progress(sum2, 1)
                    new_active.add(sum2)
                    sum2_applied = True
                else:
                    print(f"  Skipping sum2={sum2} (not in active: {sum2 not in active_runners}, no room: {len(new_active) >= 3})")

            print(f"  Result: sum1_applied={sum1_applied}, sum2_applied={sum2_applied}")

        return new_temp, new_active

    @staticmethod
    def check_reached_tops(
        temp_progress: Dict[int, int],
        permanent_progress: Dict[int, int]
    ) -> Set[int]:
        """Check which columns reached the top"""
        reached = set()
        for col, temp_steps in temp_progress.items():
            total = permanent_progress.get(col, 0) + temp_steps
            if total >= GameMechanics.COLUMN_LENGTHS[col]:
                reached.add(col)
        return reached

    @staticmethod
    def commit_progress(
        temp_progress: Dict[int, int],
        permanent_progress: Dict[int, int],
        player_completed: Set[int]
    ) -> Tuple[Dict[int, int], Set[int]]:
        """Commit temporary progress on stop"""
        new_permanent = dict(permanent_progress)
        newly_completed = set()

        for col, steps in temp_progress.items():
            new_permanent[col] = new_permanent.get(col, 0) + steps

            if new_permanent[col] >= GameMechanics.COLUMN_LENGTHS[col]:
                if col not in player_completed:
                    newly_completed.add(col)

        return new_permanent, newly_completed


# ============================================================================
# GAME STATE MODELS
# ============================================================================

class GameState:
    """Complete game state"""

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.current_player = 1

        # Player progress
        self.player1_permanent = {col: 0 for col in range(2, 13)}
        self.player2_permanent = {col: 0 for col in range(2, 13)}
        self.player1_completed = set()
        self.player2_completed = set()

        # Turn state
        self.current_dice = None
        self.temp_progress = {}
        self.active_runners = set()
        self.available_pairings = []
        self.valid_pairings = []
        self.last_chosen_pairing_index = None  # Track which pairing was just chosen

        # Game status
        self.game_over = False
        self.winner = None
        self.is_bust = False

        # Metadata
        self.created_at = datetime.now().isoformat()
        self.last_updated = datetime.now().isoformat()

        # History for undo/redo
        self.history = []  # List of state snapshots
        self.history_index = -1  # Current position in history

    def _create_snapshot(self) -> dict:
        """Create a snapshot of current game state for history (internal state only)"""
        return {
            "current_player": self.current_player,
            "player1_permanent": dict(self.player1_permanent),
            "player2_permanent": dict(self.player2_permanent),
            "player1_completed": set(self.player1_completed),
            "player2_completed": set(self.player2_completed),
            "current_dice": list(self.current_dice) if self.current_dice else None,
            "temp_progress": dict(self.temp_progress),
            "active_runners": set(self.active_runners),
            "available_pairings": list(self.available_pairings),
            "valid_pairings": list(self.valid_pairings),
            "last_chosen_pairing_index": self.last_chosen_pairing_index,
            "game_over": self.game_over,
            "winner": self.winner,
            "is_bust": self.is_bust
        }

    def _restore_from_snapshot(self, snapshot: dict):
        """Restore game state from a snapshot"""
        self.current_player = snapshot["current_player"]
        self.player1_permanent = dict(snapshot["player1_permanent"])
        self.player2_permanent = dict(snapshot["player2_permanent"])
        self.player1_completed = set(snapshot["player1_completed"])
        self.player2_completed = set(snapshot["player2_completed"])
        self.current_dice = list(snapshot["current_dice"]) if snapshot["current_dice"] else None
        self.temp_progress = dict(snapshot["temp_progress"])
        self.active_runners = set(snapshot["active_runners"])
        self.available_pairings = list(snapshot["available_pairings"])
        self.valid_pairings = list(snapshot["valid_pairings"])
        self.last_chosen_pairing_index = snapshot.get("last_chosen_pairing_index")
        self.game_over = snapshot["game_over"]
        self.winner = snapshot["winner"]
        self.is_bust = snapshot["is_bust"]
        self.last_updated = datetime.now().isoformat()

    def save_to_history(self):
        """Save current state to history, truncating any future history if needed"""
        # If we're not at the end of history, truncate everything after current position
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]

        # Add current state to history
        snapshot = self._create_snapshot()
        self.history.append(snapshot)
        self.history_index = len(self.history) - 1

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict"""
        # Calculate playability info for valid pairings
        all_completed = self.player1_completed.union(self.player2_completed)
        current_perm = (self.player1_permanent if self.current_player == 1
                       else self.player2_permanent)

        # Check which columns reached the top
        columns_at_top = GameMechanics.check_reached_tops(self.temp_progress, current_perm)

        pairing_playability = {}
        for i, pairing in enumerate(self.valid_pairings):
            playability = GameMechanics.get_pairing_playability(
                pairing,
                self.active_runners,
                all_completed,
                columns_at_top
            )
            pairing_playability[i] = playability

        return {
            "game_id": self.game_id,
            "current_player": self.current_player,
            "player1_permanent": self.player1_permanent,
            "player2_permanent": self.player2_permanent,
            "player1_completed": list(self.player1_completed),
            "player2_completed": list(self.player2_completed),
            "current_dice": self.current_dice,
            "temp_progress": self.temp_progress,
            "active_runners": list(self.active_runners),
            "available_pairings": self.available_pairings,
            "valid_pairings": self.valid_pairings,
            "pairing_playability": pairing_playability,  # New: playability info for each valid pairing
            "last_chosen_pairing_index": self.last_chosen_pairing_index,  # Which pairing was just chosen
            "game_over": self.game_over,
            "winner": self.winner,
            "is_bust": self.is_bust,
            "column_lengths": GameMechanics.COLUMN_LENGTHS,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "can_undo": self.history_index > 0,
            "can_redo": self.history_index < len(self.history) - 1
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'GameState':
        """Create GameState from dictionary"""
        game = cls(data["game_id"])
        game.current_player = data["current_player"]
        game.player1_permanent = data["player1_permanent"]
        game.player2_permanent = data["player2_permanent"]
        game.player1_completed = set(data["player1_completed"])
        game.player2_completed = set(data["player2_completed"])
        game.current_dice = data.get("current_dice")
        game.temp_progress = data.get("temp_progress", {})
        game.active_runners = set(data.get("active_runners", []))
        game.available_pairings = data.get("available_pairings", [])
        game.valid_pairings = data.get("valid_pairings", [])
        game.game_over = data.get("game_over", False)
        game.winner = data.get("winner")
        game.is_bust = data.get("is_bust", False)
        game.created_at = data.get("created_at", datetime.now().isoformat())
        game.last_updated = data.get("last_updated", datetime.now().isoformat())

        # Note: We don't restore history when loading from file
        # This gives a fresh start for the loaded game
        # If you want to preserve history, save it in to_dict() and restore it here
        game.history = []
        game.history_index = -1
        game.save_to_history()  # Save the loaded state as the first history entry

        return game


# ============================================================================
# GAME MANAGER
# ============================================================================

class GameManager:
    """Manages active games"""

    def __init__(self):
        self.games: Dict[str, GameState] = {}
        self.save_dir = Path("saved_games")
        self.save_dir.mkdir(exist_ok=True)

    def create_game(self) -> str:
        """Create new game, return game_id"""
        game_id = str(uuid.uuid4())
        game = GameState(game_id)
        # Save initial state to history
        game.save_to_history()
        self.games[game_id] = game
        return game_id

    def get_game(self, game_id: str) -> GameState:
        """Get game by ID"""
        if game_id not in self.games:
            raise HTTPException(status_code=404, detail="Game not found")
        return self.games[game_id]

    def roll_dice(self, game_id: str) -> dict:
        """Roll dice for current player"""
        game = self.get_game(game_id)

        if game.game_over:
            raise HTTPException(status_code=400, detail="Game is over")

        # Save state to history before rolling
        game.save_to_history()

        # Clear bust state from previous roll (if any)
        # Note: Player switch is handled by the continue_after_bust endpoint
        game.is_bust = False

        # Clear last chosen pairing (new roll means new choices)
        game.last_chosen_pairing_index = None

        # Roll dice
        game.current_dice = GameMechanics.roll_dice()
        game.available_pairings = GameMechanics.get_all_pairings(game.current_dice)

        # DEBUG: print(f"\n=== ROLL DICE ===")
        # DEBUG: print(f"Dice: {game.current_dice}")
        # DEBUG: print(f"Available pairings: {game.available_pairings}")
        # DEBUG: print(f"Active runners: {game.active_runners}")

        # Determine valid pairings
        current_perm = (game.player1_permanent if game.current_player == 1
                       else game.player2_permanent)
        current_comp = (game.player1_completed if game.current_player == 1
                       else game.player2_completed)
        opponent_comp = (game.player2_completed if game.current_player == 1
                        else game.player1_completed)

        all_completed = current_comp.union(opponent_comp)
        # DEBUG: print(f"All completed: {all_completed}")

        # Check which columns have reached the top (temp + permanent >= length)
        columns_at_top = GameMechanics.check_reached_tops(game.temp_progress, current_perm)
        # DEBUG: print(f"Columns at top (not yet saved): {columns_at_top}")

        game.valid_pairings = GameMechanics.get_valid_pairings(
            game.available_pairings,
            game.active_runners,
            all_completed,
            columns_at_top
        )

        # DEBUG: print(f"Valid pairings: {game.valid_pairings}")
        # DEBUG: print(f"Calculating playability for {len(game.valid_pairings)} valid pairings:")

        # Check for bust - keep dice visible AND temp pegs visible, DON'T switch player yet
        if len(game.valid_pairings) == 0:
            game.is_bust = True
            print(f"BUST! No valid pairings")

            # DON'T clear temp progress yet - keep pegs visible on board until "Next Player" is clicked
            # This will be cleared in continue_after_bust()
            # game.temp_progress = {}
            # game.active_runners = set()

            # Keep dice, pairings, and temp pegs visible for review
            # DO NOT clear: game.current_dice, game.available_pairings, game.valid_pairings, game.temp_progress, game.active_runners
            # The frontend will show them with disabled state

            # DON'T switch players yet - the busted player stays "current"
            # but the next player's Roll button will be enabled in the frontend
            print(f"Player {game.current_player} is busted, temp pegs remain visible until Next Player clicked")

        # DEBUG: print(f"=================\n")

        return game.to_dict()

    def choose_pairing(self, game_id: str, pairing_index: int, chosen_number: Optional[int] = None) -> dict:
        """Apply chosen pairing

        Args:
            game_id: Game ID
            pairing_index: Index of the chosen pairing
            chosen_number: Optional specific number to play (for partial pairings where choice is needed)
        """
        game = self.get_game(game_id)

        if game.is_bust:
            raise HTTPException(status_code=400, detail="Player busted, cannot choose")

        if pairing_index < 0 or pairing_index >= len(game.valid_pairings):
            raise HTTPException(status_code=400, detail="Invalid pairing index")

        # Save state to history before choosing
        game.save_to_history()

        chosen_pairing = game.valid_pairings[pairing_index]

        # Get current player's permanent progress and completed columns
        current_perm = (game.player1_permanent if game.current_player == 1
                       else game.player2_permanent)
        current_comp = (game.player1_completed if game.current_player == 1
                       else game.player2_completed)
        opponent_comp = (game.player2_completed if game.current_player == 1
                        else game.player1_completed)
        all_completed = current_comp.union(opponent_comp)

        # Debug logging
        # DEBUG: print(f"=== APPLYING PAIRING ===")
        # DEBUG: print(f"Chosen pairing: {chosen_pairing}")
        # DEBUG: print(f"Chosen number: {chosen_number}")
        # DEBUG: print(f"Active runners before: {game.active_runners}")
        # DEBUG: print(f"Temp progress before: {game.temp_progress}")
        # DEBUG: print(f"All completed: {all_completed}")

        # Apply pairing with optional chosen number
        game.temp_progress, game.active_runners = GameMechanics.apply_pairing(
            chosen_pairing,
            game.temp_progress,
            game.active_runners,
            all_completed,
            current_perm,
            chosen_number
        )

        # DEBUG: print(f"Active runners after: {game.active_runners}")
        # DEBUG: print(f"Temp progress after: {game.temp_progress}")
        # DEBUG: print(f"=======================")

        # Keep dice visible AND keep pairings visible (but mark as locked)
        # DON'T clear: game.current_dice, game.available_pairings, game.valid_pairings
        # The frontend will show them as locked/highlighted after selection

        # Track which pairing was chosen so frontend can highlight it
        game.last_chosen_pairing_index = pairing_index

        return game.to_dict()

    def stop_turn(self, game_id: str) -> dict:
        """Stop turn and commit progress"""
        game = self.get_game(game_id)

        # Save state to history before stopping
        game.save_to_history()

        current_perm = (game.player1_permanent if game.current_player == 1
                       else game.player2_permanent)
        current_comp = (game.player1_completed if game.current_player == 1
                       else game.player2_completed)

        # Commit progress
        new_perm, newly_completed = GameMechanics.commit_progress(
            game.temp_progress,
            current_perm,
            current_comp
        )

        # Update state
        if game.current_player == 1:
            game.player1_permanent = new_perm
            game.player1_completed.update(newly_completed)
        else:
            game.player2_permanent = new_perm
            game.player2_completed.update(newly_completed)

        # Check for win
        if len(current_comp.union(newly_completed)) >= 3:
            game.game_over = True
            game.winner = game.current_player

        # Reset turn state
        game.temp_progress = {}
        game.active_runners = set()
        game.current_dice = None
        game.available_pairings = []
        game.valid_pairings = []

        # Switch player if game not over
        if not game.game_over:
            game.current_player = 2 if game.current_player == 1 else 1

        return game.to_dict()

    def continue_after_bust(self, game_id: str) -> dict:
        """Clear bust state and switch to next player"""
        game = self.get_game(game_id)

        # Save state to history before continuing
        game.save_to_history()

        # Clear ONLY temp progress (permanent stays intact)
        game.temp_progress = {}
        game.active_runners = set()
        game.current_dice = None
        game.available_pairings = []
        game.valid_pairings = []
        game.is_bust = False

        # Switch player
        game.current_player = 2 if game.current_player == 1 else 1

        return game.to_dict()

    def undo(self, game_id: str) -> dict:
        """Undo to previous state"""
        game = self.get_game(game_id)

        if game.history_index <= 0:
            raise HTTPException(status_code=400, detail="Nothing to undo")

        # Move back one step in history
        game.history_index -= 1
        snapshot = game.history[game.history_index]
        game._restore_from_snapshot(snapshot)

        return game.to_dict()

    def redo(self, game_id: str) -> dict:
        """Redo to next state"""
        game = self.get_game(game_id)

        if game.history_index >= len(game.history) - 1:
            raise HTTPException(status_code=400, detail="Nothing to redo")

        # Move forward one step in history
        game.history_index += 1
        snapshot = game.history[game.history_index]
        game._restore_from_snapshot(snapshot)

        return game.to_dict()

    def save_game(self, game_id: str, filename: Optional[str] = None) -> str:
        """Save game state to JSON file

        Args:
            game_id: ID of the game to save
            filename: Optional custom filename (without extension)

        Returns:
            Path to saved file
        """
        game = self.get_game(game_id)
        game.last_updated = datetime.now().isoformat()

        if filename is None:
            filename = f"game_{game_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        elif not filename.endswith('.json'):
            filename = f"{filename}.json"

        filepath = self.save_dir / filename

        with open(filepath, 'w') as f:
            json.dump(game.to_dict(), f, indent=2)

        return str(filepath)

    def load_game(self, filename: str) -> str:
        """Load game state from JSON file

        Args:
            filename: Name of the file to load (with or without .json extension)

        Returns:
            game_id of loaded game
        """
        if not filename.endswith('.json'):
            filename = f"{filename}.json"

        filepath = self.save_dir / filename

        if not filepath.exists():
            raise HTTPException(status_code=404, detail=f"Save file not found: {filename}")

        with open(filepath, 'r') as f:
            data = json.load(f)

        game = GameState.from_dict(data)
        self.games[game.game_id] = game

        return game.game_id

    def list_saved_games(self) -> List[Dict[str, str]]:
        """List all saved game files

        Returns:
            List of dicts with filename, game_id, created_at, last_updated
        """
        saved_games = []

        for filepath in self.save_dir.glob("*.json"):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                saved_games.append({
                    "filename": filepath.name,
                    "game_id": data.get("game_id"),
                    "created_at": data.get("created_at"),
                    "last_updated": data.get("last_updated"),
                    "game_over": data.get("game_over", False),
                    "winner": data.get("winner")
                })
            except Exception as e:
                print(f"Error reading {filepath}: {e}")

        # Sort by last_updated descending
        saved_games.sort(key=lambda x: x.get("last_updated", ""), reverse=True)

        return saved_games


# Global game manager
game_manager = GameManager()


# ============================================================================
# API ENDPOINTS
# ============================================================================

class CreateGameResponse(BaseModel):
    game_id: str
    state: dict

class RollDiceResponse(BaseModel):
    state: dict

class ChoosePairingRequest(BaseModel):
    pairing_index: int
    chosen_number: Optional[int] = None  # Specific number to play (for partial pairings)

class ChoosePairingResponse(BaseModel):
    state: dict

class StopTurnResponse(BaseModel):
    state: dict


@app.post("/api/games", response_model=CreateGameResponse)
async def create_game():
    """Create a new game"""
    game_id = game_manager.create_game()
    game = game_manager.get_game(game_id)
    return {"game_id": game_id, "state": game.to_dict()}


@app.get("/api/games/{game_id}")
async def get_game(game_id: str):
    """Get current game state"""
    game = game_manager.get_game(game_id)
    return game.to_dict()


@app.post("/api/games/{game_id}/roll", response_model=RollDiceResponse)
async def roll_dice(game_id: str):
    """Roll dice for current turn"""
    state = game_manager.roll_dice(game_id)
    return {"state": state}


@app.post("/api/games/{game_id}/choose", response_model=ChoosePairingResponse)
async def choose_pairing(game_id: str, request: ChoosePairingRequest):
    """Choose a pairing and apply it"""
    state = game_manager.choose_pairing(game_id, request.pairing_index, request.chosen_number)
    return {"state": state}


@app.post("/api/games/{game_id}/stop", response_model=StopTurnResponse)
async def stop_turn(game_id: str):
    """Stop turn and commit progress"""
    state = game_manager.stop_turn(game_id)
    return {"state": state}


@app.post("/api/games/{game_id}/continue")
async def continue_after_bust(game_id: str):
    """Continue after bust - clears temp state and switches player"""
    state = game_manager.continue_after_bust(game_id)
    return {"state": state}


@app.post("/api/games/{game_id}/undo")
async def undo(game_id: str):
    """Undo to previous game state"""
    state = game_manager.undo(game_id)
    return {"state": state}


@app.post("/api/games/{game_id}/redo")
async def redo(game_id: str):
    """Redo to next game state"""
    state = game_manager.redo(game_id)
    return {"state": state}


@app.post("/api/games/{game_id}/save")
async def save_game(game_id: str, filename: Optional[str] = None):
    """Save game to file"""
    filepath = game_manager.save_game(game_id, filename)
    return {"message": "Game saved successfully", "filepath": filepath}


@app.post("/api/games/load")
async def load_game(filename: str):
    """Load game from file"""
    game_id = game_manager.load_game(filename)
    game = game_manager.get_game(game_id)
    return {"message": "Game loaded successfully", "game_id": game_id, "state": game.to_dict()}


@app.get("/api/games/saved")
async def list_saved_games():
    """List all saved games"""
    games = game_manager.list_saved_games()
    return {"saved_games": games}


@app.get("/")
async def root():
    """Health check"""
    return {"status": "ok", "game": "Can't Stop"}


@app.get("/api/health")
async def health():
    """Health check for Render"""
    return {"status": "healthy", "service": "Can't Stop API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
