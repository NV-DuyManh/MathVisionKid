from pydantic import BaseModel, Field
from typing import Optional, List

class LineBox(BaseModel):
    line_id: str
    x: int
    y: int
    width: int
    height: int
    order: int
    # Text Semantics Contract:
    # - rawOcrText: Immutable raw CRNN prediction / raw OCR output. Never overwritten.
    # - finalText: Current effective text (CRNN raw, auto-applied correction, or user choice).
    # - text: Effective text alias mirroring finalText.
    # - predictedText: Legacy effective-text alias mirroring finalText for backwards compatibility.
    text: Optional[str] = None
    rawOcrText: Optional[str] = None
    predictedText: Optional[str] = None
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

    # Groq Advisor 1 explicit fields (mirrored from correctedText for clarity)
    groqSuggestion: Optional[str] = None
    groqConfidence: Optional[float] = None
    groqDecision: Optional[str] = None
    groqStatus: Optional[str] = None
    groqModel: Optional[str] = None

    # Gemini Advisor 2 explicit fields
    geminiSuggestion: Optional[str] = None
    geminiConfidence: Optional[float] = None
    geminiDecision: Optional[str] = None
    geminiStatus: Optional[str] = None
    geminiModel: Optional[str] = None

    # Unified suggestions list
    suggestions: List[dict] = Field(default_factory=list)


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
