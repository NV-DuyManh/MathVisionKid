"""Worksheet regressions: exact first-request solutions without provider calls."""
from unittest.mock import AsyncMock
from fractions import Fraction
import pytest

from app.tutoring import lesson
from app.tutoring.short_math import verified_plan
from _lesson_test_data import step, mock_generation


CASES = [
    ('1 + 1 = ?', '2'),
    ('Tính: 7,5 + 9,86', '17.36'),
    ('Tính (12-3)*2 = ?', '18'),
    ('Tính 1/3 + 2/5', '11/15'),
    ('Tính 7,5 : 3', '2.5'),
    ('Câu 1. Cho các phân số sau 18/10; 32/500; 99/100; 51/1000. Có .... phân số thập phân. A. 1 B. 2 C. 3 D. 4', '3'),
    ('Câu 2. Số thập phân bằng với 0,85 là: A. 8,05 B. 0,850 C. 0,805 D. 0,580', '0,850'),
    ('Câu 3. Số thập phân “năm mươi lăm phẩy hai mươi hai” là: A. 55,202 B. 505,22 C. 505,202 D. 55,22', '55,22'),
    ('Câu 4. Điền vào chỗ chấm để: 1,7 km² = .... ha A. 170 B. 1700 C. 17 D. 17000', '170'),
    ('Câu 5. Hỗn số 2 5/100 chuyển thành phân số thập phân là: A. 7/100 B. 207/100 C. 250/100 D. 205/100', '205/100'),
    ('Câu 6. Kết quả của phép tính 17/25 + 32/15 là: A. 49/40 B. 211/75 C. 211/40 D. 49/75', '211/75'),
    ('Đổi 1,7 km² sang ha.', '170'),
    ('25 cm = ... m', '0.25'),
]


@pytest.mark.asyncio
@pytest.mark.parametrize('source, answer', CASES)
async def test_short_task_one_step_checked_without_provider(source, answer, monkeypatch):
    monkeypatch.setattr('app.tutoring.catalog.load_plan', lambda request: None)
    monkeypatch.setattr('app.tutoring.catalog.save_plan', lambda *args: None)
    provider = AsyncMock(side_effect=AssertionError('Exact exercise must not call a provider'))
    monkeypatch.setattr(lesson, 'generate_plan', provider)
    request = lesson.LessonRequest(owner='short-math-pupil', problemText=source, problemConfirmed=True,
                                  guidedUnderstanding=True, startWithReading=True)
    response = await lesson.start_lesson(request)
    assert response.understandingSteps == 0 and len(response.outline) == 1
    assert not response.preparingMath and response.step.kind == 'MATH'
    assert not response.conclusion
    # Wrong attempts stay on the same task and never reveal another task's answer.
    wrong = lesson.answer_lesson(lesson.TurnRequest(owner=request.owner, sessionId=response.sessionId, revision=0, answer='-999999'))
    assert wrong.status == 'TRY_AGAIN' and wrong.revision == 0
    result = lesson.answer_lesson(lesson.TurnRequest(owner=request.owner, sessionId=response.sessionId, revision=0, answer=answer))
    assert result.status == 'COMPLETE' and len(result.completed) == 1
    assert result.conclusion and result.completed[0].answer
    if source in {'Tính: 7,5 + 9,86', '25 cm = ... m', 'Tính 7,5 : 3'}:
        assert result.completed[0].answer == answer.replace('.', ',')
        assert result.conclusion.startswith('Đáp số: ' + answer.replace('.', ','))
    assert not provider.called


@pytest.mark.parametrize('source', [
    '1+1 = 3', '1+1 = 2', '1/0 = ?', '2**99 = ?',
    '1+1 = ? Câu 2: 3+4 = ?', 'Tính 1+1 nếu số đầu là số âm.',
    '1 m² = ... kg', '1,7 km² = ... ha. Sau đó cộng thêm 3 ha.',
    'Số thập phân bằng với 0,85 là: A. 0,850 B. 0,85 C. 8,5 D. 0,805',
    'Số thập phân bằng với 0,85 là: A. 0,8 B. 0,805 C. 8,5 D. 0,580',
    'Cho các phân số sau 1/0; 2/10. Có ... phân số thập phân. A. 1 B. 2 C. 3 D. 4',
    'Hỗn số 2 5/100 chuyển thành phân số thập phân là: A. 41/20 B. 207/100 C. 250/100 D. 7/100',
    'Hỗn số 2 5/100 chuyển thành phân số thập phân là: A. 205/100 B. 2050/1000 C. 250/100 D. 7/100',
    'Số thập phân “năm mươi lăm phẩy hai nhăm hai” là: A. 55,202 B. 505,22 C. 505,202 D. 55,22',
    '[?]+1=?',
])
def test_unsupported_or_inconsistent_source_keeps_independent_review(source):
    assert verified_plan(source) is None


