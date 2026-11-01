import io
import json
import threading
import time
import wave
from concurrent.futures import Future, ThreadPoolExecutor
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI
from app.tutoring import lesson, narration, media_preparation as media
from app.tutoring import speech_render as speech
from app.api import tutor
from app.config import settings

SESSION='private-future-lesson-session-123'

def pcm():
    output=io.BytesIO()
    with wave.open(output,'wb') as audio:
        audio.setnchannels(1);audio.setsampwidth(2);audio.setframerate(16000);audio.writeframes(b'\x01\x00'*16000)
    return output.getvalue()

@pytest.fixture
def prepared(monkeypatch):
    plan=lesson.Plan(topic='Phân số',goal='Tìm phần còn lại',steps=[
        lesson.Step(title='Gộp hai phần',explanation='Hai phần cùng nói về một vườn.',question='Hai loại cây chiếm bao nhiêu phần?',expression='1/3+2/5',fractionNotation=True),
        lesson.Step(title='Tìm phần còn lại',explanation='Cây cam chiếm phần còn lại.',question='Cây cam chiếm bao nhiêu phần?',expression='1-{s0}',fractionNotation=True)])
    session=lesson.Session('pupil-a',plan,time.monotonic()+600,givens=frozenset({'1','2','3','5','16'}))
    monkeypatch.setattr(lesson,'_sessions',{SESSION:session})
    with media._lock: media._jobs.clear()
    narration._cache.clear();narration._progress.clear();narration._background_pause_until=0
    lesson.present(SESSION,session)
    calls=[]
    def render(parts,voice,progress=None,**kwargs):calls.append((parts,voice));return pcm()
    monkeypatch.setattr(narration,'render_audio',render)
    model=AsyncMock();monkeypatch.setattr(lesson,'_generate',model)
    yield session,calls,model
    with media._lock:
        for job in media._jobs.values():job.stopped=True
        media._jobs.clear()


def request(**changes):return media.PrepareRequest(owner='pupil-a',sessionId=SESSION,revision=0,**changes)


def test_future_projection_never_advances_or_publishes_private_teaching(prepared):
    session,calls,model=prepared
    before=list(session.narration_texts)
    projected=media.scripts_for(session)
    assert len(projected)==2 and session.answers==[] and session.completed==[] and session.revision==0
    assert session.narration_texts==before
    assert '{s0}' not in ' '.join(projected[1])
    assert '4/15' not in json.dumps(projected[0])
    model.assert_not_called()


def test_all_steps_and_two_voices_are_ready_before_the_future_step_opens(prepared):
    session,calls,model=prepared
    first=media.schedule(request(voice=speech.SPEECH_VOICES[1]))
    assert first['preparedSteps']==0 and first['totalSteps']==2
    job=media._jobs[SESSION]
    media._run()
    assert len(calls)==10 and [call[1] for call in calls[:2]]==[speech.SPEECH_VOICES[1],speech.SPEECH_VOICES[0]]
    assert media.schedule(request(voice=speech.SPEECH_VOICES[1]))['preparedSteps']==2
    assert len(job.ready)==10
    future_parts=job.scripts[1]
    future=narration.NarrationRequest(owner='pupil-a',sessionId=SESSION,revision=0,paragraphs=future_parts,voice=speech.SPEECH_VOICES[1])
    with pytest.raises(ValueError):narration.narrate(future)
    lesson.answer_lesson(lesson.TurnRequest(owner='pupil-a',sessionId=SESSION,revision=0,answer='11/15'))
    public=lesson.present(SESSION,session).step
    assert media.script_for_step(public)==future_parts
    assert narration.narrate(future.model_copy(update={'revision':1}))==pcm() and len(calls)==10
    model.assert_not_called()


def test_repeated_prepare_requests_do_not_generate_more_speech(prepared):
    _,calls,_=prepared
    media.schedule(request());media._run()
    for _ in range(10):media.schedule(request())
    media._run()
    assert len(calls)==10


