import io
import time
import wave
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from app.tutoring import lesson


def pcm(silent=False):
    output = io.BytesIO()
    with wave.open(output, 'wb') as sound:
        sound.setnchannels(1); sound.setsampwidth(2); sound.setframerate(16000)
        sound.writeframes((b'\x00\x00' if silent else b'\x01\x00') * 16000)
    return output.getvalue()


@pytest.fixture
def audio_session(monkeypatch):
    from app.tutoring import narration
    session = SimpleNamespace(owner='pupil-a', revision=2, expires=time.monotonic()+90,
                              narration_texts=['Em gộp hai nhóm bút.', 'Em cộng hàng đơn vị trước.'])
    monkeypatch.setattr(lesson, '_sessions', {'narration-session-12345': session})
    narration._cache.clear()
    narration._progress.clear()
    narration._checkpoints.clear()
    return session


def test_explicit_new_audio_yields_full_speculative_jobs_but_keeps_the_other_current_voice(audio_session,monkeypatch):
    from app.tutoring import narration
    request=narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,
        paragraphs=[audio_session.narration_texts[0]])
    same=narration.request_key(request.model_copy(update={'voice':'vi-VN-HoaiMyNeural'}))
    old=narration.request_key(request.model_copy(update={'paragraphs':[audio_session.narration_texts[1]]}))
    same_cancel,old_cancel=threading.Event(),threading.Event()
    jobs={key:dict(future=Future(),finished=False,prefetch=True,cancel=cancel,expires=audio_session.expires)
          for key,cancel in [(same,same_cancel),(old,old_cancel)]}
    monkeypatch.setattr(narration,'_public_jobs',jobs)
    monkeypatch.setattr(narration,'_prepare_slots',threading.BoundedSemaphore(0))
    monkeypatch.setattr(narration,'_foreground_waiters',{})
    monkeypatch.setattr(narration,'_background',{same:same_cancel,old:old_cancel})
    monkeypatch.setattr(narration,'_background_pause_until',0)
    with pytest.raises(narration.NarrationBusy):narration.prepare_narration(request)
    assert old_cancel.is_set() and not same_cancel.is_set()
    assert narration._background_pause_until>time.monotonic()


def test_foreground_render_pressure_keeps_the_other_current_voice_and_yields_only_unrelated_audio(audio_session,monkeypatch):
    from app.tutoring import narration
    request=narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,
        paragraphs=[audio_session.narration_texts[0]])
    same=narration.request_key(request.model_copy(update={'voice':'vi-VN-HoaiMyNeural'}))
    old=narration.request_key(request.model_copy(update={'paragraphs':[audio_session.narration_texts[1]]}))
    same_cancel,old_cancel=threading.Event(),threading.Event()
    monkeypatch.setattr(narration,'_render_slot',threading.BoundedSemaphore(0))
    monkeypatch.setattr(narration,'_foreground_waiters',{})
    monkeypatch.setattr(narration,'_background',{same:same_cancel,old:old_cancel})
    monkeypatch.setattr(narration,'_background_pause_until',0)
    with pytest.raises(narration.NarrationBusy):narration.narrate(request)
    assert old_cancel.is_set() and not same_cancel.is_set()


def test_private_narration_renders_once_and_replays_without_model_calls(audio_session, monkeypatch):
    from app.tutoring import narration
    rendered = []
    monkeypatch.setattr(narration, 'render_audio', lambda parts, voice, progress=None, **kwargs: rendered.append((parts, voice)) or pcm())
    request = narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,
                                         paragraphs=['Em gộp hai nhóm bút.'])
    first = narration.narrate(request)
    assert first[:4] == b'RIFF' and narration.narrate(request) == first
    assert len(rendered) == 1
    with pytest.raises(lesson.LessonExpired): narration.narrate(request.model_copy(update={'owner':'other'}))
    with pytest.raises(lesson.StaleTurn): narration.narrate(request.model_copy(update={'revision':1}))
    with pytest.raises(ValueError): narration.narrate(request.model_copy(update={'paragraphs':['Unpublished answer = 999']}))


def test_response_is_rejected_if_the_opened_lesson_changes_while_rendering(audio_session, monkeypatch):
    from app.tutoring import narration
    def render(_, voice, progress=None, **kwargs):
        audio_session.revision += 1
        return pcm()
    monkeypatch.setattr(narration, 'render_audio', render)
    request = narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'])
    with pytest.raises(lesson.StaleTurn): narration.narrate(request)
    assert not narration._cache


