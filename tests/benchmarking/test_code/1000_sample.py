"""
This module provides various mathematical helper functions.
It intentionally contains code smells for demonstration purposes.
"""

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


def longestArithSeqLength2(A: list[int]) -> int:
    dp = collections.defaultdict(int)
    for i in range(len(A)):
        for j in range(i + 1, len(A)):
            a, b = A[i], A[j]
            dp[b - a, j] = max(dp[b - a, j], dp[b - a, i] + 1)
    return max(dp.values()) + 1


def longestArithSeqLength3(A: list[int]) -> int:
    dp = collections.defaultdict(int)
    for i in range(len(A)):
        for j in range(i + 1, len(A)):
            a, b = A[i], A[j]
            dp[b - a, j] = max(dp[b - a, j], dp[b - a, i] + 1)
    return max(dp.values()) + 1


def longestArithSeqLength4(A: list[int]) -> int:
    dp = collections.defaultdict(int)
    for i in range(len(A)):
        for j in range(i + 1, len(A)):
            a, b = A[i], A[j]
            dp[b - a, j] = max(dp[b - a, j], dp[b - a, i] + 1)
    return max(dp.values()) + 1


def longestArithSeqLength5(A: list[int]) -> int:
    dp = collections.defaultdict(int)
    for i in range(len(A)):
        for j in range(i + 1, len(A)):
            a, b = A[i], A[j]
            dp[b - a, j] = max(dp[b - a, j], dp[b - a, i] + 1)
    return max(dp.values()) + 1


class Calculator:
    def add(sum):
        a = int(input("Enter number 1: "))
        b = int(input("Enter number 2: "))
        sum = a + b
        print("The addition of two numbers:", sum)

    def mul(mul):
        a = int(input("Enter number 1: "))
        b = int(input("Enter number 2: "))
        mul = a * b
        print("The multiplication of two numbers:", mul)

    def sub(sub):
        a = int(input("Enter number 1: "))
        b = int(input("Enter number 2: "))
        sub = a - b
        print("The subtraction of two numbers:", sub)

    def div(div):
        a = int(input("Enter number 1: "))
        b = int(input("Enter number 2: "))
        div = a / b
        print("The division of two numbers: ", div)

    def exp(exp):
        a = int(input("Enter number 1: "))
        b = int(input("Enter number 2: "))
        exp = a**b
        print("The exponent of the following numbers are: ", exp)


class rootop:
    def sqrt(self):
        a = int(input("Enter number 1: "))
        b = int(input("Enter number 2: "))
        print(math.sqrt(a))
        print(math.sqrt(b))

    def cbrt(self):
        a = int(input("Enter number 1: "))
        b = int(input("Enter number 2: "))
        print(a ** (1 / 3))
        print(b ** (1 / 3))

    def ranroot(self):
        a = int(input("Enter the x: "))
        b = int(input("Enter the y: "))
        b_div = 1 / b
        print("Your answer for the random root is: ", a**b_div)


import random
import string


