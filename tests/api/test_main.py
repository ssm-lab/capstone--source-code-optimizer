from pathlib import Path
from fastapi.testclient import TestClient
import pytest
from ecooptimizer.api.main import app

DIRNAME = Path(__file__).parent
SOURCE_DIR = (DIRNAME / "../input/project_car_stuff").resolve()
TEST_FILE = SOURCE_DIR / "main.py"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_get_smells(client):
    response = client.get(f"/smells?file_path={TEST_FILE!s}")
    print(response.content)
    assert response.status_code == 200


def test_refactor(client):
    payload = {
        "source_dir": str(SOURCE_DIR),
        "smell": {
            "path": str(TEST_FILE),
            "confidence": "UNDEFINED",
            "message": "Too many arguments (9/6)",
            "messageId": "R0913",
            "module": "car_stuff",
            "obj": "Vehicle.__init__",
            "symbol": "too-many-arguments",
            "type": "refactor",
            "occurences": [
                {
                    "line": 5,
                    "endLine": 5,
                    "column": 4,
                    "endColumn": 16,
                }
            ],
        },
    }
    response = client.post("/refactor", json=payload)
    print(response.content)
    assert response.status_code == 200
    assert "refactored_data" in response.json()
