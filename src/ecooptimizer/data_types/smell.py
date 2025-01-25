from pydantic import BaseModel
from typing import Generic, TypeVar


from .custom_fields import (
    BasicAddInfo,
    BasicOccurence,
    CRCInfo,
    CRCOccurence,
    LECInfo,
    LLEInfo,
    LMCInfo,
    LPLInfo,
    MIMInfo,
    SCLInfo,
    UGEInfo,
    UVAInfo,
)

O = TypeVar("O", bound=BasicOccurence)  # noqa: E741
A = TypeVar("A", bound=BasicAddInfo)


class Smell(BaseModel, Generic[O, A]):
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
        additionalInfo (Any): (Optional) Any custom information for a type of smell
    """

    confidence: str
    message: str
    messageId: str
    module: str
    obj: str | None
    path: str
    symbol: str
    type: str
    occurences: list[O]
    additionalInfo: A | None = None  # type: ignore


CRCSmell = Smell[CRCOccurence, CRCInfo]
SCLSmell = Smell[BasicOccurence, SCLInfo]
LECSmell = Smell[BasicOccurence, LECInfo]
LLESmell = Smell[BasicOccurence, LLEInfo]
LMCSmell = Smell[BasicOccurence, LMCInfo]
LPLSmell = Smell[BasicOccurence, LPLInfo]
UVASmell = Smell[BasicOccurence, UVAInfo]
MIMSmell = Smell[BasicOccurence, MIMInfo]
UGESmell = Smell[BasicOccurence, UGEInfo]
