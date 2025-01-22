# Import specific refactorer classes
from pathlib import Path
from ..refactorers.list_comp_any_all import UseAGeneratorRefactorer
from ..refactorers.unused import RemoveUnusedRefactorer
from ..refactorers.member_ignoring_method import MakeStaticRefactorer
from ..refactorers.long_message_chain import LongMessageChainRefactorer
from ..refactorers.long_element_chain import LongElementChainRefactorer
from ..refactorers.str_concat_in_loop import UseListAccumulationRefactorer
from ..refactorers.repeated_calls import CacheRepeatedCallsRefactorer

# Import the configuration for all Pylint smells
from ..utils.analyzers_config import AllSmells, CustomSmell, PylintSmell


class RefactorerFactory:
    """
    Factory class for creating appropriate refactorer instances based on
    the specific code smell detected by Pylint.
    """

    @staticmethod
    def build_refactorer_class(smell_messageID: CustomSmell | PylintSmell, output_dir: Path):
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
                selected = UseAGeneratorRefactorer(output_dir)
            case AllSmells.UNUSED_IMPORT:  # type: ignore
                selected = RemoveUnusedRefactorer(output_dir)
            case AllSmells.UNUSED_VAR_OR_ATTRIBUTE:  # type: ignore
                selected = RemoveUnusedRefactorer(output_dir)
            case AllSmells.NO_SELF_USE:  # type: ignore
                selected = MakeStaticRefactorer(output_dir)
            # case AllSmells.LONG_PARAMETER_LIST:  # type: ignore
            #     selected = LongParameterListRefactorer(output_dir)
            case AllSmells.LONG_MESSAGE_CHAIN:  # type: ignore
                selected = LongMessageChainRefactorer(output_dir)
            case AllSmells.LONG_ELEMENT_CHAIN:  # type: ignore
                selected = LongElementChainRefactorer(output_dir)
            case AllSmells.STR_CONCAT_IN_LOOP:  # type: ignore
                selected = UseListAccumulationRefactorer(output_dir)
            case AllSmells.CACHE_REPEATED_CALLS:  # type: ignore
                selected = CacheRepeatedCallsRefactorer(output_dir)
            case _:
                selected = None

        return selected  # Return the selected refactorer instance or None if no match was found
