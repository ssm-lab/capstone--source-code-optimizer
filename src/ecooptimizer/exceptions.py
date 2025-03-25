"""Custom exceptions and utilities for refactoring operations."""

import os
import stat


class RefactoringError(Exception):
    """Exception raised when errors occur during code refactoring.

    Args:
        targetFile: Path to the file being refactored
        message: Explanation of what went wrong
    """

    def __init__(self, targetFile: str, message: str) -> None:
        self.targetFile = targetFile
        super().__init__(message)


class EnergySavingsError(RefactoringError):
    """Special case of RefactoringError when no energy savings are achieved."""


def remove_readonly(func, path, _) -> None:  # noqa: ANN001
    """Removes readonly attribute from files/directories to enable deletion.

    Args:
        func: Original removal function that failed
        path: Path to the file/directory
        _: Unused excinfo parameter

    Note:
        Used as error handler for shutil.rmtree()
    """
    os.chmod(path, stat.S_IWRITE)  # noqa: PTH101
    func(path)
