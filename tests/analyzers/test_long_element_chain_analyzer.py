import ast
from pathlib import Path
import textwrap
import pytest

from ecooptimizer.analyzers.ast_analyzers.detect_long_element_chain import detect_long_element_chain
from ecooptimizer.data_types.smell import LECSmell


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""
    file_path = tmp_path / "test_code.py"
    return file_path


def parse_code(code_str):
    """Parse code string into an AST."""
    return ast.parse(code_str)


def test_no_chains(temp_file):
    """Test with code that has no chains."""
    code = textwrap.dedent("""
        a = 1
        b = 2
        c = a + b
        d = {'key': 'value'}
        e = d['key']
    """)

    with Path.open(temp_file, "w") as f:
        f.write(code)

    tree = parse_code(code)
    result = detect_long_element_chain(temp_file, tree)

    assert len(result) == 0


def test_chains_below_threshold(temp_file):
    """Test with chains shorter than threshold."""
    code = textwrap.dedent("""
        a = {'key1': {'key2': 'value'}}
        b = a['key1']['key2']
    """)

    with Path.open(temp_file, "w") as f:
        f.write(code)

    tree = parse_code(code)
    # Using threshold of 5
    result = detect_long_element_chain(temp_file, tree, 5)

    assert len(result) == 0


def test_chains_at_threshold(temp_file):
    """Test with chains exactly at threshold."""
    code = textwrap.dedent("""
        a = {'key1': {'key2': {'key3': 'value'}}}
        b = a['key1']['key2']['key3']
    """)

    with Path.open(temp_file, "w") as f:
        f.write(code)

    tree = parse_code(code)
    # Using threshold of 3
    result = detect_long_element_chain(temp_file, tree, 3)

    assert len(result) == 1
    assert result[0].messageId == "LEC001"
    assert result[0].symbol == "long-element-chain"
    assert result[0].occurences[0].line == 3  # Line 3 in the code


def test_chains_above_threshold(temp_file):
    """Test with chains longer than threshold."""
    code = textwrap.dedent("""
        data = {'a': {'b': {'c': {'d': 'value'}}}}
        result = data['a']['b']['c']['d']
    """)

    with Path.open(temp_file, "w") as f:
        f.write(code)

    tree = parse_code(code)
    # Using threshold of 3
    result = detect_long_element_chain(temp_file, tree, 3)

    assert len(result) == 1
    assert "Dictionary chain too long (4/3)" in result[0].message


def test_multiple_chains(temp_file):
    """Test with multiple chains in the same file."""
    code = textwrap.dedent("""
        data1 = {'a': {'b': {'c': 'value1'}}}
        data2 = {'x': {'y': {'z': 'value2'}}}

        result1 = data1['a']['b']['c']
        result2 = data2['x']['y']['z']

        # Some other code without chains
        a = 1
        b = 2
    """)

    with Path.open(temp_file, "w") as f:
        f.write(code)

    tree = parse_code(code)
    result = detect_long_element_chain(temp_file, tree, 3)

    assert len(result) == 2
    assert result[0].occurences[0].line != result[1].occurences[0].line


def test_nested_functions_with_chains(temp_file):
    """Test chains inside nested functions and classes."""
    code = textwrap.dedent("""
        def outer_function():
            data = {'a': {'b': {'c': 'value'}}}

            def inner_function():
                return data['a']['b']['c']

            return inner_function()

        class TestClass:
            def method(self):
                obj = {'x': {'y': {'z': {'deep': 'nested'}}}}
                return obj['x']['y']['z']['deep']
    """)

    with Path.open(temp_file, "w") as f:
        f.write(code)

    tree = parse_code(code)
    result = detect_long_element_chain(temp_file, tree, 3)

    assert len(result) == 2
    # Check that we detected the chain in both locations


def test_same_line_reported_once(temp_file):
    """Test that chains on the same line are reported only once."""
    code = textwrap.dedent("""
        data = {'a': {'b': {'c': 'value1'}}}
        # Two identical chains on the same line
        result1, result2 = data['a']['b']['c'], data['a']['b']['c']
    """)

    with Path.open(temp_file, "w") as f:
        f.write(code)

    tree = parse_code(code)
    result = detect_long_element_chain(temp_file, tree, 2)

    assert len(result) == 1

    assert result[0].occurences[0].line == 4