def test_completed_provider_chunks_survive_failure_privately_then_are_released_on_success(audio_session,monkeypatch):
    from app.tutoring import narration
    from app.tutoring.service import TutorUnavailable
    request=narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'])
    calls=[]
    def render(parts,voice,progress=None,*,checkpoint,**kwargs):
        calls.append(voice)
        if len(calls)==1:
            checkpoint[1](0,b'a'*128);raise TutorUnavailable()
        assert checkpoint[0](0)==b'a'*128
        return pcm()
    monkeypatch.setattr(narration,'render_audio',render)
    assert narration.narrate(request)==pcm()
    assert len(calls)==2 and not narration._checkpoints
    with pytest.raises(lesson.LessonExpired):narration.narrate(request.model_copy(update={'owner':'other'}))
    assert len(calls)==2


def test_automatic_partial_recovery_is_bounded_and_respects_the_total_deadline(audio_session,monkeypatch):
    from app.tutoring import narration
    from app.tutoring.service import TutorUnavailable
    request=narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'])
    calls=[]
    def render(parts,voice,progress=None,*,checkpoint,deadline,**kwargs):
        calls.append(deadline);checkpoint[1](0,b'a'*128);raise TutorUnavailable()
    monkeypatch.setattr(narration,'render_audio',render)
    with pytest.raises(TutorUnavailable):narration.narrate(request)
    assert len(calls)==2 and calls[0]==calls[1]
    calls.clear();monkeypatch.setattr(narration,'PUBLIC_TIMEOUT_SECONDS',.01)
    with pytest.raises(TutorUnavailable):narration.narrate(request)
    assert len(calls)==1


def test_a_failed_shared_future_is_retryable_while_its_owner_is_releasing_capacity(audio_session):
    from app.tutoring import narration
    from app.tutoring.service import TutorUnavailable
    request=narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'])
    key=narration.request_key(request);previous=Future();previous.set_exception(TutorUnavailable())
    narration._inflight[key]=previous
    try:
        with pytest.raises(narration.NarrationBusy):narration.narrate(request)
    finally:narration._inflight.pop(key,None)


def test_private_warmup_yields_an_inflight_asset_without_waiting_but_foreground_joins(audio_session,monkeypatch):
    from app.tutoring import narration
    waits=[];renders=[]
    class ObservedFuture(Future):
        def result(self,timeout=None):
            waits.append(timeout)
            assert self.done(), 'Private warm-up must not block the global worker on this future'
            return super().result(timeout=timeout)
    pending=ObservedFuture()
    request=narration.NarrationRequest(owner=audio_session.owner,sessionId='narration-session-12345',revision=2,
        paragraphs=['Em gộp hai nhóm bút.'])
    key=narration.request_key(request);narration._inflight[key]=pending
    monkeypatch.setattr(narration,'render_audio',lambda *args,**kwargs:renders.append(1) or pcm())
    try:
        with pytest.raises(narration.NarrationBusy):narration.prepare_private(request,audio_session)
        assert not waits and not renders and narration._inflight[key] is pending
        pending.set_result(pcm())
        assert narration.narrate(request)==pcm()
        assert len(waits)==1 and not renders and key not in narration._foreground_waiters
    finally:narration._inflight.pop(key,None)


def test_chunk_checkpoints_are_voice_content_owner_scoped_and_have_a_memory_and_time_limit(audio_session,monkeypatch):
    from app.tutoring import narration
    request=narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'])
    read,write=narration.chunk_checkpoint(request,audio_session)
    write(0,b'a'*128);assert read(0)==b'a'*128
    for changes in ({'owner':'other'},{'voice':'vi-VN-HoaiMyNeural'},{'paragraphs':['Nội dung khác.']},{'sessionId':'other-session-key-12345'}):
        assert narration.chunk_checkpoint(request.model_copy(update=changes),audio_session)[0](0) is None
    monkeypatch.setattr(narration,'MAX_CHECKPOINT_BYTES',128)
    _,write_other=narration.chunk_checkpoint(request.model_copy(update={'voice':'vi-VN-HoaiMyNeural'}),audio_session)
    write_other(0,b'b'*128)
    assert sum(len(part) for _,parts in narration._checkpoints.values() for part in parts.values())<=128
    for key,(_,parts) in list(narration._checkpoints.items()):narration._checkpoints[key]=(time.monotonic()-1,parts)
    assert narration.chunk_checkpoint(request.model_copy(update={'voice':'vi-VN-HoaiMyNeural'}),audio_session)[0](0) is None
    assert not narration._checkpoints


def test_preparation_returns_before_synthesis_and_duplicate_polling_does_not_start_more_work(audio_session,monkeypatch):
    from app.tutoring import narration
    started=threading.Event();release=threading.Event();calls=[]
    request=narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'])
    def render(*args,**kwargs):
        calls.append(1);started.set();assert release.wait(2);return pcm()
    monkeypatch.setattr(narration,'render_audio',render)
    began=time.perf_counter();state=narration.prepare_narration(request)
    assert time.perf_counter()-began<.5 and state['phase']!='ready'
    assert started.wait(1)
    try:
        for _ in range(3):assert narration.prepare_narration(request)['phase']!='ready'
        assert len(calls)==1
        with pytest.raises(lesson.LessonExpired):narration.prepare_narration(request.model_copy(update={'owner':'other'}))
    finally:release.set()
    assert narration._public_jobs[narration.request_key(request)]['future'].result(timeout=2) is None
    assert narration.narration_status(request)['phase']=='ready'


