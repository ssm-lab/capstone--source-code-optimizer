import logging
from pathlib import Path
import astor
import ast
from ast import NodeTransformer

from ..testing.run_tests import run_tests

from .base_refactorer import BaseRefactorer

from ..data_wrappers.smell import Smell


class MakeStaticRefactorer(BaseRefactorer, NodeTransformer):
    """
    Refactorer that targets methods that don't use any class attributes and makes them static to improve performance
    """

    def __init__(self):
        super().__init__()
        self.target_line = None

    def refactor(self, file_path: Path, pylint_smell: Smell, initial_emissions: float):
        """
        Perform refactoring

        :param file_path: absolute path to source code
        :param pylint_smell: pylint code for smell
        :param initial_emission: inital carbon emission prior to refactoring
        """
        self.target_line = pylint_smell["line"]
        logging.info(
            f"Applying 'Make Method Static' refactor on '{file_path.name}' at line {self.target_line} for identified code smell."
        )
        with file_path.open() as f:
            code = f.read()

        # Parse the code into an AST
        tree = ast.parse(code)

        # Apply the transformation
        modified_tree = self.visit(tree)

        # Convert the modified AST back to source code
        modified_code = astor.to_source(modified_tree)

        temp_file_path = self.temp_dir / Path(f"{file_path.stem}_MIMR_line_{self.target_line}.py")

        with temp_file_path.open("w") as temp_file:
            temp_file.write(modified_code)

        # Measure emissions of the modified code
        final_emission = self.measure_energy(temp_file_path)

        if not final_emission:
            # os.remove(temp_file_path)
            logging.info(
                f"Could not measure emissions for '{temp_file_path.name}'. Discarded refactoring."
            )
            return

        # Check for improvement in emissions
        if self.check_energy_improvement(initial_emissions, final_emission):
            # If improved, replace the original file with the modified content

            if run_tests() == 0:
                logging.info("All test pass! Functionality maintained.")
                # shutil.move(temp_file_path, file_path)
                logging.info(
                    f"Refactored 'Member Ignoring Method' to static method on line {self.target_line} and saved.\n"
                )
                return

            logging.info("Tests Fail! Discarded refactored changes")

        else:
            logging.info(
                "No emission improvement after refactoring. Discarded refactored changes.\n"
            )

        # Remove the temporary file if no energy improvement or failing tests
        # os.remove(temp_file_path)

    def visit_FunctionDef(self, node):  # noqa: ANN001
        if node.lineno == self.target_line:
            # Step 1: Add the decorator
            decorator = ast.Name(id="staticmethod", ctx=ast.Load())
            node.decorator_list.append(decorator)

            # Step 2: Remove 'self' from the arguments if it exists
            if node.args.args and node.args.args[0].arg == "self":
                node.args.args.pop(0)
        # Add the decorator to the function's decorator list
        return node
