"""
Basic probability calculations for Can't Stop
Computes probabilities for 2-dice and 4-dice scenarios
"""

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

def calculate_four_dice_probabilities():
    """Calculate P(can make sum n) for all sums 2-12 with four dice"""
    all_rolls = list(product(range(1, 7), repeat=4))
    total = len(all_rolls)  # 1296

    probabilities = {}
    for target_sum in range(2, 13):
        count = sum(1 for roll in all_rolls if can_make_sum(roll, target_sum))
        probabilities[target_sum] = {
            'count': count,
            'total': total,
            'probability': count / total,
            'percentage': f"{100 * count / total:.1f}%"
        }

    return probabilities

def calculate_two_dice_probabilities():
    """Calculate standard 2-dice probabilities for comparison"""
    probabilities = {}
    for target_sum in range(2, 13):
        count = 0
        for d1 in range(1, 7):
            for d2 in range(1, 7):
                if d1 + d2 == target_sum:
                    count += 1

        probabilities[target_sum] = {
            'count': count,
            'total': 36,
            'probability': count / 36,
            'percentage': f"{100 * count / 36:.2f}%"
        }

    return probabilities

def print_comparison_table():
    """Print side-by-side comparison of 2-dice vs 4-dice"""
    two_dice = calculate_two_dice_probabilities()
    four_dice = calculate_four_dice_probabilities()

    print("Sum | 2-Dice P(sum) | 4-Dice P(can make sum)")
    print("----|---------------|------------------------")
    for s in range(2, 13):
        print(f"{s:2d}  | {two_dice[s]['percentage']:>6s} ({two_dice[s]['count']:2d}/36) | "
              f"{four_dice[s]['percentage']:>6s} ({four_dice[s]['count']:4d}/1296)")

if __name__ == "__main__":
    print("Two-Dice Probabilities:")
    print("=" * 50)
    two_dice = calculate_two_dice_probabilities()
    for s in range(2, 13):
        print(f"Sum {s:2d}: {two_dice[s]['percentage']}")

    print("\n" + "=" * 50)
    print("Four-Dice Probabilities:")
    print("=" * 50)
    four_dice = calculate_four_dice_probabilities()
    for s in range(2, 13):
        print(f"Sum {s:2d}: {four_dice[s]['percentage']}")

    print("\n" + "=" * 50)
    print("Comparison Table:")
    print("=" * 50)
    print_comparison_table()
