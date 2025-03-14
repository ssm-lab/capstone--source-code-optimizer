from pathlib import Path
from astroid import parse
from unittest.mock import patch

from ecooptimizer.data_types.smell import SCLSmell
from ecooptimizer.analyzers.astroid_analyzers.detect_string_concat_in_loop import (
    detect_string_concat_in_loop,
)

# === Basic Concatenation Cases ===


def test_detects_simple_for_loop_concat():
    """Detects += string concatenation inside a for loop."""
    code = """
    def test():
        result = ""
        for i in range(10):
            result += str(i)
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 1
    assert isinstance(smells[0], SCLSmell)

    assert len(smells[0].occurences) == 1
    assert smells[0].additionalInfo.concatTarget == "result"
    assert smells[0].additionalInfo.innerLoopLine == 4


def test_detects_simple_assign_loop_concat():
    """Detects <var = var + ...> string concatenation inside a loop."""
    code = """
    def test():
        result = ""
        for i in range(10):
            result = result + str(i)
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 1
    assert isinstance(smells[0], SCLSmell)

    assert len(smells[0].occurences) == 1
    assert smells[0].additionalInfo.concatTarget == "result"
    assert smells[0].additionalInfo.innerLoopLine == 4


def test_detects_simple_while_loop_concat():
    """Detects += string concatenation inside a while loop."""
    code = """
    def test():
        result = ""
        while i < 10:
            result += str(i)
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 1
    assert isinstance(smells[0], SCLSmell)

    assert len(smells[0].occurences) == 1
    assert smells[0].additionalInfo.concatTarget == "result"
    assert smells[0].additionalInfo.innerLoopLine == 4


def test_detects_list_attribute_concat():
    """Detects += modifying a list item inside a loop."""
    code = """
    class Test:
        def __init__(self):
            self.text = [""] * 5
        def update(self):
            for i in range(5):
                self.text[0] += str(i)
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 1
    assert isinstance(smells[0], SCLSmell)

    assert len(smells[0].occurences) == 1
    assert smells[0].additionalInfo.concatTarget == "self.text[0]"
    assert smells[0].additionalInfo.innerLoopLine == 6


def test_detects_object_attribute_concat():
    """Detects += modifying an object attribute inside a loop."""
    code = """
    class Test:
        def __init__(self):
            self.text = ""
        def update(self):
            for i in range(5):
                self.text += str(i)
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 1
    assert isinstance(smells[0], SCLSmell)

    assert len(smells[0].occurences) == 1
    assert smells[0].additionalInfo.concatTarget == "self.text"
    assert smells[0].additionalInfo.innerLoopLine == 6


def test_detects_dict_value_concat():
    """Detects += modifying a dictionary value inside a loop."""
    code = """
    def test():
        data = {"key": ""}
        for i in range(5):
            data["key"] += str(i)
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 1
    assert isinstance(smells[0], SCLSmell)

    assert len(smells[0].occurences) == 1
    # astroid changes double quotes to singles
    assert smells[0].additionalInfo.concatTarget == "data['key']"
    assert smells[0].additionalInfo.innerLoopLine == 4


def test_detects_multi_loop_concat():
    """Detects multiple separate string concats in a loop."""
    code = """
    def test():
        result = ""
        logs = [""] * 4
        for i in range(10):
            result += str(i)
            logs[0] += str(i)
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 2
    assert all(isinstance(smell, SCLSmell) for smell in smells)

    assert len(smells[0].occurences) == 1
    assert smells[0].additionalInfo.concatTarget == "result"
    assert smells[0].additionalInfo.innerLoopLine == 5

    assert len(smells[1].occurences) == 1
    assert smells[1].additionalInfo.concatTarget == "logs[0]"
    assert smells[1].additionalInfo.innerLoopLine == 5


def test_detects_reset_loop_concat():
    """Detects string concats with re-assignments inside the loop."""
    code = """
    def reset():
        result = ''
        for i in range(5):
            result += "Iteration: " + str(i)
            if i == 2:
                result = ""  # Resetting `result`
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 1
    assert isinstance(smells[0], SCLSmell)

    assert len(smells[0].occurences) == 1
    assert smells[0].additionalInfo.concatTarget == "result"
    assert smells[0].additionalInfo.innerLoopLine == 4


