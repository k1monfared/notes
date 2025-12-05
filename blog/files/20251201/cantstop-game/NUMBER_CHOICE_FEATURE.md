# Number Choice Feature

## Problem Solved

Previously, when a player was at the 3-runner limit and rolled a pairing where both numbers were individually playable but couldn't both be applied (e.g., active runners [3, 4], rolls pairing (6, 7)), the game would automatically choose which number to play. This removed strategic choice from the player.

## Solution

Added a **number choice UI** that appears when a pairing requires the player to choose which number to play.

## When Does This Happen?

A choice is needed when:
1. Both numbers in the pairing are individually playable
2. BUT both cannot be applied together (would exceed 3-runner limit)

### Example Scenario

**Active runners:** [3, 4] (at limit of 3)
**Dice rolled:** [2, 3, 4, 5]
**Pairing options:**
- (5, 9): Both need new runners → Can choose 5 OR 9 (but not both)
- (6, 8): Both need new runners → Can choose 6 OR 8 (but not both)
- (7, 7): One number, needs new runner → Would play 7 automatically (no choice)

If the player selects (6, 8), they'll see the **number choice panel** asking them to pick either 6 or 8.

## User Flow

### Normal Flow (No Choice Needed)
1. Player selects a pairing
2. Clicks "Confirm Move"
3. Move is applied immediately

### Choice Needed Flow
1. Player selects a pairing that needs a choice
2. Pairing shows **"Choose One"** badge (purple, pulsing)
3. Player clicks "Confirm Move"
4. **Number choice panel appears** with two large buttons showing the numbers
5. Player clicks one number (turns golden when selected)
6. Player clicks "Confirm Choice"
7. Move is applied with only the chosen number

### Cancel Option
- Player can click "Cancel" to go back and select a different pairing

## Visual Indicators

### In Pairing Selector
- **"Choose One" badge**: Purple gradient, pulsing animation
- Replaces the normal "Partial" badge when choice is needed

### Number Choice Panel
- Glass-morphism style panel
- Large number buttons (blue gradient)
- Selected number turns golden with glow effect
- "Confirm Choice" button (enabled only when a number is selected)
- "Cancel" button to go back

## Technical Implementation

### Backend Changes

1. **New `get_pairing_playability()` method** ([main.py:108-165](backend/main.py#L108-L165))
   - Analyzes each pairing to determine playability
   - Returns `needs_choice` flag when player must choose

2. **Updated `apply_pairing()` method** ([main.py:167-211](backend/main.py#L167-L211))
   - Accepts optional `chosen_number` parameter
   - If provided, only applies that number
   - Otherwise applies all playable numbers

3. **Enhanced API response** ([main.py:275-305](backend/main.py#L275-L305))
   - `pairing_playability` object included in game state
   - Contains playability info for each valid pairing

4. **Updated `/choose` endpoint**
   - Accepts `chosen_number` in request body
   - Passes it to `apply_pairing()`

### Frontend Changes

1. **New state variables** ([App.jsx:17-18](frontend/src/App.jsx#L17-L18))
   - `needsNumberChoice`: Whether to show choice panel
   - `chosenNumber`: Which number the player selected

2. **Enhanced `confirmPairing()` function** ([App.jsx:71-102](frontend/src/App.jsx#L71-L102))
   - Checks `pairing_playability` before confirming
   - Shows choice panel if needed
   - Sends `chosen_number` to backend

3. **Number Choice Panel UI** ([App.jsx:254-299](frontend/src/App.jsx#L254-L299))
   - Two number buttons
   - Confirm and Cancel actions
   - Clear visual feedback

4. **Updated PairingSelector** ([PairingSelector.jsx:123-124](frontend/src/components/PairingSelector.jsx#L123-L124))
   - Shows "Choose One" badge when `needs_choice` is true
   - Receives `pairingPlayability` prop

5. **New CSS styles** ([App.css:206-267](frontend/src/App.css#L206-L267))
   - `.number-choice-panel`
   - `.choice-btn` with hover and selected states
   - Slide-in animation

## Example Game Flow

```
Turn 1:
- Active: [5, 8]
- Roll: [1, 2, 3, 4]
- Select (3, 7)
- Active becomes: [3, 5, 7, 8] - Wait, that's 4!

Actually:
- Active: [5, 8]
- Select (3, 7) → Both playable, both can be applied
- Active becomes: [3, 5, 7, 8] - Still wrong!

Let me recalculate:
- Active: [5, 8] (2 runners)
- Select (3, 7) (both are new)
- Can add both? 2 + 2 = 4 > 3 ❌
- Need choice!
- Choose 7
- Active becomes: [5, 7, 8] ✓
```

Correct example:

```
Turn 1:
- Active: [] (none)
- Roll: [2, 3, 5, 6]
- Select (5, 8)
- Active: [5, 8]

Turn 2:
- Active: [5, 8]
- Roll: [1, 4, 5, 6]
- Options:
  - (5, 10): 5 is active, 10 is new → Both can apply ✓
  - (9, 6): Both new → Both can apply ✓
- Select (9, 6)
- Active: [5, 6, 8, 9] - Wait, that's 4 again!

Hmm, let me think... If active is [5, 8], we have 2 runners.
Selecting (9, 6) would add 2 new runners.
Total would be 4 runners, which exceeds the limit.

So:
- Active: [5, 8] (2 runners)
- Select (9, 6)
- Both are new, both individually playable
- But can't add both (would be 4 total)
- "Choose One" badge appears!
- Player selects either 9 or 6
- Active becomes: [5, 8, 9] or [5, 6, 8]
```

## Benefits

1. **Player agency**: Strategic choice remains with the player
2. **Clear feedback**: Visual indicators show when choice is needed
3. **Intuitive UI**: Large buttons, obvious selection
4. **Consistent with game rules**: Matches physical Can't Stop gameplay

## Related Files

- [backend/main.py](backend/main.py) - Core mechanics and API
- [frontend/src/App.jsx](frontend/src/App.jsx) - Main game component
- [frontend/src/App.css](frontend/src/App.css) - Choice panel styles
- [frontend/src/components/PairingSelector.jsx](frontend/src/components/PairingSelector.jsx) - Pairing display
- [frontend/src/components/PairingSelector.css](frontend/src/components/PairingSelector.css) - "Choose One" badge
