# ruff: noqa: PT004, ARG001
import pytest
import shutil
from pathlib import Path
from typing import Any
from collections.abc import Generator
from fastapi.testclient import TestClient
from unittest.mock import patch

from ecooptimizer.api.app import app
from ecooptimizer.api.error_handler import AppError
from ecooptimizer.api.routes.refactor_smell import perform_refactoring
from ecooptimizer.analyzers.analyzer_controller import AnalyzerController
from ecooptimizer.data_types.custom_fields import Occurence
from ecooptimizer.data_types.smell import Smell
from ecooptimizer.refactorers.refactorer_controller import RefactorerController


client = TestClient(app)

SAMPLE_SMELL_MODEL = Smell(
    confidence="UNKNOWN",
    message="This is a message",
    messageId="smellID",
    module="module",
    obj="obj",
    path=str(Path("path/to/source_dir/fake_path.py").absolute()),
    symbol="smell-symbol",
    type="type",
    occurences=[
        Occurence(
            line=9,
            endLine=999,
            column=999,
            endColumn=999,
        )
    ],
)

SAMPLE_SMELL = SAMPLE_SMELL_MODEL.model_dump()
SAMPLE_SOURCE_DIR = str(Path("path/to/source_dir").absolute())


@pytest.fixture(scope="module")
def mock_dependencies() -> Generator[None, Any, None]:
    """Fixture to mock all dependencies for the /refactor route."""
    with (
        patch.object(Path, "is_dir"),
        patch.object(Path, "exists"),
        patch.object(shutil, "copytree"),
        patch.object(shutil, "rmtree"),
        patch.object(
            RefactorerController,
            "run_refactorer",
            return_value=[
                Path("path/to/modified_file_1.py").absolute(),
                Path("path/to/modified_file_2.py").absolute(),
            ],
        ),
        patch.object(AnalyzerController, "run_analysis"),
        patch(
            "ecooptimizer.api.routes.refactor_smell.mkdtemp",
            return_value="/fake/temp/dir",
        ),
    ):
        yield


@pytest.fixture
def mock_refactor_success():
    """Fixture for successful refactor operations."""
    with (
        patch.object(Path, "is_dir", return_value=True),
        patch.object(Path, "exists", return_value=True),
        patch("ecooptimizer.api.routes.refactor_smell.measure_energy", side_effect=[10.0, 5.0]),
        patch.object(
            RefactorerController,
            "run_refactorer",
            return_value=[
                Path("path/to/modified_file_1.py").absolute(),
                Path("path/to/modified_file_2.py").absolute(),
            ],
        ),
        patch.object(Path, "relative_to", return_value=Path("fake_path.py")),
    ):
        yield


def test_refactor_target_file_not_found(mock_dependencies):
    """Test the /refactor route when the source directory does not exist."""
    Path.exists.return_value = False  # type: ignore

    request_data = {
        "sourceDir": SAMPLE_SOURCE_DIR,
        "smell": SAMPLE_SMELL,
    }

    response = client.post("/refactor", json=request_data)

    assert response.status_code == 404
    assert "File not found" in response.json()["detail"]


def test_refactor_source_dir_not_found(mock_dependencies):
    """Test the /refactor route when the source directory does not exist."""
    Path.exists.return_value = True  # type: ignore
    Path.is_dir.return_value = False  # type: ignore

    request_data = {
        "sourceDir": SAMPLE_SOURCE_DIR,
        "smell": SAMPLE_SMELL,
    }

    response = client.post("/refactor", json=request_data)

    assert response.status_code == 404
    assert "Folder not found" in response.json()["detail"]


@patch("ecooptimizer.api.routes.refactor_smell.measure_energy", side_effect=[10.0, 15.0])
def test_refactor_energy_not_saved(mock_measure, mock_dependencies, mock_refactor_success):
    """Test the /refactor route when no energy is saved after refactoring."""
    request_data = {
        "sourceDir": SAMPLE_SOURCE_DIR,
        "smell": SAMPLE_SMELL,
    }

    response = client.post("/refactor", json=request_data)

    assert response.status_code == 400
    assert "Energy was not saved" in response.json()["detail"]


