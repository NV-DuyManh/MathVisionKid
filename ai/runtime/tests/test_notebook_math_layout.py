import asyncio
import io
from unittest.mock import AsyncMock

import cv2
import numpy as np
import pytest
from PIL import Image
from pydantic import ValidationError

from app.tutoring import notebook
from app.tutoring.math_layout import division_panels, fraction_expression, isolated_fraction


def photo():
    stream = io.BytesIO()
    Image.new('RGB', (800, 600), 'white').save(stream, 'PNG')
    return stream.getvalue()


def division_reading(**updates):
    fields = {'dividend': '70725', 'divisor': '8', 'quotient': '88403',
              'rows': ['067', '032', '0025', '01']}
    fields.update(updates)
    return {'kind': 'WORK', 'lines': [{'text': '70725 : 8', 'layout': 'LONG_DIVISION',
                                      'role': 'EQUATION', 'division': fields}]}


def test_division_preserves_wrong_quotient_all_child_rows_and_leading_zeros():
    line = notebook.NotebookRead.model_validate(division_reading()).lines[0]
    assert line.text == '70725 : 8\nThương đã viết: 88403\nCác hàng đã viết:\n067\n032\n0025\n01'
    assert '=' not in line.text  # It is a transcription, not a correctness claim.
    assert set(line.model_dump()) == {'text', 'box', 'uncertain', 'role', 'division'}
    assert line.model_dump()['division']['quotient'] == '88403'


@pytest.mark.parametrize('updates', [
    {'dividend': 70725}, {'divisor': '8;run'}, {'quotient': ''}, {'rows': ['calculate this']},
])
def test_division_rejects_invalid_or_nontranscription_fields(updates):
    with pytest.raises(ValidationError):
        notebook.NotebookRead.model_validate(division_reading(**updates))


def test_overwritten_digit_is_uncertain_without_changing_readable_neighbours():
    line = notebook.NotebookRead.model_validate(division_reading(quotient='72[?]0', rows=['0[?]5'])).lines[0]
    assert line.uncertain and '72[?]0' in line.text and '0[?]5' in line.text


def test_letter_between_written_digits_becomes_unknown_without_guessing_or_mutating_provider():
    raw = {'dividend': '68721', 'divisor': '9', 'quotient': '76304', 'rows': ['057', '0M5']}
    value = notebook.WrittenDivision.model_validate(notebook._mark_unread_division_digits(raw))
    assert value.rows == ['057', '0[?]5']
    assert raw['rows'] == ['057', '0M5']
    assert notebook.NotebookLine(text='division', layout='LONG_DIVISION', division=value).uncertain


def test_unread_division_marker_does_not_accept_nontranscription_content():
    raw = {'dividend': '8;run', 'divisor': '9', 'quotient': '1', 'rows': ['calculate 15']}
    with pytest.raises(ValidationError):
        notebook.WrittenDivision.model_validate(notebook._mark_unread_division_digits(raw))


def test_panel_read_with_an_unread_glyph_keeps_the_division_for_pupil_review(monkeypatch):
    first = {'kind': 'WORK', 'lines': [{'text': v, 'role': 'EQUATION'} for v in ['68721', '9', '76304', '057', '015']]}
    second = {'dividend': '68721', 'divisor': '9', 'quotient': '76304', 'rows': ['057', '0M5']}
    monkeypatch.setattr(notebook, 'division_panels', lambda _: 'source panels')
    monkeypatch.setattr(notebook, '_generate', AsyncMock(side_effect=[first, second]))
    result = asyncio.run(notebook.inspect_notebook(photo()))
    assert len(result.lines) == 1 and result.lines[0].uncertain
    assert result.lines[0].division.rows == ['057', '0[?]5']
    assert result.lines[0].division.quotient == '76304'


@pytest.mark.parametrize('text', ['(3)/(2)', '13/2', '(3)/(2) + (1)/(4) = (7)/(4)',
                                '2 (3)/(2)', '(7+44)/(24)', '(3+5)/8', '[?]/2'])
