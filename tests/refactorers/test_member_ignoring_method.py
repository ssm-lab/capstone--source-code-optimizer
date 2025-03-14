import pytest

import textwrap
from pathlib import Path

from ecooptimizer.refactorers.concrete.member_ignoring_method import MakeStaticRefactorer
from ecooptimizer.data_types import MIMSmell, Occurence
from ecooptimizer.utils.smell_enums import PylintSmell


@pytest.fixture
def refactorer():
    return MakeStaticRefactorer()


def create_smell(occurences: list[int], obj: str):
    """Factory function to create a smell object"""

    def _create():
        return MIMSmell(
            path="fake.py",
            module="some_module",
            obj=obj,
            type="refactor",
            symbol="no-self-use",
            message="Method could be a function",
            messageId=PylintSmell.NO_SELF_USE.value,
            confidence="INFERENCE",
            occurences=[
                Occurence(
                    line=occ,
                    endLine=999,
                    column=999,
                    endColumn=999,
                )
                for occ in occurences
            ],
            additionalInfo=None,
        )

    return _create


def test_mim_basic_case(source_files, refactorer):
    """
    Tests that the member ignoring method refactorer:
    - Adds @staticmethod decorator.
    - Removes 'self' from method signature.
    - Updates calls in external files.
    """

    # --- File 1: Defines the method ---
    test_dir = Path(source_files, "temp_basic_mim")
    test_dir.mkdir(exist_ok=True)

    file1 = test_dir / "class_def.py"
    file1.write_text(
        textwrap.dedent("""\
    class Example:
        def __init__(self):
            self.attr = "something"
        def mim_method(self, x):
            return x * 2

    example = Example()
    num = example.mim_method(5)
    """)
    )

    # --- File 2: Calls the method ---
    file2 = test_dir / "caller.py"
    file2.write_text(
        textwrap.dedent("""\
    from .class_def import Example
    example = Example()
    result = example.mim_method(5)
    """)
    )

    smell = create_smell(occurences=[4], obj="Example.mim_method")()

    refactorer.refactor(file1, test_dir, smell, Path("fake.py"))

    # --- Expected Result for File 1 ---
    expected_file1 = textwrap.dedent("""\
    class Example:
        def __init__(self):
            self.attr = "something"
        @staticmethod
        def mim_method(x):
            return x * 2

    example = Example()
    num = Example.mim_method(5)
    """)

    # --- Expected Result for File 2 ---
    expected_file2 = textwrap.dedent("""\
    from .class_def import Example
    example = Example()
    result = Example.mim_method(5)
    """)

    # Check if the refactoring worked
    assert file1.read_text().strip() == expected_file1.strip()
    assert file2.read_text().strip() == expected_file2.strip()


def test_mim_inheritence_case(source_files, refactorer):
    """
    Tests that calls originating from a subclass instance are also refactored.
    """

    # --- File 1: Defines the method ---
    test_dir = Path(source_files, "temp_inherited_mim")
    test_dir.mkdir(exist_ok=True)

    file1 = test_dir / "class_def.py"
    file1.write_text(
        textwrap.dedent("""\
    class Example:
        def __init__(self):
            self.attr = "something"
        def mim_method(self, x):
            return x * 2

    class SubExample(Example):
         pass

    example = SubExample()
    num = example.mim_method(5)
    """)
    )

    # --- File 2: Calls the method ---
    file2 = test_dir / "caller.py"
    file2.write_text(
        textwrap.dedent("""\
    from .class_def import SubExample
    example = SubExample()
    result = example.mim_method(5)
    """)
    )

    smell = create_smell(occurences=[4], obj="Example.mim_method")()

    refactorer.refactor(file1, test_dir, smell, Path("fake.py"))

    # --- Expected Result for File 1 ---
    expected_file1 = textwrap.dedent("""\
    class Example:
        def __init__(self):
            self.attr = "something"
        @staticmethod
        def mim_method(x):
            return x * 2

    class SubExample(Example):
         pass

    example = SubExample()
    num = SubExample.mim_method(5)
    """)

    # --- Expected Result for File 2 ---
    expected_file2 = textwrap.dedent("""\
    from .class_def import SubExample
    example = SubExample()
    result = SubExample.mim_method(5)
    """)

    # Check if the refactoring worked
    assert file1.read_text().strip() == expected_file1.strip()
    assert file2.read_text().strip() == expected_file2.strip()


