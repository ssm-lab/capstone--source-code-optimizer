from typing import Callable, Any
from pathlib import Path
from astroid import nodes, parse

from ..data_types.custom_fields import BasicAddInfo, BasicOccurence

from .base_analyzer import Analyzer
from ..data_types.smell import Smell


class AstroidAnalyzer(Analyzer):
    def analyze(
        self,
        file_path: Path,
        extra_options: list[
            tuple[
                Callable[[Path, nodes.Module], list[Smell[BasicOccurence, BasicAddInfo]]],
                dict[str, Any],
            ]
        ],
    ):
        smells_data: list[Smell[BasicOccurence, BasicAddInfo]] = []

        source_code = file_path.read_text()

        tree = parse(source_code)

        for detector, params in extra_options:
            if callable(detector):
                result = detector(file_path, tree, **params)
                smells_data.extend(result)

        return smells_data
