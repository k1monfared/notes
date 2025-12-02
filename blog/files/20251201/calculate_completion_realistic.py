import numpy as np

# This is the more complex calculation:
# When you have 3 columns active, the bust probability depends on the combination
# Let's calculate for typical combinations

column_probs = {
    2: 171/1296,
    3: 302/1296,
    4: 461/1296,
    5: 580/1296,
    6: 727/1296,
    7: 834/1296,
    8: 727/1296,
    9: 580/1296,
    10: 461/1296,
    11: 302/1296,
    12: 171/1296
}

column_lengths = {n: 2*n-1 for n in range(2, 13)}

# Some representative bust probabilities from the full table
bust_probs = {
    (6,7,8): 0.080,
    (5,7,9): 0.147,
    (4,7,10): 0.123,
    (2,7,12): 0.219,
    (2,3,12): 0.562,
}

print("Expected progress per turn for different column combinations:")
print("(Aggressive play: roll until bust)")
print("\n| Columns | P(bust) | P(success) | E[steps/turn] | Turns to complete 13 steps |")
print("|:--------|--------:|-----------:|--------------:|---------------------------:|")

for cols, p_bust in bust_probs.items():
    p_success = 1 - p_bust
    # Expected number of successes before busting = p_success / p_bust
    expected_steps = p_success / p_bust
    turns_for_13 = 13 / expected_steps
    
    print(f"| {{{cols[0]},{cols[1]},{cols[2]}}} | {p_bust:.3f} | {p_success:.3f} | {expected_steps:.3f} | {turns_for_13:.2f} |")

print("\n\nSingle column completion (simplified model):")
print("If we focus on one specific column from a good combination:")
print("\n| Column | Length | When in {6,7,8} | When in {2,3,12} |")
print("|-------:|-------:|----------------:|-----------------:|")

# For {6,7,8} with p_bust = 0.080, p_success = 0.920
# Expected rolls before bust = 1/p_bust = 12.5
# But not every roll advances YOUR specific column

for n in [6, 7, 8]:
    L = column_lengths[n]
    p_col = column_probs[n]
    
    # In combination {6,7,8}, you make ~12.5 rolls before bust
    # Each roll has probability p_col of hitting your column
    # Expected times you hit your column = 12.5 * p_col
    rolls_before_bust_good = 1 / 0.080
    expected_hits_good = rolls_before_bust_good * p_col
    turns_good = L / expected_hits_good
    
    # In combination {2,3,12}, you make ~1.78 rolls before bust
    rolls_before_bust_bad = 1 / 0.562
    expected_hits_bad = rolls_before_bust_bad * column_probs[n] if n in [2,3,12] else 0
    
    if n in [2, 3, 12]:
        turns_bad = L / expected_hits_bad if expected_hits_bad > 0 else float('inf')
        print(f"| {n} | {L} | {turns_good:.2f} turns | {turns_bad:.2f} turns |")
    else:
        print(f"| {n} | {L} | {turns_good:.2f} turns | N/A |")

print("\n\nKey insight:")
print("For column 7 in combination {6,7,8}:")
p_7 = column_probs[7]
rolls_678 = 1 / 0.080
expected_hits_7 = rolls_678 * p_7
turns_7 = 13 / expected_hits_7
print(f"  - Expected rolls before bust: {rolls_678:.2f}")
print(f"  - Probability of rolling 7 each time: {p_7:.4f}")
print(f"  - Expected times you advance on col 7 per turn: {expected_hits_7:.2f}")
print(f"  - Expected turns to complete 13 steps: {turns_7:.2f}")

print("\n\nFor column 2 in combination {2,3,12}:")
p_2 = column_probs[2]
rolls_2312 = 1 / 0.562
expected_hits_2 = rolls_2312 * p_2
turns_2 = 3 / expected_hits_2
print(f"  - Expected rolls before bust: {rolls_2312:.2f}")
print(f"  - Probability of rolling 2 each time: {p_2:.4f}")
print(f"  - Expected times you advance on col 2 per turn: {expected_hits_2:.2f}")
print(f"  - Expected turns to complete 3 steps: {turns_2:.2f}")
