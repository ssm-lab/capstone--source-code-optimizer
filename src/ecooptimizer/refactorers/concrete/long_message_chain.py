from pathlib import Path
import re
from ..base_refactorer import BaseRefactorer
from ...data_types.smell import LMCSmell


class LongMessageChainRefactorer(BaseRefactorer[LMCSmell]):
    """
    Refactorer that targets long method chains to improve performance.
    """

    def __init__(self) -> None:
        super().__init__()

    def refactor(
        self,
        target_file: Path,
        source_dir: Path,  # noqa: ARG002
        smell: LMCSmell,
        output_file: Path,
        overwrite: bool = True,
    ):
        """
        Refactor long message chains by breaking them into separate statements
        and writing the refactored code to a new file.
        """
        # Extract details from smell
        line_number = smell.occurences[0].line
        # temp_filename = output_file

        # Read file content using read_text
        content = target_file.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=True)  # Preserve line endings

        # Identify the line with the long method chain
        line_with_chain = lines[line_number - 1].rstrip()

        # Extract leading whitespace for correct indentation
        leading_whitespace = re.match(r"^\s*", line_with_chain).group()  # type: ignore

        # Check if the line contains an f-string
        f_string_pattern = r"f\".*?\""
        if re.search(f_string_pattern, line_with_chain):
            # Determine if original was print or assignment
            is_print = line_with_chain.startswith("print(")
            original_var = None if is_print else line_with_chain.split("=", 1)[0].strip()

            # Extract f-string and methods
            f_string_content = re.search(f_string_pattern, line_with_chain).group()  # type: ignore
            remaining_chain = line_with_chain.split(f_string_content, 1)[-1].lstrip(".")

            method_calls = re.split(r"\.(?![^()]*\))", remaining_chain.strip())
            refactored_lines = []

            # Initial f-string assignment
            refactored_lines.append(f"{leading_whitespace}intermediate_0 = {f_string_content}")

            # Process method calls
            for i, method in enumerate(method_calls, start=1):
                method = method.strip()
                if not method:
                    continue

                if i < len(method_calls):
                    refactored_lines.append(
                        f"{leading_whitespace}intermediate_{i} = " f"intermediate_{i-1}.{method}"
                    )
                else:
                    # Final assignment using original variable name
                    if is_print:
                        refactored_lines.append(
                            f"{leading_whitespace}print(intermediate_{i-1}.{method})"
                        )
                    else:
                        refactored_lines.append(
                            f"{leading_whitespace}{original_var} = " f"intermediate_{i-1}.{method}"
                        )

            lines[line_number - 1] = "\n".join(refactored_lines) + "\n"

        else:
            # Handle non-f-string chains
            original_has_print = "print(" in line_with_chain
            chain_content = re.sub(r"^\s*print\((.*)\)\s*$", r"\1", line_with_chain)

            # Extract RHS if assignment exists
            if "=" in chain_content:
                chain_content = chain_content.split("=", 1)[1].strip()

            # Split chain after closing parentheses
            method_calls = re.split(r"(?<=\))\.", chain_content)

            if len(method_calls) > 1:
                refactored_lines = []
                base_var = method_calls[0].strip()
                refactored_lines.append(f"{leading_whitespace}intermediate_0 = {base_var}")

                # Process subsequent method calls
                for i, method in enumerate(method_calls[1:], start=1):
                    method = method.strip().lstrip(".")
                    if not method:
                        continue

                    if i < len(method_calls) - 1:
                        refactored_lines.append(
                            f"{leading_whitespace}intermediate_{i} = "
                            f"intermediate_{i-1}.{method}"
                        )
                    else:
                        # Preserve original assignment/print structure
                        if original_has_print:
                            refactored_lines.append(
                                f"{leading_whitespace}print(intermediate_{i-1}.{method})"
                            )
                        else:
                            original_assignment = line_with_chain.split("=", 1)[0].strip()
                            refactored_lines.append(
                                f"{leading_whitespace}{original_assignment} = "
                                f"intermediate_{i-1}.{method}"
                            )

                lines[line_number - 1] = "\n".join(refactored_lines) + "\n"

        # # Write the refactored file
        # with temp_filename.open("w") as f:
        #     f.writelines(lines)

        # Join lines and write using write_text
        new_content = "".join(lines)

        # Write to appropriate file based on overwrite flag
        if overwrite:
            target_file.write_text(new_content, encoding="utf-8")
        else:
            output_file.write_text(new_content, encoding="utf-8")

        self.modified_files.append(target_file)