def test_exact_cached_parts_join_in_order_without_provider_calls_and_keep_owner_and_voice_checks(audio_session,monkeypatch):
    from app.tutoring import narration
    calls=[]
    def render(parts,*args,**kwargs):
        calls.append(parts)
        data=bytearray(pcm());data[44:]=bytes([len(calls),0])*16000
        return bytes(data)
    monkeypatch.setattr(narration,'render_audio',render)
    request=narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=audio_session.narration_texts)
    for part in request.paragraphs:narration.narrate(request.model_copy(update={'paragraphs':[part]}))
    joined=narration.narrate(request)
    with wave.open(io.BytesIO(joined),'rb') as audio:
        assert audio.getnframes()==32000
        assert audio.readframes(32000)==b'\x01\x00'*16000+b'\x02\x00'*16000
    assert len(calls)==2 and narration.narration_status(request)['phase']=='ready'
    with pytest.raises(lesson.LessonExpired):narration.narrate(request.model_copy(update={'owner':'other'}))
    with pytest.raises(ValueError):narration.narrate(request.model_copy(update={'paragraphs':['Chữ chưa công bố.']}))
    narration.narrate(request.model_copy(update={'voice':'vi-VN-HoaiMyNeural'}))
    assert len(calls)==3


def test_failed_preparation_has_a_terminal_status_and_does_not_retain_audio_or_exception(audio_session,monkeypatch):
    from app.tutoring import narration
    from app.tutoring.service import TutorUnavailable
    calls=[]
    def fail(*args,**kwargs):
        calls.append(1);raise TutorUnavailable()
    monkeypatch.setattr(narration,'render_audio',fail)
    request=narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'])
    narration.prepare_narration(request)
    job=narration._public_jobs[narration.request_key(request)]
    assert job['future'].result(timeout=2) is None
    assert job['failed'] and job['future'].exception() is None and len(calls)==1
    assert narration.narration_status(request)['phase']=='failed'
    assert narration.request_key(request) not in narration._cache


def test_background_result_survives_step_advance_but_stale_public_reads_still_fail(audio_session,monkeypatch):
    from app.tutoring import narration
    began=threading.Event();release=threading.Event();calls=[]
    def render(*args,**kwargs):calls.append(1);began.set();assert release.wait(2);return pcm()
    monkeypatch.setattr(narration,'render_audio',render)
    request=narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'])
    narration.prepare_narration(request);assert began.wait(1)
    try:audio_session.revision=3
    finally:release.set()
    narration._public_jobs[narration.request_key(request)]['future'].result(timeout=2)
    with pytest.raises(lesson.StaleTurn):narration.narrate(request)
    assert narration.narrate(request.model_copy(update={'revision':3}))==pcm()
    assert len(calls)==1


def test_two_obsolete_prefetch_jobs_release_preparation_capacity_promptly(audio_session,monkeypatch):
    from collections import OrderedDict
    from app.tutoring import narration
    monkeypatch.setattr(narration,'_public_jobs',OrderedDict())
    slots=threading.BoundedSemaphore(2);monkeypatch.setattr(narration,'_prepare_slots',slots)
    started=[threading.Event(),threading.Event()]
    def render(parts,voice,*args,cancel_event=None,**kwargs):
        assert cancel_event is not None
        started[voice!='vi-VN-NamMinhNeural'].set()
        assert cancel_event.wait(2)
        raise narration.TutorUnavailable()
    monkeypatch.setattr(narration,'render_audio',render)
    base=narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'],prefetch=True)
    requests=[base,base.model_copy(update={'voice':'vi-VN-HoaiMyNeural'})]
    try:
        for request in requests:narration.prepare_narration(request)
        assert all(event.wait(1) for event in started)
        assert not slots.acquire(blocking=False)
        audio_session.revision=3;began=time.perf_counter()
        narration.cancel_obsolete_prefetch(base.owner,base.sessionId,3)
        for job in narration._public_jobs.values():assert job['future'].result(timeout=1) is None
        assert time.perf_counter()-began<1
        assert slots.acquire(blocking=False) and slots.acquire(blocking=False)
        slots.release();slots.release()
        assert not narration._inflight and not narration._foreground_waiters
    finally:narration.cancel_preparation(base.owner,base.sessionId)


