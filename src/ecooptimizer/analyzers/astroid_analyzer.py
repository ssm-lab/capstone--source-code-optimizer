from typing import Callable, Any
from pathlib import Path
from astroid import nodes, parse

from .base_analyzer import Analyzer
from ..data_types.smell import Smell


class AstroidAnalyzer(Analyzer):
    """
    Analyzes Python source code using the Astroid library to detect code smells.
    """

    def analyze(
        self,
        file_path: Path,
        extra_options: list[
            tuple[
                Callable[[Path, nodes.Module], list[Smell]],
                dict[str, Any],
            ]
        ],
    ):
        """
        Runs analysis on the given file using Astroid-based detectors.

        Args:
            file_path (Path): Path to the source file to analyze.
            extra_options (list[tuple[Callable[[Path, nodes.Module], list[Smell]], dict[str, Any]]]):
                A list of tuples where:
                - The first element is a detector function that analyzes the AST.
                - The second element is a dictionary of additional parameters for the detector.

        Returns:
            list[Smell]: A list of detected code smells.
        """
        smells_data: list[Smell] = []

        # Read the source code from the file
        source_code = file_path.read_text()

        # Parse the source code into an AST (Abstract Syntax Tree)
        tree = parse(source_code)

        # Apply each detector function to the AST and accumulate detected smells
        for detector, params in extra_options:
            if callable(detector):
                result = detector(file_path, tree, **params)
                smells_data.extend(result)

        return smells_data
