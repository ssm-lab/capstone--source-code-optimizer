import logging
from pathlib import Path
import re
from ..testing.run_tests import run_tests
from .base_refactorer import BaseRefactorer
from ..data_wrappers.smell import Smell


class LongMessageChainRefactorer(BaseRefactorer):
    """
    Refactorer that targets long method chains to improve performance.
    """

    def __init__(self, output_dir: Path):
        super().__init__(output_dir)

    @staticmethod
    def remove_unmatched_brackets(input_string):
        """
        Removes unmatched brackets from the input string.

        Args:
            input_string (str): The string to process.

        Returns:
            str: The string with unmatched brackets removed.
        """
        stack = []
        indexes_to_remove = set()

        # Iterate through the string to find unmatched brackets
        for i, char in enumerate(input_string):
            if char == "(":
                stack.append(i)
            elif char == ")":
                if stack:
                    stack.pop()  # Matched bracket, remove from stack
                else:
                    indexes_to_remove.add(i)  # Unmatched closing bracket

        # Add any unmatched opening brackets left in the stack
        indexes_to_remove.update(stack)

        # Build the result string without unmatched brackets
        result = "".join(char for i, char in enumerate(input_string) if i not in indexes_to_remove)

        return result

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

        # Check if the line contains an f-string
        f_string_pattern = r"f\".*?\""
        if re.search(f_string_pattern, line_with_chain):
            # Extract the f-string part and its methods
            f_string_content = re.search(f_string_pattern, line_with_chain).group()  # type: ignore
            remaining_chain = line_with_chain.split(f_string_content, 1)[-1]

            # Start refactoring
            refactored_lines = []

            if remaining_chain.strip():
                # Split the chain into method calls
                method_calls = re.split(r"\.(?![^()]*\))", remaining_chain.strip())

                # Handle the first method call directly on the f-string or as intermediate_0
                refactored_lines.append(f"{leading_whitespace}intermediate_0 = {f_string_content}")
                counter = 0
                # Handle remaining method calls
                for i, method in enumerate(method_calls, start=1):
                    if method.strip():
                        if i < len(method_calls):
                            refactored_lines.append(
                                f"{leading_whitespace}intermediate_{counter+1} = intermediate_{counter}.{method.strip()}"
                            )
                            counter += 1
                        else:
                            # Final result
                            refactored_lines.append(
                                f"{leading_whitespace}result = intermediate_{counter}.{LongMessageChainRefactorer.remove_unmatched_brackets(method.strip())}"
                            )
                            counter += 1
            else:
                refactored_lines.append(
                    f"{leading_whitespace}result = {LongMessageChainRefactorer.remove_unmatched_brackets(f_string_content)}"
                )

            # Add final print statement or function call
            refactored_lines.append(f"{leading_whitespace}print(result)\n")

            # Replace the original line with the refactored lines
            lines[line_number - 1] = "\n".join(refactored_lines) + "\n"
        else:
            # Handle non-f-string long method chains (existing logic)
            chain_content = re.sub(r"^\s*print\((.*)\)\s*$", r"\1", line_with_chain)
            method_calls = re.split(r"\.(?![^()]*\))", chain_content)

            if len(method_calls) > 2:
                refactored_lines = []
                base_var = method_calls[0].strip()
                refactored_lines.append(f"{leading_whitespace}intermediate_0 = {base_var}")

                for i, method in enumerate(method_calls[1:], start=1):
                    if i < len(method_calls) - 1:
                        refactored_lines.append(
                            f"{leading_whitespace}intermediate_{i} = intermediate_{i-1}.{method.strip()}"
                        )
                    else:
                        refactored_lines.append(
                            f"{leading_whitespace}result = intermediate_{i-1}.{method.strip()}"
                        )

                refactored_lines.append(f"{leading_whitespace}print(result)\n")
                lines[line_number - 1] = "\n".join(refactored_lines) + "\n"

        # Write the refactored file
        with temp_filename.open("w") as f:
            f.writelines(lines)

        logging.info(f"Refactored temp file saved to {temp_filename}")

        # Log completion
        # Measure emissions of the modified code
        final_emission = self.measure_energy(temp_filename)

        if not final_emission:
            # os.remove(temp_file_path)
            logging.info(
                f"Could not measure emissions for '{temp_filename.name}'. Discarded refactoring."
            )
            return

        # Check for improvement in emissions
        if self.check_energy_improvement(initial_emissions, final_emission):
            # If improved, replace the original file with the modified content
            if run_tests() == 0:
                logging.info("All test pass! Functionality maintained.")
                # shutil.move(temp_file_path, file_path)
                logging.info(
                    f'Refactored long message chain on line {pylint_smell["line"]} and saved.\n'
                )
                return

            logging.info("Tests Fail! Discarded refactored changes")

        else:
            logging.info(
                "No emission improvement after refactoring. Discarded refactored changes.\n"
            )

        # Remove the temporary file if no energy improvement or failing tests
        # os.remove(temp_file_path)
