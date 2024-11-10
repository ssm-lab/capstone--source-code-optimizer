import os
import shutil
import astor
import ast
from ast import NodeTransformer

from .base_refactorer import BaseRefactorer


class MakeStaticRefactorer(BaseRefactorer, NodeTransformer):
    """
    Refactorer that targets methods that don't use any class attributes and makes them static to improve performance
    """

    def __init__(self, logger):
        super().__init__(logger)
        self.target_line = None

    def refactor(self, file_path: str, pylint_smell: object, initial_emissions: float):
        """
        Perform refactoring

        :param file_path: absolute path to source code
        :param pylint_smell: pylint code for smell
        :param initial_emission: inital carbon emission prior to refactoring
        """
        self.target_line = pylint_smell["line"]
        self.logger.log(
            f"Applying 'Make Method Static' refactor on '{os.path.basename(file_path)}' at line {self.target_line} for identified code smell."
        )
        with open(file_path, "r") as f:
            code = f.read()

        # Parse the code into an AST
        tree = ast.parse(code)

        # Apply the transformation
        modified_tree = self.visit(tree)

        # Convert the modified AST back to source code
        modified_code = astor.to_source(modified_tree)

        temp_file_path = f"{os.path.basename(file_path).split(".")[0]}_temp.py"
        with open(temp_file_path, "w") as temp_file:
            temp_file.write(modified_code)

        # Measure emissions of the modified code
        final_emission = self.measure_energy(temp_file_path)

        # Check for improvement in emissions
        if self.check_energy_improvement(initial_emissions, final_emission):
            # If improved, replace the original file with the modified content
            shutil.move(temp_file_path, file_path)
            self.logger.log(
                f"Refactored list comprehension to generator expression on line {self.target_line} and saved.\n"
            )
        else:
            # Remove the temporary file if no improvement
            os.remove(temp_file_path)
            self.logger.log(
                "No emission improvement after refactoring. Discarded refactored changes.\n"
            )
        

    def visit_FunctionDef(self, node):
        if node.lineno == self.target_line:
            # Step 1: Add the decorator
            decorator = ast.Name(id="staticmethod", ctx=ast.Load())
            node.decorator_list.append(decorator)

            # Step 2: Remove 'self' from the arguments if it exists
            if node.args.args and node.args.args[0].arg == 'self':
                node.args.args.pop(0)
        # Add the decorator to the function's decorator list
        return node
