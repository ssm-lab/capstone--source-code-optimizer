# Should trigger Use A Generator code smells

def has_positive(numbers):
    # List comprehension inside `any()` - triggers R1729
    return any([num > 0 for num in numbers])

def all_non_negative(numbers):
    # List comprehension inside `all()` - triggers R1729
    return all([num >= 0 for num in numbers])

def contains_large_strings(strings):
    # List comprehension inside `any()` - triggers R1729
    return any([len(s) > 10 for s in strings])

def all_uppercase(strings):
    # List comprehension inside `all()` - triggers R1729
    return all([s.isupper() for s in strings])

def contains_special_numbers(numbers):
    # List comprehension inside `any()` - triggers R1729
    return any([num % 5 == 0 and num > 100 for num in numbers])

def all_lowercase(strings):
    # List comprehension inside `all()` - triggers R1729
    return all(s.islower() for s in strings)

def any_even_numbers(numbers):
    # List comprehension inside `any()` - triggers R1729
    return any(num % 2 == 0 for num in numbers)

def all_strings_start_with_a(strings):
    # List comprehension inside `all()` - triggers R1729
    return all(s.startswith('A') for s in strings)
