"""Synthetic region geometry controls, not model-accuracy measurements."""
import itertools

import cv2
import numpy as np
import pytest

from app.recognition import text_detector


@pytest.mark.parametrize('scale', [1, 3])
@pytest.mark.parametrize('mark', [(80, 118, 94, 121), (80, 113, 94, 127)])
def test_compact_leading_math_mark_stays_in_the_numeral_row(scale, mark):
    boxes = [tuple(value * scale for value in box)
             for box in [mark, (100, 100, 130, 140)]]
    expected = [tuple(value * scale for value in (80, 100, 130, 140))]
    for order in itertools.permutations(boxes):
        assert text_detector.merge_fragments(order) == expected


@pytest.mark.parametrize('mark', [
    (80, 70, 94, 73),       # Another baseline.
    (80, 145, 94, 148),     # Underline / fraction tier.
    (20, 118, 34, 121),     # A distant column.
    (15, 118, 94, 121),     # A long ruling / fraction bar.
    (80, 100, 90, 190),     # Vertical arithmetic beside the numeral.
])
def test_compact_mark_rule_cannot_join_unrelated_geometry(mark):
    boxes = [mark, (100, 100, 130, 140)]
    assert len(text_detector.merge_fragments(boxes)) == 2


@pytest.mark.parametrize('scale', [1, 3])
def test_photo_pipeline_keeps_minus_and_numeral_in_one_source_crop(monkeypatch, scale):
    from app.api import generalized_pipeline as pipeline

    image = np.full((300, 200, 3), 245, np.uint8)
    cv2.line(image, (81, 119), (92, 119), (30, 30, 30), 2)
    cv2.putText(image, '7', (100, 138), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (30, 30, 30), 2)
    image = cv2.resize(image, None, fx=scale, fy=scale)
    original = image.copy()
    # Isolate learned detector variability; exercise actual merging, source
    # coordinate mapping, production line output and cache with known regions.
    boxes = [tuple(value * scale for value in box)
             for box in [(80, 118, 94, 121), (100, 100, 130, 140)]]
    monkeypatch.setattr(text_detector, '_infer_regions', lambda pixels: boxes)
    pipeline.clear_detection_cache()
    lines, diagnostics = pipeline.run_generalized_line_detection(image)
    assert [(line.x, line.y, line.width, line.height) for line in lines] == [
        tuple(value * scale for value in (80, 100, 50, 40))]
    assert diagnostics['selected_profile'] == 'PPOCR_TEXT_REGIONS'
    assert diagnostics['needs_review'] and not diagnostics['geometry_verified']
    cached, second = pipeline.run_generalized_line_detection(image)
    assert cached == lines and second['cacheHit']
    assert np.array_equal(image, original)
