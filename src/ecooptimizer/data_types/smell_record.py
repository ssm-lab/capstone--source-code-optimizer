from typing import Any, Callable, TypedDict

from ..refactorers.base_refactorer import BaseRefactorer


class SmellRecord(TypedDict):
    """
    Represents a code smell configuration used for analysis and refactoring details.

    Attributes:
        id (str): The unique identifier for the specific smell or rule.
        enabled (bool): Indicates whether the smell detection is enabled.
        analyzer_method (Any): The method used for analysis. Could be a string (e.g., "pylint") or a Callable (for AST).
        refactorer (Type[Any]): The class responsible for refactoring the detected smell.
        analyzer_options (dict[str, Any]): Optional configuration options for the analyzer method.
    """

    id: str
    enabled: bool
    analyzer_method: str
    checker: Callable | None  # type: ignore
    refactorer: type[BaseRefactorer]  # type: ignore # Refers to a class, not an instance
    analyzer_options: dict[str, Any]  # type: ignore
