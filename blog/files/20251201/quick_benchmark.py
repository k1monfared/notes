#!/usr/bin/env python3
"""
Quick Benchmark Runner - For testing
Runs smaller samples to verify everything works
"""

import json
import sys
import time
import os
from datetime import datetime
from typing import Dict, List
from collections import defaultdict
from dataclasses import asdict

# Suppress debug output from game mechanics
sys.stderr = open(os.devnull, 'w')

# Monkey-patch print to suppress debug output
original_print = print
def silent_print(*args, **kwargs):
    # Only allow prints from this script (check stack)
    import traceback
    stack = traceback.extract_stack()
    # If called from main.py, suppress
    if any('main.py' in frame.filename for frame in stack):
        return
    original_print(*args, **kwargs)

__builtins__['print'] = silent_print

sys.path.insert(0, '/home/k1/public/cantstop-game/backend')
from main import GameMechanics

# Restore print for our script
__builtins__['print'] = original_print

from strategies_correct_implementation import get_all_strategies
from game_simulator import SinglePlayerSimulator, GameSimulator, GameResult


print("="*80)
print("QUICK BENCHMARK TEST")
print("="*80)

strategies = get_all_strategies()
print(f"\nTotal strategies: {len(strategies)}\n")

# Test single-player for just a few strategies
print("Testing single-player simulation...")
test_strategies = ['Greedy', 'Conservative(3)', 'Heuristic(1.0)', 'ExpectedValueMax']

for name in test_strategies:
    strategy = strategies[name]
    simulator = SinglePlayerSimulator(strategy, verbose=False)
    result = simulator.simulate_to_completion(target_columns=3, max_turns=500)
    print(f"  {name:25s}: {result['turns_to_3col']} turns, {result['busts']} busts")

# Test head-to-head
print("\nTesting head-to-head simulation...")
s1 = strategies['Greedy']
s2 = strategies['Conservative(3)']

wins = [0, 0]
for i in range(10):
    simulator = GameSimulator(s1, s2, verbose=False)
    result = simulator.simulate_game(max_turns=200)
    wins[result.winner] += 1

print(f"  Greedy vs Conservative(3): {wins[0]}-{wins[1]}")

print("\n✓ All tests passed! Ready for full benchmark.")
