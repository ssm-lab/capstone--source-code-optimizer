"""
This module provides various mathematical helper functions.
It intentionally contains code smells for demonstration purposes.
"""

from ast import List
import collections
import math


def long_element_chain(data):
    """Access deeply nested elements repeatedly."""
    return data["level1"]["level2"]["level3"]["level4"]["level5"]


def long_lambda_function():
    """Creates an unnecessarily long lambda function."""
    return lambda x: (x**2 + 2 * x + 1) / (math.sqrt(x) + x**3 + x**4 + math.sin(x) + math.cos(x))


def long_message_chain(obj):
    """Access multiple chained attributes and methods."""
    return obj.get_first().get_second().get_third().get_fourth().get_fifth().value


def long_parameter_list(a, b, c, d, e, f, g, h, i, j):
    """Function with too many parameters."""
    return (a + b) * (c - d) / (e + f) ** g - h * i + j


def member_ignoring_method(self):
    """Method that does not use instance attributes."""
    return "I ignore all instance members!"


_cache = {}


def cached_expensive_call(x):
    """Caches repeated calls to avoid redundant computations."""
    if x in _cache:
        return _cache[x]
    result = math.factorial(x) + math.sqrt(x) + math.log(x + 1)
    _cache[x] = result
    return result


def string_concatenation_in_loop(words):
    """Bad practice: String concatenation inside a loop."""
    result = ""
    for word in words:
        result += word + ", "  # Inefficient
    return result.strip(", ")


# More functions to reach 250 lines with similar issues.
def complex_math_operation(a, b, c, d, e, f, g, h):
    """Another long parameter list with a complex calculation."""
    return a**b + math.sqrt(c) - math.log(d) + e**f + g / h


def factorial_chain(x):
    """Long element chain for factorial calculations."""
    return math.factorial(math.ceil(math.sqrt(math.fabs(x))))


def inefficient_fibonacci(n):
    """Recursively calculates Fibonacci inefficiently."""
    if n <= 1:
        return n
    return inefficient_fibonacci(n - 1) + inefficient_fibonacci(n - 2)


class MathHelper:
    def __init__(self, value):
        self.value = value

    def chained_operations(self):
        """Demonstrates a long message chain."""
        return self.value.increment().double().square().cube().finalize()

    def ignore_member(self):
        """This method does not use 'self' but exists in the class."""
        return "Completely ignores instance attributes!"


def expensive_function(x):
    return x * x


def test_case():
    result1 = expensive_function(42)
    result2 = expensive_function(42)
    result3 = expensive_function(42)
    return result1 + result2 + result3


def long_loop_with_string_concatenation(n):
    """Creates a long string inefficiently inside a loop."""
    result = ""
    for i in range(n):
        result += str(i) + " - "  # Inefficient string building
    return result.strip(" - ")


# More helper functions to reach 250 lines with similar bad practices.
def another_long_parameter_list(a, b, c, d, e, f, g, h, i):
    """Another example of too many parameters."""
    return a * b + c / d - e**f + g - h + i


def contains_large_strings(strings):
    return any([len(s) > 10 for s in strings])


def do_god_knows_what():
    mystring = "i hate capstone"
    n = 10

    for i in range(n):
        b = 10
        mystring += "word"

    return n


def do_something_dumb():
    return


class Solution:
    def isSameTree(self, p, q):
        return (
            p == q
            if not p or not q
            else p.val == q.val
            and self.isSameTree(p.left, q.left)
            and self.isSameTree(p.right, q.right)
        )


# Code Smell: Long Parameter List
class Vehicle:
    def __init__(
        self,
        make,
        model,
        year: int,
        color,
        fuel_type,
        engine_start_stop_option,
        mileage,
        suspension_setting,
        transmission,
        price,
        seat_position_setting=None,
    ):
        # Code Smell: Long Parameter List in __init__
        self.make = make  # positional argument
        self.model = model
        self.year = year
        self.color = color
        self.fuel_type = fuel_type
        self.engine_start_stop_option = engine_start_stop_option
        self.mileage = mileage
        self.suspension_setting = suspension_setting
        self.transmission = transmission
        self.price = price
        self.seat_position_setting = seat_position_setting  # default value
        self.owner = None  # Unused class attribute, used in constructor

    def display_info(self):
        # Code Smell: Long Message Chain
        random_test = self.make.split("")
        print(
            f"Make: {self.make}, Model: {self.model}, Year: {self.year}".upper().replace(",", "")[
                ::2
            ]
        )

    def calculate_price(self):
        # Code Smell: List Comprehension in an All Statement
        condition = all(
            [
                isinstance(attribute, str)
                for attribute in [self.make, self.model, self.year, self.color]
            ]
        )
        if condition:
            return (
                self.price * 0.9
            )  # Apply a 10% discount if all attributes are strings (totally arbitrary condition)

        return self.price

    def unused_method(self):
        # Code Smell: Member Ignoring Method
        print("This method doesn't interact with instance attributes, it just prints a statement.")


def longestArithSeqLength2(A: List[int]) -> int:
    dp = collections.defaultdict(int)
    for i in range(len(A)):
        for j in range(i + 1, len(A)):
            a, b = A[i], A[j]
            dp[b - a, j] = max(dp[b - a, j], dp[b - a, i] + 1)
    return max(dp.values()) + 1


def longestArithSeqLength3(A: List[int]) -> int:
    dp = collections.defaultdict(int)
    for i in range(len(A)):
        for j in range(i + 1, len(A)):
            a, b = A[i], A[j]
            dp[b - a, j] = max(dp[b - a, j], dp[b - a, i] + 1)
    return max(dp.values()) + 1


if __name__ == "__main__":
    print("Math Helper Library Loaded")
