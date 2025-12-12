#!/usr/bin/env python3
"""
Can't Stop Data Loader - Transforms raw simulation data into analysis-ready formats

Usage:
    from data_loader import DataLoader

    loader = DataLoader('results/single_player_raw_20251210_*.jsonl.gz',
                        'results/head_to_head_raw_20251210_*.jsonl.gz')

    # Get different views of the data
    sp_df = loader.get_single_player()
    h2h_df = loader.get_head_to_head()
    h2h_symmetric = loader.get_head_to_head_symmetric()
    matchup_summary = loader.get_matchup_summary()
"""

import pandas as pd
import numpy as np
import json
import gzip
from pathlib import Path
from typing import Optional, Dict, List
import glob


class DataLoader:
    """Loads and transforms Can't Stop simulation data into analysis-ready formats."""

    def __init__(self, single_player_path: Optional[str] = None,
                 head_to_head_path: Optional[str] = None):
        """
        Initialize data loader.

        Args:
            single_player_path: Path to single-player JSONL.gz file (supports wildcards)
            head_to_head_path: Path to head-to-head JSONL.gz file (supports wildcards)
        """
        self.sp_path = single_player_path
        self.h2h_path = head_to_head_path

        # Cached dataframes
        self._sp_df = None
        self._h2h_df = None

    def _find_file(self, pattern: str) -> str:
        """Find file matching pattern."""
        files = glob.glob(pattern)
        if not files:
            raise FileNotFoundError(f"No files found matching: {pattern}")
        if len(files) > 1:
            print(f"Warning: Multiple files found, using: {files[0]}")
        return files[0]

    def get_single_player(self, reload: bool = False) -> pd.DataFrame:
        """
        Load single-player data with expanded columns.

        Returns DataFrame with columns:
            - strategy: Strategy name
            - trial: Trial number (0-999)
            - turns_to_1col, turns_to_2col, turns_to_3col: Milestone turns
            - busts: Total busts
            - columns_completed: List of completed columns
            - col_2 through col_12: Usage count for each column
            - completed_2 through completed_12: Boolean if column was completed
        """
        if self._sp_df is not None and not reload:
            return self._sp_df

        if self.sp_path is None:
            raise ValueError("No single-player data path provided")

        file_path = self._find_file(self.sp_path)
        print(f"Loading single-player data from: {file_path}")

        # Load raw data
        df = pd.read_json(file_path, lines=True, compression='gzip')

        # Expand column_usage into separate columns
        column_usage = pd.json_normalize(df['column_usage'])
        column_usage.columns = [f'col_{c}' for c in column_usage.columns]

        # Create binary columns for which columns were completed
        for col in range(2, 13):
            df[f'completed_{col}'] = df['columns_completed'].apply(
                lambda x: col in x if isinstance(x, list) else False
            )

        # Combine
        df = pd.concat([df.drop('column_usage', axis=1), column_usage], axis=1)

        # Add derived metrics
        df['total_column_usage'] = df[[f'col_{i}' for i in range(2, 13)]].sum(axis=1)
        df['num_columns_completed'] = df['columns_completed'].apply(
            lambda x: len(x) if isinstance(x, list) else 0
        )

        self._sp_df = df
        print(f"  Loaded {len(df)} trials across {df['strategy'].nunique()} strategies")
        return df

    def get_head_to_head(self, reload: bool = False) -> pd.DataFrame:
        """
        Load head-to-head data with enhanced columns.

        Returns DataFrame with columns:
            - s1, s2: Player 1 and Player 2 strategy names
            - game: Game number
            - winner: Winner (0=P1, 1=P2)
            - turns: Game length
            - p1_cols, p2_cols: Columns completed
            - p1_busts, p2_busts: Bust counts
            - p1_won: Boolean (True if P1 won)
            - p2_won: Boolean (True if P2 won)
            - is_self_play: Boolean (True if s1 == s2)
            - matchup: "Strategy1 vs Strategy2" string
            - matchup_ordered: Alphabetically ordered matchup (for grouping)
        """
        if self._h2h_df is not None and not reload:
            return self._h2h_df

        if self.h2h_path is None:
            raise ValueError("No head-to-head data path provided")

        file_path = self._find_file(self.h2h_path)
        print(f"Loading head-to-head data from: {file_path}")

        # Load raw data
        df = pd.read_json(file_path, lines=True, compression='gzip')

        # Add derived columns
        df['p1_won'] = (df['winner'] == 0)
        df['p2_won'] = (df['winner'] == 1)
        df['is_self_play'] = (df['s1'] == df['s2'])
        df['matchup'] = df['s1'] + ' vs ' + df['s2']

        # Create ordered matchup for symmetric analysis
        df['matchup_ordered'] = df.apply(
            lambda row: ' vs '.join(sorted([row['s1'], row['s2']])),
            axis=1
        )

        # Add game length categories
        df['game_length_cat'] = pd.cut(
            df['turns'],
            bins=[0, 10, 15, 20, 30, 100],
            labels=['very_short', 'short', 'medium', 'long', 'very_long']
        )

        self._h2h_df = df
        print(f"  Loaded {len(df)} games across {df['matchup'].nunique()} matchups")
        return df

    def get_head_to_head_symmetric(self) -> pd.DataFrame:
        """
        Get head-to-head data in symmetric format (both P1 and P2 perspectives).

        This creates TWO rows for each game:
        - One from Player 1's perspective
        - One from Player 2's perspective

        Useful for analyzing strategy performance independent of player position.

        Returns DataFrame with columns:
            - strategy: The strategy being analyzed
            - opponent: The opponent strategy
            - game_id: Original game identifier
            - won: Boolean (did this strategy win)
            - player_position: 'P1' or 'P2'
            - my_cols, opp_cols: Columns completed
            - my_busts, opp_busts: Bust counts
            - turns: Game length
            - is_self_play: Boolean
        """
        h2h = self.get_head_to_head()

        # Player 1 perspective
        p1_view = pd.DataFrame({
            'strategy': h2h['s1'],
            'opponent': h2h['s2'],
            'game_id': h2h.index,
            'won': h2h['p1_won'],
            'player_position': 'P1',
            'my_cols': h2h['p1_cols'],
            'opp_cols': h2h['p2_cols'],
            'my_busts': h2h['p1_busts'],
            'opp_busts': h2h['p2_busts'],
            'turns': h2h['turns'],
            'is_self_play': h2h['is_self_play']
        })

        # Player 2 perspective
        p2_view = pd.DataFrame({
            'strategy': h2h['s2'],
            'opponent': h2h['s1'],
            'game_id': h2h.index,
            'won': h2h['p2_won'],
            'player_position': 'P2',
            'my_cols': h2h['p2_cols'],
            'opp_cols': h2h['p1_cols'],
            'my_busts': h2h['p2_busts'],
            'opp_busts': h2h['p1_busts'],
            'turns': h2h['turns'],
            'is_self_play': h2h['is_self_play']
        })

        # Combine both views
        symmetric_df = pd.concat([p1_view, p2_view], ignore_index=True)

        print(f"Created symmetric view: {len(symmetric_df)} records ({len(h2h)} games × 2)")
        return symmetric_df

    def get_matchup_summary(self) -> pd.DataFrame:
        """
        Get aggregated summary for each matchup.

        Returns DataFrame with one row per matchup (s1, s2 pair):
            - s1, s2: Strategies
            - total_games: Number of games
            - p1_wins, p2_wins: Win counts
            - p1_win_rate, p2_win_rate: Win rates
            - avg_turns, median_turns, std_turns: Game length stats
            - avg_p1_cols, avg_p2_cols: Average columns completed
            - avg_p1_busts, avg_p2_busts: Average busts
            - is_self_play: Boolean
        """
        h2h = self.get_head_to_head()

        summary = h2h.groupby(['s1', 's2']).agg({
            'game': 'count',
            'p1_won': ['sum', 'mean'],
            'p2_won': ['sum', 'mean'],
            'turns': ['mean', 'median', 'std'],
            'p1_cols': 'mean',
            'p2_cols': 'mean',
            'p1_busts': 'mean',
            'p2_busts': 'mean',
            'is_self_play': 'first'
        }).reset_index()

        # Flatten multi-level columns
        summary.columns = [
            's1', 's2',
            'total_games',
            'p1_wins', 'p1_win_rate',
            'p2_wins', 'p2_win_rate',
            'avg_turns', 'median_turns', 'std_turns',
            'avg_p1_cols', 'avg_p2_cols',
            'avg_p1_busts', 'avg_p2_busts',
            'is_self_play'
        ]

        print(f"Created matchup summary: {len(summary)} matchups")
        return summary

    def get_strategy_overall_stats(self) -> pd.DataFrame:
        """
        Get overall statistics for each strategy across all matchups.

        Returns DataFrame with one row per strategy:
            - strategy: Strategy name
            - total_games: Games played (as P1 and P2)
            - total_wins: Total wins
            - overall_win_rate: Overall win rate
            - as_p1_games, as_p1_wins, as_p1_win_rate: Stats as Player 1
            - as_p2_games, as_p2_wins, as_p2_win_rate: Stats as Player 2
            - first_player_advantage: Difference (p1_rate - p2_rate)
            - avg_turns_when_winning: Average game length when winning
            - avg_turns_when_losing: Average game length when losing
        """
        symmetric = self.get_head_to_head_symmetric()

        overall = symmetric.groupby('strategy').agg({
            'game_id': 'count',
            'won': ['sum', 'mean']
        })
        overall.columns = ['total_games', 'total_wins', 'overall_win_rate']
        overall = overall.reset_index()

        # Player 1 stats
        p1_stats = symmetric[symmetric['player_position'] == 'P1'].groupby('strategy').agg({
            'game_id': 'count',
            'won': ['sum', 'mean']
        })
        p1_stats.columns = ['as_p1_games', 'as_p1_wins', 'as_p1_win_rate']

        # Player 2 stats
        p2_stats = symmetric[symmetric['player_position'] == 'P2'].groupby('strategy').agg({
            'game_id': 'count',
            'won': ['sum', 'mean']
        })
        p2_stats.columns = ['as_p2_games', 'as_p2_wins', 'as_p2_win_rate']

        # Combine
        overall = overall.merge(p1_stats, on='strategy', how='left')
        overall = overall.merge(p2_stats, on='strategy', how='left')

        # First-player advantage
        overall['first_player_advantage'] = overall['as_p1_win_rate'] - overall['as_p2_win_rate']

        # Avg turns when winning/losing
        winning_turns = symmetric[symmetric['won']].groupby('strategy')['turns'].mean()
        losing_turns = symmetric[~symmetric['won']].groupby('strategy')['turns'].mean()

        overall = overall.merge(
            winning_turns.rename('avg_turns_when_winning'),
            on='strategy',
            how='left'
        )
        overall = overall.merge(
            losing_turns.rename('avg_turns_when_losing'),
            on='strategy',
            how='left'
        )

        print(f"Created strategy overall stats: {len(overall)} strategies")
        return overall


