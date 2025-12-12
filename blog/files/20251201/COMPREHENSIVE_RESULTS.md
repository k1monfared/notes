# Can't Stop: Comprehensive Strategy Analysis Results

**Simulation Date**: December 10, 2025
**Total Runtime**: 3.89 hours
**Strategies Tested**: 38
**Single-Player Trials**: 1,000 per strategy (38,000 total)
**Head-to-Head Games**: 2,500 per matchup (3,610,000 total across 1,444 matchups)

---

## Executive Summary

After running 3.6 million games across 38 different strategies, we found that **FiftyPercentSurvival** emerged as the dominant strategy in competitive head-to-head play with a **69.84% overall win rate**, while **GreedyUntil1Col** proved fastest in single-player efficiency averaging just **10.5 turns** to complete three columns.

**Key Findings**:
1. **Probabilistic strategies dominate**: Strategies using survival probability calculations outperform simple threshold-based approaches
2. **Significant first-player advantage**: Player 1 wins 55.59% of games overall (+11.18% advantage)
3. **Some strategies are position-sensitive**: GreedyUntil1Col shows extreme first-player bias (+31.24%)
4. **Middle columns are preferred**: Top strategies complete columns 6-8 most frequently
5. **Self-play fairness issues**: 4 strategies show >10% deviation from 50/50 in mirror matchups

---

## Top Performers

### Single-Player Efficiency (Speed to Win)

Measured by average turns to complete all 3 columns in solo play:

| Rank | Strategy | Avg Turns | Median | StdDev | Avg Busts | Win Speed |
|------|----------|-----------|--------|--------|-----------|-----------|
| 1 | **GreedyUntil1Col** | 10.5 | 9 | 5.73 | 7.50 | ⚡⚡⚡ Fastest |
| 2 | **FiftyPercentSurvival** | 11.3 | 11 | 2.86 | 2.67 | ⚡⚡ Very Fast |
| 3 | **OpponentAware(0.5,1,2)** | 11.4 | 11 | 3.02 | 2.86 | ⚡⚡ Very Fast |
| 4 | **OpponentAware(0.3,1,2)** | 11.6 | 11 | 3.15 | 2.95 | ⚡⚡ Very Fast |
| 5 | **OpponentAware(0.7,1,1.5)** | 11.8 | 11 | 3.63 | 3.59 | ⚡ Fast |
| 6 | **Heuristic(1.5)** | 11.9 | 12 | 2.78 | 2.03 | ⚡ Fast |
| 7 | **Heuristic(2.0)** | 12.3 | 12 | 2.14 | 0.92 | ⚡ Fast |
| 8 | **Heuristic(1.0)** | 12.3 | 12 | 4.26 | 4.87 | ⚡ Fast |
| 9 | **ExpectedValueMax** | 12.3 | 12 | 5.01 | 4.98 | ⚡ Fast |
| 10 | **MonteCarloLookahead** | 12.4 | 12 | 2.14 | 0.97 | ⚡ Fast |

**Key Insights**:
- **GreedyUntil1Col** is fastest but has high variance (σ=5.73) and bust rate (7.50 per game)
- **FiftyPercentSurvival** balances speed with consistency (σ=2.86, only 2.67 busts)
- **Heuristic(2.0)** and **MonteCarloLookahead** are most conservative (< 1 bust per game)
- The top 10 all complete games in 11-12 turns on average

### Head-to-Head Competitive Performance

Measured by overall win rate across all matchups:

