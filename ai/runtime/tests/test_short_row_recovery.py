"""Short handwriting rows need model evidence and independent letter bodies."""
import cv2
import numpy as np
import pytest

from app.tutoring.rows import short_row_candidates


INK = (145, 45, 25)


@pytest.mark.parametrize('end,baseline', [(120, 145), (135, 160)])
def test_short_two_letter_row_recovers_without_trimming_the_slanted_row(end, baseline):
    image = np.full((300, 500, 3), 248, np.uint8)
    cv2.putText(image, 'la', (25, baseline), cv2.FONT_HERSHEY_SIMPLEX, 1.5, INK, 3)
    existing = [(20, 40, 450, end), (150, 205, 450, 260)]
    original = list(existing)
    short = (20, baseline-40, 100, baseline+15)
    regions = [existing[0], short, short, existing[1]]
    assert short_row_candidates(image, existing, regions) == [short]
    assert existing == original
    assert short_row_candidates(image, [], regions) == []


@pytest.mark.parametrize('content', ['single_letter', 'specks', 'neutral_ink'])
def test_model_candidate_without_two_strong_letter_bodies_is_rejected(content):
    image = np.full((300, 500, 3), 248, np.uint8)
    if content == 'specks':
        for x in (30, 60):
            cv2.circle(image, (x, 130), 2, INK, -1)
    else:
        cv2.putText(image, 'l' if content == 'single_letter' else 'la', (25, 145),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5,
                    INK if content == 'single_letter' else (80, 80, 80), 3)
    existing = [(20, 40, 450, 120), (150, 205, 450, 260)]
    assert short_row_candidates(image, existing,
                                [existing[0], (20, 105, 100, 160), existing[1]]) == []


def test_numerator_and_denominator_never_become_supplemental_rows():
    image = np.full((300, 500, 3), 248, np.uint8)
    cv2.putText(image, '12', (30, 115), cv2.FONT_HERSHEY_SIMPLEX, 1, INK, 2)
    cv2.line(image, (28, 130), (76, 130), INK, 2)
    cv2.putText(image, '34', (30, 170), cv2.FONT_HERSHEY_SIMPLEX, 1, INK, 2)
    existing = [(150, 40, 450, 75), (150, 215, 450, 250)]
    fragments = [(25, 85, 85, 120), (25, 145, 85, 180)]
    regions = [existing[0], *fragments, existing[1]]
    assert short_row_candidates(image, existing, regions) == []
    whole_expression = (20, 70, 100, 185)
    assert short_row_candidates(image, [whole_expression, *existing], regions) == []


def test_pipeline_limits_supplements_and_marks_recovered_geometry_for_review(monkeypatch):
    from app.api import generalized_pipeline as pipeline
    from app.recognition import text_detector
    from app.tutoring import rows

    image = np.full((300, 500, 3), 248, np.uint8)
    cv2.putText(image, 'la', (25, 145), cv2.FONT_HERSHEY_SIMPLEX, 1.5, INK, 3)
    physical = [(20, 40, 450, 120), (150, 205, 450, 260)]
    short = (20, 105, 100, 160)
    monkeypatch.setattr(pipeline, '_run_single_profile',
                        lambda *args: ([], {}, 95, None, 30))
    monkeypatch.setattr(rows, 'handwriting_rows', lambda *args: physical)
    calls = []

    def regions(pixels):
        calls.append(True)
        return [physical[0], short, physical[1]]

    monkeypatch.setattr(text_detector, 'detect_text_regions', regions)
    pipeline.clear_detection_cache()
    lines, diag = pipeline.run_generalized_line_detection(image, max_lines=3)
    assert len(lines) == 3 and diag['short_rows_recovered'] == 1
    assert diag['needs_review'] and not diag['geometry_verified']
    for x1, y1, x2, y2 in [*physical, short]:
        assert any(line.x <= x1 and line.y <= y1
                   and line.x+line.width >= x2 and line.y+line.height >= y2
                   for line in lines)
    limited, limited_diag = pipeline.run_generalized_line_detection(image, max_lines=2)
    assert len(limited) == 2 and 'short_rows_recovered' not in limited_diag
    assert len(calls) == 1
    monkeypatch.setattr(rows, 'handwriting_rows', lambda *args: [])
    monkeypatch.setattr(pipeline, '_run_single_profile',
                        lambda *args: ([limited[0]], {}, 95, None, 30))
    pipeline.clear_detection_cache()
    pipeline.run_generalized_line_detection(image)
    assert len(calls) == 1
