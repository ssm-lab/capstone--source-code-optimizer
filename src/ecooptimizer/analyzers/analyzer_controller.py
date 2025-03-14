# pyright: reportOptionalMemberAccess=false
from pathlib import Path
from typing import Callable, Any

from ..data_types.smell_record import SmellRecord

from ..config import CONFIG

from ..data_types.smell import Smell

from .pylint_analyzer import PylintAnalyzer
from .ast_analyzer import ASTAnalyzer
from .astroid_analyzer import AstroidAnalyzer

from ..utils.smells_registry import retrieve_smell_registry


class AnalyzerController:
    def __init__(self):
        """Initializes analyzers for different analysis methods."""
        self.pylint_analyzer = PylintAnalyzer()
        self.ast_analyzer = ASTAnalyzer()
        self.astroid_analyzer = AstroidAnalyzer()

    def run_analysis(self, file_path: Path, selected_smells: str | list[str] = "ALL"):
        """
        Runs multiple analysis tools on the given Python file and logs the results.
        Returns a list of detected code smells.
        """

        smells_data: list[Smell] = []

        if not selected_smells:
            raise TypeError("At least 1 smell must be selected for detection")

        SMELL_REGISTRY = retrieve_smell_registry(selected_smells)

        try:
            pylint_smells = self.filter_smells_by_method(SMELL_REGISTRY, "pylint")
            ast_smells = self.filter_smells_by_method(SMELL_REGISTRY, "ast")
            astroid_smells = self.filter_smells_by_method(SMELL_REGISTRY, "astroid")

            CONFIG["detectLogger"].info("🟢 Starting analysis process")
            CONFIG["detectLogger"].info(f"📂 Analyzing file: {file_path}")

            if pylint_smells:
                CONFIG["detectLogger"].info(f"🔍 Running Pylint analysis on {file_path}")
                pylint_options = self.generate_pylint_options(pylint_smells)
                pylint_results = self.pylint_analyzer.analyze(file_path, pylint_options)
                smells_data.extend(pylint_results)
                CONFIG["detectLogger"].info(
                    f"✅ Pylint analysis completed. {len(pylint_results)} smells detected."
                )

            if ast_smells:
                CONFIG["detectLogger"].info(f"🔍 Running AST analysis on {file_path}")
                ast_options = self.generate_custom_options(ast_smells)
                ast_results = self.ast_analyzer.analyze(file_path, ast_options)
                smells_data.extend(ast_results)
                CONFIG["detectLogger"].info(
                    f"✅ AST analysis completed. {len(ast_results)} smells detected."
                )

            if astroid_smells:
                CONFIG["detectLogger"].info(f"🔍 Running Astroid analysis on {file_path}")
                astroid_options = self.generate_custom_options(astroid_smells)
                astroid_results = self.astroid_analyzer.analyze(file_path, astroid_options)
                smells_data.extend(astroid_results)
                CONFIG["detectLogger"].info(
                    f"✅ Astroid analysis completed. {len(astroid_results)} smells detected."
                )

            if smells_data:
                CONFIG["detectLogger"].info("⚠️ Detected Code Smells:")
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

                    CONFIG["detectLogger"].info(f"   • {smell.symbol} {line_info}: {smell.message}")
            else:
                CONFIG["detectLogger"].info("🎉 No code smells detected.")

        except Exception as e:
            CONFIG["detectLogger"].error(f"❌ Error during analysis: {e!s}")

        return smells_data

    @staticmethod
    def filter_smells_by_method(
        smell_registry: dict[str, SmellRecord], method: str
    ) -> dict[str, SmellRecord]:
        filtered = {
            name: smell
            for name, smell in smell_registry.items()
            if smell["enabled"] and (method == smell["analyzer_method"])
        }
        return filtered

    @staticmethod
    def generate_pylint_options(filtered_smells: dict[str, SmellRecord]) -> list[str]:
        pylint_smell_symbols = []
        extra_pylint_options = [
            "--disable=all",
        ]

        for symbol, smell in zip(filtered_smells.keys(), filtered_smells.values()):
            pylint_smell_symbols.append(symbol)

            if len(smell["analyzer_options"]) > 0:
                for param_data in smell["analyzer_options"].values():
                    flag = param_data["flag"]
                    value = param_data["value"]
                    if value:
                        extra_pylint_options.append(f"{flag}={value}")

        extra_pylint_options.append(f"--enable={','.join(pylint_smell_symbols)}")
        return extra_pylint_options

    @staticmethod
    def generate_custom_options(
        filtered_smells: dict[str, SmellRecord],
    ) -> list[tuple[Callable, dict[str, Any]]]:  # type: ignore
        ast_options = []
        for smell in filtered_smells.values():
            method = smell["checker"]
            options = smell["analyzer_options"]
            ast_options.append((method, options))

        return ast_options
