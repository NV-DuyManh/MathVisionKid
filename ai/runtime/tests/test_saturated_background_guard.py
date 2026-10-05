"""Text evidence guards patterned backgrounds without rejecting clipped writing."""
import cv2
import numpy as np
import pytest

from app.api import generalized_pipeline as pipeline
from app.recognition import text_detector
from app.schemas.ocr import LineBox
from app.tutoring import rows


@pytest.fixture(autouse=True)
def isolated_cache():
    pipeline.clear_detection_cache()
    yield
    pipeline.clear_detection_cache()


def saturated_image(height=300, width=500):
    image = np.full((height, width, 3), (80, 20, 160), np.uint8)
    for y in range(20, height, 35):
        cv2.ellipse(image, (width//2, y), (width//3, 18), 0, 0, 180,
                    (90, 35, 175), 3)
    return image


def test_empty_learned_evidence_rejects_background_before_classical_rows(monkeypatch):
    image = saturated_image()
    calls = []
    monkeypatch.setattr(text_detector, 'detect_crop_regions',
                        lambda pixels: calls.append(pixels.shape) or [])

    def unexpected(*args):
        pytest.fail('A confirmed unsupported background reached classical segmentation')

    monkeypatch.setattr(pipeline, '_run_single_profile', unexpected)
    monkeypatch.setattr(rows, 'handwriting_rows', unexpected)
    lines, diag = pipeline.run_generalized_line_detection(image, request_id='first')
    assert lines == [] and diag['background_rejected']
    assert diag['needs_review'] and not diag['geometry_verified']
    assert diag['requestId'] == 'first' and not diag['cacheHit']
    cached, cached_diag = pipeline.run_generalized_line_detection(image, request_id='second')
    assert cached == [] and cached_diag['cacheHit']
    assert cached_diag['requestId'] == 'second' and len(calls) == 1
    retried, retry_diag = pipeline.run_generalized_line_detection(image, force_redetect=True)
    assert retried == [] and not retry_diag['cacheHit'] and len(calls) == 2


@pytest.mark.parametrize('evidence', [None, [(20, 50, 250, 90)]],
                         ids=['model-unavailable', 'writing-on-colored-paper'])
def test_unavailable_model_or_real_text_preserves_classical_regions(monkeypatch, evidence):
    image = saturated_image()
    monkeypatch.setattr(text_detector, 'detect_crop_regions', lambda pixels: evidence)
    monkeypatch.setattr(pipeline, '_run_single_profile', lambda *args:
                        ([LineBox(line_id='line_1', x=20, y=50, width=230, height=40, order=1)],
                         {}, 95, None, 30))
    monkeypatch.setattr(rows, 'handwriting_rows', lambda *args: [])
    lines, diag = pipeline.run_generalized_line_detection(image)
    assert len(lines) == 1 and 'background_rejected' not in diag
    assert lines[0].x <= 20 and lines[0].x + lines[0].width >= 250


@pytest.mark.parametrize('kind', ['small-writing', 'tight-strip', 'paper', 'exact-threshold'])
def test_clipped_strips_and_paper_do_not_consult_background_rejection(monkeypatch, kind):
    if kind == 'small-writing':
        image = saturated_image(80, 400)
    elif kind == 'tight-strip':
        image = saturated_image(128, 1100)
    elif kind == 'paper':
        image = np.full((300, 500, 3), 240, np.uint8)
    else:
        image = np.full((300, 500, 3), (80, 20, 160), np.uint8)
        image[:, 400:] = 240  # Exactly 80% saturation cannot justify rejection.

    def unexpected(*args):
        pytest.fail('Clipped writing or paper was evaluated as a background')

    monkeypatch.setattr(text_detector, 'detect_crop_regions', unexpected)
    monkeypatch.setattr(pipeline, '_run_single_profile', lambda *args:
                        ([LineBox(line_id='line_1', x=10, y=10, width=60, height=20, order=1)],
                         {}, 95, None, 15))
    monkeypatch.setattr(rows, 'handwriting_rows', lambda *args: [])
    lines, diag = pipeline.run_generalized_line_detection(image)
    assert len(lines) == 1 and 'background_rejected' not in diag
