from pathlib import Path

from ..data_types.smell import Smell
from ..utils.smells_registry import SMELL_REGISTRY


class RefactorerController:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.smell_counters = {}

    def run_refactorer(
        self, target_file: Path, source_dir: Path, smell: Smell, overwrite: bool = True
    ):
        smell_id = smell.messageId
        smell_symbol = smell.symbol
        refactorer_class = self._get_refactorer(smell_symbol)
        modified_files = []

        if refactorer_class:
            self.smell_counters[smell_id] = self.smell_counters.get(smell_id, 0) + 1
            file_count = self.smell_counters[smell_id]

            output_file_name = f"{target_file.stem}_path_{smell_id}_{file_count}.py"
            output_file_path = self.output_dir / output_file_name

            print(f"Refactoring {smell_symbol} using {refactorer_class.__name__}")
            refactorer = refactorer_class()
            refactorer.refactor(
                target_file, source_dir, smell, output_file_path, file_count, overwrite
            )
            modified_files = refactorer.modified_files
        else:
            print(f"No refactorer found for smell: {smell_symbol}")
            raise NotImplementedError(f"No refactorer implemented for smell: {smell_symbol}")

        return modified_files

    def _get_refactorer(self, smell_symbol: str):
        refactorer = SMELL_REGISTRY.get(smell_symbol)
        return refactorer.get("refactorer") if refactorer else None
