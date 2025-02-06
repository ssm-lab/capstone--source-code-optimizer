import logging
from pathlib import Path

from .pylint_analyzer import PylintAnalyzer
from .ast_analyzer import ASTAnalyzer
from .astroid_analyzer import AstroidAnalyzer

from ..utils.smells_registry import SMELL_REGISTRY
from ..utils.analysis_tools import (
    filter_smells_by_id,
    filter_smells_by_method,
    generate_pylint_options,
    generate_custom_options,
)

from ..data_types.smell import Smell

# Logger for analyzer operations
logger = logging.getLogger("analyzers")


class AnalyzerController:
    """
    Controls the execution of different static code analyzers (Pylint, AST, Astroid)
    to detect code smells in a given Python file.
    """

    def __init__(self):
        """Initializes the available analyzers."""
        self.pylint_analyzer = PylintAnalyzer()
        self.ast_analyzer = ASTAnalyzer()
        self.astroid_analyzer = AstroidAnalyzer()

    def run_analysis(self, file_path: Path) -> list[Smell]:
        """
        Executes code analysis using Pylint, AST, and Astroid-based analyzers.

        Args:
            file_path (Path): Path to the Python file being analyzed.

        Returns:
            list[Smell]: A list of detected code smells.
        """
        logger.info("=" * 100)
        logger.info(f"Starting new analysis for file: {file_path}")

        smells_data: list[Smell] = []

        # Retrieve relevant smell detection rules for each analyzer
        pylint_smells = filter_smells_by_method(SMELL_REGISTRY, "pylint")
        ast_smells = filter_smells_by_method(SMELL_REGISTRY, "ast")
        astroid_smells = filter_smells_by_method(SMELL_REGISTRY, "astroid")

        # Run Pylint analyzer if configured
        if pylint_smells:
            logger.info("Running Pylint analyzer...")
            pylint_options = generate_pylint_options(pylint_smells)
            pylint_results = self.pylint_analyzer.analyze(file_path, pylint_options)
            smells_data.extend(pylint_results)
            logger.info(f"Pylint detected {len(pylint_results)} smells.")
        else:
            logger.warning("Skipping Pylint analysis (No smells configured).")

        # Run AST analyzer if configured
        if ast_smells:
            logger.info("Running AST analyzer...")
            ast_options = generate_custom_options(ast_smells)
            ast_results = self.ast_analyzer.analyze(file_path, ast_options)
            smells_data.extend(ast_results)
            logger.info(f"AST detected {len(ast_results)} smells.")
        else:
            logger.warning("Skipping AST analysis (No smells configured).")

        # Run Astroid analyzer if configured
        if astroid_smells:
            logger.info("Running Astroid analyzer...")
            astroid_options = generate_custom_options(astroid_smells)
            astroid_results = self.astroid_analyzer.analyze(file_path, astroid_options)
            smells_data.extend(astroid_results)
            logger.info(f"Astroid detected {len(astroid_results)} smells.")
        else:
            logger.warning("Skipping Astroid analysis (No smells configured).")

        # Filter and remove duplicate smells
        filtered_smells = filter_smells_by_id(smells_data)
        logger.info(
            f"Analysis completed for {file_path}. Total smells detected: {len(filtered_smells)}"
        )
        logger.info("=" * 100 + "\n")  # End marker

        return filtered_smells
