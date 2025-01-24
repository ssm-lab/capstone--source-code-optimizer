from typing import Callable, Any
from pathlib import Path
import ast

from .base_analyzer import Analyzer
from ..data_wrappers.smell import Smell


class ASTAnalyzer(Analyzer):
    def analyze(
        self,
        file_path: Path,
        extra_options: list[tuple[Callable[[Path, ast.AST], list[Smell]], dict[str, Any]]],
    ) -> list[Smell]:
        smells_data: list[Smell] = []

        source_code = file_path.read_text()

        tree = ast.parse(source_code)

        for detector, params in extra_options:
            if callable(detector):
                result = detector(file_path, tree, **params)
                smells_data.extend(result)

        return smells_data
