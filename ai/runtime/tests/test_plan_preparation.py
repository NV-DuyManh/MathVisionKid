"""Private precomputation is reusable only after exact source/account confirmation."""
import asyncio
from collections import OrderedDict
from unittest.mock import AsyncMock

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from pydantic import ValidationError

from app.api import tutor
from app.config import settings
from app.tutoring import lesson, plan_preparation as preparation
from app.tutoring.service import TutorUnavailable
from test_lesson_metric_amounts import SOURCE, candidate


@pytest_asyncio.fixture(autouse=True)
async def isolated(monkeypatch):
    monkeypatch.setattr(preparation, '_jobs', OrderedDict())
    monkeypatch.setattr(lesson, '_sessions', OrderedDict())
    yield
    tasks = [task for _, task in preparation._jobs.values() if not task.done()]
    tasks += [session.preparation_task for session in lesson._sessions.values()
              if session.preparation_task and not session.preparation_task.done()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


def draft(**changes):
    return preparation.SourceDraft(**{'owner': 'student-a', 'problemText': SOURCE, **changes})


def confirmed(**changes):
    return lesson.LessonRequest(**{'owner': 'student-a', 'problemText': SOURCE, 'problemConfirmed': True, **changes})


@pytest.mark.asyncio
async def test_ready_preparation_reuses_checked_plan_and_never_returns_answers(monkeypatch):
    checked = AsyncMock(return_value=lesson.Plan.model_validate(candidate()))
    monkeypatch.setattr(lesson, 'checked_plan', checked)
    assert await preparation.prepare(draft()) == {'phase': 'preparing'}
    await asyncio.sleep(0)
    assert await preparation.prepare(draft()) == {'phase': 'ready'}
    first = await lesson.reviewed_plan(confirmed(), [])
    first.steps[0].title = 'Changed only in this session'
    second = await lesson.reviewed_plan(confirmed(), [])
    assert second.steps[0].title != first.steps[0].title and checked.await_count == 1


@pytest.mark.asyncio
async def test_inflight_work_is_shared_and_cancelling_waiter_keeps_preparation(monkeypatch):
    gate = asyncio.Event()
    async def slow(request):
        await gate.wait()
        return lesson.Plan.model_validate(candidate())
    checked = AsyncMock(side_effect=slow)
    monkeypatch.setattr(lesson, 'checked_plan', checked)
    await preparation.prepare(draft())
    first = asyncio.create_task(preparation.prepared_plan(confirmed()))
    second = asyncio.create_task(preparation.prepared_plan(confirmed()))
    await asyncio.sleep(0)
    first.cancel()
    await asyncio.gather(first, return_exceptions=True)
    assert not preparation._jobs[preparation.source_key(draft())][1].cancelled()
    gate.set()
    assert await second and checked.await_count == 1


@pytest.mark.asyncio
async def test_other_owner_edited_source_or_work_cannot_reuse_preparation(monkeypatch):
    monkeypatch.setattr(lesson, 'checked_plan', AsyncMock(return_value=lesson.Plan.model_validate(candidate())))
    await preparation.prepare(draft())
    await asyncio.sleep(0)
    for changes in ({'owner': 'student-b'}, {'problemText': SOURCE.replace('8m', '9m')}, {'workText': 'Bài em vừa viết.', 'workConfirmed': True}):
        assert await preparation.prepared_plan(confirmed(**changes)) is None
    with pytest.raises(ValidationError):
        lesson.LessonRequest(owner='student-a', problemText=SOURCE, problemConfirmed=False)
    assert not lesson._sessions


@pytest.mark.asyncio
async def test_failed_warmup_cannot_publish_or_poison_explicit_retry(monkeypatch):
    checked = AsyncMock(side_effect=[TutorUnavailable('validation'), lesson.Plan.model_validate(candidate())])
    monkeypatch.setattr(lesson, 'checked_plan', checked)
    await preparation.prepare(draft())
    await asyncio.sleep(0)
    assert await preparation.prepare(draft()) == {'phase': 'unavailable'}
    assert not lesson._sessions
    assert await lesson.reviewed_plan(confirmed(), [])
    assert checked.await_count == 2


@pytest.mark.asyncio
async def test_expired_completed_preparation_is_not_reused(monkeypatch):
    monkeypatch.setattr(lesson, 'checked_plan', AsyncMock(return_value=lesson.Plan.model_validate(candidate())))
    await preparation.prepare(draft())
    await asyncio.sleep(0)
    key = preparation.source_key(draft())
    preparation._jobs[key] = (0, preparation._jobs[key][1])
    assert await preparation.prepared_plan(confirmed()) is None and not preparation._jobs


@pytest.mark.asyncio
async def test_bounded_background_work_and_unknown_symbols_do_not_spend_more_calls(monkeypatch):
    async def slow(request): await asyncio.sleep(20)
    checked = AsyncMock(side_effect=slow)
    monkeypatch.setattr(lesson, 'checked_plan', checked)
    await preparation.prepare(draft())
    assert await preparation.prepare(draft(problemText=SOURCE+' ')) == {'phase': 'preparing'}
    assert await preparation.prepare(draft(problemText=SOURCE.replace('8m', '9m'))) == {'phase': 'busy'}
    await preparation.prepare(draft(owner='student-b'))
    assert await preparation.prepare(draft(owner='student-c')) == {'phase': 'busy'}
    with pytest.raises(ValidationError): draft(problemText='Có [?] viên gạch.')
    await asyncio.sleep(0)
    assert checked.await_count == 2


@pytest.mark.asyncio
async def test_labelled_parts_open_source_reading_without_waiting_for_model(monkeypatch):
    gate = asyncio.Event()
    async def slow(request):
        await gate.wait()
        return lesson.Plan.model_validate(candidate())
    monkeypatch.setattr(lesson, 'checked_plan', AsyncMock(side_effect=slow))
    response = await asyncio.wait_for(lesson.start_lesson(confirmed(guidedUnderstanding=True, startWithReading=True)), 1)
    assert response.preparingMath and response.understandingSteps == 3 and response.step.kind == 'UNDERSTAND'
    session = lesson._sessions[response.sessionId]
    assert session.summary is None  # Neither individual question claims to summarize both parts.
    assert 'Ý a' in session.plan.steps[1].question and 'Ý b' in session.plan.steps[2].question
    assert session.plan.steps[2].correctChoice in SOURCE
    gate.set()
    assert await session.preparation_task
    assert len(session.plan.steps) == 8


@pytest.mark.parametrize('text', [SOURCE+' c) Hỏi còn lại bao nhiêu?', SOURCE+' Bài 4: Tính 7+2?', SOURCE.replace('b)', 'c)')])
def test_unclear_multiple_parts_never_get_guessed_reading_questions(text):
    with pytest.raises(lesson.UnderstandingUnsupported): lesson.labelled_understanding(text)


@pytest.mark.asyncio
async def test_preparation_route_is_internal_and_returns_only_phase(monkeypatch):
    monkeypatch.setattr(settings, 'internal_api_key', 'test-internal')
    monkeypatch.setattr(lesson, 'checked_plan', AsyncMock(return_value=lesson.Plan.model_validate(candidate())))
    app=FastAPI();app.include_router(tutor.router,prefix='/internal/v1/tutor')
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
        payload={'owner':'student-a','problemText':SOURCE}
        denied=await client.post('/internal/v1/tutor/lesson/prepare',json=payload)
        assert denied.status_code == 401 and not preparation._jobs
        result=await client.post('/internal/v1/tutor/lesson/prepare',headers={'X-Internal-API-Key':'test-internal'},json=payload)
        assert result.status_code == 200 and result.json() == {'phase':'preparing'}
        assert result.headers['cache-control'] == 'no-store' and not lesson._sessions
