"""Recover private planner formatting without skipping mathematical review."""
import copy
import json
from unittest.mock import AsyncMock

import pytest

from app.tutoring import lesson, catalog
from app.tutoring.service import TutorUnavailable
from _lesson_test_data import step, review_for


SOURCE = ('Một căn phòng hình chữ nhật có chiều dài bằng 45/4 m, chiều rộng bằng 6 m. '
          'Bác Hà lát nền căn phòng đó bằng các viên gạch men hình vuông cạnh 30 cm. '
          'Hỏi bác Hà cần bao nhiêu viên gạch để lát kín nền căn phòng đó? '
          '(Biết diện tích phần mạch vữa là không đáng kể)')


def candidate():
    return dict(topic='Lát nền phòng', goal='Tìm số viên gạch cần dùng.', finalAnswerStep=3, steps=[
        step(title='Tìm diện tích nền phòng', expression='45/4*6*10000', unit='cm²'),
        step(title='Tìm diện tích viên gạch', expression='30*30', unit='cm²'),
        step(title='Tìm số viên gạch cần dùng', expression='{s0}/{s1}', unit='viên'),
    ])


def review():
    valid = candidate()
    valid['finalAnswerStep'] = 2
    return review_for(valid, [dict(stepIndex=2, answer='750', unit='viên')])


@pytest.mark.asyncio
async def test_uncached_last_step_count_is_normalized_then_independently_checked(monkeypatch):
    monkeypatch.setattr(catalog, 'load_plan', lambda _: None)
    save = []
    monkeypatch.setattr(catalog, 'save_plan', lambda request, plan: save.append(plan))
    cloud = AsyncMock(side_effect=[candidate(), review()])
    monkeypatch.setattr(lesson, '_generate', cloud)
    request = lesson.LessonRequest(owner='fresh-index', problemText=SOURCE, problemConfirmed=True)
    plan = await lesson.checked_plan(request)
    assert plan.finalAnswerStep == 2
    assert cloud.await_count == 2 and save == [plan]
    checked = json.loads(cloud.call_args_list[1].args[1])
    assert checked['computedAnswers'] == ['675000', '900', '750']
    assert checked['candidate']['finalAnswerStep'] == 2
    assert checked['resultScope']['finalAnswerStep'] == 2


@pytest.mark.asyncio
@pytest.mark.parametrize('fault', ['wrong_answer', 'wrong_unit', 'wrong_question'])
async def test_index_recovery_never_skips_independent_mathematical_review(monkeypatch, fault):
    bad_review = review()
    if fault == 'wrong_answer': bad_review['results'][0]['answer'] = '751'
    elif fault == 'wrong_unit': bad_review['results'][0]['unit'] = 'm²'
    else: bad_review['answersQuestion'] = False
    cloud = AsyncMock(side_effect=[candidate(), copy.deepcopy(bad_review), candidate(), bad_review])
    monkeypatch.setattr(lesson, '_generate', cloud)
    monkeypatch.setattr(catalog, 'load_plan', lambda _: None)
    save = []
    monkeypatch.setattr(catalog, 'save_plan', lambda request, plan: save.append(plan))
    with pytest.raises(TutorUnavailable) as rejected:
        await lesson.checked_plan(lesson.LessonRequest(owner='fresh-index', problemText=SOURCE, problemConfirmed=True))
    assert rejected.value.reason == 'validation' and not save
    assert cloud.await_count == 4


@pytest.mark.asyncio
async def test_other_invalid_final_indexes_are_not_silently_reassigned(monkeypatch):
    invalid = candidate()
    invalid['finalAnswerStep'] = 4
    cloud = AsyncMock(return_value=invalid)
    monkeypatch.setattr(lesson, '_generate', cloud)
    with pytest.raises(ValueError, match='Invalid final answer step'):
        await lesson.generate_plan(lesson.LessonRequest(owner='fresh-index', problemText=SOURCE, problemConfirmed=True))
    assert cloud.await_count == 2


@pytest.mark.asyncio
async def test_misplaced_current_worked_paragraph_stays_private_and_is_still_reviewed(monkeypatch):
    draft = candidate()
    draft['finalAnswerStep'] = 2
    draft['steps'][2]['initialGuidance'] = [*draft['steps'][2]['guidance'][:2],
        'Sau khi tính phép chia, số viên gạch cần dùng là 750 viên. Em viết lại câu trả lời và kiểm tra đơn vị.']
    cloud = AsyncMock(side_effect=[draft, review()])
    monkeypatch.setattr(lesson, '_generate', cloud)
    plan = await lesson.generate_plan(lesson.LessonRequest(owner='fresh-index', problemText=SOURCE, problemConfirmed=True))
    checked = json.loads(cloud.call_args_list[1].args[1])
    assert cloud.await_count == 2
    assert '750' not in lesson.numeric_values('\n'.join(checked['initialTeaching'][2]))
    assert any('750' in item for item in checked['workedTeaching'][2])
    assert any('750' in item for item in plan.steps[2].guidance)


@pytest.mark.asyncio
async def test_moving_a_future_answer_to_worked_help_still_rejects_it(monkeypatch):
    draft = candidate()
    draft['finalAnswerStep'] = 2
    draft['steps'][0]['initialGuidance'] = [*draft['steps'][0]['guidance'][:2],
        'Cuối cùng sẽ cần 750 viên gạch để lát nền. Em dùng đáp án này khi ghi câu trả lời cho bài toán.']
    cloud = AsyncMock(return_value=draft)
    monkeypatch.setattr(lesson, '_generate', cloud)
    with pytest.raises(ValueError, match='Future answer in teaching'):
        await lesson.generate_plan(lesson.LessonRequest(owner='fresh-index', problemText=SOURCE, problemConfirmed=True))
    assert cloud.await_count == 2


@pytest.mark.asyncio
async def test_recovery_cannot_open_a_plan_without_enough_answer_free_teaching(monkeypatch):
    draft = candidate()
    draft['finalAnswerStep'] = 2
    draft['steps'][2]['initialGuidance'] = [draft['steps'][2]['guidance'][0],
        'Kết quả phép chia này là 750 viên.', 'Em ghi đáp số bằng 750 viên gạch.']
    cloud = AsyncMock(return_value=draft)
    monkeypatch.setattr(lesson, '_generate', cloud)
    with pytest.raises(ValueError, match='reveals unearned'):
        await lesson.generate_plan(lesson.LessonRequest(owner='fresh-index', problemText=SOURCE, problemConfirmed=True))
    assert cloud.await_count == 2