| Rank | Strategy | Win Rate | Total Wins | P1 Advantage | Games |
|------|----------|----------|------------|--------------|-------|
| 1 | **FiftyPercentSurvival** | 69.84% | 132,696 | +9.42% | 190,000 |
| 2 | **Heuristic(1.5)** | 66.46% | 126,274 | +10.15% | 190,000 |
| 3 | **Heuristic(2.0)** | 63.26% | 120,194 | +11.73% | 190,000 |
| 4 | **MonteCarloLookahead** | 63.09% | 119,871 | +11.38% | 190,000 |
| 5 | **AdaptiveThreshold** | 62.21% | 118,199 | +11.14% | 190,000 |
| 6 | **ExpectedValueMax** | 62.08% | 117,952 | +8.40% | 190,000 |
| 7 | **Heuristic(1.0)** | 61.87% | 117,553 | +8.49% | 190,000 |
| 8 | **OpportunisticActivation** | 61.43% | 116,717 | +7.28% | 190,000 |
| 9 | **GreedyImproved2** | 60.23% | 114,437 | +11.06% | 190,000 |
| 10 | **OpponentAware(0.7,1,1.5)** | 59.92% | 113,848 | +12.58% | 190,000 |
| 11 | **GreedyUntil1Col** | 58.90% | 111,910 | +31.24% | 190,000 |

**Key Insights**:
- **FiftyPercentSurvival** dominates with nearly 70% win rate
- **Heuristic strategies** (especially 1.5 and 2.0) perform extremely well in competition
- **MonteCarloLookahead** (our "perfect play" baseline) places 4th, suggesting the top 3 are near-optimal
- **GreedyUntil1Col** is #1 in speed but only #11 in competitive play - speed isn't everything!
- Most top strategies show 8-12% first-player advantage (more on this below)

---

## The Champion Strategy: FiftyPercentSurvival

