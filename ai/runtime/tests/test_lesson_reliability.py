"""Regression coverage for lesson preparation failures; no real provider calls."""
import asyncio
import copy
from collections import OrderedDict
from unittest.mock import AsyncMock
import httpx
import pytest
from fastapi import FastAPI
from app.api import tutor
from app.config import settings
from app.tutoring import lesson, service
from _lesson_test_data import step, review_for

SOURCE = "Vườn cây nhà bác Nam có 1/3 số cây là cây táo, 2/5 số cây là cây xoài, còn lại là cây cam. Biết rằng số cây cam có trong vườn là 16 cây Hỏi trong vườn nhà bác Nam có tất cả bao nhiêu cây?"

def test_explicit_question_survives_ocr_sentence_punctuation_loss():
    steps = lesson.source_understanding(SOURCE)
    assert len(steps) == 3
    assert steps[0].correctChoice in SOURCE and steps[1].correctChoice in SOURCE
    assert steps[1].correctChoice.startswith('Hỏi trong vườn')
    with pytest.raises(lesson.UnderstandingUnsupported):
        lesson.source_understanding(SOURCE + ' Hỏi có bao nhiêu cây táo?')

@pytest.mark.asyncio
async def test_missing_punctuation_does_not_wait_for_cloud_before_reading(monkeypatch):
    monkeypatch.setattr(lesson, '_sessions', OrderedDict())
    gate = asyncio.Event()
    async def pending(request):
        await gate.wait()
    monkeypatch.setattr(lesson, 'generate_plan', pending)
    result = await asyncio.wait_for(lesson.start_lesson(lesson.LessonRequest(owner='regression', problemText=SOURCE,
        problemConfirmed=True, guidedUnderstanding=True, startWithReading=True)), timeout=1)
    session = lesson._sessions[result.sessionId]
    try:
        assert result.preparingMath and result.step.kind == 'UNDERSTAND'
        assert result.completed == [] and not result.step.expression
    finally:
        session.preparation_task.cancel()
        await asyncio.gather(session.preparation_task, return_exceptions=True)

@pytest.mark.asyncio
async def test_separate_initial_and_worked_guidance_accepts_valid_draft_without_repair(monkeypatch):
    candidate = dict(topic='Bút', goal='Tìm số bút.', finalAnswerStep=1, steps=[
        step(title='Chọn cách tính', choices=['Gộp các nhóm', 'Bớt một nhóm'], correctChoice='Gộp các nhóm'),
        step(title='Tính số bút', expression='7*9', unit='bút')])
    draft = copy.deepcopy(candidate)
    draft['canSolve'] = True
    for item in draft['steps']:
        item['initialGuidance'] = item['guidance']
        item['guidance'] = ['Sau khi tự làm, đối chiếu phép tính với đề.', 'Đọc lại đơn vị của đại lượng cần tìm.',
            'Kiểm tra các thao tác đã làm theo đúng thứ tự.', 'Ghi câu trả lời đầy đủ và kiểm tra câu hỏi.']
        item['workLineIndexes'] = []
    cloud = AsyncMock(side_effect=[draft, review_for(candidate)])
    monkeypatch.setattr(lesson, '_generate', cloud)
    plan = await lesson.generate_plan(lesson.LessonRequest(owner='regression', problemText='Có 7 hộp, mỗi hộp 9 bút. Hỏi có tất cả bao nhiêu bút?', problemConfirmed=True))
    assert cloud.await_count == 2
    assert len(plan.steps[1].initialGuidance) == 3 and len(plan.steps[1].guidance) == 4
    public = lesson.guidance_at(plan.steps[1], [], {'7','9'}, reveal_work=False)
    assert public == plan.steps[1].initialGuidance and all('Sau khi tự làm' not in x for x in public)

