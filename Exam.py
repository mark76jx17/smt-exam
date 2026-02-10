
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
from z3 import *
from argparse import ArgumentParser

parser = ArgumentParser()

parser.add_argument(
    "--numbers",
    type=int,
    nargs="+",      
    required=True,
    help="List of space-separated numbers"
)

parser.add_argument(
    "--target",
    type=int,
    required=True,
    help="Target number to reach"
)

parser.add_argument(
    "--resilient",
    action="store_true",
    help="Use the resilient strategy (adversarial variant)"
)

def CountingStrategy(numbers: list, target: int):
    n = len(numbers)
    #the best sequence of RESULTS to minimize the distance and the number of used numbers
    results = [Int(f'res_{i}') for i in range(n)]

    # the best permutation of NUMBERS) to use to minimize the distance and the number of used numbers
    perm = [Int(f"perm_{i}") for i in range(n)]

    Operation = Datatype('Operation')
    Operation.declare('add')
    Operation.declare('sub')
    Operation.declare('mul')
    Operation.declare('div')
    Operation = Operation.create()
    ops = [Const(f"op_{i}", Operation) for i in range(n-1)]

    final_result = Int("final_result")
    # The primary goal is to minimize the distance from the target
    distance = Int("distance")
    # The secondary goal is to minimize the number of used numbers
    used_numbers = Int("used_numbers")

    solver = Optimize() # minimize two objective functions - distance and used_numbers
    num_array = Array('num_array', IntSort(), IntSort())
    for i, v in enumerate(numbers):
        solver.add(num_array[i] == v)
    res_array = Array('res_array', IntSort(), IntSort())
    for i, _ in enumerate(range(n)):
        solver.add(res_array[i] == results[i])

    def add(init_res, next_num):
        return init_res + next_num
    
    def sub(init_res, next_num):
        return init_res - next_num
    
    def mul(init_res, next_num):
        return init_res * next_num
    
    def div(init_res, next_num):
        return If(And(next_num != 0, init_res % next_num == 0), init_res / next_num, init_res)  

    # constraints
    solver.add(Distinct(perm))  # The permutations MUST contain different values
    for i in range(n):
        solver.add(And(perm[i] >= 0, perm[i] < n))  
    solver.add(And(used_numbers >= 1, used_numbers <= n))  

    solver.add(results[0] == Select(num_array, perm[0]))  

    for i in range(n-1):

        transition = Or(
            And(ops[i] == Operation.add, Select(res_array, i+1) == add(results[i], Select(num_array, perm[i+1]))),
            And(ops[i] == Operation.sub, Select(res_array, i+1) == sub(results[i], Select(num_array, perm[i+1]))),
            And(ops[i] == Operation.mul, Select(res_array, i+1) == mul(results[i], Select(num_array, perm[i+1]))),
            And(ops[i] == Operation.div, Select(res_array, i+1) == div(results[i], Select(num_array, perm[i+1])))
        )

        # If the step number is greater than the number of used numbers, do not apply any transition: next state is equal to previous one
        solver.add(If(i < used_numbers - 1, transition, Select(res_array, i+1) == Select(res_array, i)))

    # The final result is the element in the array of intermediate results at the used_numbers-1 position
    solver.add(final_result == Select(res_array, used_numbers - 1))
    # The distance is defined as absolute value of final_result - target
    solver.add(distance == Abs(final_result - target))    
    solver.minimize(distance)
    solver.minimize(used_numbers)


    if solver.check() == sat:
        model = solver.model()

        # The as_long() method allows to convert z3 object into python-readable integers
        used_count = model[used_numbers].as_long()
        order_vals = [model[perm[i]].as_long() for i in range(used_count)]
        result_vals = [model[results[i]].as_long() for i in range(used_count)]

        first_num = model[results[0]].as_long()
        print("Initial number:", first_num)
        
        for i in range(used_count - 1):
            op_symbol = "?"
            if model[ops[i]] == Operation.add:
                op_symbol = "+"
            elif model[ops[i]] == Operation.sub:
                op_symbol = "-"
            elif model[ops[i]] == Operation.mul:
                op_symbol = "*"
            elif model[ops[i]] == Operation.div:
                op_symbol = "/"

            print(f"Step {i+1}: operation {op_symbol} with number {numbers[order_vals[i+1]]} -> result {result_vals[i+1]}")
        
        final = result_vals[used_count-1]
        dist = model[distance].as_long()
        
        print(f"Final number: {final}")
        print(f"Distance from goal: {dist}")


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

