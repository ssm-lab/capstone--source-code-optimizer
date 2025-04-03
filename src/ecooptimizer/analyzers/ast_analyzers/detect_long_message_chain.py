import ast
from pathlib import Path

from ecooptimizer.utils.smell_enums import CustomSmell

from ecooptimizer.data_types.smell import LMCSmell
from ecooptimizer.data_types.custom_fields import AdditionalInfo, Occurence


def compute_chain_length(node: ast.expr) -> int:
    """
    Recursively determines how many consecutive calls exist in a chain
    ending at 'node'. Each .something() is +1.
    """
    if isinstance(node, ast.Call):
        # We have a call, so that's +1
        if isinstance(node.func, ast.Attribute):
            # The chain might continue if node.func.value is also a call
            return 1 + compute_chain_length(node.func.value)
        else:
            return 1
    elif isinstance(node, ast.Attribute):
        # If it's just an attribute (like `details` or `obj.x`),
        # we keep looking up the chain but *don’t increment*,
        # because we only count calls.
        return compute_chain_length(node.value)
    else:
        # If it's a Name or something else, we stop
        return 0


def detect_long_message_chain(file_path: Path, tree: ast.AST, threshold: int = 5) -> list[LMCSmell]:
    """
    Detects long message chains in the given Python code.

    Args:
        file_path (Path): The file path to analyze.
        tree (ast.AST): The Abstract Syntax Tree (AST) of the source code.
        threshold (int): The minimum number of chained method calls to flag as a long chain. Default is 5.

    Returns:
        list[Smell]: A list of Smell objects, each containing details about the detected long chains.
    """
    # Initialize an empty list to store detected Smell objects
    results: list[LMCSmell] = []
    used_lines = set()

    # Walk through the AST to find method calls and attribute chains
    for node in ast.walk(tree):
        # Check only method calls (Call node whose func is an Attribute)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            length = compute_chain_length(node)
            if length >= threshold:
                line = node.lineno
                # Make sure we haven’t already reported on this line
                if line not in used_lines:
                    used_lines.add(line)

                    message = f"Method chain too long ({length}/{threshold})"
                    # Create the smell object
                    smell = LMCSmell(
                        path=str(file_path),
                        module=file_path.stem,
                        obj=None,
                        type="convention",
                        symbol="long-message-chain",
                        message=message,
                        messageId=CustomSmell.LONG_MESSAGE_CHAIN.value,
                        confidence="UNDEFINED",
                        occurences=[
                            Occurence(
                                line=node.lineno,
                                endLine=node.end_lineno,
                                column=node.col_offset,
                                endColumn=node.end_col_offset,
                            )
                        ],
                        additionalInfo=AdditionalInfo(),
                    )
                    results.append(smell)

    # Return the list of detected Smell objects
    return results
