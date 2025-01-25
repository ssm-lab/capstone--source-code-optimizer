from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypeVar

from ..data_types.custom_fields import BasicAddInfo, BasicOccurence
from ..data_types.smell import Smell

O = TypeVar("O", bound=BasicOccurence)  # noqa: E741
A = TypeVar("A", bound=BasicAddInfo)


class BaseRefactorer(ABC):
    def __init__(self):
        self.modified_files: list[Path] = []

    @abstractmethod
    def refactor(
        self,
        target_file: Path,
        source_dir: Path,
        smell: Smell[O, A],
        output_file: Path,
        overwrite: bool = True,
    ):
        pass
