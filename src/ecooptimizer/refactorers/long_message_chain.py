import logging
from pathlib import Path
import re

from testing.run_tests import run_tests
from .base_refactorer import BaseRefactorer

from data_wrappers.smell import Smell


class LongMessageChainRefactorer(BaseRefactorer):
    """
    Refactorer that targets long method chains to improve performance.
    """

    def __init__(self):
        super().__init__()

    def refactor(self, file_path: Path, pylint_smell: Smell, initial_emissions: float):
        """
        Refactor long message chains by breaking them into separate statements
        and writing the refactored code to a new file.
        """
        # Extract details from pylint_smell
        line_number = pylint_smell["line"]
        temp_filename = self.temp_dir / Path(f"{file_path.stem}_LMCR_line_{line_number}.py")

        logging.info(
            f"Applying 'Separate Statements' refactor on '{file_path.name}' at line {line_number} for identified code smell."
        )
        # Read the original file
        with file_path.open() as f:
            lines = f.readlines()

        # Identify the line with the long method chain
        line_with_chain = lines[line_number - 1].rstrip()

        # Extract leading whitespace for correct indentation
        leading_whitespace = re.match(r"^\s*", line_with_chain).group()  # type: ignore

        # Remove the function call wrapper if present (e.g., `print(...)`)
        chain_content = re.sub(r"^\s*print\((.*)\)\s*$", r"\1", line_with_chain)

        # Split the chain into individual method calls
        method_calls = re.split(r"\.(?![^()]*\))", chain_content)

        # Refactor if it's a long chain
        if len(method_calls) > 2:
            refactored_lines = []
            base_var = method_calls[0].strip()  # Initial part, e.g., `self.data[0]`
            refactored_lines.append(f"{leading_whitespace}intermediate_0 = {base_var}")

            # Generate intermediate variables for each method in the chain
            for i, method in enumerate(method_calls[1:], start=1):
                if i < len(method_calls) - 1:
                    refactored_lines.append(
                        f"{leading_whitespace}intermediate_{i} = intermediate_{i-1}.{method.strip()}"
                    )
                else:
                    # Final result to pass to function
                    refactored_lines.append(
                        f"{leading_whitespace}result = intermediate_{i-1}.{method.strip()}"
                    )

            # Add final function call with result
            refactored_lines.append(f"{leading_whitespace}print(result)\n")

            # Replace the original line with the refactored lines
            lines[line_number - 1] = "\n".join(refactored_lines) + "\n"

        temp_file_path = temp_filename
        # Write the refactored code to a new temporary file
        with temp_file_path.open("w") as temp_file:
            temp_file.writelines(lines)

        # Log completion
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
                    f"Refactored long message chain on line {pylint_smell["line"]} and saved.\n"
                )
                return

            logging.info("Tests Fail! Discarded refactored changes")

        else:
            logging.info(
                "No emission improvement after refactoring. Discarded refactored changes.\n"
            )

        # Remove the temporary file if no energy improvement or failing tests
        # os.remove(temp_file_path)
