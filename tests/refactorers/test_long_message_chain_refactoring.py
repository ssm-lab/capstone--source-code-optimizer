import pytest
import textwrap
from unittest.mock import patch
from pathlib import Path

from ecooptimizer.refactorers.concrete.long_message_chain import (
    LongMessageChainRefactorer,
)
from ecooptimizer.data_types import Occurence, LMCSmell
from ecooptimizer.utils.smell_enums import CustomSmell


@pytest.fixture
def refactorer():
    return LongMessageChainRefactorer()


def create_smell(occurences: list[int]):
    """Factory function to create a smell object for long message chains."""

    def _create():
        return LMCSmell(
            path="fake.py",
            module="some_module",
            obj=None,
            type="convention",
            symbol="long-message-chain",
            message="Method chain too long",
            messageId=CustomSmell.LONG_MESSAGE_CHAIN.value,
            confidence="UNDEFINED",
            occurences=[
                Occurence(line=occ, endLine=999, column=999, endColumn=999)
                for occ in occurences
            ],
            additionalInfo=None,
        )

    return _create


def test_basic_method_chain_refactoring(refactorer):
    """Tests refactoring of a basic method chain."""
    code = textwrap.dedent(
        """
        def example():
            text = "Hello"
            result = text.strip().lower().replace("|", "-").title()
        """
    )
    expected_code = textwrap.dedent(
        """
        def example():
            text = "Hello"
            intermediate_0 = text.strip()
            intermediate_1 = intermediate_0.lower()
            intermediate_2 = intermediate_1.replace("|", "-")
            result = intermediate_2.title()
        """
    )

    smell = create_smell([4])()
    with (
        patch.object(Path, "read_text", return_value=code),
        patch.object(Path, "write_text") as mock_write_text,
    ):
        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))

    mock_write_text.assert_called_once()
    written_code = mock_write_text.call_args[0][0]
    assert written_code.strip() == expected_code.strip()


def test_fstring_chain_refactoring(refactorer):
    """Tests refactoring of a long message chain with an f-string."""
    code = textwrap.dedent(
        """
        def example():
            name = "John"
            greeting = f"Hello {name}".strip().replace(" ", "-").upper()
        """
    )
    expected_code = textwrap.dedent(
        """
        def example():
            name = "John"
            intermediate_0 = f"Hello {name}"
            intermediate_1 = intermediate_0.strip()
            intermediate_2 = intermediate_1.replace(" ", "-")
            greeting = intermediate_2.upper()
        """
    )

    smell = create_smell([4])()
    with (
        patch.object(Path, "read_text", return_value=code),
        patch.object(Path, "write_text") as mock_write_text,
    ):
        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))

    mock_write_text.assert_called_once()
    written_code = mock_write_text.call_args[0][0]
    assert written_code.strip() == expected_code.strip()


def test_modifications_if_no_long_chain(refactorer):
    """Ensures modifications occur even if the method chain isnt long."""
    code = textwrap.dedent(
        """
        def example():
            text = "Hello"
            result = text.strip().lower()
        """
    )

    expected_code = textwrap.dedent(
        """
        def example():
            text = "Hello"
            intermediate_0 = text.strip()
            result = intermediate_0.lower()
        """
    )

    smell = create_smell([4])()
    with (
        patch.object(Path, "read_text", return_value=code),
        patch.object(Path, "write_text") as mock_write_text,
    ):
        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))

    mock_write_text.assert_called_once()
    written_code = mock_write_text.call_args[0][0]
    assert written_code.strip() == expected_code.strip()


def test_proper_indentation_preserved(refactorer):
    """Ensures indentation is preserved after refactoring."""
    code = textwrap.dedent(
        """
        def example():
            if True:
                text = "Hello"
                result = text.strip().lower().replace("|", "-").title()
        """
    )
    expected_code = textwrap.dedent(
        """
        def example():
            if True:
                text = "Hello"
                intermediate_0 = text.strip()
                intermediate_1 = intermediate_0.lower()
                intermediate_2 = intermediate_1.replace("|", "-")
                result = intermediate_2.title()
        """
    )

    smell = create_smell([5])()
    with (
        patch.object(Path, "read_text", return_value=code),
        patch.object(Path, "write_text") as mock_write_text,
    ):
        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))

    mock_write_text.assert_called_once()
    written_code = mock_write_text.call_args[0][0]
    print(written_code, "\n")
    assert written_code.splitlines() == expected_code.splitlines()


def test_method_chain_with_arguments(refactorer):
    """Tests refactoring of method chains containing method arguments."""
    code = textwrap.dedent(
        """
        def example():
            text = "Hello"
            result = text.strip().replace("H", "J").lower().title()
        """
    )
    expected_code = textwrap.dedent(
        """
        def example():
            text = "Hello"
            intermediate_0 = text.strip()
            intermediate_1 = intermediate_0.replace("H", "J")
            intermediate_2 = intermediate_1.lower()
            result = intermediate_2.title()
        """
    )

    smell = create_smell([4])()
    with (
        patch.object(Path, "read_text", return_value=code),
        patch.object(Path, "write_text") as mock_write,
    ):

        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))

        written = mock_write.call_args[0][0]
        assert written.strip() == expected_code.strip()


def test_print_statement_preservation(refactorer):
    """Tests refactoring of print statements with method chains."""
    code = textwrap.dedent(
        """
        def example():
            text = "Hello"
            print(text.strip().lower().title())
        """
    )
    expected_code = textwrap.dedent(
        """
        def example():
            text = "Hello"
            intermediate_0 = text.strip()
            intermediate_1 = intermediate_0.lower()
            print(intermediate_1.title())
        """
    )

    smell = create_smell([4])()
    with (
        patch.object(Path, "read_text", return_value=code),
        patch.object(Path, "write_text") as mock_write,
    ):

        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))

        written = mock_write.call_args[0][0]
        assert written.strip() == expected_code.strip()


def test_nested_method_chains(refactorer):
    """Tests refactoring of nested method chains."""
    code = textwrap.dedent(
        """
        def example():
            result = get_object().config().settings().load()
        """
    )
    expected_code = textwrap.dedent(
        """
        def example():
            intermediate_0 = get_object()
            intermediate_1 = intermediate_0.config()
            intermediate_2 = intermediate_1.settings()
            result = intermediate_2.load()
        """
    )

    smell = create_smell([3])()
    with (
        patch.object(Path, "read_text", return_value=code),
        patch.object(Path, "write_text") as mock_write,
    ):

        refactorer.refactor(Path("fake.py"), Path("fake.py"), smell, Path("fake.py"))

        written = mock_write.call_args[0][0]
        assert written.strip() == expected_code.strip()
