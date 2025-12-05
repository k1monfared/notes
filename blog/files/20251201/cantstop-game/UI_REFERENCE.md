# UI Reference - Visual Layout

## Main Screen Layout

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  Can't Stop                                            [New Game]            ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━┓  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  ┏━━━━━━━━━━━┓
┃ Player 1  ┃  ┃                 GAME BOARD                        ┃  ┃ Player 2  ┃
┃  [Active] ┃  ┃                                                   ┃  ┃           ┃
┃━━━━━━━━━━━┃  ┃  2   3   4   5   6   7   8   9  10  11  12       ┃  ┃━━━━━━━━━━━┃
┃           ┃  ┃ ╔═╗ ╔═╗ ╔═╗ ╔═╗ ╔═╗ ╔═╗ ╔═╗ ╔═╗ ╔═╗ ╔═╗ ╔═╗      ┃  ┃           ┃
┃Completed  ┃  ┃ ║3║ ║5║ ║7║ ║9║ ║11║║13║║11║║9║ ║7║ ║5║ ║3║      ┃  ┃Completed  ┃
┃  1/3      ┃  ┃ ╚═╝ ╚═╝ ╚═╝ ╚═╝ ╚═╝ ╚═╝ ╚═╝ ╚═╝ ╚═╝ ╚═╝ ╚═╝      ┃  ┃  0/3      ┃
┃           ┃  ┃                                                   ┃  ┃           ┃
┃Total Steps┃  ┃ [3] [3] [3] [3] [3] [█] [3] [3] [3] [3] [3]      ┃  ┃Total Steps┃
┃    12     ┃  ┃ [2] [2] [2] [2] [2] [█] [2] [2] [2] [2] [2]      ┃  ┃     5     ┃
┃━━━━━━━━━━━┃  ┃ [1] [1] [◐] [1] [1] [●] [○] [1] [1] [1] [1]      ┃  ┃━━━━━━━━━━━┃
┃           ┃  ┃     Active                                        ┃  ┃           ┃
┃Completed: ┃  ┃ P1                                                ┃  ┃Completed: ┃
┃  ╔═══╗    ┃  ┃                                                   ┃  ┃  (none)   ┃
┃  ║ 7 ║    ┃  ┃━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┃  ┃           ┃
┃  ╚═══╝    ┃  ┃           ROLLED DICE                             ┃  ┃Progress:  ┃
┃           ┃  ┃                                                   ┃  ┃           ┃
┃Progress:  ┃  ┃  ┏━━━┓ ┏━━━┓ ┏━━━┓ ┏━━━┓                         ┃  ┃Col 6: ████┃
┃           ┃  ┃  ┃ ● ┃ ┃ ● ┃ ┃●  ┃ ┃● ●┃                         ┃  ┃     4/11  ┃
┃Col 4: ████┃  ┃  ┃   ┃ ┃   ┃ ┃ ● ┃ ┃  ●┃                         ┃  ┃           ┃
┃     3/7   ┃  ┃  ┃ ● ┃ ┃ ● ┃ ┃●  ┃ ┃● ●┃                         ┃  ┃Col 9: ██  ┃
┃           ┃  ┃  ┗━━━┓ ┗━━━┓ ┗━━━┓ ┗━━━┓                         ┃  ┃     1/9   ┃
┃Col 7: ████┃  ┃   [2]   [2]   [5]   [6]                          ┃  ┃           ┃
┃     5/13✓ ┃  ┃                                                   ┃  ┗━━━━━━━━━━━┛
┃           ┃  ┃━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┃
┃Col 8: ██  ┃  ┃        CHOOSE YOUR PAIRING                        ┃
┃     2/11  ┃  ┃                                                   ┃
┃           ┃  ┃ ┏━━━━━━━━━━━┓ ┏━━━━━━━━━━━┓ ┏━━━━━━━━━━━┓       ┃
┗━━━━━━━━━━━┛  ┃ ┃   ╔══╗    ┃ ┃   ╔══╗    ┃ ┃   ╔══╗    ┃       ┃
               ┃ ┃   ║4 ║ +  ┃ ┃   ║7 ║ +  ┃ ┃   ║8 ║ +  ┃       ┃
               ┃ ┃   ╚══╝    ┃ ┃   ╚══╝    ┃ ┃   ╚══╝    ┃       ┃
               ┃ ┃   ╔══╗    ┃ ┃   ╔══╗    ┃ ┃   ╔══╗    ┃       ┃
               ┃ ┃   ║11║    ┃ ┃   ║8 ║    ┃ ┃   ║7 ║    ┃       ┃
               ┃ ┃   ╚══╝    ┃ ┃   ╚══╝    ┃ ┃   ╚══╝    ┃       ┃
               ┃ ┃━━━━━━━━━━━┃ ┃━━━━━━━━━━━┃ ┃━━━━━━━━━━━┃       ┃
               ┃ ┃  Extends 4┃ ┃   New 7   ┃ ┃   New 8   ┃       ┃
               ┃ ┃   New 11  ┃ ┃  Extends 8┃ ┃   New 7   ┃       ┃
               ┃ ┗━━━━━━━━━━━┛ ┗━━━━━━━━━━━┛ ┗━━━━━━━━━━━┛       ┃
               ┃         ✓          ✓            ✓                 ┃
               ┃       Valid       Valid        Valid              ┃
               ┃                                                   ┃
               ┃━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┃
               ┃                                                   ┃
               ┃        ┏━━━━━━━━━━━━━━━━━━━━━━━━━━┓              ┃
               ┃        ┃      Confirm Move        ┃              ┃
               ┃        ┗━━━━━━━━━━━━━━━━━━━━━━━━━━┛              ┃
               ┃                                                   ┃
               ┃        ┏━━━━━━━━━━━━━━━━━━━━━━━━━━┓              ┃
               ┃        ┃   Stop & Save Progress   ┃              ┃
               ┃        ┗━━━━━━━━━━━━━━━━━━━━━━━━━━┛              ┃
               ┃                                                   ┃
               ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

