# refactorers/base_refactor.py

from abc import ABC, abstractmethod
from pathlib import Path

from ..data_wrappers.smell import Smell


class BaseRefactorer(ABC):
    def __init__(self, output_dir: Path):
        """
        Base class for refactoring specific code smells.

        :param logger: Logger instance to handle log messages.
        """
        self.temp_dir = (output_dir / "refactored_source").resolve()
        self.temp_dir.mkdir(exist_ok=True)

    @abstractmethod
    def refactor(self, file_path: Path, pylint_smell: Smell, overwrite: bool = True):
        """
        Abstract method for refactoring the code smell.
        Each subclass should implement this method.

        :param file_path: Path to the file to be refactored.
        :param pylint_smell: Dictionary containing details of the Pylint smell.
        :param initial_emission: Initial emission value before refactoring.
        """
        pass
