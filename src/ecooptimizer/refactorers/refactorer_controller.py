# pyright: reportOptionalMemberAccess=false
from pathlib import Path

from ..config import CONFIG

from ..data_types.smell import Smell
from ..utils.smells_registry import get_refactorer


class RefactorerController:
    def __init__(self):
        """Manages the execution of refactorers for detected code smells."""
        self.smell_counters = {}

    def run_refactorer(
        self, target_file: Path, source_dir: Path, smell: Smell, overwrite: bool = True
    ):
        """Executes the appropriate refactorer for the given smell.

        Args:
            target_file (Path): The file to be refactored.
            source_dir (Path): The source directory containing the file.
            smell (Smell): The detected smell to be refactored.
            overwrite (bool, optional): Whether to overwrite existing files. Defaults to True.

        Returns:
            list[Path]: A list of modified files resulting from the refactoring process.

        Raises:
            NotImplementedError: If no refactorer exists for the given smell.
        """
        smell_id = smell.messageId
        smell_symbol = smell.symbol
        refactorer_class = get_refactorer(smell_symbol)
        modified_files = []

        if refactorer_class:
            self.smell_counters[smell_id] = self.smell_counters.get(smell_id, 0) + 1
            file_count = self.smell_counters[smell_id]

            output_file_name = f"{target_file.stem}_path_{smell_id}_{file_count}.py"
            output_file_path = Path(__file__).parent / "../../../outputs" / output_file_name

            CONFIG["refactorLogger"].info(
                f"🔄 Running refactoring for {smell_symbol} using {refactorer_class.__name__}"
            )
            refactorer = refactorer_class()
            refactorer.refactor(target_file, source_dir, smell, output_file_path, overwrite)
            modified_files = refactorer.modified_files
        else:
            CONFIG["refactorLogger"].error(f"❌ No refactorer found for smell: {smell_symbol}")
            raise NotImplementedError(f"No refactorer implemented for smell: {smell_symbol}")

        return modified_files