# ============================================================================
# Analysis Helper Functions
# ============================================================================

def analyze_self_play(loader: DataLoader) -> pd.DataFrame:
    """
    Analyze self-play matchups to verify fairness and detect first-player advantage.

    Returns DataFrame with:
        - strategy: Strategy name
        - total_games: Games played
        - p1_wins, p2_wins: Win counts
        - p1_win_rate: Should be ~0.5
        - deviation_from_50: Absolute deviation from 50%
        - is_fair: Boolean (deviation < 10%)
    """
    h2h = loader.get_head_to_head()
    self_play = h2h[h2h['is_self_play']].copy()

    results = self_play.groupby('s1').agg({
        'game': 'count',
        'p1_won': 'sum',
        'p2_won': 'sum'
    }).reset_index()

    results.columns = ['strategy', 'total_games', 'p1_wins', 'p2_wins']
    results['p1_win_rate'] = results['p1_wins'] / results['total_games']
    results['deviation_from_50'] = (results['p1_win_rate'] - 0.5).abs()
    results['is_fair'] = results['deviation_from_50'] < 0.1

    return results.sort_values('deviation_from_50', ascending=False)


def get_win_matrix(loader: DataLoader) -> pd.DataFrame:
    """
    Create win rate matrix (strategies as rows, opponents as columns).

    Returns DataFrame where:
        - Rows = Strategy as Player 1
        - Columns = Opponent as Player 2
        - Values = Player 1 win rate
    """
    summary = loader.get_matchup_summary()
    pivot = summary.pivot(index='s1', columns='s2', values='p1_win_rate')
    return pivot


