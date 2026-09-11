import io
import base64
import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

EXPECTED_CHECKPOINT_SHA256 = "a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941"
EXPECTED_VOCAB_SHA256 = "6af4062e92e22cc91ece5198638e29a6ceec6cb92e3b12bd71deb4b874ac9e0d"

def _create_test_line_image() -> bytes:
    """Create a synthetic single-line image for smoke testing."""
    img = Image.new("RGB", (300, 60), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((10, 20), "123", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def test_ocr_pilot_recognize_line_raw_bytes_success():
    img_bytes = _create_test_line_image()
    response = client.post(
        "/internal/v1/ocr/recognize-line",
        content=img_bytes,
        headers={"Content-Type": "image/jpeg"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "recognized_text" in data
    assert isinstance(data["recognized_text"], str)
    assert data["checkpoint_sha256"] == EXPECTED_CHECKPOINT_SHA256
    assert data["vocab_sha256"] == EXPECTED_VOCAB_SHA256
    assert data["model_name"] == "Vietnamese-Handwriting-OCR-Full"
    assert data["latency_ms"] >= 0
    assert data["preprocessing_version"] == "v1_resize_64x1024_imagenet"

def test_ocr_pilot_recognize_line_base64_json_success():
    img_bytes = _create_test_line_image()
    b64_str = base64.b64encode(img_bytes).decode("utf-8")
    response = client.post(
        "/internal/v1/ocr/recognize-line",
        json={"image_base64": b64_str},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "recognized_text" in data
    assert isinstance(data["recognized_text"], str)
    assert data["checkpoint_sha256"] == EXPECTED_CHECKPOINT_SHA256

def test_ocr_pilot_empty_image_rejected():
    response = client.post(
        "/internal/v1/ocr/recognize-line",
        content=b"",
        headers={"Content-Type": "image/jpeg"},
    )
    assert response.status_code == 400

def test_ocr_pilot_invalid_json_rejected():
    response = client.post(
        "/internal/v1/ocr/recognize-line",
        json={"foo": "bar"},
    )
    assert response.status_code == 400
