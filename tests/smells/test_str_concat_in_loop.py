from pathlib import Path
import py_compile
import textwrap
import pytest

from ecooptimizer.analyzers.analyzer_controller import AnalyzerController
from ecooptimizer.data_types.smell import SCLSmell
from ecooptimizer.refactorers.concrete.str_concat_in_loop import (
    UseListAccumulationRefactorer,
)
from ecooptimizer.utils.smell_enums import CustomSmell


@pytest.fixture
def str_concat_loop_code(source_files: Path):
    test_code = textwrap.dedent(
        """\
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
            result = str(i)
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

    def repeated_variable_reassignment():
        result = Demo()
        for i in range(2):
            result.test = result.test + "First"
            result.test = result.test + "Second"  # Multiple reassignments
        return result

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
    def simple_variable_concat(a: str, b: str):
        result = Demo().test
        for i in range(2):
            result += a + b
        return result

    def middle_var_concat():
        result = ''
        for i in range(3):
            result = str(i) + result + str(i)
        return result

    def end_var_concat():
        result = ''
        for i in range(3):
            result = str(i) + result
        return result

    def concat_referenced_in_loop():
        result = ""
        for i in range(3):
            result += "Complex" + str(i * i) + "End"  # Expression inside concatenation
            print(result)
        return result

    def concat_not_in_loop():
        name = "Bob"
        name += "Ross"
        return name
    """
    )
    file = source_files / Path("str_concat_loop_code.py")
    file.write_text(test_code)
    return file


@pytest.fixture
def get_smells(str_concat_loop_code) -> list[SCLSmell]:
    analyzer = AnalyzerController()
    smells = analyzer.run_analysis(str_concat_loop_code)

    return [smell for smell in smells if smell.messageId == CustomSmell.STR_CONCAT_IN_LOOP.value]


def test_str_concat_in_loop_detection(get_smells):
    smells: list[SCLSmell] = get_smells

    # Assert the expected number of smells
    assert len(smells) == 11

    # Verify that the detected smells correspond to the correct lines in the sample code
    expected_lines = {
        8,
        14,
        21,
        30,
        37,
        45,
        53,
        60,
        67,
        73,
        79,
    }  # Update based on actual line numbers of long lambdas
    detected_lines = {smell.occurences[0].line for smell in smells}
    assert detected_lines == expected_lines


def test_scl_refactoring(
    get_smells, str_concat_loop_code: Path, source_files: Path, output_dir: Path
):
    smells: list[SCLSmell] = get_smells

    # Instantiate the refactorer
    refactorer = UseListAccumulationRefactorer()

    # Apply refactoring to each smell
    for smell in smells:
        output_file = output_dir / f"{str_concat_loop_code.stem}_SCLR_{smell.occurences[0].line}.py"
        refactorer.refactor(str_concat_loop_code, source_files, smell, output_file, overwrite=False)
        refactorer.reset()

        assert output_file.exists()

        py_compile.compile(str(output_file), doraise=True)

    num_files = 0

    for file in output_dir.iterdir():
        if file.stem.startswith(f"{str_concat_loop_code.stem}_SCLR"):
            num_files += 1

    assert num_files == 11
