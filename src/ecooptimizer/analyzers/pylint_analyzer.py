import logging
from io import StringIO
import json
from pathlib import Path
from pylint.lint import Run
from pylint.reporters.json_reporter import JSON2Reporter

from ..data_types.custom_fields import AdditionalInfo, Occurence
from .base_analyzer import Analyzer
from ..data_types.smell import Smell

logger = logging.getLogger("analyzers")


class PylintAnalyzer(Analyzer):
    """
    Runs Pylint analysis on a given file and extracts detected code smells.
    """

    def build_smells(self, pylint_smells: dict):  # type: ignore
        """
        Converts raw Pylint output into structured `Smell` objects.

        Args:
            pylint_smells (dict): Raw Pylint messages.

        Returns:
            list[Smell]: A list of formatted smell objects.
        """
        smells: list[Smell] = []
        for smell in pylint_smells:
            smells.append(
                Smell(
                    confidence=smell["confidence"],
                    message=smell["message"],
                    messageId=smell["messageId"],
                    module=smell["module"],
                    obj=smell["obj"],
                    path=smell["absolutePath"],
                    symbol=smell["symbol"],
                    type=smell["type"],
                    occurences=[
                        Occurence(
                            line=smell["line"],
                            endLine=smell["endLine"],
                            column=smell["column"],
                            endColumn=smell["endColumn"],
                        )
                    ],
                    additionalInfo=AdditionalInfo(),
                )
            )
        return smells

    def analyze(self, file_path: Path, extra_options: list[str]):
        """
        Runs Pylint analysis on a given file and extracts smells.

        Args:
            file_path (Path): Path to the file to analyze.
            extra_options (list[str]): Additional Pylint configuration options.

        Returns:
            list[Smell]: A list of detected code smells.
        """
        smells_data: list[Smell] = []
        pylint_options = [str(file_path), *extra_options]

        with StringIO() as buffer:
            reporter = JSON2Reporter(buffer)

            try:
                Run(pylint_options, reporter=reporter, exit=False)
                buffer.seek(0)
                parsed_output = json.loads(buffer.getvalue())["messages"]
                smells_data.extend(self.build_smells(parsed_output))
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON output from Pylint: {e}")
            except Exception as e:
                logger.error(f"An error occurred during Pylint analysis: {e}")

        return smells_data
