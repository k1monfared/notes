# Partial Pairing Fix - Game Mechanics Correction

## The Problem

The original implementation required BOTH numbers in a pairing to be playable. This was incorrect!

### Example Scenario
- Player has 2 active runners: [6, 8]
- Rolls dice: [2, 3, 4, 5]
- Pairing options:
  - (2+3, 4+5) = (5, 9)
  - (2+4, 3+5) = (6, 8)
  - (2+5, 3+4) = (7, 7)

**OLD (WRONG) BEHAVIOR:**
- (5, 9): ❌ Invalid - would need 2 new runners, exceeds limit
- (6, 8): ✅ Valid - both already active
- (7, 7): ❌ Invalid - would need 1 new runner, but counts as trying to add 1 new

**NEW (CORRECT) BEHAVIOR:**
- (5, 9): ✅ Valid - can't play 5 (new runner, at limit) but CAN play 9 (existing runner... wait, 9 isn't active!)

Let me reconsider...

**ACTUAL CORRECT BEHAVIOR:**

A pairing is valid if AT LEAST ONE number can be played.

A number can be played if:
1. The column is not completed, AND
2. Either:
   - It's already an active runner, OR
   - You have room for a new runner (< 3 active)

So with active runners [6, 8]:

- **(5, 9)**:
  - 5: Not active, not completed, have room? NO (already have 2 runners)
  - 9: Not active, not completed, have room? NO (already have 2 runners)
  - **Result: INVALID** (neither playable)

- **(6, 8)**:
  - 6: Active ✓
  - 8: Active ✓
  - **Result: VALID** (both playable, both advance)

- **(7, 7)**:
  - 7: Not active, not completed, have room? NO (already have 2 runners)
  - **Result: INVALID** (not playable)

### Better Example

Active runners: [6, 8]
Completed: [7]
Rolls: [1, 5, 6, 6]

Pairings:
- (1+5, 6+6) = **(6, 12)**
  - 6: Active ✓ (playable)
  - 12: Not active, not completed, no room (have 2 runners already)
  - **Result: VALID - can play just the 6!**
  - Badge shows: "+6" and "12 ✗" with "Partial" tag

- (1+6, 5+6) = **(7, 11)**
  - 7: Completed ✗
  - 11: Not active, not completed, no room
  - **Result: INVALID**

- (1+6, 5+6) = **(7, 11)** (same as above)

## The Fix

### Backend Changes

1. **Updated `is_pairing_valid()`** - Returns true if ANY number is playable
2. **Updated `apply_pairing()`** - Only applies playable numbers
   - Takes `all_completed` parameter
   - Checks each number independently
   - Skips unplayable numbers

### Frontend Changes

1. **Visual Indicators**:
   - Unplayable numbers: Red badge with ✗ mark
   - Playable numbers: Normal or gold (if active)
   - Partial pairings: Show "Partial" badge

2. **Clearer Feedback**:
   - "+6" means extending column 6
   - "New 12" means starting column 12
   - Shows which numbers will actually be played

## Game Rules Clarification

### Can't Stop Rules
1. You have 3 "runners" to use
2. On your turn, roll 4 dice
3. Pair them in one of 3 ways
4. Advance in those columns
5. If pairing has a playable number, you can use it!
6. If NEITHER number is playable → BUST

### What Makes a Number Playable?
- ✅ Already have a runner there (extend it)
- ✅ Don't have a runner there, but have < 3 runners (start new)
- ❌ Column is completed by someone
- ❌ Don't have a runner there AND already have 3 runners

### Example Game Flow

**Turn Start:**
- Active: None
- Roll: [2, 3, 5, 6]
- Choose (5, 8)
- Active: [5, 8] ← Started 2 new runners

**Second Roll:**
- Active: [5, 8]
- Roll: [1, 4, 5, 6]
- Pairings:
  - (5, 10): Valid! ✓ 5 is active, 10 is new
  - (9, 6): Valid! ✓ Both are new, have room for 1 more
  - (10, 9): Valid! ✓ Both are new, have room for 1 more
- Choose (5, 10)
- Active: [5, 8, 10] ← Extended 5, added 10 (now at max!)

**Third Roll:**
- Active: [5, 8, 10] (AT LIMIT)
- Roll: [2, 2, 3, 4]
- Pairings:
  - (4, 7): Invalid ❌ Neither is active, no room
  - (5, 6): **VALID!** ✓ 5 is active (6 is not, but that's OK!)
  - (6, 5): **VALID!** ✓ Same as above
- Choose (5, 6)
- **Only 5 advances!** 6 is ignored
- Active: Still [5, 8, 10]
- Badge shows: "+5" and "6 ✗" with "Partial"

## Visual Examples

### Full Pairing (Both Playable)
```
┌─────────────┐
│  ╔══╗  +    │  ← Active runner
│  ║6 ║       │
│  ╚══╝       │
│  ╔══╗       │  ← Active runner
│  ║8 ║       │
│  ╚══╝       │
│─────────────│
│  +6   +8    │  ← Both advance
└─────────────┘
```

### Partial Pairing (One Playable)
```
┌─────────────┐
│  ╔══╗  +    │  ← Active runner
│  ║6 ║       │
│  ╚══╝       │
│  ╔══╗  ✗    │  ← Not playable (no room)
│  ║12║       │
│  ╚══╝       │
│─────────────│
│  +6   Partial│  ← Only 6 advances
└─────────────┘
```

### Invalid Pairing (Neither Playable)
```
┌─────────────┐
│  ╔══╗  ✗    │  ← Completed
│  ║7 ║       │
│  ╚══╝       │
│  ╔══╗  ✗    │  ← No room
│  ║11║       │
│  ╚══╝       │
│─────────────│
│  Cannot play│  ← Disabled
└─────────────┘
```

## Testing Scenarios

### Scenario 1: Partial at Runner Limit
```
Active: [4, 8, 11]
Roll: [3, 3, 5, 6]
Pairings:
  (6, 11): VALID ✓ (only 11 playable)
  (8, 9):  VALID ✓ (only 8 playable)
  (9, 8):  VALID ✓ (only 8 playable)
```

### Scenario 2: Completed Column Blocks
```
Active: [6]
Completed: [7]
Roll: [3, 4, 5, 6]
Pairings:
  (7, 11): VALID ✓ (only 11 playable, 7 is completed)
  (8, 9):  VALID ✓ (both playable, room for 2 more)
  (9, 8):  VALID ✓ (same as above)
```

### Scenario 3: All Invalid = BUST
```
Active: [5, 7, 9] (at limit)
Completed: []
Roll: [1, 2, 3, 4]
Pairings:
  (3, 7):  VALID ✓ (7 is active!)
  ... wait, that's valid!

Let me try again:
Active: [5, 7, 9] (at limit)
Completed: [6]
Roll: [1, 1, 2, 4]
Pairings:
  (2, 6):  INVALID ❌ (2 no room, 6 completed)
  (3, 5):  VALID ✓ (5 is active!)
  ... still not a bust!

For a bust, ALL pairings must have NO playable numbers.
```

## Benefits

1. **Correct gameplay** - Matches real Can't Stop rules
2. **Better strategy** - Can keep pushing even at runner limit
3. **Clear feedback** - Visual indicators show what's playable
4. **Fewer busts** - More options to continue playing

## Auto-Reload Still Works!

Changes take effect immediately - just save and refresh browser.
