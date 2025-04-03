"""Base class for refactorers that operate across multiple files."""

# pyright: reportOptionalMemberAccess=false
from abc import abstractmethod
import fnmatch
from pathlib import Path
from typing import TypeVar

from ecooptimizer.config import CONFIG
from ecooptimizer.refactorers.base_refactorer import BaseRefactorer
from ecooptimizer.data_types.smell import Smell

T = TypeVar("T", bound=Smell)

# Default patterns for files/directories to ignore during refactoring
DEFAULT_IGNORED_PATTERNS = {
    "__pycache__",
    "build",
    ".venv",
    "*.egg-info",
    ".git",
    "node_modules",
    ".*",
}

# Default location for ignore pattern configuration files
DEFAULT_IGNORE_PATH = Path(__file__).parent / "patterns_to_ignore"


class MultiFileRefactorer(BaseRefactorer[T]):
    """Abstract base class for refactorers that need to process multiple files."""

    def __init__(self):
        """Initializes the refactorer with default ignore patterns."""
        super().__init__()
        self.target_file: Path = None  # type: ignore
        self.ignore_patterns = self._load_ignore_patterns()
        self.py_files: list[Path] = []

    def _load_ignore_patterns(self, ignore_dir: Path = DEFAULT_IGNORE_PATH) -> set[str]:
        """Loads ignore patterns from configuration files.

        Args:
            ignore_dir: Directory containing ignore pattern files

        Returns:
            Combined set of default and custom ignore patterns
        """
        if not ignore_dir.is_dir():
            return DEFAULT_IGNORED_PATTERNS

        patterns = DEFAULT_IGNORED_PATTERNS
        for file in ignore_dir.iterdir():
            with file.open() as f:
                patterns.update(
                    [line.strip() for line in f if line.strip() and not line.startswith("#")]
                )

        return patterns

    def is_ignored(self, item: Path) -> bool:
        """Checks if a path should be ignored during refactoring.

        Args:
            item: File or directory path to check

        Returns:
            True if the path matches any ignore pattern, False otherwise
        """
        return any(fnmatch.fnmatch(item.name, pattern) for pattern in self.ignore_patterns)

    def traverse(self, directory: Path) -> None:
        """Recursively scans a directory for Python files, skipping ignored paths.

        Args:
            directory: Root directory to scan
        """
        for item in directory.iterdir():
            if item.is_dir():
                CONFIG["refactorLogger"].debug(f"Scanning directory: {item!s}")
                if self.is_ignored(item):
                    CONFIG["refactorLogger"].debug(f"Ignored directory: {item!s}")
                    continue

                self.traverse(item)
            elif item.is_file() and item.suffix == ".py":
                self.py_files.append(item)

    def traverse_and_process(self, directory: Path) -> None:
        """Processes all Python files in a directory.

        Args:
            directory: Root directory containing files to process
        """
        if not self.py_files:
            self.traverse(directory)
        for file in self.py_files:
            CONFIG["refactorLogger"].debug(f"Processing file: {file!s}")
            if self._process_file(file):
                if file not in self.modified_files and not file.samefile(self.target_file):
                    self.modified_files.append(file.resolve())
            CONFIG["refactorLogger"].debug("Finished processing file")

    @abstractmethod
    def _process_file(self, file: Path) -> bool:
        """Processes an individual file (implemented by concrete refactorers).

        Args:
            file: Python file to process

        Returns:
            True if the file was modified, False otherwise
        """
        pass
