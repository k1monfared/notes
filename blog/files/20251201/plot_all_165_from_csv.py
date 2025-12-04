#!/usr/bin/env python3
"""
Create a dense visualization of all 165 column combinations from CSV data.
Shows the full distribution without individual labels for readability.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

# Set modern style parameters
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Inter', 'Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'figure.facecolor': '#FAFAFA',
    'axes.facecolor': '#FFFFFF',
    'axes.edgecolor': '#CCCCCC',
    'axes.linewidth': 1.2,
    'grid.alpha': 0.3,
    'grid.linestyle': '--',
    'grid.linewidth': 0.8,
})

def save_fig(fig, filename, dpi=300):
    """Save figure with consistent settings."""
    filepath = Path(__file__).parent / filename
    fig.savefig(filepath, dpi=dpi, bbox_inches='tight', facecolor='#FAFAFA')
    print(f"✓ Generated: {filename}")
    plt.close(fig)


# Read data from CSV
csv_path = Path(__file__).parent / 'column_combinations_all.csv'
df = pd.read_csv(csv_path)

# Sort by success probability (already sorted, but just to be sure)
df = df.sort_values('Success_Prob', ascending=False).reset_index(drop=True)

combos = df['Columns'].tolist()
success_rates = (df['Success_Prob'] * 100).tolist()

# Create figure
fig, ax = plt.subplots(figsize=(14, 22))

# Color based on success rate
colors = []
for sr in success_rates:
    if sr >= 85:
        colors.append('#06A77D')  # Green - excellent
    elif sr >= 75:
        colors.append('#2E86AB')  # Blue - good
    elif sr >= 65:
        colors.append('#F18F01')  # Orange - mediocre
    else:
        colors.append('#C73E1D')  # Red - poor

# Create lollipop chart
positions = range(len(combos))

# Draw lines from 0
for i, (val, color) in enumerate(zip(success_rates, colors)):
    ax.plot([0, val], [i, i], color=color, linewidth=1.2, alpha=0.5)

# Draw dots
ax.scatter(success_rates, positions, s=25, c=colors, alpha=0.85,
           edgecolor='none', zorder=3)

# Only label key combinations
labels_to_show = [
    (0, combos[0], success_rates[0], 'Best'),  # Best
    (20, combos[20], success_rates[20], ''),  # Top 20
    (41, combos[41], success_rates[41], '25th'),  # 25th percentile
    (82, combos[82], success_rates[82], 'Median'),  # Median
    (123, combos[123], success_rates[123], '75th'),  # 75th percentile
    (144, combos[144], success_rates[144], ''),  # Bottom 20
    (164, combos[164], success_rates[164], 'Worst'),  # Worst
]

for idx, combo, sr, label in labels_to_show:
    label_text = f'{combo}\n{sr:.1f}%'
    if label:
        label_text = f'{label}: {label_text}'

    ax.annotate(label_text,
                xy=(sr, idx),
                xytext=(10, 0),
                textcoords='offset points',
                fontsize=7.5,
                fontweight='600',
                va='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                         edgecolor=colors[idx], linewidth=1.5, alpha=0.95),
                zorder=10)

# Add horizontal divider lines
tier_boundaries = []
for i, sr in enumerate(success_rates):
    if i > 0:
        prev_sr = success_rates[i-1]
        if (prev_sr >= 85 and sr < 85) or (prev_sr >= 75 and sr < 75) or (prev_sr >= 65 and sr < 65):
            tier_boundaries.append(i - 0.5)
            ax.axhline(y=i-0.5, color='#CCCCCC', linestyle='-', linewidth=1.5, alpha=0.4, zorder=2)

# Reference lines
ax.axvline(x=50, color='#999999', linestyle=':', linewidth=2, alpha=0.4,
           label='50% (coin flip)', zorder=1)
ax.axvline(x=75, color='#666666', linestyle='--', linewidth=1.5, alpha=0.5,
           label='75% threshold', zorder=1)
ax.axvline(x=85, color='#333333', linestyle='--', linewidth=1.5, alpha=0.5,
           label='85% threshold', zorder=1)

# Styling
ax.set_xlabel('Success Rate (%)', fontsize=14, fontweight='600', color='#333333')
ax.set_ylabel('Rank (1 = Best, 165 = Worst)', fontsize=14, fontweight='600', color='#333333')
ax.set_title('All 165 Three-Column Combinations Ranked by Success Rate',
             fontsize=17, fontweight='700', pad=25, color='#1a1a1a')
ax.set_xlim(0, 100)
ax.set_ylim(-3, len(combos) + 3)
ax.grid(axis='x', alpha=0.3)
ax.invert_yaxis()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.set_yticks([0, 41, 82, 123, 164])
ax.set_yticklabels(['#1', '#42', '#83', '#124', '#165'], fontsize=10, color='#666666')

# Add color legend
legend_elements = [
    plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#06A77D',
               markersize=10, label='Excellent (≥85%)', markeredgewidth=0),
    plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#2E86AB',
               markersize=10, label='Good (75-85%)', markeredgewidth=0),
    plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#F18F01',
               markersize=10, label='Mediocre (65-75%)', markeredgewidth=0),
    plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#C73E1D',
               markersize=10, label='Poor (<65%)', markeredgewidth=0),
]

legend1 = ax.legend(handles=legend_elements, loc='lower right',
                    frameon=True, fancybox=True, shadow=True, title='Success Tiers',
                    fontsize=9, title_fontsize=10)

# Add second legend for reference lines
ax.add_artist(legend1)
ax.legend(loc='upper right', frameon=True, fancybox=True, shadow=True, fontsize=9)

# Add statistics box
stats_text = (
    f'Range: {min(success_rates):.1f}% – {max(success_rates):.1f}%\n'
    f'Spread: {max(success_rates) - min(success_rates):.1f} pp\n'
    f'Median: {success_rates[82]:.1f}%\n'
    f'Mean: {np.mean(success_rates):.1f}%'
)

ax.text(0.02, 0.02, stats_text,
        transform=ax.transAxes, fontsize=9, verticalalignment='bottom',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#FFF8DC',
                 edgecolor='#CCCCCC', linewidth=1.5, alpha=0.9))

# Add tier counts
tier_counts_text = (
    f'Excellent: {sum(1 for sr in success_rates if sr >= 85)} combos\n'
    f'Good: {sum(1 for sr in success_rates if 75 <= sr < 85)} combos\n'
    f'Mediocre: {sum(1 for sr in success_rates if 65 <= sr < 75)} combos\n'
    f'Poor: {sum(1 for sr in success_rates if sr < 65)} combos'
)

ax.text(0.98, 0.02, tier_counts_text,
        transform=ax.transAxes, fontsize=9, verticalalignment='bottom',
        horizontalalignment='right',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#F0F8FF',
                 edgecolor='#CCCCCC', linewidth=1.5, alpha=0.9))

plt.tight_layout()
save_fig(fig, 'all_165_combinations_ranked.png', dpi=250)

print(f"\nStatistics:")
print(f"  Total combinations: {len(combos)}")
print(f"  Best: {combos[0]} at {success_rates[0]:.1f}%")
print(f"  Worst: {combos[-1]} at {success_rates[-1]:.1f}%")
print(f"  Median: {success_rates[82]:.1f}%")
print(f"  Mean: {np.mean(success_rates):.1f}%")
print(f"  Excellent (≥85%): {sum(1 for sr in success_rates if sr >= 85)}")
print(f"  Good (75-85%): {sum(1 for sr in success_rates if 75 <= sr < 85)}")
print(f"  Mediocre (65-75%): {sum(1 for sr in success_rates if 65 <= sr < 75)}")
print(f"  Poor (<65%): {sum(1 for sr in success_rates if sr < 65)}")