def test_mim_inheritence_seperate_subclass(source_files, refactorer):
    """
    Tests that subclasses declared in files other than the initial one are detected.
    """

    # --- File 1: Defines the method ---
    test_dir = Path(source_files, "temp_inherited_ss_mim")
    test_dir.mkdir(exist_ok=True)

    file1 = test_dir / "class_def.py"
    file1.write_text(
        textwrap.dedent("""\
    class Example:
        def __init__(self):
            self.attr = "something"
        def mim_method(self, x):
            return x * 2

    example = Example()
    num = example.mim_method(5)
    """)
    )

    # --- File 2: Calls the method ---
    file2 = test_dir / "caller.py"
    file2.write_text(
        textwrap.dedent("""\
    from .class_def import Example

    class SubExample(Example):
         pass

    example = SubExample()
    result = example.mim_method(5)
    """)
    )

    smell = create_smell(occurences=[4], obj="Example.mim_method")()

    refactorer.refactor(file1, test_dir, smell, Path("fake.py"))

    # --- Expected Result for File 1 ---
    expected_file1 = textwrap.dedent("""\
    class Example:
        def __init__(self):
            self.attr = "something"
        @staticmethod
        def mim_method(x):
            return x * 2

    example = Example()
    num = Example.mim_method(5)
    """)

    # --- Expected Result for File 2 ---
    expected_file2 = textwrap.dedent("""\
    from .class_def import Example

    class SubExample(Example):
         pass

    example = SubExample()
    result = SubExample.mim_method(5)
    """)

    # Check if the refactoring worked
    assert file1.read_text().strip() == expected_file1.strip()
    assert file2.read_text().strip() == expected_file2.strip()


def test_mim_inheritence_subclass_method_override(source_files, refactorer):
    """
    Tests that calls to the mim method from subclass instance with method override are NOT changed.
    """

    # --- File 1: Defines the method ---
    test_dir = Path(source_files, "temp_inherited_override_mim")
    test_dir.mkdir(exist_ok=True)

    file1 = test_dir / "class_def.py"
    file1.write_text(
        textwrap.dedent("""\
    class Example:
        def __init__(self):
            self.attr = "something"
        def mim_method(self, x):
            return x * 2

    class SubExample(Example):
         def mim_method(self, x):
            return x * 3

    example = Example()
    num = example.mim_method(5)
    """)
    )

    # --- File 2: Calls the method ---
    file2 = test_dir / "caller.py"
    file2.write_text(
        textwrap.dedent("""\
    from .class_def import SubExample
    example = SubExample()
    result = example.mim_method(5)
    """)
    )

    smell = create_smell(occurences=[4], obj="Example.mim_method")()

    refactorer.refactor(file1, test_dir, smell, Path("fake.py"))

    # --- Expected Result for File 1 ---
    expected_file1 = textwrap.dedent("""\
    class Example:
        def __init__(self):
            self.attr = "something"
        @staticmethod
        def mim_method(x):
            return x * 2

    class SubExample(Example):
         def mim_method(self, x):
            return x * 3

    example = Example()
    num = Example.mim_method(5)
    """)

    # --- Expected Result for File 2 ---
    expected_file2 = textwrap.dedent("""\
    from .class_def import SubExample
    example = SubExample()
    result = example.mim_method(5)
    """)

    # Check if the refactoring worked
    assert file1.read_text().strip() == expected_file1.strip()
    assert file2.read_text().strip() == expected_file2.strip()


def test_mim_type_hint_inferrence(source_files, refactorer):
    """
    Tests that type hints declaring and instance type are detected.
    """

    # --- File 1: Defines the method ---
    test_dir = Path(source_files, "temp_mim_type_hint_mim")
    test_dir.mkdir(exist_ok=True)

    file1 = test_dir / "class_def.py"
    file1.write_text(
        textwrap.dedent("""\
    class Example:
        def __init__(self):
            self.attr = "something"
        def mim_method(self, x):
            return x * 2

    def test(example: Example):
        print(example.mim_method(3))

    example = Example()
    num = example.mim_method(5)
    """)
    )

    smell = create_smell(occurences=[4], obj="Example.mim_method")()

    refactorer.refactor(file1, test_dir, smell, Path("fake.py"))

    # --- Expected Result for File 1 ---
    expected_file1 = textwrap.dedent("""\
    class Example:
        def __init__(self):
            self.attr = "something"
        @staticmethod
        def mim_method(x):
            return x * 2

    def test(example: Example):
        print(Example.mim_method(3))

    example = Example()
    num = Example.mim_method(5)
    """)

    # Check if the refactoring worked
    assert file1.read_text().strip() == expected_file1.strip()
