from typing import Optional
from pydantic import BaseModel


class Occurence(BaseModel):
    line: int
    endLine: int | None
    column: int
    endColumn: int | None


class AdditionalInfo(BaseModel):
    innerLoopLine: Optional[int] = None
    concatTarget: Optional[str] = None
    repetitions: Optional[int] = None
    callString: Optional[str] = None


class CRCInfo(AdditionalInfo):
    callString: str  # type: ignore
    repetitions: int  # type: ignore


class SCLInfo(AdditionalInfo):
    innerLoopLine: int  # type: ignore
    concatTarget: str  # type: ignore
