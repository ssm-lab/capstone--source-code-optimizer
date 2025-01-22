from pathlib import Path
import ast
from ecooptimizer.analyzers.pylint_analyzer import PylintAnalyzer
from ecooptimizer.refactorers.long_parameter_list import LongParameterListRefactorer
from ecooptimizer.utils.analyzers_config import PylintSmell

TEST_INPUT_FILE = Path("../input/long_param.py")


def get_smells(code: Path):
    analyzer = PylintAnalyzer(code, ast.parse(code.read_text()))
    analyzer.analyze()
    analyzer.configure_smells()
    return analyzer.smells_data


def test_long_param_list_detection():
    smells = get_smells(TEST_INPUT_FILE)

    # filter out long lambda smells from all calls
    long_param_list_smells = [
        smell for smell in smells if smell["messageId"] == PylintSmell.LONG_PARAMETER_LIST.value
    ]

    # assert expected number of long lambda functions
    assert len(long_param_list_smells) == 11

    # ensure that detected smells correspond to correct line numbers in test input file
    expected_lines = {26, 38, 50, 77, 88, 99, 126, 140, 183, 196, 209}
    detected_lines = {smell["occurences"][0]["line"] for smell in long_param_list_smells}
    assert detected_lines == expected_lines


def test_long_parameter_refactoring(output_dir):
    smells = get_smells(TEST_INPUT_FILE)

    long_param_list_smells = [
        smell for smell in smells if smell["messageId"] == PylintSmell.LONG_PARAMETER_LIST.value
    ]

    refactorer = LongParameterListRefactorer(output_dir)

    for smell in long_param_list_smells:
        refactorer.refactor(TEST_INPUT_FILE, smell)

        refactored_file = refactorer.temp_dir / Path(
            f"{TEST_INPUT_FILE.stem}_LPLR_line_{smell['occurences'][0]['line']}.py"
        )

        assert refactored_file.exists()