def test_listener_promotes_one_prefetch_render_and_protects_it_from_speculative_cancellation(audio_session,monkeypatch):
    from collections import OrderedDict
    from app.tutoring import narration
    monkeypatch.setattr(narration,'_public_jobs',OrderedDict())
    began=threading.Event();release=threading.Event();calls=[];events=[]
    def render(*args,cancel_event=None,**kwargs):
        calls.append(1);events.append(cancel_event);began.set();assert release.wait(2);return pcm()
    monkeypatch.setattr(narration,'render_audio',render)
    request=narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'],prefetch=True)
    narration.prepare_narration(request);assert began.wait(1)
    key=narration.request_key(request);job=narration._public_jobs[key];future=job['future'];started=job['started']
    try:
        for _ in range(2):narration.prepare_narration(request.model_copy(update={'prefetch':False}))
        assert narration._public_jobs[key]['future'] is future and job['started']==started
        assert not job['prefetch'] and narration._foreground_waiters[key]==1
        audio_session.revision=3
        narration.cancel_obsolete_prefetch(request.owner,request.sessionId,3)
        narration.cancel_preparation(request.owner,request.sessionId,request.voice)
        assert events[0] is not None and not events[0].is_set()
    finally:release.set()
    assert future.result(timeout=1) is None
    assert narration.narrate(request.model_copy(update={'revision':3}))==pcm()
    assert calls==[1] and key not in narration._foreground_waiters
    with pytest.raises(lesson.StaleTurn):narration.narrate(request)


def test_cancelling_a_prefetch_waiter_does_not_wait_for_shared_private_render(audio_session,monkeypatch):
    from collections import OrderedDict
    from app.tutoring import narration
    monkeypatch.setattr(narration,'_public_jobs',OrderedDict())
    began=threading.Event();release=threading.Event()
    def render(*args,**kwargs):began.set();assert release.wait(2);return pcm()
    monkeypatch.setattr(narration,'render_audio',render)
    request=narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'],prefetch=True)
    with ThreadPoolExecutor(max_workers=1) as pool:
        private=pool.submit(narration.prepare_private,request,audio_session);assert began.wait(1)
        try:
            narration.prepare_narration(request)
            job=narration._public_jobs[narration.request_key(request)]
            narration.cancel_obsolete_prefetch(request.owner,request.sessionId,3)
            assert job['future'].result(timeout=1) is None and not private.done()
        finally:release.set()
        assert private.result(timeout=1)==pcm()


def test_promotion_racing_a_yield_resumes_missing_audio_within_original_job(audio_session,monkeypatch):
    from collections import OrderedDict
    from app.tutoring import narration
    monkeypatch.setattr(narration,'_public_jobs',OrderedDict())
    began=threading.Event();interrupted=threading.Event();release=threading.Event();calls=[]
    def render(*args,cancel_event=None,**kwargs):
        calls.append(1)
        if len(calls)==1:
            began.set();assert cancel_event.wait(2);interrupted.set();assert release.wait(2)
            raise narration.TutorUnavailable()
        return pcm()
    monkeypatch.setattr(narration,'render_audio',render)
    request=narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'],prefetch=True)
    narration.prepare_narration(request);assert began.wait(1)
    key=narration.request_key(request);job=narration._public_jobs[key];future=job['future'];started=job['started']
    try:
        narration.cancel_preparation(request.owner,request.sessionId,request.voice)
        assert interrupted.wait(1)
        narration.prepare_narration(request.model_copy(update={'prefetch':False}))
    finally:release.set()
    assert future.result(timeout=1) is None and job['started']==started
    assert narration.narration_status(request)['phase']=='ready' and len(calls)==2


