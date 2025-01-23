import ast
from pathlib import Path
import py_compile
import re
import textwrap
import pytest

from ecooptimizer.analyzers.pylint_analyzer import PylintAnalyzer
from ecooptimizer.data_wrappers.smell import MIMSmell
from ecooptimizer.refactorers.member_ignoring_method import MakeStaticRefactorer
from ecooptimizer.utils.analyzers_config import PylintSmell


@pytest.fixture
def MIM_code(source_files: Path):
    mim_code = textwrap.dedent(
        """\
    class SomeClass():

        def __init__(self, string):
            self.string = string

        def print_str(self):
            print(self.string)

        def say_hello(self, name):
            print(f"Hello {name}!")

    some_class = SomeClass("random")
    some_class.say_hello()
    """
    )
    file = source_files / Path("mim_code.py")
    with file.open("w") as f:
        f.write(mim_code)

    return file


@pytest.fixture(autouse=True)
def get_smells(MIM_code) -> list[MIMSmell]:
    analyzer = PylintAnalyzer(MIM_code, ast.parse(MIM_code.read_text()))
    analyzer.analyze()
    analyzer.configure_smells()

    return [
        smell
        for smell in analyzer.smells_data
        if smell["messageId"] == PylintSmell.NO_SELF_USE.value
    ]


def test_member_ignoring_method_detection(get_smells, MIM_code: Path):
    smells = get_smells

    # Filter for long lambda smells

    assert len(smells) == 1
    assert smells[0]["symbol"] == "no-self-use"
    assert smells[0]["messageId"] == "R6301"
    assert smells[0]["occurences"]["line"] == 9
    assert smells[0]["module"] == MIM_code.stem


def test_mim_refactoring(get_smells, MIM_code: Path, output_dir: Path):
    smells = get_smells

    # Instantiate the refactorer
    refactorer = MakeStaticRefactorer(output_dir)

    # Apply refactoring to each smell
    for smell in smells:
        refactorer.refactor(MIM_code, smell, overwrite=False)

        # Verify the refactored file exists and contains expected changes
        refactored_file = refactorer.temp_dir / Path(
            f"{MIM_code.stem}_MIMR_line_{smell['occurences']['line']}.py"
        )

        refactored_lines = refactored_file.read_text().splitlines()

        assert refactored_file.exists()

        # Check that the refactored file compiles
        py_compile.compile(str(refactored_file), doraise=True)

        method_line = smell["occurences"]["line"] - 1
        assert refactored_lines[method_line].find("@staticmethod") != -1
        assert re.search(r"(\s*\bself\b\s*)", refactored_lines[method_line + 1]) is None
