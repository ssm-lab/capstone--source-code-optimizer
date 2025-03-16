import os
import stat


class RefactoringError(Exception):
    """Exception raised for errors that occured during the refcatoring process.

    Attributes:
        targetFile -- file being refactored
        message -- explanation of the error
    """

    def __init__(self, targetFile: str, message: str) -> None:
        self.targetFile = targetFile
        super().__init__(message)


class EnergySavingsError(RefactoringError):
    pass


def remove_readonly(func, path, _):  # noqa: ANN001
    # "Clear the readonly bit and reattempt the removal"
    os.chmod(path, stat.S_IWRITE)  # noqa: PTH101
    func(path)
