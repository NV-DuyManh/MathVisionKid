"""Reading can open before planning; mathematics must still pass every review."""
import asyncio
import threading
from collections import OrderedDict
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
import httpx
from fastapi import FastAPI
from pydantic import ValidationError

from app.tutoring import lesson, media_preparation as media, narration
from app.tutoring.service import TutorUnavailable
from _lesson_test_data import step, mock_generation
from app.api import tutor
from app.config import settings

SOURCE='Lan có 12 bút, được tặng thêm 5 bút. Hỏi Lan có tất cả bao nhiêu bút?'


@pytest_asyncio.fixture
async def pending_lesson(monkeypatch):
    monkeypatch.setattr(lesson,'_sessions',OrderedDict())
    monkeypatch.setattr(media,'_jobs',OrderedDict())
    candidate=dict(topic='Bút',goal='Tìm số bút có tất cả.',finalAnswerStep=1,steps=[
        step(title='Chọn cách tính',choices=['Gộp hai nhóm','Bớt một nhóm'],correctChoice='Gộp hai nhóm'),
        step(title='Tìm số bút',expression='12+5',unit='bút')])
    cloud=mock_generation(monkeypatch,candidate,[dict(stepIndex=1,answer='17',unit='bút')])
    gate=asyncio.Event();generate=lesson.generate_plan
    async def deferred(request):
        await gate.wait()
        return await generate(request)
    monkeypatch.setattr(lesson,'generate_plan',deferred)
    request=lesson.LessonRequest(owner='reader-a',problemText=SOURCE,problemConfirmed=True,
        guidedUnderstanding=True,startWithReading=True)
    response=await lesson.start_lesson(request)
    session=lesson._sessions[response.sessionId]
    yield response,session,gate,cloud,request
    tasks=[s.preparation_task for s in lesson._sessions.values() if s.preparation_task]
    for task in tasks:
        if not task.done():task.cancel()
    await asyncio.gather(*tasks,return_exceptions=True)


def turn(response,session,answer=None,**changes):
    values=dict(owner=session.owner,sessionId=response.sessionId,revision=session.revision,
        answer=session.plan.steps[len(session.answers)].correctChoice if answer is None else answer)
    return lesson.TurnRequest(**(values|changes))


@pytest.mark.asyncio
async def test_reading_opens_without_waiting_for_model_and_prewarms_without_publishing_math(pending_lesson):
    response,session,_,cloud,_=pending_lesson
    assert response.preparingMath and response.understandingSteps==3 and len(response.outline)==3
    assert response.step.kind=='UNDERSTAND' and not response.step.expression
    assert 'correctChoice' not in response.model_dump_json() and '17' not in response.model_dump_json(exclude={'sessionId'})
    cloud.assert_not_awaited()
    media.schedule(media.PrepareRequest(owner=session.owner,sessionId=response.sessionId,revision=0))
    assert len(media._jobs[response.sessionId].scripts)==3
    with pytest.raises(ValueError):
        narration.owned(narration.NarrationRequest(owner=session.owner,sessionId=response.sessionId,revision=0,paragraphs=['12 + 5 = 17']))


@pytest.mark.asyncio
async def test_final_reading_answer_is_retained_before_review_then_enters_math_once(pending_lesson):
    response,session,gate,cloud,_=pending_lesson
    for _ in range(2):lesson.answer_lesson(turn(response,session))
    last=turn(response,session)
    await lesson.ready_for_answer(last)
    pending=lesson.answer_lesson(last)
    assert pending.status=='PREPARING' and pending.step is None
    assert session.revision==3 and len(session.completed)==3
    gate.set();assert await session.preparation_task
    assert cloud.await_count==2  # Planner AND independent semantic review, unchanged.
    result=lesson.lesson_preparation(lesson.PreparationRequest(owner=session.owner,sessionId=response.sessionId,revision=3))
    assert result.stepIndex==3 and result.step.kind=='MATH' and not result.preparingMath
    assert result.status=='READY' and len(result.outline)==5
    with pytest.raises(lesson.StaleTurn):lesson.answer_lesson(last)


