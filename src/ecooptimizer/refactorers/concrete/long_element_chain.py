import ast
import json
from pathlib import Path
import re
from typing import Any, Optional

from ..multi_file_refactorer import MultiFileRefactorer
from ...data_types.smell import LECSmell


class DictAccess:
    """Represents a dictionary access pattern found in code."""

    def __init__(
        self,
        dictionary_name: str,
        full_access: str,
        nesting_level: int,
        line_number: int,
        col_offset: int,
        path: Path,
        node: ast.AST,
    ):
        self.dictionary_name = dictionary_name
        self.full_access = full_access
        self.nesting_level = nesting_level
        self.col_offset = col_offset
        self.line_number = line_number
        self.path = path
        self.node = node


class LongElementChainRefactorer(MultiFileRefactorer[LECSmell]):
    """
    Refactors long element chains by flattening nested dictionaries.
    Only implements flatten dictionary strategy as it proved most effective for energy savings.
    """

    def __init__(self):
        super().__init__()
        self.dict_name: set[str] = set()
        self.access_patterns: set[DictAccess] = set()
        self.min_value = float("inf")
        self.dict_assignment: Optional[dict[str, Any]] = None
        self.initial_parsing = True

    def refactor(
        self,
        target_file: Path,
        source_dir: Path,
        smell: LECSmell,
        output_file: Path,  # noqa: ARG002
        overwrite: bool = True,  # noqa: ARG002
    ) -> None:
        """Main refactoring method that processes the target file and related files."""
        self.target_file = target_file
        line_number = smell.occurences[0].line

        tree = ast.parse(target_file.read_text())
        self._find_dict_names(tree, line_number)

        # Abort if dictionary access is too shallow
        self.traverse_and_process(source_dir)
        if self.min_value <= 1:
            return

        self.initial_parsing = False
        self.traverse_and_process(source_dir)

    def _find_dict_names(self, tree: ast.AST, line_number: int) -> None:
        """Extract dictionary names from the AST at the given line number."""
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.Subscript)
                and hasattr(node, "lineno")
                and node.lineno == line_number
            ):
                continue

            if isinstance(node.value, ast.Name):
                self.dict_name.add(node.value.id)
            else:
                dict_name = self._extract_dict_name(node.value)
                if dict_name:
                    self.dict_name.add(dict_name)
                    self.dict_name.add(dict_name.split(".")[-1])

    def _extract_dict_name(self, node: ast.AST) -> Optional[str]:
        """Extract dictionary name from attribute access chains."""
        while isinstance(node, ast.Subscript):
            node = node.value

        if isinstance(node, ast.Attribute):
            return f"{node.value.id}.{node.attr}"
        return None

    def _process_file(self, file: Path):
        tree = ast.parse(file.read_text())
        if self.initial_parsing:
            self._find_access_pattern_in_file(tree, file)
        else:
            self.find_dict_assignment_in_file(tree)
            if self._refactor_all_in_file(file):
                return True

        return False

    # finds all access patterns in the file
    def _find_access_pattern_in_file(self, tree: ast.AST, path: Path):
        offset = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript):  # Check for dictionary access (Subscript)
                dict_name, full_access, line_number, col_offset = self.extract_full_dict_access(
                    node
                )

                if (line_number, col_offset) in offset:
                    continue
                offset.add((line_number, col_offset))

                if dict_name.split(".")[-1] in self.dict_name:
                    nesting_level = self._count_nested_subscripts(node)
                    access = DictAccess(
                        dict_name, full_access, nesting_level, line_number, col_offset, path, node
                    )
                    self.access_patterns.add(access)
                    # print(self.access_patterns)
                    self.min_value = min(self.min_value, nesting_level)

    def extract_full_dict_access(self, node: ast.Subscript):
        """Extracts the full dictionary access chain as a string."""
        access_chain = []
        curr = node
        # Traverse nested subscripts to build access path
        while isinstance(curr, ast.Subscript):
            if isinstance(curr.slice, ast.Constant):  # Python 3.8+
                access_chain.append(f"['{curr.slice.value}']")
            curr = curr.value  # Move to parent node

        # Get the dictionary root (can be a variable or an attribute)
        if isinstance(curr, ast.Name):
            dict_name = curr.id  # Simple variable (e.g., "long_chain")
        elif isinstance(curr, ast.Attribute) and isinstance(curr.value, ast.Name):
            dict_name = f"{curr.value.id}.{curr.attr}"  # Attribute access (e.g., "self.long_chain")
        else:
            dict_name = "UNKNOWN"

        full_access = f"{dict_name}{''.join(reversed(access_chain))}"

        return dict_name, full_access, curr.lineno, curr.col_offset

    def _count_nested_subscripts(self, node: ast.Subscript):
        """
        Counts how many times a dictionary is accessed (nested Subscript nodes).
        """
        level = 0
        curr = node
        while isinstance(curr, ast.Subscript):
            curr = curr.value  # Move up the AST
            level += 1
        return level

    def find_dict_assignment_in_file(self, tree: ast.AST):
        """find the dictionary assignment from AST based on the dict name"""

        class DictVisitor(ast.NodeVisitor):
            def visit_Assign(self_, node: ast.Assign):
                if isinstance(node.value, ast.Dict) and len(node.targets) == 1:
                    # dictionary is a varibale
                    if (
                        isinstance(node.targets[0], ast.Name)
                        and node.targets[0].id in self.dict_name
                    ):
                        dict_value = self.extract_dict_literal(node.value)
                        flattened_version = self.flatten_dict(dict_value)  # type: ignore
                        self.dict_assignment = flattened_version

                    # dictionary is an attribute
                    elif (
                        isinstance(node.targets[0], ast.Attribute)
                        and node.targets[0].attr in self.dict_name
                    ):
                        dict_value = self.extract_dict_literal(node.value)
                        self.dict_assignment = self.flatten_dict(dict_value)  # type: ignore
                self_.generic_visit(node)

        DictVisitor().visit(tree)

    def extract_dict_literal(self, node: ast.AST):
        """Convert AST dict literal to Python dict."""
        if isinstance(node, ast.Dict):
            return {
                self.extract_dict_literal(k)
                if isinstance(k, ast.AST)
                else k: self.extract_dict_literal(v) if isinstance(v, ast.AST) else v
                for k, v in zip(node.keys, node.values)
            }
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            return node.id
        return node

    def flatten_dict(
        self, d: dict[str, Any], depth: int = 0, parent_key: str = ""
    ) -> dict[str, Any]:
        """Recursively flatten a nested dictionary."""

        if depth >= self.min_value - 1:
            # At max_depth, we return the current dictionary as flattened key-value pairs
            items = {}
            for k, v in d.items():
                new_key = f"{parent_key}_{k}" if parent_key else k
                items[new_key] = v
            return items

        items = {}
        for k, v in d.items():
            new_key = f"{parent_key}_{k}" if parent_key else k

            if isinstance(v, dict):
                # Recursively flatten the dictionary, increasing the depth
                items.update(self.flatten_dict(v, depth + 1, new_key))
            else:
                # If it's not a dictionary, just add it to the result
                items[new_key] = v

        return items

    def generate_flattened_access(self, access_chain: list[str]) -> str:
        """Generate flattened dictionary key only until given min_value."""

        joined = "_".join(k.strip("'\"") for k in access_chain[: self.min_value])
        if not joined.endswith("']") or not joined.endswith('"]'):  # Corrected to check for "']"
            joined += "']"
        remaining = access_chain[self.min_value :]  # Keep the rest unchanged

        rest = "".join(f"[{key}]" for key in remaining)

        return f"{joined}" + rest

    def _refactor_all_in_file(self, file_path: Path):
        """Refactor dictionary access patterns in a single file."""
        # Skip if no access patterns found
        if not any(access.path == file_path for access in self.access_patterns):
            return False

        source_code = file_path.read_text()
        lines = source_code.split("\n")
        line_modifications = self._collect_line_modifications(file_path)

        refactored_lines = self._apply_modifications(lines, line_modifications)
        refactored_lines = self._update_dict_assignment(refactored_lines)

        # Write changes back to file
        file_path.write_text("\n".join(refactored_lines))

        return True

    def _collect_line_modifications(self, file_path: Path) -> dict[int, list[tuple[int, str, str]]]:
        """Collect all modifications needed for each line."""
        modifications: dict[int, list[tuple[int, str, str]]] = {}

        for access in sorted(self.access_patterns, key=lambda a: (a.line_number, a.col_offset)):
            if access.path != file_path:
                continue

            access_chain = access.full_access.split("][")
            for i in range(len(access_chain)):
                access_chain[i] = access_chain[i].replace("]", "")
            new_access = self.generate_flattened_access(access_chain)

            if access.line_number not in modifications:
                modifications[access.line_number] = []
            modifications[access.line_number].append(
                (access.col_offset, access.full_access, new_access)
            )

        return modifications

    def _apply_modifications(
        self, lines: list[str], modifications: dict[int, list[tuple[int, str, str]]]
    ) -> list[str]:
        """Apply collected modifications to each line."""
        refactored_lines = []
        for line_num, original_line in enumerate(lines, start=1):
            if line_num in modifications:
                # Sort modifications by column offset (reverse to replace from right to left)
                mods = sorted(modifications[line_num], key=lambda x: x[0], reverse=True)
                modified_line = original_line
                # print("this si the  og line: " + modified_line)

                for col_offset, old_access, new_access in mods:
                    end_idx = col_offset + len(old_access)
                    # Replace specific occurrence using slicing
                    modified_line = (
                        modified_line[:col_offset] + new_access + modified_line[end_idx:]
                    )
                    # print(modified_line)

                refactored_lines.append(modified_line)
            else:
                # No modification, add original line
                refactored_lines.append(original_line)

        return refactored_lines

    def _update_dict_assignment(self, refactored_lines: list[str]) -> None:
        """Update dictionary assignment to be the new flattened dictionary."""
        dictionary_assignment_name = self.dict_name
        for i, line in enumerate(refactored_lines):
            match = next(
                (
                    name
                    for name in dictionary_assignment_name
                    if re.match(rf"^\s*(?:\w+\.)*{re.escape(name)}\s*=", line)
                ),
                None,
            )

            if match:
                # Preserve indentation and the `=`
                indent, prefix, _ = re.split(r"(=)", line, maxsplit=1)

                # Convert dict to a properly formatted string
                dict_str = json.dumps(self.dict_assignment, separators=(",", ": "))
                # Update the line with the new flattened dictionary
                refactored_lines[i] = f"{indent}{prefix} {dict_str}"

                # Remove the following lines of the original nested dictionary,
                # leaving only one empty line after them
                j = i + 1
                while j < len(refactored_lines) and (
                    refactored_lines[j].strip().startswith('"')
                    or refactored_lines[j].strip().startswith("}")
                ):
                    refactored_lines[j] = "Remove this line"  # Mark for removal
                    j += 1
                break

        refactored_lines = [line for line in refactored_lines if line.strip() != "Remove this line"]

        return refactored_lines
