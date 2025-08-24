"""Abstract base class for all code smell refactorers."""

from abc import ABC, abstractmethod
import hashlib
from pathlib import Path
import shutil
from typing import Generic, TypeVar
import tempfile

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

    def store_original(self, file: Path, rel_path: Path, smell_id: str):
        """
        Saves a copy of the original file to a temp directory for a specific smell.
        Returns the path to the temp copy and a mapping of temp -> original.

        Parameters:
            file_path (str or Path): Full path to the original file.
            smell_id (str or int): Unique ID for the smell being refactored.

        Returns:
            temp_file_path (Path): Path to the saved temp copy.
            mapping (dict): {temp_file_path: original_file_path}
        """

        # Base temp directory for EcoOptimizer
        base_temp_dir = Path(tempfile.gettempdir()) / ".ecooptimizer" / str(smell_id)
        base_temp_dir.mkdir(parents=True, exist_ok=True)

        file_hash = hashlib.sha1(str(rel_path).encode()).hexdigest()
        temp_file_name = file_hash + file.suffix
        temp_file = base_temp_dir / temp_file_name

        shutil.copy2(file, temp_file)

        # # Mapping for traceability
        # mapping = {temp_file: file}

        # return temp_file, mapping
