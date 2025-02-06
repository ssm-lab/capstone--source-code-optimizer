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
        """
        Analyzes a Python file using AST-based smell detectors.

        Args:
            file_path (Path): The path to the file to analyze.
            extra_options (list): A list of tuples containing detector functions and their parameters.

        Returns:
            list[Smell]: A list of detected code smells.
        """
        source_code = file_path.read_text()
        tree = parse(source_code)

        smells_data: list[Smell] = []
        for detector, params in extra_options:
            if callable(detector):
                result = detector(file_path, tree, **params)
                smells_data.extend(result)

        return smells_data
