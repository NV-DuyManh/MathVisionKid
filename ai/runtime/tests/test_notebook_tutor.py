import asyncio
import io
import cv2
import numpy as np
import pytest
from unittest.mock import AsyncMock

from PIL import Image

from app.tutoring import notebook
from app.tutoring.rows import handwriting_rows


def image_bytes(size=(1800, 890)):
    buffer = io.BytesIO()
    Image.new("RGB", size, "white").save(buffer, "PNG")
    return buffer.getvalue()


def run(value):
    return asyncio.run(value)


def cow_reading():
    return {
        "kind": "WORK", "problemText": "", "needsProblem": True,
        "lines": [
            {"text": "Bài giải:", "box": [280, 10, 560, 70], "uncertain": False},
            {"text": "49 : 7 × 2 = 14 (con)", "box": [240, 205, 640, 270], "uncertain": False},
            {"text": "Bò vàng: 35 con", "box": [510, 405, 820, 470], "uncertain": False},
        ],
    }


def test_unverified_model_geometry_is_not_displayed(monkeypatch):
    cloud=AsyncMock(return_value=cow_reading())
    monkeypatch.setattr(notebook, "_generate", cloud)
    result = run(notebook.inspect_notebook(image_bytes()))
    assert [line.text for line in result.lines][-1] == "Bò vàng: 35 con"
    assert all(line.box is None for line in result.lines)
    assert result.needsProblem is True
    assert cloud.await_args_list[0].kwargs['max_output_tokens']==4000


def test_notebook_uses_physically_supported_short_rows_before_grounding_transcript(monkeypatch):
    from app.recognition import text_detector
    from app.tutoring import rows
    generate = AsyncMock(return_value=cow_reading())
    monkeypatch.setattr(notebook, '_generate', generate)
    physical = [(100, 100, 600, 180), (100, 500, 800, 580)]
    short = (100, 300, 200, 360)
    learned = [physical[0], short, physical[1]]
    monkeypatch.setattr(notebook, 'handwriting_rows', lambda pixels: physical)
    monkeypatch.setattr(text_detector, 'detect_text_regions', lambda pixels: learned)
    def recover(pixels, existing, candidates):
        assert existing == physical and candidates == learned
        return [short]
    monkeypatch.setattr(rows, 'short_row_candidates', recover)
    result = run(notebook.inspect_notebook(image_bytes((1000, 1000))))
    assert [line.box for line in result.lines] == [
        (100, 100, 600, 180), short, (100, 500, 800, 580)]
    assert generate.await_count == 2  # Row count does not independently verify digits.


@pytest.mark.parametrize('review', ['same', 'digit_change', 'operator_change', 'crossed_out', 'unavailable'])
def test_numeric_rows_need_exact_independent_reading_even_when_row_counts_match(monkeypatch, review):
    from copy import deepcopy
    first = {'kind': 'WORK', 'lines': [
        {'text': 'Bài giải'}, {'text': '864 : 4 = 216 (con)', 'role': 'EQUATION'}]}
    second = deepcopy(first)
    if review == 'digit_change':
        second['lines'][1]['text'] = '864 : 4 = 218 (con)'
    elif review == 'operator_change':
        second['lines'][1]['text'] = '864 + 4 = 216 (con)'
    elif review == 'crossed_out':
        second['lines'][1]['uncertain'] = True
    monkeypatch.setattr(notebook, 'handwriting_rows',
                        lambda _: [(100, 100, 600, 180), (100, 300, 800, 380)])
    cloud = AsyncMock(side_effect=[first, notebook.TutorUnavailable() if review == 'unavailable' else second])
    monkeypatch.setattr(notebook, '_generate', cloud)
    result = run(notebook.inspect_notebook(image_bytes((1000, 1000))))
    assert cloud.await_count == 2
    assert result.lines[1].text == first['lines'][1]['text']
    assert result.lines[1].uncertain is (review != 'same')
    assert result.lines[1].box == (100, 300, 800, 380)


