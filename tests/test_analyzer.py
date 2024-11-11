import os
import textwrap
import pytest
from ecooptimizer.analyzers.pylint_analyzer import PylintAnalyzer

@pytest.fixture(scope="module")
def source_files(tmp_path_factory):
    return tmp_path_factory.mktemp("input")

@pytest.fixture
def LMC_code(source_files):
    lmc_code = textwrap.dedent("""\
    def transform_str(string):
        return string.lstrip().rstrip().lower().capitalize().split().remove("var")
    """)
    file = os.path.join(source_files, "lmc_code.py")
    with open(file, "w") as f:
        f.write(lmc_code)

    return file

@pytest.fixture
def MIM_code(source_files):
    mim_code = textwrap.dedent("""\
    class SomeClass():
        def __init__(self, string):
            self.string = string
    
        def print_str(self):
            print(self.string)
    
        def say_hello(self, name):
            print(f"Hello {name}!")
    """)
    file = os.path.join(source_files, "mim_code.py")
    with open(file, "w") as f:
        f.write(mim_code)

    return file

def test_long_message_chain(LMC_code, logger):
    analyzer = PylintAnalyzer(LMC_code, logger)
    analyzer.analyze()
    analyzer.configure_smells()
    
    smells = analyzer.smells_data
    
    assert len(smells) == 1
    assert smells[0].get("symbol") == "long-message-chain"
    assert smells[0].get("message-id") == "LMC001"
    assert smells[0].get("line") == 2
    assert smells[0].get("module") == os.path.basename(LMC_code)

def test_member_ignoring_method(MIM_code, logger):
    analyzer = PylintAnalyzer(MIM_code, logger)
    analyzer.analyze()
    analyzer.configure_smells()
    
    smells = analyzer.smells_data
    
    assert len(smells) == 1
    assert smells[0].get("symbol") == "no-self-use"
    assert smells[0].get("message-id") == "R6301"
    assert smells[0].get("line") == 8
    assert smells[0].get("module") == os.path.splitext(os.path.basename(MIM_code))[0]

