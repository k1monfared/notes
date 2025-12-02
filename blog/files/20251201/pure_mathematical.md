# Pure Mathematical Calculation for P(at least one of {2, 3, 12})

## Setup

Rolling 4 dice gives us (d₁, d₂, d₃, d₄) where each dᵢ ∈ {1,2,3,4,5,6}.

We have 3 ways to pair them:
1. (d₁, d₂) + (d₃, d₄)
2. (d₁, d₃) + (d₂, d₄)
3. (d₁, d₄) + (d₂, d₃)

We succeed if **at least one pairing** contains **at least one pair** that sums to one of our targets: {2, 3, 12}.

## Step 1: Calculate P(can make sum = 2)

To make sum 2, we need at least one pair (a,b) where a+b=2.
The only way: (1,1)

So we need at least two 1's among our 4 dice.

**Method 1: Complement**
- P(no 1's) = (5/6)⁴ = 625/1296
- P(exactly one 1) = C(4,1) × (1/6)¹ × (5/6)³ = 4 × 125/1296 = 500/1296
- P(at least two 1's) = 1 - 625/1296 - 500/1296 = **171/1296**

But wait! Having two 1's doesn't guarantee we can make 2 in a pairing!

**Method 2: More careful analysis**

We need a pairing where (1,1) appears. Consider all rolls with at least two 1's:
- If we have (1,1,a,b) where a,b ∈ {1,2,3,4,5,6}: then pairing 1 gives us (1,1)+(a,b) ✓

Actually, if we have at least two 1's, at least one of our three pairings MUST pair them together:
- Pairing 1: (d₁,d₂) + (d₃,d₄)
- Pairing 2: (d₁,d₃) + (d₂,d₄)
- Pairing 3: (d₁,d₄) + (d₂,d₃)

If 1's are at positions i and j, then one of these pairings pairs them.

**Verification**: P(can make 2) = 171/1296 ✓

## Step 2: Calculate P(can make sum = 3)

To make sum 3, we need a pair (a,b) where a+b=3:
- (1,2) or (2,1)

So we need at least one 1 and at least one 2 among our 4 dice.

**Using inclusion-exclusion:**
- Total rolls: 6⁴ = 1296
- Rolls with no 1: 5⁴ = 625
- Rolls with no 2: 5⁴ = 625
- Rolls with no 1 AND no 2: 4⁴ = 256

Rolls with at least one 1 AND at least one 2:
= 1296 - 625 - 625 + 256 = 302

But again, this only works if some pairing pairs a 1 with a 2.

After enumeration: **P(can make 3) = 302/1296** ✓

## Step 3: Calculate P(can make sum = 12)

By symmetry with sum = 2:
**P(can make 12) = 171/1296** ✓

## Step 4: Calculate intersections

### P(can make 2 AND 3)

Need at least two 1's (for sum 2) AND {at least one 1 and one 2} (for sum 3).

This simplifies to: at least two 1's AND at least one 2.

Count rolls with pattern: {1,1,2,x} where x ∈ {1,2,3,4,5,6}
- Different arrangements of {1,1,2,1}: C(4,3) × 1 = 4 ways
- Different arrangements of {1,1,2,2}: C(4,2) × 1 = 6 ways
- Different arrangements of {1,1,2,3}: 4!/2! = 12 ways
- Different arrangements of {1,1,2,4}: 4!/2! = 12 ways
- Different arrangements of {1,1,2,5}: 4!/2! = 12 ways
- Different arrangements of {1,1,2,6}: 4!/2! = 12 ways

Total: 4 + 6 + 12 + 12 + 12 + 12 = **58** rolls

**P(can make 2 AND 3) = 58/1296** ✓

### P(can make 2 AND 12)

Need at least two 1's AND at least two 6's.

Only possible with pattern {1,1,6,6}:
- Arrangements: 4!/(2!×2!) = 6

**P(can make 2 AND 12) = 6/1296** ✓

### P(can make 3 AND 12)

Need {at least one 1 and one 2} AND at least two 6's.

Patterns: {1,2,6,6} and {2,6,6,6} and {1,6,6,6}... wait, we need the 1 AND 2.

Pattern {1,2,6,6} only:
- Arrangements: 4!/(2!) = 12

**P(can make 3 AND 12) = 12/1296** ✓

### P(can make ALL three: 2 AND 3 AND 12)

Need: at least two 1's, at least one 2, AND at least two 6's.
This requires at least 5 dice: {1,1,2,6,6} - impossible with only 4 dice!

**P(can make 2 AND 3 AND 12) = 0/1296** ✓

## Step 5: Apply Inclusion-Exclusion

P(at least one of {2,3,12}) = P(2) + P(3) + P(12) - P(2∩3) - P(2∩12) - P(3∩12) + P(2∩3∩12)

= 171 + 302 + 171 - 58 - 6 - 12 + 0

= **568/1296**

= **43.8%**

Therefore: **P(Bust) = 728/1296 = 56.2%**

## Key Insights

1. **Inclusion-exclusion is necessary** because rolls can satisfy multiple conditions (e.g., {1,1,2,3} can make both 2 and 3)

2. **The pairing structure matters**: Having the right dice values isn't enough - they must be pairable. But if you have at least two of the same value, at least one of the three pairings will pair them.

3. **Symmetry**: P(sum = 2) = P(sum = 12) due to the symmetry of dice around 7: if (d₁,d₂,d₃,d₄) can make sum S, then (7-d₁, 7-d₂, 7-d₃, 7-d₄) can make sum 14-S.

4. **Why it's worst**: Sums 2, 3, and 12 require extreme dice values (1's and 6's) which rarely coexist in a single roll. The best combination (6,7,8) uses the most common sums around 7.
