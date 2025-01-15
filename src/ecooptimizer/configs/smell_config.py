from enum import Enum

# Individual AST Analyzers
from ..analyzers.ast_analyzers.detect_repeated_calls import detect_repeated_calls
from ..analyzers.ast_analyzers.detect_long_element_chain import detect_long_element_chain
from ..analyzers.ast_analyzers.detect_long_lambda_expression import detect_long_lambda_expression
from ..analyzers.ast_analyzers.detect_long_message_chain import detect_long_message_chain
from ..analyzers.ast_analyzers.detect_unused_variables_and_attributes import (
    detect_unused_variables_and_attributes,
)

# Refactorer Classes
from ..refactorers.repeated_calls import CacheRepeatedCallsRefactorer
from ..refactorers.list_comp_any_all import UseAGeneratorRefactorer
from ..refactorers.long_lambda_function import LongLambdaFunctionRefactorer
from ..refactorers.long_element_chain import LongElementChainRefactorer
from ..refactorers.long_message_chain import LongMessageChainRefactorer
from ..refactorers.unused import RemoveUnusedRefactorer
from ..refactorers.member_ignoring_method import MakeStaticRefactorer
from ..refactorers.long_parameter_list import LongParameterListRefactorer


# Just an example of how we can add characteristics to the smells
class SmellSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Centralized smells configuration
SMELL_CONFIG = {
    "use-a-generator": {
        "id": "R1729",
        "severity": SmellSeverity.MEDIUM,
        "analyzer_method": "pylint",
        "refactorer": UseAGeneratorRefactorer,
    },
    "long-parameter-list": {
        "id": "R0913",
        "severity": SmellSeverity.MEDIUM,
        "analyzer_method": "pylint",
        "refactorer": LongParameterListRefactorer,
    },
    "no-self-use": {
        "id": "R6301",
        "severity": SmellSeverity.MEDIUM,
        "analyzer_method": "pylint",
        "refactorer": MakeStaticRefactorer,
    },
    "repeated-calls": {
        "id": "CRC001",
        "severity": SmellSeverity.MEDIUM,
        "analyzer_method": detect_repeated_calls,
        "refactorer": CacheRepeatedCallsRefactorer,
    },
    "long-lambda-expression": {
        "id": "LLE001",
        "severity": SmellSeverity.MEDIUM,
        "analyzer_method": detect_long_lambda_expression,
        "refactorer": LongLambdaFunctionRefactorer,
    },
    "long-message-chain": {
        "id": "LMC001",
        "severity": SmellSeverity.MEDIUM,
        "analyzer_method": detect_long_message_chain,
        "refactorer": LongMessageChainRefactorer,
    },
    "unused_variables_and_attributes": {
        "id": "UVA001",
        "severity": SmellSeverity.MEDIUM,
        "analyzer_method": detect_unused_variables_and_attributes,
        "refactorer": RemoveUnusedRefactorer,
    },
    "long-element-chain": {
        "id": "LEC001",
        "severity": SmellSeverity.MEDIUM,
        "analyzer_method": detect_long_element_chain,
        "refactorer": LongElementChainRefactorer,
    },
}


class SmellConfig:
    @staticmethod
    def list_pylint_smell_ids() -> list[str]:
        """Returns a list of Pylint-specific smell IDs."""
        return [
            config["id"]
            for config in SMELL_CONFIG.values()
            if config["analyzer_method"] == "pylint"
        ]

    @staticmethod
    def list_ast_smell_methods() -> list[str]:
        """Returns a list of function names (methods) for all AST smells."""
        return [
            config["analyzer_method"]
            for config in SMELL_CONFIG.values()
            if config["analyzer_method"] != "pylint"
        ]
