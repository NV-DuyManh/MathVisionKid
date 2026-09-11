from pydantic import BaseModel, Field
from typing import Optional

class OcrRecognizeLineRequest(BaseModel):
    image_reference: Optional[str] = Field(None, description="minio://bucket/key or fixture:// tag")
    image_base64: Optional[str] = Field(None, description="Base64 encoded image bytes")

class OcrRecognizeLineResponse(BaseModel):
    recognized_text: str
    model_name: str
    model_version: str
    checkpoint_sha256: str
    vocab_sha256: str
    preprocessing_version: str = "v1_resize_64x1024_imagenet"
    latency_ms: float
