from pathlib import Path
import py_compile
import re
import textwrap
import pytest

from ecooptimizer.analyzers.analyzer_controller import AnalyzerController
from ecooptimizer.data_types.smell import MIMSmell
from ecooptimizer.refactorers.member_ignoring_method import MakeStaticRefactorer
from ecooptimizer.utils.smell_enums import PylintSmell


@pytest.fixture
def MIM_code(source_files) -> tuple[Path, Path]:
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
    some_class.say_hello("Mary")
    """
    )
    sample_dir = source_files / "sample_project"
    sample_dir.mkdir(exist_ok=True)
    file = source_files / sample_dir.name / Path("mim_code.py")
    with file.open("w") as f:
        f.write(mim_code)

    return sample_dir, file


@pytest.fixture(autouse=True)
def get_smells(MIM_code) -> list[MIMSmell]:
    analyzer = AnalyzerController()
    smells = analyzer.run_analysis(MIM_code[1])

    return [smell for smell in smells if smell.messageId == PylintSmell.NO_SELF_USE.value]


def test_member_ignoring_method_detection(get_smells, MIM_code):
    smells: list[MIMSmell] = get_smells

    assert len(smells) == 1
    assert smells[0].symbol == "no-self-use"
    assert smells[0].messageId == "R6301"
    assert smells[0].occurences[0].line == 9
    assert smells[0].module == MIM_code[1].stem


def test_mim_refactoring(get_smells, MIM_code, output_dir):
    smells: list[MIMSmell] = get_smells

    # Instantiate the refactorer
    refactorer = MakeStaticRefactorer()

    # Apply refactoring to each smell
    for smell in smells:
        output_file = output_dir / f"{MIM_code[1].stem}_MIMR_{smell.occurences[0].line}.py"
        refactorer.refactor(MIM_code[1], MIM_code[0], smell, output_file, overwrite=False)

        refactored_lines = output_file.read_text().splitlines()

        assert output_file.exists()

        # Check that the refactored file compiles
        py_compile.compile(str(output_file), doraise=True)

        method_line = smell.occurences[0].line - 1
        assert refactored_lines[method_line].find("@staticmethod") != -1
        assert re.search(r"(\s*\bself\b\s*)", refactored_lines[method_line + 1]) is None