@pytest.mark.asyncio
@pytest.mark.parametrize('primary,secondary,expected', [('rate_limit','unavailable','rate_limit'), ('timeout','configuration','timeout'), ('configuration','configuration','configuration')])
async def test_fallback_preserves_reason_without_extra_provider_attempts(monkeypatch, primary, secondary, expected):
    monkeypatch.setattr(settings,'groq_enabled',True);monkeypatch.setattr(settings,'groq_api_keys','fake-primary')
    monkeypatch.setattr(settings,'gemini_enabled',True);monkeypatch.setattr(settings,'gemini_api_keys','fake-secondary')
    first=AsyncMock(side_effect=service.TutorUnavailable(primary));second=AsyncMock(side_effect=service.TutorUnavailable(secondary))
    monkeypatch.setattr(service,'_call_groq',first);monkeypatch.setattr(service,'_call_gemini',second)
    with pytest.raises(service.TutorUnavailable) as result: await service._generate('prompt','data')
    assert result.value.reason == expected and first.await_count == second.await_count == 1

@pytest.mark.asyncio
@pytest.mark.parametrize('failure,reason', [(ValueError('private model output'),'validation'), (TimeoutError(),'timeout')])
async def test_review_failure_is_typed_and_never_exposes_raw_content(monkeypatch,failure,reason):
    monkeypatch.setattr(lesson,'generate_plan',AsyncMock(side_effect=failure))
    with pytest.raises(service.TutorUnavailable) as result:
        await lesson.reviewed_plan(lesson.LessonRequest(owner='regression',problemText='Tính 7+9.',problemConfirmed=True),[])
    assert result.value.reason == reason and 'private' not in str(result.value)

@pytest.mark.asyncio
@pytest.mark.parametrize('reason', ['rate_limit','validation','timeout','configuration'])
async def test_api_returns_safe_category_for_lesson_failures(monkeypatch,reason):
    monkeypatch.setattr(settings,'internal_api_key','test-internal')
    monkeypatch.setattr(tutor,'start_lesson',AsyncMock(side_effect=service.TutorUnavailable(reason)))
    app=FastAPI();app.include_router(tutor.router,prefix='/internal/v1/tutor')
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
        response=await client.post('/internal/v1/tutor/lesson',headers={'X-Internal-API-Key':'test-internal'},json={
            'owner':'regression','problemText':'Tính 7+9.','problemConfirmed':True})
    assert response.status_code == 503 and response.headers['x-tutor-failure'] == reason
    assert reason not in response.json()['detail']

@pytest.mark.asyncio
async def test_background_failure_keeps_reason_and_never_advances_to_unreviewed_math(monkeypatch):
    monkeypatch.setattr(lesson, '_sessions', OrderedDict())
    generate = AsyncMock(side_effect=service.TutorUnavailable('rate_limit'))
    monkeypatch.setattr(lesson, 'generate_plan', generate)
    source = 'Lan có 12 bút, được tặng thêm 5 bút. Hỏi Lan có tất cả bao nhiêu bút?'
    response = await lesson.start_lesson(lesson.LessonRequest(owner='regression',problemText=source,
        problemConfirmed=True,guidedUnderstanding=True,startWithReading=True))
    session = lesson._sessions[response.sessionId]
    assert await session.preparation_task is False
    for _ in range(2):
        lesson.answer_lesson(lesson.TurnRequest(owner=session.owner,sessionId=response.sessionId,revision=session.revision,
            answer=session.plan.steps[len(session.answers)].correctChoice))
    final = lesson.TurnRequest(owner=session.owner,sessionId=response.sessionId,revision=session.revision,
        answer=session.plan.steps[2].correctChoice)
    await lesson.ready_for_answer(final)
    result = lesson.answer_lesson(final)
    assert session.preparation_failure == 'rate_limit'
    assert result.status == 'RETRYABLE' and result.step is None
    assert session.revision == 3 and len(session.completed) == 3
    assert isinstance(session.plan, lesson.ReadingPlan)
    assert generate.await_count == 1
