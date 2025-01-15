from abc import ABC, abstractmethod
from pathlib import Path


class Analyzer(ABC):
    def __init__(self, file_path: Path):
        """
        Base class for analyzers to find code smells of a given file.
        :param file_path: Path to the file to be analyzed.
        """
        self.file_path = file_path
        self.smells_data = list()

    @abstractmethod
    def analyze(self):
        """
        Abstract method to analyze the code smells of the specified file.
        Must be implemented by subclasses.
        """
        pass
