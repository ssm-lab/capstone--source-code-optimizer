# src/refactorer/base_refactorer.py

from abc import ABC, abstractmethod


class BaseRefactorer(ABC):
    """
    Abstract base class for refactorers.
    Subclasses should implement the `refactor` method.
    """
    @abstractmethod
    def __init__(self, code):
        """
        Initialize the refactorer with the code to refactor.

        :param code: The code that needs refactoring
        """
        self.code = code

    @abstractmethod
    def refactor(code_smell_error, input_code):
        """
        Perform the refactoring process.
        Must be implemented by subclasses.
        """
        pass