@pytest.mark.parametrize('value',['true',1,None])
def test_prefetch_flag_is_strict_and_does_not_change_audio_identity(value):
    from app.tutoring import narration
    payload=dict(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'])
    with pytest.raises(ValueError):narration.NarrationRequest(**payload,prefetch=value)
    request=narration.NarrationRequest(**payload)
    assert request.prefetch is False and narration.request_key(request)==narration.request_key(request.model_copy(update={'prefetch':True}))


def test_cancelled_old_warmup_is_waiting_for_a_new_revision_not_a_new_failure(audio_session,monkeypatch):
    from collections import OrderedDict
    from app.tutoring import narration
    monkeypatch.setattr(narration,'_public_jobs',OrderedDict())
    request=narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'],prefetch=True)
    old=Future();old.set_result(None);key=narration.request_key(request)
    narration._public_jobs[key]=dict(future=old,failed=True,prefetch=True,revision=2,started=time.monotonic(),expires=audio_session.expires)
    audio_session.revision=3
    assert narration.narration_status(request.model_copy(update={'revision':3}))['phase']=='waiting'
    with pytest.raises(lesson.StaleTurn):narration.narration_status(request)


def test_promotion_after_worker_cleanup_cannot_leak_a_foreground_hold(audio_session,monkeypatch):
    from collections import OrderedDict
    from app.tutoring import narration
    monkeypatch.setattr(narration,'_public_jobs',OrderedDict())
    monkeypatch.setattr(narration,'render_audio',lambda *args,**kwargs:pcm())
    request=narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'])
    narration.narrate(request);key=narration.request_key(request)
    # The executor has not marked Future.done yet, but the worker already
    # released its hold and capacity. A ready-cache tap must not add a new hold.
    old=dict(future=Future(),prefetch=True,revision=2,started=time.monotonic(),expires=audio_session.expires,
             cancel=threading.Event(),hold=False,finished=True)
    narration._public_jobs[key]=old
    assert narration.prepare_narration(request)['phase']=='ready'
    assert key not in narration._foreground_waiters and not old['hold']


def test_background_preparation_stops_at_60_seconds_even_when_chunks_make_progress(audio_session,monkeypatch):
    from app.tutoring import narration
    from app.tutoring.service import TutorUnavailable
    clock=[time.monotonic()];began=clock[0];calls=[]
    audio_session.expires=began+300
    monkeypatch.setattr(narration.time,'monotonic',lambda:clock[0])
    def render(parts,voice,progress=None,**kwargs):
        calls.append(1)
        kwargs['checkpoint'][1](len(calls)-1,b'a'*128)
        clock[0]=min(clock[0]+26,kwargs['deadline'])
        raise TutorUnavailable()
    monkeypatch.setattr(narration,'render_audio',render)
    request=narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'])
    with pytest.raises(TutorUnavailable):narration.prepare_private(request,audio_session)
    assert clock[0]-began==pytest.approx(60) and len(calls)==3
    assert narration.narration_status(request)['phase']=='failed'
    assert narration._checkpoints


@pytest.mark.parametrize('persistent',[False,True])
def test_empty_provider_response_has_one_recovery_within_the_same_deadline_and_voice(audio_session,monkeypatch,persistent):
    from app.tutoring import narration
    calls=[];pauses=[]
    def render(parts,voice,progress=None,**kwargs):
        calls.append((voice,kwargs['deadline']))
        if persistent or len(calls)==1:raise narration.SpeechNoAudio()
        return pcm()
    monkeypatch.setattr(narration,'render_audio',render)
    monkeypatch.setattr(narration.time,'sleep',lambda seconds:pauses.append(seconds))
    request=narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'])
    if persistent:
        with pytest.raises(narration.SpeechNoAudio):narration.prepare_private(request,audio_session)
    else:assert narration.prepare_private(request,audio_session)==pcm()
    assert len(calls)==2 and calls[0]==calls[1] and pauses==[.25]
    assert not narration._inflight


def test_a_previous_failed_public_job_cannot_hide_a_live_private_recovery(audio_session,monkeypatch):
    from app.tutoring import narration
    monkeypatch.setattr(narration,'render_audio',lambda *args,**kwargs:pcm())
    request=narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'])
    narration.narrate(request);key=narration.request_key(request);narration._cache.clear()
    old=Future();old.set_result(None)
    narration._public_jobs[key]={'future':old,'failed':True,'started':time.monotonic(),'expires':audio_session.expires}
    narration._inflight[key]=Future();narration._progress[key]['phase']='synthesizing'
    try:assert narration.narration_status(request)['phase']=='synthesizing'
    finally:narration._inflight.pop(key,None)


@pytest.mark.parametrize('persistent',[False,True])
def test_direct_narration_and_video_audio_share_one_empty_response_recovery(audio_session,monkeypatch,persistent):
    from app.tutoring import narration
    calls=[]
    def render(parts,voice,*args,**kwargs):
        calls.append((voice,kwargs['deadline']))
        if persistent or len(calls)==1:raise narration.SpeechNoAudio()
        return pcm()
    monkeypatch.setattr(narration,'render_audio',render)
    request=narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'])
    if persistent:
        with pytest.raises(narration.SpeechNoAudio):narration.narrate(request)
    else:assert narration.narrate(request)==pcm()
    assert len(calls)==2 and calls[0]==calls[1]


def test_invalid_audio_is_not_cached_and_render_capacity_is_released(audio_session, monkeypatch):
    from app.tutoring import narration
    from app.tutoring.service import TutorUnavailable
    monkeypatch.setattr(narration, 'render_audio', lambda _, voice, progress=None, **kwargs: b'not audio')
    request = narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'])
    with pytest.raises(TutorUnavailable): narration.narrate(request)
    assert not narration._cache
    assert narration._render_slot.acquire(blocking=False)
    assert narration._render_slot.acquire(blocking=False)
    assert not narration._render_slot.acquire(blocking=False)
    narration._render_slot.release()
    narration._render_slot.release()


@pytest.mark.parametrize('data', [pcm(silent=True), pcm()[:-10]], ids=['silent', 'truncated'])
def test_silent_or_truncated_audio_is_rejected(data):
    from app.tutoring import narration
    with pytest.raises(ValueError): narration.validate_audio(data)


def test_the_two_voices_have_separate_private_cache_entries(audio_session, monkeypatch):
    from app.tutoring import narration
    from app.tutoring.speech_render import SPEECH_VOICES
    rendered = []
    monkeypatch.setattr(narration, 'render_audio', lambda parts, voice, progress=None, **kwargs: rendered.append(voice) or pcm())
    request = narration.NarrationRequest(owner='pupil-a', sessionId='narration-session-12345', revision=2,
                                         paragraphs=['Em gộp hai nhóm bút.'])
    for voice in SPEECH_VOICES:
        selected = request.model_copy(update={'voice': voice})
        assert narration.narrate(selected) == pcm()
        assert narration.narrate(selected) == pcm()
    assert rendered == list(SPEECH_VOICES)
    audio_session.revision += 1
    with pytest.raises(lesson.StaleTurn): narration.narrate(request)


def test_duplicate_downloads_share_work_and_voice_switch_does_not_fail(audio_session, monkeypatch):
    from app.tutoring import narration
    entered, release, waiting = threading.Event(), threading.Event(), threading.Event()
    class SharedFuture(Future):
        def result(self, timeout=None):
            waiting.set()
            return super().result(timeout=timeout)
    monkeypatch.setattr(narration, 'Future', SharedFuture)
    calls = []
    def render(parts, voice, progress=None, **kwargs):
        calls.append(voice)
        if voice == narration.DEFAULT_VOICE:
            entered.set()
            assert release.wait(3)
        return pcm()
    monkeypatch.setattr(narration, 'render_audio', render)
    request = narration.NarrationRequest(owner='pupil-a', sessionId='narration-session-12345', revision=2, paragraphs=['Em gộp hai nhóm bút.'])
    with ThreadPoolExecutor(max_workers=3) as pool:
        first = pool.submit(narration.narrate, request)
        assert entered.wait(3)
        second = pool.submit(narration.narrate, request)
        assert waiting.wait(3)
        female = request.model_copy(update={'voice': 'vi-VN-HoaiMyNeural'})
        try:
            assert pool.submit(narration.narrate, female).result(timeout=3) == pcm()
        finally:
            release.set()
        assert first.result(timeout=3) == second.result(timeout=3) == pcm()
    assert calls == [narration.DEFAULT_VOICE, 'vi-VN-HoaiMyNeural']
    assert not narration._inflight


def test_capacity_is_bounded_and_full_capacity_is_retryable(audio_session, monkeypatch):
    from app.tutoring import narration
    slots = threading.BoundedSemaphore(2)
    monkeypatch.setattr(narration, '_render_slot', slots)
    request = narration.NarrationRequest(owner='pupil-a', sessionId='narration-session-12345', revision=2, paragraphs=['Em gộp hai nhóm bút.'])
    assert slots.acquire(blocking=False) and slots.acquire(blocking=False)
    with pytest.raises(narration.NarrationBusy): narration.narrate(request)
    assert not narration._inflight
    slots.release(); slots.release()


def test_reopening_earlier_narration_reuses_cache_and_memory_is_bounded(audio_session, monkeypatch):
    from app.tutoring import narration
    calls = []
    monkeypatch.setattr(narration, 'render_audio', lambda parts, voice, progress=None, **kwargs: calls.append(parts) or pcm())
    audio_session.narration_texts = [f'Em học bước {i}.' for i in range(12)]
    request = narration.NarrationRequest(owner='pupil-a', sessionId='narration-session-12345', revision=2, paragraphs=[audio_session.narration_texts[0]])
    for part in audio_session.narration_texts:
        narration.narrate(request.model_copy(update={'paragraphs': [part]}))
    narration.narrate(request)
    assert len(calls) == 12  # The old eight-entry cache re-rendered the first step.
    monkeypatch.setattr(narration, 'MAX_CACHE_BYTES', len(pcm()) * 2)
    audio_session.narration_texts.append('Bước mới.')
    narration.narrate(request.model_copy(update={'paragraphs': ['Bước mới.']}))
    assert sum(len(entry[1]) for entry in narration._cache.values()) <= narration.MAX_CACHE_BYTES


def test_pruning_progress_history_preserves_a_hot_wav_under_its_independent_lru(audio_session,monkeypatch):
    from app.tutoring import narration
    calls=[]
    monkeypatch.setattr(narration,'render_audio',lambda *args,**kwargs:calls.append(1) or pcm())
    audio_session.narration_texts=[f'Đoạn đã công bố {index}.' for index in range(65)]
    request=narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=[audio_session.narration_texts[0]])
    for part in audio_session.narration_texts[:64]:narration.narrate(request.model_copy(update={'paragraphs':[part]}))
    narration.narrate(request)  # Audio becomes MRU, while its progress metadata is still oldest.
    narration.narrate(request.model_copy(update={'paragraphs':[audio_session.narration_texts[64]]}))
    key=narration.request_key(request)
    assert key not in narration._progress and key in narration._cache
    assert len(narration._cache)==64 and sum(len(entry[1]) for entry in narration._cache.values())<=narration.MAX_CACHE_BYTES
    assert narration.narrate(request)==pcm() and len(calls)==65


