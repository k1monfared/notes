#!/usr/bin/env python3
"""
Analyze the relationship between single-player speed and tournament win rate.
Find strategies where these metrics don't align.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Single-player performance (avg turns to complete 3 columns)
single_player = {
    'GreedyImproved2': 13.2,
    'GreedyFraction(0.33)': 13.2,
    'GreedyImproved1': 14.2,
    'AdaptiveThreshold': 14.1,
    'Conservative(4)': 15.0,
    'GreedyFraction(0.5)': 15.3,
    'FiftyPercentSurvival': 15.9,
    'Heuristic(1.0)': 16.0,
    'GreedyUntil1Col': 16.3,
    'ExpectedValueMax': 17.3,
    'Conservative(3)': 19.7,
    'Heuristic(1.5)': 22.3,
    'GreedyUntil3Col': 23.8,
    'Random(0.3)': 26.9,
}

# Tournament win rates (%)
tournament_winrate = {
    'GreedyUntil1Col': 81.6,
    'GreedyImproved2': 78.1,
    'GreedyFraction(0.33)': 76.9,
    'GreedyImproved1': 75.7,
    'AdaptiveThreshold': 73.1,
    'Conservative(4)': 71.1,
    'GreedyFraction(0.5)': 67.9,
    'FiftyPercentSurvival': 66.7,
    'Conservative(3)': 65.7,
    'Heuristic(1.0)': 62.1,
    'ExpectedValueMax': 56.8,
    'Random(0.3)': 56.5,
    'GreedyUntil3Col': 50.9,
}

# Combine into dataframe
data = []
for strategy in set(single_player.keys()) & set(tournament_winrate.keys()):
    data.append({
        'Strategy': strategy,
        'Avg_Turns': single_player[strategy],
        'Win_Rate': tournament_winrate[strategy],
        'Speed_Rank': None,  # Will fill these
        'WinRate_Rank': None,
    })

df = pd.DataFrame(data)

# Calculate ranks (1 = best)
df['Speed_Rank'] = df['Avg_Turns'].rank(method='min').astype(int)
df['WinRate_Rank'] = df['Win_Rate'].rank(method='min', ascending=False).astype(int)
df['Rank_Diff'] = df['Speed_Rank'] - df['WinRate_Rank']

# Sort by tournament win rate
df = df.sort_values('Win_Rate', ascending=False)

print("="*80)
print("SINGLE-PLAYER SPEED vs TOURNAMENT WIN RATE ANALYSIS")
print("="*80)
print("\nComplete Comparison:")
print("-"*80)
print(f"{'Strategy':<25} {'Turns':>6} {'Speed':>5} {'WinRate':>7} {'WR':>4} {'Diff':>5}")
print(f"{'':25} {'(avg)':>6} {'Rank':>5} {'(%)':>7} {'Rank':>4} {'':>5}")
print("-"*80)

for _, row in df.iterrows():
    diff_str = f"{row['Rank_Diff']:+d}"
    print(f"{row['Strategy']:<25} {row['Avg_Turns']:>6.1f} {row['Speed_Rank']:>5d} "
          f"{row['Win_Rate']:>6.1f}% {row['WinRate_Rank']:>4d} {diff_str:>5}")

print("\n" + "="*80)
print("KEY FINDINGS")
print("="*80)

# Biggest positive difference (faster than win rate suggests)
fastest_but_not_winning = df.nlargest(3, 'Rank_Diff')
print("\n1. SURPRISINGLY LOW WIN RATES (Fast but don't win as much):")
print("-"*80)
for _, row in fastest_but_not_winning.iterrows():
    print(f"   {row['Strategy']}: Speed rank #{row['Speed_Rank']} but win rate rank #{row['WinRate_Rank']}")
    print(f"      → Completes in {row['Avg_Turns']:.1f} turns but only wins {row['Win_Rate']:.1f}% of games")

# Biggest negative difference (slower but winning more)
slower_but_winning = df.nsmallest(3, 'Rank_Diff')
print("\n2. SURPRISINGLY HIGH WIN RATES (Slower but win more):")
print("-"*80)
for _, row in slower_but_winning.iterrows():
    print(f"   {row['Strategy']}: Speed rank #{row['Speed_Rank']} but win rate rank #{row['WinRate_Rank']}")
    print(f"      → Takes {row['Avg_Turns']:.1f} turns but wins {row['Win_Rate']:.1f}% of games")

print("\n3. CORRELATION ANALYSIS:")
print("-"*80)
correlation = df['Avg_Turns'].corr(df['Win_Rate'])
print(f"   Correlation (turns vs win rate): {correlation:.3f}")
if correlation < -0.5:
    print("   → Strong negative correlation (faster = more wins)")
elif correlation < -0.3:
    print("   → Moderate negative correlation")
else:
    print("   → Weak correlation (speed doesn't predict wins well!)")

print("\n4. EXPECTED vs ACTUAL WINNER:")
print("-"*80)
fastest = df.nsmallest(1, 'Avg_Turns').iloc[0]
actual_winner = df.nlargest(1, 'Win_Rate').iloc[0]
print(f"   Fastest strategy: {fastest['Strategy']} ({fastest['Avg_Turns']:.1f} turns)")
print(f"   → Tournament rank: #{fastest['WinRate_Rank']} ({fastest['Win_Rate']:.1f}% win rate)")
print(f"\n   Actual winner: {actual_winner['Strategy']} ({actual_winner['Win_Rate']:.1f}% win rate)")
print(f"   → Single-player rank: #{actual_winner['Speed_Rank']} ({actual_winner['Avg_Turns']:.1f} turns)")

if fastest['Strategy'] != actual_winner['Strategy']:
    print(f"\n   ⚠️  The fastest strategy is NOT the tournament winner!")
    print(f"   ⚠️  {actual_winner['Strategy']} is {actual_winner['Avg_Turns'] - fastest['Avg_Turns']:.1f} turns slower")
    print(f"   ⚠️  but wins {actual_winner['Win_Rate'] - fastest['Win_Rate']:.1f}pp more games!")

print("\n" + "="*80)
print("INTERPRETATION")
print("="*80)
print("""
Single-player speed measures "how fast can you finish in a vacuum" - it ignores
the opponent entirely. But Can't Stop is a competitive race, not a solo speedrun.