def test_checked_plan_refresh_keeps_both_unchanged_voices_and_cancels_changed_text(prepared,monkeypatch):
    session,_,_=prepared
    media.schedule(request()); previous=media._jobs[SESSION]
    previous.characters=55;previous.reserved_characters=22
    signals={}
    for voice in speech.SPEECH_VOICES:
        for index in (0,1):
            key=('pupil-a',SESSION,voice,False,tuple(previous.scripts[index]))
            signals[key]=threading.Event()
    monkeypatch.setattr(narration,'_background',signals)
    monkeypatch.setattr(narration,'_public_jobs',{})
    session.plan=session.plan.model_copy(deep=True)
    session.plan.steps[1].question='Em tìm phần còn lại bằng cách nào?'
    media.refresh_after_plan(SESSION,session)
    assert previous.stopped and media._jobs[SESSION] is not previous
    assert media._jobs[SESSION].characters==77
    for voice in speech.SPEECH_VOICES:
        assert not signals[('pupil-a',SESSION,voice,False,tuple(previous.scripts[0]))].is_set()
        assert signals[('pupil-a',SESSION,voice,False,tuple(previous.scripts[1]))].is_set()


@pytest.mark.parametrize('preferred',speech.SPEECH_VOICES)
def test_current_two_voices_are_paired_before_moving_to_the_next_step(prepared,preferred):
    media.schedule(request(voice=preferred));job=media._jobs[SESSION]
    tasks=[]
    for _ in range(3):
        task=media._next(SESSION,job);tasks.append(task);job.attempted.add(task)
    other=next(voice for voice in speech.SPEECH_VOICES if voice!=preferred)
    assert tasks==[(0,preferred),(0,other),(1,preferred)]


def test_two_workers_start_the_current_two_voices_together_without_duplicate_renders(prepared,monkeypatch):
    session,calls,_=prepared
    media.schedule(request());job=media._jobs[SESSION]
    current=job.scripts[0];started=set();lock=threading.Lock()
    paired=threading.Event();release=threading.Event()
    original=narration.render_audio
    def render(parts,voice,*args,**kwargs):
        if parts==current:
            with lock:
                started.add(voice)
                if len(started)==2:paired.set()
            assert release.wait(2)
        return original(parts,voice,*args,**kwargs)
    monkeypatch.setattr(narration,'render_audio',render)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(media._run) for _ in range(2)]
        try:
            assert paired.wait(1),'The other current voice must start before the first voice finishes'
            assert started==set(speech.SPEECH_VOICES)
        finally:release.set()
        for future in futures:future.result(timeout=3)
    assert len(calls)==10 and len({(tuple(parts),voice) for parts,voice in calls})==10
    assert not job.active_tasks and job.reserved_characters==0


def test_parallel_workers_share_one_character_budget(prepared,monkeypatch):
    _,calls,_=prepared
    media.schedule(request());job=media._jobs[SESSION]
    limit=sum(map(len,job.scripts[0]));monkeypatch.setattr(media,'MAX_CHARACTERS',limit)
    entered=threading.Event();release=threading.Event();original=narration.render_audio
    def render(*args,**kwargs):
        entered.set();assert release.wait(2);return original(*args,**kwargs)
    monkeypatch.setattr(narration,'render_audio',render)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first=pool.submit(media._run)
        assert entered.wait(1)
        second=pool.submit(media._run)
        try:second.result(timeout=1)
        finally:release.set()
        first.result(timeout=2)
    assert len(calls)==1 and job.characters==limit and job.reserved_characters==0


