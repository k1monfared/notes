# Can't Stop Simulation - Data Documentation

**Version**: 1.0
**Date**: 2025-12-10
**Purpose**: Complete guide to understanding and analyzing simulation results

---

## Table of Contents

1. [File Overview](#file-overview)
2. [Simulation Scripts](#simulation-scripts)
3. [Result Files](#result-files)
4. [Data Structures](#data-structures)
5. [Python Analysis Guide](#python-analysis-guide)
6. [Common Analysis Patterns](#common-analysis-patterns)

---

## File Overview

### Directory Structure

```
/home/k1/public/notes/blog/files/20251201/
├── Simulation Scripts
│   ├── comprehensive_benchmark_enhanced.py    # Main simulation runner
│   ├── strategies_correct_implementation.py   # All 38 strategy definitions
│   ├── game_simulator.py                      # Game simulation engine
│   ├── main_silent.py                         # Game mechanics (backend copy)
│   └── check_simulation_status.sh             # Status monitoring script
│
├── Documentation
│   ├── DATA_DOCUMENTATION.md                  # This file
│   ├── BENCHMARK_ESTIMATES.md                 # Time/storage estimates
│   └── SIMULATION_SUMMARY.md                  # Running simulation info
│
└── results/                                   # All simulation outputs
    ├── single_player_raw_YYYYMMDD_HHMMSS.jsonl.gz
    ├── single_player_stats_YYYYMMDD_HHMMSS.json
    ├── head_to_head_raw_YYYYMMDD_HHMMSS.jsonl.gz
    ├── head_to_head_stats_YYYYMMDD_HHMMSS.json
    ├── summary_report_YYYYMMDD_HHMMSS.md
    └── SIMULATION_COMPLETE_YYYYMMDD_HHMMSS.txt
```

---

## Simulation Scripts

### 1. `comprehensive_benchmark_enhanced.py`

**Purpose**: Main simulation runner that executes all benchmarks and saves results.

**Key Functions**:
- `run_single_player_benchmark(num_trials)`: Runs solo play simulations
- `run_head_to_head_tournament(games_per_matchup)`: Runs strategy vs strategy games
- `generate_summary_report()`: Creates markdown summary
- `send_completion_notification()`: Creates completion marker

**Configuration**:
```python
num_trials = 1000           # Single-player trials per strategy
games_per_matchup = 2500    # Head-to-head games per matchup
output_dir = "./results"    # Output directory
```

---

### 2. `strategies_correct_implementation.py`

**Purpose**: Defines all 38 Can't Stop strategies.

**Key Classes**:
- `Strategy`: Base class for all strategies
- `ProbabilityCalculator`: Calculates success/bust probabilities
- Various strategy classes (see Groups 1-14)

**Strategy Groups**:
1. Baseline (2): Greedy, Random
2. Conservative (4): Threshold-based stopping
3. Heuristic (5): Mathematical EV-based
4. Opponent-Aware (4): Adjusts based on game state
5. Greedy-Improved (2): Enhanced greedy variants
6. Adaptive (1): Dynamic threshold adjustment
7. Proportional (2): Progress-proportional stopping
8. Column Completion (2): Milestone-based
9. Probabilistic (2): Survival probability-based
10. Column-Count (2): Completion-focused
11. Column Targeting (3): Column preference strategies
12. Runner-Count Aware (2): Optimizes runner count
13. Column-Quality Aware (4): Values certain columns
14. Hybrid/Advanced (3): Multi-factor strategies

---

### 3. `game_simulator.py`

**Purpose**: Game simulation logic (single-player and head-to-head).

**Key Classes**:
- `SinglePlayerSimulator`: Simulates solo column completion
- `GameSimulator`: Simulates two-player games
- `GameResult`: Dataclass for game outcomes

---

### 4. `main_silent.py`

**Purpose**: Core game mechanics (copy from backend repository).

**Key Functions**:
- `roll_dice()`: Roll 4 dice
- `get_all_pairings()`: Get 3 possible pairings from dice
- `is_pairing_valid()`: Check if pairing can be played
- `apply_pairing()`: Apply chosen pairing to game state

**Game Constants**:
```python
COLUMN_LENGTHS = {
    2: 3, 3: 5, 4: 7, 5: 9, 6: 11, 7: 13,
    8: 11, 9: 9, 10: 7, 11: 5, 12: 3
}
```

---

## Result Files

### 1. Single-Player Raw Data (`single_player_raw_*.jsonl.gz`)

**Format**: Compressed JSONL (JSON Lines - one record per line)
**Size**: ~3.4 MB compressed
**Records**: 38,000 (38 strategies × 1,000 trials)

**Structure** (each line is one JSON object):
```json
{
  "strategy": "Greedy",
  "trial": 0,
  "turns_to_1col": 3,
  "turns_to_2col": 7,
  "turns_to_3col": 12,
  "busts": 5,
  "columns_completed": [7, 6, 8],
  "column_usage": {
    "2": 0,
    "3": 1,
    "4": 2,
    "5": 3,
    "6": 5,
    "7": 8,
    "8": 4,
    "9": 2,
    "10": 1,
    "11": 0,
    "12": 0
  }
}
```

**Field Definitions**:

| Field | Type | Description |
|-------|------|-------------|
| `strategy` | string | Strategy name (e.g., "Greedy", "Heuristic(1.0)") |
| `trial` | int | Trial number (0 to 999) |
| `turns_to_1col` | int | Number of turns to complete first column |
| `turns_to_2col` | int | Number of turns to complete second column |
| `turns_to_3col` | int | Number of turns to complete third column (win) |
| `busts` | int | Total number of busts in this game |
| `columns_completed` | list[int] | Which columns were completed (2-12) |
| `column_usage` | dict | How many times each column was progressed |

**Notes**:
- If a milestone wasn't reached, the value equals `max_turns` (500)
- `column_usage` counts every time progress was made on that column
- Columns in `columns_completed` are the final three columns that led to victory

---

### 2. Single-Player Statistics (`single_player_stats_*.json`)

**Format**: JSON
**Size**: ~500 KB
**Structure**: Nested dictionary with aggregated statistics

```json
{
  "Greedy": {
    "turns_to_1col": {
      "avg": 3.2,
      "median": 3.0,
      "stddev": 1.1,
      "min": 1,
      "max": 8,
      "p25": 2.0,
      "p75": 4.0,
      "p90": 5.0
    },
    "turns_to_2col": { /* same structure */ },
    "turns_to_3col": { /* same structure */ },
    "busts": {
      "avg": 4.2,
      "median": 4.0,
      "stddev": 2.1,
      "min": 0,
      "max": 15
    },
    "column_usage": {
      "2": 150,
      "3": 450,
      "4": 1200,
      ...
    },
    "column_completions": {
      "7": 850,
      "6": 720,
      "8": 680,
      ...
    },
    "trials": 1000
  },
  "Conservative(3)": { /* same structure */ },
  ...
}
```

**Field Definitions**:

| Field | Type | Description |
|-------|------|-------------|
| `avg` | float | Arithmetic mean |
| `median` | float | 50th percentile |
| `stddev` | float | Standard deviation |
| `min` | int | Minimum value observed |
| `max` | int | Maximum value observed |
| `p25` | float | 25th percentile |
| `p75` | float | 75th percentile |
| `p90` | float | 90th percentile |
| `column_usage` | dict | Total times each column was used across all trials |
| `column_completions` | dict | Total times each column was completed (won with) |

**Usage Note**: This file contains pre-computed statistics for quick analysis without loading raw data.

---

### 3. Head-to-Head Raw Data (`head_to_head_raw_*.jsonl.gz`)

**Format**: Compressed JSONL
**Size**: ~174 MB compressed
**Records**: 3,610,000 (1,444 matchups × 2,500 games)

**Structure** (each line is one JSON object):
```json
{
  "s1": "Greedy",
  "s2": "Conservative(3)",
  "game": 0,
  "winner": 0,
  "turns": 15,
  "p1_cols": 3,
  "p2_cols": 1,
  "p1_busts": 4,
  "p2_busts": 2
}
```

**Field Definitions**:

| Field | Type | Description |
|-------|------|-------------|
| `s1` | string | Player 1 strategy name |
| `s2` | string | Player 2 strategy name |
| `game` | int | Game number (0 to 2499) |
| `winner` | int | Winner (0 = Player 1, 1 = Player 2) |
| `turns` | int | Total turns in the game |
| `p1_cols` | int | Columns completed by Player 1 |
| `p2_cols` | int | Columns completed by Player 2 |
| `p1_busts` | int | Times Player 1 busted |
| `p2_busts` | int | Times Player 2 busted |

**Important Notes**:
- Player 1 always uses strategy `s1`, Player 2 uses `s2`
- For self-play matchups, `s1 == s2`
- First-player advantage can be analyzed by comparing win rates when a strategy is P1 vs P2

---

### 4. Head-to-Head Statistics (`head_to_head_stats_*.json`)

**Format**: JSON
**Size**: ~2 MB
**Structure**: Nested dictionary (strategy1 → strategy2 → stats)

```json
{
  "Greedy": {
    "Conservative(3)": {
      "p1_wins": 1450,
      "p2_wins": 1050,
      "p1_win_rate": 0.58,
      "turns": {
        "avg": 14.3,
        "median": 14.0,
        "stddev": 3.2,
        "min": 6,
        "max": 45
      },
      "p1_columns": {
        "avg": 2.8,
        "median": 3.0
      },
      "p2_columns": {
        "avg": 1.4,
        "median": 1.0
      },
      "p1_busts": {
        "avg": 3.2,
        "median": 3.0
      },
      "p2_busts": {
        "avg": 2.1,
        "median": 2.0
      },
      "games_played": 2500
    },
    "Heuristic(1.0)": { /* same structure */ },
    ...
  },
  "Conservative(3)": { /* all matchups for this strategy */ },
  ...
}
```

**Field Definitions**:

| Field | Type | Description |
|-------|------|-------------|
| `p1_wins` | int | Number of games won by Player 1 |
| `p2_wins` | int | Number of games won by Player 2 |
| `p1_win_rate` | float | Win rate for Player 1 (0.0 to 1.0) |
| `turns.*` | dict | Game length statistics |
| `p1_columns.*` | dict | Columns completed by P1 statistics |
| `p2_columns.*` | dict | Columns completed by P2 statistics |
| `p1_busts.*` | dict | Bust count for P1 statistics |
| `p2_busts.*` | dict | Bust count for P2 statistics |
| `games_played` | int | Total games in matchup (should be 2500) |

---

### 5. Summary Report (`summary_report_*.md`)

**Format**: Markdown
**Size**: ~10 KB
**Purpose**: Human-readable summary of key findings

**Contains**:
- Top 10 single-player performers (by avg turns to win)
- Top 10 head-to-head performers (by overall win rate)
- Simulation metadata (time, date, parameters)

---

### 6. Completion Marker (`SIMULATION_COMPLETE_*.txt`)

**Format**: Plain text
**Size**: <1 KB
**Purpose**: Signals simulation completion

**Contents**:
```
Simulation completed at: 2025-12-10 15:30:45
Total time: 7.2 hours
Timestamp: 20251210_153045
```

---

## Data Structures

### Column Number Mapping

Columns 2-12 represent different sums on two dice:

| Column | Dice Combinations | Probability | Length |
|--------|-------------------|-------------|--------|
| 2 | (1,1) | 1/36 | 3 |
| 3 | (1,2), (2,1) | 2/36 | 5 |
| 4 | (1,3), (2,2), (3,1) | 3/36 | 7 |
| 5 | (1,4), (2,3), (3,2), (4,1) | 4/36 | 9 |
| 6 | (1,5), (2,4), (3,3), (4,2), (5,1) | 5/36 | 11 |
| 7 | (1,6), (2,5), (3,4), (4,3), (5,2), (6,1) | 6/36 | 13 |
| 8 | (2,6), (3,5), (4,4), (5,3), (6,2) | 5/36 | 11 |
| 9 | (3,6), (4,5), (5,4), (6,3) | 4/36 | 9 |
| 10 | (4,6), (5,5), (6,4) | 3/36 | 7 |
| 11 | (5,6), (6,5) | 2/36 | 5 |
| 12 | (6,6) | 1/36 | 3 |

**Note**: Column 7 is most common (16.7% probability), columns 2 and 12 are rarest (2.8%).

---

### Strategy Name Patterns

Strategies follow naming conventions:

| Pattern | Example | Parameters |
|---------|---------|------------|
| `Simple` | `Greedy` | None |
| `WithParam(x)` | `Conservative(3)` | Single threshold |
| `WithFloat(x)` | `Heuristic(1.0)` | Risk tolerance |
| `WithMulti(x,y,z)` | `OpponentAware(0.3,1,2)` | Behind, tied, ahead alphas |
| `Descriptive` | `GreedyUntil1Col` | None |

---

## Python Analysis Guide

### Loading Data

#### Example 1: Load Single-Player Raw Data

```python
import pandas as pd
import gzip
import json

# Method 1: Using pandas (easiest)
sp_raw = pd.read_json('results/single_player_raw_20251210_153045.jsonl.gz',
                      lines=True,
                      compression='gzip')

print(f"Loaded {len(sp_raw)} trials")
print(sp_raw.head())

# Method 2: Manual parsing (more control)
trials = []
with gzip.open('results/single_player_raw_20251210_153045.jsonl.gz', 'rt') as f:
    for line in f:
        trials.append(json.loads(line))

df = pd.DataFrame(trials)
```

**Output Schema**:
```
   strategy  trial  turns_to_1col  turns_to_2col  turns_to_3col  busts  columns_completed  column_usage
0  Greedy       0              3              7             12      5        [7, 6, 8]     {'2': 0, '3': 1, ...}
1  Greedy       1              2              5              9      3        [7, 8, 9]     {'2': 0, '3': 0, ...}
```

---

#### Example 2: Load Head-to-Head Raw Data

```python
import pandas as pd

# Load compressed JSONL
h2h_raw = pd.read_json('results/head_to_head_raw_20251210_153045.jsonl.gz',
                       lines=True,
                       compression='gzip')

print(f"Loaded {len(h2h_raw)} games")
print(h2h_raw.head())

# Filter to specific matchup
greedy_vs_conservative = h2h_raw[
    (h2h_raw['s1'] == 'Greedy') &
    (h2h_raw['s2'] == 'Conservative(3)')
]
```

**Output Schema**:
```
              s1               s2  game  winner  turns  p1_cols  p2_cols  p1_busts  p2_busts
0         Greedy  Conservative(3)     0       0     15        3        1         4         2
1         Greedy  Conservative(3)     1       1     18        2        3         5         1
```

---

#### Example 3: Load Aggregated Statistics

```python
import json

# Load single-player stats
with open('results/single_player_stats_20251210_153045.json', 'r') as f:
    sp_stats = json.load(f)

# Access a specific strategy
greedy_stats = sp_stats['Greedy']
print(f"Average turns to win: {greedy_stats['turns_to_3col']['avg']:.1f}")
print(f"Median busts: {greedy_stats['busts']['median']:.0f}")
print(f"90th percentile turns: {greedy_stats['turns_to_3col']['p90']:.0f}")

# Load head-to-head stats
with open('results/head_to_head_stats_20251210_153045.json', 'r') as f:
    h2h_stats = json.load(f)

# Access specific matchup
matchup = h2h_stats['Greedy']['Conservative(3)']
print(f"Win rate: {matchup['p1_win_rate']:.1%}")
```

---

### Common Data Transformations

#### Expand column_usage Dictionary

```python
# Single-player data has column_usage as a dict in each row
# Expand it into separate columns

import pandas as pd

sp_raw = pd.read_json('results/single_player_raw_20251210_153045.jsonl.gz',
                      lines=True, compression='gzip')

# Extract column usage into separate columns
column_usage_df = pd.json_normalize(sp_raw['column_usage'])
column_usage_df.columns = [f'col_{c}' for c in column_usage_df.columns]

# Combine with original data
sp_expanded = pd.concat([sp_raw.drop('column_usage', axis=1), column_usage_df], axis=1)

print(sp_expanded.columns)
# ['strategy', 'trial', 'turns_to_1col', ..., 'col_2', 'col_3', ..., 'col_12']
```

---

#### Calculate Win Matrix

```python
import pandas as pd
import numpy as np

h2h_stats = json.load(open('results/head_to_head_stats_20251210_153045.json'))

# Get list of all strategies
strategies = sorted(h2h_stats.keys())

# Create win rate matrix
win_matrix = np.zeros((len(strategies), len(strategies)))

for i, s1 in enumerate(strategies):
    for j, s2 in enumerate(strategies):
        win_matrix[i, j] = h2h_stats[s1][s2]['p1_win_rate']

# Convert to DataFrame for easy viewing
win_df = pd.DataFrame(win_matrix, index=strategies, columns=strategies)

print(win_df.head())
```

---

## Common Analysis Patterns

### 1. Find Best Single-Player Strategy

```python
import pandas as pd
import json

# Load stats
with open('results/single_player_stats_20251210_153045.json') as f:
    stats = json.load(f)

# Extract average turns to win for each strategy
results = []
for strategy, data in stats.items():
    results.append({
        'strategy': strategy,
        'avg_turns': data['turns_to_3col']['avg'],
        'median_turns': data['turns_to_3col']['median'],
        'avg_busts': data['busts']['avg']
    })

df = pd.DataFrame(results).sort_values('avg_turns')
print("Top 10 strategies:")
print(df.head(10))
```

---

### 2. Analyze Column Preferences

```python
import pandas as pd
import matplotlib.pyplot as plt

sp_raw = pd.read_json('results/single_player_raw_20251210_153045.jsonl.gz',
                      lines=True, compression='gzip')

# Which columns does "Greedy" prefer to complete?
greedy_data = sp_raw[sp_raw['strategy'] == 'Greedy']

# Count frequency of each column being completed
from collections import Counter
all_columns = []
for cols in greedy_data['columns_completed']:
    all_columns.extend(cols)

column_freq = Counter(all_columns)

# Plot
plt.bar(column_freq.keys(), column_freq.values())
plt.xlabel('Column')
plt.ylabel('Times Completed')
plt.title('Column Completion Frequency - Greedy Strategy')
plt.savefig('greedy_column_preferences.png')
```

---

### 3. Head-to-Head Performance Matrix

```python
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import json

# Load head-to-head stats
with open('results/head_to_head_stats_20251210_153045.json') as f:
    h2h = json.load(f)

strategies = sorted(h2h.keys())

# Build win rate matrix
win_rates = []
for s1 in strategies:
    row = []
    for s2 in strategies:
        row.append(h2h[s1][s2]['p1_win_rate'])
    win_rates.append(row)

df = pd.DataFrame(win_rates, index=strategies, columns=strategies)

# Create heatmap
plt.figure(figsize=(15, 15))
sns.heatmap(df, annot=False, cmap='RdYlGn', center=0.5, vmin=0, vmax=1,
            xticklabels=True, yticklabels=True)
plt.title('Head-to-Head Win Rate Matrix')
plt.xlabel('Opponent (Player 2)')
plt.ylabel('Strategy (Player 1)')
plt.tight_layout()
plt.savefig('h2h_heatmap.png', dpi=150)
```

---

### 4. Identify Dominant Strategy

```python
import pandas as pd
import json

with open('results/head_to_head_stats_20251210_153045.json') as f:
    h2h = json.load(f)

# Calculate overall win rate for each strategy
overall_wins = {}

for s1, matchups in h2h.items():
    total_wins = sum(m['p1_wins'] for m in matchups.values())
    total_games = sum(m['games_played'] for m in matchups.values())
    overall_wins[s1] = total_wins / total_games

# Sort by win rate
sorted_strategies = sorted(overall_wins.items(), key=lambda x: x[1], reverse=True)

print("Overall Head-to-Head Rankings:")
for rank, (strategy, win_rate) in enumerate(sorted_strategies, 1):
    print(f"{rank:2d}. {strategy:30s} {win_rate:.1%}")
```

---

### 5. Compare Strategy Variability

```python
import pandas as pd
import json

with open('results/single_player_stats_20251210_153045.json') as f:
    stats = json.load(f)

# Analyze consistency (low stddev = more consistent)
consistency = []
for strategy, data in stats.items():
    consistency.append({
        'strategy': strategy,
        'avg_turns': data['turns_to_3col']['avg'],
        'stddev': data['turns_to_3col']['stddev'],
        'coefficient_of_variation': data['turns_to_3col']['stddev'] / data['turns_to_3col']['avg']
    })

df = pd.DataFrame(consistency).sort_values('coefficient_of_variation')

print("Most Consistent Strategies (low variation):")
print(df.head(10))

print("\nMost Volatile Strategies (high variation):")
print(df.tail(10))
```

---

### 6. Detect First-Player Advantage

```python
import pandas as pd
import json

with open('results/head_to_head_stats_20251210_153045.json') as f:
    h2h = json.load(f)

# For each strategy, compare performance as P1 vs P2
first_player_advantage = []

for strategy in sorted(h2h.keys()):
    # When this strategy is Player 1
    p1_wins = sum(h2h[strategy][opp]['p1_wins'] for opp in h2h[strategy].keys())
    p1_games = sum(h2h[strategy][opp]['games_played'] for opp in h2h[strategy].keys())
    p1_rate = p1_wins / p1_games

    # When this strategy is Player 2 (reversed matchup)
    p2_wins = sum(h2h[opp][strategy]['p2_wins'] for opp in h2h.keys())
    p2_games = sum(h2h[opp][strategy]['games_played'] for opp in h2h.keys())
    p2_rate = p2_wins / p2_games

    first_player_advantage.append({
        'strategy': strategy,
        'as_p1': p1_rate,
        'as_p2': p2_rate,
        'advantage': p1_rate - p2_rate
    })

df = pd.DataFrame(first_player_advantage).sort_values('advantage', ascending=False)

print("Strategies that benefit most from going first:")
print(df.head())

print("\nStrategies that perform better going second:")
print(df.tail())

print(f"\nOverall first-player advantage: {df['advantage'].mean():.1%}")
```

---

## Advanced Topics

### Memory-Efficient Processing

For very large datasets, you can process JSONL files line-by-line:

```python
import gzip
import json

def process_large_file(filename):
    """Process JSONL.gz file without loading everything into memory."""

    strategy_stats = {}

    with gzip.open(filename, 'rt') as f:
        for line in f:
            record = json.loads(line)
            strategy = record['strategy']

            if strategy not in strategy_stats:
                strategy_stats[strategy] = {'turns': [], 'busts': []}

            strategy_stats[strategy]['turns'].append(record['turns_to_3col'])
            strategy_stats[strategy]['busts'].append(record['busts'])

    return strategy_stats

# Process without loading all data
stats = process_large_file('results/single_player_raw_20251210_153045.jsonl.gz')
```

---

### Parallel Processing with Dask

For very large analyses, use Dask for parallel processing:

```python
import dask.dataframe as dd

# Load with Dask (lazy evaluation)
h2h_raw = dd.read_json('results/head_to_head_raw_*.jsonl.gz',
                       lines=True,
                       compression='gzip',
                       blocksize='50MB')

# Compute statistics in parallel
win_rates = h2h_raw.groupby(['s1', 's2'])['winner'].mean().compute()
```

---

## Data Quality Checks

### Verify Data Integrity

```python
import pandas as pd
import json

# Check single-player data
sp_raw = pd.read_json('results/single_player_raw_20251210_153045.jsonl.gz',
                      lines=True, compression='gzip')

print("Single-Player Data Quality:")
print(f"  Total records: {len(sp_raw)}")
print(f"  Expected: 38,000 (38 strategies × 1,000 trials)")
print(f"  Unique strategies: {sp_raw['strategy'].nunique()}")
print(f"  Trials per strategy: {sp_raw.groupby('strategy').size().describe()}")
print(f"  Missing values: {sp_raw.isnull().sum().sum()}")

# Check head-to-head data
h2h_raw = pd.read_json('results/head_to_head_raw_20251210_153045.jsonl.gz',
                       lines=True, compression='gzip')

print("\nHead-to-Head Data Quality:")
print(f"  Total records: {len(h2h_raw)}")
print(f"  Expected: 3,610,000 (1,444 matchups × 2,500 games)")
print(f"  Unique matchups: {h2h_raw.groupby(['s1', 's2']).ngroups}")
print(f"  Expected matchups: 1,444 (38 × 38)")
print(f"  Games per matchup: {h2h_raw.groupby(['s1', 's2']).size().describe()}")

# Verify self-play symmetry
for strategy in sp_raw['strategy'].unique():
    self_play = h2h_raw[(h2h_raw['s1'] == strategy) & (h2h_raw['s2'] == strategy)]
    p1_wins = (self_play['winner'] == 0).sum()
    p2_wins = (self_play['winner'] == 1).sum()
    win_rate = p1_wins / len(self_play)
    deviation = abs(win_rate - 0.5)

    if deviation > 0.1:  # More than 10% deviation
        print(f"⚠ {strategy}: self-play win rate = {win_rate:.1%} (expected ~50%)")
```

---

## Questions?

If you encounter issues or need specific analysis examples not covered here:

1. Check `SIMULATION_SUMMARY.md` for simulation status
2. Review `BENCHMARK_ESTIMATES.md` for expected file sizes
3. Verify data integrity using quality checks above
4. Ensure file timestamps match your simulation run

---

**Last Updated**: 2025-12-10
**Documentation Version**: 1.0
