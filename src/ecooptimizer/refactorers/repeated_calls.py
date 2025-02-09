import ast
from pathlib import Path

from ..data_types.smell import CRCSmell

from .base_refactorer import BaseRefactorer


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

        self.cached_var_name = "cached_" + self.call_string.split("(")[0]

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

        # Save the modified file
        temp_file_path = output_file

        with temp_file_path.open("w") as refactored_file:
            refactored_file.writelines(lines)

        # CHANGE FOR MULTI FILE IMPLEMENTATION
        if overwrite:
            with target_file.open("w") as f:
                f.writelines(lines)
        else:
            with output_file.open("w") as f:
                f.writelines(lines)

    def _get_indentation(self, lines: list[str], line_number: int):
        """
        Determine the indentation level of a given line.

        :param lines: List of source code lines.
        :param line_number: The line number to check.
        :return: The indentation string.
        """
        line = lines[line_number - 1]
        return line[: len(line) - len(line.lstrip())]

    def _replace_call_in_line(self, line: str, call_string: str, cached_var_name: str):
        """
        Replace the repeated call in a line with the cached variable.

        :param line: The original line of source code.
        :param call_string: The string representation of the call.
        :param cached_var_name: The name of the cached variable.
        :return: The updated line.
        """
        # Replace all exact matches of the call string with the cached variable
        updated_line = line.replace(call_string, cached_var_name)
        return updated_line

    def _find_valid_parent(self, tree: ast.Module):
        """
        Find the valid parent node that contains all occurences of the repeated call.

        :param tree: The root AST tree.
        :return: The valid parent node, or None if not found.
        """
        candidate_parent = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                if all(self._line_in_node_body(node, occ.line) for occ in self.smell.occurences):
                    candidate_parent = node
        if candidate_parent:
            print(
                f"Valid parent found: {type(candidate_parent).__name__} at line "
                f"{getattr(candidate_parent, 'lineno', 'module')}"
            )
        return candidate_parent

    def _find_insert_line(self, parent_node: ast.FunctionDef | ast.ClassDef | ast.Module):
        """
        Find the line to insert the cached variable assignment.

        :param parent_node: The parent node containing the occurences.
        :return: The line number where the cached variable should be inserted.
        """
        if isinstance(parent_node, ast.Module):
            return 1  # Top of the module
        return parent_node.body[0].lineno  # Beginning of the parent node's body

    def _line_in_node_body(self, node: ast.FunctionDef | ast.ClassDef | ast.Module, line: int):
        """
        Check if a line is within the body of a given AST node.

        :param node: The AST node to check.
        :param line: The line number to check.
        :return: True if the line is within the node's body, False otherwise.
        """
        if not hasattr(node, "body"):
            return False

        for child in node.body:
            if hasattr(child, "lineno") and child.lineno <= line <= getattr(
                child, "end_lineno", child.lineno
            ):
                return True
        return False
