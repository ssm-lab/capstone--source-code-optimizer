"""Data models for representing different types of code smells."""

from pydantic import BaseModel
from typing import Optional

from .custom_fields import CRCInfo, Occurence, AdditionalInfo, SCLInfo


class Smell(BaseModel):
    """Base model representing a detected code smell.

    Attributes:
        id: Optional unique identifier
        confidence: Detection confidence level
        message: Description of the smell
        messageId: Unique message identifier
        module: Module where smell was found
        obj: Specific object containing the smell
        path: File path relative to project root
        symbol: Code symbol involved
        type: Smell category/type
        occurences: List of locations where smell appears
        additionalInfo: Optional smell-specific metadata
    """

    id: Optional[str] = ""
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
    """Represents Cache-Related Computation smells with required CRC metadata."""

    additionalInfo: CRCInfo  # type: ignore


class SCLSmell(Smell):
    """Represents String Concatenation in Loops smells with required SCL metadata."""

    additionalInfo: SCLInfo  # type: ignore


# Type aliases for other smell categories
LECSmell = Smell  # Long Element Chain
LLESmell = Smell  # Long List Expansion
LMCSmell = Smell  # Long Method Chain
LPLSmell = Smell  # Long Parameter List
UVASmell = Smell  # Unused Variable Assignment
MIMSmell = Smell  # Multiple Items Mutation
UGESmell = Smell  # Unnecessary Get Element
