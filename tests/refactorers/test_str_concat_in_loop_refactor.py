import pytest
from unittest.mock import patch

from pathlib import Path

from ecooptimizer.refactorers.concrete.str_concat_in_loop import UseListAccumulationRefactorer
from ecooptimizer.data_types import SCLInfo, Occurence, SCLSmell
from ecooptimizer.utils.smell_enums import CustomSmell


@pytest.fixture
def refactorer():
    return UseListAccumulationRefactorer()


def create_smell(occurences: list[int], concat_target: str, inner_loop_line: int):
    """Factory function to create a smell object"""

    def _create():
        return SCLSmell(
            path="fake.py",
            module="some_module",
            obj=None,
            type="performance",
            symbol="string-concat-loop",
            message="String concatenation inside loop detected",
            messageId=CustomSmell.STR_CONCAT_IN_LOOP.value,
            confidence="UNDEFINED",
            occurences=[
                Occurence(
                    line=occ,
                    endLine=999,
                    column=999,
                    endColumn=999,
                )
                for occ in occurences
            ],
            additionalInfo=SCLInfo(
                concatTarget=concat_target,
                innerLoopLine=inner_loop_line,
            ),
        )

    return _create


@pytest.mark.parametrize("val", [("''"), ('""'), ("str()")])
def test_empty_initial_var(refactorer, val):
    """Test for inital concat var being empty."""
    code = f"""
    def example():
        result = {val}
        for i in range(5):
            result += str(i)
        return result
    """
    smell = create_smell(occurences=[5], concat_target="result", inner_loop_line=4)()

    with (
        patch.object(Path, "read_text", return_value=code),
        patch.object(Path, "write_text") as mock_write_text,
    ):
        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))

    mock_write_text.assert_called_once()  # Ensure write_text was called once
    written_code = mock_write_text.call_args[0][0]  # The first argument is the modified code

    # Check that the modified code is correct
    assert "result = []\n" in written_code
    assert f"result = {val}\n" not in written_code

    assert "result.append(str(i))\n" in written_code

    assert "result = ''.join(result)\n" in written_code


def test_non_empty_initial_name_var_not_referenced(refactorer):
    """Test for initial concat value being none empty."""
    code = """
    def example():
        result = "Hello"
        for i in range(5):
            result += str(i)
        return result
    """
    smell = create_smell(occurences=[5], concat_target="result", inner_loop_line=4)()

    with (
        patch.object(Path, "read_text", return_value=code),
        patch.object(Path, "write_text") as mock_write_text,
    ):
        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))

    mock_write_text.assert_called_once()  # Ensure write_text was called once
    written_code = mock_write_text.call_args[0][0]  # The first argument is the modified code

    # Check that the modified code is correct
    assert "result = ['Hello']\n" in written_code
    assert 'result = "Hello"\n' not in written_code

    assert "result.append(str(i))\n" in written_code

    assert "result = ''.join(result)\n" in written_code


def test_non_empty_initial_name_var_referenced(refactorer):
    """Test for initialization when var is referenced after but before the loop start."""
    code = """
    def example():
        result = "Hello"
        backup = result
        for i in range(5):
            result += str(i)
        return result
    """
    smell = create_smell(occurences=[6], concat_target="result", inner_loop_line=5)()

    with (
        patch.object(Path, "read_text", return_value=code),
        patch.object(Path, "write_text") as mock_write_text,
    ):
        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))

    mock_write_text.assert_called_once()  # Ensure write_text was called once
    written_code = mock_write_text.call_args[0][0]  # The first argument is the modified code

    # Check that the modified code is correct
    assert 'result = "Hello"\n' in written_code
    assert "result = [result]\n" in written_code

    assert "result.append(str(i))\n" in written_code

    assert "result = ''.join(result)\n" in written_code


def test_initial_not_name_var(refactorer):
    """Test that none name vars are initialized to a temp list"""
    code = """
    def example():
        result = {"key" : "Hello"}
        for i in range(5):
            result["key"] += str(i)
        return result
    """
    smell = create_smell(occurences=[5], concat_target='result["key"]', inner_loop_line=4)()

    with (
        patch.object(Path, "read_text", return_value=code),
        patch.object(Path, "write_text") as mock_write_text,
    ):
        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))

    list_name = refactorer.generate_temp_list_name()

    mock_write_text.assert_called_once()  # Ensure write_text was called once
    written_code = mock_write_text.call_args[0][0]  # The first argument is the modified code

    # Check that the modified code is correct
    assert 'result = {"key" : "Hello"}\n' in written_code
    assert f'{list_name} = [result["key"]]\n' in written_code

    assert f"{list_name}.append(str(i))\n" in written_code

    assert f"result[\"key\"] = ''.join({list_name})\n" in written_code


