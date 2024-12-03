import logging
from pathlib import Path
from refactorers.base_refactorer import BaseRefactorer
from testing.run_tests import run_tests

from data_wrappers.smell import Smell


class RemoveUnusedRefactorer(BaseRefactorer):
    def __init__(self):
        """
        Initializes the RemoveUnusedRefactor with the specified logger.

        :param logger: Logger instance to handle log messages.
        """
        super().__init__()

    def refactor(self, file_path: Path, pylint_smell: Smell, initial_emissions: float):
        """
        Refactors unused imports, variables and class attributes by removing lines where they appear.
        Modifies the specified instance in the file if it results in lower emissions.

        :param file_path: Path to the file to be refactored.
        :param pylint_smell: Dictionary containing details of the Pylint smell, including the line number.
        :param initial_emission: Initial emission value before refactoring.
        """
        line_number = pylint_smell.get("line")
        code_type = pylint_smell.get("messageId")
        logging.info(
            f"Applying 'Remove Unused Stuff' refactor on '{file_path.name}' at line {line_number} for identified code smell."
        )

        # Load the source code as a list of lines
        with file_path.open() as file:
            original_lines = file.readlines()

        # Check if the line number is valid within the file
        if not (1 <= line_number <= len(original_lines)):
            logging.info("Specified line number is out of bounds.\n")
            return

        # remove specified line
        modified_lines = original_lines[:]
        modified_lines[line_number - 1] = "\n"

        # for logging purpose to see what was removed
        if code_type == "W0611":  # UNUSED_IMPORT
            logging.info("Removed unused import.")
        elif code_type == "UV001":  # UNUSED_VARIABLE
            logging.info("Removed unused variable or class attribute")
        else:
            logging.info(
                "No matching refactor type found for this code smell but line was removed."
            )
            return

        # Write the modified content to a temporary file
        temp_file_path = self.temp_dir / Path(f"{file_path.stem}_UNSDR_line_{line_number}.py")

        with temp_file_path.open("w") as temp_file:
            temp_file.writelines(modified_lines)

        # Measure emissions of the modified code
        final_emissions = self.measure_energy(temp_file_path)

        if not final_emissions:
            # os.remove(temp_file_path)
            logging.info(
                f"Could not measure emissions for '{temp_file_path.name}'. Discarded refactoring."
            )
            return

        # shutil.move(temp_file_path, file_path)

        # check for improvement in emissions (for logging purposes only)
        if self.check_energy_improvement(initial_emissions, final_emissions):
            if run_tests() == 0:
                logging.info("All test pass! Functionality maintained.")
                logging.info(f"Removed unused stuff on line {line_number} and saved changes.\n")
                return

            logging.info("Tests Fail! Discarded refactored changes")

        else:
            logging.info(
                "No emission improvement after refactoring. Discarded refactored changes.\n"
            )

        # Remove the temporary file if no energy improvement or failing tests
        # os.remove(temp_file_path)