def test_idempotent_prepare_restores_an_evicted_completed_wav(audio_session,monkeypatch):
    from app.tutoring import narration
    calls=[]
    monkeypatch.setattr(narration,'render_audio',lambda *args,**kwargs:calls.append(1) or pcm())
    request=narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'])
    narration.prepare_narration(request);key=narration.request_key(request)
    narration._public_jobs[key]['future'].result(timeout=2)
    with narration._cache_lock:narration._cache.pop(key)
    assert narration.narration_status(request)['phase']=='waiting'
    narration.prepare_narration(request)
    narration._public_jobs[key]['future'].result(timeout=2)
    assert narration.narration_status(request)['phase']=='ready' and len(calls)==2


@pytest.mark.parametrize('voice', ['en-US-EmmaMultilingualNeural', '', 'vi-VN-NamMinhNeural-evil'])
def test_unknown_voices_are_rejected_before_rendering(voice):
    from app.tutoring import narration
    with pytest.raises(ValueError):
        narration.NarrationRequest(owner='pupil-a', sessionId='narration-session-12345', revision=2,
                                   paragraphs=['Em gộp hai nhóm bút.'], voice=voice)


def test_real_lesson_publishes_only_opened_guidance_to_the_narration_allowlist(monkeypatch):
    from app.tutoring import narration
    plan=lesson.Plan(topic='Phân số',goal='Tìm phần còn lại',steps=[
        lesson.Step(title='Gộp hai phần',explanation='Em gộp phần táo và phần xoài.',question='Hai phần chiếm bao nhiêu?',expression='1/3+2/5',fractionNotation=True),
        lesson.Step(title='Phần còn lại',explanation='Cả hình là một đơn vị.',question='Còn bao nhiêu phần?',expression='1-{s0}',fractionNotation=True)])
    session=lesson.Session('real-pupil',plan,time.monotonic()+60,givens=frozenset({'1','3','2','5'}))
    key='real-narration-session-12345'; monkeypatch.setattr(lesson,'_sessions',{key:session})
    opened=lesson.present(key,session)
    assert opened.step.explanation in session.narration_texts
    monkeypatch.setattr(narration,'render_audio',lambda _, voice, progress=None, **kwargs:pcm())
    request=narration.NarrationRequest(owner='real-pupil',sessionId=key,revision=0,paragraphs=[opened.step.explanation])
    assert narration.narrate(request)[:4]==b'RIFF'
    with pytest.raises(ValueError): narration.narrate(request.model_copy(update={'paragraphs':['11/15']}))


