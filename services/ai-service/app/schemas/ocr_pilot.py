from pydantic import BaseModel, Field
from typing import Optional, List

class LineBox(BaseModel):
    line_id: str
    x: int
    y: int
    width: int
    height: int
    order: int
    text: Optional[str] = None
    rawOcrText: Optional[str] = None
    rawOcrConfidence: Optional[float] = None
    correctedText: Optional[str] = None
    correctionConfidence: Optional[float] = None
    correctionApplied: bool = False
    correctionDecision: Optional[str] = None
    finalText: Optional[str] = None
    minTokenConfidence: Optional[float] = None
    p10TokenConfidence: Optional[float] = None
    meanTokenConfidence: Optional[float] = None
    blankRatio: Optional[float] = None
    meanEntropy: Optional[float] = None


class OcrDetectLinesResponse(BaseModel):
    width: int
    height: int
    lines: List[LineBox]
    detector_version: Optional[str] = None
    diagnostics: Optional[dict] = None

class OcrRecognizeLineResponse(BaseModel):
    recognized_text: str
    model_name: str
    model_version: str
    checkpoint_sha256: str
    vocab_sha256: str
    preprocessing_version: str = "v1_resize_64x1024_imagenet"
    confidence: Optional[float] = Field(None, description="Calibrated confidence score if available; otherwise null (no fake 1.0)")
    latency_ms: float
