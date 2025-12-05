# Debugging Bust Display Issue

## Problem
When a player busts, the dice and pairings are not visible. The bust message appears correctly, but the dice and pairing selector are missing.

## Expected Behavior
When a bust occurs:
1. Dice should remain visible showing what was rolled
2. All 3 pairings should be shown (all marked as invalid/disabled)
3. Bust message should appear
4. "Next Player" button should appear

## Current Behavior
- Bust message appears ✓
- "Next Player" button appears ✓
- Dice are NOT visible ✗
- Pairings are NOT visible ✗

## Debugging Changes Made

### Frontend (App.jsx)

Added comprehensive console logging in `rollDice()` function:
- Full response object
- response.data structure
- current_dice value, type, and if it's an array
- available_pairings
- valid_pairings
- is_bust flag

Added bust state logging:
- Logs `hasDice`, `current_dice`, `available_pairings`, and `valid_pairings` whenever `is_bust` is true
- This will show on every render when busted

### What to Check

1. **Open browser console (F12)**
2. **Start a new game and play until you get a bust**
3. **Look for the console output**

#### Expected Output When Bust Occurs:

```
=== ROLL RESPONSE ===
Full response: {...}
response.data: {...}
response.data.state: {...}
current_dice: [1, 2, 3, 4]  ← Should be array of 4 numbers
current_dice type: "object"
current_dice is array: true
available_pairings: [[3, 7], [4, 6], [5, 5]]  ← Should be 3 pairings
valid_pairings: []  ← Empty when busted
is_bust: true
====================

BUST STATE - hasDice: true  ← Should be true!
BUST STATE - current_dice: [1, 2, 3, 4]
BUST STATE - available_pairings: [[3, 7], [4, 6], [5, 5]]
BUST STATE - valid_pairings: []
```

#### If Bug Persists:

If `current_dice` is `null`:
- Check backend `roll_dice()` method
- Check if something is clearing the dice

If `current_dice` is an empty array `[]`:
- Check `GameMechanics.roll_dice()` implementation
- This would cause DiceRoller to return null (line 71)

If `hasDice` is false:
- Check why `gameState.current_dice` is null/undefined
- Check state update timing

## Backend Logic (Already Verified)

The backend correctly:
1. Rolls dice: `game.current_dice = GameMechanics.roll_dice()`
2. Generates pairings: `game.available_pairings = GameMechanics.get_all_pairings(...)`
3. Validates pairings: `game.valid_pairings = GameMechanics.get_valid_pairings(...)`
4. Detects bust: `if len(game.valid_pairings) == 0: game.is_bust = True`
5. Does NOT clear dice: No `game.current_dice = None` on bust
6. Returns full state: `game.to_dict()` includes current_dice

## Frontend Display Logic

Dice and pairings are shown when:
```javascript
hasDice = gameState.current_dice !== null && gameState.current_dice !== undefined
```

And rendered with:
```jsx
{hasDice && (
  <DiceRoller dice={gameState.current_dice} isBust={gameState.is_bust} />
)}
```

DiceRoller returns null if:
```javascript
if (!dice || dice.length === 0) return null
```

## Next Steps

1. Run the game and trigger a bust
2. Check browser console logs
3. Share the console output
4. Based on the logs, we'll know if:
   - Backend is sending correct data (but frontend is losing it)
   - Backend is sending wrong data (null/empty dice)
   - State update timing issue
   - React rendering issue

## Note on "Next Player" Button Text

The button text "Next Player (Player X)" is CORRECT:
- If Player 2 is active (has golden border) and busts
- Then Player 1 is next
- So button says "Next Player (Player 1)"

This is NOT a bug - it shows the NEXT player, not the current player.
