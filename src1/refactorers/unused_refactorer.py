import os
import shutil
from refactorers.base_refactorer import BaseRefactorer
from testing.run_tests import run_tests

class RemoveUnusedRefactorer(BaseRefactorer):
    def __init__(self, logger):
        """
        Initializes the RemoveUnusedRefactor with the specified logger.

        :param logger: Logger instance to handle log messages.
        """
        super().__init__(logger)

    def refactor(self, file_path: str, pylint_smell: object, initial_emissions: float):
        """
        Refactors unused imports, variables and class attributes by removing lines where they appear.
        Modifies the specified instance in the file if it results in lower emissions.

        :param file_path: Path to the file to be refactored.
        :param pylint_smell: Dictionary containing details of the Pylint smell, including the line number.
        :param initial_emission: Initial emission value before refactoring.
        """
        line_number = pylint_smell.get("line")
        code_type = pylint_smell.get("message-id")
        print(code_type)
        self.logger.log(
            f"Applying 'Remove Unused Stuff' refactor on '{os.path.basename(file_path)}' at line {line_number} for identified code smell."
        )

        # Load the source code as a list of lines
        with open(file_path, "r") as file:
            original_lines = file.readlines()

        # Check if the line number is valid within the file
        if not (1 <= line_number <= len(original_lines)):
            self.logger.log("Specified line number is out of bounds.\n")
            return

        # remove specified line 
        modified_lines = original_lines[:]
        modified_lines[line_number - 1] = "\n"

        # for logging purpose to see what was removed
        if code_type == "W0611":  # UNUSED_IMPORT
            self.logger.log("Removed unused import.")
        elif code_type == "UV001":  # UNUSED_VARIABLE
            self.logger.log("Removed unused variable or class attribute")
        else:
            self.logger.log("No matching refactor type found for this code smell but line was removed.")
            return

        # Write the modified content to a temporary file
        original_filename = os.path.basename(file_path)
        temp_file_path = f"src1/outputs/refactored_source/{os.path.splitext(original_filename)[0]}_UNSDR_line_{line_number}.py"

        with open(temp_file_path, "w") as temp_file:
            temp_file.writelines(modified_lines)

        # Measure emissions of the modified code
        final_emissions = self.measure_energy(temp_file_path)

        # shutil.move(temp_file_path, file_path)

        # check for improvement in emissions (for logging purposes only)
        if self.check_energy_improvement(initial_emissions, final_emissions):
            if run_tests() == 0:
                self.logger.log("All test pass! Functionality maintained.")
                self.logger.log(
                    f"Removed unused stuff on line {line_number} and saved changes.\n"
                )
                return
            
            self.logger.log("Tests Fail! Discarded refactored changes")

        else:
            self.logger.log(
                "No emission improvement after refactoring. Discarded refactored changes.\n"
            )

        # Remove the temporary file if no energy improvement or failing tests
        # os.remove(temp_file_path)