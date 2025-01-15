import ast
from collections import defaultdict
from pathlib import Path
import astor


def detect_repeated_calls(file_path: Path, tree: ast.AST, threshold: int = 2):
    """
    Detects repeated function calls within a given AST (Abstract Syntax Tree).

    Parameters:
        file_path (Path): The file path to analyze.
        tree (ast.AST): The Abstract Syntax Tree (AST) of the source code.
        threshold (int, optional): The minimum number of repetitions of a function call to be considered a performance issue. Default is 2.

    Returns:
        list[dict]: A list of dictionaries containing details about detected performance smells.
    """
    results = []
    messageId = "CRC001"

    # Traverse the AST nodes
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.For, ast.While)):
            call_counts = defaultdict(list)  # Stores call occurrences
            modified_lines = set()  # Tracks lines where variables are modified

            # Detect lines with variable assignments or modifications
            for subnode in ast.walk(node):
                if isinstance(subnode, (ast.Assign, ast.AugAssign)):
                    modified_lines.add(subnode.lineno)

            # Count occurrences of each function call within the node
            for subnode in ast.walk(node):
                if isinstance(subnode, ast.Call):
                    call_string = astor.to_source(subnode).strip()
                    call_counts[call_string].append(subnode)

            # Analyze the call counts to detect repeated calls
            for call_string, occurrences in call_counts.items():
                if len(occurrences) >= threshold:
                    # Check if the repeated calls are interrupted by modifications
                    skip_due_to_modification = any(
                        line in modified_lines
                        for start_line, end_line in zip(
                            [occ.lineno for occ in occurrences[:-1]],
                            [occ.lineno for occ in occurrences[1:]],
                        )
                        for line in range(start_line + 1, end_line)
                    )

                    if skip_due_to_modification:
                        continue

                    # Create a performance smell entry
                    smell = {
                        "absolutePath": str(file_path),
                        "confidence": "UNDEFINED",
                        "occurrences": [
                            {
                                "line": occ.lineno,
                                "column": occ.col_offset,
                                "call_string": call_string,
                            }
                            for occ in occurrences
                        ],
                        "repetitions": len(occurrences),
                        "message": f"Repeated function call detected ({len(occurrences)}/{threshold}). "
                        f"Consider caching the result: {call_string}",
                        "messageId": messageId,
                        "module": file_path.name,
                        "path": str(file_path),
                        "symbol": "repeated-calls",
                        "type": "convention",
                    }
                    results.append(smell)

    return results