def test_checked_step_reviews_and_final_summary_are_prepared_before_they_are_opened(prepared):
    session,calls,_=prepared
    media.schedule(request());media._run()
    job=media._jobs[SESSION]
    review=job.extra_scripts[2];summary=job.extra_scripts[4]
    query=narration.NarrationRequest(owner='pupil-a',sessionId=SESSION,revision=0,paragraphs=summary)
    with pytest.raises(ValueError):narration.narrate(query)
    lesson.answer_lesson(lesson.TurnRequest(owner='pupil-a',sessionId=SESSION,revision=0,answer='11/15'))
    assert review==media.script_for_review(session.completed[-1:])
    assert narration.narrate(query.model_copy(update={'revision':1,'paragraphs':review}))==pcm()
    lesson.answer_lesson(lesson.TurnRequest(owner='pupil-a',sessionId=SESSION,revision=1,answer='4/15'))
    assert summary==media.script_for_review(session.completed)
    # The compact final recap is prepared separately from the richer per-step reviews.
    before=len(calls)
    joined=narration.narrate(query.model_copy(update={'revision':2}))
    narration.validate_audio(joined)
    with wave.open(io.BytesIO(joined),'rb') as audio:assert audio.getnframes()==16000
    assert len(calls)==before==10


def test_current_review_warms_before_distant_steps_without_delaying_current_and_next(prepared):
    session,_,_=prepared
    source='Vườn có 1/3 số cây là táo, 2/5 là xoài, còn lại 16 cây cam. Hỏi có tất cả bao nhiêu cây?'
    session.plan=lesson.prepend_understanding(session.plan,lesson.source_understanding(source))
    media.schedule(request());job=media._jobs[SESSION]
    tasks=[]
    for _ in range(4):
        task=media._next(SESSION,job);tasks.append(task);job.attempted.add(task)
    assert tasks==[(0,speech.DEFAULT_VOICE),(0,speech.SPEECH_VOICES[1]),
                   (1,speech.DEFAULT_VOICE),(1,speech.SPEECH_VOICES[1])]


@pytest.mark.parametrize('expired',[False,True])
def test_missing_nearby_audio_rewarms_both_voices_after_cache_eviction(prepared,expired):
    session,calls,_=prepared
    media.schedule(request());media._run();job=media._jobs[SESSION]
    selected=job.voice;other=next(voice for voice in speech.SPEECH_VOICES if voice!=selected)
    def key(index,voice):return (session.owner,SESSION,voice,False,tuple(job.scripts[index]))
    if expired:narration._cache[key(0,selected)]=(time.monotonic()-1,pcm())
    else:narration._cache.pop(key(0,selected))
    narration._cache.pop(key(1,other));before=len(calls)
    media.schedule(request())
    assert (0,selected) not in job.ready and (1,other) not in job.attempted
    media._run()
    assert len(calls)==before+2 and {(tuple(parts),voice) for parts,voice in calls[before:]}=={(tuple(job.scripts[0]),selected),(tuple(job.scripts[1]),other)}
    assert key(0,selected) in narration._cache and key(1,other) in narration._cache
    assert media.schedule(request())['preparedSteps']==len(job.scripts)


@pytest.mark.parametrize('limit',['failure','characters'])
def test_evicted_audio_repair_does_not_bypass_failure_or_character_budget(prepared,limit):
    session,calls,_=prepared
    media.schedule(request());media._run();job=media._jobs[SESSION]
    narration._cache.pop((session.owner,SESSION,job.voice,False,tuple(job.scripts[0])))
    if limit=='failure':job.voice_failures[job.voice]=2
    else:job.characters=media.MAX_CHARACTERS
    before=len(calls);media.schedule(request());media._run()
    assert len(calls)==before and media.schedule(request())['preparedSteps']==len(job.scripts)-1


