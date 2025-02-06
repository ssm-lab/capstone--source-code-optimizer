from pydantic import BaseModel
from typing import Optional

from .custom_fields import CRCInfo, Occurence, AdditionalInfo, SCLInfo


class Smell(BaseModel):
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
        occurences (list[Occurence]): A list of individual occurences of a same smell, contains positional info.
        additionalInfo (AddInfo): (Optional) Any custom information m for a type of smell
    """

    confidence: str
    message: str
    messageId: str
    module: str
    obj: str | None
    path: str
    symbol: str
    type: str
    occurences: list[Occurence]
    additionalInfo: Optional[AdditionalInfo] = None


class CRCSmell(Smell):
    additionalInfo: CRCInfo  # type: ignore


class SCLSmell(Smell):
    additionalInfo: SCLInfo  # type: ignore


LECSmell = Smell
LLESmell = Smell
LMCSmell = Smell
LPLSmell = Smell
UVASmell = Smell
MIMSmell = Smell
UGESmell = Smell
