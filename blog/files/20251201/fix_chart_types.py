#!/usr/bin/env python3
"""
Fix charts that don't start from zero - convert to appropriate chart types.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns
from pathlib import Path

# Set modern style parameters
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Inter', 'Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.facecolor': '#FAFAFA',
    'axes.facecolor': '#FFFFFF',
    'axes.edgecolor': '#CCCCCC',
    'axes.linewidth': 1.2,
    'grid.alpha': 0.3,
    'grid.linestyle': '--',
    'grid.linewidth': 0.8,
})

# Color palette
COLORS = {
    'primary': '#2E86AB',
    'secondary': '#A23B72',
    'accent': '#F18F01',
    'success': '#06A77D',
    'warning': '#C73E1D',
    'neutral': '#6C757D',
}

def save_fig(fig, filename, dpi=300):
    """Save figure with consistent settings."""
    filepath = Path(__file__).parent / filename
    fig.savefig(filepath, dpi=dpi, bbox_inches='tight', facecolor='#FAFAFA')
    print(f"✓ Generated: {filename}")
    plt.close(fig)


def plot_expected_rolls_per_column():
    """Line plot for expected rolls (shows deviations from target better)."""
    columns = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    lengths = [3, 5, 7, 9, 11, 13, 11, 9, 7, 5, 3]
    probabilities = [13.2, 23.3, 35.6, 44.8, 56.1, 64.4, 56.1, 44.8, 35.6, 23.3, 13.2]
    expected_rolls = [l/(p/100) for l, p in zip(lengths, probabilities)]

    fig, ax = plt.subplots(figsize=(12, 7))

    # Plot line with markers
    ax.plot(columns, expected_rolls, marker='o', linewidth=2.5, markersize=10,
            color=COLORS['primary'], markerfacecolor=COLORS['primary'],
            markeredgecolor='#333333', markeredgewidth=1.5, label='Expected Rolls')

    # Add horizontal reference line at 20
    ax.axhline(y=20, color=COLORS['neutral'], linestyle='--', linewidth=2,
               alpha=0.7, label='20 rolls (reference)', zorder=1)

    # Highlight range
    ax.fill_between(columns, 19, 21, alpha=0.15, color=COLORS['success'],
                     label='19-21 roll range')

    # Add value labels
    for col, er in zip(columns, expected_rolls):
        offset = 0.4 if er > 20 else -0.4
        va = 'bottom' if er > 20 else 'top'
        ax.text(col, er + offset, f'{er:.1f}', ha='center', va=va,
                fontsize=9, fontweight='600', color='#333333')

    # Styling
    ax.set_xlabel('Column Number', fontsize=13, fontweight='600', color='#333333')
    ax.set_ylabel('Expected Rolls to Complete', fontsize=13, fontweight='600', color='#333333')
    ax.set_title('Expected Rolls per Column (Single Column Analysis)',
                 fontsize=16, fontweight='700', pad=20, color='#1a1a1a')
    ax.set_xticks(columns)
    ax.set_ylim(18, 24)
    ax.grid(axis='both', alpha=0.3)
    ax.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    save_fig(fig, 'expected_rolls_per_column.png')


def plot_column_combinations():
    """Dot plot for column combinations to show differences without truncated bars."""
    # Top 10 and Bottom 10
    top_combos = [
        ('{6,7,8}', 92.0),
        ('{5,7,8}', 91.4),
        ('{6,7,9}', 91.4),
        ('{4,6,8}', 91.1),
        ('{6,8,10}', 91.1),
        ('{4,7,8}', 90.3),
        ('{6,7,10}', 90.3),
        ('{5,6,8}', 89.5),
        ('{6,8,9}', 89.5),
        ('{5,7,10}', 89.3),
    ]

    bottom_combos = [
        ('{2,11,12}', 43.8),
        ('{2,3,12}', 43.8),
        ('{10,11,12}', 52.2),
        ('{2,3,4}', 52.2),
        ('{3,11,12}', 52.5),
        ('{2,3,11}', 52.5),
        ('{2,10,12}', 55.2),
        ('{2,4,12}', 55.2),
        ('{3,4,12}', 57.9),
        ('{2,10,11}', 57.9),
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # Top combinations - Lollipop chart
    combos_top = [c[0] for c in top_combos]
    success_top = [c[1] for c in top_combos]

    # Draw lines from 0 to value
    for i, val in enumerate(success_top):
        ax1.plot([0, val], [i, i], color=COLORS['success'], linewidth=2, alpha=0.6)

    # Draw dots
    ax1.scatter(success_top, range(len(combos_top)), s=200, color=COLORS['success'],
                alpha=0.9, edgecolor='#333333', linewidth=2, zorder=3)

    ax1.set_yticks(range(len(combos_top)))
    ax1.set_yticklabels(combos_top, fontsize=11)
    ax1.set_xlabel('Success Rate (%)', fontsize=13, fontweight='600')
    ax1.set_title('Top 10 Best Column Combinations', fontsize=14, fontweight='700', pad=15)
    ax1.set_xlim(0, 100)
    ax1.grid(axis='x', alpha=0.3)
    ax1.invert_yaxis()
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    # Add value labels
    for i, (combo, val) in enumerate(top_combos):
        ax1.text(val + 1.5, i, f'{val:.1f}%', va='center', fontsize=10, fontweight='600')

    # Bottom combinations - Lollipop chart
    combos_bottom = [c[0] for c in bottom_combos]
    success_bottom = [c[1] for c in bottom_combos]

    # Draw lines from 0 to value
    for i, val in enumerate(success_bottom):
        ax2.plot([0, val], [i, i], color=COLORS['warning'], linewidth=2, alpha=0.6)

    # Draw dots
    ax2.scatter(success_bottom, range(len(combos_bottom)), s=200, color=COLORS['warning'],
                alpha=0.9, edgecolor='#333333', linewidth=2, zorder=3)

    ax2.set_yticks(range(len(combos_bottom)))
    ax2.set_yticklabels(combos_bottom, fontsize=11)
    ax2.set_xlabel('Success Rate (%)', fontsize=13, fontweight='600')
    ax2.set_title('Top 10 Worst Column Combinations', fontsize=14, fontweight='700', pad=15)
    ax2.set_xlim(0, 100)
    ax2.grid(axis='x', alpha=0.3)
    ax2.invert_yaxis()
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    # Add value labels
    for i, (combo, val) in enumerate(bottom_combos):
        ax2.text(val + 1.5, i, f'{val:.1f}%', va='center', fontsize=10, fontweight='600')

    plt.tight_layout()
    save_fig(fig, 'column_combinations_comparison.png')


def plot_strategy_rankings():
    """Lollipop chart for strategy rankings (better than truncated bars)."""
    strategies = [
        'GreedyUntil1Col', 'GreedyImproved2', 'GreedyFraction(0.33)',
        'GreedyImproved1', 'AdaptiveThreshold', 'Conservative(4)',
        'GreedyFraction(0.5)', 'FiftyPercentSurvival', 'Conservative(3)',
        'Heuristic(1.0)', 'ExpectedValueMax', 'Random(0.3)',
        'OppAware(0.7,1,1.5)', 'GreedyUntil3Col'
    ]
    win_rates = [81.6, 78.1, 76.9, 75.7, 73.1, 71.1, 67.9, 66.7, 65.7, 62.1,
                 56.8, 56.5, 53.1, 50.9]

    fig, ax = plt.subplots(figsize=(12, 10))

    # Color gradient from best to worst
    colors = [plt.cm.RdYlGn(0.2 + 0.7 * (wr - min(win_rates)) / (max(win_rates) - min(win_rates)))
              for wr in win_rates]

    # Draw lines from 0 to value
    for i, (val, color) in enumerate(zip(win_rates, colors)):
        ax.plot([0, val], [i, i], color=color, linewidth=2.5, alpha=0.6)

    # Draw dots
    ax.scatter(win_rates, range(len(strategies)), s=250, c=colors,
               alpha=0.9, edgecolor='#333333', linewidth=1.5, zorder=3)

    # Highlight the champion with special marker
    ax.scatter([win_rates[0]], [0], s=400, marker='*', color='#FFD700',
               edgecolor='#000000', linewidth=2.5, zorder=4, label='Champion')

    ax.set_yticks(range(len(strategies)))
    ax.set_yticklabels(strategies, fontsize=11)
    ax.set_xlabel('Win Rate (%)', fontsize=13, fontweight='600')
    ax.set_title('Strategy Tournament Rankings (Overall Win Rate)',
                 fontsize=16, fontweight='700', pad=20)
    ax.set_xlim(0, 100)
    ax.grid(axis='x', alpha=0.3)
    ax.invert_yaxis()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Add value labels
    for i, (strat, wr) in enumerate(zip(strategies, win_rates)):
        ax.text(wr + 1.5, i, f'{wr:.1f}%', va='center', fontsize=10, fontweight='600')

    # Add 50% reference line
    ax.axvline(x=50, color='#999999', linestyle=':', linewidth=2, alpha=0.5, label='50% (even odds)')

    ax.legend(loc='lower right', frameon=True, fancybox=True, shadow=True)

    plt.tight_layout()
    save_fig(fig, 'strategy_tournament_rankings.png')


def plot_single_player_performance():
    """Lollipop chart for single-player performance."""
    strategies = [
        'GreedyImproved2', 'GreedyFraction(0.33)', 'GreedyImproved1',
        'AdaptiveThreshold', 'Conservative(4)', 'GreedyFraction(0.5)',
        'FiftyPercentSurvival', 'Heuristic(1.0)', 'GreedyUntil1Col',
        'ExpectedValueMax', 'Conservative(3)', 'Heuristic(1.5)',
        'GreedyUntil3Col', 'Random(0.3)'
    ]
    avg_turns = [13.2, 13.2, 14.2, 14.1, 15.0, 15.3, 15.9, 16.0, 16.3,
                 17.3, 19.7, 22.3, 23.8, 26.9]

    fig, ax = plt.subplots(figsize=(12, 9))

    # Color based on speed (faster is better) - reversed color scale
    colors = [COLORS['success'] if t < 15 else COLORS['primary'] if t < 18 else
              COLORS['accent'] if t < 23 else COLORS['warning'] for t in avg_turns]

    # Draw lines from 0 to value
    for i, (val, color) in enumerate(zip(avg_turns, colors)):
        ax.plot([0, val], [i, i], color=color, linewidth=2.5, alpha=0.6)

    # Draw dots
    for i, (val, color) in enumerate(zip(avg_turns, colors)):
        ax.scatter([val], [i], s=250, color=color, alpha=0.9,
                   edgecolor='#333333', linewidth=1.5, zorder=3)

    ax.set_yticks(range(len(strategies)))
    ax.set_yticklabels(strategies, fontsize=11)
    ax.set_xlabel('Average Turns to Complete 3 Columns', fontsize=13, fontweight='600')
    ax.set_title('Single-Player Performance (Lower is Better)',
                 fontsize=16, fontweight='700', pad=20)
    ax.set_xlim(0, 30)
    ax.grid(axis='x', alpha=0.3)
    ax.invert_yaxis()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Add value labels
    for i, (strat, turns) in enumerate(zip(strategies, avg_turns)):
        ax.text(turns + 0.5, i, f'{turns:.1f}', va='center', fontsize=10, fontweight='600')

    # Add reference zones
    ax.axvspan(0, 15, alpha=0.1, color=COLORS['success'], label='Fast (< 15 turns)')
    ax.axvspan(15, 20, alpha=0.1, color=COLORS['primary'], label='Moderate (15-20 turns)')
    ax.axvspan(20, 30, alpha=0.1, color=COLORS['warning'], label='Slow (> 20 turns)')

    ax.legend(loc='lower right', frameon=True, fancybox=True, shadow=True)

    plt.tight_layout()
    save_fig(fig, 'single_player_performance.png')


def main():
    """Regenerate charts with proper zero baselines."""
    print("\n" + "="*60)
    print("FIXING CHARTS - PROPER ZERO BASELINES")
    print("="*60 + "\n")

    print("📊 Fixing expected rolls chart (line plot)...")
    plot_expected_rolls_per_column()

    print("📊 Fixing column combinations (lollipop chart)...")
    plot_column_combinations()

    print("📊 Fixing strategy rankings (lollipop chart)...")
    plot_strategy_rankings()

    print("📊 Fixing single-player performance (lollipop chart)...")
    plot_single_player_performance()

    print("\n" + "="*60)
    print("✅ ALL CHARTS FIXED")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
