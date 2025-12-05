#!/usr/bin/env python3
"""
Generate individual PNG frames from game replay
These can be stitched into video/GIF later
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path


class GameFrameGenerator:
    """Generates PNG frames from game replay"""

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

    def render_frame(self, state_idx, output_file):
        """Render a single frame to PNG"""
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

        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='#FAFAFA')
        plt.close(fig)

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

            # Column track (gray boxes)
            for j in range(length):
                y = 13 - j
                rect = mpatches.Rectangle((i-0.4, y-0.4), 0.8, 0.8,
                                        linewidth=1, edgecolor='#CCC',
                                        facecolor='#F5F5F5')
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

            # Temporary markers (dashed circles)
            if col in state['player1_active_columns']:
                temp_steps = state['player1_temporary'].get(str(col), 0)
                if temp_steps > 0:
                    start_y = 13 - p1_prog
                    end_y = start_y - temp_steps
                    # Draw line showing progress
                    ax.plot([i-0.15, i-0.15], [start_y, end_y],
                           color=self.color_p1, linewidth=4, alpha=0.5, zorder=2)
                    # Draw hollow circle at end
                    circle = mpatches.Circle((i-0.15, end_y), 0.25,
                                           facecolor='white',
                                           ec=self.color_p1, linewidth=3,
                                           zorder=4)
                    ax.add_patch(circle)

            if col in state['player2_active_columns']:
                temp_steps = state['player2_temporary'].get(str(col), 0)
                if temp_steps > 0:
                    start_y = 13 - p2_prog
                    end_y = start_y - temp_steps
                    ax.plot([i+0.15, i+0.15], [start_y, end_y],
                           color=self.color_p2, linewidth=4, alpha=0.5, zorder=2)
                    circle = mpatches.Circle((i+0.15, end_y), 0.25,
                                           facecolor='white',
                                           ec=self.color_p2, linewidth=3,
                                           zorder=4)
                    ax.add_patch(circle)

        # Legend
        p1_patch = mpatches.Patch(color=self.color_p1, label=f'{self.player1} (Blue)')
        p2_patch = mpatches.Patch(color=self.color_p2, label=f'{self.player2} (Orange)')
        temp_patch = mpatches.Patch(facecolor='white', edgecolor='#666',
                                   linewidth=2, label='Unsaved Progress')
        ax.legend(handles=[p1_patch, p2_patch, temp_patch],
                 loc='upper right', fontsize=11, frameon=True,
                 fancybox=True, shadow=True)

    def draw_dice_and_decision(self, ax, state):
        """Draw dice roll and decision info"""
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # Dice
        dice = state['roll']
        dice_str = '  '.join([f'[{d}]' for d in dice])
        ax.text(0.05, 0.75, f"Dice Roll: {dice_str}", fontsize=16,
               fontweight='bold', family='monospace')

        # Available pairings
        pairings = state['available_pairings']
        pairing_strs = [f"{p[0]}+{p[1]}" for p in pairings]
        ax.text(0.05, 0.55, f"Available: {' / '.join(pairing_strs)}",
               fontsize=13)

        # Chosen pairing
        if state['chosen_pairing']:
            chosen = state['chosen_pairing']
            color = self.color_p1 if state['current_player'] == self.player1 else self.color_p2
            ax.text(0.05, 0.35, f"Chosen: {chosen[0]}+{chosen[1]} ✓",
                   fontsize=15, fontweight='bold', color=color)

        # EV calculation if available
        if state['ev_calculation'] is not None:
            ev_color = '#06A77D' if state['ev_calculation'] > 0 else '#C73E1D'
            ax.text(0.05, 0.15, f"Expected Value: {state['ev_calculation']:.2f}",
                   fontsize=13, fontweight='bold', color=ev_color)

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

        # Add emoji based on state
        if state['busted']:
            reasoning = f"💥 {reasoning}"
        elif state['stopped']:
            reasoning = f"✋ {reasoning}"

        ax.text(0.5, 0.5, reasoning, ha='center', va='center',
               fontsize=13, wrap=True, fontweight='600')

    def generate_all_frames(self, output_dir):
        """Generate all frames"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        print(f"Generating {len(self.history)} frames...")

        for i, state in enumerate(self.history):
            if i % 5 == 0:
                print(f"  Frame {i+1}/{len(self.history)}...")

            output_file = output_path / f"frame_{i:03d}.png"
            self.render_frame(i, str(output_file))

        print(f"✓ All frames saved to {output_path}")

        # Also generate a summary frame showing key moments
        self.generate_summary_frame(output_path)

    def generate_summary_frame(self, output_path):
        """Generate a single summary image showing key moments"""
        # Find key moments: start, busts, end
        key_frames = [0]  # Start

        # Find busts
        for i, state in enumerate(self.history):
            if state['busted']:
                key_frames.append(i)

        key_frames.append(len(self.history) - 1)  # End

        # Render key frames side by side
        fig, axes = plt.subplots(1, min(4, len(key_frames)), figsize=(20, 6), facecolor='#FAFAFA')

        if len(key_frames) == 1:
            axes = [axes]

        for idx, (ax, frame_idx) in enumerate(zip(axes, key_frames[:4])):
            state = self.history[frame_idx]
            ax.set_title(f"Turn {state['turn_number']}", fontsize=14, fontweight='bold')
            self.draw_mini_board(ax, state)

        plt.tight_layout()
        summary_file = output_path / "summary.png"
        plt.savefig(summary_file, dpi=150, bbox_inches='tight', facecolor='#FAFAFA')
        plt.close(fig)
        print(f"✓ Summary frame saved: {summary_file}")

    def draw_mini_board(self, ax, state):
        """Draw a simplified board for summary view"""
        ax.set_xlim(-0.5, 11.5)
        ax.set_ylim(0, 14)
        ax.axis('off')

        for i, col in enumerate(self.columns):
            length = self.column_length[col]

            # Column header
            ax.text(i, 13, str(col), ha='center', va='bottom', fontsize=10)

            # Draw progress bars
            p1_prog = state['player1_permanent'].get(str(col), 0)
            p2_prog = state['player2_permanent'].get(str(col), 0)

            if p1_prog > 0:
                ax.bar(i-0.2, p1_prog, width=0.3, bottom=0,
                      color=self.color_p1, alpha=0.7)

            if p2_prog > 0:
                ax.bar(i+0.2, p2_prog, width=0.3, bottom=0,
                      color=self.color_p2, alpha=0.7)

            # Show max height
            ax.plot([i-0.4, i+0.4], [length, length], 'k--', linewidth=1, alpha=0.3)


if __name__ == '__main__':
    game_file = Path(__file__).parent / 'dramatic_game.json'
    output_dir = Path(__file__).parent / 'game_frames'

    generator = GameFrameGenerator(game_file)
    generator.generate_all_frames(output_dir)

    print("\n✓ Done! Frames are ready.")
    print(f"  To create video: ffmpeg -framerate 2 -i game_frames/frame_%03d.png -c:v libx264 -pix_fmt yuv420p game_replay.mp4")
    print(f"  To create GIF: convert -delay 50 game_frames/frame_*.png game_replay.gif")
