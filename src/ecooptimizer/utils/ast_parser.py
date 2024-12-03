import ast
from pathlib import Path


def parse_line(file: Path, line: int):
    """
    Parses a specific line of code from a file into an AST node.

    :param file: Path to the file to parse.
    :param line: Line number to parse (1-based index).
    :return: AST node of the line, or None if a SyntaxError occurs.
    """
    with file.open() as f:
        file_lines = f.readlines()  # Read all lines of the file into a list
    try:
        # Parse the specified line (adjusted for 0-based indexing) into an AST node
        node = ast.parse(file_lines[line - 1].strip())
    except SyntaxError:
        # Return None if there is a syntax error in the specified line
        return None

    return node  # Return the parsed AST node for the line


def parse_file(file: Path):
    """
    Parses the entire contents of a file into an AST node.

    :param file: Path to the file to parse.
    :return: AST node of the entire file contents.
    """
    with file.open() as f:
        source = f.read()  # Read the full content of the file

    return ast.parse(source)  # Parse the entire content as an AST node
