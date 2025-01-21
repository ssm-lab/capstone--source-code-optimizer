from abc import ABC, abstractmethod
import ast
import logging
from pathlib import Path

from ecooptimizer.data_wrappers.smell import Smell


class Analyzer(ABC):
    def __init__(self, file_path: Path, source_code: ast.Module):
        """
        Base class for analyzers to find code smells of a given file.

        :param file_path: Path to the file to be analyzed.
        :param logger: Logger instance to handle log messages.
        """
        self.file_path = file_path
        self.source_code = source_code
        self.smells_data: list[Smell] = list()

    def validate_file(self):
        """
        Validates that the specified file path exists and is a file.

        :return: Boolean indicating the validity of the file path.
        """
        if not self.file_path.is_file():
            logging.error(f"File not found: {self.file_path!s}")
            return False

        return True

    @abstractmethod
    def analyze(self):
        """
        Abstract method to analyze the code smells of the specified file.
        Must be implemented by subclasses.
        """
        pass
