from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar

from ..data_types.smell import Smell

T = TypeVar("T", bound=Smell)


class BaseRefactorer(ABC, Generic[T]):
    def __init__(self):
        self.modified_files: list[Path] = []

    @abstractmethod
    def refactor(
        self,
        target_file: Path,
        source_dir: Path,
        smell: T,
        output_file: Path,
        overwrite: bool = True,
    ):
        pass