def get_strategy_rankings(loader: DataLoader, by: str = 'overall') -> pd.DataFrame:
    """
    Get strategy rankings.

    Args:
        by: Ranking method
            - 'overall': Overall win rate across all matchups
            - 'single_player': Average turns to win (single-player)
            - 'head_to_head': ELO-like ranking (TODO)

    Returns ranked DataFrame.
    """
    if by == 'overall':
        stats = loader.get_strategy_overall_stats()
        ranked = stats.sort_values('overall_win_rate', ascending=False)
        ranked['rank'] = range(1, len(ranked) + 1)
        return ranked[['rank', 'strategy', 'overall_win_rate', 'total_wins',
                      'first_player_advantage']]

    elif by == 'single_player':
        sp = loader.get_single_player()
        avg_turns = sp.groupby('strategy')['turns_to_3col'].agg(['mean', 'median', 'std'])
        avg_turns = avg_turns.reset_index().sort_values('mean')
        avg_turns['rank'] = range(1, len(avg_turns) + 1)
        return avg_turns[['rank', 'strategy', 'mean', 'median', 'std']]

    else:
        raise ValueError(f"Unknown ranking method: {by}")


def find_counter_strategies(loader: DataLoader, target_strategy: str, top_n: int = 5) -> pd.DataFrame:
    """
    Find strategies that perform best/worst against a target strategy.

    Returns DataFrame with top N counter strategies (highest win rate against target).
    """
    symmetric = loader.get_head_to_head_symmetric()

    # Games where target is the opponent
    against_target = symmetric[symmetric['opponent'] == target_strategy]

    # Calculate win rate against target
    counter_stats = against_target.groupby('strategy').agg({
        'won': ['sum', 'count', 'mean']
    }).reset_index()
    counter_stats.columns = ['strategy', 'wins', 'games', 'win_rate']

    # Sort by win rate
    counter_stats = counter_stats.sort_values('win_rate', ascending=False)

    return counter_stats.head(top_n)


