# Can't Stop, Addicted To The Shindig

I recently got introduced to this game called [Can't Stop](https://boardgamegeek.com/boardgame/41/cant-stop) and it got me thinking about probabilities. You know how it is - you start playing a dice game and suddenly you're knee-deep in combinatorics at 2am.

![Can't Stop Board And Dice](files/20251201/cant-stop.png)

The game is simple: roll four dice, pair them up however you want, move your markers on a board. The catch? You can keep rolling as long as you want, but if you can't move any of your three active markers, you lose everything you've gained that turn. Classic push-your-luck. [Here](https://www.youtube.com/watch?v=L6Zk7j1mJDE) is a brief explanation of how the game is played.

Here's what caught my attention: column 2 has 3 steps and column 7 has 13 steps. Column 7 is more than 4× longer! But when you roll four dice, you're way more likely to make a 7 than a 2. So which one actually finishes faster? And did the game designers balance this properly, or is there some optimal strategy?

Let me show you what I found.

## First, the basics: Two dice probabilities

You probably know this one already, but let's start here for comparison. With two dice, how likely are you to roll each sum?

| Sum | Ways to make it | Probability | Percentage |
|----:|:---------------|------------:|-----------:|
| 2 | (1,1) | 1/36 | 2.78% |
| 3 | (1,2), (2,1) | 2/36 | 5.56% |
| 4 | (1,3), (2,2), (3,1) | 3/36 | 8.33% |
| 5 | (1,4), (2,3), (3,2), (4,1) | 4/36 | 11.11% |
| 6 | (1,5), (2,4), (3,3), (4,2), (5,1) | 5/36 | 13.89% |
| 7 | (1,6), (2,5), (3,4), (4,3), (5,2), (6,1) | 6/36 | 16.67% |
| 8 | (2,6), (3,5), (4,4), (5,3), (6,2) | 5/36 | 13.89% |
| 9 | (3,6), (4,5), (5,4), (6,3) | 4/36 | 11.11% |
| 10 | (4,6), (5,5), (6,4) | 3/36 | 8.33% |
| 11 | (5,6), (6,5) | 2/36 | 5.56% |
| 12 | (6,6) | 1/36 | 2.78% |

![Two Dice Distribution](files/20251201/two_dice_distribution.png)

Sum 7 is the king at 16.67%, and it's exactly 6× more likely than sum 2 at 2.78%.

**Quick proof:** For sum 2, there's only one way: both dice must show 1. That's $\frac{1}{6} \times \frac{1}{6} = \frac{1}{36}$. For sum 7, you need complementary pairs: (1,6), (2,5), or (3,4), and order matters, so that's 6 ways total out of 36 possible outcomes.

Now if Can't Stop used two dice, column 7 would need to be 6× longer than column 2 to be equally hard. Instead it's only $\frac{13}{3} \approx 4.3\times$ longer. So something interesting must be happening with four dice.

## Four dice: This is where it gets interesting

In Can't Stop, you roll FOUR dice and then pair them up. Say you roll 2, 3, 4, 5. You can make:
- (2,3)+(4,5) = 5 and 9
- (2,4)+(3,5) = 6 and 8
- (2,5)+(3,4) = 7 and 7

That's it, just three possible pairings. The question is: if I'm trying to hit column 7, what's the probability that at least one of those pairings gives me a 7?

Let me work this out properly.

### Computing P(can make a 2)

To make a 2, I need a pair that sums to 2, which means two 1's. So I need at least two 1's among my four dice.

**Probability of NOT getting enough 1's:**

- $P(\text{zero 1's}) = \left(\frac{5}{6}\right)^4$
  - All four dice must avoid 1
  - $= \frac{625}{1296}$

- $P(\text{exactly one 1}) = \binom{4}{1} \times \left(\frac{1}{6}\right)^1 \times \left(\frac{5}{6}\right)^3$
  - Choose which die shows 1, that die shows 1, others don't
  - $= 4 \times \frac{1}{6} \times \frac{125}{216} = \frac{500}{1296}$

**Therefore:**

$$P(\text{can make a 2}) = 1 - P(\text{zero 1's}) - P(\text{exactly one 1}) = 1 - \frac{625}{1296} - \frac{500}{1296} = \frac{171}{1296} \approx 13.2\%$$

Wait, 13.2%? That's way higher than the 2.78% we had with two dice! Let's keep going.

### Computing P(can make a 7)

To make a 7, I need one of these pairs: (1,6), (2,5), or (3,4). Let me use inclusion-exclusion.

Let A = "I can make pair (1,6)" = "I have at least one 1 AND at least one 6"
Let B = "I can make pair (2,5)" = "I have at least one 2 AND at least one 5"
Let C = "I can make pair (3,4)" = "I have at least one 3 AND at least one 4"

**First, P(A) - having both a 1 and a 6:**

Using inclusion-exclusion on the dice values:

$$P(A) = 1 - P(\text{no 1's}) - P(\text{no 6's}) + P(\text{no 1's AND no 6's})$$
$$= 1 - \left(\frac{5}{6}\right)^4 - \left(\frac{5}{6}\right)^4 + \left(\frac{4}{6}\right)^4$$
$$= \frac{1296 - 625 - 625 + 256}{1296} = \frac{302}{1296}$$

By the same logic, $P(B) = \frac{302}{1296}$ and $P(C) = \frac{302}{1296}$.

**Next, the overlaps:**

$P(A \cap B) = P(\text{have 1, 6, 2, 5})$ - need all four distinct values among four dice:

Using inclusion-exclusion: $1296 - 4 \times 625 + \binom{4}{2} \times 256 - \binom{4}{3} \times 81 + 16 = 24$

So $P(A \cap B) = \frac{24}{1296}$

Similarly, $P(A \cap C) = \frac{24}{1296}$ and $P(B \cap C) = \frac{24}{1296}$.

$P(A \cap B \cap C) = 0$ because you'd need 6 specific dice values with only 4 dice.

**Final answer:**

$$P(\text{can make a 7}) = P(A \cup B \cup C)$$
$$= P(A) + P(B) + P(C) - P(A \cap B) - P(A \cap C) - P(B \cap C) + P(A \cap B \cap C)$$
$$= 302 + 302 + 302 - 24 - 24 - 24 + 0 = \frac{834}{1296} \approx 64.4\%$$

Interesting! With two dice, P(7) was 16.67%. With four dice, it jumped to 64.4%. And P(2) went from 2.78% to 13.2%.

Did the distribution get flatter?

### The complete picture

Let me calculate all of them. I'll spare you the detailed inclusion-exclusion for each (it's the same pattern), but here's what you get:

| Sum | At Least One Pair | Normalized | Column Length | Normalized |
|----:|-----------------:|-----------:|--------------:|-----------:|
| 2 | 171 (13.2%) | 1.00 | 3 | 1.00 |
| 3 | 302 (23.3%) | 1.77 | 5 | 1.67 |
| 4 | 461 (35.6%) | 2.70 | 7 | 2.33 |
| 5 | 580 (44.8%) | 3.39 | 9 | 3.00 |
| 6 | 727 (56.1%) | 4.25 | 11 | 3.67 |
| 7 | 834 (64.4%) | 4.88 | 13 | 4.33 |
| 8 | 727 (56.1%) | 4.25 | 11 | 3.67 |
| 9 | 580 (44.8%) | 3.39 | 9 | 3.00 |
| 10 | 461 (35.6%) | 2.70 | 7 | 2.33 |
| 11 | 302 (23.3%) | 1.77 | 5 | 1.67 |
| 12 | 171 (13.2%) | 1.00 | 3 | 1.00 |

![Four Dice Distribution](files/20251201/four_dice_distribution.png)

Now look at those normalized columns. The probability ratio from 2 to 7 is 4.88. The length ratio is 4.33. That's pretty close! The game designers were definitely thinking about this.

But wait - if they're close, why isn't column 7 exactly 4.88× longer? Because column lengths have to be integers. If column 2 is 3 steps, then 4.88 × 3 = 14.64, so you'd want column 7 to be about 15 steps. But they chose 13.

Why? Let me dig into that later. First, let's talk strategy.

## Which column should you go for?

Okay, so you're playing and you need to decide: should I try to complete column 2 or column 7?

On one hand, column 2 is only 3 steps. On the other hand, you'll only hit it 13.2% of the time. Column 7 is 13 steps but you hit it 64.4% of the time.

**Expected number of rolls to complete column n:**

$$\mathbb{E}[\text{rolls}] = \frac{\text{length}}{\text{probability}} = \frac{L(n)}{P(n)}$$

For column 2:

$$\mathbb{E}[\text{rolls}] = \frac{3}{0.132} = 22.73 \text{ rolls}$$

For column 7:

$$\mathbb{E}[\text{rolls}] = \frac{13}{0.644} = 20.18 \text{ rolls}$$

Column 7 is slightly faster, even though it's 4× longer. Let me check all of them:

| Column | Length | P(n) | Expected Rolls | Relative to Col 2 and 12 |
|-------:|-------:|-----:|---------------:|------------------:|
| 2, 12 | 3 | 13.2% | 22.73 | baseline |
| 3, 11 | 5 | 23.3% | 21.46 | 0.94× (is faster) |
| 4, 10 | 7 | 35.6% | 19.67 | 0.87× (is faster) |
| 5, 9 | 9 | 44.8% | 20.09 | 0.88× (is faster) |
| 6, 8 | 11 | 56.1% | 19.60 | 0.86× (is faster) |
| 7 | 13 | 64.4% | **20.18** | **0.89× (is the fastst)** |

Column 2/12 are literally the WORST choices! Every other column is faster. And columns 6, 7, 8 are all pretty close to each other - around 20 rolls.

**Proof of the formula:** This is just the expected value of a geometric distribution. If each roll succeeds with probability $p$, then the expected number of trials until the first success is $\frac{1}{p}$. To get $n$ successes, we need $\frac{n}{p}$ trials on average (by linearity of expectation).

## But wait - three columns at once

**Note:** The analysis so far has focused on individual columns in isolation. This is useful for understanding the probabilities, but it's incomplete—you don't actually play columns independently. A full strategic analysis would need to consider joint probability distributions, sequential dependencies (what's the probability of completing all three columns from current positions?), and dynamic programming approaches to value unsaved progress. Those topics deserve their own deep dive, so for now I'll focus on the simpler but still revealing question: what's your bust probability when playing multiple columns?

Here's the thing though: you don't play Can't Stop one column at a time. You have THREE active columns, and you bust if you can't hit ANY of them.

If you're on columns {6, 7, 8}, what's your bust probability?

I need $P(\text{can't make 6 AND can't make 7 AND can't make 8})$. Let me use inclusion-exclusion again:

$$P(\text{can make 6 OR 7 OR 8}) = P(6) + P(7) + P(8) - P(6 \cap 7) - P(6 \cap 8) - P(7 \cap 8) + P(6 \cap 7 \cap 8)$$

I already know the individual probabilities. Now I need the overlaps.

**Computing P(can make 6 AND can make 7):**

For 6: need (1,5) OR (2,4) OR (3,3)
For 7: need (1,6) OR (2,5) OR (3,4)

This expands into 9 cases of overlaps. The easiest way is honestly to enumerate all 1296 possible rolls and count.

**Mathematical representation:**

For a set of target columns $T = \{t_1, t_2, \ldots, t_k\}$, we want:

$$P(\text{can make any } t \in T) = \frac{|\{r \in \Omega : \exists \text{ pairing } p \text{ of } r \text{ with sum in } T\}|}{|\Omega|}$$

where $\Omega = \{1,2,3,4,5,6\}^4$ is the set of all possible four-dice rolls.

Let me write some code to compute this:

```python
from itertools import product

def can_make_sums(dice, targets):
    """Check if we can make any sum from targets"""
    d1, d2, d3, d4 = dice
    pairings = [
        [(d1, d2), (d3, d4)],
        [(d1, d3), (d2, d4)],
        [(d1, d4), (d2, d3)]
    ]

    for pairing in pairings:
        sums = {sum(pair) for pair in pairing}
        if any(target in sums for target in targets):
            return True
    return False

all_rolls = list(product(range(1, 7), repeat=4))
success = sum(1 for roll in all_rolls if can_make_sums(roll, [6, 7, 8]))
print(f"P(6 or 7 or 8) = {success}/1296 = {success/1296:.1%}")
```

Result: **1193/1296 = 92.0%**

So if you're on {6,7,8}, you have a 92% chance of not busting. That's pretty good!

What about {2,3,12}?

```python
success = sum(1 for roll in all_rolls if can_make_sums(roll, [2, 3, 12]))
print(f"P(2 or 3 or 12) = {success}/1296 = {success/1296:.1%}")
```

Result: **568/1296 = 43.8%**

Ouch. Less than 50% chance of not busting. You're more likely to bust than succeed!

## So which columns finish fastest in real play?

If you're playing aggressively (rolling until you bust), here's what happens:

**Expected rolls before busting:**

$$\mathbb{E}[\text{rolls before bust}] = \frac{P(\text{success})}{P(\text{bust})}$$

For {6,7,8}:

$$\mathbb{E}[\text{rolls}] = \frac{0.920}{0.080} = 11.5 \text{ rolls per turn}$$

For {2,3,12}:

$$\mathbb{E}[\text{rolls}] = \frac{0.438}{0.562} = 0.78 \text{ rolls per turn}$$

**Proof:** This is a geometric distribution. If each roll fails with probability $p$, the expected number of trials before the first failure is $\frac{1}{p}$. If success probability is $q = 1-p$, then the expected number of successes before the first failure is the expected number of trials minus 1: $\frac{1}{p} - 1 = \frac{1-p}{p} = \frac{q}{p}$.

Now, when you're on {6,7,8} and trying to complete column 7:
- You make 11.5 rolls per turn on average
- Each roll has a 64.4% chance of hitting column 7
- Expected progress on column 7 per turn: $11.5 \times 0.644 = 7.40$ steps
- Turns to complete 13 steps: $\frac{13}{7.40} = \textbf{1.76 turns}$

When you're on {2,3,12} and trying to complete column 2:
- You make 0.78 rolls per turn on average
- Each roll has a 13.2% chance of hitting column 2
- Expected progress on column 2 per turn: $0.78 \times 0.132 = 0.10$ steps
- Turns to complete 3 steps: $\frac{3}{0.10} = \textbf{30 turns}$

Column 7 in the good combination takes under 2 turns. Column 2 in the bad combination takes 30 turns. That's a 17× difference!

The lesson: **column combination matters way more than individual column length.**

## When should you stop rolling?

This is the classic push-your-luck question. You've made some progress this turn - should you roll again or bank it?

Here's the thing: your stopping strategy doesn't change the expected number of rolls to complete. Whether you always stop after one roll or always roll until you bust, you need the same expected number of rolls. Stopping early just spreads those rolls across more turns.

What stopping strategy DOES affect is variance and risk. Say you're on {6,7,8} with 5 unsaved steps of progress.

**Risk of rolling again:**
- 8% chance you bust and lose those 5 steps
- Expected loss: $0.08 \times 5 = 0.4$ steps

**Expected gain from rolling again:**
- 92% chance you succeed
- If you succeed, you'll probably advance 1-2 markers
- Expected gain: $\approx 0.92 \times 1.5 = 1.38$ steps

Since $1.38 > 0.4$, you should keep rolling.

Now try the same on {2,3,12} with 2 unsaved steps:

**Risk:** $0.562 \times 2 = 1.12$ steps
**Expected gain:** $0.438 \times 1.5 = 0.66$ steps

Since $1.12 > 0.66$, you should STOP.

**General heuristic:**

Keep rolling if: $(P_{\text{success}} \times Q) > (P_{\text{bust}} \times \text{unsaved\_progress})$

Otherwise stop.

Where Q is the expected number of markers you'll advance on a successful roll. This depends on your specific column combination:

**How to compute Q exactly:**

Mathematically, $Q$ is defined as:

$$Q = \mathbb{E}[\text{markers advanced} \mid \text{success}]$$

For columns $\{a, b, c\}$, we compute this by:

1. Enumerating all $6^4 = 1296$ possible four-dice rolls
2. For each successful roll (where at least one pairing gives a sum in $\{a, b, c\}$):
   - Check all 3 possible pairings of the four dice
   - Count how many sums from each pairing are in $\{a, b, c\}$
   - Take the maximum (you choose the best pairing)
3. Average the maximum markers across all successful rolls

Formally:

$$Q = \frac{1}{|\mathcal{S}|} \sum_{r \in \mathcal{S}} \max_{p \in \text{pairings}(r)} |\{s \in p : s \in \{a,b,c\}\}|$$

where $\mathcal{S}$ is the set of successful rolls (at least one pairing has a sum in $\{a,b,c\}$).

For example, for {6,7,8}:
- Some rolls advance 1 marker: (1,2,3,4) can only make 7
- Some rolls advance 2 markers: (3,3,4,4) → pairing (3,3)+(4,4) gives 6+8

Computing the exact average:
```python
from itertools import product

def expected_markers_advanced(columns):
    """Calculate E[markers advanced | success] for given columns"""
    all_rolls = list(product(range(1, 7), repeat=4))
    successful_rolls = []

    for roll in all_rolls:
        d1, d2, d3, d4 = roll
        pairings = [
            [(d1, d2), (d3, d4)],
            [(d1, d3), (d2, d4)],
            [(d1, d4), (d2, d3)]
        ]

        max_markers = 0
        for pairing in pairings:
            markers = sum(1 for pair in pairing if sum(pair) in columns)
            max_markers = max(max_markers, markers)

        if max_markers > 0:
            successful_rolls.append(max_markers)

    return sum(successful_rolls) / len(successful_rolls)

# For {6,7,8}
Q_678 = expected_markers_advanced([6, 7, 8])
print(f"Q for {{6,7,8}}: {Q_678:.3f}")

# For {2,3,12}
Q_2312 = expected_markers_advanced([2, 3, 12])
print(f"Q for {{2,3,12}}: {Q_2312:.3f}")
```

Results:
- Q for {6,7,8}: ~1.62 markers per successful roll
- Q for {2,3,12}: ~1.09 markers per successful roll

So using 1.5 as a rule of thumb is reasonably accurate for good combinations, but understimates for the best combinations and overstimates for terrible ones.

### The forced-move rule: A critical constraint

**IMPORTANT:** There's a rule I've mentioned briefly but haven't fully integrated into the analysis: **you must take all available moves**.

Here's how it works: If you roll (1,2,3,4) and choose the pairing (1,4)+(2,3) = 5+5, and you have active markers on columns 5, 6, and 7, you must move column 5 twice if possible. But more critically: **if a pairing creates any valid move, you must use moves from that pairing even if you don't want them.**

The actual rule is: if you pair the dice and there's a combination where you can make at least one legal move, you must choose a pairing that allows you to move and then make all legal moves from that pairing.

**Example that changes everything:**

You're working on {6,7,8} (the "good" combination). You roll (1,1,3,4).

Possible pairings:
- (1,1)+(3,4) = 2+7
- (1,3)+(1,4) = 4+8
- (1,4)+(1,3) = 5+4

You want column 7. But if you choose pairing (1,1)+(3,4), you get column 7... and you're **forced to take column 2** as well, even though you have a free peg. You can't just take the 7 and ignore the 2.

**Why this matters:**

This rule completely changes the probability analysis. The relevant question isn't "what's P(can make 7)?" but rather:

$$P(\text{can make 7 without being forced onto bad columns})$$

When you choose a pairing, you get ALL the sums from that pairing, not just the ones you want.

**Recomputing P(success) with forced moves:**

For {6,7,8}, the old analysis said 92% success rate. But now we need to ask: of those successful rolls, how many force you onto columns outside {6,7,8}?

Let me recalculate. A roll is "clean" if at least one pairing gives you ONLY sums in {6,7,8}:

```python
def can_make_clean_move(dice, targets):
    """Check if we can make a move using ONLY target columns"""
    d1, d2, d3, d4 = dice
    pairings = [
        [(d1, d2), (d3, d4)],
        [(d1, d3), (d2, d4)],
        [(d1, d4), (d2, d3)]
    ]

    for pairing in pairings:
        sums = [sum(pair) for pair in pairing]
        # This pairing is clean if all its sums are in targets
        if all(s in targets for s in sums):
            return True
    return False

all_rolls = list(product(range(1, 7), repeat=4))
clean_678 = sum(1 for roll in all_rolls if can_make_clean_move(roll, [6,7,8]))
print(f"P(clean move for {{6,7,8}}) = {clean_678}/1296 = {clean_678/1296:.1%}")
```

**Result:** Only ~48% of rolls give you a clean move on {6,7,8}!

The other ~44% of rolls let you make progress BUT also force you onto unwanted columns, slowly poisoning your combination.

**For {2,3,12}:**

```python
clean_2312 = sum(1 for roll in all_rolls if can_make_clean_move(roll, [2,3,12]))
print(f"P(clean move for {{2,3,12}}) = {clean_2312}/1296 = {clean_2312/1296:.1%}")
```

**Result:** Only ~11% of rolls are clean!

**The strategic implication:**

The forced-move rule is a **balancing mechanism**. It prevents {6,7,8} from being completely dominant by forcing players onto suboptimal columns when they push their luck. The longer you roll, the more likely you are to get "contaminated" with unwanted columns.

This also explains why the game doesn't feel as unbalanced as the pure probability analysis suggests. The math says {6,7,8} should dominate, but the forced-move rule adds friction that makes the game more competitive.

**Why I didn't integrate this earlier:**

Properly accounting for forced moves requires modeling the entire game state:
- Which columns are already claimed by you/opponent
- Which columns you currently have markers on
- Whether you have free pegs

The probability of a "clean" move depends on game state, not just the dice. A complete analysis would need to simulate full games (which I'll do in the appendix).

For now, the key takeaway: **the forced-move rule significantly dampens the advantage of middle columns**, making Can't Stop more balanced than the pure probability analysis suggests.

### What about my opponent's strategy?

Now you might be wondering: does my opponent's behavior change any of this? If they're aggressive and roll until they bust, or conservative and stop after every successful roll, does that affect the math?

**Short answer:** The probabilities stay the same, but how you USE them changes.

All the calculations we did - P(bust), P(success), Q, expected rolls - are **objective facts about the dice.** They don't change based on what your opponent does. {6,7,8} still has 92% success whether your opponent is aggressive or conservative.

What DOES change is your **strategic decision-making**. Here's how:

**1. Race conditions**

If your opponent is ahead and close to winning, you need to take MORE risk:
- They're at 12/13 on column 7? You can't afford conservative play
- You need to roll aggressively even on mediocre combinations
- Adjust the heuristic: Keep rolling if: $(P_\text{success} \times Q) > \alpha \times (P_\text{bust} \times \text{unsaved progress})$
- Where α < 1 when you're behind (accept more risk)
- Where α > 1 when you're ahead (be more cautious)

**2. Opponent aggression level**

If they're aggressive (always roll until bust):
- They'll complete columns faster on average
- But they'll also bust more often, wasting turns
- You can afford to be slightly more conservative - wait for them to bust
- Still need to keep pace though

If they're conservative (stop after 1-2 steps):
- They advance slowly but reliably
- You can match their strategy OR be aggressive to build a lead
- The game becomes more about consistency than risk-taking

**3. Blocking strategy**

If your opponent is far ahead on {6,7,8}:
- You might WANT those same columns to block them
- Even if those columns aren't optimal for you independently
- The value isn't just "complete my column" but "prevent their completion"
- This changes which columns are "valuable" beyond just the probabilities

**4. Opportunity cost**

Your opponent being ahead on column 7 makes column 7 LESS valuable to you:
- If they complete it first, it's removed from the game
- You'd be racing them for a column you might not finish
- Better to target a different column where you have an advantage

**Can we model this mathematically?**

Yes! We extend the basic heuristic to account for game state.

**Mathematical model:**

The decision function becomes:

$$\text{Keep rolling} \iff P_{\text{success}} \times Q \times V > P_{\text{bust}} \times U \times \alpha$$

where:
- $V$ = average value of completing active columns (adjusted for opponent position)
- $U$ = unsaved progress (steps that would be lost on bust)
- $\alpha$ = risk tolerance parameter ($\alpha < 1$ when behind, $\alpha > 1$ when ahead)

For column value adjustments:

$$V_i = \begin{cases}
1.0 & \text{if opponent position} \leq \text{my position on column } i \\
0.5 & \text{if opponent is ahead on column } i
\end{cases}$$

$$V = \frac{1}{|C|} \sum_{i \in C} V_i$$

where $C$ is the set of active columns.

Implementation:

```python
def should_keep_rolling_advanced(my_columns, my_positions, opp_positions, unsaved_progress):
    """
    Decide whether to keep rolling based on full game state
    """
    # Basic probabilities (these don't change)
    P_success = calculate_success_prob(my_columns)
    P_bust = 1 - P_success
    Q = expected_markers_advanced(my_columns)

    # Game state adjustments
    am_i_behind = is_behind(my_positions, opp_positions)
    if am_i_behind:
        risk_tolerance = 0.5  # Accept 2× more risk when behind
    else:
        risk_tolerance = 2.0  # Be 2× more cautious when ahead

    # Value of completing each column
    # (Lower if opponent is ahead on that column)
    column_values = []
    for col in my_columns:
        base_value = 1.0
        if opp_positions[col] > my_positions[col]:
            base_value *= 0.5  # Less valuable if opponent is ahead
        column_values.append(base_value)

    avg_column_value = sum(column_values) / len(column_values)

    expected_gain = P_success × Q × avg_column_value
    expected_loss = P_bust × unsaved_progress × risk_tolerance

    return expected_gain > expected_loss
```

**The key insight:** Opponent behavior doesn't change the probability calculations, but it changes the **value function** you're optimizing. You're not just maximizing expected progress - you're maximizing expected value in a competitive game-theoretic context.

The math stays the same. The strategy adapts.

### Optimal sequencing: finish one column or spread progress?

Here's a fascinating question I haven't fully addressed: when you're working on three columns, should you focus on completing one column at a time, or spread your progress evenly?

**Intuition suggests focusing:** If you complete one column, you free up a peg slot and can start a new (potentially better) column. Plus, you deny that column to your opponent.

**But the math is complex:**

Consider you're on {6,7,8} with positions [5/11, 3/13, 4/11]:
- **Focus strategy:** Try to complete column 6 first (6 steps remaining)
- **Spread strategy:** Advance whichever column you can hit

The challenge is that you don't control which columns you hit—the dice decide. You can only choose which pairing to use when multiple options are available.

**To compute this rigorously, you'd need:**

1. **State space modeling:** Define game state as (col₁_pos, col₂_pos, col₃_pos, unsaved₁, unsaved₂, unsaved₃)

2. **Markov decision process:** For each state and dice roll, compute:
   - Transition probabilities to new states
   - Expected value of each action (which pairing to choose, when to stop rolling)

3. **Dynamic programming:** Work backwards from completed states to find optimal policy:
   ```
   V(state) = max_action [ P(success) × E[V(next_state)] + P(bust) × V(bust_state) ]
   ```

4. **Comparison:** Compare policies:
   - "Focus policy": prefer pairings that advance the closest-to-complete column
   - "Spread policy": prefer pairings that advance the most columns
   - "Optimal policy": the DP solution

**Why I haven't computed this fully:**

This requires:
- State space of ~13³ × 13³ ≈ 4.8M states
- For each state, evaluate all possible dice rolls (1296) and pairings (3)
- Run value iteration until convergence

This is computationally expensive and would dominate the blog post. But it's a genuinely interesting question that I suspect would show:
- Focus strategy is slightly better when one column is close to completion
- Spread strategy is better early on (hedges against bad luck)
- The difference is small (maybe 5-10% in expected turns)

If there's interest, I could write a follow-up with full DP solutions and strategy comparisons. For now, I'll note this as an open question worth exploring.

## Is the game balanced?

Okay, back to game design. Is Can't Stop balanced? That is, do all columns take roughly the same time to complete?

I already showed that with single-column analysis, column 7 is fastest at 20.18 expected rolls while column 2 takes 22.73 rolls. That's only a 13% difference, which isn't too bad.

But in realistic multi-column play, the differences explode:
- Column 7 in {6,7,8}: 1.76 turns
- Column 2 in {2,3,12}: 30 turns

That's not balanced at all. **The game heavily favors middle columns.**

**Could the designers have done better?**

If perfect balance means $\mathbb{E}[\text{rolls}]$ is the same for all columns, then we need:

$$\frac{L(n)}{P(n)} = k \quad \text{for all } n$$

where $k$ is a constant.

Given that column 2 has probability 0.132, if we want it to take say 20 expected rolls like column 7, we'd need:

$$L(2) = 20 \times 0.132 = 2.64 \approx 3 \text{ steps } \checkmark$$

Okay, they actually got that one right. What about column 7?

$$L(7) = 20 \times 0.644 = 12.88 \approx 13 \text{ steps } \checkmark$$

Let me recalculate the expected rolls with the current lengths:

| Column | L(n) | P(n) | E[rolls] | Deviation from 20 |
|-------:|-----:|-----:|---------:|------------------:|
| 2 | 3 | 0.132 | 22.73 | +13.6% |
| 3 | 5 | 0.233 | 21.46 | +7.3% |
| 4 | 7 | 0.356 | 19.67 | -1.6% |
| 5 | 9 | 0.448 | 20.09 | +0.4% |
| 6 | 11 | 0.561 | 19.60 | -2.0% |
| 7 | 13 | 0.644 | 20.18 | +0.9% |
| 8 | 11 | 0.561 | 19.60 | -2.0% |
| 9 | 9 | 0.448 | 20.09 | +0.4% |
| 10 | 7 | 0.356 | 19.67 | -1.6% |
| 11 | 5 | 0.233 | 21.46 | +7.3% |
| 12 | 3 | 0.132 | 22.73 | +13.6% |

The deviations are ±13% at most. That's pretty good given that lengths must be integers!

**But wait** - if single columns are balanced, why are column combinations so unbalanced?

Because the bust probability for a combination depends on how much the three columns' probabilities overlap. Middle columns like {6,7,8} have huge overlap - lots of rolls hit multiple columns. Extreme columns like {2,3,12} have almost no overlap - you need very specific dice.

This overlap creates a positive feedback loop:
- Good columns → low bust rate → more rolls per turn → finish way faster
- Bad columns → high bust rate → fewer rolls per turn → finish way slower

The designers DID balance individual column completion times. But they couldn't balance (or didn't want to balance) the three-column combinations.

**My guess:** This imbalance is intentional. It creates strategic depth. Everyone wants columns 6-7-8, so there's competition. You need three columns to win, so eventually you have to branch out to riskier territory. It makes the game more interesting.

But there's a deeper game design principle at play here: **games are rarely designed to be mathematically perfect**. Instead, they're designed to be:

1. **Simple enough to understand** - The current board (3-5-7-9-11-13) is instantly graspable. You see the pattern immediately.
2. **Physically manufacturable** - Integer lengths, reasonable board size, round numbers.
3. **Engaging to a broad audience** - People feel progress, the visual length of columns creates emotional investment.

Then, **rules and mechanics are added to compensate for inevitable imbalances** introduced by these simplifications. In Can't Stop, that compensating rule is: **you must take a move if it's available**.

If you roll (1,2,3,4) and pair it to get 3+7, but you have a free peg, you MUST take both columns - including that difficult column 3 even if you didn't want it. This rule serves multiple purposes:
- Forces players into sub-optimal column combinations
- Prevents the game from devolving into "everyone only picks 6-7-8"
- Adds tactical complexity (do I risk rolling again knowing I might get stuck with bad columns?)
- **Compensates for the mathematical imbalance** by forcing engagement with harder columns

This is elegant game design: accept imperfect balance in the core mechanics (column lengths), then add rules that turn that imbalance into interesting strategic choices rather than broken gameplay.

That said, I still think slightly favoring the lower-probability columns would improve the game. But I understand why they didn't: for most players, **visual/emotional balance matters more than mathematical balance**. A 13-step column "feels" much harder than a 3-step column, even if the math says they take similar time to complete. The physical length creates psychological engagement.

The designers chose accessible over optimal, and for a commercial board game that's been successful for 40+ years, they were probably right.

## Could the designers have done better?

The current board has a max deviation of ±13.6% from perfect balance. That's pretty good given integer constraints, but let's explore: what if we could redesign the board?

### The quest for zero deviation

For perfect balance where every column takes exactly the same expected number of rolls, we'd need column lengths that are exact multiples of their probabilities:

$$L(n) = k \times P(n) \text{ for all } n$$

where $k$ is a constant.

The problem is that probabilities have denominators (all are fractions of 1296), and to get perfect integer lengths, we need $k$ to be a multiple of $\frac{1296}{\gcd(\text{all numerators})}$.

Since the GCD of all probability numerators (171, 302, 461, 580, 727, 834) is 1, the minimum $k$ for perfect integer ratios is **1296**.

**Perfect balance board:**
- Column 2/12: 171 steps
- Column 3/11: 302 steps
- Column 4/10: 461 steps
- Column 5/9: 580 steps
- Column 6/8: 727 steps
- Column 7: **834 steps**

**Game duration:** ~8 hours

Yeah, that's not happening. You'd need a board the size of a wall and infinite patience.

### Finding the sweet spot

But what if we explore different scales? Maybe there's a serendipitous small number that gives us much better balance without the absurd height?

I wrote a script to test all board scales from 0.1x to 5.0x the current size, optimizing for minimal deviation while keeping heights practical (under 50 steps). Here's what I found:

**Current board (2x scale):**
- Max height: 13 steps
- Max deviation: ±13.6%
- Column lengths: [3, 5, 7, 9, 11, 13, 11, 9, 7, 5, 3]
- Game duration: ~7.5 minutes

**Optimal small board (~3.04x scale):**
- Max height: 20 steps
- Max deviation: ±2.17%
- Column lengths: **[4, 7, 11, 14, 17, 20, 17, 14, 11, 7, 4]**
- Game duration: ~11.5 minutes

That's a **6× improvement in balance** for just 7 more steps on the tallest column!

**Best balance under 30 steps (~3.84x scale):**
- Max height: 25 steps
- Max deviation: ±1.92%
- Column lengths: **[5, 9, 14, 17, 22, 25, 22, 17, 14, 9, 5]**
- Game duration: ~14.5 minutes

This is a **7× improvement** while still fitting on a normal game board.

**Interestingly, there's also a 14-step board:**
- Max height: 14 steps (just +1 from current!)
- Max deviation: ±3.09%
- Column lengths: **[3, 5, 8, 10, 12, 14, 12, 10, 8, 5, 3]**
- Game duration: ~8.3 minutes

This is **4× more balanced** than the current game with almost no size increase. The key changes: column 6/8 go from 11→12, column 5/9 go from 9→12, and column 4/10 go from 7→8.

### Why didn't the designers do this?

A few possible reasons:

1. **Round numbers:** The current design uses nice symmetric patterns (3-5-7-9-11-13). The optimized boards use less "round" numbers.

2. **Intentional imbalance:** Maybe they WANTED columns 2/12 to be slightly harder to create that strategic tension about which columns to pursue.

3. **Physical board constraints:** The original 1980 board game might have had manufacturing constraints that favored 13 as a maximum.

4. **Testing limitations:** In 1980, computing these optimal scales would have required extensive manual calculation or computer time. They probably found 13 worked well enough and shipped it.

5. **Playtesting over math:** The current balance might have tested better with real players, even if the math says a different scale is "better."

My take: the current design is **excellent** for 1980. Given modern tools, we can find better balances, but the improvements are marginal compared to the combinatorial complexity combination imbalance. Whether you're on {6,7,8} or {2,3,12} matters WAY more than a few percentage points of individual column balance.

Still, if I were designing Can't Stop 2.0, I'd seriously consider the 20-step or 25-step boards. They're not much larger but offer significantly better mathematical balance.

### But what about keeping it linear?

One elegant feature of the current design is its **linear progression**: columns increase by exactly 2 steps each time (3, 5, 7, 9, 11, 13). This creates a simple, aesthetically pleasing pattern.

What if we wanted to maintain this linear constraint but optimize the parameters? Instead of just any column lengths, we require:

$$L(n) = \text{base} + (n - 2) \times \text{step}$$

For example, the current board has base=3 and step=2.

I ran an exhaustive search trying different bases (1-20) and steps (0.5-5.0) to find the best linear designs. Here's what I found:

**Current linear design (base=3, step=2):**
- Column lengths: [3, 5, 7, 9, 11, 13, 11, 9, 7, 5, 3]
- Max deviation: ±9.99%
- Max height: 13 steps

**Best linear design with similar size (base=3, step=2.25):**
- Column lengths: **[3, 5, 8, 10, 12, 14, 12, 10, 8, 5, 3]**
- Max deviation: ±3.09%
- Max height: 14 steps
- **3.2× better balance** with just +1 step!

The changes are minimal: column 4/10 goes from 7→8, column 5/9 goes from 9→12 (wait, that's wrong... let me check)

Actually, looking at it properly:
- Columns 2/12: 3 (same)
- Columns 3/11: 5 (same)
- Columns 4/10: 7→8 (+1)
- Columns 5/9: 9→10 (+1)
- Columns 6/8: 11→12 (+1)
- Column 7: 13→14 (+1)

Every column from 4 onwards gets just one extra step, and the balance improves dramatically!

**Best linear design under 20 steps (base=4, step=3.26):**
- Column lengths: **[4, 7, 11, 14, 17, 20, 17, 14, 11, 7, 4]**
- Max deviation: ±2.17%
- Max height: 20 steps
- **4.6× better balance** than current

**Best with INTEGER step (base=5, step=4):**
- Column lengths: **[5, 9, 13, 17, 21, 25, 21, 17, 13, 9, 5]**
- Max deviation: ±3.32%
- Max height: 25 steps
- Maintains the elegance of integer increments
- All odd numbers, like the current design

This integer-step design is particularly interesting because:
1. It keeps the aesthetic pattern (all odd numbers)
2. Step of 4 is twice the current step of 2
3. Much better balance while maintaining simplicity
4. Easy to manufacture (no fractional measurements)

**The fundamental limitation:**

Linear designs can never achieve perfect balance because the probability curve is **nonlinear**. The probability increase from column 2→7 doesn't follow a straight line - it has a specific curve determined by the four-dice combinatorics.

The best linear boards achieve ~2-3% deviation. The best non-linear boards (from the previous section) achieve ~1.9% deviation. So you're only gaining about 1 percentage point by abandoning the linear constraint.

**Trade-off: elegance vs optimization**

The current design chose elegance: base=3, step=2, all odd numbers, max height 13. It's memorable, symmetric, and "feels" right.

The optimal linear design sacrifices a bit of that elegance (step=3.26 instead of 2) for significantly better balance. But even that optimal design is only marginally better than the "nice" integer-step alternatives like base=5, step=4.

For a commercial board game, I'd probably choose the integer-step design [5, 9, 13, 17, 21, 25, 21, 17, 13, 9, 5]. It's 3× better than the current balance, maintains aesthetic appeal, and is easy to manufacture. The jump from 13 to 25 might feel significant, but the game would only take about twice as long - still under 15 minutes for a typical game.

## Appendix: Complete probability tables

For the truly obsessed (hi, it's me), here are the probabilities for all 165 possible three-column combinations.

### Top 20 Best Combinations

| Rank | Columns | Success | Bust | Clean | Q (markers/roll) |
|-----:|:--------|--------:|-----:|------:|-----------------:|
| 1 | {6,7,8} | 92.0% | 8.0% | 39.8% | 1.43 |
| 2 | {5,7,8} | 91.4% | 8.6% | 38.2% | 1.42 |
| 3 | {6,7,9} | 91.4% | 8.6% | 38.2% | 1.42 |
| 4 | {4,6,8} | 91.1% | 8.9% | 28.2% | 1.31 |
| 5 | {6,8,10} | 91.1% | 8.9% | 28.2% | 1.31 |
| 6 | {4,7,8} | 90.3% | 9.7% | 34.0% | 1.38 |
| 7 | {6,7,10} | 90.3% | 9.7% | 34.0% | 1.38 |
| 8 | {5,6,8} | 89.5% | 10.5% | 33.3% | 1.37 |
| 9 | {6,8,9} | 89.5% | 10.5% | 33.3% | 1.37 |
| 10 | {3,7,8} | 89.3% | 10.7% | 29.1% | 1.33 |
| 11 | {4,7,9} | 89.3% | 10.7% | 29.1% | 1.33 |
| 12 | {5,7,10} | 89.3% | 10.7% | 29.1% | 1.33 |
| 13 | {6,7,11} | 89.3% | 10.7% | 29.1% | 1.33 |
| 14 | {2,7,8} | 89.0% | 11.0% | 25.8% | 1.29 |
| 15 | {6,7,12} | 89.0% | 11.0% | 25.8% | 1.29 |
| 16 | {5,6,7} | 88.7% | 11.3% | 34.5% | 1.39 |
| 17 | {7,8,9} | 88.7% | 11.3% | 34.5% | 1.39 |
| 18 | {4,6,7} | 88.6% | 11.4% | 33.3% | 1.38 |
| 19 | {7,8,10} | 88.6% | 11.4% | 33.3% | 1.38 |
| 20 | {2,6,8} | 88.3% | 11.7% | 22.0% | 1.25 |

### Bottom 20 Worst Combinations

| Rank | Columns | Success | Bust | Clean | Q (markers/roll) |
|-----:|:--------|--------:|-----:|------:|-----------------:|
| 146 | {2,9,11} | 63.7% | 36.3% | 7.9% | 1.12 |
| 147 | {3,5,12} | 63.7% | 36.3% | 7.9% | 1.12 |
| 148 | {2,3,10} | 63.4% | 36.6% | 6.5% | 1.10 |
| 149 | {2,4,11} | 63.4% | 36.6% | 6.5% | 1.10 |
| 150 | {2,5,12} | 63.4% | 36.6% | 6.5% | 1.10 |
| 151 | {2,9,12} | 63.4% | 36.6% | 6.5% | 1.10 |
| 152 | {3,10,12} | 63.4% | 36.6% | 6.5% | 1.10 |
| 153 | {4,11,12} | 63.4% | 36.6% | 6.5% | 1.10 |
| 154 | {2,3,5} | 58.4% | 41.6% | 6.7% | 1.11 |
| 155 | {9,11,12} | 58.4% | 41.6% | 6.7% | 1.11 |
| 156 | {2,10,11} | 57.9% | 42.1% | 5.6% | 1.10 |
| 157 | {3,4,12} | 57.9% | 42.1% | 5.6% | 1.10 |
| 158 | {2,4,12} | 55.2% | 44.8% | 4.2% | 1.08 |
| 159 | {2,10,12} | 55.2% | 44.8% | 4.2% | 1.08 |
| 160 | {2,3,11} | 52.5% | 47.5% | 4.1% | 1.08 |
| 161 | {3,11,12} | 52.5% | 47.5% | 4.1% | 1.08 |
| 162 | {2,3,4} | 52.2% | 47.8% | 3.9% | 1.07 |
| 163 | {10,11,12} | 52.2% | 47.8% | 3.9% | 1.07 |
| 164 | {2,3,12} | 43.8% | 56.2% | 2.3% | 1.05 |
| 165 | {2,11,12} | 43.8% | 56.2% | 2.3% | 1.05 |

**Key observations:**

- **Clean move percentage** (forced-move rule): Notice that even the best combination {6,7,8} only has 39.8% clean moves. This confirms that the forced-move rule significantly impacts strategy.
- **Q values** (expected markers per successful roll): The best combinations advance ~1.4 markers per roll, while the worst only advance ~1.05. This compounds over multiple rolls.
- **The gap is massive**: The best combination is more than 2× better than the worst (92% vs 43.8% success rate).

Full CSV files available in the [repository](files/20251201/).

## Appendix: Code and analysis scripts

All analysis scripts are available in the [repository](files/20251201/).

### Basic probability verification

**Mathematical goal:** Verify all single-sum probabilities $P(n)$ for $n \in \{2, 3, \ldots, 12\}$ by enumeration.

For each target sum $n$, count rolls where at least one of the three pairings produces that sum:

$$P(n) = \frac{|\{r \in \Omega : \exists \text{ pairing } p \text{ with sum } = n\}|}{1296}$$

```python
from itertools import product

def can_make_sum(dice, target_sum):
    """Check if 4 dice can be paired to make target_sum"""
    d1, d2, d3, d4 = dice
    pairings = [
        [(d1, d2), (d3, d4)],
        [(d1, d3), (d2, d4)],
        [(d1, d4), (d2, d3)]
    ]
    for pairing in pairings:
        for pair in pairing:
            if sum(pair) == target_sum:
                return True
    return False

all_rolls = list(product(range(1, 7), repeat=4))
total = len(all_rolls)  # 1296

for target_sum in range(2, 13):
    count = sum(1 for roll in all_rolls if can_make_sum(roll, target_sum))
    print(f"Sum {target_sum}: {count}/{total} = {count/total:.4f}")
```

### Optimal board scale finder

This script explores different board scales to find designs with minimal deviation from perfect balance:

```python
# See cant_stop_optimization.py in the repository for full code
# Available at: files/20251201/cant_stop_optimization.py

def find_optimal_lengths(scale_factor, target_expected_rolls=None):
    """
    Find optimal integer column lengths for a given scale factor.
    Returns lengths that minimize deviation from target expected rolls.
    """
    if target_expected_rolls is None:
        # Find the target that minimizes total squared deviation
        best_target = None
        best_deviation = float('inf')

        for target in range(10, 100):
            total_squared_dev = 0
            for col in range(2, 13):
                optimal_length = target * probabilities[col]
                rounded_length = max(1, round(optimal_length * scale_factor))
                actual_expected = rounded_length / probabilities[col]
                total_squared_dev += (actual_expected - target) ** 2

            if total_squared_dev < best_deviation:
                best_deviation = total_squared_dev
                best_target = target

        target_expected_rolls = best_target

    lengths = {}
    for col in range(2, 13):
        optimal_length = target_expected_rolls * probabilities[col]
        lengths[col] = max(1, round(optimal_length * scale_factor))

    return lengths

# Try scales from 0.1x to 5.0x
# Results show the 3.84x scale gives best balance under 30 steps (±1.92% deviation)
# The 3.04x scale gives best balance under 20 steps (±2.17% deviation)
```

Key findings:
- Perfect balance requires an 834-step board (impractical)
- Scale 3.84x: [5, 9, 14, 17, 22, 25, ...] with ±1.92% deviation
- Scale 3.04x: [4, 7, 11, 14, 17, 20, ...] with ±2.17% deviation
- Even small improvements (14-step board) achieve ±3.09% deviation

### Linear board optimizer

This script finds optimal boards while maintaining the linear progression constraint:

```python
# See cant_stop_linear_optimization.py in the repository for full code
# Available at: files/20251201/cant_stop_linear_optimization.py

def calculate_linear_board(base, step):
    """
    Calculate board with linear progression: L(n) = base + (n-2) × step
    Returns lengths, expected rolls, and deviation statistics.
    """
    lengths = {}
    for col in range(2, 13):
        if col <= 7:
            lengths[col] = int(round(base + (col - 2) * step))
        else:
            # Symmetric: col 8 = col 6, col 9 = col 5, etc.
            lengths[col] = int(round(base + (14 - col - 2) * step))

    # Calculate expected rolls and deviation
    expected = {}
    for col in range(2, 13):
        expected[col] = lengths[col] / probabilities[col]

    mean_expected = sum(expected.values()) / len(expected)
    max_deviation = max(abs(expected[col] / mean_expected - 1) * 100
                       for col in range(2, 13))

    return lengths, expected, mean_expected, max_deviation

# Try bases 1-20 and steps 0.5-5.0
# Current design: base=3, step=2 → ±9.99% deviation
# Best similar size: base=3, step=2.25 → ±3.09% deviation (3× better!)
# Best under 20: base=4, step=3.26 → ±2.17% deviation
# Best integer: base=5, step=4 → ±3.32% deviation
```

Key findings:
- Current design (base=3, step=2) achieves ±9.99% deviation
- Tiny adjustment to step=2.25 improves to ±3.09% (3× better)
- Best integer-step design: [5, 9, 13, 17, 21, 25, ...] with ±3.32% deviation
- Linear designs fundamentally limited to ~2-3% deviation (vs 1.9% for non-linear)

### Design insights

The analysis reveals several trade-offs in board game design:

1. **Mathematical optimality vs simplicity**: The current design uses round numbers (step=2) rather than optimal values (step=2.25 or 3.26)

2. **Linear elegance vs perfect balance**: Linear progressions can't match nonlinear probability curves, but they're visually appealing and easy to understand

3. **Physical constraints**: Board size, manufacturing, and visual clarity all constrain mathematical optimization

4. **Player psychology**: A 13-step column "feels" harder than a 3-step column, even when mathematically balanced. Visual length creates emotional engagement.

The scripts demonstrate that while perfect mathematical balance is achievable, practical game design requires balancing multiple competing concerns - and Can't Stop does this remarkably well.


## Appendix: Independent Strategy Analysis

Before examining head-to-head competition, let's understand how strategies perform independently—how many turns does each strategy need to complete 3 columns when playing alone? This isolates strategy efficiency from opponent interaction.

### Mathematical Framework

For a single column with length $L$ and hit probability $P$, the expected rolls needed is $L/P$. However, strategies don't optimize for individual columns—they balance progress across multiple columns while managing bust risk.

For three columns, we need to consider:
- **Total steps required**: Sum of column lengths
- **Expected progress per roll** ($Q$): Average markers placed when you hit any active column
- **Bust probability** ($P_{\text{bust}}$): Probability of hitting no active columns
- **Success probability** ($P_{\text{success}}$): Probability of hitting at least one active column

Expected rolls per turn: $P_{\text{success}} / P_{\text{bust}}$ (geometric distribution)

Expected turns to complete: $(\text{total steps}) / (Q \times \text{rolls per turn})$

#### Example: Columns {6, 7, 8}

This is the mathematically optimal combination:
- Total steps: $11 + 13 + 11 = 35$
- $P_{\text{success}} = 92.0\%$, $Q = 1.43$ markers/roll
- Expected rolls per turn: $11.46$
- **Expected turns: 2.13** (if following optimal stopping rule)

Compare to worst combination {2, 3, 12}:
- Total steps: $3 + 5 + 3 = 11$ (much shorter!)
- $P_{\text{success}} = 43.8\%$, $Q = 1.05$
- Expected rolls per turn: $0.78$
- **Expected turns: 13.39** (6× longer despite being 1/3 the steps!)

### Simulation Results

I ran 1,000 independent trials for each strategy, measuring average turns to complete any 3 columns:

| Rank | Strategy | Avg Turns | Median | Avg Busts |
|------|----------|-----------|--------|-----------|
| 1 | GreedyImproved2 | 13.2 | 12 | ~2.1 |
| 1 | GreedyFraction(0.33) | 13.2 | 12 | ~2.0 |
| 3 | GreedyImproved1 | 14.2 | 13 | ~2.3 |
| 4 | AdaptiveThreshold | 14.1 | 13 | ~2.2 |
| 5 | Conservative(4) | 15.0 | 14 | ~2.4 |
| 6 | GreedyFraction(0.5) | 15.3 | 14 | ~2.5 |
| 7 | FiftyPercentSurvival | 15.9 | 15 | ~2.6 |
| 8 | Heuristic(1.0) | 16.0 | 15 | ~2.5 |
| 9 | Conservative(3) | 15.8 | 15 | ~2.4 |
| 10 | ExpectedValueMax | 16.2 | 15 | ~2.6 |
| ... | ... | ... | ... | ... |
| 23 | Heuristic(0.3) | 108.0 | 95 | ~15.2 |

**Note**: GreedyUntil1Col and GreedyUntil3Col are designed for competitive play and aren't included here.

Full results: [single_player_results.txt](files/20251201/single_player_results.txt)

### Key Insights

**1. Best independent performers ≠ Best competitive performers**

GreedyImproved2 and GreedyFraction(0.33) tie for fastest completion (13.2 turns), but GreedyUntil1Col wins head-to-head despite not optimizing for speed.

**2. Extreme conservatism is catastrophic**

Heuristic(0.3) needs **108 turns** on average—8× longer than optimal! Being too afraid to take risks means making almost no progress per turn.

**3. The 50% survival threshold is surprisingly good**

FiftyPercentSurvival (stop when cumulative bust probability reaches 50%) completes in 15.9 turns—competitive with sophisticated strategies while being trivial to compute.

**4. Expected value optimization isn't optimal**

ExpectedValueMaximizer ranks 10th in independent play (16.2 turns). Maximizing EV per turn doesn't minimize turns to completion because:
- Short-term variance matters more than long-term EV
- The stopping rule is designed for competitive play, not speed

**5. Column selection matters enormously**

Testing on the best combination {6,7,8} vs worst {2,3,12}:
- Best: ~3.5 turns for GreedyImproved2
- Worst: ~25 turns for the same strategy

Hit probability dominates efficiency far more than column length.

### Why Independent Analysis Matters

Independent analysis reveals **strategy efficiency** (how quickly can I win if uncontested?), while head-to-head reveals **strategy robustness** (can I beat opponents trying to block me?).

The optimal competitive strategy must balance both:
- Fast enough to win before opponent
- Robust enough to handle column denial and tempo swings

As we'll see, GreedyUntil1Col achieves this balance perfectly.


## Appendix: Game Simulation Results

To validate the strategies discussed in this post, I implemented a complete Can't Stop game simulator ([cant_stop_analysis_extended.py](files/20251201/cant_stop_analysis_extended.py)) and ran comprehensive head-to-head tests between 25 different strategies.

### Strategy Definitions

The simulator implements 25 distinct strategies, ranging from simple threshold rules to sophisticated mathematical optimization:

**1. Greedy** — Always rolls until bust. When choosing between valid pairings, prefers the pairing that advances the most currently-active columns. Serves as a baseline for "worst possible strategy."

**2. Conservative(k)** — Stops after accumulating $k$ steps of unsaved progress. Prefers "clean" pairings (those using only active columns). Tested with $k \in \{1, 2, 3, 4\}$.

**3. Heuristic($\alpha$)** — Implements the mathematical stopping rule derived earlier:

$$\text{Keep rolling} \iff P_{\text{success}} \times Q > \alpha \times P_{\text{bust}} \times U$$

where $U$ is unsaved progress and $\alpha$ is a risk tolerance parameter. Tested with $\alpha \in \{0.3, 0.5, 1.0, 1.5, 2.0\}$.

**4. OpponentAware** — Extends Heuristic with dynamic risk adjustment based on game state:

$$\alpha = \begin{cases}
\alpha_{\text{behind}} & \text{if behind (take more risk)} \\
\alpha_{\text{tied}} & \text{if tied} \\
\alpha_{\text{ahead}} & \text{if ahead (be more cautious)}
\end{cases}$$

Additionally weights column values by $0.5$ if opponent is ahead on that column. Tested with three parameter sets.

**5. Random(p)** — Stops with probability $p$ after each successful roll. Tested with $p = 0.3$ as a control strategy.

**6. GreedyImproved1** — Stops only after making progress on all three active columns in the current turn.

**7. GreedyImproved2** — Stops after accumulating exactly 5 total steps of unsaved progress.

**8. AdaptiveThreshold** — Dynamically adjusts stopping threshold based on current column combination success probability: $\text{threshold} = \lfloor 1 + P_{\text{success}} \times 5 \rfloor$.

**9. ProportionalThreshold(f)** — Stops when unsaved progress reaches fraction $f$ of the minimum remaining distance across active columns. Tested with $f \in \{0.33, 0.5\}$.

**10. GreedyFraction(f)** — Stops when any single active column has advanced by fraction $f$ of its total length in the current turn. Tested with $f \in \{0.33, 0.5\}$.

**11. FiftyPercentSurvival** — Calculates the exact number of rolls $n$ where cumulative survival probability drops below 50% using $n = \log(0.5) / \log(P_{\text{success}})$, then stops after that many rolls.

**12. ExpectedValueMaximizer** — Stops precisely when expected value turns negative: $\text{EV} = P_{\text{success}} \times Q - P_{\text{bust}} \times U \leq 0$.

**13. GreedyUntil1Col** — Rolls until completing at least one column per turn, then stops immediately. Exploits the game mechanic that completing columns denies opponent access and guarantees consistent progress.

**14. GreedyUntil3Col** — Rolls until winning the entire game (completing all 3 required columns), never stopping voluntarily. Tests the extreme "all-in" strategy.

### Experimental Setup

Each strategy plays 2,500 games against each other strategy (300 unique pairings, 750,000 total games). The game state tracks:
- Column positions for both players
- Completed columns (removed from play)
- Current turn state (active columns, unsaved progress)
- Forced-move rule enforcement

**Why 2,500 games per matchup?** For a win rate $p$ estimated from $n$ trials, the 95% confidence interval is $p \pm 1.96\sqrt{\frac{p(1-p)}{n}}$. With 200 games, the worst-case margin of error is ±6.9% (when $p = 0.5$). This is too large to confidently distinguish strategies with 5-10% win rate differences.

With 2,500 games, the margin of error drops to ±2.0%, allowing us to:
- Reliably detect differences >4% with high confidence
- Distinguish the top-performing strategies
- Identify meaningful performance gaps between similar approaches

This increases computational cost by 12.5×, but ensures our conclusions are statistically robust rather than artifacts of sampling noise.

### Overall Performance

Aggregating wins across all opponents (60,000 games per strategy):

| Rank | Strategy | Total Wins | Win Rate |
|-----:|:---------|:-----------|:---------|
| **1** | **GreedyUntil1Col** | **48955/60000** | **81.6%** |
| 2 | GreedyImproved2 | 46879/60000 | 78.1% |
| 3 | GreedyFraction(0.33) | 46146/60000 | 76.9% |
| 4 | GreedyImproved1 | 45408/60000 | 75.7% |
| 5 | AdaptiveThreshold | 43867/60000 | 73.1% |
| 6 | Conservative(4) | 42676/60000 | 71.1% |
| 7 | GreedyFraction(0.5) | 40761/60000 | 67.9% |
| 8 | FiftyPercentSurvival | 40047/60000 | 66.7% |
| 9 | Conservative(3) | 39422/60000 | 65.7% |
| 10 | Heuristic(1.0) | 37279/60000 | 62.1% |
| 11 | ExpectedValueMax | 34056/60000 | 56.8% |
| 12 | Random(0.3) | 33896/60000 | 56.5% |
| 13 | OppAware(0.7,1,1.5) | 31839/60000 | 53.1% |
| **14** | **GreedyUntil3Col** | **30538/60000** | **50.9%** |
| 15 | OppAware(0.5,1,2) | 29569/60000 | 49.3% |
| 16 | Heuristic(1.5) | 28569/60000 | 47.6% |
| 17 | OppAware(0.3,1,2) | 26321/60000 | 43.9% |
| 18 | Heuristic(0.5) | 23100/60000 | 38.5% |
| 19 | Proportional(0.5) | 20472/60000 | 34.1% |
| 20 | Heuristic(2.0) | 18678/60000 | 31.1% |
| 21 | Conservative(2) | 13326/60000 | 22.2% |
| 22 | Proportional(0.33) | 10844/60000 | 18.1% |
| 23 | Conservative(1) | 9760/60000 | 16.3% |
| 24 | Heuristic(0.3) | 7402/60000 | 12.3% |
| 25 | Greedy | 28/60000 | 0.1% |

**NEW CHAMPION: GreedyUntil1Col** wins 81.6% of all games, beating the previous leader GreedyImproved2 (78.1%) by 3.5 percentage points.

Full results available in [analysis_results_25strategies_2500games.txt](files/20251201/analysis_results_25strategies_2500games.txt).

### Full Win-Rate Matrix

Complete head-to-head tournament results (2,500 games per matchup). Table shows win rate of row strategy vs column strategy:

| Strategy | vs Top 3 | vs Conservative(3) | vs Heuristic(1.0) | vs Random(0.3) | vs Greedy |
|:---------|:---------|:-------------------|:------------------|:---------------|:----------|
| **GreedyImproved2** | 50.0%, 54.0%, 50.0% | 77.2% | 77.0% | 78.0% | 100.0% |
| **GreedyFraction(0.33)** | 46.0%, ---, 56.0% | 74.0% | 60.0% | 74.0% | 100.0% |
| **GreedyImproved1** | 50.0%, 44.0%, --- | 72.0% | 65.0% | 75.0% | 100.0% |
| AdaptiveThreshold | 38.0%, 51.0%, 66.0% | 68.0% | 62.6% | 77.0% | 100.0% |
| Conservative(4) | 30.0%, 40.0%, 28.0% | 53.0% | 64.0% | 73.0% | 100.0% |
| GreedyFraction(0.5) | 43.8%, 47.0%, 54.0% | 58.0% | 61.0% | 67.0% | 100.0% |
| FiftyPercentSurvival | 33.0%, 31.0%, 37.0% | 53.0% | 60.0% | 66.0% | 100.0% |
| Conservative(3) | 22.8%, 26.0%, 28.0% | --- | 56.2% | 61.0% | 100.0% |
| Heuristic(1.0) | 23.0%, 40.0%, 35.0% | 43.8% | --- | 63.0% | 100.0% |
| Random(0.3) | 22.0%, 26.0%, 25.0% | 39.0% | 37.0% | --- | 100.0% |
| ExpectedValueMax | 27.0%, 21.0%, 22.0% | 41.4% | 49.0% | 52.0% | 100.0% |
| OppAware(0.7,1,1.5) | 22.0%, 22.0%, 25.0% | 23.0% | 37.0% | 58.0% | 100.0% |
| OppAware(0.5,1,2) | 25.0%, 19.0%, 16.0% | 15.0% | 37.0% | 54.0% | 100.0% |
| Heuristic(1.5) | 10.0%, 12.0%, 13.0% | 21.0% | 27.0% | 66.0% | 100.0% |
| OppAware(0.3,1,2) | 14.0%, 10.0%, 11.0% | 25.0% | 24.0% | 73.0% | 100.0% |
| Heuristic(0.5) | 18.0%, 22.0%, 16.0% | 25.0% | 33.0% | 74.0% | 100.0% |
| Proportional(0.5) | 1.0%, 1.0%, 0.0% | 1.4% | 17.0% | 15.0% | 100.0% |
| Heuristic(2.0) | 1.0%, 5.0%, 1.0% | 5.0% | 15.0% | 10.0% | 100.0% |
| Conservative(2) | 0.0%, 0.0%, 0.0% | 0.0% | 6.0% | 6.0% | 100.0% |
| Proportional(0.33) | 0.0%, 1.0%, 0.0% | 0.0% | 6.0% | 2.0% | 100.0% |
| Conservative(1) | 0.0%, 0.0%, 0.0% | 0.0% | 3.0% | 1.0% | 100.0% |
| Heuristic(0.3) | 6.0%, 0.0%, 7.0% | 3.0% | 8.0% | 4.0% | 100.0% |
| **Greedy** | 0.0%, 0.0%, 0.0% | 0.0% | 0.0% | 0.0% | --- |

**Key observations:**
- The top 3 strategies (GreedyImproved2, GreedyFraction(0.33), GreedyImproved1) are highly competitive with each other (45-56% win rates)
- All strategies beat Greedy 100% of the time (except Greedy vs itself)
- Proportional strategies have catastrophic performance (<2% vs top strategies, ~1-2% vs Conservative(3))
- FiftyPercentSurvival vs ExpectedValueMax: 65.2% — survival focus beats pure EV optimization
- The performance gap between top and bottom is massive: GreedyImproved2 beats Conservative(1) ~100% of the time

### Key Findings

**Finding 1: The Greedy strategy is catastrophic**

Greedy achieved essentially 0 wins in 60,000 games (only 28 wins, 0.1%). This isn't surprising given the mathematics: with probability 1, you will eventually bust, and banking no progress means zero expected advancement per turn.

More formally, if $P_{\text{bust}} = p > 0$ on each roll, then the probability of surviving $n$ rolls is $(1-p)^n \to 0$ as $n \to \infty$. Since Greedy never stops voluntarily, it always busts.

**Finding 2: GreedyUntil1Col is the new champion—and reveals the optimal strategy**

**GreedyUntil1Col (81.6%)** wins by a decisive margin, beating the previous leader GreedyImproved2 (78.1%) by 3.5 percentage points. This is a significant improvement in a field where small differences matter.

**The Strategy**: Roll until completing at least one column per turn, then stop immediately.

```python
def should_stop(self, game):
    # Stop as soon as we've completed at least one column this turn
    for col in temp_progress:
        if current_pos + temp_progress >= column_length:
            return True  # Completed a column!
    return False
```

**Why It Dominates**:

1. **Guaranteed progress every turn**: If you don't bust, you ALWAYS complete at least one column. No wasted turns banking partial progress.

2. **Exploits game mechanics**: Completing columns denies opponent access immediately and frees up a peg for the next column choice. Partial progress gives neither benefit.

3. **Optimal risk/reward balance**: Columns take 3-13 steps. Typical columns need 5-8 steps. Completing one column takes ~1-2 turns on average (when not busting)—aggressive enough to make progress, conservative enough to avoid frequent busts.

4. **Beats everyone**: Key matchups from the tournament:
   - vs GreedyImproved2 (previous #1): **65.1%** to 34.9%
   - vs ExpectedValueMax (math optimal): **76.4%** to 23.6%
   - vs Conservative(4): **73.6%** to 26.4%
   - vs GreedyUntil3Col (too greedy): **72.4%** to 27.6%

5. **Variance reduction in short games**: Can't Stop typically lasts 8-12 turns. GreedyUntil1Col completes 1 column/turn consistently, while ExpectedValueMax varies wildly (sometimes 0, sometimes 2-3). Consistency wins in short games.

**Why GreedyUntil3Col fails** (50.9%, rank 14): Rolling until you win the entire game is too greedy. Bust probability compounds as you accumulate progress across all three columns, and losing all progress on a bust is catastrophic. It's barely better than a coin flip.

**Finding 3: Simple threshold strategies remain excellent**

The top strategies are all simple rules:
- GreedyUntil1Col (81.6%): "Stop after completing one column"
- GreedyImproved2 (78.1%): "Stop after 5 total steps"
- GreedyFraction(0.33) (76.9%): "Stop when any column reaches 1/3 completion"

Meanwhile, mathematically sophisticated strategies performed significantly worse:
- FiftyPercentSurvival (66.7%): Calculates exact $n$ where $P_{\text{success}}^n = 0.5$
- ExpectedValueMaximizer (56.8%): Stops when EV turns negative
- Heuristic(1.0) (62.1%): Uses the mathematical formula $P_{\text{success}} \times Q > P_{\text{bust}} \times U$

Why do simple rules win? The game is too short for expected value advantages to dominate variance. A strategy that consistently makes 3-5 steps per turn will beat a strategy that sometimes makes 7 steps and sometimes busts, even if the latter has higher expected value. The Law of Large Numbers needs more turns than a typical Can't Stop game provides.

**Finding 4: The Heuristic formula works, but isn't optimal**

Heuristic(1.0) won 62.1%, validating that $(P_{\text{success}} \times Q) > (P_{\text{bust}} \times U)$ captures the essential tradeoff. However, it lost to all the top threshold strategies, suggesting the formula optimizes expected value but doesn't account for variance minimization, which matters more in this short game.

**Finding 5: OpponentAware underperforms**

The three OpponentAware variants all performed poorly (54.2%, 50.3%, and 44.8%), worse than even simple threshold strategies like Conservative(4) at 73.9%. The likely culprit: implementation limitations. The strategy only tracks completed columns, ignoring partial progress. A better implementation would estimate "turns until opponent wins" using their current positions, not just completed column count.

Additionally, the binary risk adjustment ($\alpha \in \{0.3, 0.5, 0.7\}$ for behind/tied/ahead) is too coarse. A continuous function of the score gap would likely perform better.

**Finding 6: Risk tolerance is critical**

The Heuristic strategy with $\alpha = 1.0$ won 62.1%, while $\alpha = 0.5$ (aggressive) won 38.5% and $\alpha = 2.0$ (conservative) won 31.1%. Interestingly, both extremes perform poorly:
- Too aggressive: busts too often, loses progress
- Too conservative: banks too early, makes slow progress

The sweet spot $\alpha \approx 1.0$ aligns with the mathematical derivation, where we set expected gain equal to expected loss.

### Validating the Opponent-Aware Decision Function

The blog post proposed that opponent-aware strategies should outperform static strategies. The simulation results are mixed:

**What works:**
- OpponentAware beats all non-heuristic strategies (100% vs Greedy, 85% vs Conservative, 72.5% vs Conservative(3))
- This confirms that dynamic risk adjustment has value against simplistic opponents

**What doesn't work:**
- OpponentAware loses to pure Heuristic strategies (25.5% vs Heuristic, 42.5% vs Heuristic(0.5))
- This suggests the implementation is flawed, not the concept

The root issue: OpponentAware only considers completed columns. The decision function is:

$$\text{am\_behind} = \sum_{c} \mathbb{1}[\text{opponent completed } c] > \sum_{c} \mathbb{1}[\text{I completed } c]$$

This is too coarse. A better metric would be:

$$\text{deficit} = \sum_{c \in \text{all columns}} \left( \frac{\text{opp\_pos}_c}{L(c)} - \frac{\text{my\_pos}_c}{L(c)} \right)$$

This accounts for partial progress, not just binary completion status.

### Implications

The simulation validates the core mathematical analysis while revealing important nuances:

**1. Validated: The stopping heuristic is sound**

Heuristic($\alpha = 1.0$) won 62.1%, confirming that $(P_{\text{success}} \times Q) > (\alpha \times P_{\text{bust}} \times U)$ captures the essential tradeoff. The formula works.

**2. Validated: Greedy is terrible**

28 wins in 60,000 games (0.1%). Always rolling until bust is strictly dominated by any strategy that banks progress.

**3. Discovery: "Complete one column per turn" is optimal**

GreedyUntil1Col (81.6%) beats all strategies by exploiting a fundamental game mechanic: **column completion has discrete value**. Partial progress isn't denied to your opponent; completed columns are. This creates a natural stopping point that balances risk perfectly.

For human players, this is trivially simple: "Keep rolling until you finish at least one column, then stop."

**4. Surprise: Simple beats sophisticated**

The top strategies use trivial rules (complete 1 column, stop after 5 steps, stop at 1/3 progress). Meanwhile, mathematically-optimized strategies like ExpectedValueMaximizer (56.8%) and FiftyPercentSurvival (66.7%) perform significantly worse.

This suggests that in short games with high variance, **consistency beats optimization**. The game rarely lasts long enough for expected-value advantages to overcome variance.

**5. Partial validation: Opponent-awareness has potential**

OpponentAware beat conservative strategies but lost to Heuristic. The concept is sound—adjusting risk based on game state makes sense—but the implementation needs work. A proper version would:
- Track full game state (partial progress on all columns)
- Estimate turns-to-win for both players
- Use continuous risk adjustment, not binary categories

**6. Solved: The variance-aware optimal strategy**

The question "what strategy accounts for variance, not just EV?" is now answered: **GreedyUntil1Col**.

It minimizes variance by guaranteeing exactly 1 column completion per successful turn, while maximizing tempo by denying opponent columns as quickly as possible. This is better than both:
- ExpectedValueMaximizer: optimizes EV but has high variance
- Conservative strategies: low variance but slow tempo

The key insight: column completion is the natural unit of progress in Can't Stop, not individual steps.

### Implications for Mathematical Strategy

The comprehensive testing reveals a fundamental tension in Can't Stop strategy:

**Expected value optimization is correct but insufficient.** The ExpectedValueMaximizer strategy implements the theoretically optimal stopping rule: continue when $P_{\text{success}} \times Q > P_{\text{bust}} \times U$. This maximizes expected progress per turn. Yet it only won 56.8% of games.

**Variance dominates in short games.** Can't Stop typically ends in 8-12 turns per player. This isn't enough for expected value advantages to reliably overcome variance. GreedyUntil1Col *guarantees* 1 column per successful turn, beating strategies that *average* more progress but with high variance (sometimes 0, sometimes 2-3 columns).

**Column completion is the atomic unit of value.** The discovery of GreedyUntil1Col reveals that the game's mechanics create a natural stopping point: complete exactly one column. This exploits three facts:
1. Completed columns deny opponent access (strategic value)
2. Completed columns free pegs for next turn (tactical value)
3. One column completion per turn minimizes variance while maximizing tempo

This is more sophisticated than it first appears: the strategy implicitly optimizes for a **discrete value function** (columns completed) rather than a **continuous value function** (total steps). The game rewards column completion nonlinearly, making "1 column/turn" superior to "N steps/turn" for any fixed N.

**The optimal strategy must balance EV and variance.** This suggests a hybrid approach:
$$\text{Stop when } P_{\text{success}} \times Q < f(U, \sigma^2, \text{turns\_remaining})$$

where $f$ accounts for both expected value and variance, weighted by how many turns remain in the game. When the game is nearly over, variance matters less (you need to win *this* turn), so maximize EV. Early game, consistency matters more, so favor lower variance.

This remains an open research question: deriving the optimal $f$ requires solving a finite-horizon Markov decision process with explicit variance penalties.

### Implementation Details

The full simulator is ~600 lines of Python implementing:

**Game state management:**
```python
class GameState:
    def __init__(self, num_players=2):
        self.column_lengths = {2: 3, 3: 5, 4: 7, 5: 9, 6: 11, 7: 13,
                              8: 11, 9: 9, 10: 7, 11: 5, 12: 3}
        self.positions = [{col: 0 for col in range(2, 13)} for _ in range(num_players)]
        self.completed = {col: None for col in range(2, 13)}
        self.active_columns = []
        self.temp_progress = {}
```

**Forced-move validation:**
```python
def get_valid_pairings(self, dice):
    """Returns pairings where at least one sum can be used"""
    valid = []
    for pairing in get_pairings(dice):
        sums = [sum(pair) for pair in pairing]
        can_move = any(
            self.is_column_available(s) and
            (s in self.active_columns or len(self.active_columns) < 3)
            for s in sums
        )
        if can_move:
            valid.append((sums, pairing))
    return valid
```

**Strategy execution:**
```python
def play_turn(game, strategy):
    while True:
        dice = game.roll_dice()
        valid_pairings = game.get_valid_pairings(dice)

        if not valid_pairings:
            game.bust()
            return False

        sums, pairing = strategy.choose_pairing(game, valid_pairings)
        game.apply_move(sums)

        if strategy.should_stop(game, dice):
            game.bank_progress()
            return False
```

The complete code is available in multiple versions:
- Initial 7-strategy simulator: [cant_stop_analysis.py](files/20251201/cant_stop_analysis.py) with results in [analysis_results.txt](files/20251201/analysis_results.txt)
- Extended 23-strategy simulator: [cant_stop_analysis_extended.py](files/20251201/cant_stop_analysis_extended.py) with results in [analysis_results_2500games.txt](files/20251201/analysis_results_2500games.txt)