def test_provider_outage_preserves_selected_voice_until_fallback_is_explicit(audio_session, monkeypatch, tmp_path):
    from app.tutoring import narration
    from app.tutoring.service import TutorUnavailable
    cloud, events = [], []
    def unavailable(*args, **kwargs):
        cloud.append(kwargs)
        assert 0 < args[2]-time.monotonic() <= narration.ONLINE_TIMEOUT_SECONDS
        raise TutorUnavailable()
    monkeypatch.setattr(narration, 'synthesize_neural', unavailable)
    monkeypatch.setattr(narration, 'synthesize', lambda text, path, deadline, **kwargs: path.write_bytes(pcm()))
    monkeypatch.setattr(narration.shutil, 'which', lambda _: 'ffmpeg')
    monkeypatch.setattr(narration, 'run', lambda args, deadline: __import__('pathlib').Path(args[-1]).write_bytes(pcm()))
    with pytest.raises(TutorUnavailable):
        narration.render_audio(['Em cộng hai số.'], narration.DEFAULT_VOICE)
    first = narration.render_audio(['Em cộng hai số.'], narration.DEFAULT_VOICE, lambda *args: events.append(args), fallback=True)
    narration.validate_audio(first)
    second = narration.render_audio(['Bài khác.'], 'vi-VN-HoaiMyNeural', fallback=True)
    assert first == second == pcm() and len(cloud) == 1
    assert events[0][0] == 'fallback' and events[0][-1] == 'offline'
    assert events[-1][0] == 'decoding' and events[-1][-1] == 'offline'