def CountingStrategyResilient(numbers: list, target: int):
    n = len(numbers)
    results = [Int(f'res_{i}') for i in range(n)]
    perm = [Int(f"perm_{i}") for i in range(n)]
    Operation = Datatype('Operation')
    Operation.declare('add')
    Operation.declare('sub')
    Operation.declare('mul')
    Operation.declare('div')
    Operation = Operation.create()
    ops = [Const(f"op_{i}", Operation) for i in range(n-1)]

    final_result = Int("final_result")
    distance = Int("distance")
    used_numbers = Int("used_numbers")    
    worst_distance = Int("worst_distance") # The worst-case distance after the adversary's attack

    solver = Optimize()
    num_array = Array('num_array', IntSort(), IntSort())
    for i, v in enumerate(numbers):
        solver.add(num_array[i] == v)

    res_array = Array('res_array', IntSort(), IntSort())
    for i in range(n):
        solver.add(res_array[i] == results[i])

    def add(init_res, next_num):
        return init_res + next_num

    def sub(init_res, next_num):
        return init_res - next_num

    def mul(init_res, next_num):
        return init_res * next_num

    def div(init_res, next_num):
        return If(And(next_num != 0, init_res % next_num == 0), init_res / next_num, init_res)

    def apply_op(op, pre, num):
        return If(op == Operation.add, add(pre, num),
               If(op == Operation.sub, sub(pre, num),
               If(op == Operation.mul, mul(pre, num),
                  div(pre, num))))

    solver.add(Distinct(perm))
    for i in range(n):
        solver.add(And(perm[i] >= 0, perm[i] < n))

    
    solver.add(And(used_numbers >= 2, used_numbers <= n)) # At least 2 numbers must be used to be resilient to the attack
    solver.add(results[0] == Select(num_array, perm[0]))

    for i in range(n-1):

        transition = Or(
            And(ops[i] == Operation.add, Select(res_array, i+1) == add(results[i], Select(num_array, perm[i+1]))),
            And(ops[i] == Operation.sub, Select(res_array, i+1) == sub(results[i], Select(num_array, perm[i+1]))),
            And(ops[i] == Operation.mul, Select(res_array, i+1) == mul(results[i], Select(num_array, perm[i+1]))),
            And(ops[i] == Operation.div, Select(res_array, i+1) == div(results[i], Select(num_array, perm[i+1])))
        )

        solver.add(If(i < used_numbers - 1, transition, Select(res_array, i+1) == Select(res_array, i)))

    solver.add(final_result == Select(res_array, used_numbers - 1))
    solver.add(distance == Abs(final_result - target))

    # The adversary replaces the last number used with an attack number in [0, 10].
    # For each possible attack number a, we compute the attacked final result:
    #   - When used_numbers == k (k >= 2): attacked_final = results[k-2] ops[k-2] a
    # The worst_distance must be >= the attacked distance for ALL possible attacks.
    # By minimizing worst_distance, we get worst_distance = max over all attack distances.

    for a in range(0, 11):
        attacked_final = IntVal(a)
        for k in range(n, 1, -1):  # k from n down to 2
            attacked_final = If(used_numbers == k,
                               apply_op(ops[k-2], results[k-2], IntVal(a)),
                               attacked_final)

        solver.add(worst_distance >= Abs(attacked_final - target))

    # Primary: minimize the worst-case distance after the adversary's best attack
    solver.minimize(worst_distance)
    # Secondary: minimize the number of used numbers
    solver.minimize(used_numbers)
    if solver.check() == sat:
        model = solver.model()

        used_count = model[used_numbers].as_long()
        order_vals = [model[perm[i]].as_long() for i in range(used_count)]
        result_vals = [model[results[i]].as_long() for i in range(used_count)]

        first_num = model[results[0]].as_long()
        print("Initial number:", first_num)

        for i in range(used_count - 1):
            op_symbol = "?"
            if model[ops[i]] == Operation.add:
                op_symbol = "+"
            elif model[ops[i]] == Operation.sub:
                op_symbol = "-"
            elif model[ops[i]] == Operation.mul:
                op_symbol = "*"
            elif model[ops[i]] == Operation.div:
                op_symbol = "/"

            print(f"Step {i+1}: operation {op_symbol} with number {numbers[order_vals[i+1]]} -> result {result_vals[i+1]}")

        final = result_vals[used_count-1]
        dist = model[distance].as_long()
        worst_dist = model[worst_distance].as_long()

        print(f"Final number: {final}")
        print(f"Distance from goal: {dist}")
        print(f"Distance from goal after attack: {worst_dist}")

# to execute the code, run in terminal:
# python Exam.py --numbers 1 3 5 8 10 50 --target 462
# to execute the resilient strategy, run in terminal:
# python Exam.py --numbers 1 3 5 8 10 50 --target 462 --resilient

if __name__ == "__main__":
    args = parser.parse_args()
    if args.resilient:
        CountingStrategyResilient(args.numbers, args.target)
    else:
        CountingStrategy(args.numbers, args.target)