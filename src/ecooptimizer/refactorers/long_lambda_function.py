import logging
from pathlib import Path
import re
from .base_refactorer import BaseRefactorer
from ecooptimizer.data_wrappers.smell import Smell


class LongLambdaFunctionRefactorer(BaseRefactorer):
    """
    Refactorer that targets long lambda functions by converting them into normal functions.
    """

    def __init__(self, output_dir: Path):
        super().__init__(output_dir)

    @staticmethod
    def truncate_at_top_level_comma(body: str) -> str:
        """
        Truncate the lambda body at the first top-level comma, ignoring commas
        within nested parentheses, brackets, or braces.
        """
        truncated_body = []
        open_parens = 0

        for char in body:
            if char in "([{":
                open_parens += 1
            elif char in ")]}":
                open_parens -= 1
            elif char == "," and open_parens == 0:
                # Stop at the first top-level comma
                break

            truncated_body.append(char)

        return "".join(truncated_body).strip()

    def refactor(self, file_path: Path, pylint_smell: Smell):
        """
        Refactor long lambda functions by converting them into normal functions
        and writing the refactored code to a new file.
        """
        # Extract details from pylint_smell
        line_number = pylint_smell["line"]
        temp_filename = self.temp_dir / Path(f"{file_path.stem}_LLFR_line_{line_number}.py")

        logging.info(
            f"Applying 'Lambda to Function' refactor on '{file_path.name}' at line {line_number} for identified code smell."
        )

        # Read the original file
        with file_path.open() as f:
            lines = f.readlines()

        # Capture the entire logical line containing the lambda
        current_line = line_number - 1
        lambda_lines = [lines[current_line].rstrip()]
        while not lambda_lines[-1].strip().endswith(")"):  # Continue until the block ends
            current_line += 1
            lambda_lines.append(lines[current_line].rstrip())
        full_lambda_line = " ".join(lambda_lines).strip()

        # Extract leading whitespace for correct indentation
        leading_whitespace = re.match(r"^\s*", lambda_lines[0]).group()  # type: ignore

        # Match and extract the lambda content using regex
        lambda_match = re.search(r"lambda\s+([\w, ]+):\s+(.+)", full_lambda_line)
        if not lambda_match:
            logging.warning(f"No valid lambda function found on line {line_number}.")
            return

        # Extract arguments and body of the lambda
        lambda_args = lambda_match.group(1).strip()
        lambda_body_before = lambda_match.group(2).strip()
        lambda_body_before = LongLambdaFunctionRefactorer.truncate_at_top_level_comma(
            lambda_body_before
        )
        print("1:", lambda_body_before)

        # Ensure that the lambda body does not contain extra trailing characters
        # Remove any trailing commas or mismatched closing brackets
        lambda_body = re.sub(r",\s*\)$", "", lambda_body_before).strip()

        lambda_body_no_extra_space = re.sub(r"\s{2,}", " ", lambda_body)
        # Generate a unique function name
        function_name = f"converted_lambda_{line_number}"

        # Create the new function definition
        function_def = (
            f"{leading_whitespace}def {function_name}({lambda_args}):\n"
            f"{leading_whitespace}result = {lambda_body_no_extra_space}\n"
            f"{leading_whitespace}return result\n\n"
        )

        # Find the start of the block containing the lambda
        block_start = line_number - 1
        while block_start > 0 and not lines[block_start - 1].strip().endswith(":"):
            block_start -= 1

        # Determine the appropriate scope for the new function
        block_indentation = re.match(r"^\s*", lines[block_start]).group()  # type: ignore
        adjusted_function_def = function_def.replace(leading_whitespace, block_indentation, 1)

        # Replace the lambda usage with the function call
        replacement_indentation = re.match(r"^\s*", lambda_lines[0]).group()  # type: ignore
        refactored_line = str(full_lambda_line).replace(
            f"lambda {lambda_args}: {lambda_body}",
            f"{function_name}",
        )
        # Add the indentation at the beginning of the refactored line
        refactored_line = f"{replacement_indentation}{refactored_line.strip()}"
        # Extract the initial leading whitespace
        match = re.match(r"^\s*", refactored_line)
        leading_whitespace = match.group() if match else ""

        # Remove all whitespace except the initial leading whitespace
        refactored_line = re.sub(r"\s+", "", refactored_line)

        # Insert newline after commas and follow with leading whitespace
        refactored_line = re.sub(r",(?![^,]*$)", f",\n{leading_whitespace}", refactored_line)
        refactored_line = re.sub(r"\)$", "", refactored_line)  # remove bracket
        refactored_line = f"{leading_whitespace}{refactored_line}"

        # Insert the new function definition above the block
        lines.insert(block_start, adjusted_function_def)
        lines[line_number : current_line + 1] = [refactored_line + "\n"]

        # Write the refactored code to a new temporary file
        with temp_filename.open("w") as temp_file:
            temp_file.writelines(lines)

        with file_path.open("w") as f:
            f.writelines(lines)

        logging.info(f"Refactoring completed and saved to: {temp_filename}")