def test_fraction_tiers_keep_one_expression(text):
    line = notebook.NotebookLine(text=text, layout='FRACTION')
    assert line.text == text and line.role == 'EQUATION'


def test_fraction_layout_cannot_lose_the_denominator():
    with pytest.raises(ValidationError):
        notebook.NotebookLine(text='3', layout='FRACTION')


def test_legacy_equation_with_both_fraction_tiers_is_reviewed_as_math():
    line = notebook.NotebookLine(text='3 + 5/8 = 3/1 + 5/8 = (3+5)/8 = 8/8 = 1', role='EQUATION')
    assert line.layout == 'FRACTION'
    assert '3/1' in line.text and '(3+5)/8' in line.text


def test_fraction_answers_do_not_become_an_invented_original_question(monkeypatch):
    expression = '3 + 5/8 = 3/1 + 5/8 = (3+5)/8 = 8/8 = 1'
    payload = {'kind': 'PROBLEM', 'problemText': expression,
               'lines': [{'text': expression, 'role': 'EQUATION'}]}
    monkeypatch.setattr(notebook, '_generate', AsyncMock(return_value=payload))
    result = asyncio.run(notebook.inspect_notebook(photo()))
    assert result.kind == 'WORK' and result.problemText == '' and result.needsProblem
    assert result.lines[0].text == expression


def test_fraction_work_keeps_the_separately_transcribed_original_question(monkeypatch):
    payload = {'kind': 'MIXED', 'problemText': 'Tính 3 + 5/8.',
               'lines': [{'text': '3 + 5/8 = 3/1 + 5/8 = (3+5)/8 = 1', 'role': 'EQUATION'}]}
    monkeypatch.setattr(notebook, '_generate', AsyncMock(return_value=payload))
    result = asyncio.run(notebook.inspect_notebook(photo()))
    assert result.kind == 'MIXED' and result.problemText == 'Tính 3 + 5/8.'
    assert not result.needsProblem


@pytest.mark.parametrize('different', [False, True])
def test_fraction_review_compares_every_tier_and_never_attaches_row_count_geometry(monkeypatch, different):
    first = {'kind': 'WORK', 'lines': [{'text': '(3)/(2)', 'layout': 'FRACTION'}]}
    second = {'kind': 'WORK', 'lines': [{'text': '(2)/(3)' if different else '(3)/(2)', 'layout': 'FRACTION'}]}
    monkeypatch.setattr(notebook, 'handwriting_rows', lambda _: [(10, 10, 70, 90)])
    monkeypatch.setattr(notebook, '_generate', AsyncMock(side_effect=[first, second]))
    result = asyncio.run(notebook.inspect_notebook(photo()))
    assert result.lines[0].text == '(3)/(2)'
    assert result.lines[0].uncertain is different
    assert result.lines[0].box is None


def test_grouped_math_is_uncertain_when_verification_is_unavailable(monkeypatch):
    monkeypatch.setattr(notebook, '_generate', AsyncMock(side_effect=[division_reading(), notebook.TutorUnavailable()]))
    monkeypatch.setattr(notebook, 'division_panels', lambda _: None)
    result = asyncio.run(notebook.inspect_notebook(photo()))
    assert result.lines[0].uncertain and result.lines[0].division.quotient == '88403'


def test_position_panels_fix_operand_order_with_explicit_uncertainty(monkeypatch):
    original = division_reading(dividend='88403', divisor='70725', quotient='8')
    actual = division_reading()['lines'][0]['division']
    generate = AsyncMock(side_effect=[original, actual])
    monkeypatch.setattr(notebook, '_generate', generate)
    monkeypatch.setattr(notebook, 'division_panels', lambda _: 'verified image panels')
    result = asyncio.run(notebook.inspect_notebook(photo()))
    assert result.lines[0].division == notebook.WrittenDivision.model_validate(actual)
    assert result.lines[0].uncertain and result.lines[0].box is None
    assert generate.call_args_list[1].args[0] == notebook.READ_DIVISION


