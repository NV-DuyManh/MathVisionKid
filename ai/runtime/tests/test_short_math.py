"""Worksheet regressions: exact first-request solutions without provider calls."""
from unittest.mock import AsyncMock
from fractions import Fraction
import pytest

from app.tutoring import lesson


def test_blank_working_rows_and_explicit_mcq_instruction_do_not_require_cloud():
    from app.tutoring.short_math import verified_plan
    source = 'Câu 2. Tính bằng cách thuận tiện:\n724×63+724×37-4500 =\n=\n=……'
    raw = verified_plan(source)
    assert raw is not None
    plan = lesson.Plan.model_validate(raw)
    lesson.validate_plan(plan,lesson.LessonRequest(owner='layout',problemText=source,problemConfirmed=True),lesson.formula_constants(source))
    assert lesson.calculate_exact(plan.steps[0].expression) == 67900
    assert verified_plan(source + '\nSau đó cộng thêm 5.') is None
    mcq = ('Câu 1: Khoanh vào chữ cái trước câu trả lời đúng.\n'
        'Hai mươi bốn đơn vị, một phần mười, tám phần trăm được viết là:\nA. 24,18\nB. 24,108\nC. 24,018\nD. 24,0108')
    assert verified_plan(mcq)['steps'][0]['correctChoice'] == '24,18'
from app.tutoring.short_math import verified_plan
from _lesson_test_data import step, mock_generation


