"""Pylint-based analyzer for detecting code smells."""

from io import StringIO
import json
from pathlib import Path
from pylint.lint import Run
from pylint.reporters.json_reporter import JSON2Reporter

from ..config import CONFIG
from ..data_types.custom_fields import AdditionalInfo, Occurence
from .base_analyzer import Analyzer
from ..data_types.smell import Smell


class PylintAnalyzer(Analyzer):
    """Analyzer that detects code smells using Pylint."""

    def _build_smells(self, pylint_smells: dict) -> list[Smell]:  # type: ignore
        """Convert Pylint JSON output to Eco Optimizer smell objects.

        Args:
            pylint_smells: Dictionary of smells from Pylint JSON report

        Returns:
            list[Smell]: List of converted smell objects
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

    def analyze(self, file_path: Path, extra_options: list[str]) -> list[Smell]:
        """Run Pylint analysis on a source file and return detected smells.

        Args:
            file_path: Path to the source file to analyze
            extra_options: Additional Pylint command-line options

        Returns:
            list[Smell]: Detected code smells

        Note:
            Catches and logs Pylint execution and JSON parsing errors
        """
        smells_data: list[Smell] = []
        pylint_options = [str(file_path), *extra_options]

        with StringIO() as buffer:
            reporter = JSON2Reporter(buffer)

            try:
                Run(pylint_options, reporter=reporter, exit=False)
                buffer.seek(0)
                smells_data.extend(self._build_smells(json.loads(buffer.getvalue())["messages"]))
            except json.JSONDecodeError as e:
                CONFIG["detectLogger"].error(f"❌ Failed to parse JSON output from pylint: {e}")
            except Exception as e:
                CONFIG["detectLogger"].error(f"❌ An error occurred during pylint analysis: {e}")

        return smells_data
