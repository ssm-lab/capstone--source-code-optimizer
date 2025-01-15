import ast
from pathlib import Path


def detect_unused_variables_and_attributes(file_path: Path, tree: ast.AST):
    """
    Detects unused variables and class attributes in the given Python code and returns a list of results.

    Parameters:
        file_path (Path): The file path to analyze.
        tree (ast.AST): The Abstract Syntax Tree (AST) of the source code.

    Returns:
        list[dict]: A list of dictionaries containing details about detected performance smells.
    """
    # Store variable and attribute declarations and usage
    results = []
    messageId = "UVA001"
    declared_vars = set()
    used_vars = set()

    # Helper function to gather declared variables (including class attributes)
    def gather_declarations(node: ast.AST):
        # For assignment statements (variables or class attributes)
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):  # Simple variable
                    declared_vars.add(target.id)
                elif isinstance(target, ast.Attribute):  # Class attribute
                    declared_vars.add(f"{target.value.id}.{target.attr}")  # type: ignore

        # For class attribute assignments (e.g., self.attribute)
        elif isinstance(node, ast.ClassDef):
            for class_node in ast.walk(node):
                if isinstance(class_node, ast.Assign):
                    for target in class_node.targets:
                        if isinstance(target, ast.Name):
                            declared_vars.add(target.id)
                        elif isinstance(target, ast.Attribute):
                            declared_vars.add(f"{target.value.id}.{target.attr}")  # type: ignore

    # Helper function to gather used variables and class attributes
    def gather_usages(node: ast.AST):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):  # Variable usage
            used_vars.add(node.id)
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):  # Attribute usage
            # Check if the attribute is accessed as `self.attribute`
            if isinstance(node.value, ast.Name) and node.value.id == "self":
                # Only add to used_vars if it’s in the form of `self.attribute`
                used_vars.add(f"self.{node.attr}")

    # Gather declared and used variables
    for node in ast.walk(tree):
        gather_declarations(node)
        gather_usages(node)

    # Detect unused variables by finding declared variables not in used variables
    unused_vars = declared_vars - used_vars

    for var in unused_vars:
        # Locate the line number for each unused variable or attribute
        line_no, column_no = 0, 0
        symbol = ""
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == var:
                line_no = node.lineno
                column_no = node.col_offset
                symbol = "unused-variable"
                break
            elif (
                isinstance(node, ast.Attribute)
                and f"self.{node.attr}" == var
                and isinstance(node.value, ast.Name)
                and node.value.id == "self"
            ):
                line_no = node.lineno
                column_no = node.col_offset
                symbol = "unused-attribute"
                break

        smell = {
            "absolutePath": str(tree),
            "column": column_no,
            "confidence": "UNDEFINED",
            "endColumn": None,
            "endLine": None,
            "line": line_no,
            "message": f"Unused variable or attribute '{var}'",
            "messageId": messageId,
            "module": file_path.name,
            "obj": "",
            "path": str(file_path),
            "symbol": symbol,
            "type": "convention",
        }

        results.append(smell)

    return results
