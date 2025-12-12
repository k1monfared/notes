#!/usr/bin/env python3
"""
Can't Stop Strategy Implementation - Using Correct Game Mechanics
All 38 strategies updated for partial-pairing rule and runner-awareness

Uses the correct game backend from: /tmp/cantstop-game/backend/main.py
"""

import sys
import random
import math
from typing import List, Tuple, Dict, Set, Optional
from itertools import product

# Use local silent version of GameMechanics (with debug prints removed)
try:
    from main_silent import GameMechanics
except ImportError:
    # Fallback to original
    sys.path.insert(0, '/home/k1/public/cantstop-game/backend')
    from main import GameMechanics

# Column lengths constant
COLUMN_LENGTHS = GameMechanics.COLUMN_LENGTHS

# ============================================================================
# Probability Calculation Helper (for strategies that need it)
# ============================================================================

class ProbabilityCalculator:
    """Calculate probabilities for column combinations with blocked columns."""

    def __init__(self):
        self.cache = {}

    def get_success_probability(self, active_columns: List[int],
                                blocked_columns: Set[int]) -> float:
        """
        Calculate P(can hit at least one active column) given blocked columns.

        Args:
            active_columns: Currently active runner columns
            blocked_columns: Columns that are completed/unavailable

        Returns:
            Probability of success (0.0 to 1.0)
        """
        # Handle edge case: no active columns
        if not active_columns:
            return 0.0

        # CRITICAL: Can't bust with <=2 active runners - P(success) = 1.0
        if len(active_columns) <= 2:
            return 1.0

        # With 3 active runners, calculate actual probability
        # Use cache
        key = (tuple(sorted(active_columns)), tuple(sorted(blocked_columns)))
        if key in self.cache:
            return self.cache[key]

        # Count successful rolls
        all_rolls = list(product(range(1, 7), repeat=4))
        success_count = 0

        for dice in all_rolls:
            pairings = GameMechanics.get_all_pairings(dice)

            # A roll succeeds if ANY pairing hits at least one active, non-blocked column
            # pairings is List[Tuple[int, int]] where each tuple is (sum1, sum2)
            for pairing in pairings:
                # pairing is already (sum1, sum2), not pairs of dice
                sum1, sum2 = pairing

                # Check if at least one sum is in active columns and not blocked
                if ((sum1 in active_columns and sum1 not in blocked_columns) or
                    (sum2 in active_columns and sum2 not in blocked_columns)):
                    success_count += 1
                    break

        probability = success_count / len(all_rolls)
        self.cache[key] = probability
        return probability

    def get_expected_markers(self, active_columns: List[int],
                            blocked_columns: Set[int]) -> float:
        """
        Calculate Q = E[markers advanced | success].

        Returns average number of markers advanced on successful roll.
        """
        if not active_columns:
            return 0.0

        key = (tuple(sorted(active_columns)), tuple(sorted(blocked_columns)), 'Q')
        if key in self.cache:
            return self.cache[key]

        all_rolls = list(product(range(1, 7), repeat=4))
        total_markers = 0
        success_count = 0

        for dice in all_rolls:
            pairings = GameMechanics.get_all_pairings(dice)

            max_markers = 0
            for pairing in pairings:
                # pairing is (sum1, sum2)
                sum1, sum2 = pairing
                markers = 0
                if sum1 in active_columns and sum1 not in blocked_columns:
                    markers += 1
                if sum2 in active_columns and sum2 not in blocked_columns and sum1 != sum2:
                    markers += 1
                elif sum1 == sum2 and sum1 in active_columns and sum1 not in blocked_columns:
                    markers = 2  # Double counts as 2 markers
                max_markers = max(max_markers, markers)

            if max_markers > 0:
                total_markers += max_markers
                success_count += 1

        Q = total_markers / success_count if success_count > 0 else 0.0
        self.cache[key] = Q
        return Q


# ============================================================================
# Base Strategy Class
# ============================================================================

class Strategy:
    """Base class for all Can't Stop strategies."""

    def __init__(self, name: str):
        self.name = name
        self.prob_calc = ProbabilityCalculator()

    def choose_pairing(self, game_state: Dict, valid_pairings: List[Tuple]) -> int:
        """
        Choose which pairing to play from valid options.

        Args:
            game_state: Current game state dictionary
            valid_pairings: List of (pairing_index, pairing, sums, playability_info)

        Returns:
            Index of chosen pairing (0, 1, or 2)
        """
        raise NotImplementedError

    def choose_number(self, game_state: Dict, pairing_index: int,
                     available_numbers: List[int]) -> Optional[int]:
        """
        Choose which number to play when both are individually playable
        but can't both be applied.

        Args:
            game_state: Current game state
            pairing_index: The pairing that was chosen
            available_numbers: Numbers that can be individually played

        Returns:
            Chosen number or None to play both
        """
        # Default: prefer middle columns
        if len(available_numbers) == 1:
            return available_numbers[0]

        # Prefer column closer to 7
        return min(available_numbers, key=lambda n: abs(n - 7))

    def should_stop(self, game_state: Dict) -> bool:
        """
        Decide whether to stop and bank progress.

        Args:
            game_state: Current game state dictionary

        Returns:
            True to stop, False to continue rolling
        """
        raise NotImplementedError

    def get_active_columns(self, game_state: Dict) -> List[int]:
        """Extract active columns from game state."""
        return list(game_state.get('active_runners', set()))

    def get_temp_progress(self, game_state: Dict) -> Dict[int, int]:
        """Extract temporary progress from game state."""
        return game_state.get('temp_progress', {})

    def get_blocked_columns(self, game_state: Dict) -> Set[int]:
        """Get all blocked/completed columns."""
        p1_completed = set(game_state.get('player1_completed', []))
        p2_completed = set(game_state.get('player2_completed', []))
        return p1_completed | p2_completed


