import ast
import textwrap
from pathlib import Path
from unittest.mock import patch

from ecooptimizer.data_types.smell import LMCSmell
from ecooptimizer.analyzers.ast_analyzers.detect_long_message_chain import (
    detect_long_message_chain,
)

# NOTE: The default threshold is 5. That means a chain of 5 or more consecutive calls will be flagged.


def test_detects_exact_five_calls_chain():
    """Detects a chain with exactly five method calls."""
    code = textwrap.dedent(
        """
    def example():
        details = "some text"
        details.upper().lower().capitalize().replace("|", "-").strip()
    """
    )

    # This chain has 5 calls: upper -> lower -> capitalize -> replace -> strip
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_long_message_chain(Path("fake.py"), ast.parse(code))

    assert len(smells) == 1, "Expected exactly one smell for a chain of length 5"
    assert isinstance(smells[0], LMCSmell)
    assert "Method chain too long" in smells[0].message
    assert smells[0].occurences[0].line == 4


def test_detects_six_calls_chain():
    """Detects a chain with six method calls, definitely flagged."""
    code = textwrap.dedent(
        """
    def example():
        details = "some text"
        details.upper().lower().upper().capitalize().upper().replace("|", "-")
    """
    )

    # This chain has 6 calls: upper -> lower -> upper -> capitalize -> upper -> replace
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_long_message_chain(Path("fake.py"), ast.parse(code))

    assert len(smells) == 1, "Expected exactly one smell for a chain of length 6"
    assert isinstance(smells[0], LMCSmell)
    assert "Method chain too long" in smells[0].message
    assert smells[0].occurences[0].line == 4


def test_ignores_chain_of_four_calls():
    """Ensures a chain with only four calls is NOT flagged (below threshold)."""
    code = textwrap.dedent(
        """
    def example():
        text = "some-other"
        text.strip().lower().replace("-", "_").title()
    """
    )

    # This chain has 4 calls: strip -> lower -> replace -> title
    # The default threshold is 5, so it should not be detected.
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_long_message_chain(Path("fake.py"), ast.parse(code))

    assert len(smells) == 0, "Chain of length 4 should NOT be flagged"


def test_detects_chain_with_attributes_and_calls():
    """Detects a long chain that involves both attribute and method calls."""
    code = textwrap.dedent(
        """
    class Sample:
        def __init__(self):
            self.details = "some text".upper()
        def method(self):
            # below is a chain with 5 steps:
            # self.details -> lower() -> capitalize() -> isalpha() -> bit_length()
            # isalpha() returns bool, bit_length() is from int => means chain length is still counted.
            return self.details.upper().lower().capitalize().isalpha().bit_length()
    """
    )

    with patch.object(Path, "read_text", return_value=code):
        smells = detect_long_message_chain(Path("fake.py"), ast.parse(code))

    # Because we have 5 method calls, it should be flagged.
    assert len(smells) == 1, "Expected one smell for chain of length >= 5"
    assert isinstance(smells[0], LMCSmell)


def test_detects_chain_inside_loop():
    """Detects a chain inside a loop that meets the threshold."""
    code = textwrap.dedent(
        """
    def loop_chain(data_list):
        for item in data_list:
            item.strip().replace("-", "_").split("_").index("some")
    """
    )

    # Calls: strip -> replace -> split -> index = 4 calls total.
    # add to 5
    code = code.replace('index("some")', 'index("some").upper()')

    with patch.object(Path, "read_text", return_value=code):
        smells = detect_long_message_chain(Path("fake.py"), ast.parse(code))

    assert len(smells) == 1, "Expected smell for chain length 5"
    assert isinstance(smells[0], LMCSmell)


def test_multiple_chains_one_line():
    """Detect multiple separate long chains on the same line. Should only report 1 smell, the first chain"""
    code = textwrap.dedent(
        """
    def combo():
        details = "some text"
        other = "other text"
        details.lower().title().replace("|", "-").upper().split("-"); other.upper().lower().capitalize().zfill(10).replace("xyz", "abc")
    """
    )

    # On line 5, we have two separate chains:
    # 1) details -> lower -> title -> replace -> upper -> split => 5 calls.
    # 2) other -> upper -> lower -> capitalize -> zfill -> replace => 5 calls.

    with patch.object(Path, "read_text", return_value=code):
        smells = detect_long_message_chain(Path("fake.py"), ast.parse(code))

    # The function logic says it only reports once per line. So we expect 1 smell, not 2.
    assert len(smells) == 1, "Both chains on the same line => single smell reported"
    assert "Method chain too long" in smells[0].message


def test_ignores_separate_statements():
    """Ensures that separate statements with fewer calls each are not combined into one chain."""
    code = textwrap.dedent(
        """
    def example():
        details = "some-other"
        data = details.upper()
        data = data.lower()
        data = data.capitalize()
        data = data.replace("|", "-")
        data = data.title()
    """
    )

    # Each statement individually has only 1 call.
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_long_message_chain(Path("fake.py"), ast.parse(code))

    assert len(smells) == 0, "No single chain of length >= 5 in separate statements"


def test_ignores_short_chain_comprehension():
    """Ensures short chain in a comprehension doesn't get flagged."""
    code = textwrap.dedent(
        """
    def short_comp(lst):
        return [item.replace("-", "_").lower() for item in lst]
    """
    )

    # Only 2 calls in the chain: replace -> lower.
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_long_message_chain(Path("fake.py"), ast.parse(code))

    assert len(smells) == 0


