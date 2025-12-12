# Can't Stop Strategy Analysis - Updated for Correct Game Rules

## Critical Rule Updates

### The Partial Pairing Rule
**Previous (WRONG)**: Both numbers in a pairing must be playable
**Correct**: At least ONE number must be playable; unplayable numbers are skipped

**Impact on strategies**: This significantly affects:
1. Bust probability calculations (you can't bust with <3 active runners)
2. Pairing selection (prefer doubles to consolidate runners)
3. Conservative strategies (shouldn't stop before 3 runners)

---

## UPDATED STRATEGIES (25 total)

### GROUP 1: BASELINE STRATEGIES (2 strategies)
These establish performance bounds.

#### 1. **Greedy** [EXISTING - NO CHANGES NEEDED]
- **Logic**: Always rolls until bust
- **Pairing choice**: Prefers pairings hitting most active columns
- **Purpose**: Worst-case baseline
- **Expected performance**: ~0.1% win rate

#### 2. **Random(0.3)** [EXISTING - NO CHANGES NEEDED]
- **Logic**: Random stopping (30% chance after each roll)
- **Pairing choice**: Random selection
- **Purpose**: Control baseline for random decision-making
- **Expected performance**: ~50-56% win rate

---

### GROUP 2: CONSERVATIVE STRATEGIES (4 strategies)
Stop after accumulating threshold steps. **NEEDS MAJOR UPDATE**.

#### 3. **Conservative(2)** [UPDATED]
**CHANGE**: Minimum 3 runners before considering stop
- **Stop rule**:
  - If <3 active runners: keep rolling (can't bust yet!)
  - If 3 runners AND unsaved ≥ 2: stop
- **Pairing choice**: Prefer clean moves, then doubles, then most active columns

#### 4. **Conservative(3)** [UPDATED]
- Same logic as Conservative(2), but threshold = 3 steps

#### 5. **Conservative(4)** [UPDATED]
- Same logic as Conservative(2), but threshold = 4 steps

#### 6. **Conservative(1)** [UPDATED - for comparison only]
- Still stops early but respects 3-runner rule
- Expected to perform poorly but included for completeness

---

### GROUP 3: MATHEMATICAL HEURISTIC STRATEGIES (5 strategies)
Use EV calculation: Keep rolling if (P_success × Q) > (α × P_bust × U)

**NEEDS UPDATE**: Pairing selection should prefer doubles when possible

#### 7. **Heuristic(0.3)** [UPDATED - Aggressive]
- **Risk tolerance α = 0.3**: Very aggressive
- **Stop rule**: 3-runner minimum, then EV-based
- **Pairing choice**: Prefer doubles > clean moves > active columns

#### 8. **Heuristic(0.5)** [UPDATED - Moderately Aggressive]
- α = 0.5
- Same pairing preference as above

#### 9. **Heuristic(1.0)** [UPDATED - Neutral]
- α = 1.0: Pure mathematical EV
- **The "theoretically optimal" stopping rule**

#### 10. **Heuristic(1.5)** [UPDATED - Moderately Conservative]
- α = 1.5

#### 11. **Heuristic(2.0)** [UPDATED - Very Conservative]
- α = 2.0

---

### GROUP 4: OPPONENT-AWARE STRATEGIES (4 strategies)
Dynamic risk adjustment based on game state. **NEEDS UPDATE**.

#### 12. **OpponentAware(0.3, 1, 2)** [UPDATED]
- **Logic**: α_behind=0.3, α_tied=1.0, α_ahead=2.0
- **Behind = aggressive, ahead = conservative**
- **Pairing choice**: Prefer doubles > clean > active
- **Stop rule**: 3-runner minimum, then adjusted EV

#### 13. **OpponentAware(0.5, 1, 2)** [UPDATED]
- More moderate when behind (α=0.5)

#### 14. **OpponentAware(0.7, 1, 1.5)** [UPDATED]
- Balanced approach

#### 15. **OpponentAware(2, 1, 0.3)** [NEW - OPPOSITE]
- **Logic**: α_behind=2.0, α_tied=1.0, α_ahead=0.3
- **Behind = conservative, ahead = aggressive**
- **Reasoning**: When behind, minimize losses; when ahead, maximize lead
- **Pairing choice**: Prefer doubles > clean > active
- **Stop rule**: 3-runner minimum, then adjusted EV

---

### GROUP 5: GREEDY-IMPROVED STRATEGIES (2 strategies)
Simple threshold-based improvements. **NEED UPDATES**.

#### 15. **GreedyImproved1** [UPDATED]
- **Stop rule**: All 3 active columns have progress
- **Pairing choice**: Prefer doubles > clean > active
- **Note**: This implicitly requires 3 runners

#### 16. **GreedyImproved2** [UPDATED]
- **Stop rule**: Unsaved progress ≥ 5
- **Pairing choice**: Prefer doubles > clean > active
- **Note**: Add 3-runner minimum for safety

---

### GROUP 6: ADAPTIVE STRATEGIES (1 strategy)
Dynamically adjust based on column combination quality.

#### 17. **AdaptiveThreshold** [UPDATED]
- **Threshold calculation**: 1 + P_success × 5
- **Stop rule**: 3-runner minimum, then threshold-based
- **Pairing choice**: Prefer doubles > clean > active

---

### GROUP 7: PROPORTIONAL STRATEGIES (2 strategies)
Stop based on fraction of remaining column length. **NEED UPDATES**.

#### 18. **ProportionalThreshold(0.33)** [UPDATED]
- **Threshold**: max(1, 0.33 × min(remaining steps))
- **Stop rule**: 3-runner minimum, then threshold
- **Pairing choice**: Prefer doubles > clean > active

#### 19. **ProportionalThreshold(0.5)** [UPDATED]
- Same logic, fraction = 0.5

---

### GROUP 8: COLUMN COMPLETION STRATEGIES (2 strategies)
Focus on completing individual columns **with progressive thresholds**.

#### 20. **GreedyFraction(0.33)** [UPDATED]
- **Stop rule**: Any active column reaches next 1/3 milestone
- **Progressive thresholds**:
  - 0-33% complete: stop when reaching 33%
  - 33-66% complete: stop when reaching 66%
  - 66-100% complete: stop when reaching 100% (completion)
- **Example**: Column 7 (13 steps)
  - Turn 1: Stop after 4+ steps (33% = 4.3)
  - Turn 2: Stop after 8+ steps total (66% = 8.6)
  - Turn 3: Complete it (100% = 13)
- **Pairing choice**: Prefer doubles > clean > active
- **Logic**: Progressive milestones ensure steady advancement

#### 21. **GreedyFraction(0.5)** [UPDATED]
- **Stop rule**: Any active column reaches next 1/2 milestone
- **Progressive thresholds**:
  - 0-50% complete: stop when reaching 50%
  - 50-100% complete: stop when completing (100%)
- **Example**: Column 7 (13 steps)
  - Turn 1: Stop after 6+ steps (50% = 6.5)
  - Turn 2: Complete it (100% = 13)
- **Pairing choice**: Prefer doubles > clean > active

---

### GROUP 9: PROBABILISTIC STRATEGIES (2 strategies)
Use probability calculations for stopping. **CRITICAL: Survival probability depends on runner count!**

#### 22. **FiftyPercentSurvival** [UPDATED]
- **Stop rule**: Roll until cumulative survival < 50%
- **Survival probability calculation**:
  - If <3 active runners: P_success = 1.0 (cannot bust!)
  - If 3 active runners: P_success = P(can hit at least one active column)
  - Must account for completed/blocked columns
- **Formula**: n = log(0.5) / log(P_success)
- **Pairing choice**: Prefer doubles > clean > active
- **Note**: Early game (few blocked columns) vs late game (many blocked) affects probabilities

#### 23. **ExpectedValueMaximizer** [UPDATED]
- **Stop rule**: Stop when EV ≤ 0
- **EV calculation**:
  - If <3 runners: EV = ∞ (can't bust, always continue)
  - If 3 runners: EV = P_success × Q - P_bust × U
  - P_success adjusted for blocked columns
- **Late-game adjustment**: As columns get blocked, available moves decrease
- **Pairing choice**: Prefer doubles > clean > active
- **Note**: This is Heuristic(1.0) but with runner-aware EV

---

### GROUP 10: COLUMN-COUNT STRATEGIES (2 strategies)
Stop based on columns completed.

#### 24. **GreedyUntil1Col** [NO CHANGES NEEDED]
- **Stop rule**: Stop immediately after completing any column
- **Pairing choice**: Prefers active columns
- **Current champion**: 81.6% win rate

#### 25. **GreedyUntil3Col** [NO CHANGES NEEDED]
- **Stop rule**: Never stop until winning entire game
- **Too greedy**: Expected ~51% win rate

---

## NEW STRATEGY IDEAS (13 additional strategies to consider)

### GROUP 11: DOUBLES-FOCUSED STRATEGIES (3 new strategies)
**Note**: Numbers shifted by 1 due to added OpponentAware strategy

#### 26. **DoublesFirst** [NEW]
- **Philosophy**: Doubles consolidate runners, reducing bust risk
- **Pairing choice**:
  1. Always choose doubles if available (even non-active)
  2. Then clean moves
  3. Then active columns
- **Stop rule**: Conservative(3) stopping logic
- **Hypothesis**: Consolidating runners faster = better long-term position

#### 27. **SmartDoubles** [NEW]
- **Pairing choice**:
  1. Doubles on active columns (best case)
  2. Doubles on columns 5-9 (good columns, worth activating)
  3. Clean moves
  4. Active columns
- **Stop rule**: Heuristic(1.0)
- **Hypothesis**: Smart double selection beats blind preference

#### 28. **ColumnCompletionPriority** [NEW]
- **Pairing choice**:
  1. Doubles that would complete a column this turn
  2. Moves that would complete a column
  3. Doubles on near-complete columns
  4. Clean moves
- **Stop rule**: GreedyUntil1Col logic
- **Hypothesis**: Prioritizing completion > consolidation

---

### GROUP 12: RUNNER-COUNT AWARE (3 new strategies)

#### 29. **MinimalistRunner** [NEW]
- **Philosophy**: Stay at 1-2 runners as long as possible
- **Pairing choice**:
  1. Doubles (keeps runner count low)
  2. Single active column moves
  3. Only activate 3rd runner if necessary
- **Stop rule**: When 3rd runner activated + unsaved ≥ 3
- **Hypothesis**: Fewer runners = lower bust risk

#### 30. **TwoRunnerSweet** [NEW - UPDATED]
- **Philosophy**: 2 runners is optimal (some redundancy, not too risky)
- **Stop rule**:
  - If <3 runners: keep rolling (can't bust!)
  - If 3 runners just activated: stop immediately (conservative)
  - If 3 runners already active: stop when unsaved ≥ 2
- **Pairing choice**: Doubles > clean(2 runners) > active
- **Hypothesis**: 2 runners balances risk vs reward, stop as soon as 3rd appears

#### 31. **DynamicRunnerThreshold** [NEW - UPDATED]
- **Stop threshold based on runner count**:
  - 1 runner: never stop (threshold = ∞, can't bust)
  - 2 runners: never stop (threshold = ∞, can't bust)
  - 3 runners: threshold = 3 (stop when unsaved ≥ 3)
- **Pairing choice**: Prefer doubles
- **Hypothesis**: Only consider stopping with 3 active runners
- **Note**: This is essentially Conservative(3) with explicit runner awareness

---

### GROUP 13: COLUMN-QUALITY AWARE (3 new strategies)

#### 32. **MiddleColumnsOnly** [NEW - UPDATED]
- **Philosophy**: Strongly prefer columns 5-9 (best combinations)
- **Pairing choice**:
  1. Doubles on columns 5-9 (highest priority)
  2. Clean moves within columns 5-9
  3. Any move involving at least one column from 5-9
  4. Other moves if necessary
- **Stop rule**:
  - If <3 runners: keep rolling
  - If 3 runners and all from {5-9}: stop when unsaved ≥ 4
  - If 3 runners with non-middle columns: stop when unsaved ≥ 2 (exit bad position)
- **Hypothesis**: Quality > quantity, but don't bust intentionally
- **Note**: Prefers middle columns but pragmatic when forced

#### 33. **WeightedColumnValue** [NEW - Middle-preferring]
- **Column weights**: {2:0.5, 3:0.6, 4:0.8, 5:1.0, 6:1.2, 7:1.3, 8:1.2, 9:1.0, 10:0.8, 11:0.6, 12:0.5}
- **Pairing choice**: Choose pairing maximizing weighted sum
- **Stop rule**: Weighted unsaved progress ≥ 5.0
- **Hypothesis**: Middle columns worth more, should influence both selection and stopping

#### 34. **WeightedColumnValueOuter** [NEW - Outer-preferring]
- **Column weights**: {2:1.3, 3:1.2, 4:1.0, 5:0.8, 6:0.6, 7:0.5, 8:0.6, 9:0.8, 10:1.0, 11:1.2, 12:1.3}
- **Pairing choice**: Choose pairing maximizing weighted sum (favoring outer columns)
- **Stop rule**: Weighted unsaved progress ≥ 5.0
- **Hypothesis**: Outer columns are undervalued - shorter length compensates for lower hit rate
- **Note**: Counter-intuitive strategy to test if conventional wisdom is wrong

#### 35. **OpportunisticActivation** [NEW]
- **Philosophy**: Only activate new runners on "good" rolls
- **Activation criteria**:
  - Doubles on columns 5-9: always activate
  - Columns 6-8 when paired together: activate
  - Other columns: only if <3 runners already
- **Stop rule**: Heuristic(1.0)
- **Hypothesis**: Being selective about activation improves column quality

---

### GROUP 14: HYBRID/ADVANCED (3 new strategies)

#### 36. **TwoPhase** [NEW]
- **Phase 1 (0 completed)**: Aggressive (α=0.5), prefer middle columns
- **Phase 2 (1 completed)**: Moderate (α=1.0), any good columns
- **Phase 3 (2 completed)**: Conservative (α=1.5), focus on near-complete
- **Pairing choice**: Doubles > phase-appropriate columns
- **Hypothesis**: Strategy should evolve as game progresses

#### 37. **RiskBudget** [NEW]
- **Philosophy**: Each turn has a "risk budget" (cumulative bust probability)
- **Budget**: 20% per turn (stop when cumulative bust ≥ 20%)
- **Calculation**: After n rolls, P_bust_cumulative = 1 - P_success^n
- **Pairing choice**: Doubles > clean > active
- **Hypothesis**: Fixed risk budget per turn optimizes long-term

#### 38. **MonteCarloLookahead** [NEW]
- **Philosophy**: Before each decision, simulate 100 random future rolls
- **Pairing choice**: Choose pairing with highest expected value (MC simulated)
- **Stop decision**: Stop if MC simulation shows EV(continue) < EV(stop)
- **Note**: Computationally expensive, but "perfect play" benchmark
- **Hypothesis**: Perfect information provides upper bound

---

## TESTING METHODOLOGY

### Single-Player Benchmarking
**Purpose**: Measure strategy efficiency in isolation (no opponent pressure)

**Metrics to track**:
1. **Turns to complete 1 column** (average, median, std dev)
2. **Turns to complete 2 columns** (average, median, std dev)
3. **Turns to complete 3 columns** (average, median, std dev)
4. **Bust rate** (busts per successful turn)
5. **Average unsaved progress when stopping** (risk tolerance measure)
6. **Column preferences** (which columns does each strategy favor)

**Test conditions**:
- All columns available (2-12)
- 1,000 trials per strategy
- Record full game history for each trial
- Save results to: `single_player_results_YYYYMMDD_HHMMSS.json`

**Output format**:
```json
{
  "strategy_name": "GreedyUntil1Col",
  "trials": 1000,
  "metrics": {
    "turns_to_1_col": {"avg": 3.2, "median": 3, "std": 1.1, "min": 1, "max": 8},
    "turns_to_2_col": {"avg": 6.8, "median": 6, "std": 2.3, "min": 3, "max": 15},
    "turns_to_3_col": {"avg": 10.5, "median": 10, "std": 3.1, "min": 5, "max": 22},
    "bust_rate": 0.23,
    "avg_unsaved_when_stop": 3.4,
    "column_preferences": {
      "2": 45, "3": 89, ..., "12": 42
    }
  },
  "raw_trials": [...]
}
```

### Head-to-Head Tournament
**Purpose**: Determine competitive performance (strategy vs strategy)

**Matchups**:
- Each strategy plays every other strategy
- 2,500 games per matchup
- Record: wins, losses, avg turns, avg columns completed

**Special tests**:
1. Each strategy vs itself (should be ~50% win rate, validates implementation)
2. First-player advantage analysis (does going first provide an edge?)

**First-Player Advantage Tracking**:
- For each matchup, track which player (P1 or P2) used which strategy
- Calculate win rate for each strategy as both Player 1 and Player 2
- Overall first-player advantage: P1_wins / total_games across all matchups
- Per-strategy first-player advantage: how much better/worse each strategy performs as P1 vs P2

**Output format**:
```json
{
  "tournament_date": "2025-01-15",
  "strategies": ["Strategy1", "Strategy2", ...],
  "matchups": {
    "Strategy1_vs_Strategy2": {
      "games": 2500,
      "strategy1_wins": 1342,
      "strategy2_wins": 1158,
      "strategy1_winrate": 0.537,
      "avg_turns": 8.3,
      "confidence_interval_95": "±0.019"
    },
    ...
  },
  "self_matchups": {
    "Strategy1_vs_Strategy1": {
      "games": 2500,
      "player1_wins": 1253,
      "player2_wins": 1247,
      "winrate": 0.501
    },
    ...
  },
  "first_player_advantage": {
    "overall": {
      "total_games": 3610000,
      "player1_wins": 1823456,
      "player2_wins": 1786544,
      "player1_winrate": 0.505,
      "advantage": "+0.5%"
    },
    "per_strategy": {
      "Strategy1": {
        "as_player1": {"wins": 15234, "games": 30000, "winrate": 0.508},
        "as_player2": {"wins": 14876, "games": 30000, "winrate": 0.496},
        "advantage": "+1.2%"
      },
      ...
    }
  }
}
```

### Implementation Details
**Backend**: Use `/tmp/cantstop-game/backend/main.py` GameMechanics class
- `roll_dice()`, `get_all_pairings()`, `is_pairing_valid()`, `apply_pairing()`
- Ensures correct partial-pairing rule implementation

**Results storage**: Save all raw data for post-analysis
- CSV files for easy analysis
- JSON files for full game histories
- Plots generated from results

---

## SUMMARY OF CHANGES

### Major Updates Needed (17 strategies)
1. **Conservative(1-4)**: Add 3-runner minimum (can't bust with <3 runners!)
2. **Heuristic(all)**: Add doubles preference to pairing choice
3. **OpponentAware(all 3 + 1 NEW)**: Add doubles preference + 3-runner minimum
4. **GreedyImproved1-2**: Add doubles preference
5. **AdaptiveThreshold**: Add 3-runner minimum + doubles
6. **Proportional(all)**: Add 3-runner minimum + doubles
7. **GreedyFraction(all)**: Progressive thresholds (1/3→2/3→1, or 1/2→1) + doubles preference
8. **FiftyPercentSurvival**: Runner-aware survival probability + doubles
9. **ExpectedValueMax**: Runner-aware EV calculation + doubles

### No Changes Needed (4 strategies)
1. **Greedy**: Already maximal
2. **Random**: Intentionally simple
3. **GreedyUntil1Col**: Already good pairing logic
4. **GreedyUntil3Col**: Too greedy anyway

### Pairing Preference Logic (to add to most strategies)

```python
def choose_pairing_smart(game, valid_pairings):
    """
    Smart pairing selection:
    1. Doubles on active columns (consolidate + progress)
    2. Doubles on good columns 5-9 (worth activating)
    3. Clean moves (only active columns)
    4. Moves hitting most active columns
    5. Random/first available
    """
    active = game.active_columns

    # Priority 1: Doubles on active columns
    for sums, pairing in valid_pairings:
        if sums[0] == sums[1] and sums[0] in active:
            return (sums, pairing)

    # Priority 2: Doubles on columns 5-9 (if room for new runner)
    if len(active) < 3:
        for sums, pairing in valid_pairings:
            if sums[0] == sums[1] and 5 <= sums[0] <= 9:
                return (sums, pairing)

    # Priority 3: Clean moves (all sums in active)
    for sums, pairing in valid_pairings:
        available_sums = [s for s in sums if game.is_column_available(s)]
        if all(s in active for s in available_sums):
            return (sums, pairing)

    # Priority 4: Most active columns hit
    best = max(valid_pairings,
               key=lambda p: sum(1 for s in p[0] if s in active))
    return best
```

---

## RECOMMENDED STRATEGY SET

### For Initial Testing (15 strategies)
Keep these from original 25:
1. Greedy (baseline)
2. Conservative(3), Conservative(4) (updated)
3. Heuristic(0.5), Heuristic(1.0), Heuristic(1.5) (updated)
4. OpponentAware(0.7,1,1.5) (updated)
5. GreedyImproved2 (updated)
6. AdaptiveThreshold (updated)
7. GreedyFraction(0.33) (updated)
8. FiftyPercentSurvival (updated)
9. ExpectedValueMaximizer (updated)
10. GreedyUntil1Col (no change)
11. Random(0.3) (control)

Add these new strategies:
12. DoublesFirst (NEW)
13. SmartDoubles (NEW)
14. TwoRunnerSweet (NEW)
15. WeightedColumnValue (NEW)

### For Extended Analysis (26 strategies)
Add to above:
16. Conservative(2) (updated, for comparison)
17. Heuristic(0.3), Heuristic(2.0) (updated)
18. OpponentAware(0.3,1,2), OpponentAware(0.5,1,2) (updated)
19. ProportionalThreshold(0.5) (updated)
20. GreedyFraction(0.5) (updated)
21. ColumnCompletionPriority (NEW)
22. MinimalistRunner (NEW)
23. DynamicRunnerThreshold (NEW)
24. TwoPhase (NEW)
25. RiskBudget (NEW)

### For Research/Benchmarking (38 strategies - all)
Include all 26 from extended + the remaining 12 new ideas

---

## BLOG POST INTEGRATION

### Files to Update
1. **Replace** `single_player_results.txt` with new results
2. **Replace** `analysis_results_25strategies_2500games.txt` with new tournament results
3. **Update** visualizations:
   - `single_player_performance.png` (turns to complete 3 columns)
   - `strategy_tournament_rankings.png` (overall win rates)
   - `tournament_heatmap_full.png` (full matchup matrix)
   - `speed_vs_winrate_analysis.png` (single-player vs tournament performance)

### Blog Post Sections to Update
1. **Strategy Performance** (lines 302-417 in blog post)
   - Update strategy descriptions
   - Replace single-player results table
   - Update champion analysis with corrected implementation

2. **Tournament Results** (lines 363-432)
   - New win-rate rankings
   - Updated matchup matrix
   - Confidence intervals for all matchups

3. **Speed vs Win Rate** (lines 437-452)
   - Re-analyze correlation with correct rules
   - Update scatter plots and analysis

### What Changes in Results?
**Expected differences from old analysis**:
1. **Conservative strategies improve** (they were stopping too early before)
2. **Doubles-focused strategies perform better** (new mechanic awareness)
3. **Runner-aware strategies dominate** (exploit partial-pairing rule)
4. **Bust rates decrease overall** (can't bust with <3 runners)
5. **GreedyUntil1Col might still win** (or might be overtaken by smarter strategies)
6. **First-player advantage revealed** (if any exists)

### First-Player Advantage Analysis
**Questions to answer**:
1. Is there an overall first-player advantage in Can't Stop?
2. Does it vary by strategy (some strategies benefit more from going first)?
3. Does it vary by matchup (certain strategy pairs have asymmetric advantages)?
4. What's the magnitude (is it 1%, 5%, 10%)?

**Why it matters**:
- If significant (>3%), tournament results need adjustment
- Strategies that exploit turn order might be overrated/underrated
- Important for understanding game balance

---

## IMPLEMENTATION PLAN

### Phase 1: Single-Player Benchmarking (1-2 days)
1. Implement all 38 strategies with correct rules
2. Run 1,000 trials per strategy
3. Generate single-player results JSON/CSV
4. Create visualizations
5. Update blog post with new results

### Phase 2: Head-to-Head Tournament (2-3 days)
1. Run all matchups (38×38 = 1,444 matchups × 2,500 games = 3.6M games)
2. Include self-matchups for validation
3. Generate tournament results JSON/CSV
4. Create heatmap and ranking visualizations
5. Update blog post with tournament analysis

### Phase 3: Blog Post Finalization (1 day)
1. Replace all old results
2. Update strategy descriptions
3. Re-run analysis on correlation/insights
4. Verify all visualizations
5. Final review

**Total estimated time**: 4-6 days of computation + analysis

---

## NEXT STEPS

Ready to implement! Shall I:
1. ✅ Start with implementing the 38 updated/new strategies
2. ✅ Use the GitHub repo backend for game mechanics
3. ✅ Run single-player benchmarking first (1,000 trials each)
4. ✅ Then proceed to tournament (2,500 games per matchup)
5. ✅ Save all results with timestamps for reproducibility
6. ✅ Update blog post with new findings

Let me know if you'd like any adjustments before I begin!
