from typing import Any, TypedDict

from ..utils.analyzers_config import CustomSmell, PylintSmell

from .occurence import BasicOccurence, CRCAddInfo, CRCOccurence, SCLAddInfo


class Smell(TypedDict):
    """
    Represents a code smell detected in a source file, including its location, type, and related metadata.

    Attributes:
        absolutePath (str): The absolute path to the source file containing the smell.
        column (int): The starting column in the source file where the smell is detected.
        confidence (str): The level of confidence for the smell detection (e.g., "high", "medium", "low").
        endColumn (int): The ending column in the source file for the smell location.
        endLine (int): The line number where the smell ends in the source file.
        line (int): The line number where the smell begins in the source file.
        message (str): A descriptive message explaining the nature of the smell.
        messageId (str): A unique identifier for the specific message or warning related to the smell.
        module (str): The name of the module or component in which the smell is located.
        obj (str): The specific object (e.g., function, class) associated with the smell.
        path (str): The relative path to the source file from the project root.
        symbol (str): The symbol or code construct (e.g., variable, method) involved in the smell.
        type (str): The type or category of the smell (e.g., "complexity", "duplication").
    """

    confidence: str
    message: str
    messageId: CustomSmell | PylintSmell
    module: str
    obj: str | None
    path: str
    symbol: str
    type: str
    occurences: list[Any]
    additionalInfo: Any


class CRCSmell(Smell):
    occurences: list[CRCOccurence]
    additionalInfo: CRCAddInfo


class SCLSmell(Smell):
    occurences: list[BasicOccurence]
    additionalInfo: SCLAddInfo


class LECSmell(Smell):
    occurences: list[BasicOccurence]
    additionalInfo: None


class LLESmell(Smell):
    occurences: list[BasicOccurence]
    additionalInfo: None


class LMCSmell(Smell):
    occurences: list[BasicOccurence]
    additionalInfo: None


class LPLSmell(Smell):
    occurences: list[BasicOccurence]
    additionalInfo: None


class UVASmell(Smell):
    occurences: list[BasicOccurence]
    additionalInfo: None


class MIMSmell(Smell):
    occurences: list[BasicOccurence]
    additionalInfo: None


class UGESmell(Smell):
    occurences: list[BasicOccurence]
    additionalInfo: None
