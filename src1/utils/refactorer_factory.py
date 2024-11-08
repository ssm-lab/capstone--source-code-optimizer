# Import specific refactorer classes
from refactorers.use_a_generator_refactor import UseAGeneratorRefactor
from refactorers.base_refactorer import BaseRefactorer

# Import the configuration for all Pylint smells
from utils.analyzers_config import AllPylintSmells

class RefactorerFactory():
    """
    Factory class for creating appropriate refactorer instances based on 
    the specific code smell detected by Pylint.
    """

    @staticmethod
    def build_refactorer_class(file_path, smell_messageId, smell_data, initial_emission, logger):
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
        match smell_messageId:
            case AllPylintSmells.USE_A_GENERATOR.value:
                selected = UseAGeneratorRefactor(file_path, smell_data, initial_emission, logger)
            case _:
                selected = None

        return selected  # Return the selected refactorer instance or None if no match was found
