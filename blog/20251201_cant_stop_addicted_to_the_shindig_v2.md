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

**Proof:** This is a geometric distribution. If each roll fails with probability $p$, the expected number of trials before the first failure is $\frac{1}{p}$. Equivalently, if success probability is $q$, we expect $\frac{q}{p}$ successes before failing, where $p = 1-q$, so $\frac{q}{p} = \frac{q}{1-q}$.

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

### What about my opponent's strategy?

Now you might be wondering: does my opponent's behavior change any of this? If they're aggressive and roll until they bust, or conservative and stop after every successful roll, does that affect the math?

**Short answer:** The probabilities stay the same, but how you USE them changes.

All the calculations we did - P(bust), P(success), Q, expected rolls - are **objective facts about the dice.** They don't change based on what your opponent does. {6,7,8} still has 92% success whether your opponent is aggressive or conservative.

What DOES change is your **strategic decision-making**. Here's how:

**1. Race conditions**

If your opponent is ahead and close to winning, you need to take MORE risk:
- They're at 12/13 on column 7? You can't afford conservative play
- You need to roll aggressively even on mediocre combinations
- Adjust the heuristic: `Keep rolling if: (P_success × Q) > α × (P_bust × unsaved_progress)`
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

But there is one more rule to the game: you should always pair them in a way that you can make a move, and if you pair the dice and there is a combination you can move, you should move. This means if you roll and paired so that you get a 6, but the other pair is a 2, and you have a free peg, then you SHOULD take the 2. I think that somewhat balances this part, but still I think I would have balanced the game in a way that it slightly favors the lower probability columns to encourage people take those. But people in general might feel the other way around, e.g. just the length of the column is what gets them emotionally involved, so balancing it this way might make sense for more people.



## Appendix: Complete probability tables

For the truly obsessed (hi, it's me), here are the probabilities for all 165 possible three-column combinations.

[Full table from the original post - all 165 combinations with success/bust rates]

```
Best combinations:
{6,7,8}: 92.0% success, 8.0% bust
{5,7,8} / {6,7,9}: 91.4% success, 8.6% bust
{4,6,8} / {6,8,10}: 91.1% success, 8.9% bust

Worst combinations:
{2,3,12}: 43.8% success, 56.2% bust
{2,3,4} / {10,11,12}: 52.2% success, 47.8% bust
{2,3,11} / {3,11,12}: 52.5% success, 47.5% bust
```

Full CSV files available in the [repository](files/20251201/).

## Appendix: Code for verification

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
