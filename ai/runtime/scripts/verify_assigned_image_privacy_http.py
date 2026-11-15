"""Exercise the internal HTTP contract with real models and synthetic images."""

import io
import os
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont

from assigned_image_privacy import app

FONT_PATH = os.environ.get(
    "ASSIGNED_PRIVACY_TEST_FONT", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
)


def png(text):
    image = Image.new("RGB", (900, 150), "white")
    font = ImageFont.truetype(FONT_PATH, 36)
    ImageDraw.Draw(image).text((25, 40), text, font=font, fill="black")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def worksheet_with_header(header):
    image = Image.new("RGB", (1200, 800), "white")
    draw = ImageDraw.Draw(image)
    draw.text((65, 60), header, font=ImageFont.truetype(FONT_PATH, 12), fill="black")
    draw.text((65, 390), "12 + 34 = 46", font=ImageFont.truetype(FONT_PATH, 36), fill="black")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def main():
    client = TestClient(app)
    path = "/internal/v1/assigned-image-privacy"
    headers = {"Content-Type": "image/png", "X-API-Key": os.environ["ASSIGNED_PRIVACY_KEY"]}
    arithmetic = png("12 + 34 = 46")
    assert client.post(path, content=arithmetic, headers={"Content-Type": "image/png"}).status_code == 403
    assert client.post(path, content=b"invalid", headers=headers).status_code == 415
    oversized = io.BytesIO()
    Image.new("RGB", (4096, 4096), "white").save(oversized, format="PNG")
    with patch("cv2.imdecode", side_effect=AssertionError("oversized image reached full decode")):
        assert client.post(path, content=oversized.getvalue(), headers=headers).status_code == 413
    model_dir = os.environ.pop("ASSIGNED_PRIVACY_MODEL_DIR")
    try:
        assert client.post(path, content=arithmetic, headers=headers).status_code == 503
    finally:
        os.environ["ASSIGNED_PRIVACY_MODEL_DIR"] = model_dir

    with TestClient(app) as started:
        ready = started.post(path, content=arithmetic, headers=headers)
        assert ready.json() == {"decision": "CLEAR"}, ready.status_code
    print("startup-warmup CLEAR", flush=True)

    for label, image, expected in [
        ("arithmetic", arithmetic, "CLEAR"),
        ("vertical-addition", png("  1234\n+ 2345\n  3579"), "CLEAR"),
        ("vertical-subtraction", png("  3210\n- 1111\n  2099"), "CLEAR"),
        ("arithmetic-with-unit", png("12 cm + 34 cm = 46 cm"), "CLEAR"),
        ("answer-label", png("Đáp số: 46 cm"), "CLEAR"),
        ("answer-label-with-name", png("Đáp số: 46 cm Nguyễn Văn Mẫu"), "BLOCKED"),
        ("answer-counting-objects", png("Đáp số: 46 quả táo"), "CLEAR"),
        ("answer-counting-objects-with-name", png("Đáp số: 46 quả táo Nguyễn Văn Mẫu"), "BLOCKED"),
        ("counting-word-problem", png("Có 12 quả táo. Thêm 34 quả. Đáp số: 46 quả."), "CLEAR"),
        ("counting-word-problem-with-name", png("Có 12 quả táo. Nguyễn Văn Mẫu"), "BLOCKED"),
        ("counting-word-problem-with-phone", png("Có 12 quả táo. 0900 000 000"), "BLOCKED"),
        ("unit-followed-by-name", png("46 cm Nguyễn Văn Mẫu"), "BLOCKED"),
        ("email", png("Email: test@example.invalid"), "BLOCKED"),
        ("name", png("Họ và tên: Nguyễn Văn Mẫu"), "BLOCKED"),
        ("phone", png("0900 000 000"), "BLOCKED"),
        ("small-name-above-arithmetic", worksheet_with_header("Họ và tên: Nguyễn Văn Mẫu"), "BLOCKED"),
        ("small-email-above-arithmetic", worksheet_with_header("test@example.invalid"), "BLOCKED"),
        ("split-phone", worksheet_with_header("0900\n000\n000"), "UNCERTAIN"),
        ("blank", png(""), "UNCERTAIN"),
    ]:
        response = client.post(path, content=image, headers=headers)
        assert response.status_code == 200, (label, response.status_code)
        assert response.json() == {"decision": expected}, (label, response.json())
        print(label, expected, flush=True)

    face_fixture = os.environ.get("ASSIGNED_PRIVACY_FACE_FIXTURE")
    if face_fixture:
        # A verdict from OCR would not establish that the face detector fired.
        with patch("assigned_image_privacy.review_text", return_value="CLEAR") as text_review:
            response = client.post(path, content=Path(face_fixture).read_bytes(), headers=headers)
            assert response.status_code == 200, response.status_code
            assert response.json() == {"decision": "BLOCKED"}, response.json()
            text_review.assert_not_called()
        print("adult-face BLOCKED before text review", flush=True)


if __name__ == "__main__":
    main()
