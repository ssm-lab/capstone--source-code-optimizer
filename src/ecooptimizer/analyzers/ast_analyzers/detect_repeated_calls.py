import ast
from collections import defaultdict
from pathlib import Path
import astor

from ecooptimizer.data_types.custom_fields import CRCInfo, Occurence
from ecooptimizer.data_types.smell import CRCSmell
from ecooptimizer.utils.smell_enums import CustomSmell


IGNORED_PRIMITIVE_BUILTINS = {"abs", "round"}  # Built-ins safe to ignore when used with primitives
IGNORED_CONSTRUCTORS = {"set", "list", "dict", "tuple"}  # Constructors to ignore
EXPENSIVE_BUILTINS = {
    "max",
    "sum",
    "sorted",
    "min",
}  # Built-ins to track when argument is non-primitive


def is_primitive_expression(node: ast.AST):
    """Returns True if the AST node is a primitive (int, float, str, bool), including negative numbers."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float, str, bool)):
        return True
    if (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, (ast.UAdd, ast.USub))
        and isinstance(node.operand, ast.Constant)
    ):
        return isinstance(node.operand.value, (int, float))
    return False


def detect_repeated_calls(file_path: Path, tree: ast.AST, threshold: int = 2):
    results: list[CRCSmell] = []

    source_code = file_path.read_text()

    def match_quote_style(source: str, function_call: str):
        """Detect whether the function call uses single or double quotes in the source."""
        if function_call.replace('"', "'") in source:
            return "'"
        return '"'

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.For, ast.While)):
            call_counts: dict[str, list[ast.Call]] = defaultdict(list)
            assigned_calls = set()
            modified_objects = {}
            call_lines = {}

            # Track assignments (only calls assigned to a variable should be considered)
            for subnode in ast.walk(node):
                if isinstance(subnode, ast.Assign) and isinstance(subnode.value, ast.Call):
                    call_repr = astor.to_source(subnode.value).strip()
                    assigned_calls.add(call_repr)

            # Track object attribute modifications (e.g., obj.value = 10)
            for subnode in ast.walk(node):
                if isinstance(subnode, ast.Assign) and isinstance(
                    subnode.targets[0], ast.Attribute
                ):
                    obj_name = astor.to_source(subnode.targets[0].value).strip()
                    modified_objects[obj_name] = subnode.lineno

            # Track function calls
            for subnode in ast.walk(node):
                if isinstance(subnode, ast.Call):
                    raw_call_string = astor.to_source(subnode).strip()
                    call_line = subnode.lineno

                    preferred_quote = match_quote_style(source_code, raw_call_string)
                    callString = raw_call_string.replace("'", preferred_quote).replace(
                        '"', preferred_quote
                    )

                    # Ignore built-in functions when their argument is a primitive
                    if isinstance(subnode.func, ast.Name):
                        func_name = subnode.func.id

                        if func_name in IGNORED_CONSTRUCTORS:
                            continue

                        if func_name in IGNORED_PRIMITIVE_BUILTINS:
                            if len(subnode.args) == 1 and is_primitive_expression(subnode.args[0]):
                                continue

                        if func_name in EXPENSIVE_BUILTINS:
                            if len(subnode.args) == 1 and not is_primitive_expression(
                                subnode.args[0]
                            ):
                                call_counts[callString].append(subnode)
                            continue

                        # Check if it's a class by looking for capitalized names (heuristic)
                        if func_name[0].isupper():
                            continue

                    obj_name = (
                        astor.to_source(subnode.func.value).strip()
                        if isinstance(subnode.func, ast.Attribute)
                        else None
                    )

                    if obj_name:
                        if obj_name in modified_objects and modified_objects[obj_name] < call_line:
                            continue

                    if raw_call_string in assigned_calls:
                        call_counts[raw_call_string].append(subnode)
                        call_lines[raw_call_string] = call_line

            # Identify repeated calls
            for callString, occurrences in call_counts.items():
                if len(occurrences) >= threshold:
                    preferred_quote = match_quote_style(source_code, callString)
                    normalized_callString = callString.replace("'", preferred_quote).replace(
                        '"', preferred_quote
                    )

                    smell = CRCSmell(
                        path=str(file_path),
                        type="performance",
                        obj=None,
                        module=file_path.stem,
                        symbol="cached-repeated-calls",
                        message=f"Repeated function call detected ({len(occurrences)}/{threshold}). Consider caching the result: {normalized_callString}",
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
                        additionalInfo=CRCInfo(
                            repetitions=len(occurrences), callString=normalized_callString
                        ),
                    )
                    results.append(smell)

    return results
