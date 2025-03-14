from typing import Callable, Any
from pathlib import Path
from ast import AST, parse


from .base_analyzer import Analyzer
from ..data_types.smell import Smell


class ASTAnalyzer(Analyzer):
    def analyze(
        self,
        file_path: Path,
        extra_options: list[tuple[Callable[[Path, AST], list[Smell]], dict[str, Any]]],
    ):
        smells_data: list[Smell] = []

        source_code = file_path.read_text()

        tree = parse(source_code)

        for detector, params in extra_options:
            if callable(detector):
                result = detector(file_path, tree, **params)
                smells_data.extend(result)

        return smells_data
