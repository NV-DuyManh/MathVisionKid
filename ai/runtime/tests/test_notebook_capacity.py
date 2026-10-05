import asyncio
import io
from unittest.mock import AsyncMock

import cv2
import numpy as np
import pytest
from PIL import Image

from app.tutoring import notebook
from app.tutoring.rows import handwriting_rows


def page(rows=0, ink=(140, 40, 20)):
    pixels = np.full((max(500, rows * 42 + 60), 650, 3), 245, np.uint8)
    for index in range(rows):
        cv2.putText(pixels, "49 : 7 x 2 = 14 con", (70, 40 + index * 42),
                    cv2.FONT_HERSHEY_SIMPLEX, .8, ink, 2)
    stream = io.BytesIO()
    Image.fromarray(cv2.cvtColor(pixels, cv2.COLOR_BGR2RGB)).save(stream, "PNG")
    return pixels, stream.getvalue()


def test_physical_overflow_requests_crop_before_cloud(monkeypatch):
    pixels, content = page(37)
    assert handwriting_rows(pixels) == []
    assert len(handwriting_rows(pixels, max_lines=200)) == 37
    cloud = AsyncMock()
    monkeypatch.setattr(notebook, "_generate", cloud)
    result = asyncio.run(notebook.inspect_notebook(content))
    assert result.needsCrop and result.kind == "UNREADABLE"
    assert result.lines == [] and result.problemText == ""
    cloud.assert_not_called()


@pytest.mark.parametrize("lines", [
    [{"text": "49 : 7 = 7"}] * 36,
    [{"text": "a" * 500}] * 13,
])
def test_model_overflow_does_not_return_partial_work(monkeypatch, lines):
    monkeypatch.setattr(notebook, "_generate", AsyncMock(return_value={
        "kind": "WORK", "problemText": "", "lines": lines}))
    result = asyncio.run(notebook.inspect_notebook(page()[1]))
    assert result.needsCrop and not result.lines and not result.problemText


def test_model_crop_signal_cannot_expose_incomplete_transcript(monkeypatch):
    monkeypatch.setattr(notebook, "_generate", AsyncMock(return_value={
        "kind": "WORK", "needsCrop": True, "lines": [{"text": "first row"}]}))
    result = asyncio.run(notebook.inspect_notebook(page()[1]))
    assert result.needsCrop and result.kind == "UNREADABLE" and result.lines == []


def test_exact_capacity_keeps_last_row_and_grounding(monkeypatch):
    _, content = page(35)
    cloud = AsyncMock(return_value={"kind": "WORK", "lines": [
        {"text": f"49 : 7 = 7 ({index})"} for index in range(35)]})
    monkeypatch.setattr(notebook, "_generate", cloud)
    result = asyncio.run(notebook.inspect_notebook(content))
    assert not result.needsCrop and len(result.lines) == 35
    assert result.lines[-1].text.endswith("(34)")
    assert all(line.box is not None for line in result.lines)
    assert cloud.await_count == 1


def test_learned_black_ink_overflow_discards_partial_read_before_verification(monkeypatch):
    pixels, content = page(37, ink=(0, 0, 0))
    assert handwriting_rows(pixels, max_lines=200) == []
    regions = [(60, 20 + index * 42, 570, 45 + index * 42) for index in range(37)]
    monkeypatch.setattr("app.recognition.text_detector.detect_text_regions", lambda _: regions)
    cloud = AsyncMock(return_value={"kind": "WORK", "lines": [
        {"text": f"49 : 7 = 7 ({index})"} for index in range(35)]})
    monkeypatch.setattr(notebook, "_generate", cloud)
    result = asyncio.run(notebook.inspect_notebook(content))
    assert result.needsCrop and result.kind == "UNREADABLE"
    assert result.lines == [] and result.problemText == ""
    assert cloud.await_count == 1


@pytest.mark.parametrize("reviewed", [
    {"kind": "UNREADABLE", "needsCrop": True, "lines": []},
    {"kind": "WORK", "lines": [{"text": "49 : 7 = 7"}] * 36},
    {"kind": "WORK", "lines": [{"text": "a" * 500}] * 12},
], ids=["crop_signal", "too_many_rows", "too_much_text"])
def test_independent_overflow_cannot_preserve_partial_first_read(monkeypatch, reviewed):
    pixels, content = page(3)
    assert len(handwriting_rows(pixels)) == 3
    monkeypatch.setattr("app.recognition.text_detector.detect_text_regions", lambda _: [])
    cloud = AsyncMock(side_effect=[{"kind": "WORK", "lines": [
        {"text": "49 : 7 = 7"}, {"text": "7 x 2 = 14"}]}, reviewed])
    monkeypatch.setattr(notebook, "_generate", cloud)
    result = asyncio.run(notebook.inspect_notebook(content))
    assert result.needsCrop and result.kind == "UNREADABLE"
    assert result.lines == [] and result.problemText == ""
    assert cloud.await_count == 2
