"""Conservative physical recovery for cropped rows the local model misses."""
import cv2
import numpy as np
import pytest

from app.tutoring.rows import coloured_strip_regions


INK = (160, 55, 25)


def writing_strip():
    image = np.full((34, 420, 3), 245, np.uint8)
    cv2.putText(image, '123 + 456 = 579', (25, 27),
                cv2.FONT_HERSHEY_SIMPLEX, .85, INK, 2)
    return image


@pytest.mark.parametrize('slope', [0, .04, -.04])
def test_arithmetic_and_sloped_rows_keep_their_visible_ink(slope):
    image = writing_strip()
    if slope:
        matrix = np.float32([[1, 0, 0], [slope, 1, -slope*image.shape[1]/2]])
        image = cv2.warpAffine(image, matrix, (image.shape[1], image.shape[0]),
                               borderValue=(245, 245, 245))
    regions = coloured_strip_regions(image)
    assert len(regions) == 1
    x1, y1, x2, y2 = regions[0]
    assert 0 <= x1 < x2 <= image.shape[1] and 0 <= y1 < y2 <= image.shape[0]
    ink = cv2.inRange(image, np.array(INK), np.array(INK))
    ys, xs = np.nonzero(ink)
    assert x1 <= xs.min() and x2 > xs.max() and y1 <= ys.min() and y2 > ys.max()


def test_parenthesized_fractions_keep_small_numerators_and_denominators():
    image = np.full((58, 673, 3), 245, np.uint8)
    for start in (100, 250):
        for x, begin, end in ((start, 90, 270), (start+106, -90, 90)):
            cv2.ellipse(image, (x, 29), (10, 25), 0, begin, end, INK, 2)
        cv2.putText(image, '4 + 5', (start+12, 20), cv2.FONT_HERSHEY_SIMPLEX, .6, INK, 1)
        cv2.line(image, (start+12, 29), (start+90, 29), INK, 1)
        cv2.putText(image, '9 + 9', (start+12, 52), cv2.FONT_HERSHEY_SIMPLEX, .6, INK, 1)
    regions = coloured_strip_regions(image)
    assert len(regions) == 1
    x1, y1, x2, y2 = regions[0]
    ys, xs = np.nonzero(cv2.inRange(image, np.array(INK), np.array(INK)))
    assert x1 <= xs.min() and x2 > xs.max() and y1 <= ys.min() and y2 > ys.max()


@pytest.mark.parametrize('kind', ['blank', 'weak_colour', 'specks', 'grid', 'solid_pattern', 'scattered'])
def test_backgrounds_and_insufficient_evidence_stay_empty(kind):
    image = np.full((44, 420, 3), 245, np.uint8)
    if kind == 'weak_colour':
        cv2.putText(image, '123 + 456', (25, 32), cv2.FONT_HERSHEY_SIMPLEX, .85, (140, 128, 120), 2)
    elif kind == 'specks':
        for x in range(40, 390, 25):
            cv2.circle(image, (x, 25), 2, INK, -1)
    elif kind == 'grid':
        for x in range(20, 420, 20):
            cv2.line(image, (x, 0), (x, 43), INK, 2)
        for y in (10, 30):
            cv2.line(image, (0, y), (419, y), INK, 2)
    elif kind == 'solid_pattern':
        for x in range(60, 390, 55):
            cv2.circle(image, (x, 22), 15, INK, -1)
    elif kind == 'scattered':
        cv2.putText(image, '1', (25, 32), cv2.FONT_HERSHEY_SIMPLEX, .9, INK, 2)
        cv2.putText(image, '2', (205, 32), cv2.FONT_HERSHEY_SIMPLEX, .9, INK, 2)
        cv2.putText(image, '3', (390, 32), cv2.FONT_HERSHEY_SIMPLEX, .9, INK, 2)
    assert coloured_strip_regions(image) == []


@pytest.mark.parametrize('shape', [(7, 420), (129, 700), (100, 300)])
def test_only_narrow_supported_strip_dimensions_are_eligible(shape):
    image = np.full((*shape, 3), 245, np.uint8)
    assert coloured_strip_regions(image) == []


def test_nonempty_model_result_and_unavailable_model_remain_authoritative(monkeypatch):
    from app.recognition import text_detector
    image = writing_strip()
    monkeypatch.setattr(text_detector, 'detect_text_regions', lambda pixels: [(40, 22, 330, 53)])
    assert text_detector.detect_crop_regions(image) == [(24, 6, 314, 34)]
    monkeypatch.setattr(text_detector, 'detect_text_regions', lambda pixels: None)
    assert text_detector.detect_crop_regions(image) is None
    monkeypatch.setattr(text_detector, 'detect_text_regions', lambda pixels: [])
    assert text_detector.detect_crop_regions(image) == coloured_strip_regions(image)
