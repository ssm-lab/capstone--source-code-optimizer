import ast
from pathlib import Path
import textwrap
import pytest
from ecooptimizer.analyzers.pylint_analyzer import PylintAnalyzer


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
    lmc_code = textwrap.dedent("""\
    def transform_str(string):
        return string.lstrip().rstrip().lower().capitalize().split().remove("var")
    """)
    file = source_files / Path("lmc_code.py")
    with file.open("w") as f:
        f.write(lmc_code)

    return file


@pytest.fixture
def MIM_code(source_files: Path):
    mim_code = textwrap.dedent("""\
    class SomeClass():
        def __init__(self, string):
            self.string = string

        def print_str(self):
            print(self.string)

        def say_hello(self, name):
            print(f"Hello {name}!")
    """)
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