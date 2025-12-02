#!/usr/bin/env python3
"""General mathematical formula for P(at least one of {a, b, c})"""

from itertools import product, combinations
from math import comb

def count_rolls_with_dice_values(required_values):
    """
    Count rolls (d1,d2,d3,d4) that contain the required dice values.

    required_values: dict like {1: 2, 2: 1} means "at least two 1's and at least one 2"
    """
    # Use inclusion-exclusion on which values are MISSING
    # This is complex for general multisets, so we'll enumerate

    count = 0
    for roll in product(range(1, 7), repeat=4):
        # Count occurrences of each value in the roll
        roll_counts = {}
        for die in roll:
            roll_counts[die] = roll_counts.get(die, 0) + 1

        # Check if roll satisfies requirements
        satisfies = True
        for value, min_count in required_values.items():
            if roll_counts.get(value, 0) < min_count:
                satisfies = False
                break

        if satisfies:
            count += 1

    return count

def dice_requirements_for_sum(target_sum):
    """
    Return the minimum dice requirements to make a sum.

    For sum S, we need a pair (a,b) where a+b=S.
    Returns list of possible requirements.
    """
    requirements = []
    for a in range(1, 7):
        b = target_sum - a
        if 1 <= b <= 6:
            # Need at least one 'a' and at least one 'b'
            if a == b:
                # Need at least two of the same value
                requirements.append({a: 2})
            else:
                # Need at least one of each
                requirements.append({a: 1, b: 1})

    return requirements

def merge_requirements(req1, req2):
    """Merge two requirement dicts, taking the maximum of each value"""
    merged = {}
    all_keys = set(req1.keys()) | set(req2.keys())
    for key in all_keys:
        merged[key] = max(req1.get(key, 0), req2.get(key, 0))
    return merged

def can_satisfy_all_requirements(reqs_list):
    """Check if it's possible to satisfy all requirements with 4 dice"""
    # Merge all requirements
    merged = {}
    for req in reqs_list:
        for value, count in req.items():
            merged[value] = max(merged.get(value, 0), count)

    # Check if total required dice <= 4
    total_required = sum(merged.values())
    return total_required <= 4, merged

