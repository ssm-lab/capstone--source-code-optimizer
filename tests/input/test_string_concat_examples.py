import pytest
from .string_concat_examples import (
    concat_with_for_loop_simple,
    complex_expression_concat,
    concat_with_for_loop_simple_attr,
    concat_with_for_loop_simple_sub,
    concat_with_while_loop_variable_append,
    concatenate_with_literal,
    simple_variable_concat,
    string_concat_with_condition,
    nested_loop_string_concat,
    repeated_variable_reassignment,
    greet_user_with_percent,
    describe_city_with_format,
    person_description_with_percent,
    values_with_format,
    middle_var_concat,
    end_var_concat
)

def test_concat_with_for_loop_simple_attr():
    result = concat_with_for_loop_simple_attr()
    assert result.test == ''.join(str(i) for i in range(10))

def test_concat_with_for_loop_simple_sub():
    result = concat_with_for_loop_simple_sub()
    assert result["key"] == ''.join(str(i) for i in range(10))

def test_concat_with_for_loop_simple():
    result = concat_with_for_loop_simple()
    assert result == ''.join(str(i) for i in range(10))

def test_concat_with_while_loop_variable_append():
    result = concat_with_while_loop_variable_append()
    assert result == ''.join(f"Value-{i}" for i in range(5))

def test_nested_loop_string_concat():
    result = nested_loop_string_concat()
    expected = ''.join(f"({i},{j})" for i in range(2) for j in range(3))
    assert result == expected

def test_string_concat_with_condition():
    result = string_concat_with_condition()
    expected = ''.join("Even" if i % 2 == 0 else "Odd" for i in range(5))
    assert result == expected

def test_concatenate_with_literal():
    result = concatenate_with_literal()
    assert result == "Start" + "-Next" * 4

def test_complex_expression_concat():
    result = complex_expression_concat()
    expected = ''.join(f"Complex{i*i}End" for i in range(3))
    assert result == expected

def test_repeated_variable_reassignment():
    result = repeated_variable_reassignment()
    assert result.test == ("FirstSecond" * 2)

def test_greet_user_with_percent():
    result = greet_user_with_percent("Alice")
    assert result == ("Hello, Alice" * 2)

def test_describe_city_with_format():
    result = describe_city_with_format("London")
    assert result == ("I live in the city of London" * 2)

def test_person_description_with_percent():
    result = person_description_with_percent("Bob", 25)
    assert result == ("Person: Bob, Age: 25" * 2)

def test_values_with_format():
    result = values_with_format(42, 3.14)
    assert result == ("Value of x: 42, and y: 3.14" * 2)

def test_simple_variable_concat():
    result = simple_variable_concat("foo", "bar")
    assert result == ("foobar" * 2)

def test_end_var_concat():
    result = end_var_concat()
    assert result == ("210")

def test_middle_var_concat():
    result = middle_var_concat()
    assert result == ("210012")
