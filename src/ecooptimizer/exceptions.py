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