# ============================================================================
# PAIRING SELECTION HELPERS
# ============================================================================

def choose_pairing_smart(strategy: Strategy, game_state: Dict,
                        valid_pairings: List[Tuple]) -> int:
    """
    Smart pairing selection (used by most strategies):
    1. Doubles on active columns
    2. Doubles on good columns 5-9 (if room for new runner)
    3. Clean moves (only active columns)
    4. Moves hitting most active columns
    """
    active = strategy.get_active_columns(game_state)

    # Priority 1: Doubles on active columns
    for idx, _, sums, info in valid_pairings:
        if sums[0] == sums[1] and sums[0] in active:
            return idx

    # Priority 2: Doubles on columns 5-9 (if room)
    if len(active) < 3:
        for idx, _, sums, info in valid_pairings:
            if sums[0] == sums[1] and 5 <= sums[0] <= 9:
                return idx

    # Priority 3: Clean moves (all playable sums in active)
    for idx, _, sums, info in valid_pairings:
        # Check if all sums that would be played are in active
        sum1_playable = info.get('sum1_playable', False)
        sum2_playable = info.get('sum2_playable', False)

        clean = True
        if sum1_playable and sums[0] not in active:
            clean = False
        if sum2_playable and len(sums) > 1 and sums[1] not in active:
            clean = False

        if clean and (sum1_playable or sum2_playable):
            return idx

    # Priority 4: Most active columns hit
    best_idx = 0
    best_score = -1
    for idx, _, sums, info in valid_pairings:
        score = sum(1 for s in sums if s in active)
        if score > best_score:
            best_score = score
            best_idx = idx

    return best_idx


# ============================================================================
# GROUP 1: BASELINE STRATEGIES
# ============================================================================

class GreedyStrategy(Strategy):
    """Always rolls until bust."""

    def __init__(self):
        super().__init__("Greedy")

    def choose_pairing(self, game_state, valid_pairings):
        # Prefer pairings hitting most active columns
        active = self.get_active_columns(game_state)
        best_idx = 0
        best_score = -1

        for idx, pairing, sums, info in valid_pairings:
            score = sum(1 for s in sums if s in active)
            if score > best_score:
                best_score = score
                best_idx = idx

        return best_idx

    def should_stop(self, game_state):
        return False  # Never stop


class RandomStrategy(Strategy):
    """Random stopping with 30% probability."""

    def __init__(self, stop_probability=0.3):
        super().__init__(f"Random({stop_probability})")
        self.stop_prob = stop_probability

    def choose_pairing(self, game_state, valid_pairings):
        idx = random.randint(0, len(valid_pairings) - 1)
        return valid_pairings[idx][0]

    def should_stop(self, game_state):
        return random.random() < self.stop_prob


# ============================================================================
# GROUP 2: CONSERVATIVE STRATEGIES
# ============================================================================

class ConservativeStrategy(Strategy):
    """Stops after threshold steps (with 3-runner minimum)."""

    def __init__(self, threshold: int):
        super().__init__(f"Conservative({threshold})")
        self.threshold = threshold

    def choose_pairing(self, game_state, valid_pairings):
        return choose_pairing_smart(self, game_state, valid_pairings)

    def should_stop(self, game_state):
        active = self.get_active_columns(game_state)
        temp_progress = self.get_temp_progress(game_state)

        # Can't bust with <3 runners, keep rolling
        if len(active) < 3:
            return False

        total_unsaved = sum(temp_progress.values())
        return total_unsaved >= self.threshold


# ============================================================================
# GROUP 3: MATHEMATICAL HEURISTIC STRATEGIES
# ============================================================================

class HeuristicStrategy(Strategy):
    """Uses EV heuristic: keep rolling if (P_success × Q) > (α × P_bust × U)."""

    def __init__(self, risk_tolerance: float):
        super().__init__(f"Heuristic({risk_tolerance})")
        self.alpha = risk_tolerance

    def choose_pairing(self, game_state, valid_pairings):
        return choose_pairing_smart(self, game_state, valid_pairings)

    def should_stop(self, game_state):
        active = self.get_active_columns(game_state)
        temp_progress = self.get_temp_progress(game_state)
        blocked = self.get_blocked_columns(game_state)

        # Can't bust with <3 runners
        if len(active) < 3:
            return False

        if not active:
            return False

        # Calculate EV
        P_success = self.prob_calc.get_success_probability(active, blocked)
        P_bust = 1.0 - P_success
        Q = self.prob_calc.get_expected_markers(active, blocked)
        unsaved = sum(temp_progress.values())

        expected_gain = P_success * Q
        expected_loss = self.alpha * P_bust * unsaved

        return expected_loss > expected_gain