**Performance Summary**:
- **Head-to-head win rate**: 69.84% (#1)
- **Single-player avg turns**: 11.3 (#2)
- **Bust rate**: 2.67 per game (very low)
- **Variance**: 2.86 (highly consistent)
- **First-player advantage**: +9.42% (moderate)

**How it works**:
```
Stop rolling when cumulative survival probability drops below 50%

P(survival) calculation:
- If <3 active runners: P=1.0 (can't bust!)
- If 3 active runners: P = P(can hit at least one active column)
- Must account for completed/blocked columns

Number of safe rolls: n = log(0.5) / log(P_success)
```

**Why it wins**:
1. **Mathematically sound**: Uses actual probability rather than heuristics
2. **Balances risk and reward**: 50% threshold is aggressive enough to make progress but conservative enough to avoid frequent busts
3. **Adapts to game state**: Probability changes as columns get blocked, strategy adjusts automatically
4. **Column preferences**: Favors middle columns (6-8) which have optimal frequency/length ratio

**Column Preferences** (from 1,000 trials):
- Most completed: Column 8 (42.0%), Column 7 (38.4%), Column 6 (37.7%)
- Most used: Column 8 (3.14×), Column 6 (3.09×), Column 7 (3.08×)

---

## Speed vs Competition Trade-off

There's a fascinating disconnect between single-player speed and competitive win rate:

| Strategy | Single-Player Rank | Avg Turns | H2H Rank | Win Rate | Trade-off |
|----------|-------------------|-----------|----------|----------|-----------|
| **GreedyUntil1Col** | #1 | 10.5 | #11 | 58.90% | Speed > Power |
| **FiftyPercentSurvival** | #2 | 11.3 | #1 | 69.84% | ✅ Best Balance |
| **OpponentAware(0.5,1,2)** | #3 | 11.4 | #15 | 56.20% | Speed > Power |
| **Heuristic(1.5)** | #6 | 11.9 | #2 | 66.46% | Power > Speed |
| **Heuristic(2.0)** | #7 | 12.3 | #3 | 63.26% | Power > Speed |

**Analysis**:
- **GreedyUntil1Col** wins fast but busts often (7.5 per game) and has massive first-player bias (+31%)
- **FiftyPercentSurvival** achieves the best of both worlds: #2 in speed, #1 in competition
- More conservative **Heuristic** strategies sacrifice 0.6-1.0 turns but gain +3-6% win rate
- In competitive play, **consistency beats raw speed**

---

## First-Player Advantage Analysis

### Overall Advantage
Across all 3.6 million games:
- **Player 1 win rate**: 55.59%
- **Player 2 win rate**: 44.41%
- **First-player advantage**: +11.18%

This is a **significant advantage**. Going first provides an 11-point swing in win probability, likely due to:
1. First access to middle columns (6-8)
2. Setting the pace of the game
3. Opponent must play catch-up

### Strategies with Extreme First-Player Bias

Some strategies are highly position-sensitive:

| Strategy | P1 Advantage | Interpretation |
|----------|--------------|----------------|
| **GreedyUntil1Col** | +31.24% | ⚠️ EXTREME bias - wins 73% as P1! |
| **GreedyFraction(0.5)** | +31.00% | ⚠️ EXTREME bias |
| **OpponentAware(0.3,1,2)** | +18.94% | High bias |
| **OpponentAware(0.5,1,2)** | +15.62% | High bias |
| **GreedyUntil3Col** | +13.95% | Moderate-high bias |

**Why GreedyUntil1Col is biased**:
- Stops immediately after completing 1 column
- As P1, likely completes column before P2 gets established
- As P2, P1 has already claimed a column, harder to catch up
- This makes it less viable in competitive play despite raw speed

### Fairest Strategies (Lowest First-Player Advantage)

| Strategy | P1 Advantage | Interpretation |
|----------|--------------|----------------|
| **OpponentAware(2,1,0.3)** | -4.14% | Actually favors P2! |
| **Greedy** | -0.03% | ✅ Perfectly balanced |
| **Heuristic(0.3)** | +0.65% | ✅ Nearly balanced |
| **Heuristic(0.5)** | +3.30% | Fair |
| **Random(0.3)** | +6.77% | Fair |

**OpponentAware(2,1,0.3)** is the opposite strategy (conservative when behind, aggressive when ahead) and actually benefits from going second. This suggests **catching up is easier with conservative play** in Can't Stop.

---

## Self-Play Fairness Check

When a strategy plays against itself, we expect ~50% win rate for each player (assuming the strategy is deterministic or has balanced randomness). **4 strategies failed this check**:

| Strategy | P1 Win Rate in Self-Play | Deviation | Issue |
|----------|---------------------------|-----------|-------|
| **GreedyUntil1Col** | 73.28% | +23.28% | ⚠️ SEVERE - not balanced! |
| **GreedyFraction(0.5)** | 70.16% | +20.16% | ⚠️ SEVERE |
| **GreedyFraction(0.33)** | 61.44% | +11.44% | ⚠️ Moderate |
| **Proportional(0.5)** | 60.04% | +10.04% | ⚠️ Moderate |

**What this means**:
- These strategies have **inherent first-player bias** even in mirror matchups
- GreedyUntil1Col's bias is so extreme it dominates identical opponents 73-27 just by going first
- This affects their tournament rankings - they're overperforming in aggregate due to positional advantage
- For true skill assessment, we should look at their **performance as Player 2**

---

## Counter-Strategy Analysis

### What Beats the Top 3?

#### Counters to FiftyPercentSurvival (#1, 69.84% overall)
When playing against FiftyPercentSurvival, these strategies perform best:

| Rank | Strategy | Win Rate vs FPS | Games |
|------|----------|-----------------|-------|
| 1 | **FiftyPercentSurvival** | 50.00% | 5,000 |
| 2 | **OpportunisticActivation** | 46.00% | 5,000 |
| 3 | **Heuristic(1.5)** | 45.62% | 5,000 |
| 4 | **GreedyUntil1Col** | 44.78% | 5,000 |
| 5 | **Heuristic(1.0)** | 43.66% | 5,000 |

**Analysis**: FiftyPercentSurvival is nearly unbeatable - even its best counters only win 46% of games. Only mirror match achieves 50/50.

#### Counters to GreedyUntil1Col (#1 speed, #11 competitive)

| Rank | Strategy | Win Rate vs GU1C | Games |
|------|----------|------------------|-------|
| 1 | **FiftyPercentSurvival** | 55.22% | 5,000 |
| 2 | **Heuristic(1.5)** | 53.32% | 5,000 |
| 3 | **OpportunisticActivation** | 52.78% | 5,000 |
| 4 | **ExpectedValueMax** | 51.26% | 5,000 |
| 5 | **Heuristic(1.0)** | 51.16% | 5,000 |

**Analysis**: GreedyUntil1Col is much more beatable. Conservative probabilistic strategies exploit its high bust rate and position bias.

#### Counters to Heuristic(1.5) (#2 competitive)

| Rank | Strategy | Win Rate vs H(1.5) | Games |
|------|----------|--------------------|-------|
| 1 | **FiftyPercentSurvival** | 54.38% | 5,000 |
| 2 | **OpportunisticActivation** | 50.96% | 5,000 |
| 3 | **Heuristic(1.5)** | 50.00% | 5,000 |
| 4 | **ExpectedValueMax** | 48.38% | 5,000 |
| 5 | **Heuristic(1.0)** | 48.30% | 5,000 |

**Analysis**: Again, FiftyPercentSurvival dominates. Heuristic(1.5) is well-balanced - only slight variations in alpha value come close.

---

## Column Preference Patterns

Top 3 strategies show distinct column preferences:

### FiftyPercentSurvival
- **Most completed**: 8 (42.0%), 7 (38.4%), 6 (37.7%)
- **Most used**: 8 (3.14×), 6 (3.09×), 7 (3.08×)
- **Pattern**: Strong middle preference (6-8), balanced usage

### GreedyUntil1Col
- **Most completed**: 6 (36.8%), 7 (36.4%), 8 (35.2%)
- **Most used**: 7 (1.23×), 6 (1.20×), 8 (1.17×)
- **Pattern**: Completes ONE column quickly, less repeated usage (stops immediately)

### Heuristic(1.5)
- **Most completed**: 12 (42.9%), 2 (41.0%), 6 (39.4%)
- **Most used**: 6 (3.54×), 8 (3.51×), 7 (3.41×)
- **Pattern**: Completes outer columns (2, 12) surprisingly often but still uses middle columns most

**Universal truth**: **Columns 6-8 dominate usage** across all top strategies. These columns have optimal frequency (moderate probability) combined with reasonable length.

---

## Strategy Archetypes Performance

### By Strategy Family

| Family | Best Performer | Win Rate | Avg Turns | Characteristics |
|--------|---------------|----------|-----------|-----------------|
| **Probabilistic** | FiftyPercentSurvival | 69.84% | 11.3 | Math-based, adapts to board state |
| **Heuristic (EV)** | Heuristic(1.5) | 66.46% | 11.9 | Alpha-tuned expected value |
| **Monte Carlo** | MonteCarloLookahead | 63.09% | 12.4 | Simulation-based "perfect" play |
| **Adaptive** | AdaptiveThreshold | 62.21% | 12.5 | Dynamic threshold based on P(success) |
| **Expected Value** | ExpectedValueMax | 62.08% | 12.3 | Pure EV maximization |
| **Opponent-Aware** | OpponentAware(0.7,1,1.5) | 59.92% | 11.8 | Adjusts to relative position |
| **Greedy-Improved** | GreedyImproved2 | 60.23% | 12.6 | Threshold with smart pairing |
| **Column-Focused** | GreedyUntil1Col | 58.90% | 10.5 | One-and-done completion |
| **Conservative** | Conservative(4) | 56.82% | 14.2 | Fixed step threshold |

**Takeaway**: **Probabilistic and Heuristic strategies dominate**. Simple threshold-based strategies lag behind.

---

## Surprising Findings

### 1. MonteCarloLookahead is NOT the best
Despite simulating 100 future rolls before each decision (our "perfect play" baseline), it only achieves 63.09% win rate (#4). This suggests:
- **FiftyPercentSurvival is near-optimal** (beats "perfect play"!)
- OR Monte Carlo sample size (100 rolls) is insufficient
- OR the 50% survival threshold is actually better than pure EV maximization in practice

### 2. Speed ≠ Win Rate
- Fastest strategy (GreedyUntil1Col): 10.5 turns, 58.90% win rate (#11)
- Best strategy (FiftyPercentSurvival): 11.3 turns, 69.84% win rate (#1)
- Only **0.8 turns slower** but **+10.9% win rate**

**Consistency and low bust rate matter more than raw speed.**

### 3. OpponentAware(2,1,0.3) favors Player 2
Being conservative when behind and aggressive when ahead creates a **-4.14% P1 disadvantage**. This counter-intuitive result suggests:
- Playing from behind requires **patience**, not aggression
- Playing from ahead benefits from **pressure**, not caution
- The standard OpponentAware approaches (aggressive when behind) are correct

### 4. Outer columns are underutilized
Heuristic(1.5) completes columns 2 and 12 at 41-43% rate (nearly as often as middle columns), yet most strategies ignore them. This suggests:
- **Columns 2 and 12 may be undervalued**
- Their short length (3 steps) compensates for low frequency
- WeightedColumnValueOuter (strategy #34) may perform better than expected

### 5. First-player advantage is massive
+11.18% overall is **huge** for a modern board game. For comparison:
- Chess: ~5% (white advantage)
- Go: ~7% (black advantage, hence komi)
- Can't Stop: **11.18%** (player 1 advantage)

This suggests Can't Stop could benefit from a handicap system (e.g., Player 2 starts with 1 progress on a column of choice).

---

## Recommendations

### For Competitive Play
1. **Use FiftyPercentSurvival** - highest win rate, balanced first-player advantage
2. **Avoid GreedyUntil1Col** - too position-dependent despite speed
3. **Consider Heuristic(1.5)** - slightly slower but very strong (66.46% win rate)

### For Casual/Fast Games
1. **GreedyUntil1Col** if you don't mind variance and are Player 1
2. **OpponentAware(0.5,1,2)** for balanced speed + adaptability (11.4 turns)

### For Research
1. Investigate **outer column strategies** more deeply
2. Test **handicap systems** to balance first-player advantage
3. Explore **hybrid FiftyPercentSurvival + MonteCarloLookahead** (combine probability threshold with lookahead)
4. Analyze **GreedyFraction strategies** with adjusted thresholds (currently show high P1 bias)

---

## Raw Data Access

All simulation data is available for further analysis:

**Location**: `/home/k1/public/notes/blog/files/20251201/results/`

**Files**:
- `single_player_raw_20251210_145529.jsonl.gz` (658 KB) - 38,000 trials with full game history
- `single_player_stats_20251210_145529.json` (45 KB) - Aggregated statistics
- `head_to_head_raw_20251210_145529.jsonl.gz` (20 MB) - 3.6M games with outcomes
- `head_to_head_stats_20251210_145529.json` (821 KB) - Matchup summaries
- `summary_report_20251210_145529.md` - High-level summary

**Loading the data**:
```python
from data_loader import DataLoader

loader = DataLoader(
    single_player_path='results/single_player_raw_*.jsonl.gz',
    head_to_head_path='results/head_to_head_raw_*.jsonl.gz'
)

# 5 different data views available:
sp = loader.get_single_player()              # 38K rows, one per trial
h2h = loader.get_head_to_head()              # 3.6M rows, one per game
sym = loader.get_head_to_head_symmetric()    # 7.2M rows, both perspectives
summary = loader.get_matchup_summary()        # 1,444 rows, aggregated matchups
stats = loader.get_strategy_overall_stats()  # 38 rows, strategy-level stats
```

See `DATA_FORMATS_GUIDE.md` for full usage examples.

---

## Conclusion

After 3.6 million games and 3.89 hours of computation, **FiftyPercentSurvival emerges as the dominant Can't Stop strategy**, combining near-optimal speed (11.3 turns) with exceptional competitive performance (69.84% win rate). The key to its success: **mathematically sound probability calculations** that adapt to board state, balanced risk tolerance, and consistent performance across positions.

The analysis reveals that **raw speed is overrated** - strategies that bust frequently or depend heavily on turn order underperform in competition. **Consistency, probability-aware decision making, and balanced risk tolerance** define top-tier play.

Perhaps most importantly, we've uncovered a **significant first-player advantage** (+11.18%) that warrants consideration for game balance, and identified severe position bias in popular "greedy" strategies that makes them less viable despite impressive single-player speed.

**The future of Can't Stop AI**: Hybrid approaches combining FiftyPercentSurvival's probability framework with Monte Carlo lookahead may push win rates even higher. We've likely found strategies within 3-5% of optimal play.
