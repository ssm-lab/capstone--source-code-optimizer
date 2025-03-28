"""Abstract base class for all code smell refactorers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar

from ecooptimizer.data_types.smell import Smell

T = TypeVar("T", bound=Smell)


class BaseRefactorer(ABC, Generic[T]):
    """Defines the interface for concrete refactoring implementations.

    Type Parameters:
        T: Type of smell this refactorer handles (must inherit from Smell)
    """

    def __init__(self):
        """Initializes the refactorer with empty modified files list."""
        self.modified_files: list[Path] = []

    @abstractmethod
    def refactor(
        self,
        target_file: Path,
        source_dir: Path,
        smell: T,
        output_file: Path,
        overwrite: bool = True,
    ) -> None:
        """Performs the refactoring operation on the target file.

        Args:
            target_file: File containing the smell to refactor
            source_dir: Root directory of the source files
            smell: Detected smell instance with metadata
            output_file: Destination path for refactored code
            overwrite: Whether to overwrite existing output file

        Note:
            Concrete subclasses must implement this method
        """
        pass
