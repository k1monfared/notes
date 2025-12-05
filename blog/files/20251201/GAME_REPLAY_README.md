# Can't Stop Game Replay System

## What We Built

A complete game replay visualization system that records and renders Can't Stop games as videos.

## Files Created

### Core System
- **`game_replay_system.py`** - Full game simulator with state recording
  - Records every dice roll, decision, and game state
  - Implements GreedyUntil1Col and ExpectedValueMax strategies
  - Finds "dramatic" games (big busts, comebacks, decisive wins)
  - Saves game history as JSON

### Visualization
- **`generate_game_frames.py`** - Renders game states as PNG frames
  - Beautiful board visualization showing:
    - All 11 columns with proper lengths
    - Permanent progress (solid circles)
    - Temporary/unsaved progress (hollow circles with lines)
    - Dice rolls and available pairings
    - Strategy decisions and reasoning
    - EV calculations for ExpectedValueMax
  - Commentary with emoji (💥 for busts, ✋ for stops)

- **`game_replay_final.mp4`** (233 KB) - The final video
  - 31 frames at 2 fps = ~15 seconds
  - 1890x1184 resolution
  - Shows complete GreedyUntil1Col vs ExpectedValueMax game

### Data
- **`dramatic_game.json`** - Complete game history
  - 31 turns of gameplay
  - Full state for each turn
  - Winner: GreedyUntil1Col
  - ExpectedValueMax busted badly (lost 8 steps)

- **`game_frames/`** - Directory with all PNG frames
  - `frame_000.png` through `frame_030.png`
  - `summary.png` - Key moments side-by-side

## The Game We Captured

**GreedyUntil1Col defeats ExpectedValueMax**

Key moments:
- Both start on similar columns
- GreedyUntil1Col methodically completes one column at a time
- ExpectedValueMax accumulates 8+ unsaved steps
- 💥 ExpectedValueMax BUSTS - loses everything
- GreedyUntil1Col cruises to victory completing columns 2, 4, and 12

## How It Works

### 1. Game Simulation
```python
game = CantStopGame(
    GreedyUntil1ColStrategy(),
    ExpectedValueMaxStrategy(),
    "GreedyUntil1Col",
    "ExpectedValueMax"
)
winner = game.play_game()  # Records every state
game.save_history('dramatic_game.json')
```

### 2. Frame Generation
```python
generator = GameFrameGenerator('dramatic_game.json')
generator.generate_all_frames('game_frames/')
# Creates frame_000.png, frame_001.png, ...
```

### 3. Video Creation
```bash
ffmpeg -framerate 2 -i game_frames/frame_%03d.png \
       -vf "scale=1890:1184" \
       -c:v libx264 -pix_fmt yuv420p \
       game_replay_final.mp4
```

## Frame Layout

Each frame shows:

```
┌─────────────────────────────────────────┐
│  Turn X - [Player]'s Turn               │  ← Title
├─────────────────────────────────────────┤
│                                         │
│  2  3  4  5  6  7  8  9 10 11 12       │  ← Board
│  ┃  ┃  ┃  ┃  ┃  ┃  ┃  ┃  ┃  ┃  ┃       │
│  ●  ●     ●  ●  ●  ○     ●  ●          │  ← Progress
│                                         │
│ Legend: ● Permanent  ○ Temporary       │
├─────────────────────────────────────────┤
│  Dice: [2][3][5][6]                    │  ← Dice/Decision
│  Options: 5+8 / 7+8 / 3+11             │
│  Chosen: 7+8 ✓                         │
│  EV = 2.30                             │
├─────────────────────────────────────────┤
│  ┌───────────────────────────────────┐ │  ← Commentary
│  │ EV = 2.30 > 0. Math says ROLL!   │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## Potential Improvements

1. **Add sound effects** - Dice roll sounds, bust explosions
2. **Animated dice rolls** - Show dice tumbling
3. **Progress bars** - Show completion percentage
4. **Split screen** - Both players side-by-side
5. **Zoom in on busts** - Dramatic slow-mo
6. **End screen** - Final score breakdown
7. **Multiple games** - Show best-of-3 series
8. **Interactive HTML** - Scrub through turns

## Usage in Blog Post

This could be embedded in the blog post with:

```markdown
### Seeing It In Action

Want to see why GreedyUntil1Col beats ExpectedValueMax? Watch this actual game replay:

<video controls width="100%">
  <source src="files/20251201/game_replay_final.mp4" type="video/mp4">
</video>

Watch how ExpectedValueMax's "mathematically optimal" strategy leads to accumulating 8 unsaved steps, then loses everything in a single bust. Meanwhile, GreedyUntil1Col stops after every column completion, steadily building an unassailable lead.

This is variance in action: EV's strategy optimizes expected value but creates huge swings. In a short game (typical 8-12 turns), consistency beats optimization.
```

## Technical Details

- **Language**: Python 3
- **Dependencies**: matplotlib, numpy, json
- **Video Codec**: H.264 (libx264)
- **Frame Rate**: 2 fps (slow enough to read)
- **Resolution**: 1890x1184 (scaled from 1890x1185)
- **File Size**: 233 KB for 31 frames
- **Duration**: ~15 seconds

## Statistics

- Simulated 500 games to find this one
- Scoring based on: bust size, lead changes, drama
- Best game score: 80 (8-step bust × 10 points)
- Total turns in game: 31
- GreedyUntil1Col completed: {2, 4, 12}
- ExpectedValueMax completed: {} (nothing!)
