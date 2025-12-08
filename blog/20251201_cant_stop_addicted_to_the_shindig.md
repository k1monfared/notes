# Can't Stop, Addicted To The Shindig

I recently got introduced to this game called [Can't Stop](https://boardgamegeek.com/boardgame/41/cant-stop) and it got me thinking about probabilities. You know how it is - you start playing a dice game and suddenly you're knee-deep in combinatorics at 2am.

![Can't Stop Board And Dice](files/20251201/cant-stop.png)

The game is deceptively simple but mathematically rich. In this post, I'll take you through:
- The probability foundations (2-dice vs 4-dice)
- Which columns to choose and why
- When to stop rolling (the eternal question!)
- Whether to continue your current columns or switch to new ones
- How different strategies perform head-to-head
- Whether the game designers nailed the balance

Let's dive in.

## The Game

The rules are straightforward: roll four dice, pair them up however you want, move your markers on a board. The catch? You can keep rolling as long as you want, but if you can't move any of your three active markers, you lose everything you've gained that turn. Classic push-your-luck. [Here](https://www.youtube.com/watch?v=L6Zk7j1mJDE) is a brief explanation of how the game is played.

The board has columns numbered 2 through 12, with different lengths:
- Columns 2 and 12: 3 steps
- Columns 3 and 11: 5 steps
- Columns 4 and 10: 7 steps
- Columns 5 and 9: 9 steps
- Columns 6 and 8: 11 steps
- Column 7: 13 steps

You need to complete three columns to win.

I've implemented a fully interactive web version of the game with a Python/FastAPI backend and React frontend. You can [play it online](https://cantstop-frontend.onrender.com/) and check out the
  [source code](https://github.com/k1monfared/cantstop-game).


**The Forced-Move Rule (Important!)**

Here's a critical rule that shapes the entire strategy: **you must take all available moves**. If you roll the dice and choose a pairing that creates any valid move, you must make ALL legal moves from that pairing, even if you don't want them.

For example, if you're working on columns {6, 7, 8} and you roll (1,1,3,4), you could choose pairing (1,1)+(3,4) = 2+7. But if you do, you're forced to take BOTH the 2 and the 7, even though column 2 isn't in your plan. You can't just cherry-pick the 7.

This rule prevents the game from being trivially easy and adds tactical depth.

## Probability Foundations

### Two Dice: The Baseline

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

Sum 7 is the most likely at 16.67%, and it's exactly 6× more likely than sum 2 at 2.78%.

**Quick proof:** For sum 2, there's only one way: both dice must show 1. That's $\frac{1}{6} \times \frac{1}{6} = \frac{1}{36}$. For sum 7, you need complementary pairs: (1,6), (2,5), or (3,4), and order matters, so that's 6 ways total out of 36 possible outcomes.

Now if Can't Stop used two dice, column 7 would need to be 6× longer than column 2 to be equally hard. Instead it's only $\frac{13}{3} \approx 4.3\times$ longer. So something interesting must be happening with four dice.

### Four Dice: This Is Where It Gets Interesting

In Can't Stop, you roll FOUR dice and then pair them up. Say you roll 2, 3, 4, 5. You can make:
- (2,3)+(4,5) = 5 and 9
- (2,4)+(3,5) = 6 and 8
- (2,5)+(3,4) = 7 and 7

That's it, just three possible pairings. The question is: if I'm trying to hit column 7, what's the probability that at least one of those pairings gives me a 7?

Let me work this out properly.

#### Computing P(can make a 2)

To make a 2, I need a pair that sums to 2, which means two 1's. So I need at least two 1's among my four dice.

**Probability of NOT getting enough 1's:**

- $P(\text{zero 1's}) = \left(\frac{5}{6}\right)^4 = \frac{625}{1296}$

- $P(\text{exactly one 1}) = \binom{4}{1} \times \left(\frac{1}{6}\right)^1 \times \left(\frac{5}{6}\right)^3 = 4 \times \frac{1}{6} \times \frac{125}{216} = \frac{500}{1296}$

**Therefore:**

$$P(\text{can make a 2}) = 1 - \frac{625}{1296} - \frac{500}{1296} = \frac{171}{1296} \approx 13.2\%$$

13.2%! That's way higher than the 2.78% we had with two dice.

#### Computing P(can make a 7)

To make a 7, I need one of these pairs: (1,6), (2,5), or (3,4). The intuition: I want to count rolls with at least one of these complementary pairs, but I need to be careful not to double-count rolls that contain multiple pairs. I'll use inclusion-exclusion.

Let A = "I can make pair (1,6)" = "I have at least one 1 AND at least one 6"
Let B = "I can make pair (2,5)" = "I have at least one 2 AND at least one 5"
Let C = "I can make pair (3,4)" = "I have at least one 3 AND at least one 4"

**First, P(A) - having both a 1 and a 6:**

$$P(A) = 1 - P(\text{no 1's}) - P(\text{no 6's}) + P(\text{no 1's AND no 6's})$$
$$= 1 - \left(\frac{5}{6}\right)^4 - \left(\frac{5}{6}\right)^4 + \left(\frac{4}{6}\right)^4$$
$$= \frac{1296 - 625 - 625 + 256}{1296} = \frac{302}{1296}$$

By the same logic, $P(B) = \frac{302}{1296}$ and $P(C) = \frac{302}{1296}$.

**Next, the overlaps:**

$P(A \cap B) = P(\text{have 1, 6, 2, 5})$ = $\frac{24}{1296}$ (all four distinct values among four dice)

Similarly, $P(A \cap C) = \frac{24}{1296}$ and $P(B \cap C) = \frac{24}{1296}$.

$P(A \cap B \cap C) = 0$ because you'd need 6 specific dice values with only 4 dice.

**Final answer:**

$$P(\text{can make a 7}) = P(A \cup B \cup C) = 302 + 302 + 302 - 24 - 24 - 24 + 0 = \frac{834}{1296} \approx 64.4\%$$

With two dice, P(7) was 16.67%. With four dice, it jumped to 64.4%. And P(2) went from 2.78% to 13.2%.

Did the distribution get flatter?

#### The Complete Picture

Let me calculate all of them (see [probability_calculations.py](files/20251201/probability_calculations.py) for the code):

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

Now look at those normalized columns. The probability ratio from 2 to 7 is 4.88. The length ratio is 4.33. Pretty close! The game designers were definitely thinking about this.

## Column Selection Strategy

### Which Column Should You Go For?

On one hand, column 2 is only 3 steps. On the other hand, you'll only hit it 13.2% of the time. Column 7 is 13 steps but you hit it 64.4% of the time.

**Expected number of rolls to complete column n:**

$$\mathbb{E}[\text{rolls}] = \frac{\text{length}}{\text{probability}} = \frac{L(n)}{P(n)}$$

For column 2: $\frac{3}{0.132} = 22.73$ rolls
For column 7: $\frac{13}{0.644} = 20.18$ rolls

Column 7 is slightly faster, even though it's 4× longer. Let me check all of them:

| Column | Length | P(n) | Expected Rolls |
|-------:|-------:|-----:|---------------:|
| 2, 12 | 3 | 13.2% | 22.73 |
| 3, 11 | 5 | 23.3% | 21.46 |
| 4, 10 | 7 | 35.6% | 19.67 |
| 5, 9 | 9 | 44.8% | 20.09 |
| 6, 8 | 11 | 56.1% | 19.60 |
| 7 | 13 | 64.4% | 20.18 |

Columns 2 and 12 require the most rolls. Columns 6, 7, and 8 are all close to each other around 20 rolls.

![Expected Rolls per Column](files/20251201/expected_rolls_per_column.png)

### But Wait - Three Columns at Once

Here's the thing though: you don't play Can't Stop one column at a time. You have THREE active columns, and you bust if you can't hit ANY of them.

If you're on columns {6, 7, 8}, what's your bust probability?

I need $P(\text{can't make 6 AND can't make 7 AND can't make 8})$. The easiest way is to enumerate all 1296 possible rolls and count (see [column_combinations.py](files/20251201/column_combinations.py)):

**Result: 1193/1296 = 92.0% success rate**

So if you're on {6,7,8}, you have a 92% chance of not busting.

What about {2,3,12}?

**Result: 568/1296 = 43.8% success rate**

Less than 50% chance of not busting. You're more likely to bust than succeed!

### All 165 Three-Column Combinations

Let me analyze all possible combinations and show you the best and worst (see [column_combinations.py](files/20251201/column_combinations.py) for complete results):

**Top 10 Best Combinations:**

| Rank | Columns | Success | Bust | Clean | Q (expected markers/roll) |
|-----:|:--------|--------:|-----:|------:|--------------------------:|
| 1 | {6,7,8} | 92.0% | 8.0% | 39.8% | 1.43 |
| 2 | {5,7,8} | 91.4% | 8.6% | 38.2% | 1.42 |
| 3 | {6,7,9} | 91.4% | 8.6% | 38.2% | 1.42 |
| 4 | {4,6,8} | 91.1% | 8.9% | 28.2% | 1.31 |
| 5 | {6,8,10} | 91.1% | 8.9% | 28.2% | 1.31 |
| 6 | {4,7,8} | 90.3% | 9.7% | 34.0% | 1.38 |
| 7 | {6,7,10} | 90.3% | 9.7% | 34.0% | 1.38 |
| 8 | {5,6,8} | 89.5% | 10.5% | 33.3% | 1.37 |
| 9 | {6,8,9} | 89.5% | 10.5% | 33.3% | 1.37 |
| 10 | {5,7,10} | 89.3% | 10.7% | 29.1% | 1.33 |

**Bottom 10 Worst Combinations:**

| Rank | Columns | Success | Bust | Clean | Q (expected markers/roll) |
|-----:|:--------|--------:|-----:|------:|--------------------------:|
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

**What's "Clean"?** Remember the forced-move rule? A "clean" move is one where you only hit columns you actually want. Even the best combination {6,7,8} only has 39.8% clean moves - the rest of the time you're forced onto unwanted columns.

Here's the complete picture - all 165 combinations ranked by success rate:

![All 165 Combinations Ranked](files/20251201/all_165_combinations_ranked.png)

The distribution reveals some interesting patterns: 37 combinations are "excellent" (≥85% success rate), mostly centered around columns 5-9. The median combination still succeeds 79.6% of the time, but the worst combinations drop dramatically to just 43.8% - you're more likely to bust than succeed!

The full detailed results are in [column_combinations_all.csv](files/20251201/column_combinations_all.csv).

## When Should You Stop Rolling?

This is the classic push-your-luck question. You've made some progress this turn - should you roll again or bank it?

### The Basic Heuristic

Here's a mathematical framework (see [stopping_heuristic.py](files/20251201/stopping_heuristic.py) for implementation):

**Keep rolling if:** $(P_{\text{success}} \times Q) > (P_{\text{bust}} \times U)$

Where:
- $P_{\text{success}}$ = probability of hitting at least one active column
- $Q$ = expected number of markers you'll advance on a successful roll
- $P_{\text{bust}}$ = probability of hitting no active columns
- $U$ = unsaved progress (steps you'd lose if you bust)

Let's test this on {6,7,8} with 5 unsaved steps:

**Risk of rolling again:**
- 8% chance you bust and lose those 5 steps
- Expected loss: $0.08 \times 5 = 0.4$ steps

**Expected gain from rolling again:**
- 92% chance you succeed
- You'll advance about 1.43 markers on average
- Expected gain: $0.92 \times 1.43 = 1.32$ steps

Since $1.32 > 0.4$, you should keep rolling.

Now try the same on {2,3,12} with 2 unsaved steps:

**Risk:** $0.562 \times 2 = 1.12$ steps
**Expected gain:** $0.438 \times 1.05 = 0.46$ steps

Since $1.12 > 0.46$, you should STOP.

### The Forced-Move Impact

Remember that forced-move rule? It changes everything. Let me recalculate success rates for "clean" moves only.

For {6,7,8}, the old analysis said 92% success rate. But how many of those rolls force you onto columns outside {6,7,8}?

A roll is "clean" if at least one pairing gives you ONLY sums in {6,7,8}. Running the calculation:

**Result: Only 39.8% of rolls give you a clean move on {6,7,8}!**

The other 52.2% of rolls let you make progress BUT also force you onto unwanted columns, slowly contaminating your combination.

**For {2,3,12}: Only 2.3% of rolls are clean!**

The forced-move rule is a balancing mechanism. It prevents {6,7,8} from being completely dominant by forcing players onto suboptimal columns when they push their luck.

## Continuation vs. Switching

Should you continue your current columns or switch to new ones? This depends on progress already made: if columns are nearly complete (e.g., 10/11 steps), continuing makes sense. But with minimal progress (2-3 steps), switching to a better combination might be faster.

The mathematics favor continuation in most cases: wasting accumulated progress hurts more than the marginal benefit of a slightly better combination. However, the forced-move rule gradually contaminates good combinations over time, sometimes forcing strategic switches.

**Note:** I haven't fully analyzed this aspect quantitatively. A complete treatment would require simulating "always continue" vs "switch when X" strategies across different board states and comparing their win rates. This is an interesting open question for future work, but for now I'm focusing on the stopping decision given a fixed set of active columns.

## Strategy Performance

Now let's see how different strategies actually perform. I implemented 25 different strategies and ran them against each other in a massive tournament (2,500 games per matchup, 750,000 total games).

### The Strategies

Let me describe each strategy and why it might make sense:

**1. Greedy** - Always rolls until bust. Never voluntarily stops. This is your baseline "worst possible strategy" - it tests whether stopping early has any value at all.

**2. Conservative(k)** - Stops after accumulating k steps of unsaved progress ($U \geq k$). Tested with k ∈ {1, 2, 3, 4}. The idea: bank progress early and often to minimize risk. Conservative(1) is extremely cautious, Conservative(4) is more balanced.

**3. Heuristic(α)** - Implements the mathematical stopping rule: Keep rolling if $(P_{\text{success}} \times Q) > (\alpha \times P_{\text{bust}} \times U)$ where α is a risk tolerance parameter. Tested with α ∈ {0.3, 0.5, 1.0, 1.5, 2.0}. When α = 1.0, it's the "pure" mathematical formula. α < 1 means more aggressive (accept more risk), α > 1 means more conservative.

**4. OpponentAware(α_behind, α_tied, α_ahead)** - Extends Heuristic with dynamic risk adjustment based on game state. Uses different α values when behind (take more risk), tied (neutral), or ahead (be cautious). Additionally weights column values by 0.5 if opponent is ahead on that column. Tested with three parameter sets: (0.3,1,2), (0.5,1,2), and (0.7,1,1.5).

**5. Random(p)** - Stops with probability p after each successful roll. Tested with p = 0.3. This is a control strategy to establish a baseline for random decision-making.

**6. GreedyImproved1** - Stops only after making progress on all three active columns in the current turn. The idea: ensure balanced progress across all columns before banking.

**7. GreedyImproved2** - Stops after accumulating exactly 5 total steps of unsaved progress ($U = 5$). This is an empirically-tuned threshold that balances risk and reward.

**8. AdaptiveThreshold** - Dynamically adjusts stopping threshold based on current column combination success probability: threshold = ⌊1 + P_success × 5⌋. Good combinations allow more risk, bad combinations force early stopping.

**9. ProportionalThreshold(f)** - Stops when unsaved progress reaches fraction f of the minimum remaining distance across active columns ($U \geq f \times \min(\text{remaining steps})$). Tested with f ∈ {0.33, 0.5}. The idea: stop when you've made meaningful progress relative to what's left.

**10. GreedyFraction(f)** - Stops when any single active column has advanced by fraction f of its total length in the current turn. Tested with f ∈ {0.33, 0.5}. The idea: focus on completing individual columns.

**11. FiftyPercentSurvival** - Calculates the exact number of rolls n where cumulative survival probability drops below 50% using $n = \log(0.5) / \log(P_{\text{success}})$, then stops after that many rolls. The idea: play until odds turn against you.

**12. ExpectedValueMaximizer** - Stops precisely when expected value turns negative: $\text{EV} = P_{\text{success}} \times Q - P_{\text{bust}} \times U \leq 0$. This is the "theoretically optimal" strategy from a pure EV perspective.

**13. GreedyUntil1Col** - Rolls until completing at least one column per turn, then stops immediately. The idea: column completion has discrete strategic value (denies opponent, frees a peg).

**14. GreedyUntil3Col** - Rolls until winning the entire game (completing all 3 required columns), never stopping voluntarily. This tests the extreme "all-in" strategy.

### Single-Player Performance

First, let's see how fast each strategy completes 3 columns when playing alone (1,000 trials each):

| Rank | Strategy | Avg Turns | Median |
|------|----------|-----------|--------|
| 1 | GreedyImproved2 | 13.2 | 12 |
| 1 | GreedyFraction(0.33) | 13.2 | 12 |
| 3 | GreedyImproved1 | 14.2 | 13 |
| 4 | AdaptiveThreshold | 14.1 | 13 |
| 5 | Conservative(4) | 15.0 | 14 |
| 6 | GreedyFraction(0.5) | 15.3 | 14 |
| 7 | FiftyPercentSurvival | 15.9 | 15 |
| 8 | Heuristic(1.0) | 16.0 | 15 |
| ... | ... | ... | ... |
| 23 | Heuristic(0.3) | 108.0 | 95 |

Full results: [single_player_results.txt](files/20251201/single_player_results.txt)

The fastest strategies complete in about 13 turns, while being too conservative (Heuristic with α=0.3) takes 108 turns on average!

![Single-Player Performance](files/20251201/single_player_performance.png)

### Head-to-Head Tournament Results

Now the real test: 25 strategies, each playing 2,500 games against every other strategy. Here are the overall win rates (wins against all opponents, with 95% confidence intervals calculated using the normal approximation to the binomial distribution):

| Rank | Strategy | Win Rate (±95% CI) | Total Wins |
|------|----------|----------|------------|
| **1** | **GreedyUntil1Col** | **81.6% (±0.3%)** | **48,955/60,000** |
| 2 | GreedyImproved2 | 78.1% (±0.3%) | 46,879/60,000 |
| 3 | GreedyFraction(0.33) | 76.9% (±0.3%) | 46,140/60,000 |
| 4 | GreedyImproved1 | 75.7% (±0.3%) | 45,428/60,000 |
| 5 | AdaptiveThreshold | 73.1% (±0.4%) | 43,876/60,000 |
| 6 | Conservative(4) | 71.1% (±0.4%) | 42,660/60,000 |
| 7 | GreedyFraction(0.5) | 67.9% (±0.4%) | 40,719/60,000 |
| 8 | FiftyPercentSurvival | 66.7% (±0.4%) | 40,048/60,000 |
| 9 | Conservative(3) | 65.7% (±0.4%) | 39,449/60,000 |
| 10 | Heuristic(1.0) | 62.1% (±0.4%) | 37,244/60,000 |
| 11 | ExpectedValueMax | 56.8% (±0.4%) | 34,066/60,000 |
| 12 | Random(0.3) | 56.5% (±0.4%) | 33,929/60,000 |
| 13 | OppAware(0.7,1,1.5) | 53.1% (±0.4%) | 31,855/60,000 |
| 14 | GreedyUntil3Col | 50.9% (±0.4%) | 30,538/60,000 |
| ... | ... | ... | ... |
| 25 | Greedy | 0.1% (±0.02%) | 30/60,000 |

Full results: [analysis_results_25strategies_2500games.txt](files/20251201/analysis_results_25strategies_2500games.txt)

![Strategy Tournament Rankings](files/20251201/strategy_tournament_rankings.png)

### The Champion: GreedyUntil1Col

**GreedyUntil1Col wins with 81.6% overall win rate**, beating the previous leader GreedyImproved2 (78.1%) by 3.5 percentage points.

**The strategy:** Roll until completing at least one column per turn, then stop immediately.

**Why it dominates:**

1. **Guaranteed progress** - If you don't bust, you ALWAYS complete at least one column. No wasted turns banking partial progress.

2. **Exploits game mechanics** - Column completion denies opponent access immediately and frees up a peg for the next column choice. Partial progress gives neither benefit.

3. **Optimal risk/reward balance** - Columns take 3-13 steps. Typical columns need 5-8 steps. Completing one column takes 1-2 turns on average (when not busting) - aggressive enough to make progress, conservative enough to avoid frequent busts.

4. **Variance reduction** - Can't Stop typically lasts 8-12 turns. GreedyUntil1Col completes 1 column/turn consistently, while ExpectedValueMax varies wildly (sometimes 0, sometimes 2-3 columns). Consistency wins in short games.

**Key matchups (with 95% CI):**
- vs GreedyImproved2 (previous #1): 65.1% (±1.9%) to 34.9%
- vs ExpectedValueMax (math optimal): 76.4% (±1.7%) to 23.6%
- vs Conservative(4): 73.6% (±1.8%) to 26.4%
- vs GreedyUntil3Col (too greedy): 72.4% (±1.8%) to 27.6%

### Full Tournament Matrix

Here's the complete head-to-head win-rate matrix (row vs column, percentage shown is row's win rate):

![Tournament Heatmap](files/20251201/tournament_heatmap_full.png)

[Download full CSV](files/20251201/tournament_results_full.csv)

| Strategy | vs Greedy | vs Cons(3) | vs Heur(1.0) | vs GreedyImp2 | vs GreedyU1Col |
|:---------|:---------:|:----------:|:------------:|:-------------:|:--------------:|
| GreedyUntil1Col | 100.0% | 79.1% | 76.7% | 65.1% | -- |
| GreedyImproved2 | 100.0% | 76.9% | 68.8% | -- | 34.9% |
| GreedyFraction(0.33) | 99.9% | 74.5% | 69.8% | 45.6% | 35.4% |
| GreedyImproved1 | 99.9% | 71.2% | 66.0% | 52.4% | 30.5% |
| AdaptiveThreshold | 99.9% | 67.4% | 61.7% | 34.8% | 29.6% |
| Conservative(4) | 100.0% | 59.4% | 64.9% | 32.8% | 26.4% |
| Heuristic(1.0) | 100.0% | 42.6% | -- | 31.2% | 23.3% |
| ExpectedValueMax | 100.0% | 39.7% | 45.6% | 23.6% | 23.6% |
| Random(0.3) | 100.0% | 31.6% | 40.8% | 21.2% | 20.6% |
| Conservative(3) | 100.0% | -- | 57.4% | 23.1% | 20.9% |
| GreedyUntil3Col | 99.9% | 44.6% | 41.2% | 36.4% | 27.6% |
| Greedy | -- | 0.0% | 0.0% | 0.0% | 0.0% |

(Full 25×25 matrix available in CSV)

### Wait, Why Doesn't the Fastest Strategy Win?

Something weird is going on here. Look at the single-player speed tests: GreedyImproved2 finishes in 13.2 turns on average - the fastest by far. But it only gets second place in the tournament. Meanwhile, GreedyUntil1Col wins the whole thing despite taking 16.3 turns - that's ninth place in the speed rankings!

![Speed vs Win Rate Analysis](files/20251201/speed_vs_winrate_analysis.png)

Here's what's happening: single-player speed tests measure "how fast can you finish when you're alone." But Can't Stop isn't a solo speed run - it's a race against an opponent.

Think about it like this. Say you have two runners:
- Runner A averages 13 minutes but ranges from 8–20 minutes (super inconsistent)
- Runner B averages 16 minutes but always finishes between 14–18 minutes (rock solid)

In repeated races head-to-head, Runner B wins more often because consistency matters more than raw average speed.

That's exactly what's happening with GreedyUntil1Col. It guarantees exactly 1 column completion per successful turn. No wasted turns banking partial progress. It's the tortoise beating the hare, except the tortoise has done the math.

The aggressive strategies? Sure, they complete fast WHEN they succeed. But they bust more often. In single-player, you can retry forever, and those busts just get averaged in. In a tournament, one bust = instant loss. Game over.

The numbers bear this out: there's a -0.77 correlation between speed and win rate (faster usually wins more), but the outliers tell the real story. Our champion is 3.1 turns slower than the fastest strategy, yet wins 3.5 percentage points more games. That's the power of consistency in competitive play.

### What Actually Works (And What Doesn't)

So what did we learn from 750,000 simulated games?

**Simple beats sophisticated.** The top strategies all use dead-simple rules: complete 1 column, stop after 5 steps, stop at 1/3 progress. Meanwhile, the "smart" strategies trying to optimize expected value? ExpectedValueMaximizer gets 56.8%, FiftyPercentSurvival gets 66.7%. They're getting crushed by strategies you could explain to a 10-year-old.

**Never going full greedy.** The pure Greedy strategy (never stop voluntarily) won 30 games out of 60,000. That's 0.1%. It loses to literally everything else. Always rolling until bust is a spectacular way to lose at Can't Stop.

**But also, don't be too scared.** Conservative(1) - the strategy that stops after making ANY progress - wins only 16.3% of games and takes 108 turns on average. If you're stopping after every single successful roll, you're basically not playing the game.

**The EV trap.** Expected Value Maximizer sounds smart, right? Optimize expected value on every decision! But it has high variance - sometimes you complete 3 columns fast, sometimes 0. GreedyUntil1Col guarantees exactly 1 column per turn. In a game that typically lasts 8–12 turns, consistency beats optimization every time.

**Being "opponent aware" didn't help.** I tried three variants that adjusted risk based on whether you're ahead or behind. All three performed worse than simple threshold strategies. The problem? They only looked at completed columns, not partial progress. A better implementation might track "estimated turns until opponent wins" - but that's a problem for future me.

## Game Design: Is It Balanced?

Okay, back to game design. Is Can't Stop balanced? That is, do all columns take roughly the same time to complete?

### Single-Column Balance

With single-column analysis, here's what we get:

| Column | Length | P(n) | Expected Rolls | Deviation from 20 |
|-------:|-------:|-----:|---------------:|------------------:|
| 2 | 3 | 13.2% | 22.73 | +13.6% |
| 3 | 5 | 23.3% | 21.46 | +7.3% |
| 4 | 7 | 35.6% | 19.67 | -1.6% |
| 5 | 9 | 44.8% | 20.09 | +0.4% |
| 6 | 11 | 56.1% | 19.60 | -2.0% |
| 7 | 13 | 64.4% | 20.18 | +0.9% |
| 8 | 11 | 56.1% | 19.60 | -2.0% |
| 9 | 9 | 44.8% | 20.09 | +0.4% |
| 10 | 7 | 35.6% | 19.67 | -1.6% |
| 11 | 5 | 23.3% | 21.46 | +7.3% |
| 12 | 3 | 13.2% | 22.73 | +13.6% |

The deviations are ±13.6% at most. That's pretty good given that lengths must be integers!

### Multi-Column Reality

But in realistic multi-column play, column combination choice dominates individual column balance:
- Column 7 in {6,7,8}: expected completion in ~2 turns
- Column 2 in {2,3,12}: expected completion in ~30 turns

The game heavily favors middle columns. The designers DID balance individual column completion times, but they couldn't (or didn't want to) balance the three-column combinations.

### Design Philosophy

Can't Stop's designer, Sid Sackson, was known for mathematical rigor, but practical constraints shaped the final design:

1. **Simple enough to understand** - The current board (3-5-7-9-11-13) is instantly graspable
2. **Physically manufacturable** - Integer lengths, reasonable board size (especially in 1980)
3. **Engaging to a broad audience** - The visual length creates emotional investment

Then, **rules and mechanics compensate for inevitable imbalances**. In Can't Stop, that compensating rule is the forced-move rule: you MUST take both columns even if you don't want them.

This rule:
- Forces players into sub-optimal column combinations
- Prevents the game from devolving into "everyone only picks {6,7,8}"
- Adds tactical complexity
- **Compensates for the mathematical imbalance**

This is elegant game design: accept imperfect balance in the core mechanics, then add rules that turn that imbalance into interesting strategic choices.

### Could They Have Done Better?

For perfect balance where every column takes exactly the same expected number of rolls, we'd need column lengths that are exact multiples of their probabilities. The minimum integer solution requires:

- Column 2/12: 171 steps
- Column 7: 834 steps

Game duration: ~8 hours. Yeah, that's not happening.

But what about smaller improvements? Running an optimization (see [cant_stop_optimization.py](files/20251201/cant_stop_optimization.py)):

**Current board:**
- Max height: 13 steps
- Max deviation: ±13.6%
- Lengths: [3, 5, 7, 9, 11, 13, 11, 9, 7, 5, 3]

**Optimal board (±1 step from current):**
- Max height: 14 steps
- Max deviation: ±3.09%
- Lengths: [3, 5, 8, 10, 12, 14, 12, 10, 8, 5, 3]
- **4× more balanced with just +1 step!**

**Best balance under 20 steps:**
- Max height: 20 steps
- Max deviation: ±2.17%
- Lengths: [4, 7, 11, 14, 17, 20, 17, 14, 11, 7, 4]
- **6× improvement in balance**

Why didn't the designers do this?

1. **Round numbers** - The current design uses nice symmetric patterns
2. **Intentional imbalance** - Maybe they wanted strategic tension
3. **Testing limitations** - In 1980, computing optimal scales would have required extensive manual calculation
4. **Player psychology** - A 13-step column "feels" much harder than a 3-step column, even if mathematically balanced

The current design is excellent for 1980. For a modern Can't Stop 2.0, I'd seriously consider the 20-step board.

### Linear Progression

One elegant feature of the current design is its linear progression: columns increase by exactly 2 steps each time. What if we maintained this constraint but optimized the parameters?

(See [cant_stop_linear_optimization.py](files/20251201/cant_stop_linear_optimization.py) for full analysis)

**Best linear design with similar size (step=2.25):**
- Lengths: [3, 5, 8, 10, 12, 14, 12, 10, 8, 5, 3]
- Max deviation: ±3.09%
- **3.2× better balance with just +1 step!**

**Best with integer step (base=5, step=4):**
- Lengths: [5, 9, 13, 17, 21, 25, 21, 17, 13, 9, 5]
- Max deviation: ±3.32%
- Maintains aesthetic appeal (all odd numbers, easy to manufacture)

Linear designs can never achieve perfect balance because the probability curve is nonlinear, but they can get within ~2-3% deviation while maintaining elegance.

## Conclusion

Can't Stop is a masterclass in practical game design. The mathematics reveal that:

1. **Four-dice probabilities flatten the distribution** - P(7) = 64.4% vs P(2) = 13.2%, only a 4.88× difference compared to 6× with two dice

2. **Column combinations matter more than individual columns** - {6,7,8} has 92% success rate, {2,3,12} has 44%

3. **The optimal strategy is simple** - "Roll until you complete one column per turn" beats sophisticated mathematical approaches because variance dominates in short games

4. **The forced-move rule is brilliant** - It compensates for mathematical imbalances by forcing contamination of good column combinations

5. **Perfect balance isn't necessary** - The game is engaging despite (or because of) favoring middle columns

For players: aim for columns 5-9, avoid columns 2-3 and 11-12, and stop after completing one column per turn.

For game designers: prioritize playability over mathematical perfection, then use rules to compensate for the inevitable imbalances.

And for probability nerds: keep analyzing. There's always another layer to uncover.

---

## Code and Data

All analysis code and simulation results are available:

**Probability calculations:**
- [probability_calculations.py](files/20251201/probability_calculations.py) - 2-dice and 4-dice probabilities
- [column_combinations.py](files/20251201/column_combinations.py) - All 165 three-column combinations

**Strategy analysis:**
- [stopping_heuristic.py](files/20251201/stopping_heuristic.py) - Mathematical stopping rule
- [cant_stop_analysis_extended.py](files/20251201/cant_stop_analysis_extended.py) - Full tournament simulator with 25 strategies
- [analyze_speed_vs_winrate.py](files/20251201/analyze_speed_vs_winrate.py) - Speed vs tournament performance comparison

**Game design:**
- [cant_stop_optimization.py](files/20251201/cant_stop_optimization.py) - Optimal board designs
- [cant_stop_linear_optimization.py](files/20251201/cant_stop_linear_optimization.py) - Linear progression optimization

**Results:**
- [tournament_results_full.csv](files/20251201/tournament_results_full.csv) - Complete 25×25 win-rate matrix
- [column_combinations_all.csv](files/20251201/column_combinations_all.csv) - All 165 combinations analyzed
- [single_player_results.txt](files/20251201/single_player_results.txt) - Independent strategy performance
- [analysis_results_25strategies_2500games.txt](files/20251201/analysis_results_25strategies_2500games.txt) - Full tournament results
