"""Detached marks must remain with their short row without stealing neighbours."""
import cv2
import numpy as np
import pytest

from app.tutoring.rows import _include_detached_marks, short_row_candidates


BACKGROUND = (248, 248, 248)
WEAK_INK = (140, 128, 120)


@pytest.mark.parametrize('scale', [.5, 1, 2])
def test_detached_weak_colon_with_scaling(scale):
    image = np.full((220, 320, 3), BACKGROUND, np.uint8)
    for y in (120, 144):
        cv2.circle(image, (113, y), 4, WEAK_INK, -1)
    image = cv2.resize(image, None, fx=scale, fy=scale)
    box = tuple(round(v*scale) for v in (20, 105, 100, 160))
    out = _include_detached_marks(image, box, [], 55*scale)
    assert out[2] >= round(117*scale)
    assert out[:2] == box[:2] and out[3] == box[3]


@pytest.mark.parametrize('case', ['far', 'neutral', 'large_body', 'other_column', 'above_owner', 'left_rule'])
def test_no_growth_for_unowned_or_unrelated_marks(case):
    image = np.full((220, 320, 3), BACKGROUND, np.uint8)
    others = []
    if case == 'left_rule':
        for y in range(50, 200, 20):
            cv2.circle(image, (9, y), 4, WEAK_INK, -1)
    elif case == 'large_body':
        cv2.putText(image, 'l', (115, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.5, WEAK_INK, 3)
    else:
        x, y = (150, 130) if case == 'far' else (113, 130)
        if case == 'above_owner':
            x, y = 50, 93
            others = [(15, 75, 200, 110)]
        if case == 'other_column':
            others = [(105, 115, 180, 145)]
        cv2.circle(image, (x, y), 4, (90, 90, 90) if case == 'neutral' else WEAK_INK, -1)
    box = (20, 105, 100, 160)
    assert _include_detached_marks(image, box, others, 55) == box


def test_owned_detached_accent_kept():
    image = np.full((220, 320, 3), BACKGROUND, np.uint8)
    cv2.circle(image, (50, 100), 4, WEAK_INK, -1)
    box = (20, 105, 100, 160)
    out = _include_detached_marks(image, box, [(15, 30, 200, 70)], 55)
    assert out[1] <= 96 and out[0] == box[0] and out[2:] == box[2:]


def test_growth_bounded_at_bottom_right():
    image = np.full((180, 120, 3), BACKGROUND, np.uint8)
    cv2.circle(image, (118, 174), 4, WEAK_INK, -1)
    box = (20, 110, 106, 180)
    out = _include_detached_marks(image, box, [], 70)
    assert 0 <= out[0] < out[2] <= 120 and 0 <= out[1] < out[3] <= 180
    assert out[2] == 120


def test_weaker_marks_cannot_make_a_row_eligible_without_strong_bodies():
    image = np.full((220, 320, 3), BACKGROUND, np.uint8)
    cv2.putText(image, 'la', (25, 145), cv2.FONT_HERSHEY_SIMPLEX, 1.5, WEAK_INK, 3)
    for y in (120, 144):
        cv2.circle(image, (113, y), 4, WEAK_INK, -1)
    existing = [(15, 30, 300, 70), (150, 190, 300, 220)]
    assert short_row_candidates(image, existing, [*existing, (20, 105, 100, 160)]) == []