@pytest.mark.parametrize('voice',speech.SPEECH_VOICES)
def test_understanding_reviews_are_warm_but_private_until_the_correct_answer(prepared,voice):
    session,calls,model=prepared
    source='Vườn có 1/3 số cây là táo, 2/5 là xoài, còn lại 16 cây cam. Hỏi có tất cả bao nhiêu cây?'
    session.plan=lesson.prepend_understanding(session.plan,lesson.source_understanding(source))
    session.narration_texts.clear();lesson.present(SESSION,session)
    media.schedule(request(voice=voice));media._run()
    job=media._jobs[SESSION];count=len(session.plan.steps);rendered=len(calls)
    assert job.characters<=media.MAX_CHARACTERS
    for index in range(3):
        review=job.extra_scripts[count+index]
        query=narration.NarrationRequest(owner=session.owner,sessionId=SESSION,revision=session.revision,
            paragraphs=review,voice=voice)
        with pytest.raises(ValueError):narration.narrate(query)
        with pytest.raises(lesson.LessonExpired):narration.narrate(query.model_copy(update={'owner':'other'}))
        current=session.plan.steps[index]
        result=lesson.answer_lesson(lesson.TurnRequest(owner=session.owner,sessionId=SESSION,
            revision=session.revision,answer=current.correctChoice))
        assert review==media.script_for_review(result.completed[-1:])
        assert narration.narrate(query.model_copy(update={'revision':session.revision}))==pcm()
        assert len(calls)==rendered
    for answer in ['11/15','4/15']:
        lesson.answer_lesson(lesson.TurnRequest(owner=session.owner,sessionId=SESSION,
            revision=session.revision,answer=answer))
    summary=job.extra_scripts[2*count]
    assert summary==media.script_for_review([step for step in session.completed if step.kind!='UNDERSTAND'])
    narration.narrate(query.model_copy(update={'revision':session.revision,'paragraphs':summary}))
    assert len(calls)==rendered
    model.assert_not_called()




def test_advancing_steps_yields_unused_previous_step_audio(prepared,monkeypatch):
    session,_,_=prepared
    media.schedule(request());job=media._jobs[SESSION];job.active_tasks.add((0,speech.DEFAULT_VOICE))
    yielded=[];monkeypatch.setattr(narration,'cancel_preparation',lambda *args:yielded.append(args))
    lesson.answer_lesson(lesson.TurnRequest(owner=session.owner,sessionId=SESSION,revision=0,answer='11/15'))
    media.schedule(request().model_copy(update={'revision':1}))
    assert yielded==[(session.owner,SESSION,speech.DEFAULT_VOICE,1)]
    assert media._next(SESSION,job)==(2,speech.DEFAULT_VOICE)  # Review the just-solved step before looking ahead.


@pytest.mark.parametrize('foreground_waiting',[False,True])
def test_voice_change_keeps_the_other_current_voice_in_flight(prepared,foreground_waiting):
    media.schedule(request())
    parts=media._jobs[SESSION].scripts[0]
    key=narration.request_key(narration.NarrationRequest(owner='pupil-a',sessionId=SESSION,revision=0,paragraphs=parts))
    cancellation=threading.Event()
    narration._background[key]=cancellation
    if foreground_waiting:narration._foreground_waiters[key]=1
    try:
        media.schedule(request(voice=speech.SPEECH_VOICES[1]))
        assert not cancellation.is_set()
        assert media._next(SESSION,media._jobs[SESSION])==(0,speech.SPEECH_VOICES[1])
    finally:
        narration._background.pop(key,None);narration._foreground_waiters.pop(key,None)


def test_status_counts_only_audio_still_available_after_eviction_and_expiry(prepared):
    media.schedule(request());media._run()
    assert media.schedule(request())['preparedSteps']==2
    with narration._cache_lock:
        key=next(key for key in narration._cache if key[2]==speech.DEFAULT_VOICE)
        narration._cache.pop(key)
    assert media.schedule(request())['preparedSteps']==1
    with narration._cache_lock:
        for key,(expires,data) in list(narration._cache.items()):
            narration._cache[key]=(time.monotonic()-1,data)
    assert media.schedule(request())['preparedSteps']==0


def test_jobs_are_owner_bound_and_abandoned_lessons_are_discarded(prepared):
    session,_,_=prepared
    with pytest.raises(lesson.LessonExpired):media.schedule(request().model_copy(update={'owner':'other'}))
    with pytest.raises(lesson.StaleTurn):media.schedule(request().model_copy(update={'revision':1}))
    media.schedule(request());old=media._jobs[SESSION]
    other='new-private-lesson-session-123'
    lesson._sessions[other]=lesson.Session(session.owner,session.plan,time.monotonic()+600,givens=session.givens)
    media.schedule(request().model_copy(update={'sessionId':other}))
    assert old.stopped and SESSION not in media._jobs and other in media._jobs


