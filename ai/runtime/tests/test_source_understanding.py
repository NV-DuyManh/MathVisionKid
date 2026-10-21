"""Comprehension is source-based, server-checked, and precedes arithmetic."""
import json
from unittest.mock import AsyncMock

import pytest

from app.tutoring import lesson
from _lesson_test_data import step, mock_generation


def turn(response, answer='', owner='student-a', hint=False):
    return lesson.answer_lesson(lesson.TurnRequest(owner=owner, sessionId=response.sessionId,
        revision=response.revision, answer=answer, hint=hint))


@pytest.fixture(autouse=True)
def reset_sessions(monkeypatch):
    lesson._sessions.clear()
    monkeypatch.setattr(lesson.secrets, 'choice', lambda values: values[0])


@pytest.mark.asyncio
@pytest.mark.parametrize('name,first,extra', [('Mai', 18, 7), ('Bình', 24, 9)])
async def test_source_choices_are_checked_before_math_without_leaking_answers(monkeypatch, name, first, extra):
    fact = f'{name} có {first} nhãn vở'
    question = 'Hỏi bạn có tất cả bao nhiêu nhãn vở?'
    source = f'{fact}, được tặng thêm {extra} nhãn vở. {question}'
    plan = lesson.Plan(topic='Nhãn vở', goal='Tìm số nhãn vở.', finalAnswerStep=1, steps=[
        step(title='Chọn cách tính', choices=['Gộp hai nhóm', 'Bớt một nhóm'], correctChoice='Gộp hai nhóm'),
        step(title='Tính số nhãn vở', expression=f'{first}+{extra}', unit='nhãn vở'),
    ])
    monkeypatch.setattr(lesson, 'generate_plan', AsyncMock(return_value=plan))
    response = await lesson.start_lesson(lesson.LessonRequest(owner='student-a', problemText=source,
        problemConfirmed=True, guidedUnderstanding=True))
    assert response.understandingSteps == 3 and len(response.outline) == 5
    assert response.step.kind == 'UNDERSTAND' and response.step.expression == ''
    assert all('Viết phép tính' not in item and 'trong ngoặc' not in item for item in response.step.guidance)
    assert set(response.step.choices) == {fact, question}
    assert 'correctChoice' not in response.model_dump_json()
    assert str(first + extra) not in response.model_dump_json(exclude={'sessionId'})
    wrong = turn(response, question)
    assert wrong.status == 'TRY_AGAIN' and wrong.revision == 0
    with pytest.raises(lesson.LessonExpired):
        turn(response, fact, owner='student-b')
    response = turn(wrong, fact)
    with pytest.raises(lesson.StaleTurn):
        turn(wrong, fact)
    assert response.step.kind == 'UNDERSTAND'
    response = turn(response, question)
    assert fact in response.step.question and response.step.choices == ['Đúng', 'Sai']
    assert turn(response, 'Sai').status == 'TRY_AGAIN'
    hint = turn(response, hint=True)
    assert str(first + extra) not in hint.model_dump_json(exclude={'sessionId'})
    response = turn(hint, 'Đúng')
    assert response.step.kind == 'MATH' and response.stepIndex == 3
    response = turn(response, 'Gộp hai nhóm')
    response = turn(response, str(first + extra))
    assert response.status == 'COMPLETE' and response.conclusion == f'Đáp số: {first + extra} nhãn vở.'
    assert [item.kind for item in response.completed] == ['UNDERSTAND'] * 3 + ['MATH'] * 2


