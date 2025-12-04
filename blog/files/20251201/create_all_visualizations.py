#!/usr/bin/env python3
"""
Generate all high-quality visualizations for the Can't Stop blog post.
Modern, consistent styling across all charts.
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

# Color palette - modern, accessible colors
COLORS = {
    'primary': '#2E86AB',      # Deep blue
    'secondary': '#A23B72',    # Burgundy
    'accent': '#F18F01',       # Orange
    'success': '#06A77D',      # Teal
    'warning': '#C73E1D',      # Red
    'neutral': '#6C757D',      # Gray
    'gradient': ['#2E86AB', '#3A9FC1', '#46B8D7', '#52D1ED'],
}

def save_fig(fig, filename, dpi=300):
    """Save figure with consistent settings."""
    filepath = Path(__file__).parent / filename
    fig.savefig(filepath, dpi=dpi, bbox_inches='tight', facecolor='#FAFAFA')
    print(f"✓ Generated: {filename}")
    plt.close(fig)


def plot_two_dice_distribution():
    """Enhanced two-dice probability distribution."""
    sums = list(range(2, 13))
    counts = [1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1]
    probabilities = [c/36 for c in counts]
    percentages = [p*100 for p in probabilities]

    fig, ax = plt.subplots(figsize=(12, 7))

    # Create gradient colors based on probability
    colors = [plt.cm.Blues(0.3 + 0.6 * (p / max(probabilities))) for p in probabilities]

    bars = ax.bar(sums, percentages, color=colors, edgecolor='#333333',
                   linewidth=1.5, alpha=0.9)

    # Add value labels
    for s, pct, cnt in zip(sums, percentages, counts):
        ax.text(s, pct + 0.4, f'{cnt}/36\n{pct:.1f}%',
                ha='center', va='bottom', fontsize=10, fontweight='600',
                color='#333333')

    # Styling
    ax.set_xlabel('Sum', fontsize=13, fontweight='600', color='#333333')
    ax.set_ylabel('Probability (%)', fontsize=13, fontweight='600', color='#333333')
    ax.set_title('Two Dice: Probability Distribution', fontsize=16, fontweight='700',
                 pad=20, color='#1a1a1a')
    ax.set_xticks(sums)
    ax.set_ylim(0, max(percentages) + 3)
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    save_fig(fig, 'two_dice_distribution.png')


def plot_four_dice_distribution():
    """Enhanced four-dice probability distribution."""
    sums = list(range(2, 13))
    counts = [171, 302, 461, 580, 727, 834, 727, 580, 461, 302, 171]
    probabilities = [c/1296 for c in counts]
    percentages = [p*100 for p in probabilities]

    fig, ax = plt.subplots(figsize=(12, 7))

    # Create gradient colors
    colors = [plt.cm.Oranges(0.4 + 0.5 * (p / max(probabilities))) for p in probabilities]

    bars = ax.bar(sums, percentages, color=colors, edgecolor='#333333',
                   linewidth=1.5, alpha=0.9)

    # Add value labels
    for s, pct, cnt in zip(sums, percentages, counts):
        ax.text(s, pct + 1.5, f'{cnt}/1296\n{pct:.1f}%',
                ha='center', va='bottom', fontsize=10, fontweight='600',
                color='#333333')

    # Styling
    ax.set_xlabel('Sum', fontsize=13, fontweight='600', color='#333333')
    ax.set_ylabel('Probability (%)', fontsize=13, fontweight='600', color='#333333')
    ax.set_title('Four Dice: P(at least one pair sums to x)', fontsize=16,
                 fontweight='700', pad=20, color='#1a1a1a')
    ax.set_xticks(sums)
    ax.set_ylim(0, max(percentages) + 10)
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    save_fig(fig, 'four_dice_distribution.png')


def plot_column_combinations():
    """Visualize best vs worst column combinations."""
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

    # Top combinations
    combos_top = [c[0] for c in top_combos]
    success_top = [c[1] for c in top_combos]

    bars1 = ax1.barh(range(len(combos_top)), success_top,
                     color=COLORS['success'], alpha=0.8, edgecolor='#333333', linewidth=1.5)

    ax1.set_yticks(range(len(combos_top)))
    ax1.set_yticklabels(combos_top, fontsize=11)
    ax1.set_xlabel('Success Rate (%)', fontsize=13, fontweight='600')
    ax1.set_title('Top 10 Best Column Combinations', fontsize=14, fontweight='700', pad=15)
    ax1.set_xlim(80, 95)
    ax1.grid(axis='x', alpha=0.3)
    ax1.invert_yaxis()
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    # Add value labels
    for i, (combo, val) in enumerate(top_combos):
        ax1.text(val + 0.3, i, f'{val:.1f}%', va='center', fontsize=10, fontweight='600')

    # Bottom combinations
    combos_bottom = [c[0] for c in bottom_combos]
    success_bottom = [c[1] for c in bottom_combos]

    bars2 = ax2.barh(range(len(combos_bottom)), success_bottom,
                     color=COLORS['warning'], alpha=0.8, edgecolor='#333333', linewidth=1.5)

    ax2.set_yticks(range(len(combos_bottom)))
    ax2.set_yticklabels(combos_bottom, fontsize=11)
    ax2.set_xlabel('Success Rate (%)', fontsize=13, fontweight='600')
    ax2.set_title('Top 10 Worst Column Combinations', fontsize=14, fontweight='700', pad=15)
    ax2.set_xlim(40, 60)
    ax2.grid(axis='x', alpha=0.3)
    ax2.invert_yaxis()
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    # Add value labels
    for i, (combo, val) in enumerate(bottom_combos):
        ax2.text(val + 0.3, i, f'{val:.1f}%', va='center', fontsize=10, fontweight='600')

    plt.tight_layout()
    save_fig(fig, 'column_combinations_comparison.png')


def plot_expected_rolls_per_column():
    """Visualize expected rolls needed to complete each column."""
    columns = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    lengths = [3, 5, 7, 9, 11, 13, 11, 9, 7, 5, 3]
    probabilities = [13.2, 23.3, 35.6, 44.8, 56.1, 64.4, 56.1, 44.8, 35.6, 23.3, 13.2]
    expected_rolls = [l/(p/100) for l, p in zip(lengths, probabilities)]

    fig, ax = plt.subplots(figsize=(12, 7))

    # Color based on efficiency (lower is better)
    colors = [COLORS['success'] if er < 20 else COLORS['primary'] if er < 21 else COLORS['warning']
              for er in expected_rolls]

    bars = ax.bar(columns, expected_rolls, color=colors, alpha=0.8,
                   edgecolor='#333333', linewidth=1.5)

    # Add value labels
    for col, er in zip(columns, expected_rolls):
        ax.text(col, er + 0.3, f'{er:.1f}', ha='center', va='bottom',
                fontsize=10, fontweight='600')

    # Add horizontal line at 20 (reference)
    ax.axhline(y=20, color='#666666', linestyle='--', linewidth=2, alpha=0.6, label='20 rolls')

    # Styling
    ax.set_xlabel('Column Number', fontsize=13, fontweight='600', color='#333333')
    ax.set_ylabel('Expected Rolls to Complete', fontsize=13, fontweight='600', color='#333333')
    ax.set_title('Expected Rolls per Column (Single Column Analysis)',
                 fontsize=16, fontweight='700', pad=20, color='#1a1a1a')
    ax.set_xticks(columns)
    ax.set_ylim(18, 24)
    ax.grid(axis='y', alpha=0.3)
    ax.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    save_fig(fig, 'expected_rolls_per_column.png')


def plot_strategy_rankings():
    """Visualize tournament strategy rankings."""
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

    bars = ax.barh(range(len(strategies)), win_rates, color=colors,
                   alpha=0.85, edgecolor='#333333', linewidth=1.5)

    # Highlight the champion
    bars[0].set_edgecolor('#000000')
    bars[0].set_linewidth(3)

    ax.set_yticks(range(len(strategies)))
    ax.set_yticklabels(strategies, fontsize=11)
    ax.set_xlabel('Win Rate (%)', fontsize=13, fontweight='600')
    ax.set_title('Strategy Tournament Rankings (Overall Win Rate)',
                 fontsize=16, fontweight='700', pad=20)
    ax.set_xlim(45, 85)
    ax.grid(axis='x', alpha=0.3)
    ax.invert_yaxis()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Add value labels
    for i, (strat, wr) in enumerate(zip(strategies, win_rates)):
        ax.text(wr + 0.5, i, f'{wr:.1f}%', va='center', fontsize=10, fontweight='600')

    # Add champion annotation
    ax.text(win_rates[0] - 1, 0, '★ CHAMPION', va='center', ha='right',
            fontsize=10, fontweight='700', color='#1a1a1a',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#FFD700', alpha=0.7))

    plt.tight_layout()
    save_fig(fig, 'strategy_tournament_rankings.png')


def plot_single_player_performance():
    """Visualize single-player completion times."""
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

    # Color based on speed (faster is better)
    colors = [COLORS['success'] if t < 15 else COLORS['primary'] if t < 18 else
              COLORS['accent'] if t < 23 else COLORS['warning'] for t in avg_turns]

    bars = ax.barh(range(len(strategies)), avg_turns, color=colors,
                   alpha=0.85, edgecolor='#333333', linewidth=1.5)

    ax.set_yticks(range(len(strategies)))
    ax.set_yticklabels(strategies, fontsize=11)
    ax.set_xlabel('Average Turns to Complete 3 Columns', fontsize=13, fontweight='600')
    ax.set_title('Single-Player Performance (Speed Test)',
                 fontsize=16, fontweight='700', pad=20)
    ax.set_xlim(10, 30)
    ax.grid(axis='x', alpha=0.3)
    ax.invert_yaxis()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Add value labels
    for i, (strat, turns) in enumerate(zip(strategies, avg_turns)):
        ax.text(turns + 0.3, i, f'{turns:.1f}', va='center', fontsize=10, fontweight='600')

    plt.tight_layout()
    save_fig(fig, 'single_player_performance.png')


def plot_tournament_heatmap():
    """Create heatmap of all strategy matchups."""
    # Read the tournament results CSV
    csv_path = Path(__file__).parent / 'tournament_results_full.csv'
    df = pd.read_csv(csv_path, index_col=0)

    # Convert to numeric, handling '--' entries
    df = df.replace('--', np.nan)
    df = df.astype(float)

    # Create figure with better size
    fig, ax = plt.subplots(figsize=(20, 18))

    # Create custom colormap
    cmap = sns.diverging_palette(10, 130, s=80, l=55, n=100, as_cmap=True)

    # Plot heatmap
    sns.heatmap(df, annot=False, fmt='.1f', cmap=cmap, center=50,
                vmin=0, vmax=100, linewidths=0.5, linecolor='#CCCCCC',
                cbar_kws={'label': 'Win Rate (%)', 'shrink': 0.8}, ax=ax)

    # Styling
    ax.set_title('Complete Tournament Win Matrix (Row vs Column)',
                 fontsize=18, fontweight='700', pad=25)
    ax.set_xlabel('Opponent Strategy', fontsize=13, fontweight='600', labelpad=10)
    ax.set_ylabel('Player Strategy', fontsize=13, fontweight='600', labelpad=10)

    # Rotate labels for better readability
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right', rotation_mode='anchor', fontsize=9)
    plt.setp(ax.get_yticklabels(), rotation=0, fontsize=9)

    # Add colorbar label styling
    cbar = ax.collections[0].colorbar
    cbar.ax.tick_params(labelsize=10)

    plt.tight_layout()
    save_fig(fig, 'tournament_heatmap_full.png', dpi=200)


def main():
    """Generate all visualizations."""
    print("\n" + "="*60)
    print("GENERATING HIGH-QUALITY VISUALIZATIONS")
    print("="*60 + "\n")

    print("📊 Creating probability distributions...")
    plot_two_dice_distribution()
    plot_four_dice_distribution()

    print("\n📊 Creating column analysis charts...")
    plot_column_combinations()
    plot_expected_rolls_per_column()

    print("\n📊 Creating strategy performance charts...")
    plot_strategy_rankings()
    plot_single_player_performance()

    print("\n📊 Creating tournament heatmap...")
    plot_tournament_heatmap()

    print("\n" + "="*60)
    print("✅ ALL VISUALIZATIONS GENERATED SUCCESSFULLY")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