@patch("ecooptimizer.api.routes.refactor_smell.measure_energy", return_value=None)
def test_refactor_initial_energy_not_retrieved(mock_measure, mock_dependencies):
    """Test the /refactor route when no energy is saved after refactoring."""
    Path.is_dir.return_value = True  # type: ignore
    Path.exists.return_value = True  # type: ignore

    request_data = {
        "sourceDir": SAMPLE_SOURCE_DIR,
        "smell": SAMPLE_SMELL,
    }

    response = client.post("/refactor", json=request_data)

    assert response.status_code == 400
    assert "Could not retrieve emissions" in response.json()["detail"]


@patch("ecooptimizer.api.routes.refactor_smell.measure_energy", side_effect=[10.0, None])
def test_refactor_final_energy_not_retrieved(mock_measure, mock_dependencies):
    """Test the /refactor route when no energy is saved after refactoring."""
    Path.is_dir.return_value = True  # type: ignore

    request_data = {
        "sourceDir": SAMPLE_SOURCE_DIR,
        "smell": SAMPLE_SMELL,
    }

    response = client.post("/refactor", json=request_data)

    assert response.status_code == 400
    assert "Could not retrieve emissions" in response.json()["detail"]


@patch("ecooptimizer.api.routes.refactor_smell.measure_energy", return_value=10.0)
def test_refactor_unexpected_error(mock_measure, mock_dependencies):
    """Test the /refactor route when an unexpected error occurs during refactoring."""
    Path.is_dir.return_value = True  # type: ignore
    RefactorerController.run_refactorer.side_effect = Exception("Mock error")  # type: ignore

    request_data = {
        "sourceDir": SAMPLE_SOURCE_DIR,
        "smell": SAMPLE_SMELL,
    }

    response = client.post("/refactor", json=request_data)

    assert response.status_code == 500
    assert "Mock error" == response.json()["detail"]


def test_refactor_success(mock_dependencies, mock_refactor_success):
    """Test the /refactor route with a successful refactoring process."""
    request_data = {
        "sourceDir": SAMPLE_SOURCE_DIR,
        "smell": SAMPLE_SMELL,
    }

    response = client.post("/refactor", json=request_data)

    assert response.status_code == 200
    assert set(response.json().keys()) == {
        "tempDir",
        "targetFile",
        "energySaved",
        "affectedFiles",
    }


@patch("ecooptimizer.api.routes.refactor_smell.measure_energy", side_effect=[15, 10, 8])
@patch.object(AnalyzerController, "run_analysis")
def test_refactor_by_type_success(
    mock_run_analysis, mock_measure, mock_dependencies, mock_refactor_success
):
    """Test the /refactor-by-type endpoint with successful refactoring."""
    mock_run_analysis.side_effect = [[SAMPLE_SMELL_MODEL], []]
    request_data = {
        "sourceDir": SAMPLE_SOURCE_DIR,
        "smellType": "type",
        "firstSmell": SAMPLE_SMELL,
    }

    response = client.post("/refactor-by-type", json=request_data)

    assert response.status_code == 200
    assert set(response.json().keys()) == {
        "tempDir",
        "targetFile",
        "energySaved",
        "affectedFiles",
    }
    assert response.json()["energySaved"] == 7


@patch("ecooptimizer.api.routes.refactor_smell.measure_energy", side_effect=[15, 10, 8, 6])
@patch.object(AnalyzerController, "run_analysis")
def test_refactor_by_type_multiple_smells(
    mock_run_analysis, mock_measure, mock_dependencies, mock_refactor_success
):
    """Test /refactor-by-type with multiple smells of same type."""
    mock_run_analysis.side_effect = [[SAMPLE_SMELL_MODEL], [SAMPLE_SMELL_MODEL], []]
    request_data = {
        "sourceDir": SAMPLE_SOURCE_DIR,
        "smellType": "type",
        "firstSmell": SAMPLE_SMELL,
    }

    response = client.post("/refactor-by-type", json=request_data)

    assert response.status_code == 200
    assert response.json()["energySaved"] == 9.0


