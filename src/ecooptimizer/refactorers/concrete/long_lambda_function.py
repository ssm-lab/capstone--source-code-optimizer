from pathlib import Path
import re
from ..base_refactorer import BaseRefactorer
from ...data_types.smell import LLESmell


class LongLambdaFunctionRefactorer(BaseRefactorer[LLESmell]):
    """
    Refactorer that targets long lambda functions by converting them into normal functions.
    """

    def __init__(self) -> None:
        super().__init__()

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

    def refactor(
        self,
        target_file: Path,
        source_dir: Path,  # noqa: ARG002
        smell: LLESmell,
        output_file: Path,
        overwrite: bool = True,
    ):
        """
        Refactor long lambda functions by converting them into normal functions
        and writing the refactored code to a new file.
        """
        # Extract details from smell
        line_number = smell.occurences[0].line

        # Read the original file
        content = target_file.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=True)

        # Capture the entire logical line containing the lambda
        current_line = line_number - 1
        lambda_lines = [lines[current_line].rstrip()]

        # Check if lambda is wrapped in parentheses
        has_parentheses = lambda_lines[0].strip().startswith("(")

        # Find continuation lines only if needed
        if has_parentheses:
            while current_line < len(lines) - 1 and not lambda_lines[
                -1
            ].strip().endswith(")"):
                current_line += 1
                lambda_lines.append(lines[current_line].rstrip())
        else:
            # Handle single-line lambda
            lambda_lines = [lines[current_line].rstrip()]

        full_lambda_line = " ".join(lambda_lines).strip()

        # Remove surrounding parentheses if present
        if has_parentheses:
            full_lambda_line = re.sub(r"^\((.*)\)$", r"\1", full_lambda_line)

        # Extract leading whitespace for correct indentation
        original_indent = re.match(r"^\s*", lambda_lines[0]).group()  # type: ignore

        # Use different regex based on whether the lambda line starts with a parenthesis
        if has_parentheses:
            lambda_match = re.search(
                r"lambda\s+([\w, ]+):\s+(.+?)(?=\s*\))", full_lambda_line
            )
        else:
            lambda_match = re.search(r"lambda\s+([\w, ]+):\s+(.+)", full_lambda_line)

        if not lambda_match:
            return

        # Extract arguments and body of the lambda
        lambda_args = lambda_match.group(1).strip()
        lambda_body_before = lambda_match.group(2).strip()
        lambda_body_before = LongLambdaFunctionRefactorer.truncate_at_top_level_comma(
            lambda_body_before
        )

        # Ensure that the lambda body does not contain extra trailing characters
        # Remove any trailing commas or mismatched closing brackets
        lambda_body = re.sub(r",\s*\)$", "", lambda_body_before).strip()

        lambda_body_no_extra_space = re.sub(r"\s{2,}", " ", lambda_body)
        # Generate a unique function name
        function_name = f"converted_lambda_{line_number}"

        # Find the start of the block containing the lambda
        original_indent_len = len(original_indent)
        block_start = line_number - 1
        while block_start > 0:
            prev_line = lines[block_start - 1].rstrip()
            prev_indent = len(re.match(r"^\s*", prev_line).group())  # type: ignore
            if prev_line.endswith(":") and prev_indent < original_indent_len:
                break
            block_start -= 1

        # Get proper block indentation
        block_indentation = re.match(r"^\s*", lines[block_start]).group()  # type: ignore
        function_indent = block_indentation
        body_indent = function_indent + " " * 4

        # Create properly indented function definition
        function_def = (
            f"{function_indent}def {function_name}({lambda_args}):\n"
            f"{body_indent}result = {lambda_body_no_extra_space}\n"
            f"{body_indent}return result\n\n"
        )

        # Prepare refactored line with original indentation
        replacement_line = full_lambda_line.replace(
            f"lambda {lambda_args}: {lambda_body}", function_name
        )
        refactored_line = f"{original_indent}{replacement_line.strip()}"

        # Split multi-line function definition into individual lines
        function_lines = function_def.splitlines(keepends=True)

        # Replace the lambda line with the refactored line in place
        lines[current_line] = f"{refactored_line}\n"

        # Insert the new function definition immediately at the beginning of the block
        lines.insert(block_start, "".join(function_lines))

        # Write changes
        new_content = "".join(lines)
        if overwrite:
            target_file.write_text(new_content, encoding="utf-8")
        else:
            output_file.write_text(new_content, encoding="utf-8")

        self.modified_files.append(target_file)
