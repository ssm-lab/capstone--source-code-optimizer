import ast
from pathlib import Path

from ...data_wrappers.smell import Smell


def detect_string_concat_in_loop(file_path: Path, tree: ast.AST) -> list[Smell]:
    """
    Detects string concatenation inside loops within a Python AST tree.

    Args:
        file_path (Path): The file path to analyze.
        tree (ast.AST): The Abstract Syntax Tree (AST) of the source code.

    Returns:
        list[Smell]: A list of Smell objects containing details about detected string concatenation smells.
    """
    results: list[Smell] = []
    messageId = "SCIL001"

    def is_string_concatenation(node: ast.Assign, target: ast.expr) -> bool:
        """
        Check if the assignment operation involves string concatenation with itself.

        Args:
            node (ast.Assign): The assignment node to check.
            target (ast.expr): The target of the assignment.

        Returns:
            bool: True if the operation involves string concatenation with itself, False otherwise.
        """
        if isinstance(node.value, ast.BinOp) and isinstance(node.value.op, ast.Add):
            left, right = node.value.left, node.value.right
            return (
                isinstance(left, ast.Name) and isinstance(target, ast.Name) and left.id == target.id
            ) or (
                isinstance(right, ast.Name)
                and isinstance(target, ast.Name)
                and right.id == target.id
            )
        return False

    def visit_node(node: ast.AST, in_loop_counter: int):
        """
        Recursively visits nodes to detect string concatenation in loops.

        Args:
            node (ast.AST): The current AST node to visit.
            in_loop_counter (int): Counter to track nesting within loops.
        """
        nonlocal results

        # Increment loop counter when entering a loop
        if isinstance(node, (ast.For, ast.While)):
            in_loop_counter += 1

        # Check for string concatenation in assignments inside loops
        if in_loop_counter > 0 and isinstance(node, ast.Assign):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                target = node.targets[0]
                if isinstance(node.value, ast.BinOp) and is_string_concatenation(node, target):
                    smell = Smell(
                        absolutePath=str(file_path),
                        column=node.col_offset,
                        confidence="UNDEFINED",
                        endColumn=None,
                        endLine=None,
                        line=node.lineno,
                        message="String concatenation inside loop detected",
                        messageId=messageId,
                        module=file_path.name,
                        obj="",
                        path=str(file_path),
                        symbol="string-concat-in-loop",
                        type="refactor",
                    )
                    results.append(smell)

        # Visit child nodes
        for child in ast.iter_child_nodes(node):
            visit_node(child, in_loop_counter)

        # Decrement loop counter when leaving a loop
        if isinstance(node, (ast.For, ast.While)):
            in_loop_counter -= 1

    # Start traversal of the AST
    visit_node(tree, 0)

    return results