@patch("ecooptimizer.api.routes.refactor_smell.measure_energy", return_value=None)
def test_refactor_by_type_initial_energy_failure(
    mock_measure, mock_dependencies, mock_refactor_success
):
    """Test /refactor-by-type when initial energy measurement fails."""
    Path.exists.return_value = True  # type: ignore
    Path.is_dir.return_value = True  # type: ignore

    request_data = {
        "sourceDir": SAMPLE_SOURCE_DIR,
        "smellType": "type",
        "firstSmell": SAMPLE_SMELL,
    }

    response = client.post("/refactor-by-type", json=request_data)

    assert response.status_code == 400
    assert "Could not retrieve emissions" in response.json()["detail"]


@patch.object(Path, "is_dir", return_value=False)
def test_refactor_by_type_source_dir_not_found(mock_isdir):
    """Test /refactor-by-type when source directory doesn't exist."""
    Path.exists.return_value = True  # type: ignore

    request_data = {
        "sourceDir": SAMPLE_SOURCE_DIR,
        "smellType": "type",
        "firstSmell": SAMPLE_SMELL,
    }

    response = client.post("/refactor-by-type", json=request_data)

    assert response.status_code == 404
    assert "Folder not found" in response.json()["detail"]


@patch.object(RefactorerController, "run_refactorer")
def test_refactor_by_type_refactoring_error(
    mock_run_refactor,
    mock_dependencies,
    mock_refactor_success,
):
    """Test /refactor-by-type when refactoring fails."""
    mock_run_refactor.side_effect = AppError("Refactoring failed")
    request_data = {
        "sourceDir": SAMPLE_SOURCE_DIR,
        "smellType": "type",
        "firstSmell": SAMPLE_SMELL,
    }

    response = client.post("/refactor-by-type", json=request_data)

    assert response.status_code == 500
    assert "Refactoring failed" in response.json()["detail"]


@patch("ecooptimizer.api.routes.refactor_smell.measure_energy", side_effect=[10.0, 15.0])
def test_refactor_by_type_no_energy_saved(mock_measure, mock_dependencies, mock_refactor_success):
    """Test /refactor-by-type when no energy is saved."""
    request_data = {
        "sourceDir": SAMPLE_SOURCE_DIR,
        "smellType": "type",
        "firstSmell": SAMPLE_SMELL,
    }

    response = client.post("/refactor-by-type", json=request_data)

    assert response.status_code == 400
    assert "Energy was not saved" in response.json()["detail"]


@patch("ecooptimizer.api.routes.refactor_smell.measure_energy", side_effect=[5.0])
@patch.object(RefactorerController, "run_refactorer", return_value=[Path("modified_file.py")])
@patch("shutil.copytree")
@patch("ecooptimizer.api.routes.refactor_smell.mkdtemp", return_value="/fake/temp/dir")
def test_perform_refactoring_success(
    mock_mkdtemp, mock_copytree, mock_run_refactorer, mock_measure
):
    """Test the perform_refactoring helper function."""
    source_dir = Path(SAMPLE_SOURCE_DIR)
    smell = SAMPLE_SMELL_MODEL
    result = perform_refactoring(source_dir, smell, 10.0)

    assert result.energySaved == 5.0
    mock_mkdtemp.assert_called_once_with(prefix="ecooptimizer-")
    assert result.tempDir == str(Path("/fake/temp/dir"))
    assert len(result.affectedFiles) == 1


@patch("ecooptimizer.api.routes.refactor_smell.measure_energy", side_effect=[5])
@patch.object(RefactorerController, "run_refactorer", return_value=[Path("modified_file.py")])
@patch.object(shutil, "copytree")
def test_perform_refactoring_with_existing_temp_dir(
    mock_copytree, mock_run_refactorer, mock_measure
):
    """Test perform_refactoring with an existing temp directory."""
    source_dir = Path(SAMPLE_SOURCE_DIR)
    smell = SAMPLE_SMELL_MODEL
    existing_dir = Path("/existing/temp/dir")
    result = perform_refactoring(source_dir, smell, 10.0, existing_dir)

    assert result.energySaved == 5.0
    assert result.tempDir == str(Path("/existing/temp/dir"))
    assert len(result.affectedFiles) == 1
