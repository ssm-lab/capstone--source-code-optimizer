import ast
import logging
from pathlib import Path

from .base_refactorer import BaseRefactorer


class CacheRepeatedCallsRefactorer(BaseRefactorer):
    def __init__(self, output_dir: Path):
        """
        Initializes the CacheRepeatedCallsRefactorer.
        """
        super().__init__(output_dir)
        self.target_line = None

    def refactor(self, file_path: Path, pylint_smell):  # noqa: ANN001
        """
        Refactor the repeated function call smell and save to a new file.
        """
        self.input_file = file_path
        self.smell = pylint_smell

        self.cached_var_name = "cached_" + self.smell["occurrences"][0]["call_string"].split("(")[0]

        print(f"Reading file: {self.input_file}")
        with self.input_file.open("r") as file:
            lines = file.readlines()

        # Parse the AST
        tree = ast.parse("".join(lines))
        print("Parsed AST successfully.")

        # Find the valid parent node
        parent_node = self._find_valid_parent(tree)
        if not parent_node:
            print("ERROR: Could not find a valid parent node for the repeated calls.")
            return

        # Determine the insertion point for the cached variable
        insert_line = self._find_insert_line(parent_node)
        indent = self._get_indentation(lines, insert_line)
        cached_assignment = f"{indent}{self.cached_var_name} = {self.smell['occurrences'][0]['call_string'].strip()}\n"
        print(f"Inserting cached variable at line {insert_line}: {cached_assignment.strip()}")

        # Insert the cached variable into the source lines
        lines.insert(insert_line - 1, cached_assignment)
        line_shift = 1  # Track the shift in line numbers caused by the insertion

        # Replace calls with the cached variable in the affected lines
        for occurrence in self.smell["occurrences"]:
            adjusted_line_index = occurrence["line"] - 1 + line_shift
            original_line = lines[adjusted_line_index]
            call_string = occurrence["call_string"].strip()
            print(f"Processing occurrence at line {occurrence['line']}: {original_line.strip()}")
            updated_line = self._replace_call_in_line(
                original_line, call_string, self.cached_var_name
            )
            if updated_line != original_line:
                print(f"Updated line {occurrence['line']}: {updated_line.strip()}")
                lines[adjusted_line_index] = updated_line

        # Save the modified file
        temp_file_path = self.temp_dir / Path(f"{file_path.stem}_crc_line_{self.target_line}.temp")

        with temp_file_path.open("w") as refactored_file:
            refactored_file.writelines(lines)

        with file_path.open("w") as f:
            f.writelines(lines)

        logging.info(f"Refactoring completed and saved to: {temp_file_path}")

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
        Find the valid parent node that contains all occurrences of the repeated call.

        :param tree: The root AST tree.
        :return: The valid parent node, or None if not found.
        """
        candidate_parent = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                if all(
                    self._line_in_node_body(node, occ["line"]) for occ in self.smell["occurrences"]
                ):
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

        :param parent_node: The parent node containing the occurrences.
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
