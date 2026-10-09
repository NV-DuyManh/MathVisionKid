"""Positional rereading preserves source pixels and never substitutes symbols."""
import asyncio
import base64
import io
from unittest.mock import AsyncMock

import cv2
import numpy as np
import pytest
from PIL import Image

from app.tutoring import notebook
from app.tutoring.math_layout import row_panels


def photo(pixels):
    stream = io.BytesIO()
    Image.fromarray(cv2.cvtColor(pixels, cv2.COLOR_BGR2RGB)).save(stream, 'PNG')
    return stream.getvalue()


def grouped(reading):
    return {**{key: value for key, value in reading.items() if key != 'lines'},
            'bands': [{'candidateId': i, 'lines': [line]} for i, line in enumerate(reading['lines'], 1)]}


def test_panel_sheet_preserves_scaled_full_source_and_does_not_change_pixels():
    pixels = np.full((800, 2400, 3), 245, np.uint8)
    cv2.putText(pixels, '0012 : 04 = 03', (80, 250), cv2.FONT_HERSHEY_SIMPLEX, 4, (140, 40, 20), 6)
    cv2.putText(pixels, 'bottom row', (80, 720), cv2.FONT_HERSHEY_SIMPLEX, 4, (140, 40, 20), 6)
    original = pixels.copy()
    sheet = np.asarray(Image.open(io.BytesIO(base64.b64decode(row_panels(pixels,
        [(40, 100, 2200, 300), (40, 580, 2200, 760)])))))
    expected = cv2.cvtColor(cv2.resize(pixels, None, fx=1400/2400, fy=1400/2400,
                                     interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
    source = sheet[30:30+expected.shape[0], 12:12+expected.shape[1]]
    assert source.shape == expected.shape
    assert np.abs(source.astype(float)-expected.astype(float)).mean() < 3
    assert np.array_equal(pixels, original)
    assert sheet.shape[0] * sheet.shape[1] < 9_000_000


@pytest.mark.parametrize('boxes', [[], [(0, 0, 200, 300)] * 36,
    [(-1, 0, 200, 30)], [(0, 20, 200, 20)], [(0, 0, 201, 30)],
    [(0, 0, 200, 300)] * 3])
def test_invalid_or_over_budget_bands_do_not_make_a_partial_sheet(boxes):
    assert row_panels(np.full((300, 200, 3), 245, np.uint8), boxes) is None


def test_merged_prose_uses_existing_second_call_with_source_panels(monkeypatch):
    pixels = np.full((900, 1000, 3), 245, np.uint8)
    first = {'kind': 'WORK', 'lines': [{'text': 'Số tiền sau một năm là:'},
        {'text': '12 + 8 = 20', 'role': 'EQUATION'}]}
    second = {'kind': 'WORK', 'lines': [{'text': 'Số tiền sau một'}, {'text': 'năm là:'},
        {'text': '12 + 8 = 20', 'role': 'EQUATION'}]}
    boxes = [(20, 100, 800, 170), (20, 300, 800, 370), (20, 500, 800, 570)]
    monkeypatch.setattr(notebook, 'handwriting_rows', lambda _: boxes)
    monkeypatch.setattr('app.recognition.text_detector.detect_text_regions', lambda _: [])
    cloud = AsyncMock(side_effect=[first, grouped(second)])
    monkeypatch.setattr(notebook, '_generate', cloud)
    result = asyncio.run(notebook.inspect_notebook(photo(pixels)))
    assert cloud.await_count == 2
    before, review = cloud.await_args_list
    assert before.args[2] != review.args[2] and 'FULL SOURCE is authoritative' in review.args[1]
    assert 'Ignore all printed English labels' in review.args[1]
    assert 'ZERO, ONE or SEVERAL' in review.args[0] and 'candidateId' in review.args[0]
    assert [line.text for line in result.lines] == [line['text'] for line in second['lines']]
    assert [line.box for line in result.lines] == [
        (x1, round(y1 * 1000 / 900), x2, round(y2 * 1000 / 900))
        for x1, y1, x2, y2 in boxes
    ]


def test_panel_reconciliation_cannot_certify_touching_envelopes(monkeypatch):
    first = {'kind': 'WORK', 'lines': [{'text': 'Số tiền sau một năm là:'}]}
    second = {'kind': 'WORK', 'lines': [{'text': 'Số tiền sau một'}, {'text': 'năm là:'}]}
    monkeypatch.setattr(notebook, 'handwriting_rows', lambda _: [(20, 100, 800, 200), (20, 200, 800, 300)])
    monkeypatch.setattr('app.recognition.text_detector.detect_text_regions', lambda _: [])
    cloud = AsyncMock(side_effect=[first, grouped(second)])
    monkeypatch.setattr(notebook, '_generate', cloud)
    result = asyncio.run(notebook.inspect_notebook(photo(np.full((900, 1000, 3), 245, np.uint8))))
    assert cloud.await_count == 2 and 'CANDIDATE BAND' in cloud.await_args_list[1].args[1]
    assert [line.text for line in result.lines] == [line['text'] for line in second['lines']]
    assert all(line.uncertain and line.box is None for line in result.lines)


def test_band_groups_allow_empty_and_multiple_rows_without_adding_text():
    rows = [{'text': 'Số tiền sau một'}, {'text': 'năm là:'}]
    payload = {'kind': 'WORK', 'bands': [{'candidateId': 1, 'lines': []},
        {'candidateId': 2, 'lines': rows}]}
    assert notebook._flatten_band_review(payload, 2) == ({'kind': 'WORK', 'lines': rows}, False)
    assert len(payload['bands']) == 2 and payload['bands'][0]['lines'] == []
    assert notebook._flatten_band_review({'kind': 'MULTIPLE', 'bands': []}, 2) == (
        {'kind': 'MULTIPLE', 'lines': []}, False)


def test_non_singleton_groups_keep_text_but_cannot_supply_geometry(monkeypatch):
    first = {'kind': 'WORK', 'lines': [{'text': 'một hai'}]}
    second = {'kind': 'WORK', 'bands': [{'candidateId': 1, 'lines': []},
        {'candidateId': 2, 'lines': [{'text': 'một'}, {'text': 'hai'}]}]}
    monkeypatch.setattr(notebook, 'handwriting_rows', lambda _: [(20, 100, 800, 170), (20, 300, 800, 370)])
    monkeypatch.setattr('app.recognition.text_detector.detect_text_regions', lambda _: [])
    monkeypatch.setattr(notebook, '_generate', AsyncMock(side_effect=[first, second]))
    result = asyncio.run(notebook.inspect_notebook(photo(np.full((900, 1000, 3), 245, np.uint8))))
    assert [line.text for line in result.lines] == ['một', 'hai']
    assert all(line.uncertain and line.box is None for line in result.lines)


@pytest.mark.parametrize('groups', [[{'candidateId': 1, 'lines': []}],
    [{'candidateId': 1, 'lines': []}, {'candidateId': 1, 'lines': []}],
    [{'candidateId': 2, 'lines': []}, {'candidateId': 1, 'lines': []}],
    [{'candidateId': True, 'lines': []}, {'candidateId': 2, 'lines': []}],
    [{'candidateId': 1, 'lines': 'invented'}, {'candidateId': 2, 'lines': []}]])
def test_missing_duplicated_or_unordered_band_groups_are_rejected(groups):
    with pytest.raises(ValueError):
        notebook._flatten_band_review({'kind': 'WORK', 'bands': groups}, 2)


def test_band_review_cannot_mix_flat_and_grouped_content():
    with pytest.raises(ValueError):
        notebook._flatten_band_review({'kind': 'WORK', 'lines': [], 'bands': []}, 2)


@pytest.mark.parametrize('fraction_ink', ['isolated', 'expression'])
def test_fraction_ink_misread_as_rows_keeps_the_whole_image_review(monkeypatch, fraction_ink):
    first = {'kind': 'WORK', 'lines': [{'text': '3', 'role': 'EQUATION'}, {'text': '2', 'role': 'EQUATION'}]}
    monkeypatch.setattr(notebook, 'handwriting_rows', lambda _: [(20, 20, 200, 80)])
    monkeypatch.setattr('app.recognition.text_detector.detect_text_regions', lambda _: [])
    monkeypatch.setattr(notebook, 'isolated_fraction', lambda _: fraction_ink == 'isolated')
    monkeypatch.setattr(notebook, 'fraction_expression', lambda _: fraction_ink == 'expression')
    def forbidden(*args):
        raise AssertionError('A fraction must never be split into candidate row panels')
    monkeypatch.setattr(notebook, 'row_panels', forbidden)
    cloud = AsyncMock(return_value=first)
    monkeypatch.setattr(notebook, '_generate', cloud)
    asyncio.run(notebook.inspect_notebook(photo(np.full((300, 500, 3), 245, np.uint8))))
    assert cloud.await_count == 2 and cloud.await_args_list[0].args[2] == cloud.await_args_list[1].args[2]


@pytest.mark.parametrize('other', ['Tính 12 × 8.', 'Tính 12 + 9.'])
@pytest.mark.parametrize('first_line_matches_other', [False, True])
def test_disputed_question_cannot_start_a_lesson_even_with_matching_line_text(monkeypatch, other, first_line_matches_other):
    first = {'kind': 'PROBLEM', 'problemText': 'Tính 12 + 8.', 'lines': [
        {'text': other if first_line_matches_other else 'Tính 12 + 8.'}]}
    second = {'kind': 'PROBLEM', 'problemText': other, 'lines': [{'text': other}]}
    cloud = AsyncMock(side_effect=[first, second])
    monkeypatch.setattr(notebook, '_generate', cloud)
    result = asyncio.run(notebook.inspect_notebook(photo(np.full((300, 500, 3), 245, np.uint8))))
    assert cloud.await_count == 2
    assert result.kind == 'WORK' and result.problemText == '' and result.needsProblem
    assert result.lines[0].text == first['lines'][0]['text']


@pytest.mark.parametrize('other', ['a + b = c', 'a - b = c'])
def test_symbolic_equations_need_independent_review(monkeypatch, other):
    first = {'kind': 'WORK', 'lines': [{'text': 'a + b = c', 'role': 'EQUATION'}]}
    second = {'kind': 'WORK', 'lines': [{'text': other, 'role': 'EQUATION'}]}
    cloud = AsyncMock(side_effect=[first, second])
    monkeypatch.setattr(notebook, '_generate', cloud)
    result = asyncio.run(notebook.inspect_notebook(photo(np.full((300, 500, 3), 245, np.uint8))))
    assert cloud.await_count == 2
    assert result.lines[0].text == 'a + b = c'
    assert result.lines[0].uncertain is (other != 'a + b = c')
