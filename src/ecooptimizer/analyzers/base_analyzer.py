from abc import ABC, abstractmethod
import ast
from pathlib import Path
from typing import Callable, Union

from ..data_wrappers.smell import Smell


class Analyzer(ABC):
    @abstractmethod
    def analyze(
        self,
        file_path: Path,
        extra_options: Union[list[str], tuple[Callable[[Path, ast.AST], list[Smell]]]],
    ) -> list[Smell]:
        pass
