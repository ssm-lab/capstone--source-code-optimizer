from pathlib import Path

from .pylint_analyzer import PylintAnalyzer
from .ast_analyzer import ASTAnalyzer

from ..utils.smells_registry import SMELL_REGISTRY
from ..utils.smells_registry_helper import prepare_smell_analysis

from ..data_wrappers.smell import Smell


class AnalyzerController:
    def __init__(self):
        self.pylint_analyzer = PylintAnalyzer()
        self.ast_analyzer = ASTAnalyzer()

    def run_analysis(self, file_path: Path) -> list[Smell]:
        smells_data: list[Smell] = []

        options = prepare_smell_analysis(SMELL_REGISTRY)

        smells_data.extend(self.pylint_analyzer.analyze(file_path, options["pylint_options"]))
        smells_data.extend(self.ast_analyzer.analyze(file_path, options["ast_analyzers"]))

        return smells_data
