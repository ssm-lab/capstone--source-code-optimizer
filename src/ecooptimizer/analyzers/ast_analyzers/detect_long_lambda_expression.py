import ast
from pathlib import Path

from ...utils.analyzers_config import CustomSmell

from ...data_wrappers.smell import LLESmell


def detect_long_lambda_expression(
    file_path: Path, tree: ast.AST, threshold_length: int = 100, threshold_count: int = 3
) -> list[LLESmell]:
    """
    Detects lambda functions that are too long, either by the number of expressions or the total length in characters.

    Args:
        file_path (Path): The file path to analyze.
        tree (ast.AST): The Abstract Syntax Tree (AST) of the source code.
        threshold_length (int): The maximum number of characters allowed in the lambda expression.
        threshold_count (int): The maximum number of expressions allowed inside the lambda function.

    Returns:
        list[Smell]: A list of Smell objects, each containing details about detected long lambda functions.
    """
    # Initialize an empty list to store detected Smell objects
    results: list[LLESmell] = []
    used_lines = set()

    # Function to check the length of lambda expressions
    def check_lambda(node: ast.Lambda):
        """
        Analyzes a lambda node to check if it exceeds the specified thresholds
        for the number of expressions or total character length.

        Args:
            node (ast.Lambda): The lambda node to analyze.
        """
        # Count the number of expressions in the lambda body
        if isinstance(node.body, list):
            lambda_length = len(node.body)
        else:
            lambda_length = 1  # Single expression if it's not a list

        # Check if the lambda expression exceeds the threshold based on the number of expressions
        if lambda_length >= threshold_count:
            message = f"Lambda function too long ({lambda_length}/{threshold_count} expressions)"
            smell: LLESmell = {
                "path": str(file_path),
                "module": file_path.stem,
                "obj": None,
                "type": "convention",
                "symbol": "long-lambda-expr",
                "message": message,
                "messageId": CustomSmell.LONG_LAMBDA_EXPR.value,
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

            if node.lineno in used_lines:
                return
            used_lines.add(node.lineno)
            results.append(smell)

        # Convert the lambda function to a string and check its total length in characters
        lambda_code = get_lambda_code(node)
        if len(lambda_code) > threshold_length:
            message = (
                f"Lambda function too long ({len(lambda_code)} characters, max {threshold_length})"
            )
            smell: LLESmell = {
                "path": str(file_path),
                "module": file_path.stem,
                "obj": None,
                "type": "convention",
                "symbol": "long-lambda-expr",
                "message": message,
                "messageId": CustomSmell.LONG_LAMBDA_EXPR.value,
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

            if node.lineno in used_lines:
                return
            used_lines.add(node.lineno)
            results.append(smell)

    # Helper function to get the string representation of the lambda expression
    def get_lambda_code(lambda_node: ast.Lambda) -> str:
        """
        Constructs the string representation of a lambda expression.

        Args:
            lambda_node (ast.Lambda): The lambda node to reconstruct.

        Returns:
            str: The string representation of the lambda expression.
        """
        # Reconstruct the lambda arguments and body as a string
        args = ", ".join(arg.arg for arg in lambda_node.args.args)

        # Convert the body to a string by using ast's built-in functionality
        body = ast.unparse(lambda_node.body)

        # Combine to form the lambda expression
        return f"lambda {args}: {body}"

    # Walk through the AST to find lambda expressions
    for node in ast.walk(tree):
        if isinstance(node, ast.Lambda):
            check_lambda(node)

    # Return the list of detected Smell objects
    return results