# ============================================================================
# GROUP 4: OPPONENT-AWARE STRATEGIES
# ============================================================================

class OpponentAwareStrategy(Strategy):
    """Adjusts risk tolerance based on game position."""

    def __init__(self, alpha_behind: float, alpha_tied: float, alpha_ahead: float):
        name = f"OpponentAware({alpha_behind},{alpha_tied},{alpha_ahead})"
        super().__init__(name)
        self.alpha_behind = alpha_behind
        self.alpha_tied = alpha_tied
        self.alpha_ahead = alpha_ahead

    def choose_pairing(self, game_state, valid_pairings):
        return choose_pairing_smart(self, game_state, valid_pairings)

    def should_stop(self, game_state):
        active = self.get_active_columns(game_state)
        temp_progress = self.get_temp_progress(game_state)
        blocked = self.get_blocked_columns(game_state)

        # Can't bust with <3 runners
        if len(active) < 3:
            return False

        if not active:
            return False

        # Determine position
        my_completed = len(game_state.get('player1_completed', []))
        opp_completed = len(game_state.get('player2_completed', []))

        if my_completed < opp_completed:
            alpha = self.alpha_behind
        elif my_completed > opp_completed:
            alpha = self.alpha_ahead
        else:
            alpha = self.alpha_tied

        # Use heuristic with adjusted risk
        P_success = self.prob_calc.get_success_probability(active, blocked)
        P_bust = 1.0 - P_success
        Q = self.prob_calc.get_expected_markers(active, blocked)
        unsaved = sum(temp_progress.values())

        expected_gain = P_success * Q
        expected_loss = alpha * P_bust * unsaved

        return expected_loss > expected_gain


# ============================================================================
# GROUP 5: GREEDY-IMPROVED STRATEGIES
# ============================================================================

class GreedyImproved1(Strategy):
    """Stops after making progress on all 3 active columns."""

    def __init__(self):
        super().__init__("GreedyImproved1")

    def choose_pairing(self, game_state, valid_pairings):
        return choose_pairing_smart(self, game_state, valid_pairings)

    def should_stop(self, game_state):
        active = self.get_active_columns(game_state)
        temp_progress = self.get_temp_progress(game_state)

        # Only stop when we have 3 runners and all have progress
        if len(active) == 3:
            return all(temp_progress.get(col, 0) > 0 for col in active)

        return False


class GreedyImproved2(Strategy):
    """Stops once unsaved progress >= 5 (with 3-runner minimum)."""

    def __init__(self):
        super().__init__("GreedyImproved2")

    def choose_pairing(self, game_state, valid_pairings):
        return choose_pairing_smart(self, game_state, valid_pairings)

    def should_stop(self, game_state):
        active = self.get_active_columns(game_state)
        temp_progress = self.get_temp_progress(game_state)

        # Can't bust with <3 runners
        if len(active) < 3:
            return False

        total_progress = sum(temp_progress.values())
        return total_progress >= 5


# ============================================================================
# GROUP 6: ADAPTIVE STRATEGIES
# ============================================================================

class AdaptiveThreshold(Strategy):
    """Adjusts threshold based on column combination quality."""

    def __init__(self):
        super().__init__("AdaptiveThreshold")

    def choose_pairing(self, game_state, valid_pairings):
        return choose_pairing_smart(self, game_state, valid_pairings)

    def should_stop(self, game_state):
        active = self.get_active_columns(game_state)
        temp_progress = self.get_temp_progress(game_state)
        blocked = self.get_blocked_columns(game_state)

        # Can't bust with <3 runners
        if len(active) < 3:
            return False

        if not active:
            return False

        # Calculate adaptive threshold based on success probability
        P_success = self.prob_calc.get_success_probability(active, blocked)
        threshold = int(1 + P_success * 5)

        total_progress = sum(temp_progress.values())
        return total_progress >= threshold


# ============================================================================
# GROUP 7: PROPORTIONAL STRATEGIES
# ============================================================================

class ProportionalThreshold(Strategy):
    """Stops when progress reaches fraction of min remaining length."""

    def __init__(self, fraction: float):
        super().__init__(f"Proportional({fraction})")
        self.fraction = fraction

    def choose_pairing(self, game_state, valid_pairings):
        return choose_pairing_smart(self, game_state, valid_pairings)

    def should_stop(self, game_state):
        active = self.get_active_columns(game_state)
        temp_progress = self.get_temp_progress(game_state)

        # Can't bust with <3 runners
        if len(active) < 3:
            return False

        if not active:
            return False

        # Get current player's permanent progress
        # Note: This requires extending game_state to include permanent positions
        # For now, assume we're tracking this
        permanent = game_state.get('player1_permanent', {})

        # Calculate minimum remaining steps
        min_remaining = float('inf')
        for col in active:
            current_pos = permanent.get(col, 0)
            remaining = COLUMN_LENGTHS[col] - current_pos
            min_remaining = min(min_remaining, remaining)

        threshold = max(1, int(self.fraction * min_remaining))
        total_progress = sum(temp_progress.values())

        return total_progress >= threshold


