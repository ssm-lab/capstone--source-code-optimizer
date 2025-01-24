from ..utils.analyzers_config import CustomSmell, PylintSmell  # noqa: F401

# from ..analyzers.ast_analyzers.detect_long_element_chain import detect_long_element_chain
# from ..analyzers.ast_analyzers.detect_long_lambda_expression import detect_long_lambda_expression
# from ..analyzers.ast_analyzers.detect_long_message_chain import detect_long_message_chain
# from ..analyzers.ast_analyzers.detect_string_concat_in_loop import detect_string_concat_in_loop
# from ..analyzers.ast_analyzers.detect_unused_variables_and_attributes import detect_unused_variables_and_attributes

from ..refactorers.list_comp_any_all import UseAGeneratorRefactorer

# from ..refactorers.long_lambda_function import LongLambdaFunctionRefactorer
# from ..refactorers.long_element_chain import LongElementChainRefactorer
# from ..refactorers.long_message_chain import LongMessageChainRefactorer
# from ..refactorers.unused import RemoveUnusedRefactorer
# from ..refactorers.member_ignoring_method import MakeStaticRefactorer
# from ..refactorers.long_parameter_list import LongParameterListRefactorer
# from ..refactorers.str_concat_in_loop import UseListAccumulationRefactorer


from ..data_wrappers.smell_registry import SmellRegistry

SMELL_REGISTRY: dict[str, SmellRegistry] = {
    "use-a-generator": {
        "id": PylintSmell.USE_A_GENERATOR.value,
        "enabled": True,
        "analyzer_method": "pylint",
        "analyzer_options": {},
        "refactorer": UseAGeneratorRefactorer,
    },
    # "long-parameter-list": {
    #     "id": PylintSmell.LONG_PARAMETER_LIST.value,
    #     "enabled": False,
    #     "analyzer_method": "pylint",
    #     "analyzer_options": {"max_args": {"flag": "--max-args", "value": 6}},
    #     "refactorer": LongParameterListRefactorer,
    # },
    # "no-self-use": {
    #     "id": PylintSmell.NO_SELF_USE.value,
    #     "enabled": False,
    #     "analyzer_method": "pylint",
    #     "analyzer_options": {},
    #     "refactorer": MakeStaticRefactorer,
    # },
    # "long-lambda-expression": {
    #     "id": CustomSmell.LONG_LAMBDA_EXPR.value,
    #     "enabled": False,
    #     "analyzer_method": detect_long_lambda_expression,
    #     "analyzer_options": {"threshold_length": 100, "threshold_count": 5},
    #     "refactorer": LongLambdaFunctionRefactorer,
    # },
    # "long-message-chain": {
    #     "id": CustomSmell.LONG_MESSAGE_CHAIN.value,
    #     "enabled": False,
    #     "analyzer_method": detect_long_message_chain,
    #     "analyzer_options": {"threshold": 3},
    #     "refactorer": LongMessageChainRefactorer,
    # },
    # "unused_variables_and_attributes": {
    #     "id": CustomSmell.UNUSED_VAR_OR_ATTRIBUTE.value,
    #     "enabled": False,
    #     "analyzer_method": detect_unused_variables_and_attributes,
    #     "analyzer_options": {},
    #     "refactorer": RemoveUnusedRefactorer,
    # },
    # "long-element-chain": {
    #     "id": CustomSmell.LONG_ELEMENT_CHAIN.value,
    #     "enabled": False,
    #     "analyzer_method": detect_long_element_chain,
    #     "analyzer_options": {"threshold": 5},
    #     "refactorer": LongElementChainRefactorer,
    # },
    # "string-concat-loop": {
    #     "id": CustomSmell.STR_CONCAT_IN_LOOP.value,
    #     "enabled": True,
    #     "analyzer_method": detect_string_concat_in_loop,
    #     "analyzer_options": {},
    #     "refactorer": UseListAccumulationRefactorer,
    # },
}