def test_text_budget_and_provider_failure_do_not_loop_or_poison_on_demand(prepared,monkeypatch):
    _,calls,_=prepared
    monkeypatch.setattr(media,'MAX_CHARACTERS',1)
    media.schedule(request());media._run();assert calls==[]
    media._jobs.clear();monkeypatch.setattr(media,'MAX_CHARACTERS',72000)
    failures=[]
    def fail(*args,**kwargs):failures.append(1);raise RuntimeError('provider down')
    monkeypatch.setattr(narration,'render_audio',fail)
    media.schedule(request());media._run();assert len(failures)==4
    monkeypatch.setattr(narration,'render_audio',lambda *args,**kwargs:pcm())
    assert narration.narrate(narration.NarrationRequest(owner='pupil-a',sessionId=SESSION,revision=0,paragraphs=media._jobs[SESSION].scripts[0]))==pcm()


def test_failure_of_other_voice_keeps_all_preferred_future_steps(prepared,monkeypatch):
    _,calls,_=prepared
    original=narration.render_audio
    def render(parts,voice,*args,**kwargs):
        if voice!=speech.DEFAULT_VOICE: raise RuntimeError('one voice unavailable')
        return original(parts,voice,*args,**kwargs)
    monkeypatch.setattr(narration,'render_audio',render)
    media.schedule(request());media._run()
    status=media.schedule(request())
    assert status['preparedSteps']==2 and status['failedItems']==2 and len(calls)==5


def test_separated_transient_failures_do_not_disable_the_remaining_voice(prepared,monkeypatch):
    _,calls,_=prepared
    original=narration.render_audio
    preferred_attempts=0
    def render(parts,voice,*args,**kwargs):
        nonlocal preferred_attempts
        if voice==speech.DEFAULT_VOICE:
            preferred_attempts+=1
            if preferred_attempts in {1,3}:raise TimeoutError('temporary outage')
        return original(parts,voice,*args,**kwargs)
    monkeypatch.setattr(narration,'render_audio',render)
    media.schedule(request());media._run()
    job=media._jobs[SESSION]
    assert job.failures==2 and job.voice_failures[speech.DEFAULT_VOICE]==0
    assert len(job.ready)==10 and not job.retry
    assert media.schedule(request())['preparedSteps']==2
    assert {voice for _,voice in calls}==set(speech.SPEECH_VOICES)


def test_transient_missing_step_retries_once_after_untouched_steps_and_other_voice(prepared,monkeypatch):
    _,calls,_=prepared
    original=narration.render_audio
    attempts=[]
    def render(parts,voice,*args,**kwargs):
        attempts.append((parts,voice))
        if len(attempts)==1: raise TimeoutError('temporary outage')
        return original(parts,voice,*args,**kwargs)
    monkeypatch.setattr(narration,'render_audio',render)
    media.schedule(request());media._run()
    assert len(attempts)==11 and attempts[0]==attempts[-1] and len(calls)==10
    assert media.schedule(request())['preparedSteps']==2


def test_budget_exhaustion_discards_deferred_retry_without_looping(prepared):
    _,calls,_=prepared
    media.schedule(request());job=media._jobs[SESSION]
    job.attempted.update((i,voice) for i in range(len(job.scripts)) for voice in speech.SPEECH_VOICES)
    job.retry.add((0,speech.DEFAULT_VOICE));job.characters=media.MAX_CHARACTERS
    media._run()
    assert not job.retry and not calls



