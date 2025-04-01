"""Registry of code smells with their detection and refactoring configurations."""

from copy import deepcopy
from typing import Any

from ecooptimizer.utils.smell_enums import CustomSmell, PylintSmell
from ecooptimizer.analyzers.ast_analyzers.detect_long_element_chain import detect_long_element_chain
from ecooptimizer.analyzers.ast_analyzers.detect_long_lambda_expression import (
    detect_long_lambda_expression,
)
from ecooptimizer.analyzers.ast_analyzers.detect_long_message_chain import detect_long_message_chain
from ecooptimizer.analyzers.astroid_analyzers.detect_string_concat_in_loop import (
    detect_string_concat_in_loop,
)
from ecooptimizer.analyzers.ast_analyzers.detect_repeated_calls import detect_repeated_calls
from ecooptimizer.refactorers.concrete.list_comp_any_all import UseAGeneratorRefactorer
from ecooptimizer.refactorers.concrete.long_lambda_function import LongLambdaFunctionRefactorer
from ecooptimizer.refactorers.concrete.long_element_chain import LongElementChainRefactorer
from ecooptimizer.refactorers.concrete.long_message_chain import LongMessageChainRefactorer
from ecooptimizer.refactorers.concrete.member_ignoring_method import MakeStaticRefactorer
from ecooptimizer.refactorers.concrete.long_parameter_list import LongParameterListRefactorer
from ecooptimizer.refactorers.concrete.str_concat_in_loop import UseListAccumulationRefactorer
from ecooptimizer.refactorers.concrete.repeated_calls import CacheRepeatedCallsRefactorer
from ecooptimizer.data_types.smell_record import SmellRecord

# Base registry of all supported code smells
_SMELL_REGISTRY: dict[str, SmellRecord] = {
    "use-a-generator": {
        "id": PylintSmell.USE_A_GENERATOR.value,
        "enabled": True,
        "analyzer_method": "pylint",
        "checker": None,
        "analyzer_options": {},
        "refactorer": UseAGeneratorRefactorer,
    },
    "too-many-arguments": {
        "id": PylintSmell.LONG_PARAMETER_LIST.value,
        "enabled": True,
        "analyzer_method": "pylint",
        "checker": None,
        "analyzer_options": {"max_args": {"flag": "--max-args", "value": 6}},
        "refactorer": LongParameterListRefactorer,
    },
    "no-self-use": {
        "id": PylintSmell.NO_SELF_USE.value,
        "enabled": True,
        "analyzer_method": "pylint",
        "checker": None,
        "analyzer_options": {
            "load-plugin": {"flag": "--load-plugins", "value": "pylint.extensions.no_self_use"}
        },
        "refactorer": MakeStaticRefactorer,
    },
    "long-lambda-expression": {
        "id": CustomSmell.LONG_LAMBDA_EXPR.value,
        "enabled": True,
        "analyzer_method": "ast",
        "checker": detect_long_lambda_expression,
        "analyzer_options": {"threshold_length": 100, "threshold_count": 5},
        "refactorer": LongLambdaFunctionRefactorer,
    },
    "long-message-chain": {
        "id": CustomSmell.LONG_MESSAGE_CHAIN.value,
        "enabled": True,
        "analyzer_method": "ast",
        "checker": detect_long_message_chain,
        "analyzer_options": {"threshold": 3},
        "refactorer": LongMessageChainRefactorer,
    },
    "long-element-chain": {
        "id": CustomSmell.LONG_ELEMENT_CHAIN.value,
        "enabled": True,
        "analyzer_method": "ast",
        "checker": detect_long_element_chain,
        "analyzer_options": {"threshold": 3},
        "refactorer": LongElementChainRefactorer,
    },
    "cached-repeated-calls": {
        "id": CustomSmell.CACHE_REPEATED_CALLS.value,
        "enabled": True,
        "analyzer_method": "ast",
        "checker": detect_repeated_calls,
        "analyzer_options": {"threshold": 2},
        "refactorer": CacheRepeatedCallsRefactorer,
    },
    "string-concat-loop": {
        "id": CustomSmell.STR_CONCAT_IN_LOOP.value,
        "enabled": True,
        "analyzer_method": "astroid",
        "checker": detect_string_concat_in_loop,
        "analyzer_options": {},
        "refactorer": UseListAccumulationRefactorer,
    },
}

# Default configuration values for smell detection
OPTIONS_CONFIG = {
    "too-many-arguments": {"max_args": 6},
    "long-lambda-expression": {"threshold_length": 100, "threshold_count": 5},
    "long-message-chain": {"threshold": 3},
    "long-element-chain": {"threshold": 3},
    "cached-repeated-calls": {"threshold": 2},
}


def retrieve_smell_registry(enabled_smells: dict[str, dict[str, int | str]] | list[str]):
    """Returns a modified smell registry based on user preferences.

    Args:
        enabled_smells: Either a list of enabled smell names or a dictionary
                       with smell-specific configurations

    Returns:
        Dictionary containing only enabled smells with updated configurations
    """
    updated_registry = deepcopy(_SMELL_REGISTRY)

    if isinstance(enabled_smells, list):
        return {
            smell_name: config
            for smell_name, config in updated_registry.items()
            if smell_name in enabled_smells
        }

    # Handle dictionary configuration
    for smell_name, smell_config in updated_registry.items():
        if smell_name in enabled_smells:
            smell_config["enabled"] = True
            user_options = enabled_smells[smell_name]
            if not user_options:
                continue

            analyzer_method = smell_config["analyzer_method"]
            original_options = smell_config["analyzer_options"]

            if analyzer_method == "pylint":
                updated_options = {}
                for opt_key, opt_data in original_options.items():
                    if opt_key in user_options:
                        updated_options[opt_key] = {
                            "flag": opt_data["flag"],
                            "value": user_options[opt_key],
                        }
                    else:
                        updated_options[opt_key] = opt_data
                smell_config["analyzer_options"] = updated_options
            else:
                # Merge user options with defaults for non-Pylint smells
                smell_config["analyzer_options"] = {**original_options, **user_options}
        else:
            smell_config["enabled"] = False

    return updated_registry


def get_refactorer(symbol: str) -> Any:  # noqa: ANN401
    """Retrieves the refactorer class for a given smell symbol.

    Args:
        symbol: The smell identifier (e.g., "long-lambda-expression")

    Returns:
        The refactorer class associated with the smell, or None if not found
    """
    return _SMELL_REGISTRY.get(symbol, {}).get("refactorer")
