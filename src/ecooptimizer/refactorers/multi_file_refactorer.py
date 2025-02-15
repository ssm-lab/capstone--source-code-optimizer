from abc import abstractmethod
import fnmatch
from pathlib import Path
from typing import TypeVar

from .. import OUTPUT_MANAGER

from .base_refactorer import BaseRefactorer

from ..data_types.smell import Smell

logger = OUTPUT_MANAGER.loggers["refactor_smell"]

T = TypeVar("T", bound=Smell)

DEFAULT_IGNORED_PATTERNS = {
    "__pycache__",
    "build",
    ".venv",
    "*.egg-info",
    ".git",
    "node_modules",
    ".*",
}

DEFAULT_IGNORE_PATH = Path(__file__).parent / "patterns_to_ignore"


class MultiFileRefactorer(BaseRefactorer[T]):
    def __init__(self):
        super().__init__()
        self.target_file: Path = None
        self.ignore_patterns = self._load_ignore_patterns()

    def _load_ignore_patterns(self, ignore_dir: Path = DEFAULT_IGNORE_PATH) -> set[str]:
        """Load ignore patterns from a file, similar to .gitignore."""
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
        """Check if a file or directory matches any ignore pattern."""
        return any(fnmatch.fnmatch(item.name, pattern) for pattern in self.ignore_patterns)

    def traverse_and_process(self, directory: Path):
        for item in directory.iterdir():
            if item.is_dir():
                logger.debug(f"Scanning directory: {item!s}, name: {item.name}")
                if self.is_ignored(item):
                    logger.debug(f"Ignored directory: {item!s}")
                    continue

                logger.debug(f"Entering directory: {item!s}")
                self.traverse_and_process(item)
            elif item.is_file() and item.suffix == ".py":
                logger.debug(f"Checking file: {item!s}")
                if self._process_file(item):
                    if item not in self.modified_files and not item.samefile(self.target_file):
                        self.modified_files.append(item.resolve())
                logger.debug("finished processing file")

    @abstractmethod
    def _process_file(self, file: Path) -> bool:
        """Abstract method to be implemented by subclasses to handle file processing."""
        pass