# ============================================================================
# Example Usage and Analysis Templates
# ============================================================================

def example_analyses():
    """Show example analysis patterns."""

    # Initialize loader
    loader = DataLoader(
        'results/single_player_raw_*.jsonl.gz',
        'results/head_to_head_raw_*.jsonl.gz'
    )

    print("\n" + "="*80)
    print("EXAMPLE 1: Best Single-Player Strategy")
    print("="*80)
    sp = loader.get_single_player()
    best = sp.groupby('strategy')['turns_to_3col'].mean().sort_values().head(10)
    print(best)

    print("\n" + "="*80)
    print("EXAMPLE 2: Self-Play Fairness Check")
    print("="*80)
    self_play = analyze_self_play(loader)
    print(self_play.head(10))

    print("\n" + "="*80)
    print("EXAMPLE 3: First-Player Advantage")
    print("="*80)
    stats = loader.get_strategy_overall_stats()
    print(stats[['strategy', 'as_p1_win_rate', 'as_p2_win_rate',
                 'first_player_advantage']].sort_values('first_player_advantage', ascending=False).head(10))

    print("\n" + "="*80)
    print("EXAMPLE 4: Strategy Rankings")
    print("="*80)
    rankings = get_strategy_rankings(loader, by='overall')
    print(rankings.head(10))

    print("\n" + "="*80)
    print("EXAMPLE 5: Counter Strategies (Who beats Greedy?)")
    print("="*80)
    counters = find_counter_strategies(loader, 'Greedy', top_n=10)
    print(counters)


if __name__ == "__main__":
    # Run examples if executed directly
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'examples':
        example_analyses()
    else:
        print(__doc__)
        print("\nRun with 'python data_loader.py examples' to see example analyses")
