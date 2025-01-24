from abc import ABC, abstractmethod
from pathlib import Path

from ..data_wrappers.smell import Smell


class BaseRefactorer(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def refactor(self, input_file: Path, smell: Smell, output_file: Path, overwrite: bool = True):
        pass
