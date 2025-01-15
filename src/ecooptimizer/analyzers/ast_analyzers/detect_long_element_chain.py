import ast
from pathlib import Path


def detect_long_element_chain(file_path: Path, tree: ast.AST, threshold: int = 3):
    """
    Detects long element chains in the given Python code and returns a list of results.

    Parameters:
        file_path (Path): The file path to analyze.
        tree (ast.AST): The Abstract Syntax Tree (AST) of the source code.
        threshold_count (int): The minimum length of a dictionary chain. Default is 3.

    Returns:
        list[dict]: Each dictionary contains details about the detected long chain.
    """
    # Parse the code into an Abstract Syntax Tree (AST)
    results = []
    messageId = "LEC001"
    used_lines = set()

    # Function to calculate the length of a dictionary chain
    def check_chain(node: ast.Subscript, chain_length: int = 0):
        current = node
        while isinstance(current, ast.Subscript):
            chain_length += 1
            current = current.value

        if chain_length >= threshold:
            # Create the message for the convention
            message = f"Dictionary chain too long ({chain_length}/{threshold})"

            smell = {
                "absolutePath": str(file_path),
                "column": node.col_offset,
                "confidence": "UNDEFINED",
                "endColumn": None,
                "endLine": None,
                "line": node.lineno,
                "message": message,
                "messageId": messageId,
                "module": file_path.name,
                "obj": "",
                "path": str(file_path),
                "symbol": "long-element-chain",
                "type": "convention",
            }

            if node.lineno in used_lines:
                return
            used_lines.add(node.lineno)
            results.append(smell)

    # Walk through the AST
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
            check_chain(node)

    return results