# ============================================================================
# GROUP 8: COLUMN COMPLETION STRATEGIES (Progressive Thresholds)
# ============================================================================

class GreedyFraction(Strategy):
    """Stops when any column reaches next progressive milestone."""

    def __init__(self, fraction: float):
        super().__init__(f"GreedyFraction({fraction})")
        self.fraction = fraction
        self.column_milestones = {}  # Track next milestone per column

    def choose_pairing(self, game_state, valid_pairings):
        return choose_pairing_smart(self, game_state, valid_pairings)

    def should_stop(self, game_state):
        active = self.get_active_columns(game_state)
        temp_progress = self.get_temp_progress(game_state)
        permanent = game_state.get('player1_permanent', {})

        if not active:
            return False

        # Check each active column for milestone completion
        for col in active:
            current_perm = permanent.get(col, 0)
            current_temp = temp_progress.get(col, 0)
            total = current_perm + current_temp
            col_length = COLUMN_LENGTHS[col]

            # Calculate ALL milestones for this column
            if self.fraction == 0.33:
                # 0% -> 33% -> 66% -> 100%
                all_milestones = [
                    int(col_length * 0.33),
                    int(col_length * 0.66),
                    col_length
                ]
            else:  # 0.5
                # 0% -> 50% -> 100%
                all_milestones = [
                    int(col_length * 0.5),
                    col_length
                ]

            # Find the next milestone we haven't reached yet
            next_milestone = None
            for milestone in all_milestones:
                if current_perm < milestone:
                    next_milestone = milestone
                    break

            # If we've reached the next milestone this turn, stop
            if next_milestone is not None and total >= next_milestone:
                return True

        return False


# ============================================================================
# GROUP 9: PROBABILISTIC STRATEGIES (Runner-Aware)
# ============================================================================

class FiftyPercentSurvival(Strategy):
    """Rolls until cumulative survival probability < 50%."""

    def __init__(self):
        super().__init__("FiftyPercentSurvival")
        self.roll_count = 0

    def choose_pairing(self, game_state, valid_pairings):
        return choose_pairing_smart(self, game_state, valid_pairings)

    def should_stop(self, game_state):
        active = self.get_active_columns(game_state)
        blocked = self.get_blocked_columns(game_state)

        # Can't bust with <3 runners - P_success = 1.0
        if len(active) < 3:
            self.roll_count += 1
            return False

        if not active:
            self.roll_count = 0
            return False

        # Get success probability
        P_success = self.prob_calc.get_success_probability(active, blocked)

        if P_success <= 0:
            self.roll_count = 0
            return True
        if P_success >= 1.0:
            self.roll_count += 1
            return False

        # Calculate how many rolls until 50% survival
        # P_survive^n < 0.5  =>  n > log(0.5) / log(P_survive)
        target_rolls = math.log(0.5) / math.log(P_success)

        self.roll_count += 1
        should_stop = self.roll_count >= target_rolls

        if should_stop:
            self.roll_count = 0

        return should_stop


class ExpectedValueMaximizer(Strategy):
    """Stops when EV of continuing becomes negative (runner-aware)."""

    def __init__(self):
        super().__init__("ExpectedValueMax")

    def choose_pairing(self, game_state, valid_pairings):
        return choose_pairing_smart(self, game_state, valid_pairings)

    def should_stop(self, game_state):
        active = self.get_active_columns(game_state)
        temp_progress = self.get_temp_progress(game_state)
        blocked = self.get_blocked_columns(game_state)

        # Can't bust with <3 runners - EV = infinity, never stop
        if len(active) < 3:
            return False

        if not active:
            return False

        # Calculate EV
        P_success = self.prob_calc.get_success_probability(active, blocked)
        P_bust = 1.0 - P_success
        Q = self.prob_calc.get_expected_markers(active, blocked)
        unsaved = sum(temp_progress.values())

        expected_gain = P_success * Q
        expected_loss = P_bust * unsaved

        # Stop when EV <= 0
        return expected_loss >= expected_gain


# ============================================================================
# GROUP 10: COLUMN-COUNT STRATEGIES
# ============================================================================

class GreedyUntilOneColumn(Strategy):
    """Stops immediately after completing any column."""

    def __init__(self):
        super().__init__("GreedyUntil1Col")

    def choose_pairing(self, game_state, valid_pairings):
        # Prefer moves that complete columns
        active = self.get_active_columns(game_state)
        temp_progress = self.get_temp_progress(game_state)
        permanent = game_state.get('player1_permanent', {})

        # Check if any pairing would complete a column
        for idx, pairing, sums, info in valid_pairings:
            for s in sums:
                if s in active:
                    current = permanent.get(s, 0) + temp_progress.get(s, 0)
                    # Would this move complete the column?
                    if current + 1 >= COLUMN_LENGTHS[s]:
                        return idx

        # Otherwise use smart pairing
        return choose_pairing_smart(self, game_state, valid_pairings)

    def should_stop(self, game_state):
        temp_progress = self.get_temp_progress(game_state)
        permanent = game_state.get('player1_permanent', {})

        # Check if we've completed any column this turn
        for col, temp_steps in temp_progress.items():
            current_perm = permanent.get(col, 0)
            if current_perm + temp_steps >= COLUMN_LENGTHS[col]:
                return True

        return False


