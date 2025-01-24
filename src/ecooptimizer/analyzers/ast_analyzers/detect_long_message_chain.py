import ast
from pathlib import Path

from ...utils.analyzers_config import CustomSmell

from ...data_wrappers.smell import LMCSmell


def detect_long_message_chain(file_path: Path, tree: ast.AST, threshold: int = 3) -> list[LMCSmell]:
    """
    Detects long message chains in the given Python code.

    Args:
        file_path (Path): The file path to analyze.
        tree (ast.AST): The Abstract Syntax Tree (AST) of the source code.
        threshold (int): The minimum number of chained method calls to flag as a long chain. Default is 3.

    Returns:
        list[Smell]: A list of Smell objects, each containing details about the detected long chains.
    """
    # Initialize an empty list to store detected Smell objects
    results: list[LMCSmell] = []
    used_lines = set()

    # Function to detect long chains
    def check_chain(node: ast.Attribute | ast.expr, chain_length: int = 0):
        """
        Recursively checks if a chain of method calls or attributes exceeds the threshold.

        Args:
            node (ast.Attribute | ast.expr): The current AST node to check.
            chain_length (int): The current length of the method/attribute chain.
        """
        # If the chain length exceeds the threshold, add it to results
        if chain_length >= threshold:
            # Create the message for the convention
            message = f"Method chain too long ({chain_length}/{threshold})"

            # Create a Smell object with the detected issue details
            smell: LMCSmell = {
                "path": str(file_path),
                "module": file_path.stem,
                "obj": None,
                "type": "convention",
                "symbol": "",
                "message": message,
                "messageId": CustomSmell.LONG_MESSAGE_CHAIN.value,
                "confidence": "UNDEFINED",
                "occurences": [
                    {
                        "line": node.lineno,
                        "endLine": node.end_lineno,
                        "column": node.col_offset,
                        "endColumn": node.end_col_offset,
                    }
                ],
                "additionalInfo": None,
            }

            # Ensure each line is only reported once
            if node.lineno in used_lines:
                return
            used_lines.add(node.lineno)
            results.append(smell)
            return

        if isinstance(node, ast.Call):
            # If the node is a function call, increment the chain length
            chain_length += 1
            # Recursively check if there's a chain in the function being called
            if isinstance(node.func, ast.Attribute):
                check_chain(node.func, chain_length)

        elif isinstance(node, ast.Attribute):
            # Increment chain length for attribute access (part of the chain)
            chain_length += 1
            check_chain(node.value, chain_length)

    # Walk through the AST to find method calls and attribute chains
    for node in ast.walk(tree):
        # We are only interested in method calls (attribute access)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            # Call check_chain to detect long chains
            check_chain(node.func)

    # Return the list of detected Smell objects
    return results
