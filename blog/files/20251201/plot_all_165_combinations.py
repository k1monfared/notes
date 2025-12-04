#!/usr/bin/env python3
"""
Create a dense visualization of all 165 column combinations.
Shows the full distribution without individual labels for readability.
"""

import matplotlib.pyplot as plt
import numpy as np
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

COLORS = {
    'success': '#06A77D',
    'warning': '#C73E1D',
}

def save_fig(fig, filename, dpi=300):
    """Save figure with consistent settings."""
    filepath = Path(__file__).parent / filename
    fig.savefig(filepath, dpi=dpi, bbox_inches='tight', facecolor='#FAFAFA')
    print(f"✓ Generated: {filename}")
    plt.close(fig)


# All 165 combinations with their success rates
# Generated from column_combinations.py output
all_combos_data = [
    ('{6,7,8}', 92.0), ('{5,7,8}', 91.4), ('{6,7,9}', 91.4),
    ('{4,6,8}', 91.1), ('{6,8,10}', 91.1), ('{4,7,8}', 90.3),
    ('{6,7,10}', 90.3), ('{5,6,8}', 89.5), ('{6,8,9}', 89.5),
    ('{3,7,8}', 89.3), ('{4,7,9}', 89.3), ('{5,7,10}', 89.3),
    ('{6,7,11}', 89.3), ('{2,7,8}', 89.0), ('{6,7,12}', 89.0),
    ('{5,6,7}', 88.7), ('{7,8,9}', 88.7), ('{4,6,7}', 88.6),
    ('{7,8,10}', 88.6), ('{2,6,8}', 88.3), ('{4,5,8}', 88.3),
    ('{6,8,11}', 88.3), ('{8,9,10}', 88.3), ('{3,7,9}', 88.0),
    ('{4,7,10}', 88.0), ('{5,7,11}', 88.0), ('{6,7,8}', 87.8),
    ('{3,6,8}', 87.7), ('{4,8,9}', 87.7), ('{6,8,12}', 87.7),
    ('{7,9,10}', 87.7), ('{3,4,8}', 87.4), ('{4,8,10}', 87.4),
    ('{5,6,9}', 87.4), ('{6,9,10}', 87.4), ('{3,7,10}', 87.2),
    ('{5,7,12}', 87.2), ('{2,7,9}', 86.9), ('{4,7,11}', 86.9),
    ('{3,6,7}', 86.7), ('{7,9,11}', 86.7), ('{5,8,9}', 86.5),
    ('{6,7,9}', 86.5), ('{2,6,7}', 86.4), ('{3,5,8}', 86.4),
    ('{5,8,10}', 86.4), ('{7,8,11}', 86.4), ('{8,9,11}', 86.4),
    ('{2,4,8}', 86.1), ('{4,6,9}', 86.1), ('{4,8,11}', 86.1),
    ('{6,9,11}', 86.1), ('{8,10,11}', 86.1), ('{3,7,11}', 85.9),
    ('{2,7,10}', 85.6), ('{4,7,12}', 85.6), ('{3,4,7}', 85.5),
    ('{7,10,11}', 85.5), ('{2,6,9}', 85.2), ('{3,8,9}', 85.2),
    ('{6,9,12}', 85.2), ('{8,9,12}', 85.2), ('{3,6,9}', 84.9),
    ('{5,6,10}', 84.9), ('{6,10,11}', 84.9), ('{2,5,8}', 84.6),
    ('{2,8,9}', 84.6), ('{5,8,11}', 84.6), ('{8,10,12}', 84.6),
    ('{4,5,7}', 84.4), ('{7,9,12}', 84.4), ('{3,4,9}', 84.3),
    ('{4,9,10}', 84.3), ('{2,7,11}', 84.1), ('{3,5,7}', 83.9),
    ('{7,10,12}', 83.9), ('{2,4,7}', 83.8), ('{7,11,12}', 83.8),
    ('{2,6,10}', 83.5), ('{4,8,12}', 83.5), ('{3,8,10}', 83.3),
    ('{5,6,11}', 83.3), ('{6,10,12}', 83.3), ('{5,9,10}', 83.2),
    ('{6,7,10}', 83.2), ('{4,6,10}', 82.9), ('{2,3,8}', 82.7),
    ('{3,8,11}', 82.7), ('{8,11,12}', 82.7), ('{2,8,10}', 82.5),
    ('{5,9,11}', 82.5), ('{2,7,12}', 82.2), ('{3,7,12}', 82.2),
    ('{4,5,9}', 82.0), ('{2,5,7}', 81.9), ('{7,11,12}', 81.9),
    ('{3,4,10}', 81.7), ('{4,9,11}', 81.7), ('{2,6,11}', 81.4),
    ('{3,6,10}', 81.4), ('{4,6,11}', 81.4), ('{6,11,12}', 81.4),
    ('{5,6,12}', 81.2), ('{2,4,9}', 81.0), ('{4,9,12}', 81.0),
    ('{5,9,12}', 80.9), ('{3,5,9}', 80.6), ('{9,10,11}', 80.6),
    ('{2,8,11}', 80.4), ('{4,10,11}', 80.4), ('{3,9,10}', 80.2),
    ('{2,3,7}', 80.0), ('{9,10,12}', 79.9), ('{3,5,10}', 79.7),
    ('{2,5,9}', 79.4), ('{2,9,10}', 79.4), ('{9,11,12}', 79.4),
    ('{2,8,12}', 79.2), ('{3,8,12}', 79.2), ('{3,9,11}', 78.9),
    ('{2,4,10}', 78.6), ('{4,10,12}', 78.6), ('{2,6,12}', 78.4),
    ('{3,6,11}', 78.4), ('{5,10,11}', 78.3), ('{2,5,10}', 77.9),
    ('{3,4,11}', 77.6), ('{3,9,12}', 77.7), ('{5,10,12}', 77.6),
    ('{2,3,9}', 77.3), ('{10,11,12}', 77.3), ('{3,6,12}', 77.1),
    ('{2,9,11}', 76.9), ('{3,5,11}', 76.6), ('{2,4,11}', 76.3),
    ('{2,10,11}', 76.3), ('{4,11,12}', 76.3), ('{3,10,11}', 75.9),
    ('{2,5,11}', 75.6), ('{5,11,12}', 75.6), ('{2,9,12}', 75.4),
    ('{3,10,12}', 75.4), ('{2,3,10}', 74.9), ('{2,10,12}', 74.9),
    ('{2,5,12}', 73.7), ('{3,5,12}', 73.7), ('{2,3,11}', 73.4),
    ('{3,11,12}', 73.4), ('{2,4,12}', 71.9), ('{3,4,12}', 71.9),
    ('{2,11,12}', 63.7), ('{2,3,12}', 63.7),
]

