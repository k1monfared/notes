# Can't Stop Data Formats - Quick Reference Guide

**Companion to**: `data_loader.py` and `DATA_DOCUMENTATION.md`

---

## Overview

The `data_loader.py` module provides **5 different views** of the simulation data, each optimized for specific types of analysis. This guide explains when to use each format.

---

## The 5 Data Formats

### 1. **Single-Player Format** (`get_single_player()`)

**Use when**: Analyzing individual strategy performance in isolation

**Format**: One row per trial
```python
   strategy  trial  turns_to_1col  turns_to_2col  turns_to_3col  busts  col_2  col_3  ...  completed_7  completed_8
0  Greedy       0              3              7             12      5      0      1  ...         True        True
1  Greedy       1              2              5              9      3      0      0  ...         True        True
```

**Columns**:
- `strategy`: Strategy name
- `trial`: Trial number (0-999)
- `turns_to_1col`, `turns_to_2col`, `turns_to_3col`: Milestone turns
- `busts`: Total busts in this game
- `col_2` through `col_12`: How many times each column was used
- `completed_2` through `completed_12`: Boolean flags for completed columns
- `total_column_usage`: Sum of all column usage
- `num_columns_completed`: Should always be 3 (for wins)

**Best for**:
- ✅ Comparing strategy efficiency (avg turns to win)
- ✅ Analyzing column preferences
- ✅ Studying bust rates
- ✅ Distribution analysis (variance, percentiles)

**Example**:
```python
# Which strategy is fastest?
sp = loader.get_single_player()
fastest = sp.groupby('strategy')['turns_to_3col'].mean().sort_values()
print(fastest.head(10))
```

---

### 2. **Head-to-Head Format** (`get_head_to_head()`)

**Use when**: Analyzing specific matchups with player position mattering

**Format**: One row per game (Player 1 vs Player 2 perspective)
```python
            s1               s2  game  winner  turns  p1_cols  p2_cols  p1_busts  p2_busts  p1_won  p2_won  is_self_play      matchup
0       Greedy  Conservative(3)     0       0     15        3        1         4         2    True   False         False  Greedy vs Conservative(3)
1       Greedy  Conservative(3)     1       1     18        2        3         5         1   False    True         False  Greedy vs Conservative(3)
```

**Columns**:
- `s1`, `s2`: Player 1 and Player 2 strategies
- `game`: Game number within this matchup
- `winner`: 0 (P1 won) or 1 (P2 won)
- `turns`: Game length
- `p1_cols`, `p2_cols`: Columns completed by each player
- `p1_busts`, `p2_busts`: Bust counts
- `p1_won`, `p2_won`: Boolean win flags
- `is_self_play`: True if s1 == s2
- `matchup`: Formatted matchup string
- `matchup_ordered`: Alphabetically ordered (for grouping mirror matchups)
- `game_length_cat`: Categorical (very_short, short, medium, long, very_long)

**Best for**:
- ✅ Analyzing specific matchups (Greedy vs Conservative)
- ✅ Studying first-player advantage
- ✅ Game length analysis by matchup
- ✅ Win rate matrices

**Example**:
```python
# How does Greedy perform as Player 1?
h2h = loader.get_head_to_head()
greedy_as_p1 = h2h[h2h['s1'] == 'Greedy']
win_rate = greedy_as_p1['p1_won'].mean()
print(f"Greedy as P1: {win_rate:.1%} win rate")
```

---

### 3. **Symmetric Head-to-Head Format** (`get_head_to_head_symmetric()`)

**Use when**: Analyzing strategy performance independent of player position

