from pathlib import Path

from ..data_wrappers.smell import Smell
from ..utils.smells_registry import SMELL_REGISTRY


class RefactorerController:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.smell_counters = {}

    def run_refactorer(self, input_file: Path, smell: Smell):
        smell_id = smell.get("messageId")
        smell_symbol = smell.get("symbol")
        refactorer_class = self._get_refactorer(smell_symbol)
        output_file_path = None

        if refactorer_class:
            self.smell_counters[smell_id] = self.smell_counters.get(smell_id, 0) + 1
            file_count = self.smell_counters[smell_id]

            output_file_name = f"{input_file.stem}_{smell_id}_{file_count}.py"
            output_file_path = self.output_dir / output_file_name

            print(f"Refactoring {smell_symbol} using {refactorer_class.__name__}")
            refactorer = refactorer_class()
            refactorer.refactor(input_file, smell, output_file_path)
        else:
            print(f"No refactorer found for smell: {smell_symbol}")

        return output_file_path

    def _get_refactorer(self, smell_symbol: str):
        refactorer = SMELL_REGISTRY.get(smell_symbol)
        return refactorer.get("refactorer") if refactorer else None
