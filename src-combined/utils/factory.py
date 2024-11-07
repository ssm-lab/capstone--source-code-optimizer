from refactorer.long_lambda_function_refactorer import LongLambdaFunctionRefactorer as LLFR
from refactorer.long_message_chain_refactorer import LongMessageChainRefactorer as LMCR
from refactorer.long_ternary_cond_expression import LTCERefactorer as LTCER

from refactorer.base_refactorer import BaseRefactorer

from utils.analyzers_config import CustomSmell, PylintSmell

class RefactorerFactory():

    @staticmethod
    def build(smell_name: str, file_path: str) -> BaseRefactorer:
        selected = None
        match smell_name:
            case PylintSmell.LONG_MESSAGE_CHAIN:
                selected = LMCR(file_path)
            case CustomSmell.LONG_TERN_EXPR:
                selected = LTCER(file_path)
            case _:
                selected = None
        return selected