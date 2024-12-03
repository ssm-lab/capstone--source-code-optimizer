# Import specific refactorer classes
from refactorers.list_comp_any_all import UseAGeneratorRefactorer
from refactorers.unused import RemoveUnusedRefactorer
from refactorers.long_parameter_list import LongParameterListRefactorer
from refactorers.member_ignoring_method import MakeStaticRefactorer
from refactorers.long_message_chain import LongMessageChainRefactorer

# Import the configuration for all Pylint smells
from utils.analyzers_config import AllSmells


class RefactorerFactory:
    """
    Factory class for creating appropriate refactorer instances based on
    the specific code smell detected by Pylint.
    """

    @staticmethod
    def build_refactorer_class(smell_messageID: str):
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
            case AllSmells.USE_A_GENERATOR:  # type: ignore
                selected = UseAGeneratorRefactorer()
            case AllSmells.UNUSED_IMPORT:  # type: ignore
                selected = RemoveUnusedRefactorer()
            case AllSmells.UNUSED_VAR_OR_ATTRIBUTE:  # type: ignore
                selected = RemoveUnusedRefactorer()
            case AllSmells.NO_SELF_USE:  # type: ignore
                selected = MakeStaticRefactorer()
            case AllSmells.LONG_PARAMETER_LIST:  # type: ignore
                selected = LongParameterListRefactorer()
            case AllSmells.LONG_MESSAGE_CHAIN:  # type: ignore
                selected = LongMessageChainRefactorer()
            case _:
                selected = None

        return selected  # Return the selected refactorer instance or None if no match was found