def test_review_cannot_clear_initial_uncertainty_or_supply_missing_numbers(monkeypatch):
    first = {'kind': 'WORK', 'lines': [
        {'text': '864 : [?] = 216', 'uncertain': True, 'role': 'EQUATION'}]}
    second = {'kind': 'WORK', 'lines': [{'text': '864 : 4 = 216', 'role': 'EQUATION'}]}
    monkeypatch.setattr(notebook, 'handwriting_rows', lambda _: [(100, 100, 600, 180)])
    monkeypatch.setattr(notebook, '_generate', AsyncMock(side_effect=[first, second]))
    result = run(notebook.inspect_notebook(image_bytes((1000, 1000))))
    assert result.lines[0].text == '864 : [?] = 216' and result.lines[0].uncertain


@pytest.mark.parametrize('initial_uncertainty,expired', [(True, False), (False, True)])
def test_unverified_numeric_row_stays_uncertain_without_extending_request_budget(monkeypatch, initial_uncertainty, expired):
    from types import SimpleNamespace
    payload = {'kind': 'WORK', 'lines': [
        {'text': '864 : 4 = 216', 'uncertain': initial_uncertainty, 'role': 'EQUATION'}]}
    monkeypatch.setattr(notebook, 'handwriting_rows', lambda _: [(100, 100, 600, 180)])
    if expired:
        moments = iter([0., 40.])
        monkeypatch.setattr(notebook, 'time', SimpleNamespace(monotonic=lambda: next(moments)))
    cloud = AsyncMock(return_value=payload)
    monkeypatch.setattr(notebook, '_generate', cloud)
    result = run(notebook.inspect_notebook(image_bytes((1000, 1000))))
    assert result.lines[0].text == payload['lines'][0]['text'] and result.lines[0].uncertain
    assert cloud.await_count == (1 if expired else 2)


def test_learned_short_region_alone_cannot_supply_notebook_geometry(monkeypatch):
    from app.recognition import text_detector
    from app.tutoring import rows
    monkeypatch.setattr(notebook, '_generate', AsyncMock(return_value=cow_reading()))
    monkeypatch.setattr(notebook, 'handwriting_rows',
                        lambda pixels: [(100, 100, 600, 180), (100, 500, 800, 580)])
    monkeypatch.setattr(text_detector, 'detect_text_regions',
                        lambda pixels: [(100, 300, 200, 360)])
    monkeypatch.setattr(rows, 'short_row_candidates', lambda *args: [])
    result = run(notebook.inspect_notebook(image_bytes((1000, 1000))))
    assert all(line.box is None for line in result.lines)
    assert result.lines[1].uncertain and result.lines[2].uncertain


def test_unclear_symbol_gets_targeted_question_without_cloud(monkeypatch):
    cloud = AsyncMock()
    monkeypatch.setattr(notebook, "_generate", cloud)
    result = run(notebook.coach_notebook(notebook.CoachRequest(
        problemText="", workText="49 : [?] × 2", stage="CHECK_WORK",
        focusText="49 : [?] × 2", studentAttempt="", hintLevel=0, previousHint="")))
    assert result.guarded is True
    assert "số hoặc dấu gì" in result.question
    cloud.assert_not_called()


def test_coaching_may_reference_visible_numbers_but_blocks_new_result(monkeypatch):
    request = notebook.CoachRequest(problemText="", workText="49 : 7 × 2 = 14 (con)",
        stage="CHECK_WORK", focusText="49 : 7 × 2 = 14 (con)", studentAttempt="", hintLevel=0, previousHint="")
    response = notebook.GuideResponse(stage="CHECK_WORK", hint="Em hãy nhìn lại 49 : 7 trước.",
        question="Vì sao em chia trước khi nhân?", feedback="", guarded=False)
    assert notebook.unsafe_coaching(response, request) is False
    leaked = response.model_copy(update={"hint": "Em tính được 7 rồi nhân tiếp."})
    assert notebook.unsafe_coaching(leaked, request) is True
    invented = response.model_copy(update={"hint": "Kết quả là 98."})
    assert notebook.unsafe_coaching(invented, request) is True


@pytest.mark.parametrize('needs_crop', [False, True])
def test_multiple_problems_return_crop_request_without_transcript(monkeypatch, needs_crop):
    monkeypatch.setattr(notebook, "_generate", AsyncMock(return_value={
        "kind": "MULTIPLE", "problemText": "ignored", "needsProblem": False,
        "needsCrop": needs_crop,
        "lines": [{"text": "1 + 2", "box": None, "uncertain": False}],
    }))
    result = run(notebook.inspect_notebook(image_bytes((800, 1200))))
    assert result.kind == "MULTIPLE" and result.lines == [] and result.problemText == ""
    assert not result.needsCrop


