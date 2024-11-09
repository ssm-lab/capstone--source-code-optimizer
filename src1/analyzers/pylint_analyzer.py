import json
import ast
import os

from pylint.lint import Run
from pylint.reporters.json_reporter import JSONReporter
from io import StringIO

from utils.logger import Logger

from .base_analyzer import Analyzer
from utils.analyzers_config import PylintSmell, CustomSmell, IntermediateSmells, EXTRA_PYLINT_OPTIONS

from utils.ast_parser import parse_line

class PylintAnalyzer(Analyzer):
    def __init__(self, file_path: str, logger: Logger):
        super().__init__(file_path, logger)

    def build_pylint_options(self):
        """
        Constructs the list of pylint options for analysis, including extra options from config.

        :return: List of pylint options for analysis.
        """
        return [self.file_path] + EXTRA_PYLINT_OPTIONS
        
    def analyze(self):
        """
        Executes pylint on the specified file and captures the output in JSON format.
        """
        if not self.validate_file():
            return

        self.logger.log(f"Running Pylint analysis on {os.path.basename(self.file_path)}")

        # Capture pylint output in a JSON format buffer
        with StringIO() as buffer:
            reporter = JSONReporter(buffer)
            pylint_options = self.build_pylint_options()

            try:
                # Run pylint with JSONReporter
                Run(pylint_options, reporter=reporter, exit=False)

                # Parse the JSON output
                buffer.seek(0)
                self.smells_data = json.loads(buffer.getvalue())
                self.logger.log("Pylint analyzer completed successfully.")
            except json.JSONDecodeError as e:
                self.logger.log(f"Failed to parse JSON output from pylint: {e}")
            except Exception as e:
                self.logger.log(f"An error occurred during pylint analysis: {e}")

    def configure_smells(self):
        """
        Filters the report data to retrieve only the smells with message IDs specified in the config.
        """
        self.logger.log("Filtering pylint smells")

        configured_smells: list[object] = []

        for smell in self.smells_data:
            if smell["message-id"] in PylintSmell.list():
                configured_smells.append(smell)

            if smell == IntermediateSmells.LINE_TOO_LONG.value:
                self.filter_ternary(smell)

        self.smells_data = configured_smells

    def filter_for_one_code_smell(self, pylint_results: list[object], code: str):
        """
        Filters LINE_TOO_LONG smells to find ternary expression smells
        """
        filtered_results: list[object] = []
        for error in pylint_results:
            if error["message-id"] == code:
                filtered_results.append(error)

        return filtered_results
    
    def filter_ternary(self, smell: object): 
        root_node = parse_line(self.file_path, smell["line"])

        if root_node is None:
            return

        for node in ast.walk(root_node):
            if isinstance(node, ast.IfExp):  # Ternary expression node
                smell["message-id"] = CustomSmell.LONG_TERN_EXPR.value
                self.smells_data.append(smell)
                break