"""Cross-provider recovery must retain every local and independent review."""
import asyncio
import copy
import json
from collections import OrderedDict
from unittest.mock import AsyncMock

import pytest
from app.config import settings
from app.tutoring import lesson, service
from _lesson_test_data import step, review_for


SOURCE='Có 7 hộp, mỗi hộp 9 bút. Cho đi 11 bút. Hỏi còn bao nhiêu bút?'


def candidate(expression='7*9'):
    return dict(topic='Số bút',goal='Tìm số bút còn lại.',finalAnswerStep=1,
                steps=[step(title='Tìm số bút ban đầu',expression=expression,unit='bút'),
                       step(title='Tìm số bút còn lại',expression='{s0}-11',unit='bút')])


def request():
    return lesson.LessonRequest(owner='provider-test',problemText=SOURCE,problemConfirmed=True)


@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    monkeypatch.setattr(settings,'groq_enabled',True)
    monkeypatch.setattr(settings,'groq_api_keys','fake-groq')
    monkeypatch.setattr(settings,'gemini_enabled',True)
    monkeypatch.setattr(settings,'gemini_api_keys','fake-gemini')
    monkeypatch.setattr(settings,'lesson_catalog_enabled',False)
    monkeypatch.setattr(service,'_cloud_slots',asyncio.Semaphore(1))
    monkeypatch.setattr(lesson,'_sessions',OrderedDict())


@pytest.mark.asyncio
async def test_preferred_source_is_private_and_does_not_change_json(monkeypatch):
    primary=AsyncMock(return_value={'value':1})
    secondary=AsyncMock(return_value={'value':2})
    monkeypatch.setattr(service,'_call_groq',primary)
    monkeypatch.setattr(service,'_call_gemini',secondary)
    result=await service._generate('policy','source',preferred_provider='gemini',reasoning=True)
    assert result.provider=='gemini' and json.loads(json.dumps(result))=={'value':2}
    assert primary.await_count==0 and secondary.await_count==1
    assert 'reasoning' not in secondary.await_args.kwargs


@pytest.mark.asyncio
async def test_missing_preferred_source_uses_only_configured_source(monkeypatch):
    monkeypatch.setattr(settings,'gemini_enabled',False)
    primary=AsyncMock(return_value={'value':1});secondary=AsyncMock()
    monkeypatch.setattr(service,'_call_groq',primary)
    monkeypatch.setattr(service,'_call_gemini',secondary)
    result=await service._generate('policy','source',preferred_provider='gemini')
    assert result.provider=='groq' and primary.await_count==1 and secondary.await_count==0


@pytest.mark.asyncio
async def test_concurrent_preferences_and_forged_content_cannot_change_provenance(monkeypatch):
    monkeypatch.setattr(service,'_call_groq',AsyncMock(return_value={'provider':'gemini','value':1}))
    monkeypatch.setattr(service,'_call_gemini',AsyncMock(return_value={'value':2}))
    first,second=await asyncio.gather(service._generate('policy','one',preferred_provider='groq'),
                                      service._generate('policy','two',preferred_provider='gemini'))
    assert first.provider=='groq' and first['provider']=='gemini'
    assert second.provider=='gemini' and 'provider' not in second


@pytest.mark.asyncio
async def test_slow_primary_is_cancelled_before_fallback_and_releases_slot(monkeypatch):
    cancelled=asyncio.Event()
    async def stalled(*args,**kwargs):
        try:await asyncio.Event().wait()
        finally:cancelled.set()
    monkeypatch.setattr(service,'PROVIDER_TIMEOUT_SECONDS',.02)
    monkeypatch.setattr(service,'_call_groq',stalled)
    secondary=AsyncMock(return_value={'value':2})
    monkeypatch.setattr(service,'_call_gemini',secondary)
    result=await asyncio.wait_for(service._generate('policy','source',timeout_seconds=24),.5)
    assert cancelled.is_set() and result.provider=='gemini' and secondary.await_count==1
    assert not service._cloud_slots.locked()


@pytest.mark.asyncio
async def test_cancelling_request_never_starts_another_source(monkeypatch):
    entered=asyncio.Event();cancelled=asyncio.Event()
    async def stalled(*args,**kwargs):
        entered.set()
        try:await asyncio.Event().wait()
        finally:cancelled.set()
    monkeypatch.setattr(service,'_call_groq',stalled)
    secondary=AsyncMock();monkeypatch.setattr(service,'_call_gemini',secondary)
    task=asyncio.create_task(service._generate('policy','source'))
    await entered.wait();task.cancel()
    with pytest.raises(asyncio.CancelledError):await task
    assert cancelled.is_set() and not service._cloud_slots.locked() and secondary.await_count==0


