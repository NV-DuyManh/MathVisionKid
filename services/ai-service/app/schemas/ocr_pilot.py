from pydantic import BaseModel, Field
from typing import Optional, List

class LineBox(BaseModel):
    line_id: str
    x: int
    y: int
    width: int
    height: int
    order: int

class OcrDetectLinesResponse(BaseModel):
    width: int
    height: int
    lines: List[LineBox]

class OcrRecognizeLineResponse(BaseModel):
    recognized_text: str
    model_name: str
    model_version: str
    checkpoint_sha256: str
    vocab_sha256: str
    preprocessing_version: str = "v1_resize_64x1024_imagenet"
    confidence: Optional[float] = Field(None, description="Calibrated confidence score if available; otherwise null (no fake 1.0)")
    latency_ms: float
