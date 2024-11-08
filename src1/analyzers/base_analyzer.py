from abc import ABC, abstractmethod
import os
from utils.logger import Logger

class Analyzer(ABC):
    def __init__(self, file_path, logger):
        """
        Base class for analyzers to find code smells of a given file.

        :param file_path: Path to the file to be analyzed.
        :param logger: Logger instance to handle log messages.
        """
        self.file_path = file_path
        self.smells_data = []
        self.logger = logger  # Use logger instance

    def validate_file(self):
        """
        Validates that the specified file path exists and is a file.
        
        :return: Boolean indicating the validity of the file path.
        """
        is_valid = os.path.isfile(self.file_path)
        if not is_valid:
            self.logger.log(f"File not found: {self.file_path}")
        return is_valid

    @abstractmethod
    def analyze_smells(self):
        """
        Abstract method to analyze the code smells of the specified file.
        Must be implemented by subclasses.
        """
        pass
