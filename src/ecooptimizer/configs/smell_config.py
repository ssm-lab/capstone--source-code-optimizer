from enum import Enum

# Individual AST Analyzers
from ..analyzers.ast_analyzers.detect_repeated_calls import detect_repeated_calls

# Refactorer Classes
from ..refactorers.repeated_calls import CacheRepeatedCallsRefactorer
from ..refactorers.list_comp_any_all import UseAGeneratorRefactorer
from ..refactorers.long_lambda_function import LongLambdaFunctionRefactorer


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
    "repeated-calls": {
        "id": "CRC001",
        "severity": SmellSeverity.MEDIUM,
        "analyzer_method": detect_repeated_calls,
        "refactorer": CacheRepeatedCallsRefactorer,
    },
    "long-lambda-expression": {
        "id": "CRC001",
        "severity": SmellSeverity.MEDIUM,
        "analyzer_method": detect_repeated_calls,
        "refactorer": LongLambdaFunctionRefactorer,
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