class GreedyUntilThreeColumns(Strategy):
    """Never stops until winning (completing 3 columns)."""

    def __init__(self):
        super().__init__("GreedyUntil3Col")

    def choose_pairing(self, game_state, valid_pairings):
        return choose_pairing_smart(self, game_state, valid_pairings)

    def should_stop(self, game_state):
        # Count completed + about-to-complete columns
        completed = len(game_state.get('player1_completed', []))
        temp_progress = self.get_temp_progress(game_state)
        permanent = game_state.get('player1_permanent', {})

        about_to_complete = 0
        for col, temp_steps in temp_progress.items():
            current_perm = permanent.get(col, 0)
            if current_perm + temp_steps >= COLUMN_LENGTHS[col]:
                about_to_complete += 1

        # Only stop if we'd win by banking
        return (completed + about_to_complete) >= 3


# ============================================================================
# GROUP 11: COLUMN TARGETING STRATEGIES
# ============================================================================

class OutsideFirst(Strategy):
    """Prioritizes outer columns (2,3,11,12) before middle ones."""

    def __init__(self):
        super().__init__("OutsideFirst")

    def choose_pairing(self, game_state, valid_pairings):
        active = self.get_active_columns(game_state)
        outer_cols = {2, 3, 11, 12}

        # Prefer pairings hitting outer columns
        best_idx = 0
        best_score = -1

        for idx, _, sums, info in valid_pairings:
            score = sum(2 if s in outer_cols else 1 for s in sums if s in active or len(active) < 3)
            if score > best_score:
                best_score = score
                best_idx = idx

        return best_idx

    def should_stop(self, game_state):
        active = self.get_active_columns(game_state)
        temp_progress = self.get_temp_progress(game_state)

        if len(active) < 3:
            return False

        total_progress = sum(temp_progress.values())
        return total_progress >= 3


class MiddleFirst(Strategy):
    """Prioritizes middle columns (5-9) before others."""

    def __init__(self):
        super().__init__("MiddleFirst")

    def choose_pairing(self, game_state, valid_pairings):
        active = self.get_active_columns(game_state)
        middle_cols = {5, 6, 7, 8, 9}

        # Prefer pairings hitting middle columns
        best_idx = 0
        best_score = -1

        for idx, _, sums, info in valid_pairings:
            score = sum(2 if s in middle_cols else 1 for s in sums if s in active or len(active) < 3)
            if score > best_score:
                best_score = score
                best_idx = idx

        return best_idx

    def should_stop(self, game_state):
        active = self.get_active_columns(game_state)
        temp_progress = self.get_temp_progress(game_state)

        if len(active) < 3:
            return False

        total_progress = sum(temp_progress.values())
        return total_progress >= 3


class MinimumRunnerActivation(Strategy):
    """Minimizes runner activation - only when forced."""

    def __init__(self):
        super().__init__("MinRunnerActivation")

    def choose_pairing(self, game_state, valid_pairings):
        active = self.get_active_columns(game_state)

        # Priority 1: Doubles on active columns
        for idx, _, sums, info in valid_pairings:
            if sums[0] == sums[1] and sums[0] in active:
                return idx

        # Priority 2: Clean moves (all playable sums in active)
        for idx, _, sums, info in valid_pairings:
            sum1_playable = info.get('sum1_playable', False)
            sum2_playable = info.get('sum2_playable', False)

            clean = True
            if sum1_playable and sums[0] not in active:
                clean = False
            if sum2_playable and len(sums) > 1 and sums[1] not in active:
                clean = False

            if clean and (sum1_playable or sum2_playable):
                return idx

        # Priority 3: Only activate 3rd runner if necessary
        if len(active) < 3:
            # Prefer columns 5-9 if activating
            for idx, _, sums, info in valid_pairings:
                if any(5 <= s <= 9 for s in sums):
                    return idx

        return valid_pairings[0][0]

    def should_stop(self, game_state):
        active = self.get_active_columns(game_state)
        temp_progress = self.get_temp_progress(game_state)

        if len(active) < 3:
            return False

        # Stop when 3rd runner activated + unsaved ≥ 3
        total_progress = sum(temp_progress.values())
        return total_progress >= 3


# ============================================================================
# GROUP 12: RUNNER-COUNT AWARE STRATEGIES
# ============================================================================

