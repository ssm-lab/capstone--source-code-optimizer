from typing import Any, Callable

from ..utils.analyzers_config import CustomSmell, PylintSmell

from ..data_types.smell import Smell
from ..data_types.smell_registry import SmellRegistry


def filter_smells_by_method(
    smell_registry: dict[str, SmellRegistry], method: str
) -> dict[str, SmellRegistry]:
    filtered = {
        name: smell
        for name, smell in smell_registry.items()
        if smell["enabled"] and (method == smell["analyzer_method"])
    }
    return filtered


def filter_smells_by_id(smells: list[Smell]):  # type: ignore
    all_smell_ids = [
        *[smell.value for smell in CustomSmell],
        *[smell.value for smell in PylintSmell],
    ]
    return [smell for smell in smells if smell.messageId in all_smell_ids]


def generate_pylint_options(filtered_smells: dict[str, SmellRegistry]) -> list[str]:
    pylint_smell_symbols = []
    extra_pylint_options = [
        "--disable=all",
    ]

    for symbol, smell in zip(filtered_smells.keys(), filtered_smells.values()):
        pylint_smell_symbols.append(symbol)

        if len(smell["analyzer_options"]) > 0:
            for param_data in smell["analyzer_options"].values():
                flag = param_data["flag"]
                value = param_data["value"]
                if value:
                    extra_pylint_options.append(f"{flag}={value}")

    extra_pylint_options.append(f"--enable={','.join(pylint_smell_symbols)}")
    return extra_pylint_options


def generate_custom_options(
    filtered_smells: dict[str, SmellRegistry],
) -> list[tuple[Callable, dict[str, Any]]]:  # type: ignore
    ast_options = []
    for smell in filtered_smells.values():
        method = smell["checker"]
        options = smell["analyzer_options"]
        ast_options.append((method, options))

    return ast_options