**Format**: TWO rows per game (one from each player's perspective)
```python
   strategy         opponent  game_id    won  player_position  my_cols  opp_cols  my_busts  opp_busts  turns  is_self_play
0    Greedy  Conservative(3)        0   True               P1        3         1         4          2     15         False
1    Conservative(3)       Greedy        0  False               P2        1         3         2          4     15         False
```

**Columns**:
- `strategy`: The strategy being analyzed (changes perspective)
- `opponent`: The opponent strategy
- `game_id`: Original game ID (for joining back to original data)
- `won`: Did THIS strategy win?
- `player_position`: 'P1' or 'P2'
- `my_cols`, `opp_cols`: Columns from this strategy's perspective
- `my_busts`, `opp_busts`: Busts from this strategy's perspective
- `turns`: Game length
- `is_self_play`: Boolean

**Best for**:
- ✅ Overall strategy win rates (ignoring player position)
- ✅ "How does Strategy X perform against all opponents?"
- ✅ First-player advantage calculations
- ✅ Strategy-centric analysis

**Example**:
```python
# Overall win rate for each strategy
symmetric = loader.get_head_to_head_symmetric()
win_rates = symmetric.groupby('strategy')['won'].mean().sort_values(ascending=False)
print(win_rates.head(10))

# First-player advantage
p1_rates = symmetric[symmetric['player_position'] == 'P1'].groupby('strategy')['won'].mean()
p2_rates = symmetric[symmetric['player_position'] == 'P2'].groupby('strategy')['won'].mean()
advantage = (p1_rates - p2_rates).sort_values(ascending=False)
```

---

### 4. **Matchup Summary Format** (`get_matchup_summary()`)

**Use when**: Quick lookup of matchup statistics

**Format**: One row per matchup (s1, s2 pair)
```python
            s1               s2  total_games  p1_wins  p1_win_rate  p2_wins  p2_win_rate  avg_turns  median_turns  std_turns  avg_p1_cols  avg_p2_cols  avg_p1_busts  avg_p2_busts  is_self_play
0       Greedy  Conservative(3)         2500     1450         0.58     1050         0.42       14.3          14.0        3.2          2.8          1.4           3.2           2.1         False
```

**Columns**:
- `s1`, `s2`: Strategies
- `total_games`: Number of games played
- `p1_wins`, `p2_wins`: Win counts
- `p1_win_rate`, `p2_win_rate`: Win rates (should sum to 1.0)
- `avg_turns`, `median_turns`, `std_turns`: Game length statistics
- `avg_p1_cols`, `avg_p2_cols`: Average columns completed
- `avg_p1_busts`, `avg_p2_busts`: Average bust counts
- `is_self_play`: Boolean

**Best for**:
- ✅ Quick matchup lookups
- ✅ Creating win rate matrices
- ✅ Identifying one-sided matchups
- ✅ Statistical comparisons

**Example**:
```python
# Find most one-sided matchups
summary = loader.get_matchup_summary()
summary['dominance'] = (summary['p1_win_rate'] - 0.5).abs()
most_one_sided = summary.sort_values('dominance', ascending=False).head(10)
print(most_one_sided[['s1', 's2', 'p1_win_rate']])
```

---

### 5. **Strategy Overall Stats Format** (`get_strategy_overall_stats()`)

**Use when**: Comparing strategies at a high level

**Format**: One row per strategy (aggregated across all matchups)
```python
     strategy  total_games  total_wins  overall_win_rate  as_p1_games  as_p1_wins  as_p1_win_rate  as_p2_games  as_p2_wins  as_p2_win_rate  first_player_advantage  avg_turns_when_winning  avg_turns_when_losing
0      Greedy        95000       52000              0.55        47500       27000            0.568        47500       25000            0.526                   0.042                    12.3                   18.7
```

**Columns**:
- `strategy`: Strategy name
- `total_games`: Total games played (as P1 + as P2)
- `total_wins`: Total wins
- `overall_win_rate`: Overall win rate
- `as_p1_games`, `as_p1_wins`, `as_p1_win_rate`: Stats as Player 1
- `as_p2_games`, `as_p2_wins`, `as_p2_win_rate`: Stats as Player 2
- `first_player_advantage`: Difference (P1 rate - P2 rate)
- `avg_turns_when_winning`: Average game length in wins
- `avg_turns_when_losing`: Average game length in losses

**Best for**:
- ✅ Strategy rankings
- ✅ Identifying first-player advantage per strategy
- ✅ Overall performance comparison
- ✅ Win/loss pattern analysis

**Example**:
```python
# Top strategies by overall win rate
stats = loader.get_strategy_overall_stats()
top_strategies = stats.sort_values('overall_win_rate', ascending=False)
print(top_strategies[['strategy', 'overall_win_rate', 'first_player_advantage']].head(10))
```

---

## Decision Tree: Which Format to Use?

```
What do you want to analyze?
│
├─ Individual strategy efficiency (no opponents)?
│  └─> Use: get_single_player()
│
├─ Specific matchup (Greedy vs Conservative)?
│  └─> Use: get_head_to_head() filtered by s1 and s2
│
├─ "How well does Strategy X do overall?"
│  └─> Use: get_head_to_head_symmetric() grouped by 'strategy'
│     OR: get_strategy_overall_stats()
│
├─ First-player advantage?
│  ├─ Per strategy: get_strategy_overall_stats()['first_player_advantage']
│  └─ Overall: get_head_to_head_symmetric() grouped by player_position
│
├─ Quick matchup lookup?
│  └─> Use: get_matchup_summary()
│
└─ Win rate matrix / heatmap?
   └─> Use: get_matchup_summary() pivoted on (s1, s2, p1_win_rate)
```

---

## Common Analysis Patterns

### Pattern 1: Self-Play Fairness Check

**Question**: "Does strategy X have balanced self-play?"

```python
from data_loader import DataLoader, analyze_self_play

loader = DataLoader('results/single_player_raw_*.jsonl.gz',
                    'results/head_to_head_raw_*.jsonl.gz')

fairness = analyze_self_play(loader)
print(fairness)

# Output shows deviation from 50% - should be small (<10%)
```

**Uses**: `get_head_to_head()` filtered by `is_self_play == True`

---

### Pattern 2: Find Counter Strategies

**Question**: "What beats Greedy?"

```python
from data_loader import DataLoader, find_counter_strategies

loader = DataLoader('results/single_player_raw_*.jsonl.gz',
                    'results/head_to_head_raw_*.jsonl.gz')

counters = find_counter_strategies(loader, 'Greedy', top_n=10)
print(counters)
```

**Uses**: `get_head_to_head_symmetric()` filtered by `opponent == 'Greedy'`

---

### Pattern 3: Strategy Rankings

**Question**: "Which strategy is best?"

```python
from data_loader import get_strategy_rankings

# By head-to-head performance
h2h_rankings = get_strategy_rankings(loader, by='overall')

# By single-player efficiency
sp_rankings = get_strategy_rankings(loader, by='single_player')

print("Head-to-head rankings:")
print(h2h_rankings.head(10))

print("\nSingle-player rankings:")
print(sp_rankings.head(10))
```

**Uses**:
- `by='overall'`: `get_strategy_overall_stats()`
- `by='single_player'`: `get_single_player()` grouped

---

### Pattern 4: Column Preference Analysis

**Question**: "Which columns does Strategy X prefer?"

```python
loader = DataLoader('results/single_player_raw_*.jsonl.gz',
                    'results/head_to_head_raw_*.jsonl.gz')

sp = loader.get_single_player()
greedy_data = sp[sp['strategy'] == 'Greedy']

# Which columns were completed most?
completion_counts = greedy_data[[f'completed_{i}' for i in range(2, 13)]].sum()
completion_counts.index = range(2, 13)
print(completion_counts.sort_values(ascending=False))

# Which columns were used most (regardless of completion)?
usage_counts = greedy_data[[f'col_{i}' for i in range(2, 13)]].sum()
usage_counts.index = range(2, 13)
print(usage_counts.sort_values(ascending=False))
```

**Uses**: `get_single_player()` with expanded column fields

---

### Pattern 5: First-Player Advantage Analysis

**Question**: "Is there a first-player advantage? How much?"

```python
# Overall advantage
symmetric = loader.get_head_to_head_symmetric()
overall_p1_rate = symmetric[symmetric['player_position'] == 'P1']['won'].mean()
overall_p2_rate = symmetric[symmetric['player_position'] == 'P2']['won'].mean()

print(f"Overall P1 win rate: {overall_p1_rate:.1%}")
print(f"Overall P2 win rate: {overall_p2_rate:.1%}")
print(f"First-player advantage: {overall_p1_rate - overall_p2_rate:.1%}")

# Per-strategy advantage
stats = loader.get_strategy_overall_stats()
print(stats[['strategy', 'first_player_advantage']].sort_values('first_player_advantage', ascending=False))
```

**Uses**: `get_head_to_head_symmetric()` OR `get_strategy_overall_stats()`

---

## Format Comparison Table

| Format | Rows | Columns | Best For | Memory |
|--------|------|---------|----------|--------|
| `single_player` | 38,000 | ~30 | Strategy efficiency, column prefs | Low |
| `head_to_head` | 3.6M | ~15 | Specific matchups, P1/P2 analysis | High |
| `symmetric` | 7.2M | ~11 | Strategy-centric, overall perf | Very High |
| `matchup_summary` | 1,444 | ~15 | Quick lookups, win matrices | Very Low |
| `overall_stats` | 38 | ~15 | Rankings, high-level comparison | Minimal |

**Memory tip**: Load only what you need!
```python
# If only analyzing overall stats, skip loading raw data
stats = loader.get_strategy_overall_stats()  # Loads raw data first time

# For multiple analyses, load once and reuse
loader = DataLoader(sp_path, h2h_path)
sp = loader.get_single_player()      # Cached
h2h = loader.get_head_to_head()      # Cached
symmetric = loader.get_head_to_head_symmetric()  # Uses cached h2h
```

---

## Quick Start Template

```python
from data_loader import DataLoader

# Initialize (use wildcards to auto-find files)
loader = DataLoader(
    single_player_path='results/single_player_raw_*.jsonl.gz',
    head_to_head_path='results/head_to_head_raw_*.jsonl.gz'
)

# Example: Find best strategy
stats = loader.get_strategy_overall_stats()
best = stats.sort_values('overall_win_rate', ascending=False).iloc[0]
print(f"Best strategy: {best['strategy']} ({best['overall_win_rate']:.1%} win rate)")

# Example: Check self-play fairness
from data_loader import analyze_self_play
fairness = analyze_self_play(loader)
unfair = fairness[~fairness['is_fair']]
if len(unfair) > 0:
    print(f"Warning: {len(unfair)} strategies have unfair self-play")
    print(unfair)

# Example: Create win matrix
from data_loader import get_win_matrix
win_matrix = get_win_matrix(loader)
print(win_matrix.head())
```

---

## See Also

- `DATA_DOCUMENTATION.md` - Detailed field definitions and schemas
- `data_loader.py` - Source code with full docstrings
- `BENCHMARK_ESTIMATES.md` - Expected file sizes and timings

---

**Last Updated**: 2025-12-10