def generate_random_string(length=10):
    """Generate a random string of given length."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def add_numbers(a, b):
    """Return the sum of two numbers."""
    return a + b


def multiply_numbers(a, b):
    """Return the product of two numbers."""
    return a * b


def is_even(n):
    """Check if a number is even."""
    return n % 2 == 0


def factorial(n):
    """Calculate the factorial of a number recursively."""
    return 1 if n == 0 else n * factorial(n - 1)


def reverse_string1(s):
    """Reverse a given string."""
    return s[::-1]


def count_vowels1(s):
    """Count the number of vowels in a string."""
    return sum(1 for char in s.lower() if char in "aeiou")


def find_max1(numbers):
    """Find the maximum value in a list of numbers."""
    return max(numbers) if numbers else None


def shuffle_list1(lst):
    """Shuffle a list randomly."""
    random.shuffle(lst)
    return lst


def fibonacci1(n):
    """Generate Fibonacci sequence up to the nth term."""
    sequence = [0, 1]
    for _ in range(n - 2):
        sequence.append(sequence[-1] + sequence[-2])
    return sequence[:n]


def is_palindrome1(s):
    """Check if a string is a palindrome."""
    return s == s[::-1]


def remove_duplicates1(lst):
    """Remove duplicates from a list."""
    return list(set(lst))


def roll_dice():
    """Simulate rolling a six-sided dice."""
    return random.randint(1, 6)


def guess_number_game():
    """A simple number guessing game."""
    number = random.randint(1, 100)
    attempts = 0
    print("Guess a number between 1 and 100!")
    while True:
        guess = int(input("Enter your guess: "))
        attempts += 1
        if guess < number:
            print("Too low!")
        elif guess > number:
            print("Too high!")
        else:
            print(f"Correct! You guessed it in {attempts} attempts.")
            break


def sort_numbers(lst):
    """Sort a list of numbers."""
    return sorted(lst)


def merge_dicts(d1, d2):
    """Merge two dictionaries."""
    return {**d1, **d2}


def get_random_element(lst):
    """Get a random element from a list."""
    return random.choice(lst) if lst else None


def sum_list1(lst):
    """Return the sum of elements in a list."""
    return sum(lst)


def countdown(n):
    """Print a countdown from n to 0."""
    for i in range(n, -1, -1):
        print(i)


def get_ascii_value(char):
    """Return ASCII value of a character."""
    return ord(char)


def generate_random_password(length=12):
    """Generate a random password."""
    chars = string.ascii_letters + string.digits + string.punctuation
    return "".join(random.choice(chars) for _ in range(length))


def find_common_elements(lst1, lst2):
    """Find common elements between two lists."""
    return list(set(lst1) & set(lst2))


def print_multiplication_table(n):
    """Print multiplication table for a number."""
    for i in range(1, 11):
        print(f"{n} x {i} = {n * i}")


def most_frequent_element(lst):
    """Find the most frequent element in a list."""
    return max(set(lst), key=lst.count) if lst else None


def is_prime(n):
    """Check if a number is prime."""
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True


def convert_to_binary(n):
    """Convert a number to binary."""
    return bin(n)[2:]


def sum_of_digits1(n):
    """Find the sum of digits of a number."""
    return sum(int(digit) for digit in str(n))


def matrix_transpose(matrix):
    """Transpose a matrix."""
    return list(map(list, zip(*matrix)))


# Additional random functions to make it reach 200 lines
for _ in range(100):

    def temp_func():
        pass


# 1. Function to reverse a string
def reverse_string(s):
    return s[::-1]


# 2. Function to check if a number is prime
def is_prime1(n):
    return n > 1 and all(n % i != 0 for i in range(2, int(n**0.5) + 1))


# 3. Function to calculate factorial
def factorial1(n):
    return 1 if n <= 1 else n * factorial(n - 1)


# 4. Function to find the maximum number in a list
def find_max(lst):
    return max(lst)


# 5. Function to count vowels in a string
def count_vowels(s):
    return sum(1 for char in s if char.lower() in "aeiou")


# 6. Function to flatten a nested list
def flatten(lst):
    return [item for sublist in lst for item in sublist]


# 7. Function to check if a string is a palindrome
def is_palindrome(s):
    return s == s[::-1]


# 8. Function to generate Fibonacci sequence
def fibonacci(n):
    return [0, 1] if n <= 1 else fibonacci(n - 1) + [fibonacci(n - 1)[-1] + fibonacci(n - 1)[-2]]


# 9. Function to calculate the area of a circle
def circle_area(r):
    return 3.14159 * r**2


# 10. Function to remove duplicates from a list
def remove_duplicates(lst):
    return list(set(lst))


# 11. Function to sort a dictionary by value
def sort_dict_by_value(d):
    return dict(sorted(d.items(), key=lambda x: x[1]))


# 12. Function to count words in a string
def count_words(s):
    return len(s.split())


# 13. Function to check if two strings are anagrams
def are_anagrams(s1, s2):
    return sorted(s1) == sorted(s2)


# 14. Function to find the intersection of two lists
def list_intersection(lst1, lst2):
    return list(set(lst1) & set(lst2))


# 15. Function to calculate the sum of digits of a number
def sum_of_digits2(n):
    return sum(int(digit) for digit in str(n))


# 16. Function to generate a random password
def generate_password(length=8):
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


# 21. Function to find the longest word in a string
def longest_word(s):
    return max(s.split(), key=len)


# 22. Function to capitalize the first letter of each word
def capitalize_words(s):
    return " ".join(word.capitalize() for word in s.split())


# 23. Function to check if a year is a leap year
def is_leap_year(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


# 24. Function to calculate the GCD of two numbers
def gcd1(a, b):
    return a if b == 0 else gcd(b, a % b)


# 25. Function to calculate the LCM of two numbers
def lcm1(a, b):
    return a * b // gcd(a, b)


# 26. Function to generate a list of squares
def squares(n):
    return [i**2 for i in range(1, n + 1)]


# 27. Function to generate a list of cubes
def cubes(n):
    return [i**3 for i in range(1, n + 1)]


# 28. Function to check if a list is sorted
def is_sorted(lst):
    return all(lst[i] <= lst[i + 1] for i in range(len(lst) - 1))


# 29. Function to shuffle a list
def shuffle_list(lst):
    random.shuffle(lst)
    return lst


# 30. Function to find the mode of a list
from collections import Counter


def find_mode(lst):
    return Counter(lst).most_common(1)[0][0]


# 31. Function to calculate the mean of a list
def mean(lst):
    return sum(lst) / len(lst)


# 32. Function to calculate the median of a list
def median(lst):
    lst_sorted = sorted(lst)
    mid = len(lst) // 2
    return (lst_sorted[mid] + lst_sorted[~mid]) / 2


# 33. Function to calculate the standard deviation of a list
def std_dev(lst):
    m = mean(lst)
    return math.sqrt(sum((x - m) ** 2 for x in lst) / len(lst))


# 34. Function to find the nth Fibonacci number
def nth_fibonacci(n):
    return fibonacci(n)[-1]


# 35. Function to check if a number is even
def is_even1(n):
    return n % 2 == 0


# 36. Function to check if a number is odd
def is_odd(n):
    return n % 2 != 0


# 37. Function to convert Celsius to Fahrenheit
def celsius_to_fahrenheit(c):
    return (c * 9 / 5) + 32


# 38. Function to convert Fahrenheit to Celsius
def fahrenheit_to_celsius(f):
    return (f - 32) * 5 / 9


# 39. Function to calculate the hypotenuse of a right triangle
def hypotenuse(a, b):
    return math.sqrt(a**2 + b**2)


# 40. Function to calculate the perimeter of a rectangle
def rectangle_perimeter(l, w):
    return 2 * (l + w)


# 41. Function to calculate the area of a rectangle
def rectangle_area(l, w):
    return l * w


# 42. Function to calculate the perimeter of a square
def square_perimeter(s):
    return 4 * s


# 43. Function to calculate the area of a square
def square_area(s):
    return s**2


# 44. Function to calculate the perimeter of a circle
def circle_perimeter(r):
    return 2 * 3.14159 * r


# 45. Function to calculate the volume of a cube
def cube_volume(s):
    return s**3


# 46. Function to calculate the volume of a sphere
def sphere_volume1(r):
    return (4 / 3) * 3.14159 * r**3


# 47. Function to calculate the volume of a cylinder
def cylinder_volume1(r, h):
    return 3.14159 * r**2 * h


# 48. Function to calculate the volume of a cone
def cone_volume1(r, h):
    return (1 / 3) * 3.14159 * r**2 * h


# 49. Function to calculate the surface area of a cube
def cube_surface_area(s):
    return 6 * s**2


# 50. Function to calculate the surface area of a sphere
def sphere_surface_area1(r):
    return 4 * 3.14159 * r**2


# 51. Function to calculate the surface area of a cylinder
def cylinder_surface_area1(r, h):
    return 2 * 3.14159 * r * (r + h)


# 52. Function to calculate the surface area of a cone
def cone_surface_area1(r, l):
    return 3.14159 * r * (r + l)


# 53. Function to generate a list of random numbers
def random_numbers(n, start=0, end=100):
    return [random.randint(start, end) for _ in range(n)]


# 54. Function to find the index of an element in a list
def find_index(lst, element):
    return lst.index(element) if element in lst else -1


# 55. Function to remove an element from a list
def remove_element(lst, element):
    return [x for x in lst if x != element]


# 56. Function to replace an element in a list
def replace_element(lst, old, new):
    return [new if x == old else x for x in lst]


# 57. Function to rotate a list by n positions
def rotate_list(lst, n):
    return lst[n:] + lst[:n]


# 58. Function to find the second largest number in a list
def second_largest(lst):
    return sorted(lst)[-2]


# 59. Function to find the second smallest number in a list
def second_smallest(lst):
    return sorted(lst)[1]


# 60. Function to check if all elements in a list are unique
def all_unique(lst):
    return len(lst) == len(set(lst))


# 61. Function to find the difference between two lists
def list_difference(lst1, lst2):
    return list(set(lst1) - set(lst2))


# 62. Function to find the union of two lists
def list_union(lst1, lst2):
    return list(set(lst1) | set(lst2))


# 63. Function to find the symmetric difference of two lists
def symmetric_difference(lst1, lst2):
    return list(set(lst1) ^ set(lst2))


# 64. Function to check if a list is a subset of another list
def is_subset(lst1, lst2):
    return set(lst1).issubset(set(lst2))


# 65. Function to check if a list is a superset of another list
def is_superset(lst1, lst2):
    return set(lst1).issuperset(set(lst2))


# 66. Function to find the frequency of elements in a list
def element_frequency(lst):
    return {x: lst.count(x) for x in set(lst)}


# 67. Function to find the most frequent element in a list
def most_frequent(lst):
    return max(set(lst), key=lst.count)


# 68. Function to find the least frequent element in a list
def least_frequent(lst):
    return min(set(lst), key=lst.count)


# 69. Function to find the average of a list of numbers
def average(lst):
    return sum(lst) / len(lst)


# 70. Function to find the sum of a list of numbers
def sum_list(lst):
    return sum(lst)


# 71. Function to find the product of a list of numbers
def product_list(lst):
    return math.prod(lst)


# 72. Function to find the cumulative sum of a list
def cumulative_sum(lst):
    return [sum(lst[: i + 1]) for i in range(len(lst))]


# 73. Function to find the cumulative product of a list
def cumulative_product(lst):
    return [math.prod(lst[: i + 1]) for i in range(len(lst))]


# 74. Function to find the difference between consecutive elements in a list
def consecutive_difference(lst):
    return [lst[i + 1] - lst[i] for i in range(len(lst) - 1)]


# 75. Function to find the ratio between consecutive elements in a list
def consecutive_ratio(lst):
    return [lst[i + 1] / lst[i] for i in range(len(lst) - 1)]


# 76. Function to find the cumulative difference of a list
def cumulative_difference(lst):
    return [lst[0]] + [lst[i] - lst[i - 1] for i in range(1, len(lst))]


# 77. Function to find the cumulative ratio of a list
def cumulative_ratio(lst):
    return [lst[0]] + [lst[i] / lst[i - 1] for i in range(1, len(lst))]


# 78. Function to find the absolute difference between two lists
def absolute_difference(lst1, lst2):
    return [abs(lst1[i] - lst2[i]) for i in range(len(lst1))]


# 79. Function to find the absolute sum of two lists
def absolute_sum(lst1, lst2):
    return [lst1[i] + lst2[i] for i in range(len(lst1))]


# 80. Function to find the absolute product of two lists
def absolute_product(lst1, lst2):
    return [lst1[i] * lst2[i] for i in range(len(lst1))]


# 81. Function to find the absolute ratio of two lists
def absolute_ratio(lst1, lst2):
    return [lst1[i] / lst2[i] for i in range(len(lst1))]


# 82. Function to find the absolute cumulative sum of two lists
def absolute_cumulative_sum(lst1, lst2):
    return [sum(lst1[: i + 1]) + sum(lst2[: i + 1]) for i in range(len(lst1))]


# 83. Function to find the absolute cumulative product of two lists
def absolute_cumulative_product(lst1, lst2):
    return [math.prod(lst1[: i + 1]) * math.prod(lst2[: i + 1]) for i in range(len(lst1))]


# 84. Function to find the absolute cumulative difference of two lists
def absolute_cumulative_difference(lst1, lst2):
    return [sum(lst1[: i + 1]) - sum(lst2[: i + 1]) for i in range(len(lst1))]


# 85. Function to find the absolute cumulative ratio of two lists
def absolute_cumulative_ratio(lst1, lst2):
    return [sum(lst1[: i + 1]) / sum(lst2[: i + 1]) for i in range(len(lst1))]


# 86. Function to find the absolute cumulative sum of a list
def absolute_cumulative_sum_single(lst):
    return [sum(lst[: i + 1]) for i in range(len(lst))]


# 87. Function to find the absolute cumulative product of a list
def absolute_cumulative_product_single(lst):
    return [math.prod(lst[: i + 1]) for i in range(len(lst))]


# 88. Function to find the absolute cumulative difference of a list
def absolute_cumulative_difference_single(lst):
    return [sum(lst[: i + 1]) - sum(lst[:i]) for i in range(len(lst))]


# 89. Function to find the absolute cumulative ratio of a list
def absolute_cumulative_ratio_single(lst):
    return [sum(lst[: i + 1]) / sum(lst[:i]) for i in range(len(lst))]


# 90. Function to find the absolute cumulative sum of a list with a constant
def absolute_cumulative_sum_constant(lst, constant):
    return [sum(lst[: i + 1]) + constant for i in range(len(lst))]


# 91. Function to find the absolute cumulative product of a list with a constant
def absolute_cumulative_product_constant(lst, constant):
    return [math.prod(lst[: i + 1]) * constant for i in range(len(lst))]


# 92. Function to find the absolute cumulative difference of a list with a constant
def absolute_cumulative_difference_constant(lst, constant):
    return [sum(lst[: i + 1]) - constant for i in range(len(lst))]


# 93. Function to find the absolute cumulative ratio of a list with a constant
def absolute_cumulative_ratio_constant(lst, constant):
    return [sum(lst[: i + 1]) / constant for i in range(len(lst))]


# 94. Function to find the absolute cumulative sum of a list with a list of constants
def absolute_cumulative_sum_constants(lst, constants):
    return [sum(lst[: i + 1]) + constants[i] for i in range(len(lst))]


# 95. Function to find the absolute cumulative product of a list with a list of constants
def absolute_cumulative_product_constants(lst, constants):
    return [math.prod(lst[: i + 1]) * constants[i] for i in range(len(lst))]


# 96. Function to find the absolute cumulative difference of a list with a list of constants
def absolute_cumulative_difference_constants(lst, constants):
    return [sum(lst[: i + 1]) - constants[i] for i in range(len(lst))]


# 97. Function to find the absolute cumulative ratio of a list with a list of constants
def absolute_cumulative_ratio_constants(lst, constants):
    return [sum(lst[: i + 1]) / constants[i] for i in range(len(lst))]


# 98. Function to find the absolute cumulative sum of a list with a function
def absolute_cumulative_sum_function(lst, func):
    return [sum(lst[: i + 1]) + func(i) for i in range(len(lst))]


# 99. Function to find the absolute cumulative product of a list with a function
def absolute_cumulative_product_function(lst, func):
    return [math.prod(lst[: i + 1]) * func(i) for i in range(len(lst))]


# 100. Function to find the absolute cumulative difference of a list with a function
def absolute_cumulative_difference_function(lst, func):
    return [sum(lst[: i + 1]) - func(i) for i in range(len(lst))]


# 101. Function to find the absolute cumulative ratio of a list with a function
def absolute_cumulative_ratio_function(lst, func):
    return [sum(lst[: i + 1]) / func(i) for i in range(len(lst))]


# 102. Function to find the absolute cumulative sum of a list with a lambda function
def absolute_cumulative_sum_lambda(lst, func):
    return [sum(lst[: i + 1]) + func(i) for i in range(len(lst))]


# 103. Function to find the absolute cumulative product of a list with a lambda function
def absolute_cumulative_product_lambda(lst, func):
    return [math.prod(lst[: i + 1]) * func(i) for i in range(len(lst))]


# 104. Function to find the absolute cumulative difference of a list with a lambda function
def absolute_cumulative_difference_lambda(lst, func):
    return [sum(lst[: i + 1]) - func(i) for i in range(len(lst))]


# 105. Function to find the absolute cumulative ratio of a list with a lambda function
def absolute_cumulative_ratio_lambda(lst, func):
    return [sum(lst[: i + 1]) / func(i) for i in range(len(lst))]


# 134. Function to check if a string is a valid email address
def is_valid_email(email):
    import re

    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))


# 135. Function to generate a list of prime numbers up to a given limit
def generate_primes(limit):
    primes = []
    for num in range(2, limit + 1):
        if all(num % i != 0 for i in range(2, int(num**0.5) + 1)):
            primes.append(num)
    return primes


# 136. Function to calculate the nth Fibonacci number using recursion
def nth_fibonacci_recursive(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return nth_fibonacci_recursive(n - 1) + nth_fibonacci_recursive(n - 2)


# 137. Function to calculate the nth Fibonacci number using iteration
def nth_fibonacci_iterative(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


# 138. Function to calculate the factorial of a number using iteration
def factorial_iterative(n):
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result


# 139. Function to calculate the factorial of a number using recursion
def factorial_recursive(n):
    if n <= 1:
        return 1
    else:
        return n * factorial_recursive(n - 1)


# 140. Function to calculate the sum of all elements in a nested list
def sum_nested_list(lst):
    total = 0
    for element in lst:
        if isinstance(element, list):
            total += sum_nested_list(element)
        else:
            total += element
    return total


# 141. Function to flatten a nested list
def flatten_nested_list(lst):
    flattened = []
    for element in lst:
        if isinstance(element, list):
            flattened.extend(flatten_nested_list(element))
        else:
            flattened.append(element)
    return flattened


# 142. Function to find the longest word in a string
def longest_word_in_string(s):
    words = s.split()
    longest = ""
    for word in words:
        if len(word) > len(longest):
            longest = word
    return longest


# 143. Function to count the frequency of each character in a string
def character_frequency(s):
    frequency = {}
    for char in s:
        if char in frequency:
            frequency[char] += 1
        else:
            frequency[char] = 1
    return frequency


# 144. Function to check if a number is a perfect square
def is_perfect_square(n):
    if n < 0:
        return False
    sqrt = int(n**0.5)
    return sqrt * sqrt == n


# 145. Function to check if a number is a perfect cube
def is_perfect_cube(n):
    if n < 0:
        return False
    cube_root = round(n ** (1 / 3))
    return cube_root**3 == n


# 146. Function to calculate the sum of squares of the first n natural numbers
def sum_of_squares(n):
    return sum(i**2 for i in range(1, n + 1))


# 147. Function to calculate the sum of cubes of the first n natural numbers
def sum_of_cubes(n):
    return sum(i**3 for i in range(1, n + 1))


# 148. Function to calculate the sum of the digits of a number
def sum_of_digits(n):
    total = 0
    while n > 0:
        total += n % 10
        n = n // 10
    return total


# 149. Function to calculate the product of the digits of a number
def product_of_digits(n):
    product = 1
    while n > 0:
        product *= n % 10
        n = n // 10
    return product


# 150. Function to reverse a number
def reverse_number(n):
    reversed_num = 0
    while n > 0:
        reversed_num = reversed_num * 10 + n % 10
        n = n // 10
    return reversed_num


# 151. Function to check if a number is a palindrome
def is_number_palindrome(n):
    return n == reverse_number(n)


# 152. Function to generate a list of all divisors of a number
def divisors(n):
    divisors = []
    for i in range(1, n + 1):
        if n % i == 0:
            divisors.append(i)
    return divisors


# 153. Function to check if a number is abundant
def is_abundant(n):
    return sum(divisors(n)) - n > n


# 154. Function to check if a number is deficient
def is_deficient(n):
    return sum(divisors(n)) - n < n


# 155. Function to check if a number is perfect
def is_perfect(n):
    return sum(divisors(n)) - n == n


# 156. Function to calculate the greatest common divisor (GCD) of two numbers
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a


# 157. Function to calculate the least common multiple (LCM) of two numbers
def lcm(a, b):
    return a * b // gcd(a, b)


# 158. Function to generate a list of the first n triangular numbers
def triangular_numbers(n):
    return [i * (i + 1) // 2 for i in range(1, n + 1)]


# 159. Function to generate a list of the first n square numbers
def square_numbers(n):
    return [i**2 for i in range(1, n + 1)]


# 160. Function to generate a list of the first n cube numbers
def cube_numbers(n):
    return [i**3 for i in range(1, n + 1)]


# 161. Function to calculate the area of a triangle given its base and height
def triangle_area(base, height):
    return 0.5 * base * height


# 162. Function to calculate the area of a trapezoid given its bases and height
def trapezoid_area(base1, base2, height):
    return 0.5 * (base1 + base2) * height


# 163. Function to calculate the area of a parallelogram given its base and height
def parallelogram_area(base, height):
    return base * height


# 164. Function to calculate the area of a rhombus given its diagonals
def rhombus_area(diagonal1, diagonal2):
    return 0.5 * diagonal1 * diagonal2


# 165. Function to calculate the area of a regular polygon given the number of sides and side length
def regular_polygon_area(n, side_length):
    import math

    return (n * side_length**2) / (4 * math.tan(math.pi / n))


# 166. Function to calculate the perimeter of a regular polygon given the number of sides and side length
def regular_polygon_perimeter(n, side_length):
    return n * side_length


# 167. Function to calculate the volume of a rectangular prism given its dimensions
def rectangular_prism_volume(length, width, height):
    return length * width * height


# 168. Function to calculate the surface area of a rectangular prism given its dimensions
def rectangular_prism_surface_area(length, width, height):
    return 2 * (length * width + width * height + height * length)


# 169. Function to calculate the volume of a pyramid given its base area and height
def pyramid_volume(base_area, height):
    return (1 / 3) * base_area * height


# 170. Function to calculate the surface area of a pyramid given its base area and slant height
def pyramid_surface_area(base_area, slant_height):
    return base_area + (1 / 2) * base_area * slant_height


# 171. Function to calculate the volume of a cone given its radius and height
def cone_volume(radius, height):
    return (1 / 3) * 3.14159 * radius**2 * height


# 172. Function to calculate the surface area of a cone given its radius and slant height
def cone_surface_area(radius, slant_height):
    return 3.14159 * radius * (radius + slant_height)


# 173. Function to calculate the volume of a sphere given its radius
def sphere_volume(radius):
    return (4 / 3) * 3.14159 * radius**3


# 174. Function to calculate the surface area of a sphere given its radius
def sphere_surface_area(radius):
    return 4 * 3.14159 * radius**2


# 175. Function to calculate the volume of a cylinder given its radius and height
def cylinder_volume(radius, height):
    return 3.14159 * radius**2 * height


# 176. Function to calculate the surface area of a cylinder given its radius and height
def cylinder_surface_area(radius, height):
    return 2 * 3.14159 * radius * (radius + height)


# 177. Function to calculate the volume of a torus given its major and minor radii
def torus_volume(major_radius, minor_radius):
    return 2 * 3.14159**2 * major_radius * minor_radius**2


# 178. Function to calculate the surface area of a torus given its major and minor radii
def torus_surface_area(major_radius, minor_radius):
    return 4 * 3.14159**2 * major_radius * minor_radius


# 179. Function to calculate the volume of an ellipsoid given its semi-axes
def ellipsoid_volume(a, b, c):
    return (4 / 3) * 3.14159 * a * b * c


# 180. Function to calculate the surface area of an ellipsoid given its semi-axes
def ellipsoid_surface_area(a, b, c):
    # Approximation for surface area of an ellipsoid
    p = 1.6075
    return 4 * 3.14159 * ((a**p * b**p + a**p * c**p + b**p * c**p) / 3) ** (1 / p)


# 181. Function to calculate the volume of a paraboloid given its radius and height
def paraboloid_volume(radius, height):
    return (1 / 2) * 3.14159 * radius**2 * height


# 182. Function to calculate the surface area of a paraboloid given its radius and height
def paraboloid_surface_area(radius, height):
    # Approximation for surface area of a paraboloid
    return (3.14159 * radius / (6 * height**2)) * (
        (radius**2 + 4 * height**2) ** (3 / 2) - radius**3
    )


# 183. Function to calculate the volume of a hyperboloid given its radii and height
def hyperboloid_volume(radius1, radius2, height):
    return (1 / 3) * 3.14159 * height * (radius1**2 + radius1 * radius2 + radius2**2)


# 184. Function to calculate the surface area of a hyperboloid given its radii and height
def hyperboloid_surface_area(radius1, radius2, height):
    # Approximation for surface area of a hyperboloid
    return 3.14159 * (radius1 + radius2) * math.sqrt((radius1 - radius2) ** 2 + height**2)


# 185. Function to calculate the volume of a tetrahedron given its edge length
def tetrahedron_volume(edge_length):
    return (edge_length**3) / (6 * math.sqrt(2))


# 186. Function to calculate the surface area of a tetrahedron given its edge length
def tetrahedron_surface_area(edge_length):
    return math.sqrt(3) * edge_length**2


# 187. Function to calculate the volume of an octahedron given its edge length
def octahedron_volume(edge_length):
    return (math.sqrt(2) / 3) * edge_length**3


if __name__ == "__main__":
    print("Math Helper Library Loaded")
