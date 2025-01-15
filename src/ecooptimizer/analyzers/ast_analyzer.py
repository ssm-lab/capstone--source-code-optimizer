import ast
from pathlib import Path
from typing import Callable

from .base_analyzer import Analyzer


class ASTAnalyzer(Analyzer):
    def __init__(
        self,
        file_path: Path,
        extra_ast_options: list[Callable[[Path, ast.AST], list[dict[str, object]]]],
    ):
        """
        Analyzers to find code smells using Pylint for a given file.
        :param extra_pylint_options: Options to be passed into pylint.
        """
        super().__init__(file_path)
        self.ast_options = extra_ast_options

        with self.file_path.open("r") as file:
            self.source_code = file.read()

        self.tree = ast.parse(self.source_code)

    def analyze(self):
        """
        Detect smells using AST analysis.
        """
        for detector in self.ast_options:
            self.smells_data.extend(detector(self.file_path, self.tree))
