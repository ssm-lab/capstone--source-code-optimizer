from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..data_wrappers.smell import Smell


class Analyzer(ABC):
    @abstractmethod
    def analyze(self, file_path: Path, extra_options: list[Any]) -> list[Smell]:
        pass
