# pyright: reportOptionalMemberAccess=false
from pathlib import Path
import traceback
from typing import Callable, Any

from ..data_types.smell_record import SmellRecord

from ..config import CONFIG

from ..data_types.smell import Smell

from .pylint_analyzer import PylintAnalyzer
from .ast_analyzer import ASTAnalyzer
from .astroid_analyzer import AstroidAnalyzer

from ..utils.smells_registry import retrieve_smell_registry

logger = CONFIG["detectLogger"]


class AnalyzerController:
    def __init__(self):
        """Initializes analyzers for different analysis methods."""
        self.pylint_analyzer = PylintAnalyzer()
        self.ast_analyzer = ASTAnalyzer()
        self.astroid_analyzer = AstroidAnalyzer()

    def run_analysis(
        self, file_path: Path, enabled_smells: dict[str, dict[str, int | str]] | list[str]
    ) -> list[Smell]:
        """
        Runs multiple analysis tools on the given Python file and logs the results.
        Accepts a dictionary with additional options for each smell.
        """

        smells_data: list[Smell] = []

        if not enabled_smells:
            raise TypeError("At least one smell must be selected for detection.")

        # Retrieve smells from registry and update their options dynamically
        SMELL_REGISTRY = retrieve_smell_registry(enabled_smells)

        try:
            pylint_smells = self.filter_smells_by_method(SMELL_REGISTRY, "pylint")
            ast_smells = self.filter_smells_by_method(SMELL_REGISTRY, "ast")
            astroid_smells = self.filter_smells_by_method(SMELL_REGISTRY, "astroid")

            logger.info("🟢 Starting analysis process")
            logger.info(f"📂 Analyzing file: {file_path}")

            if pylint_smells:
                logger.info(f"🔍 Running Pylint analysis on {file_path}")
                pylint_options = self.generate_pylint_options(pylint_smells)
                pylint_results = self.pylint_analyzer.analyze(file_path, pylint_options)
                smells_data.extend(pylint_results)
                logger.info(f"✅ Pylint analysis completed. {len(pylint_results)} smells detected.")

            if ast_smells:
                logger.info(f"🔍 Running AST analysis on {file_path}")
                ast_options = self.generate_custom_options(ast_smells)

                ast_results = self.ast_analyzer.analyze(file_path, ast_options)
                smells_data.extend(ast_results)
                logger.info(f"✅ AST analysis completed. {len(ast_results)} smells detected.")

            if astroid_smells:
                logger.info(f"🔍 Running Astroid analysis on {file_path}")
                astroid_options = self.generate_custom_options(astroid_smells)
                astroid_results = self.astroid_analyzer.analyze(file_path, astroid_options)
                smells_data.extend(astroid_results)
                logger.info(
                    f"✅ Astroid analysis completed. {len(astroid_results)} smells detected."
                )

            if smells_data:
                logger.info("⚠️ Detected Code Smells:")
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

                    logger.info(f"   • {smell.symbol} {line_info}: {smell.message}")
            else:
                logger.info("🎉 No code smells detected.")

        except Exception as e:
            logger.error(f"❌ Error during analysis: {e!s}")
            traceback.print_exc()
            raise e

        return smells_data

    @staticmethod
    def filter_smells_by_method(
        smell_registry: dict[str, SmellRecord], method: str
    ) -> dict[str, SmellRecord]:
        return {
            name: smell
            for name, smell in smell_registry.items()
            if smell["enabled"] and smell["analyzer_method"] == method
        }

    @staticmethod
    def generate_pylint_options(filtered_smells: dict[str, SmellRecord]) -> list[str]:
        pylint_options = ["--disable=all"]

        for _smell_name, smell in filtered_smells.items():
            if len(smell["analyzer_options"]) > 0:
                for param_data in smell["analyzer_options"].values():
                    flag = param_data["flag"]
                    value = param_data["value"]
                    if value:
                        pylint_options.append(f"{flag}={value}")

        pylint_options.append(f"--enable={','.join(filtered_smells.keys())}")
        return pylint_options

    @staticmethod
    def generate_custom_options(
        filtered_smells: dict[str, SmellRecord],
    ) -> list[tuple[Callable | None, dict[str, Any]]]:  # type: ignore
        return [(smell["checker"], smell["analyzer_options"]) for smell in filtered_smells.values()]
