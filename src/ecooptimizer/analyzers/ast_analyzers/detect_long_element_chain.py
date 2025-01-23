import ast
from pathlib import Path

from ...data_wrappers.smell import Smell


def detect_long_element_chain(file_path: Path, tree: ast.AST, threshold: int = 3) -> list[Smell]:
    """
    Detects long element chains in the given Python code and returns a list of Smell objects.

    Args:
        file_path (Path): The file path to analyze.
        tree (ast.AST): The Abstract Syntax Tree (AST) of the source code.
        threshold (int): The minimum length of a dictionary chain. Default is 3.

    Returns:
        list[Smell]: A list of Smell objects, each containing details about a detected long chain.
    """
    # Initialize an empty list to store detected Smell objects
    results: list[Smell] = []
    messageId = "LEC001"
    used_lines = set()

    # Function to calculate the length of a dictionary chain and detect long chains
    def check_chain(node: ast.Subscript, chain_length: int = 0):
        current = node
        # Traverse through the chain to count its length
        while isinstance(current, ast.Subscript):
            chain_length += 1
            current = current.value

        if chain_length >= threshold:
            # Create a descriptive message for the detected long chain
            message = f"Dictionary chain too long ({chain_length}/{threshold})"

            # Instantiate a Smell object with details about the detected issue
            smell = Smell(
                absolutePath=str(file_path),
                column=node.col_offset,
                confidence="UNDEFINED",
                endColumn=None,
                endLine=None,
                line=node.lineno,
                message=message,
                messageId=messageId,
                module=file_path.name,
                obj="",
                path=str(file_path),
                symbol="long-element-chain",
                type="convention",
            )

            # Ensure each line is only reported once
            if node.lineno in used_lines:
                return
            used_lines.add(node.lineno)
            results.append(smell)

    # Traverse the AST to identify nodes representing dictionary chains
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
            check_chain(node)

    # Return the list of detected Smell objects
    return results