def test_initial_not_in_scope(refactorer):
    """Test for refactoring of a concat variable not initialized in the same scope."""
    code = """
    def example(result: str):
        for i in range(5):
            result += str(i)
        return result
    """
    smell = create_smell(occurences=[4], concat_target="result", inner_loop_line=3)()

    with (
        patch.object(Path, "read_text", return_value=code),
        patch.object(Path, "write_text") as mock_write_text,
    ):
        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))

    mock_write_text.assert_called_once()  # Ensure write_text was called once
    written_code = mock_write_text.call_args[0][0]  # The first argument is the modified code

    # Check that the modified code is correct
    assert "result = [result]\n" in written_code

    assert "result.append(str(i))\n" in written_code

    assert "result = ''.join(result)\n" in written_code


def test_insert_on_prefix(refactorer):
    """Ensure insert(0) is used for prefix concatenation"""
    code = """
    def example():
        result = ""
        for i in range(5):
            result = str(i) + result
        return result
    """
    smell = create_smell(occurences=[5], concat_target="result", inner_loop_line=4)()

    with (
        patch.object(Path, "read_text", return_value=code),
        patch.object(Path, "write_text") as mock_write_text,
    ):
        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))

    mock_write_text.assert_called_once()  # Ensure write_text was called once
    written_code = mock_write_text.call_args[0][0]  # The first argument is the modified code

    assert "result = []\n" in written_code
    assert 'result = ""\n' not in written_code

    assert "result.insert(0, str(i))\n" in written_code

    assert "result = ''.join(result)\n" in written_code


def test_concat_with_prefix_and_suffix(refactorer):
    """Test for proper refactoring of a concatenation containing both a prefix and suffix concat."""
    code = """
    def example():
        result = ""
        for i in range(5):
            result = str(i) + result + str(i)
        return result
    """
    smell = create_smell(occurences=[5], concat_target="result", inner_loop_line=4)()

    with (
        patch.object(Path, "read_text", return_value=code),
        patch.object(Path, "write_text") as mock_write_text,
    ):
        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))

    mock_write_text.assert_called_once()  # Ensure write_text was called once
    written_code = mock_write_text.call_args[0][0]  # The first argument is the modified code

    assert "result = []\n" in written_code
    assert 'result = ""\n' not in written_code

    assert "result.insert(0, str(i))\n" in written_code
    assert "result.append(str(i))\n" in written_code

    assert "result = ''.join(result)\n" in written_code


def test_multiple_concat_occurrences(refactorer):
    """Test for multiple successive concatenations in the same loop for 1 smell."""
    code = """
    def example():
        result = ""
        fruits = ["apple", "banana", "orange", "kiwi"]
        for fruit in fruits:
            result += fruit
            result = fruit + result
        return result
    """
    smell = create_smell(occurences=[6, 7], concat_target="result", inner_loop_line=5)()

    with (
        patch.object(Path, "read_text", return_value=code),
        patch.object(Path, "write_text") as mock_write_text,
    ):
        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))

    mock_write_text.assert_called_once()  # Ensure write_text was called once
    written_code = mock_write_text.call_args[0][0]  # The first argument is the modified code

    assert "result = []\n" in written_code
    assert 'result = ""\n' not in written_code

    assert "result.append(fruit)\n" in written_code
    assert "result.insert(0, fruit)\n" in written_code

    assert "result = ''.join(result)\n" in written_code


def test_nested_concat(refactorer):
    """Test for nested concat in loop."""
    code = """
    def example():
        result = ""
        for i in range(5):
            for j in range(6):
                result = str(i) + result + str(j)
        return result
    """
    smell = create_smell(occurences=[6], concat_target="result", inner_loop_line=4)()

    with (
        patch.object(Path, "read_text", return_value=code),
        patch.object(Path, "write_text") as mock_write_text,
    ):
        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))

    mock_write_text.assert_called_once()  # Ensure write_text was called once
    written_code = mock_write_text.call_args[0][0]  # The first argument is the modified code

    assert "result = []\n" in written_code
    assert 'result = ""\n' not in written_code

    assert "result.append(str(j))\n" in written_code
    assert "result.insert(0, str(i))\n" in written_code

    assert "result = ''.join(result)\n" in written_code