def test_decimal_fraction_means_original_denominator_not_convertibility():
    source = 'Cho các phân số sau 1/2; 2/5; 1/10; 2/100. Có ... phân số thập phân. A. 1 B. 2 C. 3 D. 4'
    plan = verified_plan(source)
    assert plan['steps'][0]['correctChoice'] == '2'


def test_mixed_number_selects_decimal_fraction_form_even_if_reduced_value_matches():
    source = 'Hỗn số 2 5/100 chuyển thành phân số thập phân là: A. 41/20 B. 207/100 C. 250/100 D. 205/100'
    assert verified_plan(source)['steps'][0]['correctChoice'] == '205/100'


@pytest.mark.parametrize('reading, options, expected', [
    ('một phẩy không trăm linh năm', ['1,5', '1,005', '1,05', '1,0005'], '1,005'),
    ('một phẩy không trăm hai mươi hai', ['1,22', '1,0022', '1,022', '1,202'], '1,022'),
    ('một trăm phẩy không năm', ['100,5', '100,005', '100,05', '100,0005'], '100,05'),
    ('một phẩy không không năm', ['1,5', '1,005', '1,05', '1,0005'], '1,005'),
])
def test_fractional_reading_keeps_leading_zero_places(reading, options, expected):
    source = f'Số thập phân “{reading}” là: ' + ' '.join(f'{label}. {option}' for label, option in zip('ABCD', options))
    data = verified_plan(source)
    assert data is not None
    plan = lesson.Plan.model_validate(data)
    lesson.validate_plan(plan, lesson.LessonRequest(owner='reading-proof', problemText=source, problemConfirmed=True))
    assert plan.steps[0].correctChoice == expected


def test_empty_reading_is_unsupported_not_a_runtime_error():
    assert verified_plan('Số thập phân “   phẩy     ” là: A. 0,1 B. 0,2 C. 0,3 D. 0,4') is None


@pytest.mark.parametrize('left,right', [(a, b) for a in range(0, 20, 3) for b in range(1, 10, 2)])
def test_short_arithmetic_proof_handles_new_operands_not_example_lookup(left, right):
    for symbol, expected in [('+', Fraction(left + right)), ('-', Fraction(left - right)),
                             ('×', Fraction(left * right)), ('÷', Fraction(left, right))]:
        source = f'Bài 9: (2 điểm) Tính: {left} {symbol} {right} = ?'
        data = verified_plan(source)
        plan = lesson.Plan.model_validate(data)
        lesson.validate_plan(plan, lesson.LessonRequest(owner='short-proof', problemText=source, problemConfirmed=True))
        assert len(plan.steps) == 1 and lesson.calculate_exact(plan.steps[0].expression) == expected


@pytest.mark.asyncio
async def test_unrecognized_short_choice_can_pass_independent_review_without_a_fake_calculation(monkeypatch):
    source = 'Chọn số lớn nhất trong các số sau: A. 0,5 B. 0,85 C. 0,75 D. 0,8'
    candidate = dict(topic='So sánh số thập phân', goal='Chọn số lớn nhất.', finalAnswerStep=0,
                     steps=[step(title='So sánh các số', choices=['0,5', '0,85', '0,75', '0,8'], correctChoice='0,85')])
    cloud = mock_generation(monkeypatch, candidate, [dict(stepIndex=0, answer='0,85', unit='')])
    result = await lesson.start_lesson(lesson.LessonRequest(owner='choice-review', problemText=source, problemConfirmed=True))
    assert len(result.outline) == 1 and result.step.choices == candidate['steps'][0]['choices']
    assert cloud.await_count == 2 and not result.conclusion


@pytest.mark.asyncio
async def test_choice_key_cannot_disagree_with_independent_review(monkeypatch):
    source = 'Chọn số lớn nhất trong các số sau: A. 0,5 B. 0,85 C. 0,75 D. 0,8'
    candidate = dict(topic='So sánh số thập phân', goal='Chọn số lớn nhất.', finalAnswerStep=0,
                     steps=[step(title='So sánh các số', choices=['0,5', '0,85', '0,75', '0,8'], correctChoice='0,5')])
    review = dict(sourceFaithful=True, mathematicsCorrect=True, answersQuestion=True, teachingClear=True,
                  results=[dict(stepIndex=0, answer='0,85', unit='')])
    cloud = AsyncMock(side_effect=[candidate, review, candidate, review]);monkeypatch.setattr(lesson, '_generate', cloud)
    with pytest.raises(lesson.TutorUnavailable):
        await lesson.start_lesson(lesson.LessonRequest(owner='choice-review', problemText=source, problemConfirmed=True))
    assert cloud.await_count == 4
