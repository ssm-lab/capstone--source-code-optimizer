# refactorers/use_a_generator_refactorer.py

import ast
import logging
from pathlib import Path
import astor  # For converting AST back to source code

from ..data_wrappers.smell import UGESmell

from .base_refactorer import BaseRefactorer


class UseAGeneratorRefactorer(BaseRefactorer):
    def __init__(self, output_dir: Path):
        """
        Initializes the UseAGeneratorRefactor with a file path, pylint
        smell, initial emission, and logger.

        :param file_path: Path to the file to be refactored.
        :param pylint_smell: Dictionary containing details of the Pylint smell.
        :param initial_emission: Initial emission value before refactoring.
        :param logger: Logger instance to handle log messages.
        """
        super().__init__(output_dir)

    def refactor(self, file_path: Path, pylint_smell: UGESmell, overwrite: bool = True):
        """
        Refactors an unnecessary list comprehension by converting it to a generator expression.
        Modifies the specified instance in the file directly if it results in lower emissions.
        """
        line_number = pylint_smell["occurences"][0]["line"]
        logging.info(
            f"Applying 'Use a Generator' refactor on '{file_path.name}' at line {line_number} for identified code smell."
        )

        # Load the source code as a list of lines
        with file_path.open() as file:
            original_lines = file.readlines()

        # Check if the line number is valid within the file
        if not (1 <= line_number <= len(original_lines)):
            logging.info("Specified line number is out of bounds.\n")
            return

        # Target the specific line and remove leading whitespace for parsing
        line = original_lines[line_number - 1]
        stripped_line = line.lstrip()  # Strip leading indentation
        indentation = line[: len(line) - len(stripped_line)]  # Track indentation

        # Parse the line as an AST
        line_ast = ast.parse(stripped_line, mode="exec")  # Use 'exec' mode for full statements

        # Look for a list comprehension within the AST of this line
        modified = False
        for node in ast.walk(line_ast):
            if isinstance(node, ast.ListComp):
                # Convert the list comprehension to a generator expression
                generator_expr = ast.GeneratorExp(elt=node.elt, generators=node.generators)
                ast.copy_location(generator_expr, node)

                # Replace the list comprehension node with the generator expression
                self._replace_node(line_ast, node, generator_expr)
                modified = True
                break

        if modified:
            # Convert the modified AST back to source code
            modified_line = astor.to_source(line_ast).strip()
            # Reapply the original indentation
            modified_lines = original_lines[:]
            modified_lines[line_number - 1] = indentation + modified_line + "\n"

            # Temporarily write the modified content to a temporary file
            temp_file_path = self.temp_dir / Path(f"{file_path.stem}_UGENR_line_{line_number}.py")

            with temp_file_path.open("w") as temp_file:
                temp_file.writelines(modified_lines)

            if overwrite:
                with file_path.open("w") as f:
                    f.writelines(modified_lines)

            logging.info(f"Refactoring completed and saved to: {temp_file_path}")

    def _replace_node(self, tree: ast.Module, old_node: ast.ListComp, new_node: ast.GeneratorExp):
        """
        Helper function to replace an old AST node with a new one within a tree.

        :param tree: The AST tree or node containing the node to be replaced.
        :param old_node: The node to be replaced.
        :param new_node: The new node to replace it with.
        """
        for parent in ast.walk(tree):
            for field, value in ast.iter_fields(parent):
                if isinstance(value, list):
                    for i, item in enumerate(value):
                        if item is old_node:
                            value[i] = new_node
                            return
                elif value is old_node:
                    setattr(parent, field, new_node)
                    return
