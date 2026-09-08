from pydantic import BaseModel
from typing import List, Optional

class Token(BaseModel):
    tokenId: str
    value: str
    tokenClass: str
    boundingBox: List[float] # [x, y, width, height]
    row: Optional[int] = None
    column: Optional[int] = None
    placeValue: Optional[str] = None
    confidence: float
    alternatives: List[str] = []
    ambiguity: bool = False

class ImageRecognitionResult(BaseModel):
    tokens: List[Token]
    status: str # SUCCESS, OUT_OF_SCOPE, UNCERTAIN_RECOGNITION

class ParsedExercise(BaseModel):
    operationType: str
    operands: List[str]
    result: str
    tokens: List[Token]
    status: str # VALID_STRUCTURE, UNCERTAIN_STRUCTURE, OUT_OF_SCOPE, INVALID_LAYOUT
