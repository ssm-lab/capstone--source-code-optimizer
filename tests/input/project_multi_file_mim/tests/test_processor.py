from src.processor import process_data

def test_process_data():
    """
    Test the process_data function.
    """
    result = process_data("test")
    assert result == "TEST"
