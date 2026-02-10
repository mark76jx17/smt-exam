# Counting Game - Exam
## Requirements

Install z3 Python APIs through pip: 
```pip3 install z3-solver```

## Problem Description

Consider the following **Counting game**:

A player draws **6 different numbers**. The goal is to combine these numbers using the elementary arithmetic operations (`+`, `-`, `*`, `/`) to obtain a number as close as possible to a given goal.

### Rules

**Combining numbers** works as follows:

1. The player chooses an **initial number** from the starting six numbers in their hand
2. They choose a **second number** from their hand (different from the initial one), together with an operation, and compute the result
3. They choose a **third number** from their hand (different from the first and second), an operation, and compute the result
4. And so on...

**Important constraints:**
- Each number can only be used **one time**
- If it is possible to precisely reach the goal number, the player should try to **minimize the numbers used**

---

## Example

**Input:** Numbers `[1, 3, 5, 8, 10, 50]`, Goal `462`

### Solution using all 6 numbers:

```
8 + 1 = 9
9 * 50 = 450
450 + 10 = 460
460 - 3 = 457
457 + 5 = 462
```

### Better solution using only 4 numbers:

```
50 - 3 = 47
47 * 10 = 470
470 - 8 = 462
```

This solution is better because it uses fewer numbers while still reaching the goal.

---

## Task

Implement a function `CountingStrategy()` that:

- **Input:** A list of 6 user numbers and 1 goal number
- **Output:** The winning strategy

### Output Format

The strategy should be printed in the following form:

```
Initial number: <n1>
Step 1: operation <operation> with number <n2> -> result <r2>
Step 2: operation <operation> with number <n3> -> result <r3>
...
Final number: <final_result>
Distance from goal: <distance>
```

### Example Output

```python
CountingStrategy([1, 3, 5, 8, 10, 50], 462)
```

Should output:

```
Initial number: 50
Step 1: operation - with number 3 -> result 47
Step 2: operation * with number 10 -> result 470
Step 3: operation - with number 8 -> result 462
Final number: 462
Distance from goal: 0
```

---

## Evaluation Criteria

1. **Primary:** Minimize the distance from the goal (ideally 0)
2. **Secondary:** If goal is reachable, minimize the number of steps used

---

## Optional: Adversarial Variant

After implementing the basic `CountingStrategy` function, consider the following **variation** of the game.

### Modified Rules

The rules are as before, but now an **adversary can "attack"** the player after their last operation.

The attack consists in:
- Choosing one number between **1 and 10**
- **Replacing** the player's chosen last number to make the final result as far as possible from the goal

### Example

Using the previous example with goal `462`:

**Original strategy:**
```
50 - 3 = 47
47 * 10 = 470
470 - 8 = 462
```

**After attack:** The attacker replaces the last number `8` with `0`:
```
470 - 0 = 470
```

The player's final result becomes `470` instead of `462`.

### Resilient Strategy

In this variant, the player must find a strategy that is **resilient to the attacker's actions**.

The best strategy is **not** the one that gets closest to the goal, but rather the one that, **after the worst possible attack**, is as close as possible to the goal.

---

## Task (Optional)

Implement a function `CountingStrategyResilient()` that:

- **Input:** Same as `CountingStrategy` (list of 6 numbers + goal)
- **Output:** The optimal resilient strategy

### Output Format

Same as before, but include an additional line:

```
Initial number: <n1>
Step 1: operation <operation> with number <n2> -> result <r2>
Step 2: operation <operation> with number <n3> -> result <r3>
...
Final number: <final_result>
Distance from goal: <distance>
Distance from goal after attack: <distance_after_attack>
```

---

## Execution

To execute the code, run in terminal:

```bash
python Exam.py --numbers 1 3 5 8 10 50 --target 462
```

To execute the resilient strategy, run in terminal:

```bash
python Exam.py --numbers 1 3 5 8 10 50 --target 462 --resilient
```

