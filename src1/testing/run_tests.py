import os
import sys
import pytest

REFACTOR_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(REFACTOR_DIR))

def run_tests():
    TEST_FILE = os.path.abspath("tests/input/car_stuff_tests.py")
    print("TEST_FILE PATH:",TEST_FILE)
    # Run the tests and store the result
    return pytest.main([TEST_FILE, "--maxfail=1", "--disable-warnings", "--capture=no"])