def test_foreground_pressure_cancels_speculation_and_reserves_a_retry_window(prepared,monkeypatch):
    session,_,_=prepared
    session.narration_texts.append('Câu hỏi mới đã công bố.')
    began=threading.Event()
    def render(parts,voice,progress=None,*,cancel_event=None,**kwargs):
        if cancel_event is not None:
            began.set();assert cancel_event.wait(2);raise InterruptedError()
        return pcm()
    monkeypatch.setattr(narration,'render_audio',render)
    private=narration.NarrationRequest(owner='pupil-a',sessionId=SESSION,revision=0,paragraphs=['Đoạn tương lai.'])
    explicit=private.model_copy(update={'paragraphs':['Câu hỏi mới đã công bố.']})
    with ThreadPoolExecutor(max_workers=1) as executor:
        future=executor.submit(narration.prepare_private,private,session)
        assert began.wait(1)
        assert narration._render_slot.acquire(blocking=False)
        try:
            with pytest.raises(narration.NarrationBusy):narration.narrate(explicit)
            with pytest.raises(narration.NarrationBusy):future.result(timeout=1)
            assert narration.narrate(explicit)==pcm()
            with pytest.raises(narration.NarrationBusy):narration.prepare_private(private,session)
        finally:narration._render_slot.release()


def test_worker_warms_the_current_other_voice_while_the_preferred_voice_is_rendering(prepared,monkeypatch):
    session,calls,_=prepared
    media.schedule(request());job=media._jobs[SESSION]
    current_parts=job.scripts[0];other_voice=speech.SPEECH_VOICES[1]
    key=narration.request_key(narration.NarrationRequest(owner=session.owner,sessionId=SESSION,revision=0,paragraphs=current_parts))
    pending=Future();narration._inflight[key]=pending
    assert narration._render_slot.acquire(blocking=False)
    held=True;next_warmed=[];original=narration.render_audio
    def render(parts,voice,*args,**kwargs):
        nonlocal held
        if parts==current_parts and voice==other_voice and not next_warmed:
            assert not pending.done()
            next_warmed.append(True)
            with narration._cache_lock:
                narration._store_audio(key,session,pcm());pending.set_result(pcm());narration._inflight.pop(key)
            narration._render_slot.release();held=False
        return original(parts,voice,*args,**kwargs)
    monkeypatch.setattr(narration,'render_audio',render)
    try:
        assert media._next(SESSION,job)==(0,other_voice)
        media._run()
        assert next_warmed and pending.done() and calls[0]==(current_parts,other_voice)
        assert (current_parts,speech.DEFAULT_VOICE) not in calls
        assert media.schedule(request())['preparedSteps']==2
    finally:
        narration._inflight.pop(key,None)
        if held:narration._render_slot.release()


def test_all_pending_candidates_keep_the_worker_scheduled_without_a_new_task(prepared):
    session,_,_=prepared
    media.schedule(request());job=media._jobs[SESSION]
    candidates={(0,speech.DEFAULT_VOICE),(1,speech.DEFAULT_VOICE)}
    job.attempted.update((index,voice) for index in media.script_ids(job) for voice in speech.SPEECH_VOICES
        if (index,voice) not in candidates)
    keys=[]
    try:
        for index,_ in candidates:
            key=(session.owner,SESSION,speech.DEFAULT_VOICE,False,tuple(job.scripts[index]))
            keys.append(key);narration._inflight[key]=Future()
        assert media._next(SESSION,job)==(0,speech.DEFAULT_VOICE)
        assert all(not narration._inflight[key].done() for key in keys)
    finally:
        for key in keys:narration._inflight.pop(key,None)


