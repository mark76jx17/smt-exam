
## Exam
# Consider the following Counting game:
#
# A player draws 6 different numbers. The goal is to combine these numbers using the elementary arithmetic operations (+, -, *, /) to obtain a number as close as possible to a given goal.
# Combining numbers means the following. First, the player chooses an initial number from the starting six numbers in their hand. Then, they choose a second number from their hand (different from the initial one), together with an operation, and compute the result of the operation. Now they choose a third number from their hand (different from the first and the second number), an operation, and compute the results. And so on.
#
# For example, if the user draws the numbers 1, 3, 5, 8, 10 e 50, and the goal number is 462, they can combine their numbers in the following way:
#
# 8 + 1 = 9
# 9 * 50 = 450
# 450 + 10 = 460
# 460 - 3 = 457
# 457 + 5 = 462
#
# Here, the player precisely reached the goal number. However, there are cases in which this is not possible. In such cases, the player has to aim to find the closest possible number to the goal.
# If it is possible to precisely reach the goal number, the players should try to minimize the numbers used. E.g., in the previous game, a better solution would have been:
#
# 50 - 3 = 47
# 47 * 10 = 470
# 470 - 8 = 462
#
# which only uses 4 numbers instead of 6.
#
# Each number can only be used one time.
#
# Your task is to implement a function CountingStrategy() that takes as input a list of 6 user numbers and 1 goal number, and returns the winning strategy.
# The winning strategy should be printed in the following form:
#   Initial number: <n1>
#   Step 1: operation <operation> with number <n2> -> result <r2>
#   Step 2: operation <operation> with number <n3> -> result <r3>
#   ...
#   Final number: <final_result>
#   Distance from goal: <distance>
#
#
# E.g.:
# CountingStrategy([1, 3, 5, 8, 10, 50], 462) should output:
#   Initial number: 50
#   Step 1: operation - with number 3 -> result 47
#   Step 2: operation * with number 10 -> result 470
#   Step 3: operation - with number 8 -> result 462
#   Final number: 462
#   Distance from goal: 0
#

# [Optional]
# After you have implemented the function to find the optimal strategy for the Counting game, consider the following variation of the game.
# The rules are as before, but now an adversary can "attack" the player after their last operation.
# The attack consists in choosing one number between 1 and 10, and replace it to the user choosen last number to make the final result as far as possible from the goal number.
# E.g., in the previous example, the attacker would have replaced the last number 8 with the number 0, making the player final result be 470 - 0 = 470.
# Hence, in this variant, the player must find a strategy that is resilient to the actions of the attacker. The best strategy will not be the one that gets closest to the goal, but rather the one that, after the worst possible attack, is as close as possible to the goal.
#
#
# Your task is to implement a function CountingStrategyResilient that takes the same input as CountingStrategy, and returns the optimal strategy for this variation.
# In the output, include:
#    Distance from goal after attack: <distance_after_attack>

import sys
import argparse
import time
from z3 import *
OP = ['+', '-', '*', '/']

def pick(idx, vals):
    # if-chain: select vals[idx] where idx is a Z3 Int
    e = IntVal(vals[0])
    for j in range(1, len(vals)):
        e = If(idx == j, IntVal(vals[j]), e)
    return e

def setup(s, numbers):
    """variables and base constraints: 
    o[i]: permutation index (which number is used at position i)
    p[i]: operation at step i (0=+, 1=-, 2=*, 3=/)
    r[i]: intermediate result after step i
    used: how many numbers are actually used (1..N)
    """
    N = len(numbers)
    o = [Int(f'o{i}') for i in range(N)]
    p = [Int(f'p{i}') for i in range(N - 1)]
    r = [Int(f'r{i}') for i in range(N)]
    used = Int('used')

    s.add(Distinct(o))
    for i in range(N):
        s.add(o[i] >= 0, o[i] < N)
    for i in range(N - 1):
        s.add(p[i] >= 0, p[i] <= 3)
    s.add(r[0] == pick(o[0], numbers))
    for i in range(1, N):
        ni = pick(o[i], numbers)
        s.add(Implies(used > i, Or(
            And(p[i-1] == 0, r[i] == r[i-1] + ni),
            And(p[i-1] == 1, r[i] == r[i-1] - ni),
            And(p[i-1] == 2, r[i] == r[i-1] * ni),
            And(p[i-1] == 3, ni != 0, r[i-1] == r[i] * ni), 
        )))
        s.add(Implies(used <= i, r[i] == r[i-1]))

    return o, p, r, used

def get_final(r, used, N):
    f = r[0]
    for i in range(1, N):
        f = If(used > i, r[i], f)
    return f

def show(m, numbers, o, p, r, used):
    k = m[used].as_long()
    print(f"  Initial number: {numbers[m[o[0]].as_long()]}")
    for i in range(1, k):
        print(f"  Step {i}: operation {OP[m[p[i-1]].as_long()]} with number "
              f"{numbers[m[o[i]].as_long()]} -> result {m[r[i]].as_long()}")
    print(f"  Final number: {m[r[k-1]].as_long()}")


