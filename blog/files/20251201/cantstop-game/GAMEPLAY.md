# Gameplay Guide

## Visual Walkthrough

### The Game Board

```
   2   3   4   5   6   7   8   9  10  11  12
  [3] [5] [7] [9][11][13][11][9] [7] [5] [3]  <- Column heights
   ●                                          Player 1 (blue)
       ○                                      Player 2 (red)
           ◐                                  Temporary progress (white with color border)
               ✓                              Completed column
```

Each column (2-12) has a specific height:
- **2, 12**: 3 steps (shortest, hardest to roll)
- **3, 11**: 5 steps
- **4, 10**: 7 steps
- **5, 9**: 9 steps
- **6, 8**: 11 steps
- **7**: 13 steps (longest, easiest to roll)

### Turn Sequence

#### 1. Roll Dice
Click "Roll Dice" button → 4 dice animate and show values

Example roll: `[2, 2, 5, 6]`

#### 2. View Pairings
The game shows all 3 possible ways to pair the dice:

```
Option 1: (2+2) + (5+6) = 4 + 11  ✓ Valid
Option 2: (2+5) + (2+6) = 7 + 8   ✓ Valid
Option 3: (2+6) + (2+5) = 8 + 7   ✓ Valid (same as option 2)
```

Each pairing shows:
- **Sum values** in large badges
- **Green "New X"** = starting new column
- **Blue "Extends X"** = continuing existing column
- **Gray + disabled** = invalid move (see why below)

#### 3. Invalid Moves

A pairing is grayed out when:

**"Column completed"**
```
Option 1: 7 + 12
         [7✓] + [12]
```
Column 7 is already won by someone - can't use it

**"Too many runners"**
```
Active columns: [4, 8, 11]  (already have 3 runners)
Option 1: 5 + 10  (would need 2 NEW runners)
         [5] + [10]  ← Can't do this!
```
You can only have 3 active columns at once

**Valid move with 3 runners:**
```
Active columns: [4, 8, 11]
Option 1: 4 + 11  ✓ (uses existing runners)
         [4✓] + [11✓]
```

#### 4. Select & Confirm

1. Click a valid pairing → highlights in **gold**
2. Click "Confirm Move" → pieces animate upward
3. Now you have a choice:
   - **Roll Again** (risky - could bust)
   - **Stop & Save Progress** (safe - keeps progress)

### Example Turn

```
Player 1's Turn
================

Permanent Progress:
  Column 7: 5/13 steps
  Column 8: 3/11 steps

Turn begins:
  Active runners: []
  Temp progress: {}

Roll 1: [3, 4, 5, 6]
  Choose: 7 + 11 (3+4=7, 5+6=11)
  → Active runners: [7, 11]
  → Temp progress: {7: 1, 11: 1}

Roll 2: [2, 3, 5, 6]
  Choose: 7 + 8 (2+5=7, 3+6=8)
  → Active runners: [7, 11, 8]  ← Now at max!
  → Temp progress: {7: 2, 11: 1, 8: 1}

Roll 3: [1, 2, 4, 5]
  Options:
    3 + 9  ✗ (would need 2 new runners, already have 3)
    5 + 6  ✗ (would need 2 new runners)
    6 + 5  ✗ (same as above)

  💥 BUST! All temp progress lost!

Final state: Column 7 still at 5/13 (no change)
```

### Strategy Example: When to Stop

**Scenario A: Safe Stop** ✓
```
Temp progress: {7: 3, 8: 2}
Total unsaved: 5 steps
Reasoning: Good progress, don't risk it!
Action: STOP
```

**Scenario B: Push Your Luck**
```
Temp progress: {7: 1}
Total unsaved: 1 step
Column 7 progress: 12/13 (one away!)
Reasoning: So close! Worth the risk
Action: ROLL AGAIN
```

**Scenario C: Column Completed!**
```
Temp progress: {6: 11}  ← Hit the top!
Action: MUST STOP (automatic save)
Result: Column 6 completed! ✓
```

### Winning

Complete any 3 columns to win:

```
Player 1 completed: [7✓, 8✓, 9✓]

🎉 Player 1 Wins!
```

## UI Elements Explained

### Dice Display
- **White dice** with blue border
- **Dots** show 1-6 values
- **Animation**: Rolls with 3D rotation

### Pairing Cards
- **White background** = available
- **Gray background** = invalid
- **Gold background + glow** = selected
- **Active runner badges** = columns you're currently advancing
- **New column badges** = columns you'd start

### Game Board Columns
- **Column header** (purple circle) = column number
- **Empty cells** = no progress
- **Blue filled** = Player 1 progress
- **Red filled** = Player 2 progress
- **White with border** = temporary (unsaved) progress
- **Gold "Active" badge** = column has a runner
- **Colored badge** = completed by that player

### Player Sidebars
- **Gold border** = current player
- **"Active" badge** = your turn
- **Completed count** = X/3 columns
- **Progress bars** = advancement in each column

## Tips

1. **Start with middle columns** (6, 7, 8) - easier to roll
2. **Watch the 3-runner limit** - getting stuck is bad!
3. **Stop after completing a column** - don't get greedy
4. **Outer columns are risky** - 2 and 12 are hard to hit
5. **Calculate expected value** - is the risk worth it?
6. **Block opponents** - complete columns they need

## Common Mistakes

❌ **Rolling with 3 unrelated runners**
   - Hard to get valid moves

❌ **Not stopping after big progress**
   - Bust = lose everything

❌ **Ignoring opponent's progress**
   - They might complete 3 before you!

❌ **Always playing safe**
   - Sometimes you need to push

✓ **Balance risk and reward**
