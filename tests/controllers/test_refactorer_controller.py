from unittest.mock import Mock
import pytest

from ecooptimizer.data_types.custom_fields import Occurence
from ecooptimizer.refactorers.refactorer_controller import RefactorerController
from ecooptimizer.data_types.smell import LECSmell


@pytest.fixture
def mock_refactorer_class(mocker):
    mock_class = mocker.Mock()
    mock_class.__name__ = "TestRefactorer"
    return mock_class


@pytest.fixture
def mock_logger(mocker):
    logger = Mock()
    mocker.patch.dict("ecooptimizer.config.CONFIG", {"refactorLogger": logger})
    return logger


@pytest.fixture
def mock_smell():
    """Create a mock smell object for testing."""
    return LECSmell(
        confidence="UNDEFINED",
        message="Dictionary chain too long (6/4)",
        messageId="LEC001",
        module="lec_module",
        obj="lec_function",
        path="path/to/file.py",
        symbol="long-element-chain",
        type="convention",
        occurences=[Occurence(line=10, endLine=10, column=15, endColumn=26)],
        additionalInfo=None,
    )


def test_run_refactorer_success(mocker, mock_refactorer_class, mock_logger, tmp_path, mock_smell):
    # Setup mock refactorer
    mock_instance = mock_refactorer_class.return_value
    # mock_instance.refactor = Mock()
    mock_refactorer_class.return_value = mock_instance

    mock_instance.modified_files = [tmp_path / "modified.py"]

    mocker.patch(
        "ecooptimizer.refactorers.refactorer_controller.get_refactorer",
        return_value=mock_refactorer_class,
    )

    controller = RefactorerController()
    target_file = tmp_path / "test.py"
    target_file.write_text("print('test content')")  # 🚨 Create file with dummy content

    source_dir = tmp_path

    # Execute
    modified_files = controller.run_refactorer(target_file, source_dir, mock_smell)

    # Assertions
    assert controller.smell_counters["LEC001"] == 1
    mock_logger.info.assert_called_once_with(
        "🔄 Running refactoring for long-element-chain using TestRefactorer"
    )
    mock_instance.refactor.assert_called_once_with(
        target_file, source_dir, mock_smell, mocker.ANY, True
    )
    call_args = mock_instance.refactor.call_args
    output_path = call_args[0][3]
    assert output_path.name == "test_path_LEC001_1.py"
    assert modified_files == [tmp_path / "modified.py"]


def test_run_refactorer_no_refactorer(mock_logger, mocker, tmp_path, mock_smell):
    mocker.patch("ecooptimizer.refactorers.refactorer_controller.get_refactorer", return_value=None)
    controller = RefactorerController()
    target_file = tmp_path / "test.py"
    source_dir = tmp_path

    with pytest.raises(NotImplementedError) as exc_info:
        controller.run_refactorer(target_file, source_dir, mock_smell)

    mock_logger.error.assert_called_once_with(
        "❌ No refactorer found for smell: long-element-chain"
    )
    assert "No refactorer implemented for smell: long-element-chain" in str(exc_info.value)


def test_run_refactorer_multiple_calls(mocker, mock_refactorer_class, tmp_path, mock_smell):
    mock_instance = mock_refactorer_class.return_value
    mock_instance.modified_files = []
    mocker.patch(
        "ecooptimizer.refactorers.refactorer_controller.get_refactorer",
        return_value=mock_refactorer_class,
    )
    mocker.patch.dict("ecooptimizer.config.CONFIG", {"refactorLogger": Mock()})

    controller = RefactorerController()
    target_file = tmp_path / "test.py"
    source_dir = tmp_path
    smell = mock_smell

    controller.run_refactorer(target_file, source_dir, smell)
    controller.run_refactorer(target_file, source_dir, smell)

    assert controller.smell_counters["LEC001"] == 2
    calls = mock_instance.refactor.call_args_list
    assert calls[0][0][3].name == "test_path_LEC001_1.py"
    assert calls[1][0][3].name == "test_path_LEC001_2.py"


def test_run_refactorer_overwrite_false(mocker, mock_refactorer_class, tmp_path, mock_smell):
    mock_instance = mock_refactorer_class.return_value
    mocker.patch(
        "ecooptimizer.refactorers.refactorer_controller.get_refactorer",
        return_value=mock_refactorer_class,
    )
    mocker.patch.dict("ecooptimizer.config.CONFIG", {"refactorLogger": Mock()})

    controller = RefactorerController()
    target_file = tmp_path / "test.py"
    source_dir = tmp_path
    smell = mock_smell

    controller.run_refactorer(target_file, source_dir, smell, overwrite=False)
    call_args = mock_instance.refactor.call_args
    assert call_args[0][4] is False  # overwrite is the fifth argument


def test_run_refactorer_empty_modified_files(mocker, mock_refactorer_class, tmp_path, mock_smell):
    mock_instance = mock_refactorer_class.return_value
    mock_instance.modified_files = []
    mocker.patch(
        "ecooptimizer.refactorers.refactorer_controller.get_refactorer",
        return_value=mock_refactorer_class,
    )
    mocker.patch.dict("ecooptimizer.config.CONFIG", {"refactorLogger": Mock()})

    controller = RefactorerController()
    target_file = tmp_path / "test.py"
    source_dir = tmp_path
    smell = mock_smell

    modified_files = controller.run_refactorer(target_file, source_dir, smell)
    assert modified_files == []
