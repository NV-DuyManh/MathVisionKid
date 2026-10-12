"""Synthetic geometry safeguards; these are not real-photo accuracy metrics."""
import cv2
import numpy as np
import pytest
from app.recognition import text_detector
from app.api import generalized_pipeline as pipeline


def ruled_page():
    image = np.full((700, 500, 3), 235, np.uint8)
    for y in range(35, 690, 35):
        cv2.line(image, (20, y), (480, y), (160, 155, 145), 1)
    for x in range(25, 490, 30):
        cv2.line(image, (x, 20), (x, 680), (160, 155, 145), 1)
    return image


@pytest.mark.parametrize('scale', [1, 3])
@pytest.mark.parametrize('colour', [(40, 40, 160), (160, 40, 30)])
def test_sparse_pen_on_grid_recovers_source_pixels_without_grid_boxes(scale, colour):
    image = ruled_page()
    cv2.putText(image, 't', (125, 186), cv2.FONT_HERSHEY_SIMPLEX, 1.2, colour, 2)
    image = cv2.resize(image, None, fx=scale, fy=scale)
    original = image.copy()
    boxes = text_detector.recover_sparse_ruled_regions(image)
    assert boxes and len(boxes) == 1
    x1, y1, x2, y2 = boxes[0]
    assert x1 <= 127*scale and x2 >= 139*scale
    assert y1 <= 160*scale and y2 >= 186*scale
    assert 0 <= x1 < x2 <= image.shape[1] and 0 <= y1 < y2 <= image.shape[0]
    assert np.array_equal(image, original)


def test_empty_or_nonruled_page_is_not_certified_blank():
    assert text_detector.recover_sparse_ruled_regions(ruled_page()) is None
    plain = np.full((700, 500, 3), 235, np.uint8)
    cv2.putText(plain, 't', (125, 186), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (40, 40, 160), 2)
    assert text_detector.recover_sparse_ruled_regions(plain) is None
    assert text_detector.recover_sparse_ruled_regions(cv2.rotate(plain, cv2.ROTATE_90_CLOCKWISE)) is None


def test_coloured_mark_cannot_replace_visible_neutral_words():
    image = ruled_page()
    cv2.putText(image, 't', (125, 186), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (40, 40, 160), 2)
    cv2.putText(image, 'math', (120, 320), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (40, 40, 40), 2)
    assert text_detector.recover_sparse_ruled_regions(image) is None


def test_sparse_fraction_is_not_split_into_isolated_glyphs():
    image = ruled_page()
    colour = (40, 40, 160)
    cv2.putText(image, '1', (220, 264), cv2.FONT_HERSHEY_SIMPLEX, .9, colour, 2)
    cv2.line(image, (219, 272), (244, 272), colour, 2)
    cv2.putText(image, '3', (220, 298), cv2.FONT_HERSHEY_SIMPLEX, .9, colour, 2)
    assert text_detector.recover_sparse_ruled_regions(image) is None


def test_api_recovers_only_after_empty_learned_pass_and_preserves_cache(monkeypatch):
    image = ruled_page()
    cv2.putText(image, 't', (125, 186), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (40, 40, 160), 2)
    monkeypatch.setattr(text_detector, 'detect_text_regions', lambda bgr: [])
    pipeline.clear_detection_cache()
    boxes, diag = pipeline.run_generalized_line_detection(image, request_id='sparse-grid')
    assert len(boxes) == 1 and diag['selected_profile'] == 'SPARSE_RULED_INK_REGIONS'
    assert diag['needs_review'] and not diag['geometry_verified'] and not diag['cacheHit']
    cached, second = pipeline.run_generalized_line_detection(image, request_id='next')
    assert len(cached) == 1 and second['cacheHit'] and second['requestId'] == 'next'
    monkeypatch.setattr(text_detector, 'detect_text_regions', lambda bgr: [(50, 60, 200, 90)])
    pipeline.clear_detection_cache()
    boxes, diag = pipeline.run_generalized_line_detection(image)
    assert [(b.x, b.y, b.width, b.height) for b in boxes] == [(50, 60, 150, 30)]
    assert diag['selected_profile'] == 'PPOCR_TEXT_REGIONS'


def test_missing_model_does_not_enable_colour_only_replacement(monkeypatch):
    image = ruled_page()
    monkeypatch.setattr(text_detector, 'detect_text_regions', lambda bgr: None)
    def forbidden(_):
        raise AssertionError('Missing optional model must retain the established path')
    monkeypatch.setattr(text_detector, 'recover_sparse_ruled_regions', forbidden)
    pipeline.clear_detection_cache()
    pipeline.run_generalized_line_detection(image)
