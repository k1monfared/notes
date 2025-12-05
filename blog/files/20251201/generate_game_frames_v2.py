#!/usr/bin/env python3
"""
Generate game frames v2 - matches actual Can't Stop board design
- Bottom-to-top progression
- Clear saved state display
- Player names always visible
- Variable frame timing
- Columns colored by owner
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path


class GameFrameGeneratorV2:
    """Generates PNG frames matching actual Can't Stop board"""

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

        # Colors - more vibrant
        self.color_p1 = '#1E6FBF'  # Bright Blue
        self.color_p2 = '#FF6B35'  # Bright Orange
        self.color_neutral = '#E8E8E8'  # Light gray for empty
        self.color_track = '#FFFFFF'  # White for track

    def get_frame_duration(self, state):
        """Calculate how long this frame should be shown (in frames @ 2fps)"""
        # Base duration
        duration = 5  # 2.5 seconds

        # Hold longer on important moments
        if state['busted']:
            duration = 12  # 6 seconds for busts
        elif state['stopped']:
            duration = 8  # 4 seconds for stops

        # Hold longer if EV calculation shown
        if state['ev_calculation'] is not None and abs(state['ev_calculation']) < 0.5:
            duration = 10  # 5 seconds for close EV decisions

        return duration

    def render_frame(self, state_idx, output_file):
        """Render a single frame to PNG"""
        state = self.history[state_idx]

        fig = plt.figure(figsize=(18, 12), facecolor='#2C2C2C')  # Dark background
        gs = fig.add_gridspec(3, 3, height_ratios=[0.8, 5, 1.5],
                            width_ratios=[1, 6, 1], hspace=0.15, wspace=0.05)

        # Player 1 name (left side)
        ax_p1 = fig.add_subplot(gs[1, 0])
        self.draw_player_name(ax_p1, self.player1, self.color_p1,
                             is_active=state['current_player'] == self.player1,
                             completed_count=len([c for c in range(2, 13)
                                                if state['player1_permanent'].get(str(c), 0)
                                                >= self.column_length[c]]))

        # Main board (center)
        ax_board = fig.add_subplot(gs[0:2, 1])
        self.draw_board(ax_board, state)

        # Player 2 name (right side)
        ax_p2 = fig.add_subplot(gs[1, 2])
        self.draw_player_name(ax_p2, self.player2, self.color_p2,
                             is_active=state['current_player'] == self.player2,
                             completed_count=len([c for c in range(2, 13)
                                                if state['player2_permanent'].get(str(c), 0)
                                                >= self.column_length[c]]))

        # Dice and decision (bottom)
        ax_bottom = fig.add_subplot(gs[2, :])
        self.draw_dice_and_commentary(ax_bottom, state)

        plt.tight_layout(pad=1.5)
        plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='#2C2C2C')
        plt.close(fig)

    def draw_player_name(self, ax, name, color, is_active, completed_count):
        """Draw player name vertically with status"""
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_facecolor('#2C2C2C')
        ax.axis('off')

        # Background box if active
        if is_active:
            box = mpatches.FancyBboxPatch((0.05, 0.2), 0.9, 0.6,
                                        boxstyle="round,pad=0.05",
                                        facecolor=color, alpha=0.3,
                                        edgecolor=color, linewidth=4)
            ax.add_patch(box)

        # Player name (rotated if needed)
        name_short = name.replace('GreedyUntil', 'G1').replace('ExpectedValueMax', 'EV')
        ax.text(0.5, 0.6, name_short, ha='center', va='center',
               fontsize=16, fontweight='bold', color=color, rotation=0)

        # Completed columns count
        ax.text(0.5, 0.35, f'{completed_count}/3', ha='center', va='center',
               fontsize=20, fontweight='bold', color='white')

        # Active indicator
        if is_active:
            ax.text(0.5, 0.15, '▶', ha='center', va='center',
                   fontsize=24, color=color)

    def draw_board(self, ax, state):
        """Draw the game board - BOTTOM TO TOP progression, simplified"""
        ax.set_xlim(-0.5, 11.5)
        ax.set_ylim(-1, 15)
        ax.set_facecolor('#1A1A1A')
        ax.axis('off')

        # Determine column ownership
        p1_owned = set()
        p2_owned = set()

        for col in self.columns:
            p1_prog = state['player1_permanent'].get(str(col), 0)
            p2_prog = state['player2_permanent'].get(str(col), 0)

            if p1_prog >= self.column_length[col]:
                p1_owned.add(col)
            elif p2_prog >= self.column_length[col]:
                p2_owned.add(col)

        # Draw each column
        for i, col in enumerate(self.columns):
            length = self.column_length[col]

            # Column number at bottom
            ax.text(i, -0.5, str(col), ha='center', va='center',
                   fontsize=16, fontweight='bold', color='white',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='#3C3C3C',
                            edgecolor='white', linewidth=2))

            # Determine column color based on ownership
            if col in p1_owned:
                col_color = self.color_p1
                border_color = self.color_p1
                border_width = 3
                col_alpha = 0.25  # Dimmed background for completed
            elif col in p2_owned:
                col_color = self.color_p2
                border_color = self.color_p2
                border_width = 3
                col_alpha = 0.25  # Dimmed background for completed
            else:
                col_color = self.color_neutral
                border_color = '#666666'
                border_width = 1
                col_alpha = 0.15

            # Draw column track (BOTTOM TO TOP)
            for j in range(length):
                y = j  # Start from bottom (0) and go up

                # Track space
                rect = mpatches.Rectangle((i-0.4, y), 0.8, 0.9,
                                        linewidth=border_width,
                                        edgecolor=border_color,
                                        facecolor=col_color, alpha=col_alpha)
                ax.add_patch(rect)

            # Player 1: Show only topmost saved position (if any)
            p1_prog = state['player1_permanent'].get(str(col), 0)
            if p1_prog > 0 and p1_prog <= length:
                y = p1_prog - 1 + 0.45  # Top saved position
                circle = mpatches.Circle((i, y), 0.35, color=self.color_p1,
                                       ec='white', linewidth=2, zorder=3)
                ax.add_patch(circle)

            # Player 2: Show only topmost saved position (if any)
            p2_prog = state['player2_permanent'].get(str(col), 0)
            if p2_prog > 0 and p2_prog <= length:
                y = p2_prog - 1 + 0.45  # Top saved position
                circle = mpatches.Circle((i, y), 0.35, color=self.color_p2,
                                       ec='white', linewidth=2, zorder=3)
                ax.add_patch(circle)

            # Player 1 temporary: white marker with colored border at current position
            if col in state['player1_active_columns']:
                temp_steps = state['player1_temporary'].get(str(col), 0)
                if temp_steps > 0:
                    current_y = p1_prog + temp_steps - 1 + 0.45  # Current position
                    circle = mpatches.Circle((i, current_y), 0.35,
                                           facecolor='white',
                                           ec=self.color_p1, linewidth=4, zorder=5)
                    ax.add_patch(circle)

            # Player 2 temporary: white marker with colored border at current position
            if col in state['player2_active_columns']:
                temp_steps = state['player2_temporary'].get(str(col), 0)
                if temp_steps > 0:
                    current_y = p2_prog + temp_steps - 1 + 0.45  # Current position
                    circle = mpatches.Circle((i, current_y), 0.35,
                                           facecolor='white',
                                           ec=self.color_p2, linewidth=4, zorder=5)
                    ax.add_patch(circle)

            # Column completion marker
            if col in p1_owned or col in p2_owned:
                owner_color = self.color_p1 if col in p1_owned else self.color_p2
                ax.text(i, length + 0.5, '✓', ha='center', va='center',
                       fontsize=28, fontweight='bold', color=owner_color)

    def draw_dice_and_commentary(self, ax, state):
        """Draw dice with inline colored pairing display"""
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_facecolor('#1A1A1A')
        ax.axis('off')

        current_color = (self.color_p1 if state['current_player'] == self.player1
                        else self.color_p2)

        # Background
        box = mpatches.FancyBboxPatch((0.01, 0.05), 0.98, 0.9,
                                     boxstyle="round,pad=0.02",
                                     facecolor='#3C3C3C',
                                     edgecolor=current_color, linewidth=3)
        ax.add_patch(box)

        y_pos = 0.75

        # Turn number
        ax.text(0.05, y_pos, f"Turn {state['turn_number']}",
               fontsize=14, fontweight='bold', color='white')

        y_pos -= 0.15

        # Dice display with color-coded pairing
        dice = state['roll']
        chosen = state['chosen_pairing']

        if chosen:
            # Determine which dice pairs form the chosen pairing
            # Available pairings order: (d1+d2, d3+d4), (d1+d3, d2+d4), (d1+d4, d2+d3)
            pairings = state['available_pairings']
            chosen_idx = pairings.index(chosen) if chosen in pairings else 0

            # Map to dice indices
            if chosen_idx == 0:
                pair1_indices = (0, 1)
                pair2_indices = (2, 3)
            elif chosen_idx == 1:
                pair1_indices = (0, 2)
                pair2_indices = (1, 3)
            else:  # chosen_idx == 2
                pair1_indices = (0, 3)
                pair2_indices = (1, 2)

            # Bright colors for chosen pairing
            pair1_color = '#FF4444'  # Bright red
            pair2_color = '#44DD44'  # Bright green

            # Draw the rolled dice with color-coded pairs
            ax.text(0.5, y_pos, "Rolled:", ha='center', fontsize=14, color='#AAAAAA', fontweight='bold')
            y_pos -= 0.12

            # Draw dice in a row with colors
            x_start = 0.25
            dice_spacing = 0.12

            for i, d in enumerate(dice):
                x = x_start + i * dice_spacing

                # Determine color for this die
                if i in pair1_indices:
                    color = pair1_color
                    pair_sum = chosen[0]
                elif i in pair2_indices:
                    color = pair2_color
                    pair_sum = chosen[1]
                else:
                    color = '#888888'
                    pair_sum = None

                # Draw die with color
                ax.text(x, y_pos, f'[{d}]', ha='center', va='center',
                       fontsize=18, fontweight='bold', color=color, family='monospace')

            # Draw sum results
            y_pos -= 0.15

            # Show which dice sum to what
            x_center = 0.5

            # Pair 1 sum
            d1_idx, d2_idx = pair1_indices
            ax.text(x_center - 0.15, y_pos, f'{dice[d1_idx]} + {dice[d2_idx]} = {chosen[0]}',
                   ha='center', fontsize=14, fontweight='bold', color=pair1_color)

            # Pair 2 sum
            d3_idx, d4_idx = pair2_indices
            ax.text(x_center + 0.15, y_pos, f'{dice[d3_idx]} + {dice[d4_idx]} = {chosen[1]}',
                   ha='center', fontsize=14, fontweight='bold', color=pair2_color)

            y_pos -= 0.15

            # Show chosen columns
            ax.text(0.5, y_pos, f"→ Chose columns {chosen[0]} and {chosen[1]}",
                   ha='center', fontsize=14, fontweight='bold', color=current_color)
        else:
            # BUST - just show the dice
            dice_nums = ' '.join([f'[{d}]' for d in dice])
            ax.text(0.5, y_pos, f"Rolled: {dice_nums}", ha='center',
                   fontsize=18, fontweight='bold', color='white', family='monospace')

        y_pos -= 0.15

        # EV if available
        if state['ev_calculation'] is not None:
            ev = state['ev_calculation']
            ev_color = '#4CAF50' if ev > 0 else '#F44336'
            ax.text(0.5, y_pos, f"Expected Value: {ev:.2f}",
                   fontsize=13, fontweight='bold', color=ev_color, ha='center')
            y_pos -= 0.12

        # Commentary - with emphasis
        reasoning = state['decision_reasoning']

        # Styling based on event type
        if state['busted']:
            reasoning = f"💥 {reasoning}"
            text_color = '#FF3333'
            text_size = 13
        elif state['stopped']:
            reasoning = f"✋ {reasoning}"
            text_color = '#4CAF50'
            text_size = 13
        else:
            text_color = 'white'
            text_size = 12

        # Wrap text if too long
        if len(reasoning) > 100:
            mid = len(reasoning) // 2
            space_idx = reasoning.find(' ', mid)
            if space_idx > 0:
                reasoning = reasoning[:space_idx] + '\n' + reasoning[space_idx+1:]

        ax.text(0.5, y_pos, reasoning, ha='center', va='top',
               fontsize=text_size, color=text_color, fontweight='600',
               wrap=True)

    def generate_all_frames(self, output_dir):
        """Generate all frames with duplication for timing"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        print(f"Generating frames from {len(self.history)} game states...")

        frame_number = 0
        frame_times = []

        for i, state in enumerate(self.history):
            if i % 5 == 0:
                print(f"  State {i+1}/{len(self.history)}...")

            # Generate the frame
            base_frame = output_path / f"temp_frame_{i:03d}.png"
            self.render_frame(i, str(base_frame))

            # Duplicate frame based on timing
            duration = self.get_frame_duration(state)

            for rep in range(duration):
                output_file = output_path / f"frame_{frame_number:04d}.png"
                # Copy the frame
                import shutil
                shutil.copy(str(base_frame), str(output_file))
                frame_number += 1

            frame_times.append((i, state['turn_number'], duration))
            base_frame.unlink()  # Delete temp frame

        print(f"✓ Generated {frame_number} total frames")
        print(f"  Original states: {len(self.history)}")
        print(f"  Average duration: {frame_number / len(self.history):.1f} frames per state")

        # Save timing info
        timing_file = output_path / "frame_timing.txt"
        with open(timing_file, 'w') as f:
            f.write("State_Idx, Turn_Number, Duration_Frames, Duration_Seconds\n")
            for idx, turn, dur in frame_times:
                f.write(f"{idx}, {turn}, {dur}, {dur/2.0:.1f}\n")

        return frame_number


if __name__ == '__main__':
    game_file = Path(__file__).parent / 'dramatic_game.json'
    output_dir = Path(__file__).parent / 'game_frames_v2'

    generator = GameFrameGeneratorV2(game_file)
    total_frames = generator.generate_all_frames(output_dir)

    print(f"\n✓ Done! {total_frames} frames ready.")
    print(f"  To create video:")
    print(f"  ffmpeg -framerate 2 -i game_frames_v2/frame_%04d.png -vf 'scale=trunc(iw/2)*2:trunc(ih/2)*2' -c:v libx264 -pix_fmt yuv420p -crf 20 game_replay_v2.mp4")
