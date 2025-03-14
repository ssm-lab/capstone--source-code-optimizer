import ast
import re
from pathlib import Path

from ...data_types.smell import CRCSmell
from ..base_refactorer import BaseRefactorer


def extract_function_name(call_string: str):
    """Extracts a specific function/method name from a call string."""
    match = re.match(r"(\w+)\.(\w+)\s*\(", call_string)  # Match `obj.method()`
    if match:
        return f"{match.group(1)}_{match.group(2)}"  # Format: cache_obj_method
    match = re.match(r"(\w+)\s*\(", call_string)  # Match `function()`
    if match:
        return f"{match.group(1)}"  # Format: cache_function
    return call_string  # Fallback (shouldn't happen in valid calls)


class CacheRepeatedCallsRefactorer(BaseRefactorer[CRCSmell]):
    def __init__(self):
        """
        Initializes the CacheRepeatedCallsRefactorer.
        """
        super().__init__()
        self.target_line = None

    def refactor(
        self,
        target_file: Path,
        source_dir: Path,  # noqa: ARG002
        smell: CRCSmell,
        output_file: Path,
        overwrite: bool = True,
    ):
        """
        Refactor the repeated function call smell and save to a new file.
        """
        self.target_file = target_file
        self.smell = smell
        self.call_string = self.smell.additionalInfo.callString.strip()

        # Correctly generate cached variable name
        self.cached_var_name = "cached_" + extract_function_name(self.call_string)

        with self.target_file.open("r") as file:
            lines = file.readlines()

        # Parse the AST
        tree = ast.parse("".join(lines))

        # Find the valid parent node
        parent_node = self._find_valid_parent(tree)
        if not parent_node:
            return

        # Determine the insertion point for the cached variable
        insert_line = self._find_insert_line(parent_node)
        indent = self._get_indentation(lines, insert_line)
        cached_assignment = f"{indent}{self.cached_var_name} = {self.call_string}\n"

        # Insert the cached variable into the source lines
        lines.insert(insert_line - 1, cached_assignment)
        line_shift = 1  # Track the shift in line numbers caused by the insertion

        # Replace calls with the cached variable in the affected lines
        for occurrence in self.smell.occurences:
            adjusted_line_index = occurrence.line - 1 + line_shift
            original_line = lines[adjusted_line_index]
            updated_line = self._replace_call_in_line(
                original_line, self.call_string, self.cached_var_name
            )
            if updated_line != original_line:
                lines[adjusted_line_index] = updated_line

        # Multi-file implementation
        if overwrite:
            with target_file.open("w") as f:
                f.writelines(lines)
        else:
            with output_file.open("w") as f:
                f.writelines(lines)

    def _get_indentation(self, lines: list[str], line_number: int):
        """Determine the indentation level of a given line."""
        line = lines[line_number - 1]
        return line[: len(line) - len(line.lstrip())]

    def _replace_call_in_line(self, line: str, call_string: str, cached_var_name: str):
        """
        Replace the repeated call in a line with the cached variable.
        """
        return line.replace(call_string, cached_var_name)

    def _find_valid_parent(self, tree: ast.Module):
        """
        Find the valid parent node that contains all occurrences of the repeated call.
        """
        candidate_parent = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                if all(self._line_in_node_body(node, occ.line) for occ in self.smell.occurences):
                    candidate_parent = node
        return candidate_parent

    def _find_insert_line(self, parent_node: ast.FunctionDef | ast.ClassDef | ast.Module):
        """
        Find the line to insert the cached variable assignment.

        - If it's a function, insert at the beginning but **after a docstring** if present.
        - If it's a method call (`obj.method()`), insert after `obj` is defined.
        - If it's a lambda assignment (`compute_demo = lambda ...`), insert after it.
        """
        if isinstance(parent_node, ast.Module):
            return 1  # Top of the module

        # Extract variable or function name from call string
        var_match = re.match(r"(\w+)\.", self.call_string)  # Matches `obj.method()`
        if var_match:
            obj_name = var_match.group(1)  # Extract `obj`

            # Find the first assignment of `obj`
            for node in parent_node.body:
                if isinstance(node, ast.Assign):
                    if any(
                        isinstance(target, ast.Name) and target.id == obj_name
                        for target in node.targets
                    ):
                        return node.lineno + 1  # Insert after the assignment of `obj`

        # Find the first lambda assignment
        for node in parent_node.body:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Lambda):
                lambda_var_name = node.targets[0].id  # Extract variable name
                if lambda_var_name in self.call_string:
                    return node.lineno + 1  # Insert after the lambda function

        # Check if the first statement is a docstring
        if (
            isinstance(parent_node.body[0], ast.Expr)
            and isinstance(parent_node.body[0].value, ast.Constant)
            and isinstance(parent_node.body[0].value.value, str)  # Ensures it's a string docstring
        ):
            docstring_start = parent_node.body[0].lineno
            docstring_end = docstring_start

            # Find the last line of the docstring by counting the lines it spans
            docstring_content = parent_node.body[0].value.value
            docstring_lines = docstring_content.count("\n")
            if docstring_lines > 0:
                docstring_end += docstring_lines

            return docstring_end + 1  # Insert after the last line of the docstring

        return parent_node.body[0].lineno  # Default: insert at function start

    def _line_in_node_body(self, node: ast.FunctionDef | ast.ClassDef | ast.Module, line: int):
        """
        Check if a line is within the body of a given AST node.
        """
        if not hasattr(node, "body"):
            return False

        for child in node.body:
            if hasattr(child, "lineno") and child.lineno <= line <= getattr(
                child, "end_lineno", child.lineno
            ):
                return True
        return False
