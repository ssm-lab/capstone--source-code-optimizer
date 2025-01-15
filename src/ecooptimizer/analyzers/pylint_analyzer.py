from io import StringIO
import json
from pathlib import Path
from pylint.lint import Run
from pylint.reporters.json_reporter import JSON2Reporter

from .base_analyzer import Analyzer


class PylintAnalyzer(Analyzer):
    def __init__(self, file_path: Path, extra_pylint_options: list[str]):
        """
        Analyzers to find code smells using Pylint for a given file.
        :param extra_pylint_options: Options to be passed into pylint.
        """
        super().__init__(file_path)
        self.pylint_options = [str(self.file_path), *extra_pylint_options]

    def analyze(self):
        """
        Executes pylint on the specified file.
        """
        with StringIO() as buffer:
            reporter = JSON2Reporter(buffer)

            try:
                Run(self.pylint_options, reporter=reporter, exit=False)
                buffer.seek(0)
                self.smells_data.extend(json.loads(buffer.getvalue())["messages"])
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON output from pylint: {e}")
            except Exception as e:
                print(f"An error occurred during pylint analysis: {e}")
