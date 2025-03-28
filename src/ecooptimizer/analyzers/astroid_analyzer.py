"""Astroid-based code analysis framework for detecting code smells."""

from typing import Callable, Any
from pathlib import Path
from astroid import nodes, parse

from ecooptimizer.analyzers.base_analyzer import Analyzer
from ecooptimizer.data_types.smell import Smell


class AstroidAnalyzer(Analyzer):
    """Analyzes Python source code using Astroid to detect code smells.

    This analyzer executes multiple detection functions on parsed Astroid nodes
    and aggregates their results.
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
    ) -> list[Smell]:
        """Runs all configured detectors on the given source file.

        Args:
            file_path: Path to the Python source file to analyze
            extra_options: List of detector functions with their parameters as
                          tuples of (detector_function, params_dict)

        Returns:
            list[Smell]: Combined list of all smells detected by all detectors
        """
        smells_data: list[Smell] = []
        source_code = file_path.read_text()
        tree = parse(source_code)

        for detector, params in extra_options:
            if callable(detector):
                result = detector(file_path, tree, **params)
                smells_data.extend(result)

        return smells_data
