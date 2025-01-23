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


def generate_ast_analyzers(
    filtered_smells: dict[str, SmellRegistry],
) -> list[Callable[[Path, ast.AST], list[Smell]]]:
    ast_analyzers = []
    for smell in filtered_smells.values():
        method = smell["analyzer_method"]
        options = smell.get("analyzer_options", {})
        ast_analyzers.append((method, options))

    return ast_analyzers


def prepare_smell_analysis(smell_registry: dict[str, SmellRegistry]) -> dict[str, Any]:
    pylint_smells = filter_smells_by_method(smell_registry, "pylint")
    ast_smells = filter_smells_by_method(smell_registry, "ast")

    pylint_options = generate_pylint_options(pylint_smells)
    ast_analyzer_methods = generate_ast_analyzers(ast_smells)

    return {
        "pylint_options": pylint_options,
        "ast_analyzers": ast_analyzer_methods,
    }
