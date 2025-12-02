import numpy as np

# Probabilities for each column (from the table)
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

# Column lengths L(n) = 2n-1
column_lengths = {n: 2*n-1 for n in range(2, 13)}

print("Probability of completing column in a single turn (rolling until bust or completion):\n")
print("| Column | Length | P(sum) | P(complete in 1 turn) | Expected turns to complete |")
print("|-------:|-------:|-------:|----------------------:|---------------------------:|")

for n in range(2, 13):
    L = column_lengths[n]
    p = column_probs[n]
    
    # To complete in one turn, we need L consecutive successful rolls
    # P(complete) = p^L
    prob_complete_one_turn = p ** L
    
    # Expected number of turns to complete
    # This is a geometric distribution: E = 1/p where p is success probability
    expected_turns = 1 / prob_complete_one_turn if prob_complete_one_turn > 0 else float('inf')
    
    print(f"| {n} | {L} | {p:.4f} | {prob_complete_one_turn:.6f} | {expected_turns:.2f} |")

print("\n\nDetailed analysis:")
print("="*70)

for n in [2, 7, 12]:
    L = column_lengths[n]
    p = column_probs[n]
    prob_complete = p ** L
    
    print(f"\nColumn {n}: Length {L}, P(sum)={p:.4f}")
    print(f"  P(complete in 1 turn) = {p:.4f}^{L} = {prob_complete:.8f}")
    print(f"  = 1 in {1/prob_complete:.0f} attempts")
    print(f"  Expected turns to complete: {1/prob_complete:.2f}")

# Now calculate with the more realistic model: 
# probability of making k steps of progress before busting
print("\n\n" + "="*70)
print("More realistic: Expected steps per turn (until bust)")
print("="*70)

for n in range(2, 13):
    L = column_lengths[n]
    p = column_probs[n]
    
    # Expected number of successful rolls before first failure
    # E[successes before failure] = p/(1-p)
    expected_steps = p / (1 - p)
    
    # Expected turns to complete L steps
    expected_turns = L / expected_steps
    
    print(f"Column {n}: p={p:.4f}, E[steps/turn]={expected_steps:.3f}, E[turns to complete]={expected_turns:.2f}")