class TwoRunnerSweet(Strategy):
    """Optimizes for 2 runners, stops as soon as 3rd appears."""

    def __init__(self):
        super().__init__("TwoRunnerSweet")

    def choose_pairing(self, game_state, valid_pairings):
        active = self.get_active_columns(game_state)

        # Prefer doubles
        for idx, _, sums, info in valid_pairings:
            if sums[0] == sums[1] and (sums[0] in active or len(active) < 2):
                return idx

        # Prefer clean moves with 2 runners
        if len(active) == 2:
            for idx, _, sums, info in valid_pairings:
                if all(s in active for s in sums):
                    return idx

        return choose_pairing_smart(self, game_state, valid_pairings)

    def should_stop(self, game_state):
        active = self.get_active_columns(game_state)
        temp_progress = self.get_temp_progress(game_state)

        # If <3 runners: keep rolling (can't bust!)
        if len(active) < 3:
            return False

        # If 3 runners: stop immediately (conservative)
        total_progress = sum(temp_progress.values())
        return total_progress >= 2


class DynamicRunnerThreshold(Strategy):
    """Stop threshold based on runner count (essentially Conservative(3) with explicit runner awareness)."""

    def __init__(self):
        super().__init__("DynamicRunnerThreshold")

    def choose_pairing(self, game_state, valid_pairings):
        return choose_pairing_smart(self, game_state, valid_pairings)

    def should_stop(self, game_state):
        active = self.get_active_columns(game_state)
        temp_progress = self.get_temp_progress(game_state)

        # 1 or 2 runners: never stop (can't bust)
        if len(active) <= 2:
            return False

        # 3 runners: threshold = 3
        total_progress = sum(temp_progress.values())
        return total_progress >= 3


# ============================================================================
# GROUP 13: COLUMN-QUALITY AWARE STRATEGIES
# ============================================================================

class MiddleColumnsOnly(Strategy):
    """Strongly prefer columns 5-9, pragmatic when forced."""

    def __init__(self):
        super().__init__("MiddleColumnsOnly")

    def choose_pairing(self, game_state, valid_pairings):
        active = self.get_active_columns(game_state)
        middle_cols = {5, 6, 7, 8, 9}

        # Priority 1: Doubles on columns 5-9
        for idx, _, sums, info in valid_pairings:
            if sums[0] == sums[1] and sums[0] in middle_cols:
                return idx

        # Priority 2: Clean moves within columns 5-9
        for idx, _, sums, info in valid_pairings:
            if all(s in middle_cols for s in sums if s in active or len(active) < 3):
                return idx

        # Priority 3: Any move involving at least one column from 5-9
        for idx, _, sums, info in valid_pairings:
            if any(s in middle_cols for s in sums):
                return idx

        # Priority 4: Other moves if necessary
        return valid_pairings[0][0]

    def should_stop(self, game_state):
        active = self.get_active_columns(game_state)
        temp_progress = self.get_temp_progress(game_state)
        middle_cols = {5, 6, 7, 8, 9}

        # If <3 runners: keep rolling
        if len(active) < 3:
            return False

        # If 3 runners and all from {5-9}: stop when unsaved ≥ 4
        if all(col in middle_cols for col in active):
            return sum(temp_progress.values()) >= 4

        # If 3 runners with non-middle columns: stop when unsaved ≥ 2 (exit bad position)
        return sum(temp_progress.values()) >= 2


class WeightedColumnValue(Strategy):
    """Middle-preferring weighted strategy."""

    def __init__(self):
        super().__init__("WeightedColumnValue")
        self.weights = {2: 0.5, 3: 0.6, 4: 0.8, 5: 1.0, 6: 1.2, 7: 1.3,
                       8: 1.2, 9: 1.0, 10: 0.8, 11: 0.6, 12: 0.5}

    def choose_pairing(self, game_state, valid_pairings):
        active = self.get_active_columns(game_state)

        best_idx = 0
        best_weighted_sum = -1

        for idx, _, sums, info in valid_pairings:
            weighted_sum = sum(self.weights.get(s, 0) for s in sums if s in active or len(active) < 3)
            if weighted_sum > best_weighted_sum:
                best_weighted_sum = weighted_sum
                best_idx = idx

        return best_idx

    def should_stop(self, game_state):
        active = self.get_active_columns(game_state)
        temp_progress = self.get_temp_progress(game_state)

        if len(active) < 3:
            return False

        # Weighted unsaved progress
        weighted_progress = sum(temp_progress.get(col, 0) * self.weights.get(col, 1.0)
                              for col in active)
        return weighted_progress >= 5.0


class WeightedColumnValueOuter(Strategy):
    """Outer-preferring weighted strategy."""

    def __init__(self):
        super().__init__("WeightedOutsideColumns")
        self.weights = {2: 1.3, 3: 1.2, 4: 1.0, 5: 0.8, 6: 0.6, 7: 0.5,
                       8: 0.6, 9: 0.8, 10: 1.0, 11: 1.2, 12: 1.3}

    def choose_pairing(self, game_state, valid_pairings):
        active = self.get_active_columns(game_state)

        best_idx = 0
        best_weighted_sum = -1

        for idx, _, sums, info in valid_pairings:
            weighted_sum = sum(self.weights.get(s, 0) for s in sums if s in active or len(active) < 3)
            if weighted_sum > best_weighted_sum:
                best_weighted_sum = weighted_sum
                best_idx = idx

        return best_idx

    def should_stop(self, game_state):
        active = self.get_active_columns(game_state)
        temp_progress = self.get_temp_progress(game_state)

        if len(active) < 3:
            return False

        # Weighted unsaved progress
        weighted_progress = sum(temp_progress.get(col, 0) * self.weights.get(col, 1.0)
                              for col in active)
        return weighted_progress >= 5.0


