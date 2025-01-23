from ..analyzers.ast_analyzers.detect_long_element_chain import detect_long_element_chain
from ..analyzers.ast_analyzers.detect_long_lambda_expression import detect_long_lambda_expression
from ..analyzers.ast_analyzers.detect_long_message_chain import detect_long_message_chain
from ..analyzers.ast_analyzers.detect_unused_variables_and_attributes import (
    detect_unused_variables_and_attributes,
)

from ..refactorers.list_comp_any_all import UseAGeneratorRefactorer
from ..refactorers.long_lambda_function import LongLambdaFunctionRefactorer
from ..refactorers.long_element_chain import LongElementChainRefactorer
from ..refactorers.long_message_chain import LongMessageChainRefactorer
from ..refactorers.unused import RemoveUnusedRefactorer
from ..refactorers.member_ignoring_method import MakeStaticRefactorer
from ..refactorers.long_parameter_list import LongParameterListRefactorer

from ..data_wrappers.smell_registry import SmellRegistry

SMELL_REGISTRY: dict[str, SmellRegistry] = {
    "use-a-generator": {
        "id": "R1729",
        "enabled": True,
        "analyzer_method": "pylint",
        "analyzer_options": {"max_args": {"flag": "--max-args", "value": 6}},
        "refactorer": UseAGeneratorRefactorer,
    },
    "long-parameter-list": {
        "id": "R0913",
        "enabled": True,
        "analyzer_method": "pylint",
        "analyzer_options": {},
        "refactorer": LongParameterListRefactorer,
    },
    "no-self-use": {
        "id": "R6301",
        "enabled": False,
        "analyzer_method": "pylint",
        "analyzer_options": {},
        "refactorer": MakeStaticRefactorer,
    },
    "long-lambda-expression": {
        "id": "LLE001",
        "enabled": True,
        "analyzer_method": detect_long_lambda_expression,
        "analyzer_options": {"threshold_length": 100, "threshold_count": 5},
        "refactorer": LongLambdaFunctionRefactorer,
    },
    "long-message-chain": {
        "id": "LMC001",
        "enabled": True,
        "analyzer_method": detect_long_message_chain,
        "analyzer_options": {"threshold": 3},
        "refactorer": LongMessageChainRefactorer,
    },
    "unused_variables_and_attributes": {
        "id": "UVA001",
        "enabled": True,
        "analyzer_method": detect_unused_variables_and_attributes,
        "analyzer_options": {},
        "refactorer": RemoveUnusedRefactorer,
    },
    "long-element-chain": {
        "id": "LEC001",
        "enabled": True,
        "analyzer_method": detect_long_element_chain,
        "analyzer_options": {"threshold": 5},
        "refactorer": LongElementChainRefactorer,
    },
}
