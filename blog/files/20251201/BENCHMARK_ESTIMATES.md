# Can't Stop Strategy Benchmark - Time & Storage Estimates

**Date**: 2025-12-10
**Strategies**: 38 total
**Configuration**: 1,000 single-player trials, 2,500 head-to-head games per matchup

---

## Simulation Time Estimates

### Single-Player Benchmark (1,000 trials per strategy)
- **Average time per strategy**: 6.5 seconds
- **Maximum time per strategy**: 53 seconds (complex probabilistic strategies)
- **Total strategies**: 38
- **Estimated total time**: 4.1 minutes (average) to 33.6 minutes (worst case)

### Head-to-Head Tournament (2,500 games per matchup)
- **Average time per matchup**: 16.3 seconds
- **Maximum time per matchup**: 132.5 seconds
- **Total matchups (38×38)**: 1,444
- **Estimated total time**: 6.6 hours (average) to 53.1 hours (worst case)

### Grand Total
- **Best case estimate**: ~6.6 hours
- **Worst case estimate**: ~53.7 hours
- **Realistic estimate**: ~8-10 hours (accounting for some slow strategies)

---

## Storage Size Estimates

### Raw Data (JSONL Format)

#### Single-Player Raw Data
- **Total trial records**: 38,000 (38 strategies × 1,000 trials)
- **Bytes per record**: ~310 bytes
- **Uncompressed size**: 11.23 MB
- **Compressed (gzip)**: 3.37 MB

#### Head-to-Head Raw Data
- **Total game records**: 3,610,000 (1,444 matchups × 2,500 games)
- **Bytes per record**: ~168 bytes
- **Uncompressed size**: 578.38 MB
- **Compressed (gzip)**: 173.52 MB

### Aggregated Statistics (JSON)
- **Single-player stats**: ~500 KB
- **Head-to-head stats**: ~2 MB
- **Summary report (Markdown)**: ~10 KB

### Total Storage
- **Uncompressed**: 592.62 MB
- **Compressed**: 179.89 MB
- **Aggregates only**: 3-5 MB

---

## Performance Trade-off Analysis

### Re-simulation vs Re-analysis
- **Time to re-run full simulation**: ~6.6 hours ⏱️
- **Time to load & parse compressed raw data**: ~9 seconds ⚡
- **Speed ratio**: Re-simulation is **2,640× slower** than re-analysis

### Recommendation
**✓ Keep all raw data in compressed JSONL format**

Storage is cheap (180 MB), but re-running simulations takes hours. Having raw data enables:
- Custom analysis without re-running
- New metrics computed on demand
- Distribution analysis, percentiles, histograms
- Debugging specific game patterns
- Publication-quality visualizations

---

## Data Loading Time Estimates (for future analysis)

Using compressed JSONL (180 MB):
- **Raw read time**: ~3.6 seconds
- **JSON parsing time**: ~9.0 seconds total
- **Memory required**: ~600 MB (when fully loaded)

Using typical data analysis tools (pandas, R):
```python
# Load single-player data (~3 seconds)
import pandas as pd
sp_data = pd.read_json('single_player_raw.jsonl.gz', lines=True)

# Load head-to-head data (~6 seconds)
h2h_data = pd.read_json('head_to_head_raw.jsonl.gz', lines=True)
```

---

## File Structure

```
results/
├── single_player_stats_YYYYMMDD_HHMMSS.json        # Aggregated statistics
├── single_player_raw_YYYYMMDD_HHMMSS.jsonl.gz      # All 38,000 trials (3.4 MB)
├── head_to_head_stats_YYYYMMDD_HHMMSS.json         # Aggregated matchup results
├── head_to_head_raw_YYYYMMDD_HHMMSS.jsonl.gz       # All 3.6M games (174 MB)
└── summary_report_YYYYMMDD_HHMMSS.md               # Human-readable report
```

---

## Notes

- Estimates based on actual timing data from initial test runs (500 trials, 50 games)
- Actual performance may vary based on:
  - CPU speed and system load
  - Strategy complexity (probabilistic strategies with lookahead are slower)
  - Game length variance
  - I/O performance
- Compression ratio assumes typical JSONL gzip compression (~70% reduction)
- Memory estimates assume Python/pandas for analysis
