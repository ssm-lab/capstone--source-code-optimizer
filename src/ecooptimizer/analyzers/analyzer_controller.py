from pathlib import Path

from .pylint_analyzer import PylintAnalyzer
from .ast_analyzer import ASTAnalyzer

from ..utils.smells_registry import SMELL_REGISTRY
from ..utils.smells_registry_helper import (
    filter_smells_by_method,
    generate_pylint_options,
    generate_ast_options,
)

from ..data_wrappers.smell import Smell


class AnalyzerController:
    def __init__(self):
        self.pylint_analyzer = PylintAnalyzer()
        self.ast_analyzer = ASTAnalyzer()

    def run_analysis(self, file_path: Path) -> list[Smell]:
        smells_data: list[Smell] = []

        pylint_smells = filter_smells_by_method(SMELL_REGISTRY, "pylint")
        ast_smells = filter_smells_by_method(SMELL_REGISTRY, "ast")

        if pylint_smells:
            pylint_options = generate_pylint_options(pylint_smells)
            smells_data.extend(self.pylint_analyzer.analyze(file_path, pylint_options))

        if ast_smells:
            ast_options = generate_ast_options(ast_smells)
            smells_data.extend(self.ast_analyzer.analyze(file_path, ast_options))

        return smells_data