@pytest.mark.parametrize('needs_crop', [False, True])
def test_independent_review_multiple_overrides_a_single_work_misclassification(monkeypatch, needs_crop):
    monkeypatch.setattr(notebook, 'handwriting_rows',
                        lambda pixels: [(100, 100, 600, 180), (100, 500, 800, 580)])
    monkeypatch.setattr('app.recognition.text_detector.detect_text_regions', lambda pixels: [])
    cloud = AsyncMock(side_effect=[cow_reading(), {
        'kind': 'MULTIPLE', 'problemText': 'discard this',
        'lines': [{'text': 'discard this too'}], 'needsProblem': True, 'needsCrop': needs_crop}])
    monkeypatch.setattr(notebook, '_generate', cloud)
    result = run(notebook.inspect_notebook(image_bytes((1000, 1000))))
    assert cloud.await_count == 2
    assert result.kind == 'MULTIPLE' and result.lines == [] and result.problemText == ''
    assert not result.needsCrop


def test_independent_single_work_review_keeps_a_multi_step_solution(monkeypatch):
    monkeypatch.setattr(notebook, 'handwriting_rows',
                        lambda pixels: [(100, 100, 600, 180), (100, 500, 800, 580)])
    monkeypatch.setattr('app.recognition.text_detector.detect_text_regions', lambda pixels: [])
    cloud = AsyncMock(side_effect=[cow_reading(), cow_reading()])
    monkeypatch.setattr(notebook, '_generate', cloud)
    result = run(notebook.inspect_notebook(image_bytes((1000, 1000))))
    assert cloud.await_count == 2
    assert result.kind == 'WORK' and len(result.lines) == 3 and result.needsProblem


def test_answer_prose_cannot_become_an_original_question(monkeypatch):
    monkeypatch.setattr(notebook, "_generate", AsyncMock(return_value={
        "kind": "PROBLEM", "problemText": "Nhà trường đã vượt kế hoạch 15%", "needsProblem": False,
        "lines": [
            {"text": "Nhà trường đã vượt kế hoạch số phần trăm là:", "uncertain": False},
            {"text": "115% - 100% = 15%", "uncertain": False},
            {"text": "Đáp số: 15%", "uncertain": False},
        ],
    }))
    result = run(notebook.inspect_notebook(image_bytes()))
    assert result.kind == "WORK" and result.problemText == "" and result.needsProblem


def test_visible_question_is_preserved_with_its_work(monkeypatch):
    monkeypatch.setattr(notebook, "_generate", AsyncMock(return_value={
        "kind": "MIXED", "problemText": "Hỏi quyển vở có giá bao nhiêu tiền?", "needsProblem": False,
        "lines": [
            {"text": "Hỏi quyển vở có giá bao nhiêu tiền?", "uncertain": False},
            {"text": "Đáp số: 13000 đồng", "uncertain": False},
        ],
    }))
    result = run(notebook.inspect_notebook(image_bytes()))
    assert result.kind == "MIXED" and result.problemText and not result.needsProblem


@pytest.mark.parametrize('question', [
    'Điền số thích hợp vào ô trống: □ + 3 = 10.', 'x + 3 = 10', 'y + 3 = 10', 'm + 3 = 10',
    'Bài 2: So sánh 7 và 10.', 'Viết số thích hợp vào chỗ chấm.',
    'Đặt tính rồi tính 84 : 4.', 'Rút gọn phân số 6/8.',
])
def test_actual_tasks_survive_on_a_page_with_completed_work(monkeypatch, question):
    payload = {'kind': 'MIXED', 'problemText': question, 'lines': [
        {'text': question}, {'text': '7 + 3 = 10', 'role': 'EQUATION'}]}
    monkeypatch.setattr(notebook, '_generate', AsyncMock(return_value=payload))
    result = run(notebook.inspect_notebook(image_bytes()))
    assert result.kind == 'MIXED' and result.problemText == question and not result.needsProblem


