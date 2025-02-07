from src.utils import process_data, process_extra
from src.helper import Helper
from src.main import process_local

def test_process_data():
    assert process_data(1, 2, 3, 4, "path", "setting", "option", "env") == -6

def test_process_extra():
    assert process_extra(8, 7, 6, 5, "file", "mode", "param", "dir") == -8

def test_helper_class():
    h = Helper()
    assert h.process_class_data(1, 2, 3, 4, "config_file", "user_setting", "theme_option", "dev_env") == 34
    assert h.process_more_class_data(1, 2, 3, 4, "log_level", "cache_dir", "timeout", "user_profile") == -8

def test_process_local():
    assert process_local(1, 2, 3, 4, "cache_path", "logging_level", "debug_mode", "staging_env") == -12

if __name__ == "__main__":
    test_process_data()
    test_process_extra()
    test_helper_class()
    test_process_local()
    print("All tests passed!")
