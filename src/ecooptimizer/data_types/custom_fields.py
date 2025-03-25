"""Data models for code smell occurrences and additional metadata."""

from typing import Optional
from pydantic import BaseModel


class Occurence(BaseModel):
    """Tracks the location of a code smell in source files.

    Attributes:
        line: Starting line number
        endLine: Ending line number (optional)
        column: Starting column number
        endColumn: Ending column number (optional)
    """

    line: int
    endLine: int | None
    column: int
    endColumn: int | None


class AdditionalInfo(BaseModel):
    """Base model for storing optional metadata about code smells.

    Attributes:
        innerLoopLine: Line number of inner loop (if applicable)
        concatTarget: Target of string concatenation (if applicable)
        repetitions: Number of repetitions (if applicable)
        callString: Function call string (if applicable)
    """

    innerLoopLine: Optional[int] = None
    concatTarget: Optional[str] = None
    repetitions: Optional[int] = None
    callString: Optional[str] = None


class CRCInfo(AdditionalInfo):
    """Extended metadata for Cache-Related Computations (CRC) smells.

    Attributes:
        callString: Required function call string
        repetitions: Required number of repetitions
    """

    callString: str  # type: ignore
    repetitions: int  # type: ignore


class SCLInfo(AdditionalInfo):
    """Extended metadata for String Concatenation in Loops (SCL) smells.

    Attributes:
        innerLoopLine: Required inner loop line number
        concatTarget: Required concatenation target string
    """

    innerLoopLine: int  # type: ignore
    concatTarget: str  # type: ignore
