import ast
from pathlib import Path


def detect_long_message_chain(file_path: Path, tree: ast.AST, threshold: int = 3):
    """
    Detects long message chains in the given Python code.

    Parameters:
        file_path (Path): The file path to analyze.
        tree (ast.AST): The Abstract Syntax Tree (AST) of the source code.
        threshold (int, optional): The minimum number of chained method calls to flag as a long chain. Default is 3.

    Returns:
        list[dict]: A list of dictionaries containing details about the detected long chains.
    """
    # Parse the code into an Abstract Syntax Tree (AST)
    results = []
    messageId = "LMC001"
    used_lines = set()

    # Function to detect long chains
    def check_chain(node: ast.Attribute | ast.expr, chain_length: int = 0):
        # If the chain length exceeds the threshold, add it to results
        if chain_length >= threshold:
            # Create the message for the convention
            message = f"Method chain too long ({chain_length}/{threshold})"
            # Add the result in the required format

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
                "symbol": "long-message-chain",
                "type": "convention",
            }

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

    # Walk through the AST
    for node in ast.walk(tree):
        # We are only interested in method calls (attribute access)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            # Call check_chain to detect long chains
            check_chain(node.func)

    return results
