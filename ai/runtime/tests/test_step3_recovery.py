"""Regression: provider failure must not erase a checked reading answer."""
import asyncio
from collections import OrderedDict
from fractions import Fraction
from unittest.mock import AsyncMock

import pytest

from app.tutoring import lesson
from app.tutoring.fraction_remainder import verified_plan
from app.tutoring.service import TutorUnavailable
from test_fraction_lesson_support import garden
from _lesson_test_data import step


@pytest.mark.parametrize('population,counter,categories', [
    ('cây','cây',('cây táo','cây xoài','cây cam')),
    ('sách','quyển sách',('sách Toán','sách Văn','sách Anh')),
    ('kẹo','viên kẹo',('kẹo dâu','kẹo cam','kẹo chanh')),
    ('viên bi','viên bi',('bi đỏ','bi xanh','bi vàng')),
    ('bông hoa','bông hoa',('hoa hồng','hoa cúc','hoa lan')),
    ('quả bóng','quả bóng',('bóng đỏ','bóng xanh','bóng vàng')),
])
def test_verified_relation_supports_different_populations_and_names(population,counter,categories):
    source=(f'Bạn Ngọc có một số {population}. Trong đó, 1/4 số {population} là {categories[0]}, '
            f'2/5 số {population} là {categories[1]}, còn lại là {categories[2]}. '
            f'Biết có 14 {categories[2]}. Hỏi bạn Ngọc có tất cả bao nhiêu {counter}?')
    data=verified_plan(source)
    assert data is not None
    plan=lesson.Plan.model_validate(data)
    lesson.validate_plan(plan,lesson.LessonRequest(owner='child',problemText=source,problemConfirmed=True))
    answers=[]
    for step in plan.steps: answers.append(str(lesson.calculate_exact(lesson.expression_at(step,answers))))
    assert answers==['13/20','7/20','40']


@pytest.mark.asyncio
async def test_real_async_planner_deadline_is_classified_and_cancels_only_the_planner(monkeypatch):
    real_wait=asyncio.wait_for
    cancelled=asyncio.Event()
    async def slow(_):
        try: await asyncio.sleep(10)
        finally: cancelled.set()
    monkeypatch.setattr(lesson,'generate_plan',slow)
    monkeypatch.setattr(asyncio,'wait_for',lambda task,timeout:real_wait(task,min(timeout,.02)))
    request=lesson.LessonRequest(owner='child',problemText='Tính 12 + 5.',problemConfirmed=True)
    with pytest.raises(TutorUnavailable) as error: await lesson.reviewed_plan(request,[])
    assert error.value.reason=='TIMEOUT' and cancelled.is_set()


@pytest.mark.asyncio
async def test_written_work_provider_failure_uses_checked_math_without_claiming_work_was_reviewed(monkeypatch):
    monkeypatch.setattr(lesson,'generate_plan',AsyncMock(side_effect=TutorUnavailable('RATE_LIMIT')))
    request=lesson.LessonRequest(owner='child',problemText=garden(),problemConfirmed=True,
        workText='1/3 + 2/5 = 10/15',workConfirmed=True)
    plan=await lesson.reviewed_plan(request,[])
    assert len(plan.steps)==3 and all(not s.workExcerpt for s in plan.steps)
    assert str(lesson.calculate_exact(plan.steps[0].expression))=='11/15'


@pytest.mark.parametrize('a,b,count,total', [('1/3','2/5',16,60), ('1/4','2/5',14,40), ('2/6','1/6',9,18), ('2/7','1/7',12,21)])
@pytest.mark.asyncio
async def test_exact_solver_reaches_complete_with_cloud_disabled(monkeypatch,a,b,count,total):
    source=garden(*a.split('/'),*b.split('/'),str(count))
    monkeypatch.setattr(lesson,'_sessions',OrderedDict())
    cloud=AsyncMock(side_effect=AssertionError('Exact relation must not need a provider'))
    monkeypatch.setattr(lesson,'_generate',cloud)
    result=await lesson.start_lesson(lesson.LessonRequest(owner='child',problemText=source,problemConfirmed=True,
        guidedUnderstanding=True,startWithReading=True))
    session=lesson._sessions[result.sessionId]
    for _ in range(3):
        result=lesson.answer_lesson(lesson.TurnRequest(owner='child',sessionId=result.sessionId,revision=result.revision,
            answer=session.plan.steps[result.stepIndex].correctChoice))
    assert result.status=='PREPARING' and len(result.completed)==3 and not result.conclusion
    assert await session.preparation_task
    result=lesson.lesson_preparation(lesson.PreparationRequest(owner='child',sessionId=result.sessionId,revision=3))
    assert result.step.kind=='MATH' and result.stepIndex==3 and not result.preparingMath
    assert str(total) not in result.model_dump_json(exclude={'sessionId'})
    for value in (Fraction(a)+Fraction(b),1-Fraction(a)-Fraction(b),Fraction(total)):
        assert result.step is not None
        result=lesson.answer_lesson(lesson.TurnRequest(owner='child',sessionId=result.sessionId,revision=result.revision,answer=str(value)))
    assert result.status=='COMPLETE' and result.completed[-1].answer==str(total)
    cloud.assert_not_awaited()