@pytest.mark.parametrize('selected', [
    'Số tiền mua vở là: 10 000 × 3 = 30 000 (đồng)', 'Ta tính số tiền mua vở:',
    'Tính được số tiền là:', 'Tìm ra số tiền là:',
])
def test_question_elsewhere_cannot_validate_selected_solution_prose(monkeypatch, selected):
    question = 'Hỏi mua ba quyển vở hết bao nhiêu tiền?'
    payload = {'kind': 'MIXED', 'problemText': selected, 'lines': [
        {'text': question}, {'text': 'Ta tính số tiền mua vở:'},
        {'text': '10 000 × 3 = 30 000 (đồng)', 'role': 'EQUATION'}]}
    monkeypatch.setattr(notebook, '_generate', AsyncMock(return_value=payload))
    result = run(notebook.inspect_notebook(image_bytes()))
    assert result.kind == 'WORK' and result.problemText == '' and result.needsProblem
    assert result.lines[0].text == question  # Retain the source, require clarification.
    assert result.lines[-1].text == '10 000 × 3 = 30 000 (đồng)'


@pytest.mark.parametrize('question', ['87 : 4', 'Tính 87 : 4.'])
def test_written_division_work_is_not_itself_the_original_question(monkeypatch, question):
    division = {'dividend': '87', 'divisor': '4', 'quotient': '21', 'rows': ['07', '3']}
    payload = {'kind': 'PROBLEM', 'problemText': question, 'lines': [
        {'text': 'division', 'layout': 'LONG_DIVISION', 'division': division}]}
    monkeypatch.setattr(notebook, '_generate', AsyncMock(return_value=payload))
    monkeypatch.setattr(notebook, 'division_panels', lambda _: None)
    result = run(notebook.inspect_notebook(image_bytes()))
    assert result.lines[0].division.model_dump() == division
    assert result.problemText == (question if question.startswith('Tính') else '')
    assert result.needsProblem is (not question.startswith('Tính'))


def test_independent_reading_can_dispute_an_original_question_without_replacing_text(monkeypatch):
    lines = [{'text': 'Tính 84 : 4.'}, {'text': '84 : 4 = 21', 'role': 'EQUATION'}]
    first = {'kind': 'MIXED', 'problemText': 'Tính 84 : 4.', 'lines': lines}
    second = {'kind': 'WORK', 'lines': lines}
    monkeypatch.setattr(notebook, 'handwriting_rows', lambda _: [(20, 20, 800, 100), (20, 150, 800, 230)])
    monkeypatch.setattr(notebook, '_generate', AsyncMock(side_effect=[first, second]))
    result = run(notebook.inspect_notebook(image_bytes((1000, 1000))))
    assert result.kind == 'MIXED' and result.problemText == '[?] Tính 84 : 4.' and not result.needsProblem
    assert [line.text for line in result.lines] == [line['text'] for line in lines]


@pytest.mark.parametrize('second_question', ['Tính 12 + 8', '  Tính  12 + 8? '])
def test_worksheet_heading_or_sentence_punctuation_does_not_erase_a_question(monkeypatch, second_question):
    first = {'kind': 'PROBLEM', 'problemText': 'Bài 7: Tính 12 + 8.',
             'lines': [{'text': 'Tính 12 + 8.'}]}
    second = {'kind': 'PROBLEM', 'problemText': second_question, 'lines': first['lines']}
    monkeypatch.setattr(notebook, '_generate', AsyncMock(side_effect=[first, second]))
    result = run(notebook.inspect_notebook(image_bytes()))
    assert result.kind == 'PROBLEM' and result.problemText == first['problemText']
    assert not result.needsProblem and '[?]' not in result.problemText


def test_fraction_operand_parentheses_do_not_dispute_an_identical_transcription():
    assert notebook._question_signature('Bài 6: Có (1)/(3) số cây là táo.') == notebook._question_signature('Có 1/3 số cây là táo.')


@pytest.mark.parametrize('first,other', [('Tính 1/3 + 2/5.', 'Tính 1/2 + 2/5.'),
    ('Tính 1,5 + 2.', 'Tính 15 + 2.'), ('Tính 12 : 3.', 'Tính 12 × 3.'),
    ('Tính 1/(3 + 2).', 'Tính 1/3 + 2.')])
def test_question_comparison_preserves_disputed_digits_operators_and_decimal_separators(first, other):
    assert notebook._question_signature(first) != notebook._question_signature(other)