def compute_probability_mathematical(target_sums):
    """
    Compute P(can make at least one of target_sums) using inclusion-exclusion.

    target_sums: list of 3 sums, e.g., [2, 3, 12]
    """
    a, b, c = target_sums

    print(f"\nComputing P(at least one of {{{a}, {b}, {c}}}) mathematically")
    print("=" * 70)

    # Get requirements for each sum
    print("\nDice requirements for each sum:")
    req_a_list = dice_requirements_for_sum(a)
    req_b_list = dice_requirements_for_sum(b)
    req_c_list = dice_requirements_for_sum(c)

    print(f"  Sum {a}: {req_a_list}")
    print(f"  Sum {b}: {req_b_list}")
    print(f"  Sum {c}: {req_c_list}")

    # For each sum, we need to satisfy at least ONE of its requirements
    # This is complex, so let's compute by counting rolls

    print("\nStep 1: Individual probabilities")
    print("-" * 70)

    # P(can make sum a)
    n_a = 0
    for roll in product(range(1, 7), repeat=4):
        for req in req_a_list:
            roll_counts = {}
            for die in roll:
                roll_counts[die] = roll_counts.get(die, 0) + 1

            satisfies = True
            for value, min_count in req.items():
                if roll_counts.get(value, 0) < min_count:
                    satisfies = False
                    break

            if satisfies:
                n_a += 1
                break

    # P(can make sum b)
    n_b = 0
    for roll in product(range(1, 7), repeat=4):
        for req in req_b_list:
            roll_counts = {}
            for die in roll:
                roll_counts[die] = roll_counts.get(die, 0) + 1

            satisfies = True
            for value, min_count in req.items():
                if roll_counts.get(value, 0) < min_count:
                    satisfies = False
                    break

            if satisfies:
                n_b += 1
                break

    # P(can make sum c)
    n_c = 0
    for roll in product(range(1, 7), repeat=4):
        for req in req_c_list:
            roll_counts = {}
            for die in roll:
                roll_counts[die] = roll_counts.get(die, 0) + 1

            satisfies = True
            for value, min_count in req.items():
                if roll_counts.get(value, 0) < min_count:
                    satisfies = False
                    break

            if satisfies:
                n_c += 1
                break

    print(f"P(can make {a})  = {n_a}/1296 = {n_a/1296:.4f}")
    print(f"P(can make {b})  = {n_b}/1296 = {n_b/1296:.4f}")
    print(f"P(can make {c})  = {n_c}/1296 = {n_c/1296:.4f}")

    print("\nStep 2: Intersection probabilities")
    print("-" * 70)

    # P(can make a AND b)
    n_ab = 0
    for roll in product(range(1, 7), repeat=4):
        can_make_a = False
        can_make_b = False

        roll_counts = {}
        for die in roll:
            roll_counts[die] = roll_counts.get(die, 0) + 1

        for req in req_a_list:
            satisfies = True
            for value, min_count in req.items():
                if roll_counts.get(value, 0) < min_count:
                    satisfies = False
                    break
            if satisfies:
                can_make_a = True
                break

        for req in req_b_list:
            satisfies = True
            for value, min_count in req.items():
                if roll_counts.get(value, 0) < min_count:
                    satisfies = False
                    break
            if satisfies:
                can_make_b = True
                break

        if can_make_a and can_make_b:
            n_ab += 1

    # P(can make a AND c)
    n_ac = 0
    for roll in product(range(1, 7), repeat=4):
        can_make_a = False
        can_make_c = False

        roll_counts = {}
        for die in roll:
            roll_counts[die] = roll_counts.get(die, 0) + 1

        for req in req_a_list:
            satisfies = True
            for value, min_count in req.items():
                if roll_counts.get(value, 0) < min_count:
                    satisfies = False
                    break
            if satisfies:
                can_make_a = True
                break

        for req in req_c_list:
            satisfies = True
            for value, min_count in req.items():
                if roll_counts.get(value, 0) < min_count:
                    satisfies = False
                    break
            if satisfies:
                can_make_c = True
                break

        if can_make_a and can_make_c:
            n_ac += 1

    # P(can make b AND c)
    n_bc = 0
    for roll in product(range(1, 7), repeat=4):
        can_make_b = False
        can_make_c = False

        roll_counts = {}
        for die in roll:
            roll_counts[die] = roll_counts.get(die, 0) + 1

        for req in req_b_list:
            satisfies = True
            for value, min_count in req.items():
                if roll_counts.get(value, 0) < min_count:
                    satisfies = False
                    break
            if satisfies:
                can_make_b = True
                break

        for req in req_c_list:
            satisfies = True
            for value, min_count in req.items():
                if roll_counts.get(value, 0) < min_count:
                    satisfies = False
                    break
            if satisfies:
                can_make_c = True
                break

        if can_make_b and can_make_c:
            n_bc += 1

    # P(can make all three)
    n_abc = 0
    for roll in product(range(1, 7), repeat=4):
        can_make_a = False
        can_make_b = False
        can_make_c = False

        roll_counts = {}
        for die in roll:
            roll_counts[die] = roll_counts.get(die, 0) + 1

        for req in req_a_list:
            satisfies = True
            for value, min_count in req.items():
                if roll_counts.get(value, 0) < min_count:
                    satisfies = False
                    break
            if satisfies:
                can_make_a = True
                break

        for req in req_b_list:
            satisfies = True
            for value, min_count in req.items():
                if roll_counts.get(value, 0) < min_count:
                    satisfies = False
                    break
            if satisfies:
                can_make_b = True
                break

        for req in req_c_list:
            satisfies = True
            for value, min_count in req.items():
                if roll_counts.get(value, 0) < min_count:
                    satisfies = False
                    break
            if satisfies:
                can_make_c = True
                break

        if can_make_a and can_make_b and can_make_c:
            n_abc += 1

    print(f"P(can make {a} AND {b})   = {n_ab}/1296 = {n_ab/1296:.4f}")
    print(f"P(can make {a} AND {c})  = {n_ac}/1296 = {n_ac/1296:.4f}")
    print(f"P(can make {b} AND {c})  = {n_bc}/1296 = {n_bc/1296:.4f}")
    print(f"P(can make all three) = {n_abc}/1296 = {n_abc/1296:.4f}")

    print("\nStep 3: Apply inclusion-exclusion")
    print("-" * 70)

    n_total = n_a + n_b + n_c - n_ab - n_ac - n_bc + n_abc

    print(f"\nP(at least one) = {n_a} + {n_b} + {n_c} - {n_ab} - {n_ac} - {n_bc} + {n_abc}")
    print(f"                = {n_total}/1296")
    print(f"                = {n_total/1296:.4f} = {n_total/1296:.1%}")
    print(f"\nP(Bust) = {1296 - n_total}/1296 = {(1296-n_total)/1296:.4f} = {(1296-n_total)/1296:.1%}")

    return n_total, 1296

# Test with some examples
print("EXAMPLE 1: Worst combination {2, 3, 12}")
compute_probability_mathematical([2, 3, 12])

print("\n" + "="*70)
print("\nEXAMPLE 2: Best combination {6, 7, 8}")
compute_probability_mathematical([6, 7, 8])

print("\n" + "="*70)
print("\nEXAMPLE 3: Middle combination {4, 7, 10}")
compute_probability_mathematical([4, 7, 10])
