# Mathematical Formulas for P(n) - Individual Probabilities

## The Challenge

For a sum S, we need to find P(can make sum S with 4 dice).

**Key insight:** We can make sum S if at least one of the three pairings contains at least one pair (a,b) where a+b=S.

## Classification by Sum Type

### Type 1: Sums requiring identical dice (S=2, S=12)

**Sum 2:** Need at least one pair (1,1)
- Requires at least two 1's among 4 dice

**Formula:**
P(at least two 1's) = 1 - P(zero 1's) - P(exactly one 1)

P(zero 1's) = (5/6)⁴ = 625/1296

P(exactly one 1) = C(4,1) × (1/6)¹ × (5/6)³ = 4 × (1/6) × (125/216) = 500/1296

**P(2) = 1 - 625/1296 - 500/1296 = 171/1296**

By symmetry: **P(12) = 171/1296**

---

### Type 2: Sums requiring one specific pair (S=3, S=11)

**Sum 3:** Need pair (1,2) or (2,1)
- Requires at least one 1 AND at least one 2

**Formula using inclusion-exclusion:**
P(at least one 1 AND at least one 2) = 1 - P(no 1's) - P(no 2's) + P(no 1's AND no 2's)

P(no 1's) = (5/6)⁴ = 625/1296
P(no 2's) = (5/6)⁴ = 625/1296
P(no 1's AND no 2's) = (4/6)⁴ = 256/1296

**P(3) = 1296 - 625 - 625 + 256 = 302/1296**

By symmetry: **P(11) = 302/1296**

---

### Type 3: Sums with two options, one requiring doubles (S=4, S=10)

**Sum 4:** Need pair (1,3), (3,1), OR (2,2)
- Option A: at least one 1 AND at least one 3
- Option B: at least two 2's

**Using inclusion-exclusion on options:**
P(A or B) = P(A) + P(B) - P(A and B)

**P(A) = at least one 1 AND at least one 3:**
= 1 - P(no 1's) - P(no 3's) + P(no 1's AND no 3's)
= 1296 - 625 - 625 + 256 = 302/1296

**P(B) = at least two 2's:**
= 1 - P(zero 2's) - P(exactly one 2)
= 1 - (5/6)⁴ - C(4,1)(1/6)(5/6)³
= 1 - 625/1296 - 500/1296 = 171/1296

**P(A and B) = at least one 1, one 3, AND two 2's:**
This requires at least 4 specific values: {1,2,2,3}

Count rolls with pattern {1,2,2,3}:
- Multinomial coefficient: 4!/(1!×2!×1!) = 12 arrangements

**P(4) = 302 + 171 - 12 = 461/1296**

By symmetry: **P(10) = 461/1296**

---

### Type 4: Sums with two distinct pairs (S=5, S=9)

**Sum 5:** Need pair (1,4), (4,1) OR (2,3), (3,2)
- Option A: at least one 1 AND at least one 4
- Option B: at least one 2 AND at least one 3

**P(A) = at least one 1 AND at least one 4:**
= 1296 - 625 - 625 + 256 = 302/1296

**P(B) = at least one 2 AND at least one 3:**
= 1296 - 625 - 625 + 256 = 302/1296

**P(A and B) = at least one each of {1,2,3,4}:**
= 1 - P(missing at least one of {1,2,3,4})

Using inclusion-exclusion on which values are missing:
- P(missing 1) = (5/6)⁴ = 625
- P(missing 2) = (5/6)⁴ = 625
- P(missing 3) = (5/6)⁴ = 625
- P(missing 4) = (5/6)⁴ = 625
- P(missing 1,2) = (4/6)⁴ = 256
- P(missing 1,3) = (4/6)⁴ = 256
- P(missing 1,4) = (4/6)⁴ = 256
- P(missing 2,3) = (4/6)⁴ = 256
- P(missing 2,4) = (4/6)⁴ = 256
- P(missing 3,4) = (4/6)⁴ = 256
- P(missing 1,2,3) = (3/6)⁴ = 81
- P(missing 1,2,4) = (3/6)⁴ = 81
- P(missing 1,3,4) = (3/6)⁴ = 81
- P(missing 2,3,4) = (3/6)⁴ = 81
- P(missing all) = (2/6)⁴ = 16

By inclusion-exclusion:
P(have all of {1,2,3,4}) = 1296 - 4×625 + 6×256 - 4×81 + 16
                         = 1296 - 2500 + 1536 - 324 + 16 = 24/1296

**P(5) = 302 + 302 - 24 = 580/1296**

By symmetry: **P(9) = 580/1296**

---

### Type 5: Sums with three options, one requiring doubles (S=6, S=8)

**Sum 6:** Need (1,5), (5,1) OR (2,4), (4,2) OR (3,3)
- Option A: at least one 1 AND at least one 5
- Option B: at least one 2 AND at least one 4
- Option C: at least two 3's

P(A) = 302/1296
P(B) = 302/1296
P(C) = 171/1296

Now we need all the intersections:

**P(A∩B):** at least one each of {1,2,4,5}
Using inclusion-exclusion (similar to above): 24/1296

**P(A∩C):** at least one 1, one 5, AND two 3's
Pattern {1,3,3,5}: 4!/2! = 12 arrangements

**P(B∩C):** at least one 2, one 4, AND two 3's
Pattern {2,3,3,4}: 4!/2! = 12 arrangements

**P(A∩B∩C):** at least one each of {1,2,4,5} AND two 3's
Impossible with 4 dice (need at least 6 values)
P(A∩B∩C) = 0

**P(6) = 302 + 302 + 171 - 24 - 12 - 12 + 0 = 727/1296**

By symmetry: **P(8) = 727/1296**

---

### Type 6: Sum with three distinct pairs (S=7)

**Sum 7:** Need (1,6), (6,1) OR (2,5), (5,2) OR (3,4), (4,3)
- Option A: at least one 1 AND at least one 6
- Option B: at least one 2 AND at least one 5
- Option C: at least one 3 AND at least one 4

P(A) = P(B) = P(C) = 302/1296

**P(A∩B):** at least one each of {1,2,5,6} = 24/1296

**P(A∩C):** at least one each of {1,3,4,6} = 24/1296

**P(B∩C):** at least one each of {2,3,4,5} = 24/1296

**P(A∩B∩C):** at least one each of {1,2,3,4,5,6}
With only 4 dice, we can have at most 4 distinct values.
Need to count 4-dice rolls using all 4 values from {1,2,3,4,5,6}:

Number of ways to choose 4 values from 6: C(6,4) = 15
For each choice, number of rolls: 4! = 24 (each die gets a distinct value)
Total: 15 × 24 = 360 rolls... but wait!

Actually, we need "at least one each of all 6", which is impossible with 4 dice.
**P(A∩B∩C) = 0**

**P(7) = 302 + 302 + 302 - 24 - 24 - 24 + 0 = 834/1296**

---

## Summary Table

| Sum | Type | Formula | Count | P(n) |
|----:|:-----|:--------|------:|-----:|
| 2 | Doubles | 1 - (5/6)⁴ - C(4,1)(1/6)(5/6)³ | 171 | 171/1296 |
| 3 | One pair | 1296 - 2×625 + 256 | 302 | 302/1296 |
| 4 | Mixed | 302 + 171 - 12 | 461 | 461/1296 |
| 5 | Two pairs | 302 + 302 - 24 | 580 | 580/1296 |
| 6 | Three opts | 302 + 302 + 171 - 24 - 12 - 12 | 727 | 727/1296 |
| 7 | Three pairs | 302 + 302 + 302 - 24 - 24 - 24 | 834 | 834/1296 |
| 8 | Three opts | (by symmetry with 6) | 727 | 727/1296 |
| 9 | Two pairs | (by symmetry with 5) | 580 | 580/1296 |
| 10 | Mixed | (by symmetry with 4) | 461 | 461/1296 |
| 11 | One pair | (by symmetry with 3) | 302 | 302/1296 |
| 12 | Doubles | (by symmetry with 2) | 171 | 171/1296 |

## Key Patterns

1. **Symmetry:** P(n) = P(14-n) for all n

2. **Peak at 7:** Sum 7 has the most pair options (3 distinct pairs), giving highest probability

3. **Base formula (one pair):** For sums needing exactly one type of complementary pair:
   P = 1296 - 2×625 + 256 = 302/1296

4. **Doubles penalty:** Requiring two of the same value (like (1,1)) is harder:
   P = 1296 - 625 - 500 = 171/1296

5. **Multiple options help:** Each additional way to make the sum increases probability, but intersections reduce the gain