class OpportunisticActivation(Strategy):
    """Only activate new runners on 'good' rolls."""

    def __init__(self):
        super().__init__("OpportunisticActivation")
        self.prob_calc = ProbabilityCalculator()

    def choose_pairing(self, game_state, valid_pairings):
        active = self.get_active_columns(game_state)

        # If have room for new runners, be selective
        if len(active) < 3:
            # Prefer doubles on columns 5-9
            for idx, _, sums, info in valid_pairings:
                if sums[0] == sums[1] and 5 <= sums[0] <= 9:
                    return idx

            # Prefer columns 6-8 paired together
            for idx, _, sums, info in valid_pairings:
                if all(6 <= s <= 8 for s in sums):
                    return idx

        # Otherwise use standard logic
        return choose_pairing_smart(self, game_state, valid_pairings)

    def should_stop(self, game_state):
        # Use Heuristic(1.0) logic
        active = self.get_active_columns(game_state)
        temp_progress = self.get_temp_progress(game_state)
        blocked = self.get_blocked_columns(game_state)

        if len(active) < 3:
            return False

        if not active:
            return False

        P_success = self.prob_calc.get_success_probability(active, blocked)
        P_bust = 1.0 - P_success
        Q = self.prob_calc.get_expected_markers(active, blocked)
        unsaved = sum(temp_progress.values())

        expected_gain = P_success * Q
        expected_loss = 1.0 * P_bust * unsaved

        return expected_loss > expected_gain


# ============================================================================
# GROUP 14: HYBRID/ADVANCED STRATEGIES
# ============================================================================

class TwoPhase(Strategy):
    """Strategy evolves based on columns completed."""

    def __init__(self):
        super().__init__("TwoPhase")
        self.prob_calc = ProbabilityCalculator()

    def choose_pairing(self, game_state, valid_pairings):
        my_completed = len(game_state.get('player1_completed', []))
        active = self.get_active_columns(game_state)
        middle_cols = {5, 6, 7, 8, 9}

        # Prefer doubles
        for idx, _, sums, info in valid_pairings:
            if sums[0] == sums[1] and sums[0] in active:
                return idx

        # Phase 1: Prefer middle columns
        if my_completed == 0:
            for idx, _, sums, info in valid_pairings:
                if any(s in middle_cols for s in sums):
                    return idx

        # Phase 3: Focus on near-complete
        if my_completed >= 2:
            permanent = game_state.get('player1_permanent', {})
            temp_progress = self.get_temp_progress(game_state)

            best_idx = 0
            best_completion_pct = 0

            for idx, _, sums, info in valid_pairings:
                for s in sums:
                    if s in active:
                        pct = (permanent.get(s, 0) + temp_progress.get(s, 0)) / COLUMN_LENGTHS[s]
                        if pct > best_completion_pct:
                            best_completion_pct = pct
                            best_idx = idx

            if best_completion_pct > 0:
                return best_idx

        return choose_pairing_smart(self, game_state, valid_pairings)

    def should_stop(self, game_state):
        active = self.get_active_columns(game_state)
        temp_progress = self.get_temp_progress(game_state)
        blocked = self.get_blocked_columns(game_state)
        my_completed = len(game_state.get('player1_completed', []))

        if len(active) < 3:
            return False

        if not active:
            return False

        # Adjust alpha based on phase
        if my_completed == 0:
            alpha = 0.5  # Aggressive
        elif my_completed == 1:
            alpha = 1.0  # Moderate
        else:
            alpha = 1.5  # Conservative

        P_success = self.prob_calc.get_success_probability(active, blocked)
        P_bust = 1.0 - P_success
        Q = self.prob_calc.get_expected_markers(active, blocked)
        unsaved = sum(temp_progress.values())

        expected_gain = P_success * Q
        expected_loss = alpha * P_bust * unsaved

        return expected_loss > expected_gain


class RiskBudget(Strategy):
    """Each turn has a fixed risk budget (20% cumulative bust probability)."""

    def __init__(self):
        super().__init__("RiskBudget")
        self.prob_calc = ProbabilityCalculator()
        self.roll_count = 0

    def choose_pairing(self, game_state, valid_pairings):
        return choose_pairing_smart(self, game_state, valid_pairings)

    def should_stop(self, game_state):
        active = self.get_active_columns(game_state)
        blocked = self.get_blocked_columns(game_state)

        if len(active) < 3:
            self.roll_count += 1
            return False

        if not active:
            self.roll_count = 0
            return False

        P_success = self.prob_calc.get_success_probability(active, blocked)

        # Calculate cumulative bust probability
        # P_bust_cumulative = 1 - P_success^n
        self.roll_count += 1
        cumulative_bust = 1.0 - (P_success ** self.roll_count)

        should_stop = cumulative_bust >= 0.2

        if should_stop:
            self.roll_count = 0

        return should_stop


