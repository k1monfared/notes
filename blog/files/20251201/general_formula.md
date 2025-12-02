# General Formula for Any 3-Column Combination

## The General Inclusion-Exclusion Formula

For any three target sums {a, b, c}:

**P(Success) = P(a) + P(b) + P(c) - P(a∩b) - P(a∩c) - P(b∩c) + P(a∩b∩c)**

Where P(x) means "probability of rolling 4 dice such that at least one pairing can make sum x"

## Computing Each Component

### Step 1: Dice Requirements for Each Sum

For sum S where 2 ≤ S ≤ 12, we need at least one pair (d₁, d₂) where d₁ + d₂ = S.

The possible pairs for sum S are all (a, b) where:
- 1 ≤ a, b ≤ 6
- a + b = S

**Examples:**
- Sum 2: only (1,1) → need at least **two 1's**
- Sum 3: (1,2) or (2,1) → need at least **one 1 AND one 2**
- Sum 7: (1,6), (2,5), (3,4), (4,3), (5,2), (6,1) → need any of these pairs
- Sum 12: only (6,6) → need at least **two 6's**

### Step 2: Computing P(can make sum S)

For a specific sum S, count all rolls (d₁, d₂, d₃, d₄) that contain the dice values needed for at least one of the possible pairs.

**Key insight:** If the sum requires the same die value twice (like (1,1) for sum 2), you need at least 2 of that value. Otherwise, you need at least 1 of each value in the pair.

**General algorithm:**
```
For sum S:
  possible_pairs = all (a,b) where a+b=S and 1≤a,b≤6

  For each roll in all 6⁴ possible rolls:
    For each possible_pair (a,b):
      count_a = number of times a appears in roll
      count_b = number of times b appears in roll

      If a == b:
        if count_a >= 2: roll succeeds for sum S
      Else:
        if count_a >= 1 AND count_b >= 1: roll succeeds for sum S
```

### Step 3: Computing Intersections P(a ∩ b)

A roll can make both sum a AND sum b if it satisfies the requirements for both.

**Example:** {2, 3, 12}
- P(2∩3): Need at least two 1's (for sum 2) AND at least one 2 (for sum 3)
  - Rolls like {1,1,2,x} work
  - Count: 58 rolls

- P(2∩12): Need at least two 1's AND at least two 6's
  - Only rolls like {1,1,6,6}
  - Count: 6 rolls (just different orderings)

- P(3∩12): Need at least one 1, one 2, AND two 6's
  - Only rolls like {1,2,6,6}
  - Count: 12 rolls

- P(2∩3∩12): Would need two 1's, one 2, AND two 6's = 5 dice minimum
  - **Impossible with only 4 dice!**
  - Count: 0

### Step 4: Pattern Recognition

**Symmetry:** Due to dice symmetry around 7, we have:
- P(sum = S) = P(sum = 14-S)
- If (a,b,c) has probability p, then (14-a, 14-b, 14-c) also has probability p

**Examples:**
- P(2) = P(12) = 171/1296
- P(3) = P(11) = 302/1296
- P(4) = P(10) = 461/1296
- P(6) = P(8) = 727/1296
- P(7) = 834/1296 (most common, symmetric with itself)

## Computational Complexity

**Naive approach:** Enumerate all 6⁴ = 1,296 possible rolls (what we've been doing)

**Pure mathematical:**
- For simple cases like {2,3,12}, we can count multisets analytically
- For complex cases like {6,7,8}, enumeration is more practical
- The general pattern involves multinomial coefficients and inclusion-exclusion

## Why {6,7,8} is Best and {2,3,12} is Worst

Looking at the individual probabilities:

**{6,7,8}:**
- P(6) = 56.1% (many ways: (1,5), (2,4), (3,3))
- P(7) = 64.4% (most ways: (1,6), (2,5), (3,4))
- P(8) = 56.1% (many ways: (2,6), (3,5), (4,4))
- High overlap → lots of rolls satisfy multiple conditions
- Result: 92.0% success rate

**{2,3,12}:**
- P(2) = 13.2% (only way: (1,1))
- P(3) = 23.3% (only ways: (1,2))
- P(12) = 13.2% (only way: (6,6))
- Low overlap → few rolls satisfy multiple conditions
- Requires extreme values (1's and 6's) that rarely coexist
- Result: 43.8% success rate

**The key:** Middle sums (6,7,8) have:
1. More pairs that add up to them
2. More common dice values needed
3. Greater overlap between requirements
4. Higher individual probabilities that compound nicely

Extreme sums (2,3,12) have:
1. Fewer pairs (often just one)
2. Require rare extreme values
3. Little overlap (need 1's AND 6's)
4. Low individual probabilities that compound poorly