def test_detects_long_chain_comprehension():
    """Detects a long chain in a list comprehension."""
    code = textwrap.dedent(
        """
    def long_comp(lst):
        return [item.upper().lower().capitalize().strip().replace("|", "-") for item in lst]
    """
    )

    # 5 calls in the chain: upper -> lower -> capitalize -> strip -> replace.
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_long_message_chain(Path("fake.py"), ast.parse(code))

    assert len(smells) == 1, "Expected one smell for chain of length 5"
    assert isinstance(smells[0], LMCSmell)


def test_five_separate_long_chains():
    """
    Five distinct lines in a single function, each with a chain of exactly 5 calls.
    Expect 5 separate smells (assuming you record each line).
    """
    code = textwrap.dedent(
        """
    def combo():
        data = "text"
        data.upper().lower().capitalize().replace("|", "-").split("|")
        data.capitalize().replace("|", "-").strip().upper().title()
        data.lower().upper().replace("|", "-").strip().title()
        data.strip().replace("|", "_").split("_").capitalize().title()
        data.replace("|", "-").upper().lower().capitalize().title()
    """
    )

    with patch.object(Path, "read_text", return_value=code):
        smells = detect_long_message_chain(Path("fake.py"), ast.parse(code))

    assert len(smells) == 5, "Expected 5 smells"
    assert isinstance(smells[0], LMCSmell)


def test_element_access_chain_no_calls():
    """
    A chain of attributes and index lookups only, no parentheses (no actual calls).
    Some detectors won't flag this unless they specifically count attribute hops.
    """
    code = textwrap.dedent(
        """
    def get_nested(nested):
        return nested.a.b.c[3][0].x.y
    """
    )

    with patch.object(Path, "read_text", return_value=code):
        smells = detect_long_message_chain(Path("fake.py"), ast.parse(code))

    assert len(smells) == 0, "Expected 0 smells"


def test_chain_with_slicing():
    """
    Demonstrates slicing as part of the chain.
    e.g. `text[2:7]` -> `.replace()` -> `.upper()` ...
    """
    code = textwrap.dedent(
        """
    def slice_chain(text):
        return text[2:7].replace("abc", "xyz").upper().strip().split("-").lower()
    """
    )

    with patch.object(Path, "read_text", return_value=code):
        smells = detect_long_message_chain(Path("fake.py"), ast.parse(code))

    assert len(smells) == 1, "Expected 1 smells"


def test_multiline_chain():
    """
    A chain split over multiple lines using parentheses or backslash.
    The AST should still see them as a continuous chain of calls.
    """
    code = textwrap.dedent(
        """
    def multiline_chain():
        var = "some text"\\
            .replace(" ", "-")\\
            .lower()\\
            .title()\\
            .strip()\\
            .upper()
    """
    )

    with patch.object(Path, "read_text", return_value=code):
        smells = detect_long_message_chain(Path("fake.py"), ast.parse(code))

    assert len(smells) == 1, "Expected 1 smells"


def test_chain_in_lambda():
    """
    A chain inside a lambda's body.
    """
    code = textwrap.dedent(
        """
    def lambda_test():
        func = lambda x: x.upper().strip().replace("-", "_").lower().title()
        return func("HELLO-WORLD")
    """
    )
    # That’s 5 calls: upper -> strip -> replace -> lower -> title
    # Expect 1 chain smell if you're scanning inside lambda bodies.
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_long_message_chain(Path("fake.py"), ast.parse(code))

    assert len(smells) == 1, "Expected 1 smells"


def test_mixed_return_types_chain():
    """
    It's 5 calls, with type changes from str to bool to int.
    Typical 'chain detection' doesn't care about type.
    """
    code = textwrap.dedent(
        """
    class TypeMix:
        def do_stuff(self):
            text = "Hello"
            return text.lower().capitalize().isalpha().bit_length().to_bytes(2, 'big')
    """
    )
    # That’s 5 calls: lower -> capitalize -> isalpha -> bit_length -> to_bytes
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_long_message_chain(Path("fake.py"), ast.parse(code))

    assert len(smells) == 1, "Expected 1 smells"


def test_multiple_short_chains_same_line():
    """
    Two short chains on the same line, each with 3 calls, but they're separate.
    They should not combine into 6, so likely 0 smells if threshold=5.
    """
    code = textwrap.dedent(
        """
    def short_line():
        x = "abc"
        y = "def"
        x.upper().replace("A", "Z").strip(); y.lower().replace("d", "x").title()
    """
    )
    # Each chain is 3 calls, so if threshold is 5, expect 0 smells.
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_long_message_chain(Path("fake.py"), ast.parse(code))

    assert len(smells) == 0, "Expected 0 smells"


def test_conditional_chain():
    """
    A chain inside an inline if/else expression (ternary).
    The question: do we see it as a single chain? Usually yes, but only if we actually parse it as an ast.Call chain.
    """
    code = textwrap.dedent(
        """
    def cond_chain(cond):
        text = "some text"
        return (text.lower().replace(" ", "_").strip().upper() if cond
                else text.upper().replace(" ", "|").lower().split("|"))
    """
    )
    # code shouldnt lump them together
    with patch.object(Path, "read_text", return_value=code):
        smells = detect_long_message_chain(Path("fake.py"), ast.parse(code))

    assert len(smells) == 0, "Expected 0 smells"
