# src/refactorer/base_refactorer.py

from abc import ABC, abstractmethod

class BaseRefactorer(ABC):
    """
    Abstract base class for refactorers. Defines the interface for all specific refactoring classes.
    """

    def __init__(self, code_path: str):
        """
        Initializes the refactorer with a path to the code to be refactored.

        Parameters:
        - code_path (str): Path to the file or directory containing the code to be refactored.
        """
        self.code_path = code_path

    @abstractmethod
    def detect_smell(self) -> bool:
        """
        Detects if a specific code smell is present in the code. Must be implemented in subclasses.
        
        Returns:
        - bool: True if the smell is detected, False otherwise.
        """
        pass

    @abstractmethod
    def refactor(self) -> str:
        """
        Refactors the code to remove the detected code smell. Must be implemented by subclasses.
        
        Returns:
        - str: The refactored code as a string.
        """
        pass

    def load_code(self) -> str:
        """
        Loads the code from the specified path for analysis and refactoring.
        
        Returns:
        - str: The contents of the code file as a string.
        """
        try:
            with open(self.code_path, 'r') as code_file:
                return code_file.read()
        except FileNotFoundError:
            print(f"Error: File at {self.code_path} not found.")
            return None

    def save_code(self, modified_code: str) -> bool:
        """
        Saves the modified code back to the file after refactoring.

        Parameters:
        - modified_code (str): The refactored code as a string.
        
        Returns:
        - bool: True if the code was successfully saved, False otherwise.
        """
        try:
            with open(self.code_path, 'w') as code_file:
                code_file.write(modified_code)
            print(f"Code successfully saved to {self.code_path}.")
            return True
        except IOError as e:
            print(f"Error saving file: {e}")
            return False
