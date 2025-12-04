# Can't Stop Blog Post - Visualizations Summary

## All Charts Created (7 total)

### 1. **two_dice_distribution.png** (144 KB)
- **Type**: Bar chart with gradient colors
- **Purpose**: Show probability distribution for rolling two dice
- **Key insight**: Classic bell curve, 7 is most likely at 16.67%

### 2. **four_dice_distribution.png** (166 KB)
- **Type**: Bar chart with gradient colors
- **Purpose**: Show probability of making each sum with four dice (Can't Stop mechanic)
- **Key insight**: Distribution flattens significantly - 7 jumps to 64.4%

### 3. **expected_rolls_per_column.png** (246 KB)
- **Type**: Line plot with markers and reference bands
- **Purpose**: Show how many rolls needed to complete each column
- **Key insight**: Columns 6-8 are most efficient (~19.6 rolls), columns 2/12 worst (~22.7 rolls)
- **Note**: Uses line plot (not bars) to properly show deviations from baseline

### 4. **all_165_combinations_ranked.png** (477 KB)
- **Type**: Dense lollipop chart showing all combinations
- **Purpose**: Visualize the complete distribution of success rates for all 165 possible three-column combinations
- **Key insights**:
  - 37 "excellent" combinations (≥85%)
  - Median is 79.6%, mean is 77.6%
  - Worst combinations drop to 43.8% (more likely to bust than succeed)
  - Clear color-coded tiers with key combinations labeled
- **Note**: Replaced the top 10 vs bottom 10 comparison to show full scale

### 5. **strategy_tournament_rankings.png** (395 KB)
- **Type**: Lollipop chart with color gradient
- **Purpose**: Show overall win rates for top 14 strategies in tournament
- **Key insight**: GreedyUntil1Col dominates at 81.6%, marked with gold star
- **Note**: Uses lollipop chart (not truncated bars) to maintain proper zero baseline

### 6. **single_player_performance.png** (380 KB)
- **Type**: Lollipop chart with colored zones
- **Purpose**: Show how fast each strategy completes 3 columns solo
- **Key insight**: Best strategies take ~13 turns, worst take 27+ turns
- **Note**: Uses lollipop chart with shaded performance zones

### 7. **tournament_heatmap_full.png** (394 KB)
- **Type**: 25×25 heatmap with diverging color scheme
- **Purpose**: Show head-to-head win rates for all strategy matchups
- **Key insight**: Clear patterns emerge - simple strategies beat complex ones
- **Note**: Includes all 25 strategies as requested

## Design Philosophy

All charts follow consistent styling:
- **Colors**: Professional palette (blues, greens, oranges, reds)
- **Background**: Light (#FAFAFA) for easy web embedding
- **Typography**: Modern sans-serif (Inter/Arial fallback)
- **Resolution**: 250-300 DPI for crisp display
- **Data integrity**: All charts start from zero baseline (using lollipop/line charts where bars would be misleading)

## Data Sources

- `probability_calculations.py` - dice probability calculations
- `column_combinations.py` - all 165 three-column combination analysis
- `column_combinations_all.csv` - complete combination data
- `cant_stop_analysis_extended.py` - 25-strategy tournament simulation
- `tournament_results_full.csv` - complete win rate matrix
- `single_player_results.txt` - solo completion time tests

## Scripts

- `create_all_visualizations.py` - Initial generation of all charts
- `fix_chart_types.py` - Updated charts to use proper zero baselines
- `plot_all_165_from_csv.py` - Dense visualization of all 165 combinations
