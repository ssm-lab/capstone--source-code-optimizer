# ruff: noqa: PT004
import pytest

import shutil
from pathlib import Path
from typing import Any
from collections.abc import Generator
from fastapi.testclient import TestClient
from unittest.mock import patch


from ecooptimizer.api.app import app
from ecooptimizer.analyzers.analyzer_controller import AnalyzerController
from ecooptimizer.refactorers.refactorer_controller import RefactorerController


client = TestClient(app)

SAMPLE_SMELL = {
    "confidence": "UNKNOWN",
    "message": "This is a message",
    "messageId": "smellID",
    "module": "module",
    "obj": "obj",
    "path": "fake_path.py",
    "symbol": "smell-symbol",
    "type": "type",
    "occurences": [
        {
            "line": 9,
            "endLine": 999,
            "column": 999,
            "endColumn": 999,
        }
    ],
}

SAMPLE_SOURCE_DIR = "path\\to\\source_dir"


@pytest.fixture(scope="module")
def mock_dependencies() -> Generator[None, Any, None]:
    """Fixture to mock all dependencies for the /refactor route."""
    with (
        patch.object(Path, "is_dir"),
        patch.object(shutil, "copytree"),
        patch.object(shutil, "rmtree"),
        patch.object(
            RefactorerController,
            "run_refactorer",
            return_value=[
                Path("path/to/modified_file_1.py"),
                Path("path/to/modified_file_2.py"),
            ],
        ),
        patch.object(AnalyzerController, "run_analysis", return_value=[SAMPLE_SMELL]),
        patch("tempfile.mkdtemp", return_value="/fake/temp/dir"),
    ):
        yield


def test_refactor_success(mock_dependencies):  # noqa: ARG001
    """Test the /refactor route with a successful refactoring process."""
    Path.is_dir.return_value = True  # type: ignore

    with patch("ecooptimizer.api.routes.refactor_smell.measure_energy", side_effect=[10.0, 5.0]):
        request_data = {
            "source_dir": SAMPLE_SOURCE_DIR,
            "smell": SAMPLE_SMELL,
        }

        response = client.post("/refactor", json=request_data)

        assert response.status_code == 200
        assert "refactoredData" in response.json()
        assert "updatedSmells" in response.json()
        assert len(response.json()["updatedSmells"]) == 1


def test_refactor_source_dir_not_found(mock_dependencies):  # noqa: ARG001
    """Test the /refactor route when the source directory does not exist."""
    Path.is_dir.return_value = False  # type: ignore

    request_data = {
        "source_dir": SAMPLE_SOURCE_DIR,
        "smell": SAMPLE_SMELL,
    }

    response = client.post("/refactor", json=request_data)

    assert response.status_code == 404
    assert f"Directory {SAMPLE_SOURCE_DIR} does not exist" in response.json()["detail"]


def test_refactor_energy_not_saved(mock_dependencies):  # noqa: ARG001
    """Test the /refactor route when no energy is saved after refactoring."""
    Path.is_dir.return_value = True  # type: ignore

    with patch("ecooptimizer.api.routes.refactor_smell.measure_energy", side_effect=[10.0, 15.0]):
        request_data = {
            "source_dir": SAMPLE_SOURCE_DIR,
            "smell": SAMPLE_SMELL,
        }

        response = client.post("/refactor", json=request_data)

        assert response.status_code == 400
        assert "Energy was not saved" in response.json()["detail"]


def test_refactor_initial_energy_not_retrieved(mock_dependencies):  # noqa: ARG001
    """Test the /refactor route when no energy is saved after refactoring."""
    Path.is_dir.return_value = True  # type: ignore

    with patch("ecooptimizer.api.routes.refactor_smell.measure_energy", return_value=None):
        request_data = {
            "source_dir": SAMPLE_SOURCE_DIR,
            "smell": SAMPLE_SMELL,
        }

        response = client.post("/refactor", json=request_data)

        assert response.status_code == 400
        assert "Could not retrieve initial emissions" in response.json()["detail"]


def test_refactor_final_energy_not_retrieved(mock_dependencies):  # noqa: ARG001
    """Test the /refactor route when no energy is saved after refactoring."""
    Path.is_dir.return_value = True  # type: ignore

    with patch("ecooptimizer.api.routes.refactor_smell.measure_energy", side_effect=[10.0, None]):
        request_data = {
            "source_dir": SAMPLE_SOURCE_DIR,
            "smell": SAMPLE_SMELL,
        }

        response = client.post("/refactor", json=request_data)

        assert response.status_code == 400
        assert "Could not retrieve final emissions" in response.json()["detail"]


def test_refactor_unexpected_error(mock_dependencies):  # noqa: ARG001
    """Test the /refactor route when an unexpected error occurs during refactoring."""
    Path.is_dir.return_value = True  # type: ignore
    RefactorerController.run_refactorer.side_effect = Exception("Mock error")  # type: ignore

    with patch("ecooptimizer.api.routes.refactor_smell.measure_energy", return_value=10.0):
        request_data = {
            "source_dir": SAMPLE_SOURCE_DIR,
            "smell": SAMPLE_SMELL,
        }

        response = client.post("/refactor", json=request_data)

        assert response.status_code == 400
        assert "Mock error" in response.json()["detail"]
