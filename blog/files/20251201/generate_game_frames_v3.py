#!/usr/bin/env python3
"""
Generate game frames v3 - Educational step-by-step progression
Shows each decision stage as separate frames with animations
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional


class GameFrameGeneratorV3:
    """Generates educational step-by-step frames"""

    def __init__(self, game_data_file):
        with open(game_data_file, 'r') as f:
            self.data = json.load(f)

        self.player1 = self.data['player1']
        self.player2 = self.data['player2']
        self.history = self.data['history']

        # Column configuration
        self.columns = list(range(2, 13))
        self.column_length = {
            2: 3, 3: 5, 4: 7, 5: 9, 6: 11,
            7: 13, 8: 11, 9: 9, 10: 7, 11: 5, 12: 3
        }

        # Player colors
        self.color_p1 = '#1E88E5'  # Blue
        self.color_p2 = '#FF6F00'  # Orange

        # Pairing colors - 6 distinct colors
        self.pairing_colors = [
            ('#E53935', '#EF5350'),  # Reds for option 1
            ('#43A047', '#66BB6A'),  # Greens for option 2
            ('#8E24AA', '#AB47BC'),  # Purples for option 3
        ]

        self.bg_dark = '#1A1A1A'
        self.bg_panel = '#2C2C2C'

    def get_player_color(self, player_name):
        """Get color for player"""
        return self.color_p1 if player_name == self.player1 else self.color_p2

    def generate_all_frames(self, output_dir):
        """Generate all educational frames"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        print(f"Generating educational frames from {len(self.history)} states...")

        frame_idx = 0
        prev_player = None

        for state_idx, state in enumerate(self.history):
            current_player = state['current_player']

            # Frame 1: Turn change (if player changed)
            if prev_player != current_player:
                self.render_turn_change_frame(
                    state, f"{output_path}/frame_{frame_idx:04d}.png")
                frame_idx += 1
                prev_player = current_player

            # Frame 2: Show dice roll
            self.render_dice_only_frame(
                state, f"{output_path}/frame_{frame_idx:04d}.png")
            frame_idx += 1

            if not state['busted']:
                # Frames 3-5: Show options one by one
                for option_num in range(1, 4):
                    self.render_option_frame(
                        state, option_num, f"{output_path}/frame_{frame_idx:04d}.png")
                    frame_idx += 1

                # Frame 6: Highlight chosen option
                self.render_chosen_frame(
                    state, f"{output_path}/frame_{frame_idx:04d}.png")
                frame_idx += 1

                # Frames 7+: Animate peg movement (multiple frames)
                for anim_step in range(3):
                    self.render_peg_animation_frame(
                        state, anim_step, f"{output_path}/frame_{frame_idx:04d}.png")
                    frame_idx += 1

                # Frame: After move (pegs in new position)
                self.render_after_move_frame(
                    state, f"{output_path}/frame_{frame_idx:04d}.png")
                frame_idx += 1

                if state['stopped']:
                    # Frame: Show "Player stops and saves"
                    self.render_stop_announcement_frame(
                        state, f"{output_path}/frame_{frame_idx:04d}.png")
                    frame_idx += 1

                    # Frame: Commit progress (temp → permanent)
                    self.render_commit_frame(
                        state, f"{output_path}/frame_{frame_idx:04d}.png")
                    frame_idx += 1
            else:
                # Frame: Show BUST
                self.render_bust_announcement_frame(
                    state, f"{output_path}/frame_{frame_idx:04d}.png")
                frame_idx += 1

                # Frame: Remove active pegs
                self.render_bust_removal_frame(
                    state, f"{output_path}/frame_{frame_idx:04d}.png")
                frame_idx += 1

            if state_idx % 5 == 0:
                print(f"  Processed state {state_idx+1}/{len(self.history)}, generated {frame_idx} frames so far")

        print(f"\n✓ Generated {frame_idx} total frames")
        print(f"  At 2 fps: ~{frame_idx/2:.1f} seconds (~{frame_idx/120:.1f} minutes)")

    # ===== Frame rendering methods =====

    def render_turn_change_frame(self, state, output_file):
        """Show whose turn it is now"""
        fig = plt.figure(figsize=(18, 12), facecolor=self.bg_dark)
        gs = fig.add_gridspec(3, 3, height_ratios=[0.8, 5, 1.5],
                            width_ratios=[1, 6, 1], hspace=0.15, wspace=0.05)

        # Players
        ax_p1 = fig.add_subplot(gs[1, 0])
        self.draw_player_panel(ax_p1, self.player1, state, is_active=(state['current_player'] == self.player1))

        ax_board = fig.add_subplot(gs[0:2, 1])
        self.draw_board(ax_board, state, active_columns=set())

        ax_p2 = fig.add_subplot(gs[1, 2])
        self.draw_player_panel(ax_p2, self.player2, state, is_active=(state['current_player'] == self.player2))

        # Bottom: Big announcement
        ax_bottom = fig.add_subplot(gs[2, :])
        ax_bottom.set_xlim(0, 1)
        ax_bottom.set_ylim(0, 1)
        ax_bottom.set_facecolor(self.bg_panel)
        ax_bottom.axis('off')

        player_color = self.get_player_color(state['current_player'])
        ax_bottom.text(0.5, 0.5, f"▶ {state['current_player']}'s Turn",
                      ha='center', va='center', fontsize=28, fontweight='bold',
                      color=player_color)

        plt.tight_layout(pad=1.5)
        plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor=self.bg_dark)
        plt.close(fig)

    def render_dice_only_frame(self, state, output_file):
        """Show just the dice roll"""
        fig = plt.figure(figsize=(18, 12), facecolor=self.bg_dark)
        gs = fig.add_gridspec(3, 3, height_ratios=[0.8, 5, 1.5],
                            width_ratios=[1, 6, 1], hspace=0.15, wspace=0.05)

        ax_p1 = fig.add_subplot(gs[1, 0])
        self.draw_player_panel(ax_p1, self.player1, state, is_active=(state['current_player'] == self.player1))

        # Get active columns for highlighting
        if state['current_player'] == self.player1:
            active_cols = set(state['player1_active_columns'])
        else:
            active_cols = set(state['player2_active_columns'])

        ax_board = fig.add_subplot(gs[0:2, 1])
        self.draw_board(ax_board, state, active_columns=active_cols)

        ax_p2 = fig.add_subplot(gs[1, 2])
        self.draw_player_panel(ax_p2, self.player2, state, is_active=(state['current_player'] == self.player2))

        # Bottom: Show dice
        ax_bottom = fig.add_subplot(gs[2, :])
        self.draw_dice_panel(ax_bottom, state, show_options=0, show_chosen=False)

        plt.tight_layout(pad=1.5)
        plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor=self.bg_dark)
        plt.close(fig)

    def render_option_frame(self, state, option_num, output_file):
        """Show options progressively (1, then 1-2, then 1-2-3)"""
        fig = plt.figure(figsize=(18, 12), facecolor=self.bg_dark)
        gs = fig.add_gridspec(3, 3, height_ratios=[0.8, 5, 1.5],
                            width_ratios=[1, 6, 1], hspace=0.15, wspace=0.05)

        ax_p1 = fig.add_subplot(gs[1, 0])
        self.draw_player_panel(ax_p1, self.player1, state, is_active=(state['current_player'] == self.player1))

        if state['current_player'] == self.player1:
            active_cols = set(state['player1_active_columns'])
        else:
            active_cols = set(state['player2_active_columns'])

        ax_board = fig.add_subplot(gs[0:2, 1])
        self.draw_board(ax_board, state, active_columns=active_cols)

        ax_p2 = fig.add_subplot(gs[1, 2])
        self.draw_player_panel(ax_p2, self.player2, state, is_active=(state['current_player'] == self.player2))

        ax_bottom = fig.add_subplot(gs[2, :])
        self.draw_dice_panel(ax_bottom, state, show_options=option_num, show_chosen=False)

        plt.tight_layout(pad=1.5)
        plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor=self.bg_dark)
        plt.close(fig)

    def render_chosen_frame(self, state, output_file):
        """Highlight the chosen option"""
        fig = plt.figure(figsize=(18, 12), facecolor=self.bg_dark)
        gs = fig.add_gridspec(3, 3, height_ratios=[0.8, 5, 1.5],
                            width_ratios=[1, 6, 1], hspace=0.15, wspace=0.05)

        ax_p1 = fig.add_subplot(gs[1, 0])
        self.draw_player_panel(ax_p1, self.player1, state, is_active=(state['current_player'] == self.player1))

        if state['current_player'] == self.player1:
            active_cols = set(state['player1_active_columns'])
        else:
            active_cols = set(state['player2_active_columns'])

        ax_board = fig.add_subplot(gs[0:2, 1])
        self.draw_board(ax_board, state, active_columns=active_cols)

        ax_p2 = fig.add_subplot(gs[1, 2])
        self.draw_player_panel(ax_p2, self.player2, state, is_active=(state['current_player'] == self.player2))

        ax_bottom = fig.add_subplot(gs[2, :])
        self.draw_dice_panel(ax_bottom, state, show_options=3, show_chosen=True)

        plt.tight_layout(pad=1.5)
        plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor=self.bg_dark)
        plt.close(fig)

    def render_peg_animation_frame(self, state, anim_step, output_file):
        """Animate pegs moving (3 steps)"""
        fig = plt.figure(figsize=(18, 12), facecolor=self.bg_dark)
        gs = fig.add_gridspec(3, 3, height_ratios=[0.8, 5, 1.5],
                            width_ratios=[1, 6, 1], hspace=0.15, wspace=0.05)

        ax_p1 = fig.add_subplot(gs[1, 0])
        self.draw_player_panel(ax_p1, self.player1, state, is_active=(state['current_player'] == self.player1))

        if state['current_player'] == self.player1:
            active_cols = set(state['player1_active_columns'])
        else:
            active_cols = set(state['player2_active_columns'])

        ax_board = fig.add_subplot(gs[0:2, 1])
        self.draw_board(ax_board, state, active_columns=active_cols, anim_progress=(anim_step+1)/3)

        ax_p2 = fig.add_subplot(gs[1, 2])
        self.draw_player_panel(ax_p2, self.player2, state, is_active=(state['current_player'] == self.player2))

        ax_bottom = fig.add_subplot(gs[2, :])
        self.draw_commentary_panel(ax_bottom, "Moving pegs...")

        plt.tight_layout(pad=1.5)
        plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor=self.bg_dark)
        plt.close(fig)

    def render_after_move_frame(self, state, output_file):
        """Show board after move is complete"""
        fig = plt.figure(figsize=(18, 12), facecolor=self.bg_dark)
        gs = fig.add_gridspec(3, 3, height_ratios=[0.8, 5, 1.5],
                            width_ratios=[1, 6, 1], hspace=0.15, wspace=0.05)

        ax_p1 = fig.add_subplot(gs[1, 0])
        self.draw_player_panel(ax_p1, self.player1, state, is_active=(state['current_player'] == self.player1))

        if state['current_player'] == self.player1:
            active_cols = set(state['player1_active_columns'])
        else:
            active_cols = set(state['player2_active_columns'])

        ax_board = fig.add_subplot(gs[0:2, 1])
        self.draw_board(ax_board, state, active_columns=active_cols, anim_progress=1.0)

        ax_p2 = fig.add_subplot(gs[1, 2])
        self.draw_player_panel(ax_p2, self.player2, state, is_active=(state['current_player'] == self.player2))

        ax_bottom = fig.add_subplot(gs[2, :])
        self.draw_commentary_panel(ax_bottom, state['decision_reasoning'])

        plt.tight_layout(pad=1.5)
        plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor=self.bg_dark)
        plt.close(fig)

    def render_stop_announcement_frame(self, state, output_file):
        """Show 'Player stops and saves'"""
        fig = plt.figure(figsize=(18, 12), facecolor=self.bg_dark)
        gs = fig.add_gridspec(3, 3, height_ratios=[0.8, 5, 1.5],
                            width_ratios=[1, 6, 1], hspace=0.15, wspace=0.05)

        ax_p1 = fig.add_subplot(gs[1, 0])
        self.draw_player_panel(ax_p1, self.player1, state, is_active=(state['current_player'] == self.player1))

        if state['current_player'] == self.player1:
            active_cols = set(state['player1_active_columns'])
        else:
            active_cols = set(state['player2_active_columns'])

        ax_board = fig.add_subplot(gs[0:2, 1])
        self.draw_board(ax_board, state, active_columns=active_cols, anim_progress=1.0)

        ax_p2 = fig.add_subplot(gs[1, 2])
        self.draw_player_panel(ax_p2, self.player2, state, is_active=(state['current_player'] == self.player2))

        ax_bottom = fig.add_subplot(gs[2, :])
        self.draw_commentary_panel(ax_bottom, f"✋ {state['current_player']} STOPS and saves progress!",
                                   color='#4CAF50', size=24)

        plt.tight_layout(pad=1.5)
        plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor=self.bg_dark)
        plt.close(fig)

    def render_commit_frame(self, state, output_file):
        """Show temp progress becoming permanent"""
        # For this frame, we need to look ahead to see the final permanent state
        # But since we're showing the current state, we'll just highlight the transition
        fig = plt.figure(figsize=(18, 12), facecolor=self.bg_dark)
        gs = fig.add_gridspec(3, 3, height_ratios=[0.8, 5, 1.5],
                            width_ratios=[1, 6, 1], hspace=0.15, wspace=0.05)

        ax_p1 = fig.add_subplot(gs[1, 0])
        self.draw_player_panel(ax_p1, self.player1, state, is_active=(state['current_player'] == self.player1))

        ax_board = fig.add_subplot(gs[0:2, 1])
        self.draw_board(ax_board, state, active_columns=set(), anim_progress=1.0,
                       show_commit=True)

        ax_p2 = fig.add_subplot(gs[1, 2])
        self.draw_player_panel(ax_p2, self.player2, state, is_active=(state['current_player'] == self.player2))

        ax_bottom = fig.add_subplot(gs[2, :])
        self.draw_commentary_panel(ax_bottom, "Progress saved!", color='#4CAF50')

        plt.tight_layout(pad=1.5)
        plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor=self.bg_dark)
        plt.close(fig)

    def render_bust_announcement_frame(self, state, output_file):
        """Show BUST!"""
        fig = plt.figure(figsize=(18, 12), facecolor=self.bg_dark)
        gs = fig.add_gridspec(3, 3, height_ratios=[0.8, 5, 1.5],
                            width_ratios=[1, 6, 1], hspace=0.15, wspace=0.05)

        ax_p1 = fig.add_subplot(gs[1, 0])
        self.draw_player_panel(ax_p1, self.player1, state, is_active=(state['current_player'] == self.player1))

        if state['current_player'] == self.player1:
            active_cols = set(state['player1_active_columns'])
        else:
            active_cols = set(state['player2_active_columns'])

        ax_board = fig.add_subplot(gs[0:2, 1])
        self.draw_board(ax_board, state, active_columns=active_cols)

        ax_p2 = fig.add_subplot(gs[1, 2])
        self.draw_player_panel(ax_p2, self.player2, state, is_active=(state['current_player'] == self.player2))

        ax_bottom = fig.add_subplot(gs[2, :])
        ax_bottom.set_xlim(0, 1)
        ax_bottom.set_ylim(0, 1)
        ax_bottom.set_facecolor(self.bg_panel)
        ax_bottom.axis('off')

        # Show dice
        dice = state['roll']
        dice_str = '  '.join([f'[{d}]' for d in dice])
        ax_bottom.text(0.5, 0.7, f"Rolled: {dice_str}",
                      ha='center', va='center', fontsize=20, fontweight='bold',
                      color='white', family='monospace')

        ax_bottom.text(0.5, 0.3, f"💥 BUST! No valid moves!",
                      ha='center', va='center', fontsize=26, fontweight='bold',
                      color='#FF3333')

        plt.tight_layout(pad=1.5)
        plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor=self.bg_dark)
        plt.close(fig)

    def render_bust_removal_frame(self, state, output_file):
        """Show active pegs being removed"""
        fig = plt.figure(figsize=(18, 12), facecolor=self.bg_dark)
        gs = fig.add_gridspec(3, 3, height_ratios=[0.8, 5, 1.5],
                            width_ratios=[1, 6, 1], hspace=0.15, wspace=0.05)

        ax_p1 = fig.add_subplot(gs[1, 0])
        self.draw_player_panel(ax_p1, self.player1, state, is_active=(state['current_player'] == self.player1))

        ax_board = fig.add_subplot(gs[0:2, 1])
        self.draw_board(ax_board, state, active_columns=set(), show_bust_removed=True)

        ax_p2 = fig.add_subplot(gs[1, 2])
        self.draw_player_panel(ax_p2, self.player2, state, is_active=(state['current_player'] == self.player2))

        ax_bottom = fig.add_subplot(gs[2, :])
        if state['current_player'] == self.player1:
            lost_steps = sum(state['player1_temporary'].values())
        else:
            lost_steps = sum(state['player2_temporary'].values())
        self.draw_commentary_panel(ax_bottom, f"Lost {lost_steps} unsaved steps",
                                   color='#FF3333')

        plt.tight_layout(pad=1.5)
        plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor=self.bg_dark)
        plt.close(fig)

    # ===== Component drawing methods =====

    def draw_player_panel(self, ax, player_name, state, is_active):
        """Draw player name and status"""
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_facecolor(self.bg_panel)
        ax.axis('off')

        color = self.get_player_color(player_name)

        # Completed columns count
        if player_name == self.player1:
            completed = sum(1 for c in range(2, 13)
                          if state['player1_permanent'].get(str(c), 0) >= self.column_length[c])
        else:
            completed = sum(1 for c in range(2, 13)
                          if state['player2_permanent'].get(str(c), 0) >= self.column_length[c])

        # Name
        ax.text(0.5, 0.6, player_name[:10], ha='center', va='center',
               fontsize=18, fontweight='bold', color=color)

        # Score
        ax.text(0.5, 0.4, f"{completed}/3", ha='center', va='center',
               fontsize=24, fontweight='bold', color='white')

        # Active indicator
        if is_active:
            ax.text(0.5, 0.2, '▶', ha='center', va='center',
                   fontsize=20, color=color)

    def draw_board(self, ax, state, active_columns: Set[int],
                   anim_progress: float = 0.0, show_commit: bool = False,
                   show_bust_removed: bool = False):
        """Draw the game board"""
        ax.set_xlim(-0.5, 11.5)
        ax.set_ylim(-1, 15)
        ax.set_facecolor(self.bg_dark)
        ax.axis('off')

        # Determine completed columns
        p1_completed = set(c for c in range(2, 13)
                          if state['player1_permanent'].get(str(c), 0) >= self.column_length[c])
        p2_completed = set(c for c in range(2, 13)
                          if state['player2_permanent'].get(str(c), 0) >= self.column_length[c])

        for i, col in enumerate(self.columns):
            length = self.column_length[col]

            # Column number at bottom
            ax.text(i, -0.5, str(col), ha='center', va='center',
                   fontsize=18, fontweight='bold', color='white',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='#3C3C3C',
                            edgecolor='white', linewidth=2))

            # Determine column styling
            if col in p1_completed:
                bg_color = self.color_p1
                bg_alpha = 0.2
                border_color = self.color_p1
                border_width = 3
            elif col in p2_completed:
                bg_color = self.color_p2
                bg_alpha = 0.2
                border_color = self.color_p2
                border_width = 3
            else:
                bg_color = '#444444'
                bg_alpha = 0.1
                border_color = '#666666'
                border_width = 1

            # Highlight active columns
            if col in active_columns:
                border_color = '#FFD700'  # Gold
                border_width = 4
                bg_alpha = 0.3

            # Draw column track
            for j in range(length):
                y = j
                rect = mpatches.Rectangle((i-0.4, y), 0.8, 0.9,
                                        linewidth=border_width,
                                        edgecolor=border_color,
                                        facecolor=bg_color, alpha=bg_alpha)
                ax.add_patch(rect)

            # Draw permanent progress
            p1_perm = state['player1_permanent'].get(str(col), 0)
            if p1_perm > 0:
                for j in range(min(p1_perm, length)):
                    y = j + 0.45
                    circle = mpatches.Circle((i-0.15, y), 0.25, color=self.color_p1,
                                           ec='white', linewidth=2, zorder=3)
                    ax.add_patch(circle)

            p2_perm = state['player2_permanent'].get(str(col), 0)
            if p2_perm > 0:
                for j in range(min(p2_perm, length)):
                    y = j + 0.45
                    circle = mpatches.Circle((i+0.15, y), 0.25, color=self.color_p2,
                                           ec='white', linewidth=2, zorder=3)
                    ax.add_patch(circle)

            # Draw temporary progress (white circles with colored border)
            if not show_bust_removed:
                if col in state['player1_active_columns']:
                    temp = state['player1_temporary'].get(str(col), 0)
                    if temp > 0:
                        # Animate from p1_perm to p1_perm + temp
                        current_pos = p1_perm + temp * anim_progress
                        y = current_pos - 1 + 0.45
                        circle = mpatches.Circle((i-0.15, y), 0.25,
                                               facecolor='white',
                                               ec=self.color_p1, linewidth=3, zorder=5)
                        ax.add_patch(circle)

                if col in state['player2_active_columns']:
                    temp = state['player2_temporary'].get(str(col), 0)
                    if temp > 0:
                        current_pos = p2_perm + temp * anim_progress
                        y = current_pos - 1 + 0.45
                        circle = mpatches.Circle((i+0.15, y), 0.25,
                                               facecolor='white',
                                               ec=self.color_p2, linewidth=3, zorder=5)
                        ax.add_patch(circle)

    def draw_dice_panel(self, ax, state, show_options: int, show_chosen: bool):
        """Draw dice and options panel"""
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_facecolor(self.bg_panel)
        ax.axis('off')

        dice = state['roll']
        pairings = state['available_pairings']
        chosen = state['chosen_pairing']

        y = 0.85

        # Show rolled dice (always)
        ax.text(0.5, y, "Rolled:", ha='center', fontsize=16, color='#AAAAAA', fontweight='bold')
        y -= 0.1

        dice_str = '  '.join([f'[{d}]' for d in dice])
        ax.text(0.5, y, dice_str, ha='center', fontsize=22, fontweight='bold',
               color='white', family='monospace')
        y -= 0.15

        # Show options progressively
        for opt_idx in range(min(show_options, 3)):
            pairing = pairings[opt_idx]
            colors = self.pairing_colors[opt_idx]

            # Determine if this option is valid
            # (For simplicity, we'll show all - in real game would check validity)

            # Build colored dice string
            dice_colored = []
            if opt_idx == 0:
                pair1, pair2 = (0, 1), (2, 3)
            elif opt_idx == 1:
                pair1, pair2 = (0, 2), (1, 3)
            else:
                pair1, pair2 = (0, 3), (1, 2)

            # Background highlight if chosen
            is_chosen = (show_chosen and pairing == chosen)
            if is_chosen:
                highlight = mpatches.FancyBboxPatch((0.05, y-0.05), 0.9, 0.08,
                                                   boxstyle="round,pad=0.01",
                                                   facecolor='#FFD700', alpha=0.3,
                                                   edgecolor='#FFD700', linewidth=3)
                ax.add_patch(highlight)

            # Option label
            label = "✓ " if is_chosen else ""
            ax.text(0.08, y, f"{label}Option {opt_idx+1}:", ha='left', fontsize=14,
                   color='white', fontweight='bold' if is_chosen else 'normal')

            # Draw colored dice
            x_start = 0.35
            for d_idx, d in enumerate(dice):
                x = x_start + d_idx * 0.08
                if d_idx in pair1:
                    color = colors[0]
                elif d_idx in pair2:
                    color = colors[1]
                else:
                    color = '#888888'
                ax.text(x, y, f'[{d}]', ha='center', fontsize=16, fontweight='bold',
                       color=color, family='monospace')

            # Show sums
            sum1, sum2 = pairing
            ax.text(0.7, y, f'→ ', ha='center', fontsize=14, color='white')
            ax.text(0.75, y, f'{sum1}', ha='center', fontsize=16, fontweight='bold',
                   color=colors[0])
            ax.text(0.8, y, ',', ha='center', fontsize=14, color='white')
            ax.text(0.85, y, f'{sum2}', ha='center', fontsize=16, fontweight='bold',
                   color=colors[1])

            y -= 0.12

    def draw_commentary_panel(self, ax, text, color='white', size=16):
        """Draw commentary text"""
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_facecolor(self.bg_panel)
        ax.axis('off')

        ax.text(0.5, 0.5, text, ha='center', va='center',
               fontsize=size, fontweight='bold', color=color, wrap=True)


if __name__ == '__main__':
    game_file = Path(__file__).parent / 'dramatic_game.json'
    output_dir = Path(__file__).parent / 'game_frames_v3'

    generator = GameFrameGeneratorV3(game_file)
    generator.generate_all_frames(output_dir)

    print("\n✓ Done! Educational frames are ready.")
    print(f"  To create video: ffmpeg -framerate 2 -i {output_dir}/frame_%04d.png -vf 'scale=trunc(iw/2)*2:trunc(ih/2)*2' -c:v libx264 -pix_fmt yuv420p -crf 20 game_replay_v3.mp4")
