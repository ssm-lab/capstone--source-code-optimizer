import textwrap
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from ecooptimizer.analyzers.analyzer_controller import AnalyzerController
from ecooptimizer.analyzers.ast_analyzer import ASTAnalyzer
from ecooptimizer.analyzers.ast_analyzers.detect_repeated_calls import detect_repeated_calls
from ecooptimizer.data_types.custom_fields import CRCInfo, Occurence
from ecooptimizer.data_types.smell import Smell, CRCSmell
from ecooptimizer.data_types.smell_record import SmellRecord
from ecooptimizer.refactorers.concrete.repeated_calls import CacheRepeatedCallsRefactorer
from ecooptimizer.refactorers.base_refactorer import BaseRefactorer
from ecooptimizer.utils.smell_enums import CustomSmell


# Create proper mock refactorer classes with type parameters
class MockRefactorer(BaseRefactorer[CRCSmell]):
    def refactor(
        self,
        target_file: Path,
        source_dir: Path,
        smell: CRCSmell,
        output_file: Path,
        overwrite: bool = True,
    ):
        pass


class MockGenericRefactorer(BaseRefactorer[Smell]):
    def refactor(
        self,
        target_file: Path,
        source_dir: Path,
        smell: Smell,
        output_file: Path,
        overwrite: bool = True,
    ):
        pass


@pytest.fixture
def mock_logger(mocker):
    logger = Mock()
    mocker.patch.dict("ecooptimizer.config.CONFIG", {"detectLogger": logger})
    return logger


@pytest.fixture
def mock_crc_smell():
    """Create a mock CRC smell object for testing."""
    return CRCSmell(
        confidence="MEDIUM",
        message="Repeated function call detected (2/2). Consider caching the result: expensive_function(42)",
        messageId=CustomSmell.CACHE_REPEATED_CALLS.value,
        module="main",
        obj=None,
        path="/path/to/test.py",
        symbol="cached-repeated-calls",
        type="performance",
        occurences=[
            Occurence(line=2, endLine=2, column=14, endColumn=36),
            Occurence(line=3, endLine=3, column=14, endColumn=36),
        ],
        additionalInfo=CRCInfo(callString="expensive_function(42)", repetitions=2),
    )


