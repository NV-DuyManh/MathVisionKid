"""Geometry contracts for cropped, short and tilted notebook photographs."""
import cv2
import numpy as np
import pytest

from app.tutoring.rows import handwriting_rows, _has_stacked_fraction


def notebook(rows, width=1200, height=450):
    image = np.full((height, width, 3), 248, np.uint8)
    for y in range(20, height, 30):
        cv2.line(image, (0, y), (width-1, y), (185, 185, 185), 1)
    for y in rows:
        cv2.putText(image, "62500 + 2500 = 65000 cm", (160, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.25, (145, 45, 25), 3)
    return image


@pytest.mark.parametrize('rows,height', [([95], 150), ([80, 160], 210)])
def test_short_crop_keeps_each_visible_row(rows, height):
    image = notebook(rows, height=height)
    boxes = handwriting_rows(image)
    assert len(boxes) == len(rows)
    for box, baseline in zip(boxes, rows):
        assert box[0] < 170 < box[2]
        assert box[1] < baseline-12 < box[3]
        assert 0 <= box[1] < box[3] <= height


@pytest.mark.parametrize('height', [132, 158, 193])
def test_wide_resized_crop_keeps_bottom_ink_inside_source_image(height):
    image = notebook([60, height], width=2745, height=height)
    boxes = handwriting_rows(image)
    assert len(boxes) == 2
    assert boxes[-1][3] == height
    assert all(0 <= x1 < x2 <= 2745 and 0 <= y1 < y2 <= height
               for x1, y1, x2, y2 in boxes)


@pytest.mark.parametrize('angle', [-5, 5])
def test_tilted_notebook_boxes_map_to_original_pixels(angle):
    image = notebook([95, 180, 265, 350])
    matrix = cv2.getRotationMatrix2D((600, 225), angle, 1)
    tilted = cv2.warpAffine(image, matrix, (1200, 450), borderValue=(248, 248, 248))
    boxes = handwriting_rows(tilted)
    assert len(boxes) == 4
    for box, baseline in zip(boxes, [95, 180, 265, 350]):
        center = matrix @ np.array([450, baseline-12, 1])
        assert box[0] <= center[0] <= box[2]
        assert box[1] <= center[1] <= box[3]
        assert 0 <= box[0] < box[2] <= 1200 and 0 <= box[1] < box[3] <= 450


def test_blank_ruled_page_and_coloured_specks_are_not_rows():
    image = notebook([])
    for x in range(100, 500, 40):
        cv2.circle(image, (x, 100), 2, (145, 45, 25), -1)
    assert handwriting_rows(image) == []


def test_accent_specks_stay_with_their_row():
    image = notebook([120, 240, 360])
    for baseline in [120, 240, 360]:
        for x in range(200, 550, 50):
            cv2.line(image, (x, baseline-40), (x+5, baseline-46), (145, 45, 25), 2)
    boxes = handwriting_rows(image)
    assert len(boxes) == 3
    assert all(a[3] <= b[1] for a, b in zip(boxes, boxes[1:]))


def test_sparse_strong_writing_keeps_rows_across_a_blank_section():
    image = notebook([90, 160, 470, 540], width=900, height=800)
    boxes = handwriting_rows(image)
    assert len(boxes) == 4
    for box, baseline in zip(boxes, [90, 160, 470, 540]):
        assert box[1] < baseline-12 < box[3]
    assert all(a[3] <= b[1] for a, b in zip(boxes, boxes[1:]))


def test_sparse_faint_writing_is_not_promoted_to_trusted_geometry():
    image = notebook([], width=900, height=800)
    for y in [90, 160, 470, 540]:
        cv2.putText(image, '62500 + 2500 = 65000 cm', (160, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.25, (160, 125, 125), 3)
    assert handwriting_rows(image) == []


def test_fraction_bar_has_stacked_digits_but_equals_does_not():
    # Component statistics are [x, y, width, height, ink area].
    fraction = np.array([[0, 0, 100, 100, 0], [30, 10, 18, 25, 180],
                         [28, 39, 23, 3, 60], [30, 46, 18, 25, 180]])
    assert _has_stacked_fraction(fraction, 30)
    equals_sign = np.array([[0, 0, 100, 100, 0], [28, 39, 23, 3, 60],
                            [28, 48, 23, 3, 60], [65, 30, 18, 25, 180]])
    assert not _has_stacked_fraction(equals_sign, 30)


def annotated_equations():
    image = notebook([], width=900, height=600)
    ink = (145, 45, 25)
    for baseline in (180, 300, 420):
        cv2.putText(image, '8x - 20 + 15 = 11', (160, baseline),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.25, ink, 3)
    cv2.ellipse(image, (300, 135), (85, 25), 0, 180, 355, ink, 3)
    cv2.line(image, (384, 133), (377, 122), ink, 3)
    cv2.ellipse(image, (300, 434), (90, 22), 0, 5, 175, ink, 3)
    cv2.line(image, (389, 436), (381, 444), ink, 3)
    return image


@pytest.mark.parametrize('scale', [.5, 1, 2])
def test_curved_annotation_stays_with_equation_without_becoming_an_extra_row(scale):
    image = cv2.resize(annotated_equations(), None, fx=scale, fy=scale)
    boxes = handwriting_rows(image)
    assert len(boxes) == 3
    # The arrow ink is preserved in the first/last equation envelope.
    for box, point in [(boxes[0], (300, 110)), (boxes[-1], (300, 456))]:
        x, y = (value * scale for value in point)
        assert box[0] <= x <= box[2] and box[1] <= y <= box[3]
    assert all(a[3] <= b[1] for a, b in zip(boxes, boxes[1:]))
    assert all(0 <= x1 < x2 <= image.shape[1] and 0 <= y1 < y2 <= image.shape[0]
               for x1, y1, x2, y2 in boxes)


@pytest.mark.parametrize('text', ['la:', 'C', '12'])
def test_short_written_row_survives_annotation_association(text):
    image = annotated_equations()
    cv2.putText(image, text, (160, 535), cv2.FONT_HERSHEY_SIMPLEX,
                1.25, (145, 45, 25), 3)
    boxes = handwriting_rows(image)
    assert len(boxes) == 4
    assert boxes[-1][1] < 520 < boxes[-1][3]


@pytest.mark.parametrize('annotation_y', [120, 240])
def test_ambiguous_or_distant_annotation_is_not_assigned_arbitrarily(annotation_y):
    from app.tutoring.rows import _attach_stroke_annotations

    mask = np.zeros((300, 450), np.uint8)
    for baseline in (105, 175):
        cv2.putText(mask, '12+34=46', (100, baseline),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 2)
    cv2.ellipse(mask, (200, annotation_y), (60, 6), 0, 0, 180, 255, 2)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    keep = np.ones(count, np.uint8)
    keep[0] = 0
    boxes = [(90, 75, 350, 110), (130, annotation_y-2, 270, annotation_y+9),
             (90, 140, 350, 180)]
    original = list(boxes)
    assert _attach_stroke_annotations(boxes, labels, stats, keep, 25, 1) == original
    assert boxes == original


@pytest.mark.parametrize('kind', ['connected_word', 'small_footer'])
def test_zero_isolated_glyphs_does_not_make_a_written_row_an_annotation(kind):
    from app.tutoring.rows import _attach_stroke_annotations

    mask = np.zeros((240, 500), np.uint8)
    cv2.putText(mask, '12+34=46', (90, 95), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 2)
    if kind == 'connected_word':
        # Connected cursive strokes with a descender have no isolated glyph
        # centers. They still form their own writing row below the equation.
        points = np.array([[90, 130], [150, 145], [210, 130], [270, 145],
                           [330, 130], [390, 145], [390, 195]])
        cv2.polylines(mask, [points], False, 255, 3)
        candidate = (80, 120, 405, 200)
    else:
        # Small printing is below the handwriting body's height threshold.
        cv2.putText(mask, 'Just smile!', (90, 122),
                    cv2.FONT_HERSHEY_SIMPLEX, .35, 255, 1)
        candidate = (80, 110, 165, 128)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    keep = np.ones(count, np.uint8)
    keep[0] = 0
    boxes = [(80, 60, 420, 105), candidate]
    assert _attach_stroke_annotations(boxes, labels, stats, keep, 30, 1) == boxes


def test_an_attached_stroke_does_not_pull_a_distant_stroke_into_the_row():
    from app.tutoring.rows import _attach_stroke_annotations

    mask = np.zeros((260, 450), np.uint8)
    cv2.putText(mask, '12+34=46', (90, 95), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 2)
    for y in (105, 135):
        cv2.ellipse(mask, (200, y), (60, 6), 0, 0, 180, 255, 2)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    keep = np.ones(count, np.uint8)
    keep[0] = 0
    boxes = [(80, 65, 420, 100), (130, 103, 270, 114), (130, 133, 270, 144)]
    assert _attach_stroke_annotations(boxes, labels, stats, keep, 30, 1) == [
        (80, 65, 420, 114), (130, 133, 270, 144)]


def test_small_slanted_fractions_remain_separate_from_the_previous_equation():
    from app.tutoring.rows import _attach_stroke_annotations

    mask = np.zeros((240, 500), np.uint8)
    cv2.putText(mask, '12+34=46', (90, 95), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 2)
    for x in (140, 220):
        cv2.putText(mask, '1', (x, 118), cv2.FONT_HERSHEY_SIMPLEX, .4, 255, 2)
        cv2.line(mask, (x-10, 122), (x+40, 131), 255, 2)
        cv2.putText(mask, '2', (x+8, 146), cv2.FONT_HERSHEY_SIMPLEX, .4, 255, 2)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    keep = (stats[:, 4] >= 25).astype(np.uint8)
    keep[0] = 0
    boxes = [(80, 60, 420, 105), (125, 107, 274, 149)]
    assert _attach_stroke_annotations(boxes, labels, stats, keep, 30, 1) == boxes