@pytest.mark.parametrize('review', ['same', 'digit_change', 'initial_uncertainty', 'role_change'])
def test_independent_physical_row_breaks_require_identical_ordered_content(monkeypatch, review):
    first = {'kind': 'WORK', 'lines': [
        {'text': 'Bài giải:'}, {'text': 'Số tiền lãi là:'},
        {'text': '35 000 000 × 7,4 : 100 = 2 590 000 (đồng)', 'role': 'EQUATION'},
        {'text': 'Tổng số tiền gửi và tiền lãi sau một năm là:',
         'uncertain': review == 'initial_uncertainty'}]}
    second = {'kind': 'WORK', 'lines': [*first['lines'][:3],
        {'text': 'Tổng số tiền gửi và tiền lãi sau một'}, {'text': 'năm là:'}]}
    if review == 'digit_change':
        second['lines'][2] = {'text': '35 000 000 × 7,4 : 100 = 2 580 000 (đồng)', 'role': 'EQUATION'}
    elif review == 'role_change':
        second['lines'][-1]['role'] = 'EQUATION'
    boxes = [(20, 20 + i * 150, 800, 100 + i * 150) for i in range(5)]
    monkeypatch.setattr(notebook, 'handwriting_rows', lambda _: boxes)
    monkeypatch.setattr('app.recognition.text_detector.detect_text_regions', lambda _: [])
    cloud = AsyncMock(side_effect=[first, second])
    monkeypatch.setattr(notebook, '_generate', cloud)
    result = run(notebook.inspect_notebook(image_bytes((1000, 1000))))
    accepted = review in ('same', 'initial_uncertainty')
    assert cloud.await_count == 2
    assert [line.text for line in result.lines] == [line['text'] for line in (second if accepted else first)['lines']]
    assert [line.box for line in result.lines] == (boxes if accepted else [None] * 4)
    if accepted:
        assert all(line.uncertain is (review == 'initial_uncertainty') for line in result.lines[-2:])
    else:
        assert all(line.uncertain for line in result.lines)
    assert first['lines'][-1]['text'] == 'Tổng số tiền gửi và tiền lãi sau một năm là:'


@pytest.mark.parametrize('next_top', [100, 95])
def test_touching_ink_envelopes_cannot_be_presented_as_verified_row_geometry(monkeypatch, next_top):
    payload = {'kind': 'WORK', 'lines': [{'text': 'Bài giải:'}, {'text': 'Số tiền là:'}]}
    monkeypatch.setattr(notebook, 'handwriting_rows', lambda _: [(20, 20, 800, 100), (20, next_top, 800, 180)])
    monkeypatch.setattr(notebook, '_generate', AsyncMock(return_value=payload))
    result = run(notebook.inspect_notebook(image_bytes((1000, 1000))))
    assert [line.text for line in result.lines] == ['Bài giải:', 'Số tiền là:']
    assert all(line.box is None and line.uncertain for line in result.lines)


@pytest.mark.parametrize('heading', [
    'Bài 18: Đề-xi-mét vuông, mét vuông, mi-li-mét vuông',
    'Chương 2: Phân số', 'Tiết 7. Biểu thức chứa chữ',
])
def test_topic_heading_cannot_be_used_as_an_original_question(monkeypatch, heading):
    notes = [heading, '1dm² = 100cm²']
    payload = {'kind': 'PROBLEM', 'problemText': heading,
               'lines': [{'text': text} for text in notes]}
    monkeypatch.setattr(notebook, '_generate', AsyncMock(return_value=payload))
    result = run(notebook.inspect_notebook(image_bytes()))
    assert result.kind == 'WORK' and result.problemText == '' and result.needsProblem
    assert [line.text for line in result.lines] == notes
    assert payload['problemText'] == heading


@pytest.mark.parametrize('heading, equation', [
    ('Bài 3: Bài giải:', '35 000 000 x 7,4 : 100 = 2590 000 (đồng)'),
    ('Số tiền bán được là:', '18 000 000 : 5 × 2 = 7 200 000 (đồng)'),
    ('Kết quả phép tính là:', '92 : 4 = 22'),  # Preserve even a written wrong result.
])
def test_completed_numeric_work_cannot_become_an_original_question(monkeypatch, heading, equation):
    payload = {'kind': 'PROBLEM', 'problemText': heading + '\n' + equation,
               'lines': [{'text': heading}, {'text': equation, 'role': 'EQUATION'}]}
    original_problem = payload['problemText']
    monkeypatch.setattr(notebook, '_generate', AsyncMock(return_value=payload))
    result = run(notebook.inspect_notebook(image_bytes()))
    assert result.kind == 'WORK' and result.problemText == '' and result.needsProblem
    assert [line.text for line in result.lines] == [heading, equation]
    assert payload['problemText'] == original_problem


