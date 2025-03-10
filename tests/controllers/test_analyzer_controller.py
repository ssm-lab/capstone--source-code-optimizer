import textwrap
import pytest
from unittest.mock import Mock
from ecooptimizer.analyzers.analyzer_controller import AnalyzerController
from ecooptimizer.analyzers.ast_analyzers.detect_repeated_calls import detect_repeated_calls
from ecooptimizer.data_types.custom_fields import CRCInfo, Occurence
from ecooptimizer.refactorers.concrete.repeated_calls import CacheRepeatedCallsRefactorer
from ecooptimizer.refactorers.concrete.long_element_chain import LongElementChainRefactorer
from ecooptimizer.refactorers.concrete.list_comp_any_all import UseAGeneratorRefactorer
from ecooptimizer.refactorers.concrete.str_concat_in_loop import UseListAccumulationRefactorer
from ecooptimizer.data_types.smell import CRCSmell


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
        messageId="CRC001",
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


def test_run_analysis_detects_crc_smell(mocker, mock_logger, tmp_path):
    """Ensures the analyzer correctly detects CRC smells."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        textwrap.dedent("""
    def test_case():
        result1 = expensive_function(42)
        result2 = expensive_function(42)
    """)
    )

    mocker.patch(
        "ecooptimizer.utils.smells_registry.retrieve_smell_registry",
        return_value={
            "cached-repeated-calls": SmellRecord(
                id="CRC001",
                enabled=True,
                analyzer_method="ast",
                checker=detect_repeated_calls,
                analyzer_options={"threshold": 2},
                refactorer=CacheRepeatedCallsRefactorer,
            )
        },
    )

    controller = AnalyzerController()
    smells = controller.run_analysis(test_file)

    print("Detected smells:", smells)
    assert len(smells) == 1
    assert isinstance(smells[0], CRCSmell)
    assert smells[0].additionalInfo.callString == "expensive_function(42)"
    mock_logger.info.assert_any_call("⚠️ Detected Code Smells:")


def test_run_analysis_no_crc_smells_detected(mocker, mock_logger, tmp_path):
    """Ensures the analyzer logs properly when no CRC smells are found."""
    test_file = tmp_path / "test.py"
    test_file.write_text("print('No smells here')")

    mocker.patch(
        "ecooptimizer.utils.smells_registry.retrieve_smell_registry",
        return_value={
            "cached-repeated-calls": SmellRecord(
                id="CRC001",
                enabled=True,
                analyzer_method="ast",
                checker=detect_repeated_calls,
                analyzer_options={"threshold": 2},
                refactorer=CacheRepeatedCallsRefactorer,
            )
        },
    )

    controller = AnalyzerController()
    smells = controller.run_analysis(test_file)

    assert smells == []
    mock_logger.info.assert_called_with("🎉 No code smells detected.")


from ecooptimizer.data_types.smell_record import SmellRecord


def test_filter_smells_by_method():
    """Ensures the method filters all types of smells correctly."""
    mock_registry = {
        "cached-repeated-calls": SmellRecord(
            id="CRC001",
            enabled=True,
            analyzer_method="ast",
            checker=lambda x: x,
            analyzer_options={},
            refactorer=CacheRepeatedCallsRefactorer,
        ),
        "long-element-chain": SmellRecord(
            id="LEC001",
            enabled=True,
            analyzer_method="ast",
            checker=lambda x: x,
            analyzer_options={},
            refactorer=LongElementChainRefactorer,
        ),
        "use-a-generator": SmellRecord(
            id="R1729",
            enabled=True,
            analyzer_method="pylint",
            checker=None,
            analyzer_options={},
            refactorer=UseAGeneratorRefactorer,
        ),
        "string-concat-loop": SmellRecord(
            id="SCL001",
            enabled=True,
            analyzer_method="astroid",
            checker=lambda x: x,
            analyzer_options={},
            refactorer=UseListAccumulationRefactorer,
        ),
    }

    result_ast = AnalyzerController.filter_smells_by_method(mock_registry, "ast")
    result_pylint = AnalyzerController.filter_smells_by_method(mock_registry, "pylint")
    result_astroid = AnalyzerController.filter_smells_by_method(mock_registry, "astroid")

    assert "cached-repeated-calls" in result_ast
    assert "long-element-chain" in result_ast
    assert "use-a-generator" in result_pylint
    assert "string-concat-loop" in result_astroid


def test_generate_custom_options():
    """Ensures AST and Astroid analysis options are generated correctly."""
    mock_registry = {
        "cached-repeated-calls": SmellRecord(
            id="CRC001",
            enabled=True,
            analyzer_method="ast",
            checker=lambda x: x,
            analyzer_options={},
            refactorer=CacheRepeatedCallsRefactorer,
        ),
        "long-element-chain": SmellRecord(
            id="LEC001",
            enabled=True,
            analyzer_method="ast",
            checker=lambda x: x,
            analyzer_options={},
            refactorer=LongElementChainRefactorer,
        ),
        "string-concat-loop": SmellRecord(
            id="SCL001",
            enabled=True,
            analyzer_method="astroid",
            checker=lambda x: x,
            analyzer_options={},
            refactorer=UseListAccumulationRefactorer,
        ),
    }
    options = AnalyzerController.generate_custom_options(mock_registry)
    assert len(options) == 3
    assert callable(options[0][0])
    assert callable(options[1][0])
    assert callable(options[2][0])