@pytest.mark.asyncio
async def test_prepend_shifts_checked_fraction_dependencies_without_revealing_future_answers(monkeypatch):
    source = 'Một tấm vải dùng 1/3 để may áo, dùng 1/4 để may túi. Hỏi còn lại bao nhiêu phần tấm vải?'
    plan = lesson.Plan(topic='Tấm vải', goal='Tìm phần vải còn lại.', finalAnswerStep=1, steps=[
        step(title='Tính phần đã dùng', expression='1/3+1/4', fractionNotation=True),
        step(title='Tính phần còn lại', expression='1-{s0}', fractionNotation=True,
             guidance=['Phần đã dùng là {s0}. Cần bớt phần đã dùng khỏi toàn bộ tấm vải.',
                       'Đối chiếu những phần bằng nhau trước khi tính.', 'Em viết phép trừ rồi tự tính phần còn lại.']),
    ])
    monkeypatch.setattr(lesson, 'generate_plan', AsyncMock(return_value=plan))
    response = await lesson.start_lesson(lesson.LessonRequest(owner='student-a', problemText=source,
        problemConfirmed=True, guidedUnderstanding=True))
    for answer in ['Một tấm vải dùng 1/3 để may áo', 'Hỏi còn lại bao nhiêu phần tấm vải?', 'Đúng']:
        assert '7/12' not in response.model_dump_json(exclude={'sessionId'})
        assert '5/12' not in response.model_dump_json(exclude={'sessionId'})
        response = turn(response, answer)
    response = turn(response, '7/12')
    assert '7/12' in response.step.expression and '5/12' not in response.model_dump_json(exclude={'sessionId'})
    response = turn(response, '5/12')
    assert response.status == 'COMPLETE' and response.completed[-1].answer == '5/12'


@pytest.mark.parametrize('source', [
    'Một tấm vải dùng 1/3 để may áo.',
    'Có 12 bút. Hỏi có bao nhiêu? Tính số còn lại.',
    'Có 12 bút không? Hỏi có tất cả bao nhiêu bút?',
    'Có [?] bút. Hỏi có tất cả bao nhiêu bút?',
    'Có 12 bút. ' + 'Hỏi ' + 'bút ' * 30 + '?',
])
def test_extracting_comprehension_never_guesses_unsupported_or_ambiguous_sources(source):
    with pytest.raises(ValueError):
        lesson.source_understanding(source)


@pytest.mark.asyncio
@pytest.mark.parametrize('source,expression,answer', [
    ('Tính 1 : 3.', '1/3', '1/3'),
    ('12+5', '12+5', '17'),
    ('Mai có 12 bút, được thêm 5 bút; Mai có tất cả bao nhiêu bút?', '12+5', '17'),
    ('Mai có 12 bút, được thêm 5 bút. Hỏi sau khi nhận thêm những chiếc bút được cho, '
     'tổng số bút mà Mai có lúc này, tính cả bút ban đầu và bút được thêm, là bao nhiêu?', '12+5', '17'),
])
async def test_unsupported_comprehension_retains_standard_reviewed_math(monkeypatch, source, expression, answer):
    candidate = dict(topic='Tìm kết quả', goal='Tính theo đề đã xác nhận.', finalAnswerStep=1, steps=[
        step(title='Chọn cách làm', choices=['Làm theo đề', 'Đổi dữ kiện'], correctChoice='Làm theo đề'),
        step(title='Tính kết quả', expression=expression),
    ])
    cloud = mock_generation(monkeypatch, candidate)
    response = await lesson.start_lesson(lesson.LessonRequest(owner='student-a', problemText=source,
        problemConfirmed=True, guidedUnderstanding=True))
    assert cloud.await_count == 2
    assert cloud.await_args_list[0].args[0] == lesson.PLAN_PROMPT
    assert cloud.await_args_list[1].args[0] == lesson.REVIEW_PROMPT
    assert json.loads(cloud.await_args_list[1].args[1])['problemText'] == source
    assert response.understandingSteps == 0 and len(response.outline) == 2 and response.step.kind == 'MATH'
    assert response.summary is None
    assert turn(turn(response, 'Làm theo đề'), answer).status == 'COMPLETE'


@pytest.mark.asyncio
async def test_multiple_explicit_questions_keep_all_independently_reviewed_results(monkeypatch):
    source = 'Có 12 bút đỏ và 5 bút xanh. Hỏi có tất cả bao nhiêu bút? Tính số bút đỏ nhiều hơn số bút xanh.'
    candidate = dict(topic='Số bút', goal='Tìm tổng và hiệu số bút.', finalAnswerStep=None, steps=[
        step(title='Tìm tổng số bút', expression='12+5', unit='bút'),
        step(title='Tìm số bút nhiều hơn', expression='12-5', unit='bút'),
    ])
    cloud = mock_generation(monkeypatch, candidate, [dict(stepIndex=0, answer='17', unit='bút'),
                                                   dict(stepIndex=1, answer='7', unit='bút')])
    response = await lesson.start_lesson(lesson.LessonRequest(owner='student-a', problemText=source,
        problemConfirmed=True, guidedUnderstanding=True))
    assert cloud.await_count == 2 and response.understandingSteps == 0
    assert turn(turn(response, '17'), '7').status == 'COMPLETE'


