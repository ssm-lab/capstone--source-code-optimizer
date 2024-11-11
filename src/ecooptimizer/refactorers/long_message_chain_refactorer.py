import os
import re
import shutil

from testing.run_tests import run_tests
from .base_refactorer import BaseRefactorer


class LongMessageChainRefactorer(BaseRefactorer):
    """
    Refactorer that targets long method chains to improve performance.
    """

    def __init__(self, logger):
        super().__init__(logger)

    def refactor(self, file_path: str, pylint_smell: object, initial_emissions: float):
        """
        Refactor long message chains by breaking them into separate statements
        and writing the refactored code to a new file.
        """
        # Extract details from pylint_smell
        line_number = pylint_smell["line"]
        original_filename = os.path.basename(file_path)
        temp_filename = f"src/ecooptimizer/outputs/refactored_source/{os.path.splitext(original_filename)[0]}_LMCR_line_{line_number}.py"

        self.logger.log(
            f"Applying 'Separate Statements' refactor on '{os.path.basename(file_path)}' at line {line_number} for identified code smell."
        )
        # Read the original file
        with open(file_path, "r") as f:
            lines = f.readlines()

        # Identify the line with the long method chain
        line_with_chain = lines[line_number - 1].rstrip()

        # Extract leading whitespace for correct indentation
        leading_whitespace = re.match(r"^\s*", line_with_chain).group()

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
        with open(temp_filename, "w") as temp_file:
            temp_file.writelines(lines)

        # Log completion
        # Measure emissions of the modified code
        final_emission = self.measure_energy(temp_file_path)

        #Check for improvement in emissions
        if self.check_energy_improvement(initial_emissions, final_emission):
            # If improved, replace the original file with the modified content
            if run_tests() == 0:
                self.logger.log("All test pass! Functionality maintained.")
                # shutil.move(temp_file_path, file_path)
                self.logger.log(
                    f"Refactored long message chain on line {pylint_smell["line"]} and saved.\n"
                )
                return
            
            self.logger.log("Tests Fail! Discarded refactored changes")

        else:
            self.logger.log(
                "No emission improvement after refactoring. Discarded refactored changes.\n"
            )

        # Remove the temporary file if no energy improvement or failing tests
        # os.remove(temp_file_path)
