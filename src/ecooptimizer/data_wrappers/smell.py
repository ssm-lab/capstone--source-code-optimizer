from typing import Any, TypedDict

from ..utils.analyzers_config import CustomSmell, PylintSmell

from .custom_fields import BasicOccurence, CRCAddInfo, CRCOccurence, SCLAddInfo


class Smell(TypedDict):
    """
    Represents a code smell detected in a source file, including its location, type, and related metadata.

    Attributes:
        confidence (str): The level of confidence for the smell detection (e.g., "high", "medium", "low").
        message (str): A descriptive message explaining the nature of the smell.
        messageId (str): A unique identifier for the specific message or warning related to the smell.
        module (str): The name of the module or component in which the smell is located.
        obj (str): The specific object (e.g., function, class) associated with the smell.
        path (str): The relative path to the source file from the project root.
        symbol (str): The symbol or code construct (e.g., variable, method) involved in the smell.
        type (str): The type or category of the smell (e.g., "complexity", "duplication").
        occurences (list): A list of individual occurences of a same smell, contains positional info.
        additionalInfo (Any): Any custom information for a type of smell
    """

    confidence: str
    message: str
    messageId: CustomSmell | PylintSmell
    module: str
    obj: str | None
    path: str
    symbol: str
    type: str
    occurences: Any
    additionalInfo: Any


class CRCSmell(Smell):
    occurences: list[CRCOccurence]
    additionalInfo: CRCAddInfo


class SCLSmell(Smell):
    occurences: list[BasicOccurence]
    additionalInfo: SCLAddInfo


class LECSmell(Smell):
    occurences: BasicOccurence
    additionalInfo: None


class LLESmell(Smell):
    occurences: BasicOccurence
    additionalInfo: None


class LMCSmell(Smell):
    occurences: BasicOccurence
    additionalInfo: None


class LPLSmell(Smell):
    occurences: BasicOccurence
    additionalInfo: None


class UVASmell(Smell):
    occurences: BasicOccurence
    additionalInfo: None


class MIMSmell(Smell):
    occurences: BasicOccurence
    additionalInfo: None


class UGESmell(Smell):
    occurences: BasicOccurence
    additionalInfo: None
