import ast
from collections import defaultdict
from pathlib import Path

import astor

from ...data_types.custom_fields import CRCInfo, Occurence

from ...data_types.smell import CRCSmell

from ...utils.smell_enums import CustomSmell


def detect_repeated_calls(file_path: Path, tree: ast.AST, threshold: int = 3):
    results: list[CRCSmell] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.For, ast.While)):
            call_counts: dict[str, list[ast.Call]] = defaultdict(list)
            modified_lines = set()

            for subnode in ast.walk(node):
                if isinstance(subnode, (ast.Assign, ast.AugAssign)):
                    # targets = [target.id for target in getattr(subnode, "targets", []) if isinstance(target, ast.Name)]
                    modified_lines.add(subnode.lineno)

            for subnode in ast.walk(node):
                if isinstance(subnode, ast.Call):
                    callString = astor.to_source(subnode).strip()
                    call_counts[callString].append(subnode)

            for callString, occurrences in call_counts.items():
                if len(occurrences) >= threshold:
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

                    smell = CRCSmell(
                        path=str(file_path),
                        type="performance",
                        obj=None,
                        module=file_path.stem,
                        symbol="cached-repeated-calls",
                        message=f"Repeated function call detected ({len(occurrences)}/{threshold}). Consider caching the result: {callString}",
                        messageId=CustomSmell.CACHE_REPEATED_CALLS.value,
                        confidence="HIGH" if len(occurrences) > threshold else "MEDIUM",
                        occurences=[
                            Occurence(
                                line=occ.lineno,
                                endLine=occ.end_lineno,
                                column=occ.col_offset,
                                endColumn=occ.end_col_offset,
                            )
                            for occ in occurrences
                        ],
                        additionalInfo=CRCInfo(repetitions=len(occurrences), callString=callString),
                    )
                    results.append(smell)

    return results