@pytest.mark.parametrize('question', ['x + 3 = 10', '□ + 3 = 10', 'Tìm x: x + 3 = 10', 'Tính 84 : 4.'])
def test_unsolved_tasks_are_kept_despite_an_equals_sign_or_additional_work(monkeypatch, question):
    lines = [{'text': question, 'role': 'EQUATION'}]
    if question.startswith('Tính'):
        lines.append({'text': '84 : 4 = 21', 'role': 'EQUATION'})
    payload = {'kind': 'PROBLEM', 'problemText': question, 'lines': lines}
    monkeypatch.setattr(notebook, '_generate', AsyncMock(return_value=payload))
    result = run(notebook.inspect_notebook(image_bytes()))
    assert result.problemText == question and not result.needsProblem


@pytest.mark.parametrize('question', [
    'Bài 18: Tính diện tích hình vuông cạnh 5 cm.',
    'Bài 2: 3/4 + 2/5', 'Bài 7: Có 5 con bò. Hỏi có bao nhiêu chân?',
    'Bài 3: Đổi 1 m² sang cm².', 'Bài 4: Viết các số chẵn nhỏ hơn 10.',
    'Bài 2: 5 - 2', 'Bài 2: 5 − 2', 'Bài 2: 5 × 2', 'Bài 2: 5 : 2',
    'Bài 2: a - b',
])
def test_numbered_actual_tasks_remain_original_questions(monkeypatch, question):
    payload = {'kind': 'PROBLEM', 'problemText': question,
               'lines': [{'text': question}]}
    monkeypatch.setattr(notebook, '_generate', AsyncMock(return_value=payload))
    result = run(notebook.inspect_notebook(image_bytes()))
    assert result.kind == 'PROBLEM' and result.problemText == question and not result.needsProblem


@pytest.mark.parametrize("hint", ["Em tính được 7 rồi nhân tiếp.", "Có mười bốn con bò khoang.", "Đáp số: 14", "49 : 7 = 7.", "14 chính là đáp số."])
def test_existing_values_cannot_be_repackaged_as_answers(hint):
    request = notebook.CoachRequest(workText="49 : 7 × 2 = 14 (con)", focusText="49 : 7 × 2 = 14 (con)", stage="CHECK_WORK")
    response = notebook.GuideResponse(stage="CHECK_WORK", hint=hint, question="Em sẽ kiểm tra lại như thế nào?")
    assert notebook.unsafe_coaching(response, request)


def test_other_steps_are_not_a_source_of_new_results():
    request = notebook.CoachRequest(workText="49 : 7 × 2 = 14\n49 - 14 = 35", focusText="49 : 7 × 2 = 14", stage="CHECK_WORK")
    response = notebook.GuideResponse(stage="CHECK_WORK", hint="Em hãy so với số 35.", question="Em sẽ kiểm tra ra sao?")
    assert notebook.unsafe_coaching(response, request)


def test_short_original_problem_does_not_break_safe_fallback(monkeypatch):
    monkeypatch.setattr(notebook, "_generate", AsyncMock(return_value={}))
    result = run(notebook.coach_notebook(notebook.CoachRequest(problemText="?", workText="49 : 7", stage="CHECK_WORK")))
    assert result.guarded and result.question


def test_coloured_rows_are_independent_nonoverlapping_and_in_full_coordinates():
    image = np.full((660, 900, 3), 245, np.uint8)
    for y in range(30, 660, 30):
        cv2.line(image, (0, y), (899, y), (210, 210, 210), 1)
    for y in (90, 190, 290, 390, 490, 590):
        cv2.putText(image, "49 : 7 x 2 = 14 con", (100, y), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (140, 40, 20), 3)
    boxes = handwriting_rows(image)
    assert len(boxes) == 6
    assert all(0 <= x1 < x2 <= 900 and 0 <= y1 < y2 <= 660 for x1, y1, x2, y2 in boxes)
    assert all(first[3] <= second[1] for first, second in zip(boxes, boxes[1:]))
    assert handwriting_rows(np.full((660, 900, 3), 255, np.uint8)) == []
