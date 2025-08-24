"""Base class for refactorers that operate across multiple files."""

# pyright: reportOptionalMemberAccess=false
from abc import abstractmethod
import fnmatch
import logging
from pathlib import Path
from typing import TypeVar, Optional

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
}

# Default location for ignore pattern configuration files
DEFAULT_IGNORE_PATH = Path(__file__).parent / "patterns_to_ignore"

logger = logging.getLogger("refactor")


class MultiFileRefactorer(BaseRefactorer[T]):
    """Abstract base class for refactorers that need to process multiple files."""

    def __init__(self, extra_patterns: Optional[set[str]] = None):
        """Initializes the refactorer with default ignore patterns."""
        super().__init__()
        self.target_file: Path = None  # type: ignore
        self.ignore_patterns = self._load_ignore_patterns(extra_patterns)
        self.py_files: list[Path] = []

    def _load_ignore_patterns(
        self, extra_patterns: Optional[set[str]] = None, ignore_dir: Path = DEFAULT_IGNORE_PATH
    ) -> set[str]:
        """Loads ignore patterns from configuration files.

        Args:
            ignore_dir: Directory containing ignore pattern files

        Returns:
            Combined set of default and custom ignore patterns
        """
        if not ignore_dir.is_dir():
            return DEFAULT_IGNORED_PATTERNS

        logger.debug(f"PATTERNS: {extra_patterns}")
        patterns = DEFAULT_IGNORED_PATTERNS.union(extra_patterns or {})
        for file in ignore_dir.iterdir():
            with file.open() as f:
                patterns.update(
                    [line.strip() for line in f if line.strip() and not line.startswith("#")]
                )

        return patterns

    def is_ignored(self, item: str) -> bool:
        """Checks if a path should be ignored during refactoring.

        Args:
            item: File or directory path to check

        Returns:
            True if the path matches any ignore pattern, False otherwise
        """
        return any(fnmatch.fnmatch(item, pattern) for pattern in self.ignore_patterns)

    def traverse(self, directory: Path) -> None:
        """Recursively scans a directory for Python files, skipping ignored paths.

        Args:
            directory: Root directory to scan
        """
        for item in directory.iterdir():
            if item.is_dir():
                logger.debug(f"Scanning directory: {item!s}")
                if self.is_ignored(item.name):
                    logger.debug(f"Ignored directory: {item!s}")
                    continue

                self.traverse(item)
            elif item.is_file() and not self.is_ignored(str(item)) and item.suffix == ".py":
                self.py_files.append(item)

    def traverse_and_process(self, directory: Path, smell_id: str) -> None:
        """Processes all Python files in a directory.

        Args:
            directory: Root directory containing files to process
        """
        if not self.py_files:
            self.traverse(directory)
        for file in self.py_files:
            logger.debug(f"Processing file: {file!s}")
            if self._process_file(file, smell_id):
                if file not in self.modified_files and not file.samefile(self.target_file):
                    self.modified_files.append(file)
            logger.debug("Finished processing file")

    @abstractmethod
    def _process_file(self, file: Path, smell_id: str) -> bool:
        """Processes an individual file (implemented by concrete refactorers).

        Args:
            file: Python file to process

        Returns:
            True if the file was modified, False otherwise
        """
        pass
