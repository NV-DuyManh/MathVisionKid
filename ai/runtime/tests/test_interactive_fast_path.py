"""Interactive detection defers advisors without skipping segmentation or CRNN."""
import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.config import settings
from app.main import app
from app.ocr.crnn_provider import CrnnOcrProvider
from app.schemas.ocr import LineBox


@pytest.mark.parametrize("line_assist", [False, True])
def test_fast_path_preserves_core_ocr_and_pending_advisors(line_assist):
    image = io.BytesIO()
    Image.new("RGB", (100, 60), "white").save(image, format="PNG")
    provider = MagicMock(spec=CrnnOcrProvider)
    provider.recognize_batch_with_uncertainty.return_value = [
        ("original OCR", {"rawCrnnConfidence": 0.75}),
    ]

    def segmentation(*args, **kwargs):
        return [LineBox(line_id="l1", x=4, y=5, width=90, height=25, order=1)], {
            "strong_band_count": 1, "canonicalMatched": False,
        }

    groq = AsyncMock(return_value=None)
    gemini = AsyncMock(return_value=None)
    line_analyzer = AsyncMock(return_value=None)
    with patch("app.api.ocr.detect_text_lines", side_effect=segmentation) as detector, \
         patch("app.api.ocr.get_ocr_provider", return_value=provider), \
         patch("app.api.ocr.should_use_groq_line_analyzer", return_value=line_assist), \
         patch("app.api.ocr.analyze_with_groq", line_analyzer), \
         patch("app.integrations.groq.corrector.should_request_groq_correction", return_value=(True, "test")), \
         patch("app.integrations.groq.corrector.request_groq_correction", groq), \
         patch("app.integrations.gemini.corrector.request_gemini_correction", gemini), \
         patch.object(settings, "groq_enabled", True), \
         patch.object(settings, "groq_post_correction_enabled", True), \
         patch.object(settings, "gemini_enabled", True), \
         patch.object(settings, "gemini_post_correction_enabled", True), \
         patch.object(settings, "hwtext_always_review_enabled", False), \
         patch.object(settings, "always_review_enabled", False):
        client = TestClient(app)
        headers = {"Content-Type": "image/png", "X-Internal-API-Key": settings.internal_api_key,
                   "X-Force-Redetect": "true"}
        ordinary = client.post("/internal/v1/ocr/detect-lines", content=image.getvalue(), headers=headers)
        assert ordinary.status_code == 200, ordinary.text
        assert groq.await_count == 1
        assert gemini.await_count == 1
        groq.reset_mock()
        gemini.reset_mock()
        fast = client.post("/internal/v1/ocr/detect-lines", content=image.getvalue(),
                           headers={**headers, "X-Fast-Path": "true"})
        assert fast.status_code == 200, fast.text
        groq.assert_not_awaited()
        gemini.assert_not_awaited()
        assert detector.call_count == 2
        assert provider.recognize_batch_with_uncertainty.call_count == 2
        assert line_analyzer.await_count == (2 if line_assist else 0)
        before, after = ordinary.json(), fast.json()
        core = ("x", "y", "width", "height", "order", "rawOcrText", "rawOcrConfidence",
                "rawOcrConfidenceSource", "finalText")
        assert {key: before["lines"][0][key] for key in core} == {
            key: after["lines"][0][key] for key in core}
        line = after["lines"][0]
        assert line["rawOcrText"] == "original OCR"
        assert line["finalText"] == "original OCR"
        assert line["groqStatus"] is None
        assert line["geminiStatus"] is None
        assert line["groqConfidence"] is None
        assert line["geminiConfidence"] is None
        assert line["correctionApplied"] is False
        assert after["diagnostics"]["crnnExecuted"] is True
        assert after["diagnostics"]["groqCalls"] == 0
        assert after["diagnostics"]["geminiCalls"] == 0