# === Nested Loop Cases ===


def test_detects_nested_loop_concat():
    """Detects concatenation inside nested loops."""
    code = """
    def test():
        result = ""
        for i in range(3):
            for j in range(3):
                result += str(j)
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 1
    assert isinstance(smells[0], SCLSmell)

    assert len(smells[0].occurences) == 1
    assert smells[0].additionalInfo.concatTarget == "result"
    assert smells[0].additionalInfo.innerLoopLine == 5


def test_detects_complex_nested_loop_concat():
    """Detects multi level concatenations belonging to the same smell."""
    code = """
    def super_complex():
        result = ''
        for i in range(5):
            result += "Iteration: " + str(i)
            for j in range(3):
                result += "Nested: " + str(j)  # Contributing to `result`
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 1
    assert isinstance(smells[0], SCLSmell)

    assert len(smells[0].occurences) == 2
    assert smells[0].additionalInfo.concatTarget == "result"
    assert smells[0].additionalInfo.innerLoopLine == 4


# === Conditional Cases ===


def test_detects_if_else_concat():
    """Detects += inside an if-else condition within a loop."""
    code = """
    def test():
        result = ""
        for i in range(5):
            if i % 2 == 0:
                result += "even"
            else:
                result += "odd"
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 1
    assert isinstance(smells[0], SCLSmell)

    assert len(smells[0].occurences) == 2
    assert smells[0].additionalInfo.concatTarget == "result"
    assert smells[0].additionalInfo.innerLoopLine == 4


# === String Interpolation Cases ===


def test_detects_f_string_concat():
    """Detects += using f-strings inside a loop."""
    code = """
    def test():
        result = ""
        for i in range(5):
            result += f"{i}"
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 1
    assert isinstance(smells[0], SCLSmell)

    assert len(smells[0].occurences) == 1
    assert smells[0].additionalInfo.concatTarget == "result"
    assert smells[0].additionalInfo.innerLoopLine == 4


def test_detects_percent_format_concat():
    """Detects += using % formatting inside a loop."""
    code = """
    def test():
        result = ""
        for i in range(5):
            result += "%d" % i
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 1
    assert isinstance(smells[0], SCLSmell)

    assert len(smells[0].occurences) == 1
    assert smells[0].additionalInfo.concatTarget == "result"
    assert smells[0].additionalInfo.innerLoopLine == 4


def test_detects_str_format_concat():
    """Detects += using .format() inside a loop."""
    code = """
    def test():
        result = ""
        for i in range(5):
            result += "{}".format(i)
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 1
    assert isinstance(smells[0], SCLSmell)

    assert len(smells[0].occurences) == 1
    assert smells[0].additionalInfo.concatTarget == "result"
    assert smells[0].additionalInfo.innerLoopLine == 4


# === False Positives (Should NOT Detect) ===


def test_ignores_access_inside_loop():
    """Ensures that accessing the concatenation variable inside the loop is NOT flagged."""
    code = """
    def test():
        result = ""
        for i in range(5):
            print(result)  # Accessing result mid-loop
            result += str(i)
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 0


def test_ignores_regular_str_assign_inside_loop():
    """Ensures that regular string assignments are NOT flagged."""
    code = """
    def test():
        result = ""
        for i in range(5):
            result = str(i)
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 0


def test_ignores_number_addition_inside_loop():
    """Ensures number operations with the += format are NOT flagged."""
    code = """
    def test():
        num = 1
        for i in range(5):
            num += i
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 0


def test_ignores_concat_outside_loop():
    """Ensures that string concatenation OUTSIDE a loop is NOT flagged."""
    code = """
    def test():
        result = ""
        part1 = "Hello"
        part2 = "World"
        result = result + part1 + part2
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 0


