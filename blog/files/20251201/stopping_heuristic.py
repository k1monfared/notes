"""
Mathematical stopping heuristic for Can't Stop
Implements the formula: Keep rolling if (P_success × Q) > (P_bust × unsaved_progress)
"""

from itertools import product

def get_pairings(dice):
    """Get all 3 possible pairings of 4 dice"""
    d1, d2, d3, d4 = dice
    return [
        [(d1, d2), (d3, d4)],
        [(d1, d3), (d2, d4)],
        [(d1, d4), (d2, d3)]
    ]

def calculate_success_probability(columns):
    """Calculate P(can make at least one sum in columns)"""
    all_rolls = list(product(range(1, 7), repeat=4))
    success_count = 0

    for roll in all_rolls:
        for pairing in get_pairings(roll):
            sums = {sum(pair) for pair in pairing}
            if any(target in sums for target in columns):
                success_count += 1
                break

    return success_count / len(all_rolls)

def calculate_expected_markers(columns):
    """Calculate Q = E[markers advanced | success]"""
    all_rolls = list(product(range(1, 7), repeat=4))
    successful_markers = []

    for roll in all_rolls:
        max_markers = 0
        for pairing in get_pairings(roll):
            markers = sum(1 for pair in pairing if sum(pair) in columns)
            max_markers = max(max_markers, markers)

        if max_markers > 0:
            successful_markers.append(max_markers)

    return sum(successful_markers) / len(successful_markers) if successful_markers else 0.0

def should_keep_rolling(columns, unsaved_progress, alpha=1.0):
    """
    Determine if you should keep rolling based on the mathematical heuristic

    Args:
        columns: List of active column numbers
        unsaved_progress: Number of steps that would be lost on bust
        alpha: Risk tolerance parameter (default 1.0 for neutral)
               alpha < 1: more aggressive (accept more risk)
               alpha > 1: more conservative (avoid risk)

    Returns:
        True if you should keep rolling, False if you should stop
    """
    P_success = calculate_success_probability(columns)
    P_bust = 1 - P_success
    Q = calculate_expected_markers(columns)

    expected_gain = P_success * Q
    expected_loss = alpha * P_bust * unsaved_progress

    return expected_gain > expected_loss

def analyze_stopping_decision(columns, max_unsaved=10):
    """
    Analyze at what point you should stop for a given column combination

    Returns a table showing for each unsaved_progress value whether to keep rolling
    """
    P_success = calculate_success_probability(columns)
    P_bust = 1 - P_success
    Q = calculate_expected_markers(columns)

    print(f"Columns: {columns}")
    print(f"P(success) = {P_success:.1%}")
    print(f"P(bust) = {P_bust:.1%}")
    print(f"Q (expected markers/roll) = {Q:.2f}")
    print()
    print("Unsaved Progress | Expected Gain | Expected Loss | Decision")
    print("-" * 65)

    for unsaved in range(1, max_unsaved + 1):
        expected_gain = P_success * Q
        expected_loss = P_bust * unsaved
        decision = "KEEP ROLLING" if expected_gain > expected_loss else "STOP"

        print(f"{unsaved:16d} | {expected_gain:13.2f} | {expected_loss:13.2f} | {decision}")

def compare_combinations():
    """Compare stopping behavior for best vs worst combinations"""
    print("=" * 80)
    print("BEST COMBINATION: {6, 7, 8}")
    print("=" * 80)
    analyze_stopping_decision([6, 7, 8], max_unsaved=10)

    print("\n" + "=" * 80)
    print("WORST COMBINATION: {2, 3, 12}")
    print("=" * 80)
    analyze_stopping_decision([2, 3, 12], max_unsaved=10)

    print("\n" + "=" * 80)
    print("MODERATE COMBINATION: {4, 7, 10}")
    print("=" * 80)
    analyze_stopping_decision([4, 7, 10], max_unsaved=10)

if __name__ == "__main__":
    print("Can't Stop Stopping Heuristic Analysis")
    print("=" * 80)
    print()
    print("Formula: Keep rolling if (P_success × Q) > (α × P_bust × unsaved_progress)")
    print("where α is a risk tolerance parameter (default 1.0)")
    print()

    compare_combinations()

    print("\n" + "=" * 80)
    print("Example: Testing specific scenarios")
    print("=" * 80)

    # Example 1: Good combination with low unsaved progress
    columns = [6, 7, 8]
    unsaved = 3
    decision = should_keep_rolling(columns, unsaved)
    print(f"\nColumns {columns}, unsaved progress = {unsaved}")
    print(f"Decision: {'KEEP ROLLING' if decision else 'STOP'}")

    # Example 2: Bad combination with high unsaved progress
    columns = [2, 3, 12]
    unsaved = 2
    decision = should_keep_rolling(columns, unsaved)
    print(f"\nColumns {columns}, unsaved progress = {unsaved}")
    print(f"Decision: {'KEEP ROLLING' if decision else 'STOP'}")