CASES = [
    ('Câu 2. Tính giá trị của biểu thức. 1 (1)/(3) + (5)/(8) : (7)/(2)', '127/84'),
    ('Tính 5/8 ÷ 7/2', '5/28'),
    ('Tính 1/2 : 3/4 : 5/6', '4/5'),
    ('Tính 2 : 3/4 * 5', '40/3'),
    ('Tính -1/2 : 3/4', '-2/3'),
    ('Tính (1/2 + 3/4) : (5/6 - 1/3)', '5/2'),
    ('Tính 8/4/2', '1'),
    ('Tính 8/4/2 : 3/4', '4/3'),
    ('Bài 2 (2 điểm): Tính bằng cách thuận tiện nhất: 11,2+12,3+13,4-1,2-2,3-10,4', '23'),
    ('Câu 3. Viết số thập phân thích hợp vào chỗ chấm. 5 l 35 ml = ………… l', '5.035'),
    ('Câu 3. Viết số thập phân thích hợp vào chỗ chấm. 14 cm² 6 mm² = ………… cm²', '14.06'),
    ('Câu 3. Viết số thập phân thích hợp vào chỗ chấm. 382 mm² = ………… dm²', '0.0382'),
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


@pytest.mark.asyncio
async def test_divisor_fraction_is_not_split_and_previous_wrong_result_is_rejected(monkeypatch):
    source = 'Câu 2. Tính giá trị của biểu thức. 1 (1)/(3) + (5)/(8) : (7)/(2)'
    monkeypatch.setattr('app.tutoring.catalog.load_plan', lambda _: None)
    monkeypatch.setattr('app.tutoring.catalog.save_plan', lambda *args: None)
    monkeypatch.setattr(lesson, 'generate_plan', AsyncMock(side_effect=AssertionError('Exact proof required')))
    response = await lesson.start_lesson(lesson.LessonRequest(owner='fraction-division', problemText=source, problemConfirmed=True))
    wrong = lesson.answer_lesson(lesson.TurnRequest(owner='fraction-division', sessionId=response.sessionId,
                                                  revision=0, answer='463/336'))
    assert wrong.status == 'TRY_AGAIN' and not wrong.conclusion
    correct = lesson.answer_lesson(lesson.TurnRequest(owner='fraction-division', sessionId=response.sessionId,
                                                    revision=0, answer='127/84'))
    assert correct.status == 'COMPLETE'


def test_fraction_division_checks_original_mcq_options():
    source = 'Kết quả phép tính 5/8 : 7/2 là: A. 5/28 B. 5/112 C. 35/16 D. 7/2'
    assert verified_plan(source)['steps'][0]['correctChoice'] == '5/28'
    assert verified_plan(source.replace('5/28', '5/27')) is None


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


@pytest.mark.parametrize('source,expected', [
    ('Số thích hợp điền vào chỗ chấm 8 km² 5 ha = ... km² A. 8,5 B. 850 C. 8,05 D. 8,005', '8,05'),
    ('Số thập phân thích hợp viết vào chỗ chấm của 15l 78ml = ....... l là: A. 15,78 B. 157,8 C. 15,078 D. 1,578', '15,078'),
    ('Bài 1: (1 điểm) Điền số hoặc đơn vị thích vào chỗ chấm: 8 tấn 3 kg = …… tấn', '8003/1000'),
    ('Điền số hoặc đơn vị thích hợp vào chỗ chấm: 3 ha 26 m² = ………… ha', '15013/5000'),
])
def test_compound_measurement_keeps_the_full_instruction_and_checks_options(source, expected):
    plan = lesson.Plan.model_validate(verified_plan(source))
    lesson.validate_plan(plan, lesson.LessonRequest(owner='units', problemText=source, problemConfirmed=True), lesson.formula_constants(source))
    step = plan.steps[0]
    actual = step.correctChoice if step.choices else str(lesson.calculate_exact(step.expression))
    assert actual == expected


@pytest.mark.parametrize('source', [
    'Số thích hợp điền vào chỗ chấm 8 km² 5 ha = ... km² A. 8,05 B. 8,050 C. 8 D. 850',
    'Điền số hoặc đơn vị thích hợp vào chỗ chấm: 3 ha 26 kg = ………… ha',
    'Điền số hoặc đơn vị thích hợp vào chỗ chấm: 3 ha 26 m² = ………… ha rồi chia đôi.',
])
def test_compound_measurement_duplicate_choices_or_extra_conditions_are_not_proven(source):
    assert verified_plan(source) is None


@pytest.mark.parametrize('source,expected', [
    ('Câu 2: (1 điểm) Đúng ghi Đ, sai ghi S: 7 cm² 6 mm² = 7,06 cm²', 'Đúng'),
    ('Đúng ghi Đ, sai ghi S: 4 l 45 ml = 4,45 l', 'Sai'),
    ('Đúng ghi Đ, sai ghi S: 9,452 làm tròn đến hàng phần trăm là 9,46', 'Sai'),
    ('Đúng ghi Đ, sai ghi S: 45,905 làm tròn đến số tự nhiên gần nhất là 46', 'Đúng'),
    ('Đúng ghi Đ, sai ghi S: 9,455 làm tròn đến hàng phần trăm là 9,46', 'Đúng'),
    ('Dấu thích hợp điền vào chỗ chấm 2 km² 5ha ....... 2,5 km² là: A. > B. < C. = D. Không xác định được', '<'),
    ('Dấu thích hợp điền vào chỗ chấm 2 m 5cm ....... 2,05 m là: A. > B. < C. = D. Không xác định được', '='),
    ('Trong các số đo khối lượng: 5,14 tấn; 5 tấn 40kg; 5,05 tấn; 5,5tấn, số đo bé nhất là: A. 5,14 tấn B. 5 tấn 40 kg C. 5,05 tấn D. 5,5 tấn', '5 tấn 40 kg'),
])
@pytest.mark.asyncio
async def test_explicit_measurement_and_truth_tasks_never_start_a_provider(source, expected, monkeypatch):
    monkeypatch.setattr('app.tutoring.catalog.load_plan', lambda _: None)
    monkeypatch.setattr('app.tutoring.catalog.save_plan', lambda *args: None)
    monkeypatch.setattr(lesson, 'generate_plan', AsyncMock(side_effect=AssertionError('Exact proof required')))
    response = await lesson.start_lesson(lesson.LessonRequest(owner='units', problemText=source, problemConfirmed=True))
    assert response.step.choices and response.status == 'READY'
    wrong = next(choice for choice in response.step.choices if choice != expected)
    retry = lesson.answer_lesson(lesson.TurnRequest(owner='units', sessionId=response.sessionId, revision=response.revision, answer=wrong))
    assert retry.stepIndex == 0 and not retry.conclusion
    complete = lesson.answer_lesson(lesson.TurnRequest(owner='units', sessionId=response.sessionId, revision=retry.revision, answer=expected))
    assert complete.status == 'COMPLETE' and complete.completed[-1].answer == expected


@pytest.mark.parametrize('source', [
    '7 cm² 6 mm² = 7,06 cm²',  # A printed equation alone is not a true/false task.
    'Đúng ghi Đ, sai ghi S: 7 cm² 6 kg = 7,06 cm²',
    'Đúng ghi Đ, sai ghi S: 9,452 làm tròn là 9,46',
    'Đúng ghi Đ, sai ghi S: 9,452 làm tròn đến hàng phần trăm là 9,46 rồi cộng 1.',
    'Dấu thích hợp điền vào chỗ chấm 2 km² 5ha ....... 2,5 kg là: A. > B. < C. = D. Không xác định được',
    'Trong các số đo khối lượng: 5,14 tấn; 5 tấn 40kg; 5,05 tấn; 5,5tấn, số đo bé nhất là: A. 1 kg B. 2 kg C. 3 kg D. 4 kg',
    'Trong các số đo khối lượng: 5 tấn; 5000 kg; 6 tấn; 7 tấn, số đo bé nhất là: A. 5 tấn B. 5000 kg C. 6 tấn D. 7 tấn',
])
def test_unproven_measurements_and_ambiguous_assertions_keep_review(source):
    assert verified_plan(source) is None


def test_trailing_diagram_description_is_preserved_as_source_not_option_d():
    from app.tutoring.choice_source import split_choices
    description = 'Hình vẽ gồm hai hình ngũ giác chia thành năm phần bằng nhau.'
    source = 'Hỗn số biểu diễn phần tô màu trong hình là:\nA. 1 2/5\nB. 5 2/3\nC. 2 2/3\nD. 2 3/5\n' + description
    stem, choices = split_choices(source, allow_statement=True)
    assert stem.endswith(description) and choices == ['1 2/5', '5 2/3', '2 2/3', '2 3/5']
    # Merely mentioning a diagram is not an exact mathematical proof of it.
    assert verified_plan(source) is None


@pytest.mark.parametrize('source,expected', [
    ('Bài 2: (2 điểm) Tính: 4 (3)/(5) - 2 (1)/(4) = …………', '47/20'),
    ('Bài 2: (2 điểm) Tính: 2 (2)/(3) : 1 (2)/(5) = …………', '40/21'),
])
def test_confirmed_mixed_number_with_repeated_blank_glyphs_uses_exact_arithmetic(source, expected):
    plan = lesson.Plan.model_validate(verified_plan(source))
    lesson.validate_plan(plan, lesson.LessonRequest(owner='mixed', problemText=source, problemConfirmed=True), lesson.formula_constants(source))
    assert str(lesson.calculate_exact(plan.steps[0].expression)) == expected


def test_missing_mixed_number_whole_part_separator_is_not_inferred_from_the_answer():
    assert verified_plan('Tính: 4(3)/(5) - 2(1)/(4) = …………') is None
    assert verified_plan(r'Tính: 4\frac{3}{5} - 2\frac{1}{4} = ?') is None
    from app.tutoring.choice_source import numeric_notation
    assert numeric_notation('4(3)/(5)') == '4(3)/(5)'
    assert numeric_notation('4 (3)/(5)') == '4 3/5'


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