def test_multi_occurrence_nested_concat(refactorer):
    """Test for multiple occurrences of a same smell at different loop levels."""
    code = """
    def example():
        result = ""
        for i in range(5):
            result += str(i)
            for j in range(6):
                result = result + str(j)
        return result
    """
    smell = create_smell(occurences=[5, 7], concat_target="result", inner_loop_line=4)()

    with (
        patch.object(Path, "read_text", return_value=code),
        patch.object(Path, "write_text") as mock_write_text,
    ):
        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))

    mock_write_text.assert_called_once()  # Ensure write_text was called once
    written_code = mock_write_text.call_args[0][0]  # The first argument is the modified code

    assert "result = []\n" in written_code
    assert 'result = ""\n' not in written_code

    assert "result.append(str(i))\n" in written_code
    assert "result.append(str(j))\n" in written_code

    assert "result = ''.join(result)\n" in written_code


def test_reassignment(refactorer):
    """Ensure list is reset to new val when reassigned inside the loop."""
    code = """
    class Test:
        def __init__(self):
            self.text = ""
    obj = Test()
    for word in ["bug", "warning", "Hello", "World"]:
        obj.text += word
        if word == "warning":
            obj.text = "Well, "
    """
    smell = create_smell(occurences=[7], concat_target="obj.text", inner_loop_line=6)()

    with (
        patch.object(Path, "read_text", return_value=code),
        patch.object(Path, "write_text") as mock_write_text,
    ):
        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))

    mock_write_text.assert_called_once()  # Ensure write_text was called once
    written_code = mock_write_text.call_args[0][0]  # The first argument is the modified code

    list_name = refactorer.generate_temp_list_name()

    assert f"{list_name} = [obj.text]\n" in written_code

    assert f"{list_name}.append(word)\n" in written_code
    assert f"{list_name} = ['Well, ']\n" in written_code  # astroid changes quotes
    assert 'obj.text = "Well, "\n' not in written_code


@pytest.mark.parametrize("val", [("''"), ('""'), ("str()")])
def test_reassignment_clears_list(refactorer, val):
    """Ensure list is cleared when reassigned inside the loop using clear()."""
    code = f"""
    class Test:
        def __init__(self):
            self.text = ""
    obj = Test()
    for word in ["bug", "warning", "Hello", "World"]:
        obj.text += word
        if word == "warning":
            obj.text = {val}
    """
    smell = create_smell(occurences=[7], concat_target="obj.text", inner_loop_line=6)()

    with (
        patch.object(Path, "read_text", return_value=code),
        patch.object(Path, "write_text") as mock_write_text,
    ):
        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))

    mock_write_text.assert_called_once()  # Ensure write_text was called once
    written_code = mock_write_text.call_args[0][0]  # The first argument is the modified code

    list_name = refactorer.generate_temp_list_name()

    assert f"{list_name} = [obj.text]\n" in written_code

    assert f"{list_name}.append(word)\n" in written_code
    assert f"{list_name}.clear()\n" in written_code


def test_no_unrelated_modifications(refactorer):
    """Ensure formatting and any comments for unrelated lines are preserved."""
    code = """
    def example():
        print("Hello World")
        # This is a comment
        result = ""
        unrelated_var = 0
        for i in range(5): # This is also a comment
            result += str(i)
            unrelated_var += i # Yep, you guessed it, comment
        return result # Another one here
    random = example() # And another one, why not
    """
    smell = create_smell(occurences=[8], concat_target="result", inner_loop_line=7)()

    with (
        patch.object(Path, "read_text", return_value=code),
        patch.object(Path, "write_text") as mock_write_text,
    ):
        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))

    mock_write_text.assert_called_once()  # Ensure write_text was called once
    written_code: str = mock_write_text.call_args[0][0]  # The first argument is the modified code

    original_lines = code.split("\n")
    modified_lines = written_code.split("\n")

    assert all(line_o == line_m for line_o, line_m in zip(original_lines[:4], modified_lines[:4]))
    assert all(line_o == line_m for line_o, line_m in zip(original_lines[5:7], modified_lines[5:7]))
    assert original_lines[8] == modified_lines[8]
    assert original_lines[9] == modified_lines[10]
    assert original_lines[10] == modified_lines[11]