def test_variable_types_chains(temp_file):
    """Test chains with different variable types."""
    code = textwrap.dedent("""
        # List within dict chain
        data1 = {'a': [{'b': {'c': 'value'}}]}
        result1 = data1['a'][0]['b']['c']

        # Tuple with dict chain
        data2 = {'x': ({'y': {'z': 'value'}},)}
        result2 = data2['x'][0]['y']['z']
    """)

    with Path.open(temp_file, "w") as f:
        f.write(code)

    tree = parse_code(code)
    result = detect_long_element_chain(temp_file, tree, 3)

    assert len(result) == 2


def test_custom_threshold(temp_file):
    """Test with a custom threshold value."""
    code = textwrap.dedent("""
        data = {'a': {'b': {'c': 'value'}}}
        result = data['a']['b']['c']
    """)

    with Path.open(temp_file, "w") as f:
        f.write(code)

    tree = parse_code(code)

    # With threshold of 4, no chains should be detected
    result1 = detect_long_element_chain(temp_file, tree, 4)
    assert len(result1) == 0

    # With threshold of 2, the chain should be detected
    result2 = detect_long_element_chain(temp_file, tree, 2)
    assert len(result2) == 1
    assert "Dictionary chain too long (3/2)" in result2[0].message


def test_result_structure(temp_file):
    """Test the structure of the returned LECSmell object."""
    code = textwrap.dedent("""
        data = {'a': {'b': {'c': 'value'}}}
        result = data['a']['b']['c']
    """)

    with Path.open(temp_file, "w") as f:
        f.write(code)

    tree = parse_code(code)
    result = detect_long_element_chain(temp_file, tree, 3)

    assert len(result) == 1
    smell = result[0]

    # Verify it's the correct type
    assert isinstance(smell, LECSmell)

    # Check required fields
    assert smell.path == str(temp_file)
    assert smell.module == temp_file.stem
    assert smell.type == "convention"
    assert smell.symbol == "long-element-chain"
    assert "Dictionary chain too long" in smell.message

    # Check occurrence details
    assert len(smell.occurences) == 1
    assert smell.occurences[0].line == 3
    assert smell.occurences[0].column is not None
    assert smell.occurences[0].endLine is not None
    assert smell.occurences[0].endColumn is not None

    # Verify additional info exists
    assert hasattr(smell, "additionalInfo")


def test_complex_expressions(temp_file):
    """Test chains within complex expressions."""
    code = textwrap.dedent("""
        data = {'a': {'b': {'c': 5}}}

        # Chain in an arithmetic expression
        result1 = data['a']['b']['c'] + 10

        # Chain in a function call
        def my_func(x):
            return x * 2

        result2 = my_func(data['a']['b']['c'])

        # Chain in a comprehension
        result3 = [i * data['a']['b']['c'] for i in range(5)]
    """)

    with Path.open(temp_file, "w") as f:
        f.write(code)

    tree = parse_code(code)
    result = detect_long_element_chain(temp_file, tree, 3)

    assert len(result) == 3  # Should detect all three chains


def test_edge_case_empty_file(temp_file):
    """Test with an empty file."""
    code = ""

    with Path.open(temp_file, "w") as f:
        f.write(code)

    tree = parse_code(code)
    result = detect_long_element_chain(temp_file, tree)

    assert len(result) == 0


def test_edge_case_threshold_one(temp_file):
    """Test with threshold of 1 (every subscript would be reported)."""
    code = textwrap.dedent("""
        data1 = {'a': [{'b': {'c': {'d': 'value'}}}]}
        result1 = data1['a'][0]['b']['c']['d']
    """)

    with Path.open(temp_file, "w") as f:
        f.write(code)

    tree = parse_code(code)
    result = detect_long_element_chain(temp_file, tree, 5)

    assert len(result) == 1
    assert "Dictionary chain too long (5/5)" in result[0].message
