from io import StringIO
import json
from pathlib import Path
from pylint.lint import Run
from pylint.reporters.json_reporter import JSON2Reporter

from .base_analyzer import Analyzer
from ..data_wrappers.smell import Smell


class PylintAnalyzer(Analyzer):
    def build_smells(self, pylint_smells: dict):  # type: ignore
        """Casts inital list of pylint smells to the proper Smell configuration."""
        smells: list[Smell] = []
        for smell in pylint_smells:
            smells.append(
                {
                    "confidence": smell["confidence"],
                    "message": smell["message"],
                    "messageId": smell["messageId"],
                    "module": smell["module"],
                    "obj": smell["obj"],
                    "path": smell["absolutePath"],
                    "symbol": smell["symbol"],
                    "type": smell["type"],
                    "occurences": [
                        {
                            "line": smell["line"],
                            "endLine": smell["endLine"],
                            "column": smell["column"],
                            "endColumn": smell["endColumn"],
                        }
                    ],
                    "additionalInfo": None,
                }
            )
        return smells

    def analyze(self, file_path: Path, extra_options: list[str]) -> list[Smell]:
        smells_data: list[Smell] = []
        pylint_options = [str(file_path), *extra_options]

        with StringIO() as buffer:
            reporter = JSON2Reporter(buffer)

            try:
                Run(pylint_options, reporter=reporter, exit=False)
                buffer.seek(0)
                smells_data.extend(self.build_smells(json.loads(buffer.getvalue())["messages"]))
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON output from pylint: {e}")
            except Exception as e:
                print(f"An error occurred during pylint analysis: {e}")

        return smells_data