@pytest.mark.asyncio
@pytest.mark.parametrize('changes', [
    {'problemText': 'Có [?] bút. Hỏi có tất cả bao nhiêu bút?'},
    {'problemConfirmed': False}, {'workText': '12 + [?]', 'workConfirmed': True},
])
async def test_comprehension_fallback_never_bypasses_confirmation_or_unread_symbols(monkeypatch, changes):
    generate = AsyncMock()
    monkeypatch.setattr(lesson, 'generate_plan', generate)
    values = dict(owner='student-a', problemText='Tính 12+5.', problemConfirmed=True, guidedUnderstanding=True)
    with pytest.raises(ValueError):
        await lesson.start_lesson(lesson.LessonRequest(**{**values, **changes}))
    generate.assert_not_called()


@pytest.mark.asyncio
async def test_unsupported_comprehension_still_propagates_failed_math_planning(monkeypatch):
    cloud = AsyncMock(return_value={'unavailable': True})
    monkeypatch.setattr(lesson, '_generate', cloud)
    with pytest.raises(lesson.TutorUnavailable):
        await lesson.start_lesson(lesson.LessonRequest(owner='student-a', problemText='Có 12 bút không?',
            problemConfirmed=True, guidedUnderstanding=True))
    assert cloud.await_count == 1


@pytest.mark.asyncio
async def test_unsupported_comprehension_never_bypasses_independent_math_review(monkeypatch):
    candidate = dict(topic='Tính', goal='Tìm kết quả.', finalAnswerStep=1, steps=[
        step(title='Chọn cách làm', choices=['Gộp', 'Bớt'], correctChoice='Gộp'),
        step(title='Tính tổng', expression='12+5'),
    ])
    rejected = dict(sourceFaithful=False, mathematicsCorrect=False, answersQuestion=False,
                    teachingClear=False, results=[], issues=['Không khớp đề.'])
    cloud = AsyncMock(side_effect=[candidate, rejected, candidate, rejected])
    monkeypatch.setattr(lesson, '_generate', cloud)
    with pytest.raises(lesson.TutorUnavailable):
        await lesson.start_lesson(lesson.LessonRequest(owner='student-a', problemText='12+5',
            problemConfirmed=True, guidedUnderstanding=True))
    assert cloud.await_count == 4
    assert all(call.args[0] == lesson.REVIEW_PROMPT for call in cloud.await_args_list[1::2])


def test_source_parser_preserves_decimal_comma_and_rejects_unbounded_outline():
    steps = lesson.source_understanding('Bình có 1,5 m dây, dùng 0,5 m dây. Hỏi còn bao nhiêu mét dây?')
    assert 'Bình có 1,5 m dây' in steps[0].choices
    with pytest.raises(ValueError):
        lesson.Plan(topic='Tính', goal='Tính', steps=[lesson.Step(**step(expression='1+1'))] * 7)


def test_nine_steps_keep_six_math_steps_and_exactly_three_opening_choices():
    source = 'Có 12 bút, thêm 5 bút. Hỏi có tất cả bao nhiêu bút?'
    math = lesson.Plan(topic='Số bút', goal='Tìm số bút.', finalAnswerStep=5,
        steps=[lesson.Step(**step(expression='12+5'))] * 6)
    plan = lesson.prepend_understanding(math, lesson.source_understanding(source))
    assert len(plan.steps) == 9 and plan.finalAnswerStep == 8
    with pytest.raises(ValueError):
        lesson.Plan(topic=plan.topic, goal=plan.goal, steps=plan.steps[1:])


@pytest.mark.parametrize('heading', ['Bài 6', 'Câu 2 (2 điểm)', 'Toán lớp 5', '(2 điểm)'])
def test_exercise_headings_and_marks_are_not_taught_as_numeric_facts(heading):
    fact = 'Lan có 12 bút'
    question = 'Hỏi Lan có tất cả bao nhiêu bút?'
    steps = lesson.source_understanding(f'{heading}\n{fact}, được tặng thêm 5 bút. {question}')
    assert set(steps[0].choices) == {fact, question}
    assert heading not in steps[2].question


