from io import StringIO
import json
from pathlib import Path
from pylint.lint import Run
from pylint.reporters.json_reporter import JSON2Reporter

from ..data_types.custom_fields import BasicAddInfo, BasicOccurence

from .base_analyzer import Analyzer
from ..data_types.smell import Smell


class PylintAnalyzer(Analyzer):
    def build_smells(self, pylint_smells: dict):  # type: ignore
        """Casts inital list of pylint smells to the proper Smell configuration."""
        smells: list[Smell[BasicOccurence, BasicAddInfo]] = []
        for smell in pylint_smells:
            smells.append(
                # Initialize the SmellModel instance
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
                        BasicOccurence(
                            line=smell["line"],
                            endLine=smell["endLine"],
                            column=smell["column"],
                            endColumn=smell["endColumn"],
                        )
                    ],
                )
            )
        return smells

    def analyze(self, file_path: Path, extra_options: list[str]):
        smells_data: list[Smell[BasicOccurence, BasicAddInfo]] = []
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
