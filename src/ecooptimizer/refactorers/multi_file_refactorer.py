from abc import abstractmethod
from pathlib import Path
from typing import TypeVar

from .base_refactorer import BaseRefactorer

from ..data_types.smell import Smell

T = TypeVar("T", bound=Smell)


class MultiFileRefactorer(BaseRefactorer[T]):
    def traverse_and_process(self, directory: Path):
        for item in directory.iterdir():
            if item.is_dir():
                self.traverse_and_process(item)
            elif item.is_file() and item.suffix == ".py":
                self._process_file(item)

    @abstractmethod
    def _process_file(self, file: Path):
        """Abstract method to be implemented by subclasses to handle file processing."""
        pass
