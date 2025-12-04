# Can't Stop Blog Post - Final Summary

## Completed Work

### ✅ Content Improvements
1. Added intuitive explanation before inclusion-exclusion calculation
2. Added acknowledgment of incomplete "continuation vs switching" analysis
3. Added comprehensive speed vs win rate analysis section

### ✅ Visualizations Created (9 total)

All charts follow modern design principles with:
- Consistent styling (colors, fonts, backgrounds)
- Proper zero baselines (using lollipop/line charts where appropriate)
- High resolution (250-300 DPI)
- Professional color palette

#### 1. **cant-stop.png** (235 KB)
- Board and dice photo

#### 2. **two_dice_distribution.png** (144 KB)
- Bar chart showing classic 2-dice probability distribution
- Bell curve with 7 at 16.67%

#### 3. **four_dice_distribution.png** (166 KB)
- Bar chart showing flattened 4-dice distribution
- 7 jumps to 64.4%, distribution compresses

#### 4. **expected_rolls_per_column.png** (246 KB)
- Line plot with markers (not truncated bars)
- Shows efficiency differences between columns
- Reference line at 20 rolls, shaded optimal range

#### 5. **all_165_combinations_ranked.png** (477 KB)
- **NEW**: Dense lollipop chart showing ALL 165 combinations
- Color-coded tiers (excellent/good/mediocre/poor)
- Key combinations labeled (best, worst, quartiles)
- Statistics boxes show distribution breakdown
- Replaces the old "top 10 vs bottom 10" comparison

#### 6. **single_player_performance.png** (380 KB)
- Lollipop chart (proper zero baseline)
- Shows completion speed for 14 strategies
- Shaded performance zones

#### 7. **strategy_tournament_rankings.png** (395 KB)
- Lollipop chart (proper zero baseline)
- 14 strategies ranked by tournament win rate
- Gold star marks champion
- 50% reference line

#### 8. **tournament_heatmap_full.png** (394 KB)
- Complete 25×25 win rate matrix
- Diverging color scheme
- All strategies included as requested

#### 9. **speed_vs_winrate_analysis.png** (602 KB)
- **NEW**: Two-panel analysis
- Left: Scatter plot showing speed vs win rate correlation
- Right: Rank comparison showing discrepancies
- Reveals why GreedyUntil1Col wins despite being slower

### 📊 Key Insights Added

**Speed vs Tournament Performance:**
- GreedyUntil1Col wins tournament (81.6%) despite being #9 in speed
- GreedyImproved2 is fastest (13.2 turns) but only #2 in tournament
- Correlation is -0.77 (strong but not perfect)
- **Key finding**: Consistency beats raw speed in head-to-head races

**Why the discrepancy?**
1. Variance matters more in races than averages
2. Busts are retry-able in single-player but instant-loss in tournaments
3. Guaranteed progress (GreedyUntil1Col) beats variable speed

### 📁 All Code Files

**Probability calculations:**
- `probability_calculations.py` - 2-dice and 4-dice probabilities
- `column_combinations.py` - All 165 three-column combinations

**Strategy analysis:**
- `stopping_heuristic.py` - Mathematical stopping rule
- `cant_stop_analysis_extended.py` - Full tournament simulator (25 strategies)
- `analyze_speed_vs_winrate.py` - Speed vs tournament performance

**Visualizations:**
- `create_all_visualizations.py` - Initial chart generation
- `fix_chart_types.py` - Updated to proper zero baselines
- `plot_all_165_from_csv.py` - Dense visualization of all combinations

**Game design:**
- `cant_stop_optimization.py` - Optimal board designs
- `cant_stop_linear_optimization.py` - Linear progression optimization

**Results data:**
- `tournament_results_full.csv` - Complete 25×25 win-rate matrix
- `column_combinations_all.csv` - All 165 combinations analyzed
- `single_player_results.txt` - Independent strategy performance
- `analysis_results_25strategies_2500games.txt` - Full tournament results

### 🎨 Design Principles Applied

1. **Data integrity**: All charts start from zero (using appropriate chart types)
2. **Accessibility**: Professional color palette, high contrast
3. **Consistency**: Unified styling across all visualizations
4. **Clarity**: Dense but readable layouts with selective labeling
5. **Context**: Reference lines, zones, and annotations guide interpretation

## Blog Post Structure

1. ✅ Introduction and game rules
2. ✅ Probability foundations (2-dice vs 4-dice)
3. ✅ Column selection strategy (with complete 165-combo visualization)
4. ✅ Stopping heuristics
5. ✅ Strategy performance analysis
6. ✅ Speed vs win rate deep dive (NEW section)
7. ✅ Tournament results and key findings
8. ✅ Game design balance analysis
9. ✅ Conclusion with all code/data links

## Total Visualizations: 9 charts
## Total Analysis Scripts: 8 Python files
## Total Data Files: 4 CSVs/text files
## Blog Post Length: ~575 lines