## Visual States

### 1. Initial State (Start of Game)
```
Board: All columns empty
Dice: Hidden
Pairings: Hidden
Buttons: [Roll Dice]
Player 1: Active (gold border)
```

### 2. After Rolling Dice
```
Board: Shows any existing progress
Dice: 4 animated dice visible (e.g., [2][2][5][6])
Pairings: 3 options shown
  - Valid: White background, clickable
  - Invalid: Gray background, shows reason
Buttons: None (must select pairing)
```

### 3. Pairing Selected
```
Board: Unchanged
Dice: Still visible
Pairings: Selected one has GOLD background + glow
Buttons: [Confirm Move] [Cancel by clicking another]
```

### 4. After Confirming
```
Board: Pieces animate upward in selected columns
Dice: Hidden
Pairings: Hidden
Buttons: [Roll Dice] [Stop & Save Progress]
Temp Progress: Shows hollow markers in columns
Active Indicators: Gold "Active" badges under columns
```

### 5. After Bust
```
Board: Temp markers disappear (animated fade)
Dice: Hidden
Message: "💥 BUST! No valid moves. Lost X steps."
Buttons: [Continue] (passes turn)
Player Switches: Other player now has gold border
```

### 6. Game Over
```
Board: Shows final state
Large Modal:
  ┏━━━━━━━━━━━━━━━━━━━━━━━┓
  ┃     GAME OVER!         ┃
  ┃   Player X Wins!       ┃
  ┃   ┏━━━━━━━━━━━━━━┓    ┃
  ┃   ┃  Play Again   ┃    ┃
  ┃   ┗━━━━━━━━━━━━━━┛    ┃
  ┗━━━━━━━━━━━━━━━━━━━━━━━┛
```

## Board Cell States

### Empty Cell
```
┏━━━┓
┃   ┃  White background
┃ 1 ┃  Position number (gray, small)
┗━━━┛  Light border
```

### Player 1 Progress
```
┏━━━┓
┃ ● ┃  Blue filled circle
┃ 1 ┃  Position number
┗━━━┛  Blue border
```

### Player 2 Progress
```
┏━━━┓
┃ ○ ┃  Red filled circle
┃ 1 ┃  Position number
┗━━━┛  Red border
```

### Temporary Progress
```
┏━━━┓
┃ ◐ ┃  Hollow circle with colored border
┃ 1 ┃  Pulsing animation
┗━━━┛  Colored border (player's color)
```

### Completed Column
```
┏━━━┓
┃ ● ┃  Solid circle
┃ 1 ┃  Gray text
┗━━━┛  Colored background (player's color)
       Badge: "P1" or "P2"
```

### Highlighted Cell (in selected pairing)
```
┏━━━┓
┃ ◐ ┃  Glowing effect
┃ 1 ┃  Pulsing scale animation
┗━━━┛  Gold border + shadow
```

## Dice Faces

### Die Value 1
```
┏━━━━━┓
┃     ┃
┃  ●  ┃
┃     ┃
┗━━━━━┛
```

