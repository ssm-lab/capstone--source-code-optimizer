import ast
from pathlib import Path
from asttokens import ASTTokens

from ..base_refactorer import BaseRefactorer
from ...data_types.smell import UGESmell


class UseAGeneratorRefactorer(BaseRefactorer[UGESmell]):
    def __init__(self):
        super().__init__()

    def refactor(
        self,
        target_file: Path,
        source_dir: Path,  # noqa: ARG002
        smell: UGESmell,
        output_file: Path,
        overwrite: bool = True,
    ):
        """
        Refactors an unnecessary list comprehension by converting it to a generator expression.
        Modifies the specified instance in the file directly if it results in lower emissions.
        """
        line_number = smell.occurences[0].line
        start_column = smell.occurences[0].column
        end_column = smell.occurences[0].endColumn

        # Load the source file as a list of lines
        with target_file.open() as file:
            original_lines = file.readlines()

        # Check bounds for line number
        if not (1 <= line_number <= len(original_lines)):
            return

        # Extract the specific line to refactor
        target_line = original_lines[line_number - 1]

        # Preserve the original indentation
        leading_whitespace = target_line[: len(target_line) - len(target_line.lstrip())]

        # Remove leading whitespace for parsing
        stripped_line = target_line.lstrip()

        # Parse the stripped line
        try:
            atok = ASTTokens(stripped_line, parse=True)
            if not atok.tree:
                return
            target_ast = atok.tree
        except (SyntaxError, ValueError):
            return

        # modified = False

        # Traverse the AST and locate the list comprehension at the specified column range
        for node in ast.walk(target_ast):
            if isinstance(node, ast.ListComp):
                # Check if end_col_offset exists and is valid
                end_col_offset = getattr(node, "end_col_offset", None)
                if end_col_offset is None:
                    continue

                # Check if the node matches the specified column range
                if node.col_offset >= start_column - 1 and end_col_offset <= end_column:
                    # Calculate offsets relative to the original line
                    start_offset = node.col_offset + len(leading_whitespace)
                    end_offset = end_col_offset + len(leading_whitespace)

                    # Check if parentheses are already present
                    if target_line[start_offset - 1] == "(" and target_line[end_offset] == ")":
                        # Parentheses already exist, avoid adding redundant ones
                        refactored_code = (
                            target_line[:start_offset]
                            + f"{target_line[start_offset + 1 : end_offset - 1]}"
                            + target_line[end_offset:]
                        )
                    else:
                        # Add parentheses explicitly if not already wrapped
                        refactored_code = (
                            target_line[:start_offset]
                            + f"({target_line[start_offset + 1 : end_offset - 1]})"
                            + target_line[end_offset:]
                        )

                    original_lines[line_number - 1] = refactored_code
                    # modified = True
                    break

        if overwrite:
            with target_file.open("w") as f:
                f.writelines(original_lines)
        else:
            with output_file.open("w") as f:
                f.writelines(original_lines)
