import ast
from pathlib import Path

from ...utils.smell_enums import CustomSmell

from ...data_types.custom_fields import BasicOccurence
from ...data_types.smell import UVASmell


def detect_unused_variables_and_attributes(file_path: Path, tree: ast.AST) -> list[UVASmell]:
    """
    Detects unused variables and class attributes in the given Python code.

    Args:
        file_path (Path): The file path to analyze.
        tree (ast.AST): The Abstract Syntax Tree (AST) of the source code.

    Returns:
        list[Smell]: A list of Smell objects containing details about detected unused variables or attributes.
    """
    # Store variable and attribute declarations and usage
    results: list[UVASmell] = []
    declared_vars = set()
    used_vars = set()

    # Helper function to gather declared variables (including class attributes)
    def gather_declarations(node: ast.AST):
        """
        Identifies declared variables or class attributes.

        Args:
            node (ast.AST): The AST node to analyze.
        """
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
        """
        Identifies variables or class attributes that are used.

        Args:
            node (ast.AST): The AST node to analyze.
        """
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

        # Create a Smell object for the unused variable or attribute
        smell = UVASmell(
            path=str(file_path),
            module=file_path.stem,
            obj=None,
            type="convention",
            symbol=symbol,
            message=f"Unused variable or attribute '{var}'",
            messageId=CustomSmell.UNUSED_VAR_OR_ATTRIBUTE.value,
            confidence="UNDEFINED",
            occurences=[
                BasicOccurence(
                    line=line_no,
                    endLine=None,
                    column=column_no,
                    endColumn=None,
                )
            ],
            additionalInfo=None,
        )

        results.append(smell)

    # Return the list of detected Smell objects
    return results
