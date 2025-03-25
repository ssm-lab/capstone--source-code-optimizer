"""Abstract base class for all code smell analyzers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..data_types.smell import Smell


class Analyzer(ABC):
    """Abstract base class defining the interface for code smell analyzers.

    Concrete analyzer implementations must implement the analyze() method.
    """

    @abstractmethod
    def analyze(self, file_path: Path, extra_options: list[Any]) -> list[Smell]:
        """Analyze a source file and return detected code smells.

        Args:
            file_path: Path to the source file to analyze
            extra_options: List of analyzer-specific configuration options

        Returns:
            list[Smell]: Detected code smells in the source file

        Note:
            Concrete analyzer implementations must override this method.
        """
        pass
