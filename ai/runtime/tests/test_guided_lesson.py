import json
import time
from unittest.mock import AsyncMock

import pytest

from app.tutoring import lesson
from app.tutoring.lesson import LessonRequest, TurnRequest, LessonExpired, StaleTurn, calculate, start_lesson, answer_lesson
from app.tutoring.service import TutorUnavailable
from _lesson_test_data import step, geometry, review_for

PROBLEM = 'Cho hình thang ABCD có đáy AB = 8 cm, đáy CD = 15 cm và diện tích hình tam giác ACD là 90 cm². Tính diện tích hình thang ABCD.'
WORK = 'Bài giải\nĐộ dài chiều cao AH là:\n90 × 2 : 15 = 12 (cm)\nDiện tích hình thang ABCD là:\n(15 + 8) × 12 : 2 = 138 (cm²)'


@pytest.fixture(autouse=True)
def reset_sessions(monkeypatch):
    lesson._sessions.clear()
    async def generated(prompt, data, **options):
        value=json.loads(data)
        if prompt == lesson.PLAN_PROMPT:
            return geometry(value['problemText'], value['workText'])
        return review_for(value['candidate'])
    monkeypatch.setattr(lesson, '_generate', AsyncMock(side_effect=generated))


def turn(response, answer='', owner='student-a', hint=False):
    return answer_lesson(TurnRequest(owner=owner, sessionId=response.sessionId, revision=response.revision, answer=answer, hint=hint))


@pytest.mark.parametrize('updates', [
    {}, {'problemConfirmed': False}, {'problemConfirmed': 'true'},
    {'problemConfirmed': True, 'workText': '3/2 = 1'},
    {'problemConfirmed': True, 'workConfirmed': True, 'workText': '3/[?]'},
])
def test_unconfirmed_or_unread_source_cannot_construct_a_lesson(updates):
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        LessonRequest(owner='student-a', problemText=PROBLEM, **updates)


@pytest.mark.asyncio
async def test_geometry_guides_three_reasoning_steps_without_returning_answer_keys():
    response = await start_lesson(LessonRequest(problemConfirmed=True, workConfirmed=True, owner='student-a', problemText=PROBLEM))
    assert len(response.outline) == 3
    assert response.step.choices == ['Chiều cao', 'Chu vi', 'Đường chéo AC']
    assert '138' not in response.model_dump_json() and '12' not in response.model_dump_json()
    assert 'correctChoice' not in response.model_dump_json()
    wrong = turn(response, 'Chu vi')
    assert wrong.status == 'TRY_AGAIN' and wrong.stepIndex == 0 and wrong.revision == 0
    response = turn(wrong, 'Chiều cao')
    assert response.stepIndex == 1 and response.step.expression == '90 × 2 ÷ 15'
    assert '12' not in response.model_dump_json()
    wrong = turn(response, '90')
    assert wrong.stepIndex == 1 and '12' not in wrong.model_dump_json()
    hint = turn(wrong, hint=True)
    assert hint.stepIndex == 1 and '12' not in hint.model_dump_json()
    response = turn(hint, '12')
    assert '12' in response.step.expression and '138' not in response.model_dump_json()
    response = turn(response, '138')
    assert response.status == 'COMPLETE' and response.step is None and len(response.completed) == 3
    assert response.completed[-1].answer == '138' and response.completed[-1].unit == 'cm²'
    assert 'hoàn thành' in response.feedback


@pytest.mark.asyncio
async def test_geometry_uses_changed_givens_not_a_hardcoded_example():
    response = await start_lesson(LessonRequest(problemConfirmed=True, workConfirmed=True, owner='student-a', problemText=PROBLEM.replace('8 cm', '10 cm').replace('90 cm', '75 cm')))
    response = turn(response, 'Chiều cao')
    response = turn(response, '10')
    response = turn(response, '125')
    assert response.status == 'COMPLETE'


@pytest.mark.asyncio
async def test_accounts_cannot_access_each_others_lesson_or_replay_old_step():
    response = await start_lesson(LessonRequest(problemConfirmed=True, workConfirmed=True, owner='student-a', problemText=PROBLEM))
    with pytest.raises(LessonExpired):
        turn(response, 'Chiều cao', owner='student-b')
    turn(response, 'Chiều cao')
    with pytest.raises(StaleTurn):
        turn(response, 'Chiều cao')
    lesson._sessions[response.sessionId].expires = time.monotonic() - 1
    with pytest.raises(LessonExpired):
        turn(response, '12')


@pytest.mark.asyncio
@pytest.mark.parametrize('answer', ['90 × 2 ÷ 15 = 12', '12 cm', '12; import os', 'Infinity', 'NaN'])
async def test_only_a_single_numeric_answer_is_accepted(answer):
    response = await start_lesson(LessonRequest(problemConfirmed=True, workConfirmed=True, owner='student-a', problemText=PROBLEM))
    response = turn(response, 'Chiều cao')
    assert turn(response, answer).status == 'TRY_AGAIN'


