from fastapi.testclient import TestClient
from unittest.mock import patch

from ecooptimizer.api.app import app
from ecooptimizer.api.error_handler import AppError
from ecooptimizer.data_types import Smell
from ecooptimizer.data_types.custom_fields import Occurence

client = TestClient(app)


def get_mock_smell():
    return Smell(
        confidence="UNKNOWN",
        message="This is a message",
        messageId="smellID",
        module="module",
        obj="obj",
        path="fake_path.py",
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


def test_detect_smells_success():
    request_data = {
        "file_path": "fake_path.py",
        "enabled_smells": {
            "smell1": {"threshold": 3},
            "smell2": {"threshold": 4},
        },
    }

    with patch("pathlib.Path.exists", return_value=True):
        with patch(
            "ecooptimizer.analyzers.analyzer_controller.AnalyzerController.run_analysis"
        ) as mock_run_analysis:
            mock_run_analysis.return_value = [get_mock_smell(), get_mock_smell()]

            response = client.post("/smells", json=request_data)

            assert response.status_code == 200
            assert len(response.json()) == 2


def test_detect_smells_file_not_found():
    request_data = {
        "file_path": "path/to/nonexistent/file.py",
        "enabled_smells": {
            "smell1": {"threshold": 3},
            "smell2": {"threshold": 4},
        },
    }

    response = client.post("/smells", json=request_data)

    assert response.status_code == 404
    assert "File not found" in response.json()["detail"]


def test_detect_smells_internal_server_error():
    request_data = {
        "file_path": "fake_path.py",
        "enabled_smells": {
            "smell1": {"threshold": 3},
            "smell2": {"threshold": 4},
        },
    }

    with patch("pathlib.Path.exists", return_value=True):
        with patch(
            "ecooptimizer.analyzers.analyzer_controller.AnalyzerController.run_analysis"
        ) as mock_run_analysis:
            mock_run_analysis.side_effect = AppError("Internal error")

            response = client.post("/smells", json=request_data)

            assert response.status_code == 500
            assert response.json()["detail"] == "Internal error"
