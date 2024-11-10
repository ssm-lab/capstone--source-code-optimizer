import os
import shutil
from refactorers.base_refactorer import BaseRefactorer

class RemoveUnusedImportsRefactorer(BaseRefactorer):
    def __init__(self, logger):
        """
        Initializes the RemoveUnusedImportsRefactor with the specified logger.

        :param logger: Logger instance to handle log messages.
        """
        super().__init__(logger)

    def refactor(self, file_path: str, pylint_smell: object, initial_emissions: float):
        """
        Refactors unused imports by removing lines where they appear.
        Modifies the specified instance in the file if it results in lower emissions.

        :param file_path: Path to the file to be refactored.
        :param pylint_smell: Dictionary containing details of the Pylint smell, including the line number.
        :param initial_emission: Initial emission value before refactoring.
        """
        line_number = pylint_smell.get("line")
        self.logger.log(
            f"Applying 'Remove Unused Imports' refactor on '{os.path.basename(file_path)}' at line {line_number} for identified code smell."
        )

        # Load the source code as a list of lines
        with open(file_path, "r") as file:
            original_lines = file.readlines()

        # Check if the line number is valid within the file
        if not (1 <= line_number <= len(original_lines)):
            self.logger.log("Specified line number is out of bounds.\n")
            return

        # Remove the specified line if it's an unused import
        modified_lines = original_lines[:]
        del modified_lines[line_number - 1]

        # Write the modified content to a temporary file
        temp_file_path = f"{file_path}.temp"
        with open(temp_file_path, "w") as temp_file:
            temp_file.writelines(modified_lines)

        # Measure emissions of the modified code
        final_emissions = self.measure_energy(temp_file_path)

        # Check for improvement in emissions
        if self.check_energy_improvement(initial_emissions, final_emissions):
            # Replace the original file with the modified content if improved
            shutil.move(temp_file_path, file_path)
            self.logger.log(
                f"Removed unused import on line {line_number} and saved changes.\n"
            )
        else:
            # Remove the temporary file if no improvement
            os.remove(temp_file_path)
            self.logger.log(
                "No emission improvement after refactoring. Discarded refactored changes.\n"
            )