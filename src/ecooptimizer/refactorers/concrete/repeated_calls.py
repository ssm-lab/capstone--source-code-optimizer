import ast
import re
from pathlib import Path

from ecooptimizer.data_types.smell import CRCSmell
from ecooptimizer.refactorers.base_refactorer import BaseRefactorer


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

        # Find the first occurrence line
        first_occurrence = min(occ.line for occ in self.smell.occurences)

        # Get the indentation of the first occurrence
        indent = self._get_indentation(lines, first_occurrence)
        cached_assignment = f"{indent}{self.cached_var_name} = {self.call_string}\n"

        # Insert the cached variable at the first occurrence line
        lines.insert(first_occurrence - 1, cached_assignment)
        line_shift = 1  # Track the shift in line numbers caused by the insertion

        # Replace calls with the cached variable in the affected lines
        for occurrence in self.smell.occurences:
            # Adjust line number considering the insertion
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
