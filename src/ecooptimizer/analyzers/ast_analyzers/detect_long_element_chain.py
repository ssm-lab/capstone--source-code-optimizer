import ast
from pathlib import Path

from ...utils.smell_enums import CustomSmell

from ...data_types.smell import LECSmell
from ...data_types.custom_fields import BasicOccurence


def detect_long_element_chain(file_path: Path, tree: ast.AST, threshold: int = 3) -> list[LECSmell]:
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
    results: list[LECSmell] = []
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
            smell = LECSmell(
                path=str(file_path),
                module=file_path.stem,
                obj=None,
                type="convention",
                symbol="long-element-chain",
                message=message,
                messageId=CustomSmell.LONG_ELEMENT_CHAIN.value,
                confidence="UNDEFINED",
                occurences=[
                    BasicOccurence(
                        line=node.lineno,
                        endLine=node.end_lineno,
                        column=node.col_offset,
                        endColumn=node.end_col_offset,
                    )
                ],
                additionalInfo=None,
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
