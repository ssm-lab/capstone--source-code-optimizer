import ast
import textwrap
from pathlib import Path
from unittest.mock import patch

from ecooptimizer.data_types.smell import LLESmell
from ecooptimizer.analyzers.ast_analyzers.detect_long_lambda_expression import (
    detect_long_lambda_expression,
)


def test_no_lambdas():
    """Ensures no smells are detected when no lambda is present."""
    code = textwrap.dedent(
        """
    def example():
        x = 42
        return x + 1
    """
    )
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_long_lambda_expression(Path("fake.py"), ast.parse(code))
    assert len(smells) == 0


def test_short_single_lambda():
    """
    A single short lambda (well under length=100)
    and only one expression -> should NOT be flagged.
    """
    code = textwrap.dedent(
        """
    def example():
        f = lambda x: x + 1
        return f(5)
    """
    )
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_long_lambda_expression(
            Path("fake.py"),
            ast.parse(code),
        )
    assert len(smells) == 0


def test_lambda_exceeds_expr_count():
    """
    Long lambda due to too many expressions
    In the AST, this breaks down as:
        (x + 1 if x > 0 else 0) -> ast.IfExp (expression #1)
        abs(x) * 2 -> ast.BinOp (Call inside it) (expression #2)
        min(x, 5) -> ast.Call (expression #3)
    """
    code = textwrap.dedent(
        """
    def example():
        func = lambda x: (x + 1 if x > 0 else 0) + (x * 2 if x < 5 else 5) + abs(x)
        return func(4)
    """
    )

    with patch.object(Path, "read_text", return_value=code):
        smells = detect_long_lambda_expression(
            Path("fake.py"),
            ast.parse(code),
        )
    assert len(smells) == 1, "Expected smell due to expression count"
    assert isinstance(smells[0], LLESmell)


def test_lambda_exceeds_char_length():
    """
    Exceeds threshold_length=100 by using a very long expression in the lambda.
    """
    long_str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 4
    code = textwrap.dedent(
        f"""
    def example():
        func = lambda x: x + "{long_str}"
        return func("test")
    """
    )
    # exceeds 100 char
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_long_lambda_expression(
            Path("fake.py"),
            ast.parse(code),
        )
    assert len(smells) == 1, "Expected smell due to character length"
    assert isinstance(smells[0], LLESmell)


def test_lambda_exceeds_both_thresholds():
    """
    Both too many chars and too many expressions
    """
    code = textwrap.dedent(
        """
    def example():
        giant_lambda = lambda a, b, c: (a + b if a > b else b - c) + (max(a, b, c) * 10) + (min(a, b, c) / 2) + ("hello" + "world") 
        return giant_lambda(1,2,3)
    """
    )
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_long_lambda_expression(
            Path("fake.py"),
            ast.parse(code),
        )
    # one smell per line
    assert len(smells) >= 1
    assert all(isinstance(smell, LLESmell) for smell in smells)


def test_lambda_nested():
    """
    Nested lambdas inside one function.
    # outer and inner detected
    """
    code = textwrap.dedent(
        """
    def example():
        outer = lambda x: (x ** 2) + (lambda y: y + 10)(x)
        # inner = lambda y: y + 10 is short, but let's make it long
        # We'll artificially make it a big expression
        inner = lambda a, b: (a + b if a > 0 else 0) + (a * b) + (b - a)
        return outer(5) + inner(3,4)
    """
    )
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_long_lambda_expression(
            Path("fake.py"), ast.parse(code), threshold_length=80, threshold_count=3
        )
    # inner and outter
    assert len(smells) == 2
    assert isinstance(smells[0], LLESmell)


def test_lambda_inline_passed_to_function():
    """
    Lambdas passed inline to a function: sum(map(...)) or filter(..., lambda).
    """
    code = textwrap.dedent(
        """
    def test_lambdas():
        result = map(lambda x: x*2 + (x//3) if x > 10 else x, range(20))

        # This lambda has a ternary, but let's keep it short enough 
        # that it doesn't trigger by default unless threshold_count=2 or so.
        # We'll push it with a second ternary + more code to reach threshold_count=3

        result2 = filter(lambda z: (z+1 if z < 5 else z-1) + (z*3 if z%2==0 else z/2) and z != 0, result)
        
        return list(result2)
    """
    )

    with patch.object(Path, "read_text", return_value=code):
        smells = detect_long_lambda_expression(Path("fake.py"), ast.parse(code))
    # 2 smells
    assert len(smells) == 2
    assert all(isinstance(smell, LLESmell) for smell in smells)


def test_lambda_no_body_too_short():
    """
    A degenerate case: a lambda that has no real body or is trivially short.
    Should produce 0 smells even if it's spread out.
    """
    code = textwrap.dedent(
        """
    def example():
        trivial = lambda: None
        return trivial()
    """
    )
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_long_lambda_expression(Path("fake.py"), ast.parse(code))
    assert len(smells) == 0
