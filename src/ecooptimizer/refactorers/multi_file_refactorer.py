# pyright: reportOptionalMemberAccess=false
from abc import abstractmethod
import fnmatch
from pathlib import Path
from typing import TypeVar

from ..config import CONFIG

from .base_refactorer import BaseRefactorer

from ..data_types.smell import Smell


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
        self.target_file: Path = None  # type: ignore
        self.ignore_patterns = self._load_ignore_patterns()
        self.py_files: list[Path] = []

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

    def traverse(self, directory: Path):
        for item in directory.iterdir():
            if item.is_dir():
                CONFIG["refactorLogger"].debug(f"Scanning directory: {item!s}, name: {item.name}")
                if self.is_ignored(item):
                    CONFIG["refactorLogger"].debug(f"Ignored directory: {item!s}")
                    continue

                CONFIG["refactorLogger"].debug(f"Entering directory: {item!s}")
                self.traverse_and_process(item)
            elif item.is_file() and item.suffix == ".py":
                self.py_files.append(item)

    def traverse_and_process(self, directory: Path):
        if not self.py_files:
            self.traverse(directory)
        for file in self.py_files:
            CONFIG["refactorLogger"].debug(f"Checking file: {file!s}")
            if self._process_file(file):
                if file not in self.modified_files and not file.samefile(self.target_file):
                    self.modified_files.append(file.resolve())
            CONFIG["refactorLogger"].debug("finished processing file")

    @abstractmethod
    def _process_file(self, file: Path) -> bool:
        """Abstract method to be implemented by subclasses to handle file processing."""
        pass
