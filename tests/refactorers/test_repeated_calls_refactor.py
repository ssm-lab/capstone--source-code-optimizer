import pytest
import textwrap
from pathlib import Path
from ecooptimizer.refactorers.concrete.repeated_calls import CacheRepeatedCallsRefactorer
from ecooptimizer.data_types import CRCSmell, Occurence, CRCInfo


@pytest.fixture
def refactorer():
    return CacheRepeatedCallsRefactorer()


def create_smell(occurences: list[dict[str, int]], call_string: str, repetitions: int):
    """Factory function to create a CRCSmell object with accurate metadata."""

    def _create():
        return CRCSmell(
            path="fake.py",
            module="some_module",
            obj=None,
            type="performance",
            symbol="cached-repeated-calls",
            message=f"Repeated function call detected ({repetitions}/{repetitions}). Consider caching the result: {call_string}",
            messageId="CRC001",
            confidence="HIGH" if repetitions > 2 else "MEDIUM",
            occurences=[
                Occurence(
                    line=occ["line"],
                    endLine=occ["endLine"],
                    column=occ["column"],
                    endColumn=occ["endColumn"],
                )
                for occ in occurences
            ],
            additionalInfo=CRCInfo(
                repetitions=repetitions,
                callString=call_string,
            ),
        )

    return _create


def test_crc_basic_case(source_files, refactorer):
    """
    Tests that repeated function calls are cached properly.
    """
    test_dir = Path(source_files, "temp_crc_basic")
    test_dir.mkdir(exist_ok=True)

    file1 = test_dir / "crc_def.py"
    file1.write_text(
        textwrap.dedent("""
        def expensive_function(x):
            return x * x

        def test_case():
            result1 = expensive_function(42)
            result2 = expensive_function(42)
            result3 = expensive_function(42)
            return result1 + result2 + result3
        """)
    )

    smell = create_smell(
        occurences=[
            {"line": 6, "endLine": 6, "column": 14, "endColumn": 38},
            {"line": 7, "endLine": 7, "column": 14, "endColumn": 38},
            {"line": 8, "endLine": 8, "column": 14, "endColumn": 38},
        ],
        call_string="expensive_function(42)",
        repetitions=3,
    )()
    refactorer.refactor(file1, test_dir, smell, Path("fake.py"))

    expected_file1 = textwrap.dedent("""
        def expensive_function(x):
            return x * x

        def test_case():
            cached_expensive_function = expensive_function(42)
            result1 = cached_expensive_function
            result2 = cached_expensive_function
            result3 = cached_expensive_function
            return result1 + result2 + result3
        """)

    assert file1.read_text().strip() == expected_file1.strip()


def test_crc_method_calls(source_files, refactorer):
    """
    Tests that repeated method calls on an object are cached properly.
    """
    test_dir = Path(source_files, "temp_crc_method")
    test_dir.mkdir(exist_ok=True)

    file1 = test_dir / "crc_def.py"
    file1.write_text(
        textwrap.dedent("""
        class Demo:
            def __init__(self, value):
                self.value = value
            def compute(self):
                return self.value * 2

        def test_case():
            obj = Demo(3)
            result1 = obj.compute()
            result2 = obj.compute()
            return result1 + result2
        """)
    )

    smell = create_smell(
        occurences=[
            {"line": 10, "endLine": 10, "column": 14, "endColumn": 28},
            {"line": 11, "endLine": 11, "column": 14, "endColumn": 28},
        ],
        call_string="obj.compute()",
        repetitions=2,
    )()
    refactorer.refactor(file1, test_dir, smell, Path("fake.py"))

    expected_file1 = textwrap.dedent("""
        class Demo:
            def __init__(self, value):
                self.value = value
            def compute(self):
                return self.value * 2

        def test_case():
            obj = Demo(3)
            cached_obj_compute = obj.compute()
            result1 = cached_obj_compute
            result2 = cached_obj_compute
            return result1 + result2
        """)

    assert file1.read_text().strip() == expected_file1.strip()


def test_crc_instance_method_repeated(source_files, refactorer):
    """
    Tests that repeated method calls on the same object instance are cached.
    """
    test_dir = Path(source_files, "temp_crc_instance_method")
    test_dir.mkdir(exist_ok=True)

    file1 = test_dir / "crc_def.py"
    file1.write_text(
        textwrap.dedent("""
        class Demo:
            def __init__(self, value):
                self.value = value
            def compute(self):
                return self.value * 2

        def test_case():
            demo1 = Demo(1)
            demo2 = Demo(2)
            result1 = demo1.compute()
            result2 = demo2.compute()
            result3 = demo1.compute()
            return result1 + result2 + result3
        """)
    )

    smell = create_smell(
        occurences=[
            {"line": 11, "endLine": 11, "column": 14, "endColumn": 28},
            {"line": 13, "endLine": 13, "column": 14, "endColumn": 28},
        ],
        call_string="demo1.compute()",
        repetitions=2,
    )()
    refactorer.refactor(file1, test_dir, smell, Path("fake.py"))

    expected_file1 = textwrap.dedent("""
        class Demo:
            def __init__(self, value):
                self.value = value
            def compute(self):
                return self.value * 2

        def test_case():
            demo1 = Demo(1)
            cached_demo1_compute = demo1.compute()
            demo2 = Demo(2)
            result1 = cached_demo1_compute
            result2 = demo2.compute()
            result3 = cached_demo1_compute
            return result1 + result2 + result3
        """)

    assert file1.read_text().strip() == expected_file1.strip()


def test_crc_with_docstrigs(source_files, refactorer):
    """
    Tests that repeated function calls are cached properly when docstrings present.
    """
    test_dir = Path(source_files, "temp_crc_docstring")
    test_dir.mkdir(exist_ok=True)

    file1 = test_dir / "crc_def.py"
    file1.write_text(
        textwrap.dedent('''
        def expensive_function(x):
            return x * x

        def test_case():
            """
            Example docstring
            """
            result1 = expensive_function(100)
            result2 = expensive_function(100)
            result3 = expensive_function(42)
            return result1 + result2 + result3
        ''')
    )

    smell = create_smell(
        occurences=[
            {"line": 9, "endLine": 9, "column": 14, "endColumn": 38},
            {"line": 10, "endLine": 10, "column": 14, "endColumn": 38},
            {"line": 11, "endLine": 11, "column": 14, "endColumn": 38},
        ],
        call_string="expensive_function(100)",
        repetitions=3,
    )()
    refactorer.refactor(file1, test_dir, smell, Path("fake.py"))

    expected_file1 = textwrap.dedent('''
        def expensive_function(x):
            return x * x

        def test_case():
            """
            Example docstring
            """
            cached_expensive_function = expensive_function(100)
            result1 = cached_expensive_function
            result2 = cached_expensive_function
            result3 = expensive_function(42)
            return result1 + result2 + result3
        ''')

    assert file1.read_text().strip() == expected_file1.strip()
