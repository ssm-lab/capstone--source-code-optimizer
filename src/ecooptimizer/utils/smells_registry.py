from copy import deepcopy
from .smell_enums import CustomSmell, PylintSmell

from ..analyzers.ast_analyzers.detect_long_element_chain import detect_long_element_chain
from ..analyzers.ast_analyzers.detect_long_lambda_expression import detect_long_lambda_expression
from ..analyzers.ast_analyzers.detect_long_message_chain import detect_long_message_chain
from ..analyzers.astroid_analyzers.detect_string_concat_in_loop import detect_string_concat_in_loop
from ..analyzers.ast_analyzers.detect_repeated_calls import detect_repeated_calls

from ..refactorers.concrete.list_comp_any_all import UseAGeneratorRefactorer

from ..refactorers.concrete.long_lambda_function import LongLambdaFunctionRefactorer
from ..refactorers.concrete.long_element_chain import LongElementChainRefactorer
from ..refactorers.concrete.long_message_chain import LongMessageChainRefactorer
from ..refactorers.concrete.member_ignoring_method import MakeStaticRefactorer
from ..refactorers.concrete.long_parameter_list import LongParameterListRefactorer
from ..refactorers.concrete.str_concat_in_loop import UseListAccumulationRefactorer
from ..refactorers.concrete.repeated_calls import CacheRepeatedCallsRefactorer

from ..data_types.smell_record import SmellRecord

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


def retrieve_smell_registry(enabled_smells: dict[str, dict[str, int | str]] | str):
    """Returns a modified SMELL_REGISTRY based on user preferences (enables/disables smells)."""

    # Ensure enabled_smells is a dictionary (avoid lists)
    if isinstance(enabled_smells, list):
        enabled_smells = {smell_name: {} for smell_name in enabled_smells}  # Convert list to dict
    if enabled_smells == "ALL":
        return deepcopy(_SMELL_REGISTRY)

    updated_registry = {}

    for smell_name, default_smell_data in _SMELL_REGISTRY.items():
        if smell_name in enabled_smells:
            updated_registry[smell_name] = deepcopy(default_smell_data)

            # Ensure `enabled_smells[smell_name]` is a dictionary before updating
            if isinstance(enabled_smells[smell_name], dict):
                updated_registry[smell_name]["analyzer_options"].update(enabled_smells[smell_name])

    return updated_registry


def get_refactorer(symbol: str):
    return _SMELL_REGISTRY[symbol].get("refactorer", None)