def test_classroom_quantity_is_a_fact_even_when_it_starts_with_lop():
    fact = 'Lớp 5A có 36 học sinh'
    steps = lesson.source_understanding(f'{fact}, có 20 bạn nữ. Hỏi có bao nhiêu bạn nam?')
    assert fact in steps[0].choices


def test_heading_without_an_actual_numeric_fact_has_no_comprehension():
    with pytest.raises(lesson.UnderstandingUnsupported):
        lesson.source_understanding('Bài 6\nHỏi có tất cả bao nhiêu bút?')


@pytest.mark.asyncio
@pytest.mark.parametrize('claim_index,expected', [(0, 'Đúng'), (1, 'Sai')])
async def test_true_false_checks_the_quoted_source_role_in_both_directions(monkeypatch, claim_index, expected):
    fact = 'Mai có 12 bút'
    question = 'Hỏi Mai có tất cả bao nhiêu bút?'
    monkeypatch.setattr(lesson.secrets, 'choice', lambda values: values[claim_index])
    monkeypatch.setattr(lesson, 'generate_plan', AsyncMock(return_value=lesson.Plan(
        topic='Số bút', goal='Tìm số bút.', finalAnswerStep=1, steps=[
            step(choices=['Gộp', 'Bớt'], correctChoice='Gộp'), step(expression='12+5', unit='bút')
        ])))
    response = await lesson.start_lesson(lesson.LessonRequest(owner='student-a',
        problemText=f'{fact}, thêm 5 bút. {question}', problemConfirmed=True, guidedUnderstanding=True))
    response = turn(turn(response, fact), question)
    quote = fact if expected == 'Đúng' else question
    assert f'«{quote}»' in response.step.question
    assert response.step.choices == ['Đúng', 'Sai']
    assert all('trong mỗi lựa chọn' not in item for item in response.step.guidance)
    assert '17' not in response.model_dump_json(exclude={'sessionId'})
    hint = turn(response, hint=True)
    assert f'«{quote}»' in hint.feedback
    assert 'dữ kiện' in hint.feedback and 'điều cần tìm' in hint.feedback
    wrong = 'Sai' if expected == 'Đúng' else 'Đúng'
    rejected = turn(hint, wrong)
    assert rejected.status == 'TRY_AGAIN' and rejected.stepIndex == 2
    assert rejected.revision == response.revision
    assert 'nguyên đề' in rejected.feedback and 'đại lượng cần tìm' not in rejected.feedback
    accepted = turn(rejected, expected)
    assert accepted.step.kind == 'MATH' and accepted.stepIndex == 3
    assert 'correctChoice' not in accepted.model_dump_json()


@pytest.mark.asyncio
@pytest.mark.parametrize('claim_index,truth', [(0, 'Đúng'), (1, 'Sai')])
async def test_summary_is_complete_source_only_and_earned_by_two_correct_selections(monkeypatch, claim_index, truth):
    monkeypatch.setattr(lesson.secrets, 'choice', lambda values: values[claim_index])
    source = ('Bài 6\nCâu 2 (2 điểm)\nToán lớp 5\n(2 điểm)\n'
              'Lan có 12 bút, được tặng thêm 5 bút. Hai nhóm bút có màu khác nhau. '
              'Hỏi Lan có tất cả bao nhiêu bút?')
    monkeypatch.setattr(lesson, 'generate_plan', AsyncMock(return_value=lesson.Plan(
        topic='Số bút', goal='Tìm số bút.', finalAnswerStep=1, steps=[
            step(choices=['Gộp', 'Bớt'], correctChoice='Gộp'), step(expression='12+5', unit='bút')
        ])))
    response = await lesson.start_lesson(lesson.LessonRequest(owner='student-a', problemText=source,
        problemConfirmed=True, guidedUnderstanding=True))
    question = 'Hỏi Lan có tất cả bao nhiêu bút?'
    assert response.model_dump().get('summary') is None
    response = turn(response, question)
    assert response.status == 'TRY_AGAIN' and response.model_dump().get('summary') is None
    response = turn(turn(response, hint=True), 'Lan có 12 bút')
    assert response.stepIndex == 1 and response.model_dump().get('summary') is None
    rejected = turn(response, 'Lan có 12 bút')
    assert rejected.model_dump().get('summary') is None
    with pytest.raises(lesson.LessonExpired):
        turn(response, question, owner='student-b')
    response = turn(response, question)
    expected = {'givens': ['Lan có 12 bút', 'được tặng thêm 5 bút', 'Hai nhóm bút có màu khác nhau'],
                'question': question}
    assert response.model_dump().get('summary') == expected
    with pytest.raises(lesson.StaleTurn):
        turn(rejected, question)
    assert '17' not in response.model_dump_json(exclude={'sessionId'})
    for answer in [truth, 'Gộp', '17']:
        response = turn(response, answer)
        assert response.model_dump().get('summary') == expected
    assert response.status == 'COMPLETE'


