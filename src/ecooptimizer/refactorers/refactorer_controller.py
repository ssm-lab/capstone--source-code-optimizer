"""Controller for executing code smell refactoring operations."""

# pyright: reportOptionalMemberAccess=false
from pathlib import Path

from ..config import CONFIG
from ..data_types.smell import Smell
from ..utils.smells_registry import get_refactorer


class RefactorerController:
    """Orchestrates refactoring operations for detected code smells."""

    def __init__(self):
        """Initializes the controller with empty smell counters."""
        self.smell_counters = {}

    def run_refactorer(
        self, target_file: Path, source_dir: Path, smell: Smell, overwrite: bool = True
    ) -> list[Path]:
        """Executes the appropriate refactorer for a detected smell.

        Args:
            target_file: File containing the smell to refactor
            source_dir: Root directory of the source files
            smell: Detected smell instance with metadata
            overwrite: Whether to overwrite existing files

        Returns:
            List of paths to all modified files

        Raises:
            NotImplementedError: If no refactorer exists for this smell type
        """
        smell_id = smell.messageId
        smell_symbol = smell.symbol
        refactorer_class = get_refactorer(smell_symbol)
        modified_files = []

        if refactorer_class:
            self._track_smell_occurrence(smell_id)
            output_path = self._generate_output_path(target_file, smell_id)

            CONFIG["refactorLogger"].info(
                f"🔄 Running {refactorer_class.__name__} for {smell_symbol}"
            )

            refactorer = refactorer_class()
            refactorer.refactor(target_file, source_dir, smell, output_path, overwrite)
            modified_files = refactorer.modified_files
        else:
            self._handle_missing_refactorer(smell_symbol)

        return modified_files

    def _track_smell_occurrence(self, smell_id: str) -> None:
        """Increments counter for a specific smell type."""
        self.smell_counters[smell_id] = self.smell_counters.get(smell_id, 0) + 1

    def _generate_output_path(self, target_file: Path, smell_id: str) -> Path:
        """Generates output path for refactored file."""
        file_count = self.smell_counters[smell_id]
        output_name = f"{target_file.stem}_path_{smell_id}_{file_count}.py"
        return Path(__file__).parent / "../../../outputs" / output_name

    def _handle_missing_refactorer(self, smell_symbol: str) -> None:
        """Logs error and raises exception for unimplemented refactorers."""
        CONFIG["refactorLogger"].error(f"❌ No refactorer for smell: {smell_symbol}")
        raise NotImplementedError(f"No refactorer for smell: {smell_symbol}")
