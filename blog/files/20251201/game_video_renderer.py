#!/usr/bin/env python3
"""
Can't Stop Game Video Renderer
Creates animated video from game replay JSON
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FFMpegWriter
import numpy as np
from pathlib import Path


class GameVideoRenderer:
    """Renders Can't Stop game as video"""

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

        # Colors
        self.color_p1 = '#2E86AB'  # Blue
        self.color_p2 = '#F18F01'  # Orange
        self.color_temp = '#CCCCCC'  # Gray
        self.color_completed = '#06A77D'  # Green

    def render_frame(self, state_idx):
        """Render a single frame"""
        state = self.history[state_idx]

        fig = plt.figure(figsize=(16, 10), facecolor='#FAFAFA')
        gs = fig.add_gridspec(4, 1, height_ratios=[0.5, 3, 1.5, 1], hspace=0.3)

        # Title
        ax_title = fig.add_subplot(gs[0])
        ax_title.axis('off')
        turn_text = f"Turn {state['turn_number']} - {state['current_player']}'s Turn"
        ax_title.text(0.5, 0.5, turn_text, ha='center', va='center',
                     fontsize=20, fontweight='bold')

        # Main board
        ax_board = fig.add_subplot(gs[1])
        self.draw_board(ax_board, state)

        # Dice and decision
        ax_dice = fig.add_subplot(gs[2])
        self.draw_dice_and_decision(ax_dice, state)

        # Commentary
        ax_commentary = fig.add_subplot(gs[3])
        self.draw_commentary(ax_commentary, state)

        return fig

    def draw_board(self, ax, state):
        """Draw the game board"""
        ax.set_xlim(-0.5, 11.5)
        ax.set_ylim(-2, 15)
        ax.axis('off')

        # Draw each column
        for i, col in enumerate(self.columns):
            length = self.column_length[col]

            # Column header
            ax.text(i, 14, str(col), ha='center', va='center',
                   fontsize=14, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                            edgecolor='#333', linewidth=2))

            # Column track
            for j in range(length):
                y = 13 - j
                rect = mpatches.Rectangle((i-0.4, y-0.4), 0.8, 0.8,
                                        linewidth=1, edgecolor='#CCC',
                                        facecolor='white')
                ax.add_patch(rect)

            # Player 1 permanent progress
            p1_prog = state['player1_permanent'].get(str(col), 0)
            for j in range(min(p1_prog, length)):
                y = 13 - j
                circle = mpatches.Circle((i, y), 0.3, color=self.color_p1,
                                       ec='#333', linewidth=2, zorder=3)
                ax.add_patch(circle)

            # Player 2 permanent progress
            p2_prog = state['player2_permanent'].get(str(col), 0)
            for j in range(min(p2_prog, length)):
                y = 13 - j
                circle = mpatches.Circle((i, y), 0.3, color=self.color_p2,
                                       ec='#333', linewidth=2, zorder=3)
                ax.add_patch(circle)

            # Temporary markers
            if col in state['player1_active_columns']:
                temp_steps = state['player1_temporary'].get(str(col), 0)
                if temp_steps > 0:
                    y = 13 - p1_prog - temp_steps
                    circle = mpatches.Circle((i-0.15, y), 0.25,
                                           facecolor='none',
                                           ec=self.color_p1, linewidth=3,
                                           linestyle='--', zorder=4)
                    ax.add_patch(circle)

            if col in state['player2_active_columns']:
                temp_steps = state['player2_temporary'].get(str(col), 0)
                if temp_steps > 0:
                    y = 13 - p2_prog - temp_steps
                    circle = mpatches.Circle((i+0.15, y), 0.25,
                                           facecolor='none',
                                           ec=self.color_p2, linewidth=3,
                                           linestyle='--', zorder=4)
                    ax.add_patch(circle)

        # Legend
        p1_patch = mpatches.Patch(color=self.color_p1, label=self.player1)
        p2_patch = mpatches.Patch(color=self.color_p2, label=self.player2)
        temp_patch = mpatches.Patch(facecolor='none', edgecolor='#666',
                                   linestyle='--', label='Temporary')
        ax.legend(handles=[p1_patch, p2_patch, temp_patch],
                 loc='upper right', fontsize=12, frameon=True,
                 fancybox=True, shadow=True)

    def draw_dice_and_decision(self, ax, state):
        """Draw dice roll and decision info"""
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # Dice
        dice = state['roll']
        dice_str = '  '.join([f'[{d}]' for d in dice])
        ax.text(0.05, 0.7, f"Dice: {dice_str}", fontsize=16,
               fontweight='bold', family='monospace')

        # Available pairings
        pairings = state['available_pairings']
        pairing_strs = [f"{p[0]}+{p[1]}" for p in pairings]
        ax.text(0.05, 0.5, f"Options: {' / '.join(pairing_strs)}",
               fontsize=14)

        # Chosen pairing
        if state['chosen_pairing']:
            chosen = state['chosen_pairing']
            ax.text(0.05, 0.3, f"Choice: {chosen[0]}+{chosen[1]} ✓",
                   fontsize=14, fontweight='bold', color=self.color_p1
                   if state['current_player'] == self.player1 else self.color_p2)

        # EV calculation if available
        if state['ev_calculation'] is not None:
            ev_color = '#06A77D' if state['ev_calculation'] > 0 else '#C73E1D'
            ax.text(0.05, 0.1, f"EV = {state['ev_calculation']:.2f}",
                   fontsize=14, fontweight='bold', color=ev_color)

    def draw_commentary(self, ax, state):
        """Draw commentary text"""
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # Background box
        box = mpatches.FancyBboxPatch((0.02, 0.1), 0.96, 0.8,
                                     boxstyle="round,pad=0.02",
                                     facecolor='#FFF8DC',
                                     edgecolor='#333', linewidth=2)
        ax.add_patch(box)

        # Commentary text
        reasoning = state['decision_reasoning']

        # Add bust/stop emoji
        if state['busted']:
            reasoning = f"💥 {reasoning}"
        elif state['stopped']:
            reasoning = f"✋ {reasoning}"

        ax.text(0.5, 0.5, reasoning, ha='center', va='center',
               fontsize=14, wrap=True, fontweight='600')

    def create_video(self, output_file='game_replay.mp4', fps=2):
        """Create video from all frames"""
        print(f"Creating video with {len(self.history)} frames...")

        # Setup video writer
        metadata = dict(title='Can\'t Stop Game Replay',
                       artist='Claude',
                       comment='GreedyUntil1Col vs ExpectedValueMax')

        writer = FFMpegWriter(fps=fps, metadata=metadata,
                            extra_args=['-vcodec', 'libx264'])

        # Create first frame to get figure
        fig = self.render_frame(0)

        with writer.saving(fig, output_file, dpi=150):
            for i, state in enumerate(self.history):
                if i % 5 == 0:
                    print(f"  Rendering frame {i+1}/{len(self.history)}...")

                plt.clf()  # Clear figure
                fig = self.render_frame(i)
                writer.grab_frame(facecolor='#FAFAFA')
                plt.close(fig)

        print(f"✓ Video saved to {output_file}")


if __name__ == '__main__':
    game_file = Path(__file__).parent / 'dramatic_game.json'
    output_video = Path(__file__).parent / 'game_replay.mp4'

    renderer = GameVideoRenderer(game_file)
    renderer.create_video(str(output_video), fps=2)

    print(f"\n✓ Done! Watch the game at: {output_video}")
