from src.caller_1 import process_data, process_extra
from src.caller_2 import Helper
from src.main import process_local

def test_process_data():
    assert process_data(1, 2, 3, 4, 5, 6, 7, 8) == 33

def test_process_extra():
    assert process_extra(1, 2, 3, 4, 5, 6, 7, 8) == -1

def test_helper_class():
    h = Helper()
    assert h.process_class_data(1, 2, 3, 4, 5, 6, 7, 8) == 40
    assert h.process_more_class_data(1, 2, 3, 4, 5, 6, 7, 8) == -8

def test_process_local():
    assert process_local(1, 2, 3, 4, 5, 6, 7, 8) == -36

if __name__ == "__main__":
    test_process_data()
    test_process_extra()
    test_helper_class()
    test_process_local()
    print("All tests passed!")
