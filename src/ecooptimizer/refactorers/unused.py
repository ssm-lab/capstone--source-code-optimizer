import logging
from pathlib import Path

from ..refactorers.base_refactorer import BaseRefactorer
from ..data_types.smell import UVASmell


class RemoveUnusedRefactorer(BaseRefactorer[UVASmell]):
    def __init__(self):
        super().__init__()

    def refactor(
        self,
        target_file: Path,
        source_dir: Path,  # noqa: ARG002
        smell: UVASmell,
        output_file: Path,
        overwrite: bool = True,
    ):
        """
        Refactors unused imports, variables and class attributes by removing lines where they appear.
        Modifies the specified instance in the file if it results in lower emissions.

        :param target_file: Path to the file to be refactored.
        :param smell: Dictionary containing details of the Pylint smell, including the line number.
        :param initial_emission: Initial emission value before refactoring.
        """
        line_number = smell.occurences[0].line
        code_type = smell.messageId
        logging.info(
            f"Applying 'Remove Unused Stuff' refactor on '{target_file.name}' at line {line_number} for identified code smell."
        )

        # Load the source code as a list of lines
        with target_file.open() as file:
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
        temp_file_path = output_file

        with temp_file_path.open("w") as temp_file:
            temp_file.writelines(modified_lines)

        if overwrite:
            with target_file.open("w") as f:
                f.writelines(modified_lines)

        logging.info(f"Refactoring completed and saved to: {temp_file_path}")
