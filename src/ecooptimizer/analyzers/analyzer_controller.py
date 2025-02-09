from pathlib import Path

from ..data_types.smell import Smell
from ecooptimizer import OUTPUT_MANAGER
from .pylint_analyzer import PylintAnalyzer
from .ast_analyzer import ASTAnalyzer
from .astroid_analyzer import AstroidAnalyzer

from ..utils.smells_registry import SMELL_REGISTRY
from ..utils.analysis_tools import (
    filter_smells_by_method,
    generate_pylint_options,
    generate_custom_options,
)

detect_smells_logger = OUTPUT_MANAGER.loggers["detect_smells"]


class AnalyzerController:
    def __init__(self):
        """Initializes analyzers for different analysis methods."""
        self.pylint_analyzer = PylintAnalyzer()
        self.ast_analyzer = ASTAnalyzer()
        self.astroid_analyzer = AstroidAnalyzer()

    def run_analysis(self, file_path: Path):
        """
        Runs multiple analysis tools on the given Python file and logs the results.
        Returns a list of detected code smells.
        """
        smells_data: list[Smell] = []

        try:
            pylint_smells = filter_smells_by_method(SMELL_REGISTRY, "pylint")
            ast_smells = filter_smells_by_method(SMELL_REGISTRY, "ast")
            astroid_smells = filter_smells_by_method(SMELL_REGISTRY, "astroid")

            detect_smells_logger.info("🟢 Starting analysis process")
            detect_smells_logger.info(f"📂 Analyzing file: {file_path}")

            if pylint_smells:
                detect_smells_logger.info(f"🔍 Running Pylint analysis on {file_path}")
                pylint_options = generate_pylint_options(pylint_smells)
                pylint_results = self.pylint_analyzer.analyze(file_path, pylint_options)
                smells_data.extend(pylint_results)
                detect_smells_logger.info(
                    f"✅ Pylint analysis completed. {len(pylint_results)} smells detected."
                )

            if ast_smells:
                detect_smells_logger.info(f"🔍 Running AST analysis on {file_path}")
                ast_options = generate_custom_options(ast_smells)
                ast_results = self.ast_analyzer.analyze(file_path, ast_options)
                smells_data.extend(ast_results)
                detect_smells_logger.info(
                    f"✅ AST analysis completed. {len(ast_results)} smells detected."
                )

            if astroid_smells:
                detect_smells_logger.info(f"🔍 Running Astroid analysis on {file_path}")
                astroid_options = generate_custom_options(astroid_smells)
                astroid_results = self.astroid_analyzer.analyze(file_path, astroid_options)
                smells_data.extend(astroid_results)
                detect_smells_logger.info(
                    f"✅ Astroid analysis completed. {len(astroid_results)} smells detected."
                )

            if smells_data:
                detect_smells_logger.info("⚠️ Detected Code Smells:")
                for smell in smells_data:
                    if smell.occurences:
                        first_occurrence = smell.occurences[0]
                        total_occurrences = len(smell.occurences)
                        line_info = (
                            f"(Starting at Line {first_occurrence.line}, {total_occurrences} occurrences)"
                            if total_occurrences > 1
                            else f"(Line {first_occurrence.line})"
                        )
                    else:
                        line_info = ""

                    detect_smells_logger.info(f"   • {smell.symbol} {line_info}: {smell.message}")
            else:
                detect_smells_logger.info("🎉 No code smells detected.")

        except Exception as e:
            detect_smells_logger.error(f"❌ Error during analysis: {e!s}")

        return smells_data