Key factors that make tournament results differ from single-player speed:

1. **Variance/Consistency**: A strategy that averages 13 turns might take 8-20 turns
   per game (high variance), while one that averages 16 turns might always take
   14-18 turns (low variance). In a race, consistency can beat raw speed.

2. **Bust rates**: Aggressive strategies complete quickly WHEN they succeed, but
   bust more often. Single-player metrics average over all attempts; tournaments
   care about head-to-head races where busting loses immediately.

3. **Racing dynamics**: In a race, opponent progress matters. If your opponent
   is ahead, you need to take risks. If you're ahead, you can play conservative.
   Single-player speed doesn't capture this.

4. **Column contention**: When both players want the same columns, the forced-move
   rule creates interference. Single-player speed assumes you always get your
   preferred columns.
""")

print("\n" + "="*80)

# Create visualization
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Inter', 'Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 10,
    'figure.facecolor': '#FAFAFA',
    'axes.facecolor': '#FFFFFF',
})

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

# Plot 1: Scatter plot
colors = ['#FFD700' if s == 'GreedyUntil1Col' else '#2E86AB' for s in df['Strategy']]
sizes = [300 if s == 'GreedyUntil1Col' else 150 for s in df['Strategy']]

ax1.scatter(df['Avg_Turns'], df['Win_Rate'], c=colors, s=sizes, alpha=0.7, edgecolor='#333', linewidth=2)

# Label interesting points
for _, row in df.iterrows():
    if abs(row['Rank_Diff']) >= 3 or row['Strategy'] in ['GreedyUntil1Col', 'GreedyImproved2', 'GreedyUntil3Col']:
        ax1.annotate(row['Strategy'],
                     xy=(row['Avg_Turns'], row['Win_Rate']),
                     xytext=(5, 5), textcoords='offset points',
                     fontsize=8, alpha=0.8)

ax1.set_xlabel('Average Turns to Complete (Single-Player)', fontsize=12, fontweight='600')
ax1.set_ylabel('Tournament Win Rate (%)', fontsize=12, fontweight='600')
ax1.set_title('Speed vs Win Rate: Why the Fastest Strategy Doesn\'t Always Win',
              fontsize=13, fontweight='700', pad=15)
ax1.grid(alpha=0.3)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

# Add trendline
z = np.polyfit(df['Avg_Turns'], df['Win_Rate'], 1)
p = np.poly1d(z)
x_trend = np.linspace(df['Avg_Turns'].min(), df['Avg_Turns'].max(), 100)
ax1.plot(x_trend, p(x_trend), '--', color='#999', linewidth=2, alpha=0.5, label=f'Trend (r={correlation:.2f})')
ax1.legend()

# Plot 2: Rank comparison
df_sorted = df.sort_values('WinRate_Rank')
strategies = df_sorted['Strategy'].tolist()
speed_ranks = df_sorted['Speed_Rank'].tolist()
winrate_ranks = df_sorted['WinRate_Rank'].tolist()

y_pos = range(len(strategies))

ax2.scatter(speed_ranks, y_pos, s=100, color='#F18F01', alpha=0.7, label='Speed Rank', zorder=3)
ax2.scatter(winrate_ranks, y_pos, s=100, color='#06A77D', alpha=0.7, label='Win Rate Rank', zorder=3)

# Draw lines connecting ranks
for i, (speed_r, win_r) in enumerate(zip(speed_ranks, winrate_ranks)):
    color = '#C73E1D' if abs(speed_r - win_r) >= 4 else '#CCCCCC'
    linewidth = 2 if abs(speed_r - win_r) >= 4 else 1
    ax2.plot([speed_r, win_r], [i, i], color=color, alpha=0.5, linewidth=linewidth, zorder=2)

ax2.set_yticks(y_pos)
ax2.set_yticklabels(strategies, fontsize=9)
ax2.set_xlabel('Rank (1 = Best)', fontsize=12, fontweight='600')
ax2.set_title('Rank Comparison: Speed vs Tournament Performance',
              fontsize=13, fontweight='700', pad=15)
ax2.invert_xaxis()
ax2.invert_yaxis()
ax2.grid(alpha=0.3, axis='x')
ax2.legend(loc='lower right')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('speed_vs_winrate_analysis.png', dpi=300, bbox_inches='tight', facecolor='#FAFAFA')
print(f"\n✓ Visualization saved: speed_vs_winrate_analysis.png")
