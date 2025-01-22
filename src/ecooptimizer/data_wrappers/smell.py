from typing import TypedDict, Optional, List


class Occurrence(TypedDict):
    """
    Represents a single occurrence of a repeated function call.

    Attributes:
    - line: The line number of the function call
    - column: The column offset where the function call starts
    - call_string: The exact function call string
    """

    line: int
    column: int
    call_string: str


class Smell(TypedDict):
    """
    Represents a code smell detected in a source file, including its location, type, and related metadata.

    Attributes:
        absolutePath (str): The absolute path to the source file containing the smell.
        column (int): The starting column in the source file where the smell is detected.
        confidence (str): The level of confidence for the smell detection (e.g., "high", "medium", "low").
        endColumn (int): (Optional) The ending column in the source file for the smell location.
        endLine (int): (Optional) The line number where the smell ends in the source file.
        line (int): The line number where the smell begins in the source file.
        message (str): A descriptive message explaining the nature of the smell.
        messageId (str): A unique identifier for the specific message or warning related to the smell.
        module (str): The name of the module or component in which the smell is located.
        obj (str): The specific object (e.g., function, class) associated with the smell.
        path (str): The relative path to the source file from the project root.
        symbol (str): The symbol or code construct (e.g., variable, method) involved in the smell.
        type (str): The type or category of the smell (e.g., "complexity", "duplication").
        repetitions(int): (Optional) The number of repeated occurrences (for repeated calls).
        occurrences(Optional[List[Occurrence]]): (Optional) A list of dictionaries describing detailed occurrences (for repeated calls).
    """

    absolutePath: str
    column: int
    confidence: str
    endColumn: int | None
    endLine: int | None
    line: int
    message: str
    messageId: str
    module: str
    obj: str
    path: str
    symbol: str
    type: str
    repetitions: Optional[int]
    occurrences: Optional[List[Occurrence]]