@pytest.mark.asyncio
@pytest.mark.parametrize('initial_failure',['local','refusal','unavailable','review'])
async def test_content_failure_switches_source_then_requires_review(monkeypatch,initial_failure):
    events=[];good=candidate()
    async def provider(name,prompt,data,image,**kwargs):
        events.append((name,prompt,json.loads(data)))
        if prompt==lesson.PLAN_PROMPT:
            if initial_failure=='refusal':return {'lesson':None}
            if initial_failure=='unavailable':return {'unavailable':True}
            return candidate('63' if initial_failure=='local' else '7+9')
        if prompt==lesson.REPAIR_PROMPT:return copy.deepcopy(good)
        assert prompt==lesson.REVIEW_PROMPT
        if initial_failure=='review' and len(events)==2:
            return {**review_for(good),'mathematicsCorrect':False,'issues':['The source gives equal groups, not an addition.']}
        return review_for(good)
    async def groq(*args,**kwargs):return await provider('groq',*args,**kwargs)
    async def gemini(*args,**kwargs):return await provider('gemini',*args,**kwargs)
    monkeypatch.setattr(service,'_call_groq',groq);monkeypatch.setattr(service,'_call_gemini',gemini)
    result=await lesson.start_lesson(request())
    expected=[('groq',lesson.PLAN_PROMPT)]
    if initial_failure=='review':expected.append(('gemini',lesson.REVIEW_PROMPT))
    expected.extend([('gemini',lesson.REPAIR_PROMPT),('groq',lesson.REVIEW_PROMPT)])
    assert [(name,prompt) for name,prompt,_ in events]==expected
    assert all(data['problemText']==SOURCE for _,_,data in events)
    assert result.step.expression=='7 × 9' and not result.conclusion
    assert '63' not in result.model_dump_json(exclude={'sessionId'})
    assert 'validationIssue' not in events[-1][2] and 'rejectedCandidate' not in events[-1][2]


@pytest.mark.asyncio
async def test_repair_alternates_actual_fallback_source_not_assumed_primary(monkeypatch):
    events=[]
    async def groq(prompt,data,image,**kwargs):
        events.append(('groq',prompt))
        if prompt==lesson.PLAN_PROMPT:raise service.TutorUnavailable('rate_limit')
        return candidate()
    async def gemini(prompt,data,image,**kwargs):
        events.append(('gemini',prompt))
        return candidate('63') if prompt==lesson.PLAN_PROMPT else review_for(candidate())
    monkeypatch.setattr(service,'_call_groq',groq);monkeypatch.setattr(service,'_call_gemini',gemini)
    plan=await lesson.generate_plan(request())
    assert plan.steps[0].expression=='7*9'
    assert events==[('groq',lesson.PLAN_PROMPT),('gemini',lesson.PLAN_PROMPT),
                    ('groq',lesson.REPAIR_PROMPT),('gemini',lesson.REVIEW_PROMPT)]


@pytest.mark.asyncio
async def test_both_sources_refuse_without_publishing_fake_success(monkeypatch):
    first=AsyncMock(return_value={'unavailable':True});second=AsyncMock(return_value={'lesson':None})
    monkeypatch.setattr(service,'_call_groq',first);monkeypatch.setattr(service,'_call_gemini',second)
    with pytest.raises(service.TutorUnavailable):
        await lesson.start_lesson(lesson.LessonRequest(owner='provider-test',
            problemText='Tổng hai số là 70. Tìm hai số.',problemConfirmed=True))
    assert first.await_count==second.await_count==1 and not lesson._sessions


@pytest.mark.asyncio
async def test_two_plausible_wrong_results_still_cannot_bypass_review(monkeypatch):
    events=[]
    async def wrong(prompt,data,image,**kwargs):
        events.append(prompt)
        return ({**review_for(candidate('7+9')),'answersQuestion':False,'issues':['Wrong relation.']}
                if prompt==lesson.REVIEW_PROMPT else candidate('7+9'))
    monkeypatch.setattr(service,'_call_groq',wrong);monkeypatch.setattr(service,'_call_gemini',wrong)
    with pytest.raises(service.TutorUnavailable):await lesson.start_lesson(request())
    assert events.count(lesson.REVIEW_PROMPT)==2 and not lesson._sessions
