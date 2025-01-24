import ast
from pathlib import Path
import textwrap
import pytest
from ecooptimizer.analyzers.pylint_analyzer import PylintAnalyzer
from ecooptimizer.refactorers.long_element_chain import (
    LongElementChainRefactorer,
)


def get_smells(code: Path):
    analyzer = PylintAnalyzer(code, ast.parse(code.read_text()))
    analyzer.analyze()
    analyzer.configure_smells()
    return analyzer.smells_data


@pytest.fixture(scope="module")
def source_files(tmp_path_factory):
    return tmp_path_factory.mktemp("input")


@pytest.fixture
def refactorer(output_dir):
    return LongElementChainRefactorer(output_dir)


@pytest.fixture
def mock_smell():
    return {
        "message": "Long element chain detected",
        "messageId": "long-element-chain",
        "occurences": [{"line": 25, "column": 0}],
    }


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


def test_nested_dict1_refactor(refactorer, nested_dict_code: Path, mock_smell):
    """Test the complete refactoring process"""
    initial_content = nested_dict_code.read_text()

    # Perform refactoring
    refactorer.refactor(nested_dict_code, mock_smell, overwrite=False)

    # Find the refactored file
    refactored_files = list(refactorer.temp_dir.glob(f"{nested_dict_code.stem}_LECR_*.py"))
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


def test_nested_dict2_refactor(refactorer, nested_dict_code: Path, mock_smell):
    """Test the complete refactoring process"""
    initial_content = nested_dict_code.read_text()
    mock_smell["occurences"][0]["line"] = 26
    # Perform refactoring
    refactorer.refactor(nested_dict_code, mock_smell, overwrite=False)

    # Find the refactored file
    refactored_files = list(refactorer.temp_dir.glob(f"{nested_dict_code.stem}_LECR_*.py"))
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
