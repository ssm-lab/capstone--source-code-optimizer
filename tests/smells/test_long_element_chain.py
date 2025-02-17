import ast
from pathlib import Path
import textwrap
import pytest
from ecooptimizer.analyzers.analyzer_controller import AnalyzerController
from ecooptimizer.data_types.smell import LECSmell
from ecooptimizer.refactorers.concrete.long_element_chain import (
    LongElementChainRefactorer,
)
from ecooptimizer.utils.smell_enums import CustomSmell


@pytest.fixture
def refactorer():
    return LongElementChainRefactorer()


@pytest.fixture
def nested_dict_code(source_files: Path):
    test_code = textwrap.dedent(
        """\
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
    """
    )
    file = source_files / Path("nested_dict_code.py")
    with file.open("w") as f:
        f.write(test_code)
    return file


@pytest.fixture(autouse=True)
def get_smells(nested_dict_code: Path):
    analyzer = AnalyzerController()
    smells = analyzer.run_analysis(nested_dict_code)

    return [smell for smell in smells if smell.messageId == CustomSmell.LONG_ELEMENT_CHAIN.value]


# @pytest.fixture
# def mock_smell(nested_dict_code: Path, request):
#     return LECSmell(
#         path=str(nested_dict_code),
#         module=nested_dict_code.stem,
#         obj=None,
#         type="convention",
#         symbol="long-element-chain",
#         message="Detected long element chain",
#         messageId=CustomSmell.LONG_ELEMENT_CHAIN.value,
#         confidence="UNDEFINED",
#         occurences=[
#             Occurence(
#                 line=request.param,
#                 endLine=None,
#                 column=0,
#                 endColumn=None,
#             )
#         ],
#         additionalInfo=None,
#     )


def test_nested_dict_detection(get_smells):
    smells: list[LECSmell] = get_smells

    assert len(smells) == 5


def test_dict_flattening(refactorer):
    """Test the dictionary flattening functionality"""
    nested_dict = {"level1": {"level2": {"level3": {"key": "value"}}}}
    expected = {"level1_level2_level3_key": "value"}
    flattened = refactorer.flatten_dict(nested_dict)
    assert flattened == expected


def test_dict_reference_collection(refactorer, nested_dict_code: Path):
    """Test collection of dictionary references from AST"""
    with nested_dict_code.open() as f:
        tree = ast.parse(f.read())

    refactorer.collect_dict_references(tree)
    reference_map = refactorer._reference_map

    assert len(reference_map) > 0
    # Check that nested_dict1 references are collected
    nested_dict1_pattern = next(k for k in reference_map.keys() if k.startswith("nested_dict1"))

    assert len(reference_map[nested_dict1_pattern]) == 2

    # Check that nested_dict2 references are collected
    nested_dict2_pattern = next(k for k in reference_map.keys() if k.startswith("nested_dict2"))

    assert len(reference_map[nested_dict2_pattern]) == 1


@pytest.mark.parametrize("mock_smell", [(25)], indirect=["mock_smell"])
def test_nested_dict1_refactor(
    refactorer,
    nested_dict_code: Path,
    mock_smell: LECSmell,
    source_files,
    output_dir,
):
    """Test the complete refactoring process"""
    initial_content = nested_dict_code.read_text()

    # Perform refactoring
    output_file = output_dir / f"{nested_dict_code.stem}_LECR_{mock_smell.occurences[0].line}.py"
    refactorer.refactor(nested_dict_code, source_files, mock_smell, output_file, overwrite=False)

    # Find the refactored file
    refactored_files = list(output_dir.glob(f"{nested_dict_code.stem}_LECR_*.py"))
    assert len(refactored_files) > 0

    refactored_content = refactored_files[0].read_text()
    assert refactored_content != initial_content

    # Check for flattened dictionary
    assert any(
        [
            "level1_level2_level3_key" in refactored_content,
            "nested_dict1_level1" in refactored_content,
            'nested_dict1["level1_level2_level3_key"]' in refactored_content,
            'print(nested_dict2["level1"]["level2"]["level3"]["key2"])' in refactored_content,
        ]
    )


@pytest.mark.parametrize("mock_smell", [(26)], indirect=["mock_smell"])
def test_nested_dict2_refactor(
    refactorer,
    nested_dict_code: Path,
    mock_smell: LECSmell,
    source_files,
    output_dir,
):
    """Test the complete refactoring process"""
    initial_content = nested_dict_code.read_text()

    # Perform refactoring
    output_file = output_dir / f"{nested_dict_code.stem}_LECR_{mock_smell.occurences[0].line}.py"
    refactorer.refactor(nested_dict_code, source_files, mock_smell, output_file, overwrite=False)

    # Find the refactored file
    refactored_files = list(output_dir.glob(f"{nested_dict_code.stem}_LECR_*.py"))
    assert len(refactored_files) > 0

    refactored_content = refactored_files[0].read_text()
    assert refactored_content != initial_content

    # Check for flattened dictionary
    assert any(
        [
            "level1_level2_level3_key" in refactored_content,
            "nested_dict1_level1" in refactored_content,
            'nested_dict2["level1_level2_level3_key"]' in refactored_content,
            'print(nested_dict1["level1"]["level2"]["level3"]["key"])' in refactored_content,
        ]
    )