def CountingStrategy(numbers, goal):
    N = len(numbers)
    s = Optimize()
    o, p, r, used = setup(s, numbers)
    s.add(used >= 1, used <= N)
    final = get_final(r, used, N)
    dist = Int('dist')
    # dist >= |final - goal|
    s.add(dist >= final - goal, dist >= goal - final)
    # minimize distance first, then used numbers
    s.minimize(dist * (N + 1) + used)
    if s.check() == sat:
        m = s.model()
        show(m, numbers, o, p, r, used)
        d = m[dist].as_long()
        print(f"  Distance from goal: {d}")
        return d
    print("  No solution found")
    return None


def CountingStrategyResilient(numbers, goal):
    N = len(numbers)
    s = Optimize()
    o, p, r, used = setup(s, numbers)
    s.add(used >= 2, used <= N)

    # used==2 -> pre=r[0], lop=p[0]  |  used==k -> pre=r[k-2], lop=p[k-2]
    pre = r[0]; lop = p[0]
    for k in range(3, N + 1):
        pre = If(used == k, r[k-2], pre)
        lop = If(used == k, p[k-2], lop)

    # Minimax: for each attack number 0..10, worst >= |attacked_result - goal|
    worst = Int('worst')
    for atk in range(0, 11):
        if atk == 0:
            
            ar = If(lop == 2, IntVal(0), pre)
        else:
            ar = If(lop == 0, pre + atk,
                 If(lop == 1, pre - atk,
                 If(lop == 2, pre * atk,
                    If(pre % atk == 0, pre / atk, pre)))) 
        s.add(worst >= ar - goal, worst >= goal - ar)

    s.minimize(worst * (N + 1) + used)

    if s.check() == sat:
        m = s.model()
        show(m, numbers, o, p, r, used)
        pre_v = m.evaluate(pre).as_long()
        lop_v = m.evaluate(lop).as_long()
        wa, wd, war = 0, -1, 0
        for atk in range(0, 11):
            if atk == 0:
                a_res = 0 if lop_v == 2 else pre_v
            elif lop_v == 0: a_res = pre_v + atk
            elif lop_v == 1: a_res = pre_v - atk
            elif lop_v == 2: a_res = pre_v * atk
            else: a_res = pre_v // atk if pre_v % atk == 0 else pre_v
            d = abs(a_res - goal)
            if d > wd:
                wa, wd, war = atk, d, a_res

        wd_z3 = m[worst].as_long()
        print(f"  Distance from goal after attack: {wd_z3}")
        print(f"  Worst attack: replace last number with {wa} "
              f"-> {pre_v} {OP[lop_v]} {wa} = {war}")
        return wd_z3
    print("  No solution found")
    return None


def run_benchmark():
    TESTS = [
        # (numbers, goal, mode, expected_dist, description)
        ([1, 3, 5, 8, 10, 50], 462, "standard", 0,
         "50-3=47, *10=470, -8=462"),
        ([1, 2, 3, 4, 5, 6], 100, "standard", 0,
         "6+4=10, *2=20, *5=100"),
        ([1, 2, 3, 4, 5, 6], 720, "standard", 0,
         "1*2*3*4*5*6=720"),
        ([5, 10, 25, 50, 75, 100], 999, "standard", 0,
         "25+75=100, *100=10000, -10=9990, *5=49950, /50=999"),
        ([1, 5, 10, 25, 50, 75], 999, "standard", 0,
         "25-5=20, *50=1000, -1=999"),
        ([1, 3, 5, 8, 10, 50], 462, "resilient", 1,
         "Resilient: division no-op via prime pre-last"),
        ([1, 2, 3, 4, 5, 6], 100, "resilient", 1,
         "Resilient: division no-op, dist 1"),
    ]

    passed, failed, total = 0, 0, 0
    for nums, goal, mode, exp, desc in TESTS:
        total += 1
        print(f"{'='*60}")
        print(f"Test {total}: {desc}")
        print(f"Numbers: {nums}, Goal: {goal}, Mode: {mode}")
        print()
        t0 = time.time()
        if mode == "standard":
            got = CountingStrategy(nums, goal)
        else:
            got = CountingStrategyResilient(nums, goal)
        elapsed = time.time() - t0

        if exp is not None:
            ok = got == exp
            tag = "PASS" if ok else "FAIL"
            print(f"  Expected distance: {exp}, Got: {got} [{tag}] ({elapsed:.1f}s)")
            if ok:
                passed += 1
            else:
                failed += 1
        else:
            print(f"  Got distance: {got} (no expected value) ({elapsed:.1f}s)")
        print()

    print(f"{'='*60}")
    print(f"Benchmark results: {passed} passed, {failed} failed, "
          f"{total - passed - failed} unchecked / {total} total")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Counting Game Solver (Z3)")
    parser.add_argument('--numbers', nargs='+', type=int,
                        help='List of available numbers')
    parser.add_argument('--target', type=int,
                        help='Goal number to reach')
    parser.add_argument('--resilient', action='store_true',
                        help='Use resilient strategy (adversary variant)')
    parser.add_argument('--benchmark', action='store_true',
                        help='Run benchmark suite')
    args = parser.parse_args()

    if args.benchmark:
        run_benchmark()
    else:
        nums = args.numbers if args.numbers else [1, 3, 5, 8, 10, 50]
        goal = args.target if args.target else 462
        print(f"Numbers: {nums}, Goal: {goal}")
        if args.resilient:
            print("Mode: Resilient\n")
            CountingStrategyResilient(nums, goal)
        else:
            print("Mode: Standard\n")
            CountingStrategy(nums, goal)
