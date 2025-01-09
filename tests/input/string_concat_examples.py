class Demo:
    def __init__(self) -> None:
        self.test = ""

def concat_with_for_loop_simple_attr():
    result = Demo()
    for i in range(10):
        result.test += str(i)  # Simple concatenation
    return result

def concat_with_for_loop_simple_sub():
    result = {"key": ""}
    for i in range(10):
        result["key"] += str(i)  # Simple concatenation
    return result

def concat_with_for_loop_simple():
    result = ""
    for i in range(10):
        result += str(i)  # Simple concatenation
    return result

def concat_with_while_loop_variable_append():
    result = ""
    i = 0
    while i < 5:
        result += f"Value-{i}"  # Using f-string inside while loop
        i += 1
    return result

def nested_loop_string_concat():
    result = ""
    for i in range(2):
        for j in range(3):
            result += f"({i},{j})"  # Nested loop concatenation
    return result

def string_concat_with_condition():
    result = ""
    for i in range(5):
        if i % 2 == 0:
            result += "Even"  # Conditional concatenation
        else:
            result += "Odd"   # Different condition
    return result

def concatenate_with_literal():
    result = "Start"
    for i in range(4):
        result += "-Next"  # Concatenating a literal string
    return result

def complex_expression_concat():
    result = ""
    for i in range(3):
        result += "Complex" + str(i * i) + "End"  # Expression inside concatenation
    return result

def repeated_variable_reassignment():
    result = Demo()
    for i in range(2):
        result.test = result.test + "First"
        result.test = result.test + "Second"  # Multiple reassignments
    return result

# Concatenation with % operator using only variables
def greet_user_with_percent(name):
    greeting = ""
    for i in range(2):
        greeting += "Hello, " + "%s" % name
    return greeting

# Concatenation with str.format() using only variables
def describe_city_with_format(city):
    description = ""
    for i in range(2):
        description = description + "I live in " + "the city of {}".format(city)
    return description

# Nested interpolation with % and concatenation
def person_description_with_percent(name, age):
    description = ""
    for i in range(2):
        description += "Person: " + "%s, Age: %d" % (name, age)
    return description

# Multiple str.format() calls with concatenation
def values_with_format(x, y):
    result = ""
    for i in range(2):
        result = result + "Value of x: {}".format(x) + ", and y: {:.2f}".format(y)
    return result

# Simple variable concatenation (edge case for completeness)
def simple_variable_concat(a, b):
    result = Demo().test
    for i in range(2):
        result += a + b
    return result