@pytest.mark.asyncio
async def test_wrong_answer_and_hint_do_not_wait_for_math(pending_lesson):
    response,session,_,cloud,_=pending_lesson
    for _ in range(2):lesson.answer_lesson(turn(response,session))
    wrong=turn(response,session,answer='Không phải một lựa chọn')
    await lesson.ready_for_answer(wrong)
    assert lesson.answer_lesson(wrong).status=='TRY_AGAIN' and session.revision==2
    hint=turn(response,session,hint=True)
    await lesson.ready_for_answer(hint)
    assert lesson.answer_lesson(hint).status=='HINT'
    cloud.assert_not_awaited()


@pytest.mark.asyncio
async def test_retry_during_last_active_attempt_cannot_reset_budget_or_duplicate_task(pending_lesson):
    response,session,_,_,_=pending_lesson
    session.preparation_attempts=3
    task=session.preparation_task
    request=lesson.PreparationRequest(owner=session.owner,sessionId=response.sessionId,revision=0,retry=True)
    lesson.lesson_preparation(request)
    assert session.preparation_attempts==3 and session.preparation_task is task


@pytest.mark.asyncio
async def test_owner_revision_and_cancelled_waiter_cannot_advance_or_cancel_the_shared_plan(pending_lesson):
    response,session,gate,_,_=pending_lesson
    for _ in range(2):lesson.answer_lesson(turn(response,session))
    with pytest.raises(lesson.LessonExpired):await lesson.ready_for_answer(turn(response,session,owner='other'))
    with pytest.raises(lesson.StaleTurn):await lesson.ready_for_answer(turn(response,session,revision=0))
    waiting=asyncio.create_task(lesson.ready_for_answer(turn(response,session)))
    waiting.cancel()
    with pytest.raises(asyncio.CancelledError):await waiting
    assert not session.preparation_task.cancelled() and session.revision==2
    gate.set();assert await session.preparation_task


@pytest.mark.asyncio
async def test_failed_review_never_completes_reading_or_publishes_math(pending_lesson,monkeypatch):
    response,session,gate,cloud,_=pending_lesson
    cloud.side_effect=TutorUnavailable()
    gate.set();assert await session.preparation_task is False
    for _ in range(2):lesson.answer_lesson(turn(response,session))
    last=turn(response,session)
    await lesson.ready_for_answer(last)
    assert lesson.answer_lesson(last).status=='RETRYABLE'
    assert isinstance(session.plan,lesson.ReadingPlan) and session.revision==3
    assert all(s.kind=='UNDERSTAND' for s in session.plan.steps)


@pytest.mark.asyncio
async def test_reviewed_plan_refresh_preserves_voice_and_spent_budget(pending_lesson):
    response,session,gate,_,_=pending_lesson
    media.schedule(media.PrepareRequest(owner=session.owner,sessionId=response.sessionId,revision=0,voice='vi-VN-HoaiMyNeural'))
    old=media._jobs[response.sessionId];old.characters=1000
    gate.set();assert await session.preparation_task
    current=media._jobs[response.sessionId]
    assert old.stopped and current is not old and len(current.scripts)==5
    assert current.voice=='vi-VN-HoaiMyNeural' and current.characters==1000


@pytest.mark.asyncio
async def test_plan_refresh_yields_unused_speech_but_preserves_an_active_listener(pending_lesson):
    response,session,gate,_,_=pending_lesson
    media.schedule(media.PrepareRequest(owner=session.owner,sessionId=response.sessionId,revision=0))
    parts=media._jobs[response.sessionId].scripts[0]
    keys=[(session.owner,response.sessionId,voice,False,tuple(parts)) for voice in media.SPEECH_VOICES]
    events=[threading.Event(),threading.Event()]
    for key,event in zip(keys,events):narration._background[key]=event
    narration._foreground_waiters[keys[0]]=1
    try:
        gate.set();assert await session.preparation_task
        assert not events[0].is_set() and events[1].is_set()
    finally:
        for key in keys:narration._background.pop(key,None)
        narration._foreground_waiters.pop(keys[0],None)


@pytest.mark.asyncio
async def test_concurrent_final_answers_share_planning_and_only_one_can_advance(pending_lesson):
    response,session,gate,cloud,_=pending_lesson
    for _ in range(2):lesson.answer_lesson(turn(response,session))
    last=turn(response,session)
    async def submit():
        await lesson.ready_for_answer(last)
        return lesson.answer_lesson(last)
    one=asyncio.create_task(submit());two=asyncio.create_task(submit());await asyncio.sleep(0)
    gate.set();results=await asyncio.gather(one,two,return_exceptions=True)
    await session.preparation_task
    assert sum(isinstance(result,lesson.LessonResponse) for result in results)==1
    assert sum(isinstance(result,lesson.StaleTurn) for result in results)==1
    assert session.revision==3 and cloud.await_count==2


