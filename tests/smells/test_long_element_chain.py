import logging
from pathlib import Path
import py_compile
import textwrap
import pytest

from ecooptimizer.analyzers.analyzer_controller import AnalyzerController
from ecooptimizer.config import CONFIG
from ecooptimizer.data_types.smell import LECSmell
from ecooptimizer.refactorers.concrete.long_element_chain import LongElementChainRefactorer
from ecooptimizer.utils.smell_enums import CustomSmell


# Reuse existing logging fixtures
@pytest.fixture(autouse=True)
def _dummy_logger_detect():
    dummy = logging.getLogger("dummy")
    dummy.addHandler(logging.NullHandler())
    CONFIG["detectLogger"] = dummy
    yield
    CONFIG["detectLogger"] = None


@pytest.fixture(autouse=True)
def _dummy_logger_refactor():
    dummy = logging.getLogger("dummy")
    dummy.addHandler(logging.NullHandler())
    CONFIG["refactorLogger"] = dummy
    yield
    CONFIG["refactorLogger"] = None


@pytest.fixture
def LEC_code(source_files) -> tuple[Path, Path]:
    lec_code = textwrap.dedent("""\
    def access_nested_dict():
        nested_dict1 = {
            "level1": {
                "level2": {
                    "level3": {
                        "key": "value"
                    }
                }
            }
        }

        nested_dict2 = {
            "level1": {
                "level2": {
                    "level3": {
                        "key": "value",
                        "key2": "value2"
                    },
                    "level3a": {
                        "key": "value"
                    }
                }
            }
        }
        print(nested_dict1["level1"]["level2"]["level3"]["key"])
        print(nested_dict2["level1"]["level2"]["level3"]["key2"])
        print(nested_dict2["level1"]["level2"]["level3"]["key"])
        print(nested_dict2["level1"]["level2"]["level3a"]["key"])
        print(nested_dict1["level1"]["level2"]["level3"]["key"])
    """)
    sample_dir = source_files / "lec_project"
    sample_dir.mkdir(exist_ok=True)
    file_path = sample_dir / "lec_code.py"
    file_path.write_text(lec_code)
    return sample_dir, file_path


@pytest.fixture
def LEC_multifile_project(source_files) -> tuple[Path, list[Path]]:
    project_dir = source_files / "lec_multifile"
    project_dir.mkdir(exist_ok=True)

    # Data definition file
    data_def = textwrap.dedent("""\
    nested_dict = {
        "level1": {
            "level2": {
                "level3": {
                    "key": "deep_value"
                }
            }
        }
    }
    print(nested_dict["level1"]["level2"]["level3"]["key"])
    """)
    data_file = project_dir / "data_def.py"
    data_file.write_text(data_def)

    # Data usage file
    data_usage = textwrap.dedent("""\
    from .data_def import nested_dict

    def get_value():
        return nested_dict["level1"]["level2"]["level3"]["key"]
    """)
    usage_file = project_dir / "data_usage.py"
    usage_file.write_text(data_usage)

    return project_dir, [data_file, usage_file]


@pytest.fixture(autouse=True)
def get_smells(LEC_code) -> list[LECSmell]:
    analyzer = AnalyzerController()
    smells = analyzer.run_analysis(LEC_code[1])
    return [s for s in smells if isinstance(s, LECSmell)]


@pytest.fixture(autouse=True)
def get_multifile_smells(LEC_multifile_project) -> list[LECSmell]:
    analyzer = AnalyzerController()
    all_smells = []
    for file in LEC_multifile_project[1]:
        smells = analyzer.run_analysis(file)
        all_smells.extend([s for s in smells if isinstance(s, LECSmell)])
    return all_smells


def test_lec_detection_single_file(get_smells):
    """Test detection in a single file with multiple nested accesses"""
    smells = get_smells
    # Filter for long lambda smells
    lec_smells: list[LECSmell] = [
        smell for smell in smells if smell.messageId == CustomSmell.LONG_ELEMENT_CHAIN.value
    ]
    # Verify we detected all 5 access points
    assert len(lec_smells) == 5  # Single smell with multiple occurrences
    assert lec_smells[0].messageId == "LEC001"

    # Verify occurrence locations (lines 22-26 in the sample code)
    occurrences = lec_smells[0].occurences
    assert len(occurrences) == 1
    expected_lines = [25, 26, 27, 28, 29]
    for occ, line in zip(occurrences, expected_lines):
        assert occ.line == line
    assert lec_smells[0].module == "lec_code"


def test_lec_detection_multifile(get_multifile_smells, LEC_multifile_project):
    """Test detection across multiple files"""
    smells = get_multifile_smells
    _, files = LEC_multifile_project

    # Should detect 1 smell in the both file
    assert len(smells) == 2

    # Verify the smell is in the usage file
    usage_file = files[1]
    data_file = files[0]
    data_smell = smells[0]
    usage_smell = smells[1]

    assert str(data_smell.path) == str(data_file)
    assert str(usage_smell.path) == str(usage_file)

    assert data_smell.occurences[0].line == 10  # Line with deep access
    assert usage_smell.occurences[0].line == 4  # Line with deep access

    assert data_smell.messageId == "LEC001"
    assert usage_smell.messageId == "LEC001"


def test_lec_multifile_refactoring(get_multifile_smells, LEC_multifile_project, output_dir):
    smells: list[LECSmell] = get_multifile_smells
    refactorer = LongElementChainRefactorer()
    project_dir, files = LEC_multifile_project

    # Process each smell
    for i, smell in enumerate(smells):
        output_file = output_dir / f"refactored_{i}.py"
        refactorer.refactor(
            Path(smell.path),  # Should be implemented in your LECSmell
            project_dir,
            smell,
            output_file,
            overwrite=False,
        )

    # Verify definitions file
    refactored_data = output_dir / "refactored_0.py"
    data_content = refactored_data.read_text()

    # Check flattened dictionary structure
    assert "'level1_level2_level3_key': 'value'" in data_content
    assert "'level1_level2_level3_key2': 'value2'" in data_content
    assert "'level1_level2_level3a_key': 'value'" in data_content

    # Verify usage file
    refactored_usage = output_dir / "refactored_1.py"
    usage_content = refactored_usage.read_text()

    # Check all access points were updated
    assert "nested_dict1['level1_level2_level3_key']" in usage_content
    assert "nested_dict2['level1_level2_level3_key2']" in usage_content
    assert "nested_dict2['level1_level2_level3_key']" in usage_content
    assert "nested_dict2['level1_level2_level3a_key']" in usage_content

    # Verify compilation
    for f in [refactored_data, refactored_usage]:
        py_compile.compile(str(f), doraise=True)