def test_progress_is_private_tracks_real_chunks_and_never_marks_failed_audio_ready(audio_session, monkeypatch):
    from app.tutoring import narration
    seen=[]
    request = narration.NarrationRequest(owner='pupil-a', sessionId='narration-session-12345', revision=2, paragraphs=['Em gộp hai nhóm bút.'])
    def render(parts, voice, update, **kwargs):
        update('synthesizing',45,1,2)
        seen.append(narration.narration_status(request))
        update('fallback',10,0,0,'offline')
        seen.append(narration.narration_status(request))
        return pcm()
    monkeypatch.setattr(narration, 'render_audio', render)
    narration.narrate(request)
    assert seen[0]['percent']==45 and seen[0]['completedChunks']==1
    assert seen[1]['percent']==45 and seen[1]['mode']=='offline'
    assert narration.narration_status(request)['phase']=='ready'
    assert narration.narration_status(request)['percent']==100
    with pytest.raises(lesson.LessonExpired): narration.narration_status(request.model_copy(update={'owner':'other'}))
    with pytest.raises(lesson.StaleTurn): narration.narration_status(request.model_copy(update={'revision':1}))
    narration._cache.clear()
    monkeypatch.setattr(narration, 'render_audio', lambda *args, **kwargs: b'not wav')
    with pytest.raises(Exception): narration.narrate(request)
    assert narration.narration_status(request)['phase']=='failed'
    assert narration.narration_status(request)['percent']<100


def test_fallback_is_opt_in_and_cannot_replace_the_selected_voice_in_cache(audio_session, monkeypatch):
    from app.tutoring import narration
    calls=[]
    def render(parts, voice, update, *, fallback=False, **kwargs):
        calls.append(fallback)
        update('decoding',90,0,0,'offline' if fallback else 'online')
        return pcm()
    monkeypatch.setattr(narration,'render_audio',render)
    request=narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'])
    manual=request.model_copy(update={'useFallback':True})
    narration.narrate(manual);narration.narrate(request);narration.narrate(request)
    assert calls==[True,False]
    assert narration.narration_status(manual)['mode']=='offline'
    assert narration.narration_status(request)['mode']=='online'


@pytest.mark.asyncio
async def test_audio_route_requires_internal_auth_and_never_returns_a_public_url(audio_session, monkeypatch):
    import httpx
    from fastapi import FastAPI
    from app.api import tutor
    from app.config import settings
    from app.tutoring import narration
    monkeypatch.setattr(settings, 'internal_api_key', 'narration-test-only')
    monkeypatch.setattr(narration, 'render_audio', lambda _, voice, progress=None, **kwargs: pcm())
    app = FastAPI(); app.include_router(tutor.router)
    payload = dict(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'])
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
        assert (await client.post('/lesson/narration',json=payload)).status_code == 401
        response = await client.post('/lesson/narration',json=payload,headers={'X-Internal-API-Key':'narration-test-only'})
        assert response.status_code == 200 and response.headers['content-type'] == 'audio/wav'
        assert response.headers['cache-control'] == 'no-store' and response.content[:4] == b'RIFF'
        assert (await client.post('/lesson/narration/status',json=payload)).status_code == 401
        assert (await client.post('/lesson/narration/prepare',json=payload)).status_code == 401
        prepared = await client.post('/lesson/narration/prepare',json=payload,headers={'X-Internal-API-Key':'narration-test-only'})
        assert prepared.status_code == 200 and prepared.json()['phase']=='ready'
        assert set(prepared.json())=={'phase','percent','elapsedMs','mode','completedChunks','totalChunks'}
        assert prepared.headers['cache-control']=='no-store'
        status = await client.post('/lesson/narration/status',json=payload,headers={'X-Internal-API-Key':'narration-test-only'})
        assert status.json()['percent']==100 and status.headers['cache-control']=='no-store'
        payload['owner'] = 'another-pupil'
        assert (await client.post('/lesson/narration/status',json=payload,headers={'X-Internal-API-Key':'narration-test-only'})).status_code == 410
        assert (await client.post('/lesson/narration',json=payload,headers={'X-Internal-API-Key':'narration-test-only'})).status_code == 410
        assert (await client.post('/lesson/narration/prepare',json=payload,headers={'X-Internal-API-Key':'narration-test-only'})).status_code == 410
        payload['owner'] = 'pupil-a'
        def busy(_): raise narration.NarrationBusy()
        monkeypatch.setattr(narration, 'narrate', busy)
        busy_response = await client.post('/lesson/narration',json=payload,headers={'X-Internal-API-Key':'narration-test-only'})
        assert busy_response.status_code == 429 and busy_response.headers['retry-after'] == '1'