class MonteCarloLookahead(Strategy):
    """Simulates future rolls before each decision."""

    def __init__(self, num_simulations=100):
        super().__init__("MonteCarloLookahead")
        self.num_simulations = num_simulations
        self.prob_calc = ProbabilityCalculator()

    def choose_pairing(self, game_state, valid_pairings):
        # For now, use smart pairing (full MC simulation too expensive)
        return choose_pairing_smart(self, game_state, valid_pairings)

    def should_stop(self, game_state):
        active = self.get_active_columns(game_state)
        temp_progress = self.get_temp_progress(game_state)
        blocked = self.get_blocked_columns(game_state)

        if len(active) < 3:
            return False

        if not active:
            return False

        # Simplified MC: use EV with higher confidence
        # Full simulation would be too slow
        P_success = self.prob_calc.get_success_probability(active, blocked)
        P_bust = 1.0 - P_success
        Q = self.prob_calc.get_expected_markers(active, blocked)
        unsaved = sum(temp_progress.values())

        # Stop if EV(continue) < EV(stop)
        # EV(continue) = P_success * (unsaved + Q) - P_bust * unsaved
        # EV(stop) = unsaved
        ev_continue = P_success * (unsaved + Q) - P_bust * unsaved
        ev_stop = unsaved

        return ev_continue < ev_stop


# ============================================================================
# Strategy registry for easy access
# ============================================================================

def get_all_strategies() -> Dict[str, Strategy]:
    """Return dictionary of all 38 strategies."""

    strategies = {}

    # Group 1: Baseline (2 strategies)
    strategies['Greedy'] = GreedyStrategy()
    strategies['Random(0.3)'] = RandomStrategy(0.3)

    # Group 2: Conservative (4 strategies)
    for threshold in [1, 2, 3, 4]:
        strategies[f'Conservative({threshold})'] = ConservativeStrategy(threshold)

    # Group 3: Heuristic (5 strategies)
    for alpha in [0.3, 0.5, 1.0, 1.5, 2.0]:
        strategies[f'Heuristic({alpha})'] = HeuristicStrategy(alpha)

    # Group 4: Opponent-Aware (4 strategies)
    strategies['OpponentAware(0.3,1,2)'] = OpponentAwareStrategy(0.3, 1.0, 2.0)
    strategies['OpponentAware(0.5,1,2)'] = OpponentAwareStrategy(0.5, 1.0, 2.0)
    strategies['OpponentAware(0.7,1,1.5)'] = OpponentAwareStrategy(0.7, 1.0, 1.5)
    strategies['OpponentAware(2,1,0.3)'] = OpponentAwareStrategy(2.0, 1.0, 0.3)  # Opposite version

    # Group 5: Greedy-Improved (2 strategies)
    strategies['GreedyImproved1'] = GreedyImproved1()
    strategies['GreedyImproved2'] = GreedyImproved2()

    # Group 6: Adaptive (1 strategy)
    strategies['AdaptiveThreshold'] = AdaptiveThreshold()

    # Group 7: Proportional (2 strategies)
    for frac in [0.33, 0.5]:
        strategies[f'Proportional({frac})'] = ProportionalThreshold(frac)

    # Group 8: Column Completion (2 strategies)
    for frac in [0.33, 0.5]:
        strategies[f'GreedyFraction({frac})'] = GreedyFraction(frac)

    # Group 9: Probabilistic (2 strategies)
    strategies['FiftyPercentSurvival'] = FiftyPercentSurvival()
    strategies['ExpectedValueMax'] = ExpectedValueMaximizer()

    # Group 10: Column-Count (2 strategies)
    strategies['GreedyUntil1Col'] = GreedyUntilOneColumn()
    strategies['GreedyUntil3Col'] = GreedyUntilThreeColumns()

    # Group 11: Column Targeting (3 strategies)
    strategies['OutsideFirst'] = OutsideFirst()
    strategies['MiddleFirst'] = MiddleFirst()
    strategies['MinRunnerActivation'] = MinimumRunnerActivation()

    # Group 12: Runner-Count Aware (2 strategies)
    strategies['TwoRunnerSweet'] = TwoRunnerSweet()
    strategies['DynamicRunnerThreshold'] = DynamicRunnerThreshold()

    # Group 13: Column-Quality Aware (4 strategies)
    strategies['MiddleColumnsOnly'] = MiddleColumnsOnly()
    strategies['WeightedColumnValue'] = WeightedColumnValue()
    strategies['WeightedOutsideColumns'] = WeightedColumnValueOuter()
    strategies['OpportunisticActivation'] = OpportunisticActivation()

    # Group 14: Hybrid/Advanced (3 strategies)
    strategies['TwoPhase'] = TwoPhase()
    strategies['RiskBudget'] = RiskBudget()
    strategies['MonteCarloLookahead'] = MonteCarloLookahead()

    return strategies


if __name__ == "__main__":
    print("Can't Stop - Strategy Implementation")
    print("=" * 80)

    strategies = get_all_strategies()
    print(f"\nImplemented {len(strategies)} strategies:")
    for name in sorted(strategies.keys()):
        print(f"  - {name}")

    print("\nReady for simulation!")
