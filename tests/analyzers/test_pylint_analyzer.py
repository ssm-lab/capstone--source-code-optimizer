import ast
from pathlib import Path
import textwrap
import pytest
from ecooptimizer.analyzers.pylint_analyzer import PylintAnalyzer
from ecooptimizer.utils.analyzers_config import CustomSmell


def get_smells(code):
    analyzer = PylintAnalyzer(code, ast.parse(code))
    analyzer.analyze()
    analyzer.configure_smells()

    return analyzer.smells_data


@pytest.fixture(scope="module")
def source_files(tmp_path_factory):
    return tmp_path_factory.mktemp("input")


@pytest.fixture
def LMC_code(source_files: Path):
    lmc_code = textwrap.dedent(
        """\
    def transform_str(string):
        return string.lstrip().rstrip().lower().capitalize().split().remove("var")
    """
    )
    file = source_files / Path("lmc_code.py")
    with file.open("w") as f:
        f.write(lmc_code)

    return file


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
    """
    )
    file = source_files / Path("mim_code.py")
    with file.open("w") as f:
        f.write(mim_code)

    return file


def test_long_message_chain(LMC_code: Path):
    smells = get_smells(LMC_code)

    assert len(smells) == 1
    assert smells[0].get("symbol") == "long-message-chain"
    assert smells[0].get("messageId") == "LMC001"
    assert smells[0].get("line") == 2
    assert smells[0].get("module") == LMC_code.name


def test_member_ignoring_method(MIM_code: Path):
    smells = get_smells(MIM_code)

    assert len(smells) == 1
    assert smells[0].get("symbol") == "no-self-use"
    assert smells[0].get("messageId") == "R6301"
    assert smells[0].get("line") == 8
    assert smells[0].get("module") == MIM_code.stem


def test_long_lambda_detection():
    DIRNAME = Path(__file__).parent
    sample_code_path = (DIRNAME / Path("../tests/input/inefficient_code_example_4.py")).resolve()

    # Read the sample code
    with sample_code_path.open("r") as f:
        source_code = f.read()

    # Parse the source code into an AST
    parsed_code = ast.parse(source_code)

    # Create an instance of the PylintAnalyzer
    analyzer = PylintAnalyzer(file_path=sample_code_path, source_code=parsed_code)

    # Run the analyzer
    analyzer.analyze()

    # Filter for long lambda smells
    long_lambda_smells = [
        smell
        for smell in analyzer.smells_data
        if smell["messageId"] == CustomSmell.LONG_LAMBDA_EXPR.value
    ]

    # Assert the expected number of long lambda functions
    assert len(long_lambda_smells) == 3

    # Verify that the detected smells correspond to the correct lines in the sample code
    expected_lines = {8, 14, 20}  # Update based on actual line numbers of long lambdas
    detected_lines = {smell["line"] for smell in long_lambda_smells}
    assert detected_lines == expected_lines
