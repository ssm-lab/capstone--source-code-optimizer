# refactorers/use_a_generator_refactorer.py

import ast
import astor  # For converting AST back to source code
import shutil
import os
from .base_refactorer import BaseRefactorer


class UseAGeneratorRefactorer(BaseRefactorer):
    def __init__(self, logger):
        """
        Initializes the UseAGeneratorRefactor with a file path, pylint
        smell, initial emission, and logger.

        :param file_path: Path to the file to be refactored.
        :param pylint_smell: Dictionary containing details of the Pylint smell.
        :param initial_emission: Initial emission value before refactoring.
        :param logger: Logger instance to handle log messages.
        """
        super().__init__(logger)

    def refactor(self, file_path: str, pylint_smell: object, initial_emissions: float):
        """
        Refactors an unnecessary list comprehension by converting it to a generator expression.
        Modifies the specified instance in the file directly if it results in lower emissions.
        """
        line_number = pylint_smell["line"]
        self.logger.log(
            f"Applying 'Use a Generator' refactor on '{os.path.basename(file_path)}' at line {line_number} for identified code smell."
        )

        # Load the source code as a list of lines
        with open(file_path, "r") as file:
            original_lines = file.readlines()

        # Check if the line number is valid within the file
        if not (1 <= line_number <= len(original_lines)):
            self.logger.log("Specified line number is out of bounds.\n")
            return

        # Target the specific line and remove leading whitespace for parsing
        line = original_lines[line_number - 1]
        stripped_line = line.lstrip()  # Strip leading indentation
        indentation = line[: len(line) - len(stripped_line)]  # Track indentation

        # Parse the line as an AST
        line_ast = ast.parse(
            stripped_line, mode="exec"
        )  # Use 'exec' mode for full statements

        # Look for a list comprehension within the AST of this line
        modified = False
        for node in ast.walk(line_ast):
            if isinstance(node, ast.ListComp):
                # Convert the list comprehension to a generator expression
                generator_expr = ast.GeneratorExp(
                    elt=node.elt, generators=node.generators
                )
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
            temp_file_path = f"{file_path}.temp"
            with open(temp_file_path, "w") as temp_file:
                temp_file.writelines(modified_lines)

            # Measure emissions of the modified code
            final_emission = self.measure_energy(temp_file_path)

            # Check for improvement in emissions
            if self.check_energy_improvement(initial_emissions, final_emission):
                # If improved, replace the original file with the modified content
                shutil.move(temp_file_path, file_path)
                self.logger.log(
                    f"Refactored list comprehension to generator expression on line {line_number} and saved.\n"
                )
            else:
                # Remove the temporary file if no improvement
                os.remove(temp_file_path)
                self.logger.log(
                    "No emission improvement after refactoring. Discarded refactored changes.\n"
                )
        else:
            self.logger.log(
                "No applicable list comprehension found on the specified line.\n"
            )

    def _replace_node(self, tree, old_node, new_node):
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
