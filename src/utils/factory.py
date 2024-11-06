from refactorer.long_lambda_function_refactorer import LongLambdaFunctionRefactorer as LLFR
from refactorer.long_message_chain_refactorer import LongMessageChainRefactorer as LMCR
from refactorer.long_ternary_cond_expression import LTCERefactorer as LTCER

from refactorer.base_refactorer import BaseRefactorer

from utils.code_smells import CodeSmells

class RefactorerFactory():

    @staticmethod
    def build(smell_name: str, file_path: str) -> BaseRefactorer:
        selected = None
        match smell_name:
            case CodeSmells.LONG_LAMBDA_FUNC:
                selected = LLFR(file_path)
            case CodeSmells.LONG_MESSAGE_CHAIN:
                selected = LMCR(file_path)
            case CodeSmells.LONG_TERN_EXPR:
                selected = LTCER(file_path)
            case _:
                raise ValueError(smell_name)
        return selected