# Sort by success rate (descending)
all_combos_data.sort(key=lambda x: x[1], reverse=True)

combos = [c[0] for c in all_combos_data]
success_rates = [c[1] for c in all_combos_data]

# Create figure
fig, ax = plt.subplots(figsize=(14, 20))

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
    ax.plot([0, val], [i, i], color=color, linewidth=1.5, alpha=0.5)

# Draw dots
ax.scatter(success_rates, positions, s=30, c=colors, alpha=0.8,
           edgecolor='none', zorder=3)

# Only label notable combinations
labels_to_show = [
    (0, combos[0], success_rates[0]),  # Best
    (len(combos)//4, combos[len(combos)//4], success_rates[len(combos)//4]),  # 25th percentile
    (len(combos)//2, combos[len(combos)//2], success_rates[len(combos)//2]),  # Median
    (3*len(combos)//4, combos[3*len(combos)//4], success_rates[3*len(combos)//4]),  # 75th percentile
    (len(combos)-1, combos[-1], success_rates[-1]),  # Worst
]

for idx, combo, sr in labels_to_show:
    ax.annotate(f'{combo}\n{sr:.1f}%',
                xy=(sr, idx),
                xytext=(10, 0),
                textcoords='offset points',
                fontsize=8,
                fontweight='600',
                va='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                         edgecolor=colors[idx], linewidth=1.5, alpha=0.9))

# Reference lines
ax.axvline(x=50, color='#999999', linestyle=':', linewidth=2, alpha=0.4,
           label='50% (coin flip)', zorder=1)
ax.axvline(x=75, color='#666666', linestyle='--', linewidth=1.5, alpha=0.5,
           label='75% threshold', zorder=1)
ax.axvline(x=85, color='#333333', linestyle='--', linewidth=1.5, alpha=0.5,
           label='85% threshold', zorder=1)

# Styling
ax.set_xlabel('Success Rate (%)', fontsize=14, fontweight='600', color='#333333')
ax.set_ylabel('Rank (1 = Best)', fontsize=14, fontweight='600', color='#333333')
ax.set_title('All 165 Three-Column Combinations Ranked by Success Rate',
             fontsize=17, fontweight='700', pad=25, color='#1a1a1a')
ax.set_xlim(0, 100)
ax.set_ylim(-5, len(combos) + 5)
ax.grid(axis='x', alpha=0.3)
ax.invert_yaxis()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.set_yticks([])  # Remove y-axis tick labels for cleaner look

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
                    frameon=True, fancybox=True, shadow=True, title='Success Tiers')

# Add second legend for reference lines
ax.add_artist(legend1)
ax.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)

# Add annotation showing the range
ax.text(0.02, 0.98, f'Range: {min(success_rates):.1f}% - {max(success_rates):.1f}%\nSpread: {max(success_rates) - min(success_rates):.1f} percentage points',
        transform=ax.transAxes, fontsize=10, verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

plt.tight_layout()
save_fig(fig, 'all_165_combinations_ranked.png', dpi=250)

print(f"\nStatistics:")
print(f"  Total combinations: {len(combos)}")
print(f"  Best: {combos[0]} at {success_rates[0]:.1f}%")
print(f"  Worst: {combos[-1]} at {success_rates[-1]:.1f}%")
print(f"  Median: {success_rates[len(combos)//2]:.1f}%")
print(f"  Mean: {np.mean(success_rates):.1f}%")
print(f"  Excellent (≥85%): {sum(1 for sr in success_rates if sr >= 85)}")
print(f"  Good (75-85%): {sum(1 for sr in success_rates if 75 <= sr < 85)}")
print(f"  Mediocre (65-75%): {sum(1 for sr in success_rates if 65 <= sr < 75)}")
print(f"  Poor (<65%): {sum(1 for sr in success_rates if sr < 65)}")
