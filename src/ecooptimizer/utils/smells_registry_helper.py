import ast
from pathlib import Path
from typing import Any, Callable

from ..data_wrappers.smell import Smell
from ..data_wrappers.smell_registry import SmellRegistry


def filter_smells_by_method(
    smell_registry: dict[str, SmellRegistry], method: str
) -> dict[str, SmellRegistry]:
    filtered = {
        name: smell
        for name, smell in smell_registry.items()
        if smell["enabled"]
        and (
            (method == "pylint" and smell["analyzer_method"] == "pylint")
            or (method == "ast" and callable(smell["analyzer_method"]))
        )
    }
    return filtered


def generate_pylint_options(filtered_smells: dict[str, SmellRegistry]) -> list[str]:
    pylint_smell_ids = []
    extra_pylint_options = [
        "--disable=all",
    ]

    for smell in filtered_smells.values():
        pylint_smell_ids.append(smell["id"])

        if smell.get("analyzer_options"):
            for param_data in smell["analyzer_options"].values():
                flag = param_data["flag"]
                value = param_data["value"]
                if value:
                    extra_pylint_options.append(f"{flag}={value}")

    extra_pylint_options.append(f"--enable={','.join(pylint_smell_ids)}")
    return extra_pylint_options


def generate_ast_options(
    filtered_smells: dict[str, SmellRegistry],
) -> list[tuple[Callable[[Path, ast.AST], list[Smell]], dict[str, Any]]]:
    ast_options = []
    for smell in filtered_smells.values():
        method = smell["analyzer_method"]
        options = smell.get("analyzer_options", {})
        ast_options.append((method, options))

    return ast_options
