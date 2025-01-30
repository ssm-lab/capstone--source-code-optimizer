from pydantic import BaseModel


class BasicOccurence(BaseModel):
    line: int
    endLine: int | None
    column: int
    endColumn: int | None


class CRCOccurence(BasicOccurence):
    callString: str


class BasicAddInfo(BaseModel): ...


class CRCInfo(BasicAddInfo):
    repetitions: int


class SCLInfo(BasicAddInfo):
    innerLoopLine: int
    concatTarget: str


LECInfo = BasicAddInfo
LLEInfo = BasicAddInfo
LMCInfo = BasicAddInfo
LPLInfo = BasicAddInfo
UVAInfo = BasicAddInfo
MIMInfo = BasicAddInfo
UGEInfo = BasicAddInfo
