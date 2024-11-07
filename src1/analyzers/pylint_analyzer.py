import json
from pylint.lint import Run
from pylint.reporters.json_reporter import JSONReporter
from io import StringIO
from .base_analyzer import Analyzer
from utils.analyzers_config import PylintSmell, EXTRA_PYLINT_OPTIONS

class PylintAnalyzer(Analyzer):
    def __init__(self, file_path):
        super().__init__(file_path)

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
            print(f"File not found: {self.file_path}")
            return

        print(f"Running pylint analysis on {self.file_path}")

        # Capture pylint output in a JSON format buffer
        with StringIO() as buffer:
            reporter = JSONReporter(buffer)
            pylint_options = self.build_pylint_options()

            try:
                # Run pylint with JSONReporter
                Run(pylint_options, reporter=reporter, exit=False)

                # Parse the JSON output
                buffer.seek(0)
                self.report_data = json.loads(buffer.getvalue())
                print("Pylint JSON analysis completed.")
            except json.JSONDecodeError as e:
                print("Failed to parse JSON output from pylint:", e)
            except Exception as e:
                print("An error occurred during pylint analysis:", e)

    def get_smells_by_name(self, smell):
        """
        Retrieves smells based on the Smell enum (e.g., Smell.LINE_TOO_LONG).
        
        :param smell: The Smell enum member to filter by.
        :return: List of report entries matching the smell name.
        """
        return [
            item for item in self.report_data
            if item.get("message-id") == smell.value
        ]

    def get_configured_smells(self):
        """
        Filters the report data to retrieve only the smells with message IDs specified in the config.

        :return: List of detected code smells based on the configuration.
        """
        configured_smells = []
        for smell in PylintSmell:
            configured_smells.extend(self.get_smells_by_name(smell))
        return configured_smells
