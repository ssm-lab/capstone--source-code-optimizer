import pytest
import textwrap
from unittest.mock import patch
from pathlib import Path

from ecooptimizer.refactorers.concrete.long_lambda_function import (
    LongLambdaFunctionRefactorer,
)
from ecooptimizer.data_types import Occurence, LLESmell
from ecooptimizer.utils.smell_enums import CustomSmell


@pytest.fixture
def refactorer():
    return LongLambdaFunctionRefactorer()


def create_smell(occurences: list[int]):
    """Factory function to create lambda smell objects."""
    return lambda: LLESmell(
        path="fake.py",
        module="some_module",
        obj=None,
        type="performance",
        symbol="long-lambda",
        message="Lambda too long",
        messageId=CustomSmell.LONG_LAMBDA_EXPR.value,
        confidence="UNDEFINED",
        occurences=[
            Occurence(line=occ, endLine=999, column=999, endColumn=999)
            for occ in occurences
        ],
        additionalInfo=None,
    )


def normalize_code(code: str) -> str:
    """Normalize whitespace for reliable comparisons."""
    return "\n".join(line.rstrip() for line in code.strip().splitlines()) + "\n"


def test_basic_lambda_conversion(refactorer):
    """Tests conversion of simple single-line lambda."""
    code = textwrap.dedent(
        """
    def example():
        my_lambda = lambda x: x + 1
    """
    )

    expected = textwrap.dedent(
        """
    def example():
        def converted_lambda_3(x):
            result = x + 1
            return result
        
        my_lambda = converted_lambda_3
    """
    )

    smell = create_smell([3])()
    with (
        patch.object(Path, "read_text", return_value=code),
        patch.object(Path, "write_text") as mock_write,
    ):

        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))

        written = mock_write.call_args[0][0]
        print(written)
        assert normalize_code(written) == normalize_code(expected)


def test_no_extra_print_statements(refactorer):
    """Ensures no print statements are added unnecessarily."""
    code = textwrap.dedent(
        """
    def example():
        processor = lambda x: x.strip().lower()
    """
    )

    expected = textwrap.dedent(
        """
    def example():
        def converted_lambda_3(x):
            result = x.strip().lower()
            return result
        
        processor = converted_lambda_3
    """
    )

    smell = create_smell([3])()
    with (
        patch.object(Path, "read_text", return_value=code),
        patch.object(Path, "write_text") as mock_write,
    ):

        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))
        written = mock_write.call_args[0][0]
        assert "print(" not in written
        assert normalize_code(written) == normalize_code(expected)


def test_lambda_in_function_argument(refactorer):
    """Tests lambda passed as argument to another function."""
    code = textwrap.dedent(
        """
    def process_data():
        results = list(map(lambda x: x * 2, [1, 2, 3]))
    """
    )

    expected = textwrap.dedent(
        """
    def process_data():
        def converted_lambda_3(x):
            result = x * 2
            return result
        
        results = list(map(converted_lambda_3, [1, 2, 3]))
    """
    )

    smell = create_smell([3])()
    with (
        patch.object(Path, "read_text", return_value=code),
        patch.object(Path, "write_text") as mock_write,
    ):

        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))

        written = mock_write.call_args[0][0]
        assert normalize_code(written) == normalize_code(expected)


def test_multi_argument_lambda(refactorer):
    """Tests lambda with multiple parameters passed as argument."""
    code = textwrap.dedent(
        """
    from functools import reduce
    def calculate():
        total = reduce(lambda a, b: a + b, [1, 2, 3, 4])
    """
    )

    expected = textwrap.dedent(
        """
    from functools import reduce
    def calculate():
        def converted_lambda_4(a, b):
            result = a + b
            return result
        
        total = reduce(converted_lambda_4, [1, 2, 3, 4])
    """
    )

    smell = create_smell([4])()
    with (
        patch.object(Path, "read_text", return_value=code),
        patch.object(Path, "write_text") as mock_write,
    ):

        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))
        written = mock_write.call_args[0][0]
        assert normalize_code(written) == normalize_code(expected)


def test_lambda_with_keyword_arguments(refactorer):
    """Tests lambda used with keyword arguments."""
    code = textwrap.dedent(
        """
    def configure_settings():
        button = Button(
            text="Submit",
            on_click=lambda event: handle_event(event, retries=3)
        )
    """
    )

    expected = textwrap.dedent(
        """
    def configure_settings():
        def converted_lambda_5(event):
            result = handle_event(event, retries=3)
            return result
        
        button = Button(
            text="Submit",
            on_click=converted_lambda_5
        )
    """
    )

    smell = create_smell([5])()
    with (
        patch.object(Path, "read_text", return_value=code),
        patch.object(Path, "write_text") as mock_write,
    ):

        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))
        written = mock_write.call_args[0][0]
        print(written)
        assert normalize_code(written) == normalize_code(expected)


def test_very_long_lambda_function(refactorer):
    """Tests refactoring of a very long lambda function that spans multiple lines."""
    code = textwrap.dedent(
        """
        def calculate():
            value = (
                lambda a, b, c: a + b + c + a * b - c / (a + b) + a - b * c + a**2 - b**2 + a*b + a/(b+c) - c*(a-b) + (a+b+c)
            )(1, 2, 3)
        """
    )

    expected = textwrap.dedent(
        """
        def calculate():
            def converted_lambda_4(a, b, c):
                result = a + b + c + a * b - c / (a + b) + a - b * c + a**2 - b**2 + a*b + a/(b+c) - c*(a-b) + (a+b+c)
                return result

            value = (
                converted_lambda_4
            )(1, 2, 3)
        """
    )

    smell = create_smell([4])()
    with patch.object(Path, "read_text", return_value=code), \
         patch.object(Path, "write_text") as mock_write:
        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))
        written = mock_write.call_args[0][0]
        print(written)
        assert normalize_code(written) == normalize_code(expected)
