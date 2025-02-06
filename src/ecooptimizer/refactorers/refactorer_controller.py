import logging
from pathlib import Path

from ..data_types.smell import Smell
from ..utils.smells_registry import SMELL_REGISTRY

logger = logging.getLogger("refactorers")


class RefactorerController:
    """
    Controls the execution of code refactorers based on detected smells.
    """

    def __init__(self, output_dir: Path):
        """
        Initializes the refactoring controller.

        Args:
            output_dir (Path): Directory where refactored files will be stored.
        """
        self.output_dir = output_dir
        self.smell_counters = {}

    def run_refactorer(
        self, target_file: Path, source_dir: Path, smell: Smell, overwrite: bool = True
    ):
        """
        Executes the refactorer associated with the given smell.

        Args:
            target_file (Path): The file to be refactored.
            source_dir (Path): The directory containing the target file.
            smell (Smell): The detected code smell.
            overwrite (bool): Whether to overwrite existing files.

        Returns:
            list[Path]: List of modified files.

        Raises:
            NotImplementedError: If no refactorer is available for the given smell.
        """
        smell_id = smell.messageId
        smell_symbol = smell.symbol
        refactorer_class = self._get_refactorer(smell_symbol)
        modified_files = []

        if refactorer_class:
            self.smell_counters[smell_id] = self.smell_counters.get(smell_id, 0) + 1
            file_count = self.smell_counters[smell_id]

            output_file_name = f"{target_file.stem}_refactored_{smell_id}_{file_count}.py"
            output_file_path = self.output_dir / output_file_name

            logger.info(f"Refactoring {smell_symbol} using {refactorer_class.__name__}")

            refactorer = refactorer_class()
            refactorer.refactor(target_file, source_dir, smell, output_file_path, overwrite)
            modified_files = refactorer.modified_files
        else:
            logger.error(f"No refactorer found for smell: {smell_symbol}")
            raise NotImplementedError(f"No refactorer implemented for smell: {smell_symbol}")

        return modified_files

    def _get_refactorer(self, smell_symbol: str):
        """
        Retrieves the refactorer class for a given smell.

        Args:
            smell_symbol (str): The unique symbol of the smell.

        Returns:
            Callable | None: The refactorer class or None if not found.
        """
        refactorer = SMELL_REGISTRY.get(smell_symbol)
        return refactorer.get("refactorer") if refactorer else None
