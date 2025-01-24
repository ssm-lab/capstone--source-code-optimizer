import logging
from pathlib import Path
import re
import ast
from typing import Any

from .base_refactorer import BaseRefactorer
from ..data_wrappers.smell import LECSmell


class LongElementChainRefactorer(BaseRefactorer):
    """
    Only implements flatten dictionary stratrgy becasuse every other strategy didnt save significant amount of
    energy after flattening was done.
    Strategries considered: intermediate variables, caching
    """

    def __init__(self):
        super().__init__()
        self._reference_map: dict[str, list[tuple[int, str]]] = {}

    def flatten_dict(self, d: dict[str, Any], parent_key: str = ""):
        """Recursively flatten a nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}_{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)

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

    def find_dict_assignments(self, tree: ast.AST, name: str):
        """Find and extract dictionary assignments from AST."""
        dict_assignments = {}

        class DictVisitor(ast.NodeVisitor):
            def visit_Assign(self_, node: ast.Assign):
                if (
                    isinstance(node.value, ast.Dict)
                    and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id == name
                ):
                    dict_name = node.targets[0].id
                    dict_value = self.extract_dict_literal(node.value)
                    dict_assignments[dict_name] = dict_value
                self_.generic_visit(node)

        DictVisitor().visit(tree)

        return dict_assignments

    def collect_dict_references(self, tree: ast.AST) -> None:
        """Collect all dictionary access patterns."""
        parent_map = {}

        class ChainVisitor(ast.NodeVisitor):
            def visit_Subscript(self_, node: ast.Subscript):
                chain = []
                current = node
                while isinstance(current, ast.Subscript):
                    if isinstance(current.slice, ast.Constant):
                        chain.append(current.slice.value)
                    current = current.value

                if isinstance(current, ast.Name):
                    base_var = current.id
                    # Only store the pattern if we're at a leaf node (not part of another subscript)
                    parent = parent_map.get(node)
                    if not isinstance(parent, ast.Subscript):
                        if chain:
                            # Use single and double quotes in case user uses either
                            joined_double = "][".join(f'"{k}"' for k in reversed(chain))
                            access_pattern_double = f"{base_var}[{joined_double}]"

                            flattened_key = "_".join(str(k) for k in reversed(chain))
                            flattened_reference = f'{base_var}["{flattened_key}"]'

                            if access_pattern_double not in self._reference_map:
                                self._reference_map[access_pattern_double] = []

                            self._reference_map[access_pattern_double].append(
                                (node.lineno, flattened_reference)
                            )

                for child in ast.iter_child_nodes(node):
                    parent_map[child] = node
                self_.generic_visit(node)

        ChainVisitor().visit(tree)

    def generate_flattened_access(self, base_var: str, access_chain: list[str]) -> str:
        """Generate flattened dictionary key."""
        joined = "_".join(k.strip("'\"") for k in access_chain)
        return f"{base_var}_{joined}"

    def refactor(
        self,
        input_file: Path,
        smell: LECSmell,
        output_file: Path,
        overwrite: bool = True,
    ):
        """Refactor long element chains using the most appropriate strategy."""
        line_number = smell["occurences"][0]["line"]
        temp_filename = output_file

        with input_file.open() as f:
            content = f.read()
            lines = content.splitlines(keepends=True)
            tree = ast.parse(content)

        dict_name = ""
        # Traverse the AST
        for node in ast.walk(tree):
            if isinstance(
                node, ast.Subscript
            ):  # Check if the node is a Subscript (e.g., dictionary access)
                if hasattr(node, "lineno") and node.lineno == line_number:  # Check line number
                    if isinstance(
                        node.value, ast.Name
                    ):  # Ensure the value being accessed is a variable (dictionary)
                        dict_name = node.value.id  # Extract the name of the dictionary

        # Find dictionary assignments and collect references
        dict_assignments = self.find_dict_assignments(tree, dict_name)

        self._reference_map.clear()
        self.collect_dict_references(tree)

        new_lines = lines.copy()
        processed_patterns = set()

        for name, value in dict_assignments.items():
            flat_dict = self.flatten_dict(value)
            dict_def = f"{name} = {flat_dict!r}\n"

            # Update all references to this dictionary
            for pattern, occurrences in self._reference_map.items():
                if pattern.startswith(name) and pattern not in processed_patterns:
                    for line_num, flattened_reference in occurrences:
                        if line_num - 1 < len(new_lines):
                            line = new_lines[line_num - 1]
                            new_lines[line_num - 1] = line.replace(pattern, flattened_reference)
                    processed_patterns.add(pattern)

            # Update dictionary definition
            for i, line in enumerate(lines):
                if re.match(rf"\s*{name}\s*=", line):
                    new_lines[i] = " " * (len(line) - len(line.lstrip())) + dict_def

                    # Remove the following lines of the original nested dictionary
                    j = i + 1
                    while j < len(new_lines) and (
                        new_lines[j].strip().startswith('"') or new_lines[j].strip().startswith("}")
                    ):
                        new_lines[j] = ""  # Mark for removal
                        j += 1
                    break

        temp_file_path = temp_filename
        # Write the refactored code to a new temporary file
        with temp_file_path.open("w") as temp_file:
            temp_file.writelines(new_lines)

        if overwrite:
            with input_file.open("w") as f:
                f.writelines(new_lines)

        logging.info(f"Refactoring completed and saved to: {temp_file_path}")
