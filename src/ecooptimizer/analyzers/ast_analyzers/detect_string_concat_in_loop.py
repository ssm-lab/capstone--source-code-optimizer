from pathlib import Path
from astroid import nodes


def detect_string_concat_in_loop(file_path: Path, tree: nodes.Module):
    """
    Detects string concatenation inside loops within a Python AST tree.

    Parameters:
        file_path (Path): The file path to analyze.
        tree (nodes.Module): The parsed AST tree of the Python code.

    Returns:
        list[dict]: A list of dictionaries containing details about detected string concatenation smells.
    """
    results = []
    messageId = "SCIL001"

    def is_string_type(node: nodes.Assign):
        """Check if the target of the assignment is of type string."""
        inferred_types = node.targets[0].infer()
        for inferred in inferred_types:
            if inferred.repr_name() == "str":
                return True
        return False

    def is_concatenating_with_self(binop_node: nodes.BinOp, target: nodes.NodeNG):
        """Check if the BinOp node includes the target variable being added."""

        def is_same_variable(var1: nodes.NodeNG, var2: nodes.NodeNG):
            if isinstance(var1, nodes.Name) and isinstance(var2, nodes.AssignName):
                return var1.name == var2.name
            if isinstance(var1, nodes.Attribute) and isinstance(var2, nodes.AssignAttr):
                return var1.as_string() == var2.as_string()
            return False

        left, right = binop_node.left, binop_node.right
        return is_same_variable(left, target) or is_same_variable(right, target)

    def visit_node(node: nodes.NodeNG, in_loop_counter: int):
        """Recursively visits nodes to detect string concatenation in loops."""
        nonlocal results

        if isinstance(node, (nodes.For, nodes.While)):
            in_loop_counter += 1
            for stmt in node.body:
                visit_node(stmt, in_loop_counter)
            in_loop_counter -= 1

        elif in_loop_counter > 0 and isinstance(node, nodes.Assign):
            target = node.targets[0] if len(node.targets) == 1 else None
            value = node.value

            if target and isinstance(value, nodes.BinOp) and value.op == "+":
                if is_string_type(node) and is_concatenating_with_self(value, target):
                    smell = {
                        "absolutePath": str(file_path),
                        "column": node.col_offset,
                        "confidence": "UNDEFINED",
                        "endColumn": None,
                        "endLine": None,
                        "line": node.lineno,
                        "message": "String concatenation inside loop detected",
                        "messageId": messageId,
                        "module": file_path.name,
                        "obj": "",
                        "path": str(file_path),
                        "symbol": "string-concat-in-loop",
                        "type": "refactor",
                    }
                    results.append(smell)

        else:
            for child in node.get_children():
                visit_node(child, in_loop_counter)

    # Start traversal
    for child in tree.get_children():
        visit_node(child, 0)

    return results
