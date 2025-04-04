import textwrap
from pathlib import Path
from ast import parse
from unittest.mock import patch
from ecooptimizer.data_types.smell import CRCSmell
from ecooptimizer.analyzers.ast_analyzers.detect_repeated_calls import (
    detect_repeated_calls,
)


def run_detection_test(code: str):
    with patch.object(Path, "read_text", return_value=code):
        return detect_repeated_calls(Path("fake.py"), parse(code))


def test_detects_repeated_function_call():
    """Detects repeated function calls within the same scope."""
    code = textwrap.dedent("""
        def test_case():
            result1 = expensive_function(42)
            result2 = expensive_function(42)
    """)
    smells = run_detection_test(code)

    assert len(smells) == 1
    assert isinstance(smells[0], CRCSmell)
    assert len(smells[0].occurences) == 2
    assert smells[0].additionalInfo.callString == "expensive_function(42)"


def test_detects_repeated_method_call():
    """Detects repeated method calls on the same object instance."""
    code = textwrap.dedent("""
    class Demo:
        def compute(self):
            return 42
    def test_case():
        obj = Demo()
        result1 = obj.compute()
        result2 = obj.compute()
    """)
    smells = run_detection_test(code)

    assert len(smells) == 1
    assert isinstance(smells[0], CRCSmell)
    assert len(smells[0].occurences) == 2
    assert smells[0].additionalInfo.callString == "obj.compute()"


def test_ignores_different_arguments():
    """Ensures repeated function calls with different arguments are NOT flagged."""
    code = textwrap.dedent("""
    def test_case():
        result1 = expensive_function(1)
        result2 = expensive_function(2)
    """)
    smells = run_detection_test(code)
    assert len(smells) == 0


def test_ignores_modified_objects():
    """Ensures function calls on modified objects are NOT flagged."""
    code = textwrap.dedent("""
    class Demo:
        def compute(self):
            return self.value * 2
    def test_case():
        obj = Demo()
        obj.value = 10
        result1 = obj.compute()
        obj.value = 20
        result2 = obj.compute()
    """)
    smells = run_detection_test(code)
    assert len(smells) == 0


def test_detects_repeated_external_call():
    """Detects repeated external function calls (e.g., len(data.get("key")))."""
    code = textwrap.dedent("""
    def test_case(data):
        result = len(data.get("key"))
        repeated = len(data.get("key"))
    """)
    smells = run_detection_test(code)

    assert len(smells) == 1
    assert isinstance(smells[0], CRCSmell)
    assert len(smells[0].occurences) == 2
    assert smells[0].additionalInfo.callString == 'len(data.get("key"))'


def test_detects_expensive_builtin_call():
    """Detects repeated calls to expensive built-in functions like max()."""
    code = textwrap.dedent("""
    def test_case(data):
        result1 = max(data)
        result2 = max(data)
    """)
    smells = run_detection_test(code)

    assert len(smells) == 1
    assert isinstance(smells[0], CRCSmell)
    assert len(smells[0].occurences) == 2
    assert smells[0].additionalInfo.callString == "max(data)"


def test_ignores_primitive_builtins():
    """Ensures built-in functions like abs() are NOT flagged when used with primitives."""
    code = textwrap.dedent("""
    def test_case():
        result1 = abs(-5)
        result2 = abs(-5)
    """)
    smells = run_detection_test(code)
    assert len(smells) == 0


def test_detects_repeated_method_call_with_different_objects():
    """Ensures method calls on different objects are NOT flagged."""
    code = textwrap.dedent("""
    class Demo:
        def compute(self):
            return self.value * 2
    def test_case():
        obj1 = Demo()
        obj2 = Demo()
        result1 = obj1.compute()
        result2 = obj2.compute()
    """)
    smells = run_detection_test(code)
    assert len(smells) == 0
