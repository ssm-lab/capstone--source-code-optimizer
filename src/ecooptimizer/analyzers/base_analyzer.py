from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from ..data_types.smell import Smell


class Analyzer(ABC):
    """
    Abstract base class for all analyzers. Defines the required interface
    for any concrete analyzer that detects code smells.
    """

    @abstractmethod
    def analyze(self, file_path: Path, extra_options: list[Any]) -> list[Smell]:
        """
        Analyzes a given file and detects code smells.

        Args:
            file_path (Path): The path to the source file to be analyzed.
            extra_options (list[Any]): Additional parameters that analyzers may require.

        Returns:
            list[Smell]: A list of detected smells in the given file.
        """
        pass