@pytest.mark.parametrize('change', [
    lambda s:s.replace('1/3','2/3'), lambda s:s.replace('16 cây','17 cây'),
    lambda s:s.replace('số cây là cây xoài','số cây còn lại là cây xoài'),
    lambda s:s.replace('cây cam có trong vườn','cây táo có trong vườn'),
    lambda s:s.replace('cây xoài','cây táo'),lambda s:s.replace('Hỏi','Sau khi thêm 3 cây. Hỏi'),
    lambda s:s.replace('1/3','1/0'),lambda s:s.replace('1/3','0/3'),
])
def test_uncertain_or_inconsistent_relations_are_never_solved_by_fallback(change):
    assert verified_plan(change(garden())) is None


@pytest.mark.asyncio
@pytest.mark.parametrize('failure', [TutorUnavailable('RATE_LIMIT'),TutorUnavailable('TIMEOUT'),ValueError('invalid plan')])
async def test_failed_preparation_retains_third_answer_and_single_flight_retry(monkeypatch,failure):
    monkeypatch.setattr(lesson,'_sessions',OrderedDict())
    source='Lan có 12 bút, được tặng thêm 5 bút. Hỏi Lan có tất cả bao nhiêu bút?'
    generate=AsyncMock(side_effect=failure)
    monkeypatch.setattr(lesson,'generate_plan',generate)
    result=await lesson.start_lesson(lesson.LessonRequest(owner='child',problemText=source,problemConfirmed=True,guidedUnderstanding=True,startWithReading=True))
    session=lesson._sessions[result.sessionId]
    assert not await session.preparation_task
    for _ in range(3):
        result=lesson.answer_lesson(lesson.TurnRequest(owner='child',sessionId=result.sessionId,revision=result.revision,answer=session.plan.steps[result.stepIndex].correctChoice))
    assert result.status=='RETRYABLE' and result.revision==3 and len(result.completed)==3
    request=lesson.PreparationRequest(owner='child',sessionId=result.sessionId,revision=3,retry=True)
    session.preparation_retry_at=0
    lesson.lesson_preparation(request);task=session.preparation_task
    lesson.lesson_preparation(request)
    assert session.preparation_task is task and session.preparation_attempts==2
    assert not await task
    session.preparation_retry_at=0
    lesson.lesson_preparation(request);assert not await session.preparation_task
    assert lesson.lesson_preparation(request).status=='UNAVAILABLE'
    assert session.revision==3 and len(session.answers)==3 and session.preparation_attempts==3
    with pytest.raises(lesson.LessonExpired):
        lesson.lesson_preparation(request.model_copy(update={'owner':'other-child'}))
    # A recovered provider can be retried after the bounded cooldown without
    # requiring the pupil to repeat comprehension or photograph a valid source.
    old_task=session.preparation_task
    session.preparation_retry_at=0
    lesson.lesson_preparation(request)
    assert session.preparation_attempts==1 and session.preparation_task is not old_task
    generate.side_effect=None
    generate.return_value=lesson.Plan(topic='Bút',goal='Tìm số bút có tất cả.',finalAnswerStep=1,steps=[
        lesson.Step(**step(expression='12+5',unit='bút')),
        lesson.Step(**step(expression='{s0}*1',unit='bút'))])
    assert await session.preparation_task
    assert session.revision==3 and len(session.completed)==3
    assert lesson.lesson_preparation(request).step.kind=='MATH'


@pytest.mark.asyncio
async def test_cancelled_job_can_retry_without_losing_reading_or_resubmitting(monkeypatch):
    monkeypatch.setattr(lesson,'_sessions',OrderedDict())
    result=await lesson.start_lesson(lesson.LessonRequest(owner='child',problemText=garden(),problemConfirmed=True,guidedUnderstanding=True,startWithReading=True))
    session=lesson._sessions[result.sessionId]
    session.preparation_task.cancel()
    await asyncio.gather(session.preparation_task,return_exceptions=True)
    for _ in range(3):
        result=lesson.answer_lesson(lesson.TurnRequest(owner='child',sessionId=result.sessionId,revision=result.revision,answer=session.plan.steps[result.stepIndex].correctChoice))
    req=lesson.PreparationRequest(owner='child',sessionId=result.sessionId,revision=3)
    assert lesson.lesson_preparation(req).status=='RETRYABLE'
    lesson.lesson_preparation(req.model_copy(update={'retry':True}))
    assert await session.preparation_task
    result=lesson.lesson_preparation(req)
    assert result.step.kind=='MATH' and result.revision==3 and len(result.completed)==3
