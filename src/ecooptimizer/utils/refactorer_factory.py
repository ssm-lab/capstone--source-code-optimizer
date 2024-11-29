# Import specific refactorer classes
from ecooptimizer.refactorers.list_comp_any_all import UseAGeneratorRefactorer
from ecooptimizer.refactorers.unused import RemoveUnusedRefactorer
from ecooptimizer.refactorers.long_parameter_list import LongParameterListRefactorer
from ecooptimizer.refactorers.member_ignoring_method import MakeStaticRefactorer
from ecooptimizer.refactorers.long_message_chain import LongMessageChainRefactorer

# Import the configuration for all Pylint smells
from utils.logger import Logger
from utils.analyzers_config import AllSmells


class RefactorerFactory:
    """
    Factory class for creating appropriate refactorer instances based on
    the specific code smell detected by Pylint.
    """

    @staticmethod
    def build_refactorer_class(smell_messageID: str, logger: Logger):
        """
        Static method to create and return a refactorer instance based on the provided code smell.

        Parameters:
        - file_path (str): The path of the file to be refactored.
        - smell_messageId (str): The unique identifier (message ID) of the detected code smell.
        - smell_data (dict): Additional data related to the smell, passed to the refactorer.

        Returns:
        - BaseRefactorer: An instance of a specific refactorer class if one exists for the smell;
          otherwise, None.
        """

        selected = None  # Initialize variable to hold the selected refactorer instance

        # Use match statement to select the appropriate refactorer based on smell message ID
        match smell_messageID:
            case AllSmells.USE_A_GENERATOR: # type: ignore
                selected = UseAGeneratorRefactorer(logger)
            case AllSmells.UNUSED_IMPORT:
                selected = RemoveUnusedRefactorer(logger)
            case AllSmells.UNUSED_VAR_OR_ATTRIBUTE:
                selected = RemoveUnusedRefactorer(logger)
            case AllSmells.NO_SELF_USE:
                selected = MakeStaticRefactorer(logger)
            case AllSmells.LONG_PARAMETER_LIST:
                selected = LongParameterListRefactorer(logger)
            case AllSmells.LONG_MESSAGE_CHAIN:
                selected = LongMessageChainRefactorer(logger)
            case _:
                selected = None

        return selected  # Return the selected refactorer instance or None if no match was found
