from abc import ABC, abstractmethod
from pathlib import Path

from ..data_wrappers.smell import Smell


class BaseRefactorer(ABC):
    @abstractmethod
    def refactor(self, input_file: Path, smell: Smell, output_file: Path):
        pass
