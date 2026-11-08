"""Manually transcribed ground truth from the owner's supplied exam, not model labels."""
from unittest.mock import AsyncMock

import pytest

from app.tutoring import lesson
from app.tutoring.short_math import verified_plan


CASES = [
    ('Câu 1. Cho các phân số sau 18/10; 32/500; 99/100; 51/1000. Có .... phân số thập phân. A. 1 B. 2 C. 3 D. 4', '3'),
    ('Câu 2. Số thập phân bằng với 0,85 là: A. 8,05 B. 0,850 C. 0,805 D. 0,580', '0,850'),
    ('Câu 3. Số thập phân “năm mươi lăm phẩy hai mươi hai” là: A. 55,202 B. 505,22 C. 505,202 D. 55,22', '55,22'),
    ('Câu 4. Điền vào chỗ chấm để: 1,7 km² = .... ha A. 170 B. 1 700 C. 17 D. 17 000', '170'),
    ('Câu 5. Hỗn số 2 5/100 chuyển thành phân số thập phân là: A. 7/100 B. 207/100 C. 250/100 D. 205/100', '205/100'),
    ('Câu 6. Kết quả của phép tính 17/25 + 32/15 là: A. 49/40 B. 211/75 C. 211/40 D. 49/75', '211/75'),
    ('Câu 7. Bác An thu hoạch được 2 tấn 35 kg hạt điều và hạnh nhân. Biết rằng số lượng hạnh nhân chiếm 2/5 tổng số hạt điều và hạnh nhân thu hoạch được. Vậy, bác An thu hoạch được số ki – lô – gam hạnh nhân là: A. 814 kg B. 914 kg C. 1 221 kg D. 1 231 kg', '814'),
    ('Câu 8. Chu vi của hình chữ nhật là 48 dm. Hỏi diện tích mảnh đất là bao nhiêu dm². Biết chiều dài hơn chiều rộng là 6 dm. A. 135 B. 576 C. 432 D. 252', '135'),
    ('15 dm 2 cm = ........ dm', '15.2'),
    ('9 tấn 4 kg = ........ tấn', '9.004'),
    ('5 m² 26 dm² = ........ m²', '5.26'),
    ('7 km² 5 ha = ........ ha', '705'),
]


def notation(source, variant):
    import re
    if variant == 'grouped':
        return re.sub(r'(\d+)\s*/\s*(\d+)', r'(\1)/(\2)', source)
    if variant == 'unicode':
        return source.replace('/', '⁄').replace('1 700', '1\u202f700').replace('17 000', '17\u00a0000')
    if variant == 'lowercase':
        return re.sub(r'\b[A-D][.]', lambda match: match[0].lower(), source)
    return source


@pytest.mark.parametrize('source,answer', CASES)
@pytest.mark.parametrize('variant', ['literal', 'grouped', 'unicode', 'lowercase'])
@pytest.mark.asyncio
async def test_each_exam_task_finishes_exactly_without_cloud(source, answer, variant, monkeypatch):
    source = notation(source, variant)
    provider = AsyncMock(side_effect=AssertionError('Supported exam must use checked arithmetic, not cloud'))
    monkeypatch.setattr(lesson, 'generate_plan', provider)
    monkeypatch.setattr('app.tutoring.catalog.load_plan', lambda request: None)
    monkeypatch.setattr('app.tutoring.catalog.save_plan', lambda *args: None)
    request = lesson.LessonRequest(owner='exam-regression', problemText=source, problemConfirmed=True)
    response = await lesson.start_lesson(request)
    for index in range(len(response.outline)):
        session = lesson._sessions[response.sessionId]
        step = session.plan.steps[index]
        value = step.correctChoice if step.choices else str(lesson.calculate_exact(lesson.expression_at(step, session.answers)))
        if index == len(response.outline)-1:
            assert lesson.calculate_exact(value.replace(',', '.')) == lesson.calculate_exact(answer.replace(',', '.'))
        wrong = lesson.answer_lesson(lesson.TurnRequest(owner=request.owner, sessionId=response.sessionId,
            revision=response.revision, answer='-999999'))
        assert wrong.status == 'TRY_AGAIN' and wrong.revision == response.revision
        response = lesson.answer_lesson(lesson.TurnRequest(owner=request.owner, sessionId=response.sessionId,
            revision=response.revision, answer=value))
    assert response.status == 'COMPLETE'
    provider.assert_not_called()


@pytest.mark.parametrize('source', [
    '15 dm 2 kg = ... dm', '9 tấn 4 kg = ... m', '15 dm 2 cm = ... dm. Thêm 3 dm nữa.',
    '5 m² 26 dm² = ... m². Câu 2: 7 km² 5 ha = ... ha',
    'Chu vi của hình chữ nhật là 12 dm. Hỏi diện tích mảnh đất là bao nhiêu dm². Biết chiều dài hơn chiều rộng là 8 dm. A. 10 B. 20 C. 30 D. 40',
])
def test_extra_or_inconsistent_data_not_silently_accepted(source):
    assert verified_plan(source) is None


def test_fraction_choice_teaches_common_denominator_not_ordinary_division_order():
    plan = verified_plan(CASES[5][0])
    assert 'mẫu chung' in plan['steps'][0]['initialGuidance'][1]


def test_measurement_labels_are_readable_and_a_mixed_fraction_is_never_joined_as_thousands():
    from app.tutoring.choice_source import numeric_notation
    assert verified_plan(CASES[9][0])['steps'][0]['unit'] == 'tấn'
    assert numeric_notation('Hỗn số 2 500/1000') == 'Hỗn số 2 500/1000'