def test_grouping_does_not_hide_capacity_overflow():
    payload = {'kind': 'WORK', 'lines': division_reading()['lines'] * 6}
    assert notebook._reading_exceeds_capacity(payload)  # 36 physical tiers, six blocks.


@pytest.mark.parametrize('initial_kind', ['UNREADABLE', 'MULTIPLE'])
def test_isolated_fraction_retries_a_questionless_expression(monkeypatch, initial_kind):
    fraction = {'kind': 'PROBLEM', 'problemText': '13/2', 'needsCrop': True,
                'lines': [{'text': '13/2', 'layout': 'FRACTION'}]}
    monkeypatch.setattr(notebook, 'isolated_fraction', lambda _: True)
    cloud = AsyncMock(side_effect=[{'kind': initial_kind, 'needsCrop': True}, fraction, fraction])
    monkeypatch.setattr(notebook, '_generate', cloud)
    result = asyncio.run(notebook.inspect_notebook(photo()))
    assert result.kind == 'PROBLEM' and result.problemText == '13/2' and not result.needsCrop
    assert len(result.lines) == 1 and not result.lines[0].uncertain


def test_incomplete_fraction_still_requires_a_better_photo(monkeypatch):
    payload = {'kind': 'WORK', 'needsCrop': True,
               'lines': [{'text': '13/[?]', 'layout': 'FRACTION', 'uncertain': True}]}
    monkeypatch.setattr(notebook, 'isolated_fraction', lambda _: True)
    monkeypatch.setattr(notebook, '_generate', AsyncMock(return_value=payload))
    result = asyncio.run(notebook.inspect_notebook(photo()))
    assert result.kind == 'UNREADABLE' and result.needsCrop


def test_one_ink_supported_fraction_is_not_discarded_when_verifier_splits_tiers(monkeypatch):
    fraction = {'kind': 'PROBLEM', 'problemText': '3/2',
                'lines': [{'text': '3/2', 'layout': 'FRACTION'}]}
    monkeypatch.setattr(notebook, 'isolated_fraction', lambda _: True)
    monkeypatch.setattr(notebook, '_generate', AsyncMock(side_effect=[fraction, {'kind': 'MULTIPLE'}]))
    result = asyncio.run(notebook.inspect_notebook(photo()))
    assert result.kind == 'PROBLEM' and result.problemText == '3/2'
    assert result.lines[0].uncertain and result.lines[0].box is None