@pytest.mark.asyncio
async def test_removed_session_cannot_be_replaced_by_a_late_background_result(pending_lesson):
    response,session,gate,_,_=pending_lesson
    lesson._sessions.pop(response.sessionId);gate.set()
    assert await session.preparation_task is False
    assert not lesson._sessions and isinstance(session.plan,lesson.ReadingPlan)


@pytest.mark.asyncio
async def test_late_ready_plan_does_not_resurrect_an_abandoned_speech_queue(pending_lesson):
    response,session,gate,_,_=pending_lesson
    media.schedule(media.PrepareRequest(owner=session.owner,sessionId=response.sessionId,revision=0))
    media._jobs.clear();gate.set()
    assert await session.preparation_task and not media._jobs


@pytest.mark.asyncio
async def test_new_lesson_does_not_cancel_an_active_session(pending_lesson):
    _,session,gate,_,request=pending_lesson
    newer=await lesson.start_lesson(request.model_copy(update={'problemText':SOURCE.replace('Lan','Mai')}))
    assert not session.preparation_task.cancelled()
    assert not lesson._sessions[newer.sessionId].preparation_task.done()
    gate.set()
    await session.preparation_task
    assert not session.preparation_task.cancelled()


@pytest.mark.asyncio
async def test_unsupported_reading_source_keeps_reviewed_full_lesson_path(monkeypatch):
    plan=lesson.Plan(topic='Tính',goal='Tính biểu thức.',steps=[lesson.Step(**step(expression='12+5')),lesson.Step(**step(expression='{s0}*1'))])
    generate=AsyncMock(return_value=plan);monkeypatch.setattr(lesson,'generate_plan',generate)
    response=await lesson.start_lesson(lesson.LessonRequest(owner='reader',problemText='Tính 12+5.',problemConfirmed=True,
        guidedUnderstanding=True,startWithReading=True))
    assert not response.preparingMath and response.step.kind=='MATH'
    generate.assert_awaited_once()


@pytest.mark.parametrize('changes',[{'guidedUnderstanding':False},{'problemConfirmed':False},{'startWithReading':'true'}])
def test_reading_first_still_requires_explicit_confirmed_typed_request(changes):
    with pytest.raises(ValidationError):lesson.LessonRequest(**(dict(owner='reader',problemText=SOURCE,problemConfirmed=True,
        guidedUnderstanding=True,startWithReading=True)|changes))


@pytest.mark.asyncio
async def test_internal_api_returns_reading_while_model_is_blocked(pending_lesson,monkeypatch):
    _,_,_,cloud,request=pending_lesson
    monkeypatch.setattr(settings,'internal_api_key','reading-test-key')
    app=FastAPI();app.include_router(tutor.router)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
        assert (await client.post('/lesson',json=request.model_dump())).status_code==401
        response=await asyncio.wait_for(client.post('/lesson',json=request.model_dump(),headers={'X-Internal-API-Key':'reading-test-key'}),timeout=.5)
        assert response.status_code==200 and response.json()['preparingMath'] is True
        assert len(response.json()['outline'])==3 and 'correctChoice' not in response.text
        cloud.assert_not_awaited()


@pytest.mark.asyncio
async def test_answer_api_never_advances_to_unreviewed_math(pending_lesson,monkeypatch):
    response,session,gate,_,_=pending_lesson
    for _ in range(2):lesson.answer_lesson(turn(response,session))
    monkeypatch.setattr(settings,'internal_api_key','reading-test-key')
    app=FastAPI();app.include_router(tutor.router)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
        headers={'X-Internal-API-Key':'reading-test-key'}
        denied=await client.post('/lesson/answer',json=turn(response,session,owner='other').model_dump(),headers=headers)
        assert denied.status_code==410
        pending=await client.post('/lesson/answer',json=turn(response,session).model_dump(),headers=headers)
        assert pending.status_code==200 and pending.json()['status']=='PREPARING' and session.revision==3
        gate.set();assert await session.preparation_task
        result=await client.post('/lesson/preparation',json={'owner':session.owner,'sessionId':response.sessionId,'revision':3},headers=headers)
        assert result.status_code==200 and result.json()['step']['kind']=='MATH'
        assert result.json()['preparingMath'] is False and result.json()['revision']==3
