from src.utils import Utility

def test_unused_member_method(capfd):
    """
    Test the unused_member_method to ensure it behaves as expected.
    """
    util = Utility()
    util.unused_member_method("test")
    captured = capfd.readouterr()
    assert "This method is defined but doesn’t use its parameter." in captured.out
