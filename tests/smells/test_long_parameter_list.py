import pytest
from pathlib import Path

from ecooptimizer.analyzers.analyzer_controller import AnalyzerController
from ecooptimizer.data_types.smell import LPLSmell
from ecooptimizer.refactorers.long_parameter_list import LongParameterListRefactorer
from ecooptimizer.utils.smell_enums import PylintSmell

TEST_INPUT_FILE = (Path(__file__).parent / "../input/long_param.py").resolve()


@pytest.fixture(autouse=True)
def get_smells():
    analyzer = AnalyzerController()

    return analyzer.run_analysis(TEST_INPUT_FILE)


def test_long_param_list_detection(get_smells):
    smells = get_smells

    # filter out long lambda smells from all calls
    long_param_list_smells: list[LPLSmell] = [
        smell for smell in smells if smell.messageId == PylintSmell.LONG_PARAMETER_LIST.value
    ]

    # assert expected number of long lambda functions
    assert len(long_param_list_smells) == 11

    # ensure that detected smells correspond to correct line numbers in test input file
    expected_lines = {26, 38, 50, 77, 88, 99, 126, 140, 183, 196, 209}
    detected_lines = {smell.occurences[0].line for smell in long_param_list_smells}
    assert detected_lines == expected_lines


def test_long_parameter_refactoring(get_smells, output_dir, source_files):
    smells = get_smells

    long_param_list_smells: list[LPLSmell] = [
        smell for smell in smells if smell.messageId == PylintSmell.LONG_PARAMETER_LIST.value
    ]

    refactorer = LongParameterListRefactorer()

    for smell in long_param_list_smells:
        output_file = output_dir / f"{TEST_INPUT_FILE.stem}_LPLR_{smell.occurences[0].line}.py"
        refactorer.refactor(TEST_INPUT_FILE, source_files, smell, output_file, overwrite=False)

        assert output_file.exists()