def test_run_analysis_detects_crc_smell(mocker, tmp_path):
    """Ensures the analyzer correctly detects CRC smells."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        textwrap.dedent("""
    def test_case():
        result1 = expensive_function(42)
        result2 = expensive_function(42)
    """)
    )

    # Create a mock smell that would be returned by the analyzer
    mock_smell = CRCSmell(
        confidence="HIGH",
        message="Repeated function call detected (2/2). Consider caching the result: expensive_function(42)",
        messageId=CustomSmell.CACHE_REPEATED_CALLS.value,
        module="test",
        obj=None,
        path=str(test_file),
        symbol="cached-repeated-calls",
        type="performance",
        occurences=[
            Occurence(line=2, endLine=2, column=14, endColumn=36),
            Occurence(line=3, endLine=3, column=14, endColumn=36),
        ],
        additionalInfo=CRCInfo(callString="expensive_function(42)", repetitions=2),
    )

    # Mock the AST analyzer to return our mock smell
    mock_ast_analyzer = mocker.patch.object(ASTAnalyzer, "analyze")
    mock_ast_analyzer.return_value = [mock_smell]

    mock_registry = {
        "cached-repeated-calls": SmellRecord(
            id=CustomSmell.CACHE_REPEATED_CALLS.value,
            enabled=True,
            analyzer_method="ast",
            checker=detect_repeated_calls,
            analyzer_options={"threshold": 2},
            refactorer=CacheRepeatedCallsRefactorer,
        )
    }

    with patch(
        "ecooptimizer.utils.smells_registry.retrieve_smell_registry", return_value=mock_registry
    ):
        controller = AnalyzerController()
        smells = controller.run_analysis(test_file, enabled_smells=["cached-repeated-calls"])

        assert len(smells) == 1
        assert isinstance(smells[0], Smell)
        assert smells[0].symbol == "cached-repeated-calls"
        assert smells[0].messageId == CustomSmell.CACHE_REPEATED_CALLS.value


def test_run_analysis_no_crc_smells_detected(mocker, tmp_path):
    """Ensures the analyzer logs properly when no CRC smells are found."""
    test_file = tmp_path / "test.py"
    test_file.write_text("print('No smells here')")

    # Mock the AST analyzer to return no smells
    mock_ast_analyzer = mocker.patch.object(ASTAnalyzer, "analyze")
    mock_ast_analyzer.return_value = []

    mock_registry = {
        "cached-repeated-calls": SmellRecord(
            id=CustomSmell.CACHE_REPEATED_CALLS.value,
            enabled=True,
            analyzer_method="ast",
            checker=detect_repeated_calls,
            analyzer_options={"threshold": 2},
            refactorer=CacheRepeatedCallsRefactorer,
        )
    }

    with patch(
        "ecooptimizer.utils.smells_registry.retrieve_smell_registry", return_value=mock_registry
    ):
        controller = AnalyzerController()
        smells = controller.run_analysis(test_file, enabled_smells=["cached-repeated-calls"])

        assert smells == []


def test_filter_smells_by_method():
    """Ensures the method filters all types of smells correctly."""
    mock_registry = {
        "cached-repeated-calls": SmellRecord(
            id=CustomSmell.CACHE_REPEATED_CALLS.value,
            enabled=True,
            analyzer_method="ast",
            checker=detect_repeated_calls,
            analyzer_options={"threshold": 2},
            refactorer=CacheRepeatedCallsRefactorer,
        ),
        "use-a-generator": SmellRecord(
            id="R1729",
            enabled=True,
            analyzer_method="pylint",
            checker=None,
            analyzer_options={},
            refactorer=MockGenericRefactorer,
        ),
        "string-concat-loop": SmellRecord(
            id="SCL001",
            enabled=True,
            analyzer_method="astroid",
            checker=Mock(),
            analyzer_options={},
            refactorer=MockGenericRefactorer,
        ),
    }

    result_ast = AnalyzerController.filter_smells_by_method(mock_registry, "ast")
    result_pylint = AnalyzerController.filter_smells_by_method(mock_registry, "pylint")
    result_astroid = AnalyzerController.filter_smells_by_method(mock_registry, "astroid")

    assert "cached-repeated-calls" in result_ast
    assert "use-a-generator" in result_pylint
    assert "string-concat-loop" in result_astroid
    assert len(result_ast) == 1
    assert len(result_pylint) == 1
    assert len(result_astroid) == 1


def test_generate_custom_options():
    """Ensures AST and Astroid analysis options are generated correctly."""
    mock_registry = {
        "cached-repeated-calls": SmellRecord(
            id=CustomSmell.CACHE_REPEATED_CALLS.value,
            enabled=True,
            analyzer_method="ast",
            checker=detect_repeated_calls,
            analyzer_options={"threshold": 2},
            refactorer=CacheRepeatedCallsRefactorer,
        ),
        "string-concat-loop": SmellRecord(
            id="SCL001",
            enabled=True,
            analyzer_method="astroid",
            checker=Mock(),
            analyzer_options={},
            refactorer=MockGenericRefactorer,
        ),
    }

    options = AnalyzerController.generate_custom_options(mock_registry)
    assert len(options) == 2
    assert options[0][0] == detect_repeated_calls
    assert options[0][1] == {"threshold": 2}
    assert callable(options[1][0])  # Mock checker
    assert options[1][1] == {}


def test_generate_pylint_options():
    """Ensures Pylint analysis options are generated correctly."""
    mock_registry = {
        "use-a-generator": SmellRecord(
            id="R1729",
            enabled=True,
            analyzer_method="pylint",
            checker=None,
            analyzer_options={},
            refactorer=MockGenericRefactorer,
        ),
        "too-many-arguments": SmellRecord(
            id="R0913",
            enabled=True,
            analyzer_method="pylint",
            checker=None,
            analyzer_options={"max_args": {"flag": "--max-args", "value": 5}},
            refactorer=MockGenericRefactorer,
        ),
    }

    options = AnalyzerController.generate_pylint_options(mock_registry)
    assert "--disable=all" in options
    assert "--enable=use-a-generator,too-many-arguments" in options
    assert any(opt.startswith("--max-args=") for opt in options)
