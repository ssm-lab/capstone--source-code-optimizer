import pytest
import textwrap
from pathlib import Path
from ecooptimizer.refactorers.concrete.list_comp_any_all import UseAGeneratorRefactorer
from ecooptimizer.data_types import UGESmell, Occurence
from ecooptimizer.utils.smell_enums import PylintSmell


@pytest.fixture
def refactorer():
    return UseAGeneratorRefactorer()


def create_smell(occurences: list[int]):
    """Factory function to create a smell object"""

    def _create():
        return UGESmell(
            path="fake.py",
            module="some_module",
            obj=None,
            type="performance",
            symbol="use-a-generator",
            message="Consider using a generator expression instead of a list comprehension.",
            messageId=PylintSmell.USE_A_GENERATOR.value,
            confidence="INFERENCE",
            occurences=[
                Occurence(
                    line=occ,
                    endLine=occ,
                    column=999,
                    endColumn=999,
                )
                for occ in occurences
            ],
            additionalInfo=None,
        )

    return _create


def test_ugen_basic_all_case(source_files, refactorer):
    """
    Tests basic transformation of list comprehensions in `all()` calls.
    """
    test_dir = Path(source_files, "temp_basic_ugen")
    test_dir.mkdir(exist_ok=True)

    file1 = test_dir / "ugen_def.py"
    file1.write_text(
        textwrap.dedent("""
        def all_non_negative(numbers):
            return all([num >= 0 for num in numbers])
        """)
    )

    smell = create_smell(occurences=[3])()
    refactorer.refactor(file1, test_dir, smell, Path("fake.py"))

    expected_file1 = textwrap.dedent("""
        def all_non_negative(numbers):
            return all(num >= 0 for num in numbers)
        """)

    assert file1.read_text().strip() == expected_file1.strip()


def test_ugen_basic_any_case(source_files, refactorer):
    """
    Tests basic transformation of list comprehensions in `any()` calls.
    """
    test_dir = Path(source_files, "temp_basic_ugen_any")
    test_dir.mkdir(exist_ok=True)

    file1 = test_dir / "ugen_def.py"
    file1.write_text(
        textwrap.dedent("""
        def contains_large_strings(strings):
            return any([len(s) > 10 for s in strings])
        """)
    )

    smell = create_smell(occurences=[3])()
    refactorer.refactor(file1, test_dir, smell, Path("fake.py"))

    expected_file1 = textwrap.dedent("""
        def contains_large_strings(strings):
            return any(len(s) > 10 for s in strings)
        """)

    assert file1.read_text().strip() == expected_file1.strip()


def test_ugen_multiline_comprehension(source_files, refactorer):
    """
    Tests that multi-line list comprehensions inside `any()` or `all()` are refactored correctly.
    """
    test_dir = Path(source_files, "temp_multiline_ugen")
    test_dir.mkdir(exist_ok=True)

    file1 = test_dir / "ugem_def.py"
    file1.write_text(
        textwrap.dedent("""
        def has_long_words(words):
            return any([
                len(word) > 8
                for word in words
            ])
        """)
    )

    smell = create_smell(occurences=[3])()
    refactorer.refactor(file1, test_dir, smell, Path("fake.py"))

    expected_file1 = textwrap.dedent("""
        def has_long_words(words):
            return any(len(word) > 8
                for word in words)
        """)

    assert file1.read_text().strip() == expected_file1.strip()