### Die Value 2
```
┏━━━━━┓
┃●    ┃
┃     ┃
┃    ●┃
┗━━━━━┛
```

### Die Value 3
```
┏━━━━━┓
┃●    ┃
┃  ●  ┃
┃    ●┃
┗━━━━━┛
```

### Die Value 4
```
┏━━━━━┓
┃●   ●┃
┃     ┃
┃●   ●┃
┗━━━━━┛
```

### Die Value 5
```
┏━━━━━┓
┃●   ●┃
┃  ●  ┃
┃●   ●┃
┗━━━━━┛
```

### Die Value 6
```
┏━━━━━┓
┃●   ●┃
┃●   ●┃
┃●   ●┃
┗━━━━━┛
```

## Pairing Card States

### Valid & Available
```
┏━━━━━━━━━━━━━┓
┃   ╔════╗    ┃  White background
┃   ║ 7  ║ +  ┃  Blue badges
┃   ╚════╝    ┃  Clickable cursor
┃   ╔════╗    ┃
┃   ║ 8  ║    ┃  Hover: slight lift
┃   ╚════╝    ┃
┃─────────────┃
┃ [New 7]     ┃  Green badge = new
┃ [Extends 8] ┃  Blue badge = existing
┗━━━━━━━━━━━━━┛
```

### Invalid (Column Completed)
```
┏━━━━━━━━━━━━━┓
┃   ╔════╗    ┃  Gray background
┃   ║ 7  ║ +  ┃  Grayed badges (completed)
┃   ╚════╝    ┃  No cursor
┃   ╔════╗    ┃  Opacity: 60%
┃   ║12  ║    ┃
┃   ╚════╝    ┃
┃─────────────┃
┃   Column    ┃  Red text
┃  completed  ┃
┗━━━━━━━━━━━━━┛
```

### Invalid (Too Many Runners)
```
┏━━━━━━━━━━━━━┓
┃   ╔════╗    ┃  Gray background
┃   ║ 5  ║ +  ┃  Normal badges
┃   ╚════╝    ┃  Opacity: 60%
┃   ╔════╗    ┃
┃   ║10  ║    ┃
┃   ╚════╝    ┃
┃─────────────┃
┃  Too many   ┃  Red text
┃   runners   ┃
┗━━━━━━━━━━━━━┛
```

### Selected
```
┏━━━━━━━━━━━━━┓
┃   ╔════╗    ┃  GOLD background
┃   ║ 7  ║ +  ┃  Glowing shadow
┃   ╚════╝    ┃  Pulsing animation
┃   ╔════╗    ┃  Gold border
┃   ║ 8  ║    ┃
┃   ╚════╝    ┃
┃─────────────┃
┃ Click Confirm┃ Purple hint text
┃  to apply    ┃
┗━━━━━━━━━━━━━┛
```

## Color Legend

- **Blue (#3b82f6)**: Player 1
- **Red (#ef4444)**: Player 2
- **Purple (#667eea)**: UI elements, headers
- **Gold (#fbbf24)**: Active, selected, highlighted
- **Green (#48bb78)**: Success, new columns
- **Gray (#94a3b8)**: Disabled, inactive
- **White (#ffffff)**: Backgrounds, temporary markers

## Animations

1. **Dice Roll**:
   - Rotate 720deg (2 full rotations)
   - Duration: 0.6s
   - Easing: ease-out
   - Stagger: 0.1s delay per die

2. **Pairing Select**:
   - Background: white → gold
   - Shadow: 0 → 20px blur
   - Scale: pulse (1 → 1.05 → 1)
   - Duration: 0.3s

3. **Piece Movement**:
   - Scale: 0 → 1.2 → 1
   - Spring physics
   - Duration: ~0.8s

4. **Active Column Glow**:
   - Shadow pulse
   - Infinite loop
   - Duration: 1.5s per cycle

5. **Bust Shake**:
   - TranslateX: 0 → -10px → +10px → 0
   - Duration: 0.5s
   - Easing: ease

## Responsive Breakpoints

### Desktop (>1200px)
```
[Player 1 Sidebar] [Game Board] [Player 2 Sidebar]
      250px            fluid           250px
```

### Tablet (900px - 1200px)
```
[Player 1] [Game Board] [Player 2]
   200px       fluid        200px
```

### Mobile (<900px)
```
[Player 1 Info]
[Game Board]
[Player 2 Info]
All full width, stacked
```

This visual reference helps understand what users will see at each stage of the game!
