from pathlib import Path

from ..data_types.custom_fields import BasicAddInfo, BasicOccurence

from .pylint_analyzer import PylintAnalyzer
from .ast_analyzer import ASTAnalyzer
from .astroid_analyzer import AstroidAnalyzer

from ..utils.smells_registry import SMELL_REGISTRY
from ..utils.smells_registry_helper import (
    filter_smells_by_id,
    filter_smells_by_method,
    generate_pylint_options,
    generate_custom_options,
)

from ..data_types.smell import Smell


class AnalyzerController:
    def __init__(self):
        self.pylint_analyzer = PylintAnalyzer()
        self.ast_analyzer = ASTAnalyzer()
        self.astroid_analyzer = AstroidAnalyzer()

    def run_analysis(self, file_path: Path):
        smells_data: list[Smell[BasicOccurence, BasicAddInfo]] = []

        pylint_smells = filter_smells_by_method(SMELL_REGISTRY, "pylint")
        ast_smells = filter_smells_by_method(SMELL_REGISTRY, "ast")
        astroid_smells = filter_smells_by_method(SMELL_REGISTRY, "astroid")

        if pylint_smells:
            pylint_options = generate_pylint_options(pylint_smells)
            smells_data.extend(self.pylint_analyzer.analyze(file_path, pylint_options))

        if ast_smells:
            ast_options = generate_custom_options(ast_smells)
            smells_data.extend(self.ast_analyzer.analyze(file_path, ast_options))

        if astroid_smells:
            astroid_options = generate_custom_options(astroid_smells)
            smells_data.extend(self.astroid_analyzer.analyze(file_path, astroid_options))

        return filter_smells_by_id(smells_data)