@pytest.mark.asyncio
async def test_work_is_grouped_with_its_reason_and_compared_only_after_student_response():
    response = await start_lesson(LessonRequest(problemConfirmed=True, workConfirmed=True, owner='student-a', problemText=PROBLEM, workText=WORK.replace('= 12', '= 11')))
    response = turn(response, 'Chiều cao')
    assert 'chiều cao AH' in response.step.workExcerpt
    assert '= 11' in response.step.workExcerpt
    response = turn(response, '12')
    assert 'trong ảnh chưa khớp' in response.feedback
    assert response.stepIndex == 2


@pytest.mark.parametrize('expression', ['__import__("os")', '2**100', 'True', '1/0', 'max(1,2)', '[1]'])
def test_math_expression_evaluator_rejects_code_and_unsupported_operations(expression):
    with pytest.raises((ValueError, ArithmeticError)):
        calculate(expression)


@pytest.mark.asyncio
async def test_cloud_plan_keeps_keys_private_and_validates_arithmetic(monkeypatch):
    plan = dict(topic='Thêm bút', goal='Tìm số bút sau khi được cho thêm.', finalAnswerStep=1, steps=[
        step(title='Chọn phép tính', explanation='Xem số bút thay đổi như thế nào.', question='Em chọn phép tính nào?', choices=['Cộng', 'Trừ'], correctChoice='Cộng'),
        step(title='Tính số bút', explanation='Gộp số bút ban đầu với số bút được thêm.', question='Em tính được bao nhiêu bút?', expression='12+5', unit='bút'),
    ])
    monkeypatch.setattr(lesson, '_generate', AsyncMock(side_effect=[plan, review_for(plan)]))
    response = await start_lesson(LessonRequest(problemConfirmed=True, workConfirmed=True, owner='student-a', problemText='Lan có 12 bút, được cho 5 bút. Hỏi có tất cả bao nhiêu bút?'))
    # Opaque random session IDs may contain these digits without revealing an
    # answer. Check every learning-content field, including completed steps.
    assert '17' not in response.model_dump_json(exclude={'sessionId'})
    response = turn(response, 'Cộng')
    assert turn(response, '17').status == 'COMPLETE'
    plan['steps'][1]['question'] = 'Kết quả là 17 bút, đúng không?'
    monkeypatch.setattr(lesson, '_generate', AsyncMock(return_value=plan))
    with pytest.raises(TutorUnavailable):
        await start_lesson(LessonRequest(problemConfirmed=True, workConfirmed=True, owner='student-a', problemText='Lan có 12 bút, được cho 5 bút. Hỏi có tất cả bao nhiêu bút?'))


@pytest.mark.asyncio
async def test_cloud_plan_must_not_invent_givens_or_copy_ungrounded_work(monkeypatch):
    plan = dict(topic='Thêm bút', goal='Tìm số bút.', finalAnswerStep=1, steps=[
        step(title='Chọn phép tính', explanation='Xem số bút thay đổi.', question='Em chọn phép tính nào?', choices=['Cộng', 'Trừ'], correctChoice='Cộng'),
        step(title='Tính', explanation='Gộp hai nhóm.', question='Em tính được bao nhiêu?', expression='100+5', unit='bút'),
    ])
    monkeypatch.setattr(lesson, '_generate', AsyncMock(side_effect=[plan, review_for(plan)]))
    with pytest.raises(TutorUnavailable):
        await start_lesson(LessonRequest(problemConfirmed=True, workConfirmed=True, owner='student-a', problemText='Lan có 12 bút, được cho 5 bút.'))


@pytest.mark.asyncio
async def test_missing_or_uncertain_original_problem_cannot_start_lesson():
    with pytest.raises(ValueError):
        LessonRequest(problemConfirmed=True, workConfirmed=True, owner='student-a', problemText='', workText=WORK)
    with pytest.raises(ValueError):
        await start_lesson(LessonRequest(problemConfirmed=True, workConfirmed=True, owner='student-a', problemText=PROBLEM.replace('90', '[?]')))


@pytest.mark.asyncio
@pytest.mark.parametrize('field,value', [('unit', '17 bút'), ('title', 'Bước {s1}'), ('topic', 'groq'), ('goal', 'Xem http://localhost:8000')])
async def test_every_generated_public_field_is_checked_before_lesson_is_opened(monkeypatch, field, value):
    plan = dict(topic='Thêm bút', goal='Hiểu việc được cho thêm.', finalAnswerStep=1, steps=[
        step(title='Hiểu đề', explanation='Số bút tăng khi được cho thêm.', question='Em chọn cách nào?', choices=['Gộp', 'Bớt'], correctChoice='Gộp'),
        step(title='Tính', explanation='Gộp số bút ban đầu với số bút được thêm.', question='Có tất cả bao nhiêu bút?', expression='12+5', unit='bút'),
    ])
    if field in ['topic', 'goal']:
        plan[field] = value
    else:
        plan['steps'][1][field] = value
    monkeypatch.setattr(lesson, '_generate', AsyncMock(side_effect=[plan, review_for(plan)]))
    with pytest.raises(TutorUnavailable):
        await start_lesson(LessonRequest(problemConfirmed=True, workConfirmed=True, owner='student-a', problemText='Lan có 12 bút, được cho 5 bút. Hỏi có tất cả bao nhiêu bút?'))