def test_single_fraction_ink_guard_rejects_a_colon_and_a_prose_row():
    pixels = np.full((240, 120, 3), 248, np.uint8)
    cv2.putText(pixels, '3', (35, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (140, 40, 20), 3)
    cv2.line(pixels, (25, 105), (85, 105), (140, 40, 20), 3)
    cv2.putText(pixels, '2', (35, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (140, 40, 20), 3)
    assert isolated_fraction(pixels)
    pair = np.concatenate([pixels, pixels], axis=1)
    assert fraction_expression(pair)
    assert not isolated_fraction(pair)
    assert not isolated_fraction(np.concatenate([pixels, pixels], axis=0))
    assert not fraction_expression(pixels)
    assert division_panels(pixels) is None
    pixels[:] = 248
    cv2.putText(pixels, '3 : 2', (2, 120), cv2.FONT_HERSHEY_SIMPLEX, .7, (140, 40, 20), 2)
    assert not isolated_fraction(pixels)
    assert not fraction_expression(pixels)
    assert not isolated_fraction(np.full((240, 120, 3), 248, np.uint8))


def school_division(x=185, width=400):
    image = np.full((320, width, 3), 248, np.uint8)
    ink = (140, 40, 20)
    cv2.putText(image, '87', (x-120, 62), cv2.FONT_HERSHEY_SIMPLEX, 1, ink, 2)
    cv2.putText(image, '4', (x+18, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, ink, 2)
    cv2.line(image, (x, 18), (x, 122), ink, 2)
    cv2.line(image, (x, 78), (x+105, 78), ink, 2)
    cv2.putText(image, '21', (x+18, 118), cv2.FONT_HERSHEY_SIMPLEX, 1, ink, 2)
    cv2.putText(image, '07', (x-95, 160), cv2.FONT_HERSHEY_SIMPLEX, 1, ink, 2)
    cv2.putText(image, '3', (x-75, 212), cv2.FONT_HERSHEY_SIMPLEX, 1, ink, 2)
    return image


@pytest.mark.parametrize('ink', [(35, 35, 35), (90, 90, 90)])
def test_neutral_fraction_support_keeps_both_tiers_and_rejects_rulings(ink):
    pixels = np.full((240, 120, 3), 248, np.uint8)
    cv2.putText(pixels, '3', (35, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.2, ink, 3)
    cv2.line(pixels, (25, 105), (85, 105), ink, 3)
    cv2.putText(pixels, '2', (35, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.2, ink, 3)
    original = pixels.copy()
    assert isolated_fraction(pixels)
    assert fraction_expression(np.concatenate([pixels, pixels], axis=1))
    assert np.array_equal(pixels, original)
    assert not isolated_fraction(np.concatenate([pixels, pixels], axis=0))
    assert not fraction_expression(np.tile(pixels, (3, 3, 1)))
    assert division_panels(pixels) is None  # Neutral division path remains unchanged.
    pixels[100:110] = 248
    cv2.line(pixels, (0, 105), (119, 105), ink, 3)
    assert not isolated_fraction(pixels)  # A full-width ruling is insufficient.
    assert not fraction_expression(np.concatenate([pixels, pixels], axis=1))


def test_neutral_prose_grid_colon_and_subtraction_do_not_trigger_fraction_retry():
    pixels = np.full((220, 500, 3), 240, np.uint8)
    for text in ('3 : 2', '3 - 2', 'Read this row', '1 + 2 = 3'):
        pixels[:] = 240
        cv2.putText(pixels, text, (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (40, 40, 40), 2)
        assert not isolated_fraction(pixels) and not fraction_expression(pixels)
    pixels[:] = 240
    for x in range(0, 500, 20):
        cv2.line(pixels, (x, 0), (x, 219), (130, 130, 130), 1)
    for y in range(0, 220, 20):
        cv2.line(pixels, (0, y), (499, y), (130, 130, 130), 1)
    assert not isolated_fraction(pixels) and not fraction_expression(pixels)


def test_ruling_fragments_around_one_fraction_are_not_multiple_fractions():
    pixels = np.full((240, 120, 3), 248, np.uint8)
    cv2.putText(pixels, '3', (35, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (35, 35, 35), 3)
    cv2.putText(pixels, '2', (35, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (35, 35, 35), 3)
    for y in (95, 105, 115):
        cv2.line(pixels, (25, y), (85, y), (35, 35, 35), 2)
    assert not fraction_expression(pixels)
    assert fraction_expression(np.concatenate([pixels, pixels], axis=1))


@pytest.mark.parametrize('scale', [1, 2, 4, 8])
def test_neutral_fraction_probe_preserves_support_at_larger_capture_sizes(scale):
    pixels = np.full((240, 120, 3), 248, np.uint8)
    cv2.putText(pixels, '3', (35, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (35, 35, 35), 3)
    cv2.line(pixels, (25, 105), (85, 105), (35, 35, 35), 3)
    cv2.putText(pixels, '2', (35, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (35, 35, 35), 3)
    # A tiny blue ruling fragment grows past eight pixels in larger captures.
    cv2.rectangle(pixels, (100, 80), (104, 82), (140, 40, 20), -1)
    captured = cv2.resize(pixels, None, fx=scale, fy=scale)
    original = captured.copy()
    assert isolated_fraction(captured)
    assert fraction_expression(np.concatenate([captured, captured], axis=1))
    assert not isolated_fraction(np.concatenate([captured, captured], axis=1))
    assert not fraction_expression(captured)
    assert not fraction_expression(np.tile(captured, (3, 3, 1)))
    assert np.array_equal(captured, original)


def test_division_bracket_panels_require_one_complete_layout():
    assert division_panels(school_division())
    assert not fraction_expression(school_division())
    pair = np.concatenate([school_division(), school_division()], axis=1)
    assert division_panels(pair) is None
    assert division_panels(np.full((320, 400, 3), 248, np.uint8)) is None


def test_division_panels_retain_full_source_when_work_crosses_bracket():
    import base64
    import io
    from PIL import Image
    pixels = school_division()
    # This later working row crosses the column boundary; it must stay visible
    # even though the labelled left-column crop cannot contain its final digit.
    cv2.putText(pixels, '015', (150, 275), cv2.FONT_HERSHEY_SIMPLEX, 1, (140, 40, 20), 2)
    encoded = division_panels(pixels)
    assert encoded
    canvas = np.asarray(Image.open(io.BytesIO(base64.b64decode(encoded))))
    source = canvas[-pixels.shape[0]-15:-15, 12:12+pixels.shape[1]]
    expected = cv2.cvtColor(pixels, cv2.COLOR_BGR2RGB)
    assert source.shape == expected.shape
    assert np.abs(source.astype(float) - expected.astype(float)).mean() < 3


def test_division_bracket_accepts_a_small_source_gap_without_accepting_two_exercises():
    pixels = school_division()
    pixels[75:82, 185:198] = 248
    assert division_panels(pixels)
    assert division_panels(np.concatenate([pixels, pixels], axis=1)) is None


def test_fraction_retry_preserves_visible_operands_when_result_is_overwritten(monkeypatch):
    partial = {'kind': 'WORK', 'lines': [{'text': '(3)/(2) × (2)/(3) = [?]/2', 'layout': 'FRACTION'}]}
    monkeypatch.setattr(notebook, 'fraction_expression', lambda _: True)
    monkeypatch.setattr(notebook, '_generate', AsyncMock(side_effect=[{'kind': 'UNREADABLE'}, partial, partial]))
    result = asyncio.run(notebook.inspect_notebook(photo()))
    assert result.kind == 'WORK' and result.lines[0].uncertain
    assert result.lines[0].text == '(3)/(2) × (2)/(3) = [?]/2'


@pytest.mark.parametrize('disagrees', [False, True])
def test_fraction_review_crop_flag_requires_incomplete_or_disagreeing_content(monkeypatch, disagrees):
    first = {'kind': 'WORK', 'lines': [
        {'text': '4/9 + 2/9 - 5/18 = 8/9 - 5/18', 'role': 'EQUATION'},
        {'text': '= 16/18 - 5/18 = 11/18', 'role': 'EQUATION'}]}
    second = {'kind': 'WORK', 'needsCrop': True, 'lines': [
        first['lines'][0], {'text': '= 12/18' if disagrees else first['lines'][1]['text'], 'role': 'EQUATION'}]}
    monkeypatch.setattr(notebook, '_generate', AsyncMock(side_effect=[first, second]))
    result = asyncio.run(notebook.inspect_notebook(photo()))
    assert result.kind == 'WORK' and not result.needsCrop
    assert len(result.lines) == 2 and all(line.uncertain is disagrees for line in result.lines)
    assert all(line.box is None for line in result.lines)
    assert result.lines[1].text == first['lines'][1]['text']


def test_internal_inspect_api_preserves_existing_student_contract(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.api.tutor import router
    from app.config import settings
    reading = division_reading()
    monkeypatch.setattr(notebook, '_generate', AsyncMock(side_effect=[reading, reading['lines'][0]['division']]))
    monkeypatch.setattr(notebook, 'division_panels', lambda _: 'image panels')
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        response = client.post('/inspect', content=photo(), headers={
            'content-type': 'image/png', 'X-Internal-API-Key': settings.internal_api_key})
    assert response.status_code == 200
    body = response.json()
    assert len(body['lines']) == 1 and body['needsProblem']
    assert set(body['lines'][0]) == {'text', 'box', 'uncertain', 'role', 'division'}
    assert body['lines'][0]['division'] == reading['lines'][0]['division']
    assert '0025\n01' in body['lines'][0]['text'] and body['lines'][0]['box'] is None
