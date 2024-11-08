import json
import os
from pylint.lint import Run
from pylint.reporters.json_reporter import JSONReporter
from io import StringIO
from .base_analyzer import Analyzer
from .ternary_expression_pylint_analyzer import TernaryExpressionPylintAnalyzer
from utils.analyzers_config import AllPylintSmells, EXTRA_PYLINT_OPTIONS

class PylintAnalyzer(Analyzer):
    def __init__(self, file_path, logger):
        """
        Initializes the PylintAnalyzer with a file path and logger, 
        setting up attributes to collect code smells.
        
        :param file_path: Path to the file to be analyzed.
        :param logger: Logger instance to handle log messages.
        """
        super().__init__(file_path, logger)

    def build_pylint_options(self):
        """
        Constructs the list of pylint options for analysis, including extra options from config.

        :return: List of pylint options for analysis.
        """
        return [self.file_path] + EXTRA_PYLINT_OPTIONS

    def analyze_smells(self):
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

            self._find_custom_pylint_smells()  # Find all custom smells in pylint-detected data

    def _find_custom_pylint_smells(self):
        """
        Identifies custom smells, like long ternary expressions, in Pylint-detected data.
        Updates self.smells_data with any new custom smells found.
        """
        self.logger.log("Examining pylint smells for custom code smells")
        ternary_analyzer = TernaryExpressionPylintAnalyzer(self.file_path, self.smells_data)
        self.smells_data = ternary_analyzer.detect_long_ternary_expressions()

    def get_smells_by_name(self, smell):
        """
        Retrieves smells based on the Smell enum (e.g., Smell.LONG_MESSAGE_CHAIN).
        
        :param smell: The Smell enum member to filter by.
        :return: List of report entries matching the smell name.
        """
        return [
            item for item in self.smells_data
            if item.get("message-id") == smell.value
        ]

    def get_configured_smells(self):
        """
        Filters the report data to retrieve only the smells with message IDs specified in the config.

        :return: List of detected code smells based on the configuration.
        """
        configured_smells = []
        for smell in AllPylintSmells:
            configured_smells.extend(self.get_smells_by_name(smell))
        return configured_smells
