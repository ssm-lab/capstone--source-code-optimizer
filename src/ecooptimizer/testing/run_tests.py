from pathlib import Path
import sys
import pytest

REFACTOR_DIR = Path(__file__).absolute().parent
sys.path.append(str(REFACTOR_DIR))


def run_tests():
    TEST_FILE = (REFACTOR_DIR / Path("../../../tests/input/car_stuff_tests.py")).resolve()
    print("test file", TEST_FILE)
    return pytest.main([str(TEST_FILE), "--maxfail=1", "--disable-warnings", "--capture=no"])