@pytest.mark.asyncio
@pytest.mark.parametrize('tail', [
    ', '.join(['các bút có cùng màu'] * 12),
    'bút ' + 'màu ' * 50,
])
async def test_summary_never_silently_drops_source_clauses_to_fit_caps(monkeypatch, tail):
    source = f'Lan có 12 bút, thêm 5 bút. {tail}. Hỏi có tất cả bao nhiêu bút?'
    monkeypatch.setattr(lesson, 'generate_plan', AsyncMock(return_value=lesson.Plan(
        topic='Số bút', goal='Tìm số bút.', steps=[step(expression='12+5'), step(expression='12+5')]
    )))
    response = await lesson.start_lesson(lesson.LessonRequest(owner='student-a', problemText=source,
        problemConfirmed=True, guidedUnderstanding=True))
    response = turn(turn(response, 'Lan có 12 bút'), 'Hỏi có tất cả bao nhiêu bút?')
    assert response.understandingSteps == 3 and response.stepIndex == 2
    assert response.model_dump().get('summary') is None


@pytest.mark.asyncio
async def test_summary_keeps_decimal_commas_and_classroom_facts_verbatim(monkeypatch):
    source = 'Lớp 5A có 36 học sinh, có 20 bạn nữ. Hai nhóm cùng học một lớp. Hỏi có bao nhiêu bạn nam?'
    monkeypatch.setattr(lesson, 'generate_plan', AsyncMock(return_value=lesson.Plan(
        topic='Học sinh', goal='Tìm số bạn nam.', steps=[step(expression='36-20'), step(expression='36-20')]
    )))
    response = await lesson.start_lesson(lesson.LessonRequest(owner='student-a', problemText=source,
        problemConfirmed=True, guidedUnderstanding=True))
    response = turn(turn(response, 'Lớp 5A có 36 học sinh'), 'Hỏi có bao nhiêu bạn nam?')
    assert response.model_dump().get('summary') == {'givens': ['Lớp 5A có 36 học sinh', 'có 20 bạn nữ',
        'Hai nhóm cùng học một lớp'], 'question': 'Hỏi có bao nhiêu bạn nam?'}
    assert lesson.source_summary('Bình có 1,5 m dây, dùng 0,5 m dây. Hỏi còn bao nhiêu mét dây?').givens == [
        'Bình có 1,5 m dây', 'dùng 0,5 m dây']


def test_summary_caps_accept_all_clauses_at_the_boundary_without_shortening():
    clauses = ['Có 12 bút'] + ['a' * 200] * 11
    question = 'Hỏi ' + 'a' * 95 + '?'
    summary = lesson.source_summary('. '.join(clauses) + '. ' + question)
    assert summary.givens == clauses and summary.question == question
    assert lesson.source_summary('. '.join(clauses + ['cùng màu']) + '. ' + question) is None
    assert lesson.source_summary('Có 12 bút. ' + 'a' * 201 + '. ' + question) is None
    assert lesson.source_summary('Có 12 bút. ' + question + 'a') is None


@pytest.mark.asyncio
async def test_standard_lesson_never_publishes_a_summary_even_for_supported_source(monkeypatch):
    monkeypatch.setattr(lesson, 'generate_plan', AsyncMock(return_value=lesson.Plan(
        topic='Số bút', goal='Tìm số bút.', steps=[step(expression='12+5'), step(expression='12+5')]
    )))
    response = await lesson.start_lesson(lesson.LessonRequest(owner='student-a',
        problemText='Có 12 bút, thêm 5 bút. Hỏi có tất cả bao nhiêu bút?', problemConfirmed=True))
    assert response.summary is None
    assert turn(turn(response, '17'), '17').summary is None
