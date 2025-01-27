from fastapi.testclient import TestClient
from ecooptimizer.api.main import app

client = TestClient(app)


def test_get_smells():
    response = client.get("/smells?file_path=/Users/tanveerbrar/Desktop/car_stuff.py")
    assert response.status_code == 200


def test_refactor():
    payload = {
        "file_path": "/Users/tanveerbrar/Desktop/car_stuff.py",
        "smell": {
            "absolutePath": "/Users/tanveerbrar/Desktop/car_stuff.py",
            "column": 4,
            "confidence": "UNDEFINED",
            "endColumn": 16,
            "endLine": 5,
            "line": 5,
            "message": "Too many arguments (9/6)",
            "messageId": "R0913",
            "module": "car_stuff",
            "obj": "Vehicle.__init__",
            "path": "/Users/tanveerbrar/Desktop/car_stuff.py",
            "symbol": "too-many-arguments",
            "type": "refactor",
            "repetitions": None,
            "occurrences": None,
        },
    }
    response = client.post("/refactor", json=payload)
    assert response.status_code == 200
    assert "refactoredCode" in response.json()