# === Edge Cases ===


def test_detects_sequential_concat():
    """Detects a variable concatenated multiple times in the same loop iteration."""
    code = """
    def test():
        result = ""
        for i in range(5):
            result += str(i)
            result += "-"
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 1
    assert isinstance(smells[0], SCLSmell)

    assert len(smells[0].occurences) == 2
    assert smells[0].additionalInfo.concatTarget == "result"
    assert smells[0].additionalInfo.innerLoopLine == 4


def test_detects_concat_with_prefix_and_suffix():
    """Detects concatenation where both prefix and suffix are added."""
    code = """
    def test():
        result = ""
        for i in range(5):
            result = "prefix-" + result + "-suffix"
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 1
    assert isinstance(smells[0], SCLSmell)

    assert len(smells[0].occurences) == 1
    assert smells[0].additionalInfo.concatTarget == "result"
    assert smells[0].additionalInfo.innerLoopLine == 4


def test_detects_prepend_concat():
    """Detects += where new values are inserted at the beginning instead of the end."""
    code = """
    def test():
        result = ""
        for i in range(5):
            result = str(i) + result
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 1
    assert isinstance(smells[0], SCLSmell)

    assert len(smells[0].occurences) == 1
    assert smells[0].additionalInfo.concatTarget == "result"
    assert smells[0].additionalInfo.innerLoopLine == 4


# === Typing Cases ===


def test_ignores_unknown_type():
    """Ignores potential smells where type cannot be confirmed as a string."""
    code = """
    def test(a, b):
        result = a
        for i in range(5):
            result = result + b

    a = "Hello"
    b = "world"
    test(a)
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 0


def test_detects_param_type_hint_concat():
    """Detects string concat where type is inferrred from the FunctionDef type hints."""
    code = """
    def test(a: str, b: str):
        result = a
        for i in range(5):
            result = result + b

    a = "Hello"
    b = "world"
    test(a, b)
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 1
    assert isinstance(smells[0], SCLSmell)

    assert len(smells[0].occurences) == 1
    assert smells[0].additionalInfo.concatTarget == "result"
    assert smells[0].additionalInfo.innerLoopLine == 4


def test_detects_var_type_hint_concat():
    """Detects string concats where the type is inferred from an assign type hint."""
    code = """
    def test(a, b):
        result: str = a
        for i in range(5):
            result = result + b

    a = "Hello"
    b = "world"
    test(a, b)
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 1
    assert isinstance(smells[0], SCLSmell)

    assert len(smells[0].occurences) == 1
    assert smells[0].additionalInfo.concatTarget == "result"
    assert smells[0].additionalInfo.innerLoopLine == 4


def test_detects_cls_attr_type_hint_concat():
    """Detects string concats where type is inferred from class attributes."""
    code = """
    class Test:

        def __init__(self):
            self.text = "word"

        def test(self, a):
            result = a
            for i in range(5):
                result = result + self.text

    a = Test()
    a.test("this ")
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 1
    assert isinstance(smells[0], SCLSmell)

    assert len(smells[0].occurences) == 1
    assert smells[0].additionalInfo.concatTarget == "result"
    assert smells[0].additionalInfo.innerLoopLine == 9


def test_detects_inferred_str_type_concat():
    """Detects string concat where type is inferred from the initial value assigned."""
    code = """
    def test(a):
        result = ""
        for i in range(5):
            result = a + result

    a = "hello"
    test(a)
    """
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_string_concat_in_loop(Path("fake.py"), parse(code))

    assert len(smells) == 1
    assert isinstance(smells[0], SCLSmell)

    assert len(smells[0].occurences) == 1
    assert smells[0].additionalInfo.concatTarget == "result"
    assert smells[0].additionalInfo.innerLoopLine == 4
