"""HTTP line-limit contract with real image decoding and local pipeline routing."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import cv2
import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import ocr, generalized_pipeline
from app.config import settings
from app.recognition import text_detector
from app.schemas.ocr import LineBox


def _page(count):
    image = np.full((count * 18 + 20, 300, 3), 255, dtype=np.uint8)
    regions = []
    for index in range(count):
        y = 5 + index * 18
        cv2.putText(image, f"Row {index + 1}", (20, y + 10), cv2.FONT_HERSHEY_SIMPLEX,
                    .35, (20, 20, 20), 1)
        regions.append([20, y, 280, y + 12])
    return cv2.imencode(".png", image)[1].tobytes(), regions


@pytest.fixture
def local_route(monkeypatch):
    monkeypatch.setattr(settings, "groq_enabled", False)
    monkeypatch.setattr(settings, "gemini_enabled", False)
    monkeypatch.setattr(settings, "canonical_runtime_override_enabled", False)
    provider = Mock(spec=ocr.CrnnOcrProvider)
    provider.recognize_batch_with_uncertainty.side_effect = lambda crops, batch_size: [
        (f"raw row {index + 1}", {"rawCrnnConfidence": .8}) for index in range(len(crops))]
    monkeypatch.setattr(ocr, "get_ocr_provider", lambda _: provider)
    generalized_pipeline.clear_detection_cache()
    app = FastAPI()
    app.include_router(ocr.router, prefix="/internal/v1/ocr")
    yield TestClient(app), provider
    generalized_pipeline.clear_detection_cache()


@pytest.mark.parametrize("count", [41, 200, 201, 250])
def test_detect_route_preserves_rows_and_reports_overflow(local_route, monkeypatch, count):
    client, provider = local_route
    payload, regions = _page(count)
    monkeypatch.setattr(text_detector, "detect_text_regions", lambda _: regions)
    response = client.post("/internal/v1/ocr/detect-lines", content=payload, headers={
        "X-Internal-API-Key": settings.internal_api_key,
        "Content-Type": "image/png", "X-Fast-Path": "true", "X-Force-Redetect": "true"})
    assert response.status_code == 200, response.text
    data = response.json()
    expected = min(count, 200)
    assert len(data["lines"]) == expected
    assert [row["line_id"] for row in data["lines"]] == [f"line_{i + 1}" for i in range(expected)]
    assert [row["rawOcrText"] for row in data["lines"]] == [f"raw row {i + 1}" for i in range(expected)]
    assert [[row["x"], row["y"], row["x"] + row["width"], row["y"] + row["height"]]
            for row in data["lines"]] == regions[:expected]
    crops = provider.recognize_batch_with_uncertainty.call_args.args[0]
    assert len(crops) == expected
    assert provider.recognize_batch_with_uncertainty.call_args.kwargs["batch_size"] == 8
    diagnostics = data["diagnostics"]
    assert diagnostics["line_limit"] == 200
    assert diagnostics["final_box_count"] == expected
    assert diagnostics["returned_line_count"] == expected
    assert diagnostics["region_limit_exceeded"] is (count > 200)
    assert diagnostics["lines_truncated"] is (count > 200)
    if count > 200:
        assert diagnostics["detected_line_count_at_least"] >= count
        assert diagnostics["needs_review"] is True
        assert diagnostics["geometry_verified"] is False
    assert diagnostics["groqCalls"] == diagnostics["geminiCalls"] == 0


def test_detect_route_cap_applies_after_line_assist(local_route, monkeypatch):
    client, provider = local_route
    payload, regions = _page(201)
    monkeypatch.setattr(text_detector, "detect_text_regions", lambda _: regions[:41])
    monkeypatch.setattr(settings, "groq_enabled", True)
    monkeypatch.setattr(ocr, "should_use_groq_line_analyzer", lambda *args: True)
    monkeypatch.setattr(ocr, "analyze_with_groq", AsyncMock(return_value=SimpleNamespace(overall_confidence=.95)))
    assisted = [LineBox(line_id=f"assist_{i}", x=x1, y=y1, width=x2 - x1,
                        height=y2 - y1, order=i + 1) for i, (x1, y1, x2, y2) in enumerate(regions)]
    monkeypatch.setattr(ocr, "reconcile_groq_lines", lambda *args, **kwargs: assisted)
    response = client.post("/internal/v1/ocr/detect-lines", content=payload, headers={
        "X-Internal-API-Key": settings.internal_api_key, "Content-Type": "image/png", "X-Fast-Path": "true"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data["lines"]) == 200
    assert data["diagnostics"]["region_limit_exceeded"] is True
    assert data["diagnostics"]["lines_truncated"] is True
    assert data["diagnostics"]["needs_review"] is True
    assert len(provider.recognize_batch_with_uncertainty.call_args.args[0]) == 200


def test_detect_route_keeps_internal_authentication(local_route):
    client, provider = local_route
    payload, _ = _page(41)
    response = client.post("/internal/v1/ocr/detect-lines", content=payload,
                           headers={"Content-Type": "image/png"})
    assert response.status_code == 401
    provider.recognize_batch_with_uncertainty.assert_not_called()
