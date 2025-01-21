from typing import TypedDict


class BasicOccurence(TypedDict):
    line: int
    endLine: int | None
    column: int
    endColumn: int | None


class BasicAddInfo(TypedDict): ...


class CRCOccurence(BasicOccurence):
    call_string: str


class CRCAddInfo(BasicAddInfo):
    repetitions: int


class SCLAddInfo(BasicAddInfo):
    outerLoopLine: int