def test_worker_warms_another_pupil_instead_of_waiting_for_an_existing_render(prepared,monkeypatch):
    session,calls,_=prepared
    other_id='second-pupil-private-lesson-123'
    other_plan=session.plan.model_copy(deep=True)
    other_plan.steps[0].explanation='Bài học riêng của bạn thứ hai.'
    other_session=lesson.Session('pupil-b',other_plan,time.monotonic()+600,givens=session.givens)
    lesson._sessions[other_id]=other_session;lesson.present(other_id,other_session)
    media.schedule(request())
    media.schedule(media.PrepareRequest(owner=other_session.owner,sessionId=other_id,revision=0))
    first_parts=media._jobs[SESSION].scripts[0]
    other_parts=media._jobs[other_id].scripts[0]
    key=narration.request_key(narration.NarrationRequest(owner=session.owner,sessionId=SESSION,revision=0,paragraphs=first_parts))
    class PendingRender(Future):
        def result(self,timeout=None):
            assert self.done(), 'The worker must reach the other pupil before joining this render'
            return super().result(timeout=timeout)
    pending=PendingRender();narration._inflight[key]=pending
    assert narration._render_slot.acquire(blocking=False)
    held=True;original=narration.render_audio;other_warmed=[]
    def render(parts,voice,*args,**kwargs):
        nonlocal held
        if parts==other_parts and voice==speech.DEFAULT_VOICE and not other_warmed:
            assert not pending.done()
            other_warmed.append(True)
            with narration._cache_lock:
                narration._store_audio(key,session,pcm());pending.set_result(pcm());narration._inflight.pop(key)
            narration._render_slot.release();held=False
        return original(parts,voice,*args,**kwargs)
    monkeypatch.setattr(narration,'render_audio',render)
    try:
        media._run()
        assert other_warmed and pending.done()
        assert (first_parts,speech.DEFAULT_VOICE) not in calls
        assert media.schedule(request())['preparedSteps']==2
        assert media.schedule(media.PrepareRequest(owner=other_session.owner,sessionId=other_id,revision=0))['preparedSteps']==2
    finally:
        narration._inflight.pop(key,None)
        if held:narration._render_slot.release()


@pytest.mark.asyncio
async def test_prepare_endpoint_requires_internal_key_and_returns_counts_only(prepared,monkeypatch):
    monkeypatch.setattr(settings,'internal_api_key','prepare-test-only')
    app=FastAPI();app.include_router(tutor.router)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
        body=request().model_dump()
        assert (await client.post('/lesson/media/prepare',json=body)).status_code==401
        response=await client.post('/lesson/media/prepare',json=body,headers={'X-Internal-API-Key':'prepare-test-only'})
        assert response.status_code==200
        assert set(response.json())=={'totalSteps','preparedSteps','preparedCharacters','failedItems'}
        assert 'correctChoice' not in response.text and 'paragraphs' not in response.text and 'videoId' not in response.text


@pytest.mark.asyncio
async def test_answer_route_cancels_only_owned_obsolete_warmups_after_a_valid_turn(prepared,monkeypatch):
    monkeypatch.setattr(settings,'internal_api_key','prepare-test-only')
    cancelled=[];monkeypatch.setattr(narration,'cancel_obsolete_prefetch',lambda *args:cancelled.append(args))
    app=FastAPI();app.include_router(tutor.router)
    body={'owner':'pupil-a','sessionId':SESSION,'revision':0,'answer':'11/15'}
    headers={'X-Internal-API-Key':'prepare-test-only'}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
        assert (await client.post('/lesson/answer',json={**body,'owner':'other'},headers=headers)).status_code==410
        assert not cancelled
        response=await client.post('/lesson/answer',json=body,headers=headers)
        assert response.status_code==200 and response.json()['revision']==1
        assert cancelled==[('pupil-a',SESSION,1)]


@pytest.mark.asyncio
async def test_creating_lesson_automatically_schedules_but_optional_failure_does_not_break_it(prepared,monkeypatch):
    session,_,_=prepared
    monkeypatch.setattr(settings,'internal_api_key','prepare-test-only')
    monkeypatch.setattr(tutor,'start_lesson',AsyncMock(return_value=lesson.present(SESSION,session)))
    app=FastAPI();app.include_router(tutor.router)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
        body={'owner':'pupil-a','problemText':'Có 16 cây cam.','problemConfirmed':True}
        response=await client.post('/lesson',json=body,headers={'X-Internal-API-Key':'prepare-test-only'})
        assert response.status_code==200 and SESSION in media._jobs
        assert 'Đoạn tương lai' not in response.text and 'correctChoice' not in response.text
        monkeypatch.setattr(media,'schedule',lambda _: (_ for _ in ()).throw(RuntimeError('worker unavailable')))
        response=await client.post('/lesson',json=body,headers={'X-Internal-API-Key':'prepare-test-only'})
        assert response.status_code==200
