"""Private, bounded WAV narration of text already issued to the learner. No model calls."""
from collections import OrderedDict
from concurrent.futures import Future, ThreadPoolExecutor
import io
import logging
import shutil
from pathlib import Path
import tempfile
import threading
import time
import wave
from typing import Literal

from pydantic import Field, field_validator
from app.tutoring import lesson
from app.tutoring.service import TutorModel, TutorUnavailable
from app.tutoring.speech_render import DEFAULT_VOICE, SpeechNoAudio, synthesize_neural, synthesize, run

MAX_BYTES = 8 * 1024 * 1024
MAX_CACHE_BYTES = 32 * 1024 * 1024
MAX_CHECKPOINT_BYTES = 8 * 1024 * 1024
ONLINE_TIMEOUT_SECONDS = 25
RENDER_TIMEOUT_SECONDS = 32
PUBLIC_TIMEOUT_SECONDS = 39  # Stay below the business API's 40-second upstream read timeout.
PREPARATION_TIMEOUT_SECONDS = 45
logger = logging.getLogger(__name__)


class NarrationBusy(Exception):
    pass


class NarrationRequest(TutorModel):
    owner: str = Field(min_length=1, max_length=200)
    sessionId: str = Field(min_length=20, max_length=100)
    revision: int = Field(ge=0, strict=True)
    paragraphs: list[str] = Field(min_length=1, max_length=80)
    voice: Literal['vi-VN-NamMinhNeural', 'vi-VN-HoaiMyNeural'] = DEFAULT_VOICE
    useFallback: bool = Field(default=False, strict=True)
    prefetch: bool = Field(default=False, strict=True)

    @field_validator('paragraphs')
    @classmethod
    def bounded_text(cls, parts):
        if not 1 <= sum(len(part) for part in parts) <= 4000 or any(not part.strip() or len(part) > 1600 for part in parts):
            raise ValueError('Invalid narration length')
        return [' '.join(part.split()) for part in parts]


_cache: OrderedDict[tuple, tuple[float, bytes]] = OrderedDict()
_cache_lock = threading.Lock()
# Two independent voices can load together. Duplicate requests share the same render.
_render_slot = threading.BoundedSemaphore(2)
_inflight: dict[tuple, Future] = {}
_background: dict[tuple, threading.Event] = {}
_foreground_waiters: dict[tuple, int] = {}
_background_pause_until = 0.0
_progress: OrderedDict[tuple, dict] = OrderedDict()
_checkpoints: OrderedDict[tuple, tuple[float, dict[int, bytes]]] = OrderedDict()
_public_jobs: OrderedDict[tuple, dict] = OrderedDict()
_prepare_slots = threading.BoundedSemaphore(2)
_prepare_executor = ThreadPoolExecutor(max_workers=2,thread_name_prefix='narration-prepare')


def request_key(request):
    # Revision still gates every public read. Identical approved speech can reuse a private prebuilt asset.
    return (request.owner, request.sessionId, request.voice, request.useFallback, tuple(request.paragraphs))


def _store_audio(key, session, data):
    # Caller holds _cache_lock; use the same byte budget for rendered and joined audio.
    while _cache and (len(_cache) >= 64 or sum(len(entry[1]) for entry in _cache.values()) + len(data) > MAX_CACHE_BYTES):
        _cache.popitem(last=False)
    _cache[key] = (min(session.expires, time.monotonic()+900), data)


def _join_cached(key):
    """Join exact, ordered, private speech already rendered in this session/voice."""
    parts=key[-1];offset=0;assets=[]
    available=[(other[-1],data) for other,(expires,data) in _cache.items()
               if other[:4]==key[:4] and other!=key and expires>time.monotonic()]
    while offset<len(parts):
        match=max(((words,data) for words,data in available if parts[offset:offset+len(words)]==words),
                  key=lambda item:len(item[0]),default=None)
        if match is None:return None
        words,data=match;assets.append(data);offset+=len(words)
    if len(assets)<2:return None
    output=io.BytesIO()
    try:
        with wave.open(output,'wb') as joined:
            joined.setnchannels(1);joined.setsampwidth(2);joined.setframerate(16000)
            for data in assets:
                with wave.open(io.BytesIO(data),'rb') as source:
                    if source.getparams()[:3]!=(1,2,16000):return None
                    joined.writeframes(source.readframes(source.getnframes()))
        data=output.getvalue();validate_audio(data)
        return data
    except (ValueError,wave.Error,EOFError):return None


def chunk_checkpoint(request, session):
    """Retain completed provider turns briefly; never serve incomplete audio to a pupil."""
    key = request_key(request)
    def prune():
        for old, (expires, _) in list(_checkpoints.items()):
            if expires <= time.monotonic(): _checkpoints.pop(old)
    def read(index):
        with _cache_lock:
            prune()
            entry = _checkpoints.get(key)
            return entry[1].get(index) if entry else None
    def write(index, data):
        if not 128 <= len(data) <= 2*1024*1024: return
        with _cache_lock:
            prune()
            entry = _checkpoints.setdefault(key, (min(session.expires, time.monotonic()+300), {}))
            entry[1][index] = data
            _checkpoints.move_to_end(key)
            while len(_checkpoints)>8 or sum(len(part) for _, parts in _checkpoints.values() for part in parts.values())>MAX_CHECKPOINT_BYTES:
                _checkpoints.popitem(last=False)
    return read, write


def narration_status(request):
    owned(request)
    with _cache_lock:
        key = request_key(request)
        state = _progress.get(key)
        cached = _cache.get(key)
        job = _public_jobs.get(key)
        active = job is not None and not job.get('finished',False) and not job['future'].done()
        render=_inflight.get(key)
        rendering=render is not None and not render.done()
        if cached and cached[0]>time.monotonic():
            return dict(phase='ready',percent=100,elapsedMs=state['elapsedMs'] if state else 0,
                mode='offline' if request.useFallback else 'online',completedChunks=state['completedChunks'] if state else 0,totalChunks=state['totalChunks'] if state else 0)
        if job and job.get('prefetch') and job['revision']<request.revision:
            # The same issued words may recur at a new step. A cancelled old
            # warm-up is not a terminal failure of the new revision's request.
            return dict(phase='waiting',percent=0,elapsedMs=0,mode='offline' if request.useFallback else 'online',completedChunks=0,totalChunks=0)
        if not state or state['expires'] <= time.monotonic():
            failed=job is not None and job['future'].done() and job.get('failed',False)
            return dict(phase='failed' if failed else 'waiting', percent=0,
                elapsedMs=int((time.monotonic()-job['started'])*1000) if job else 0,
                mode='offline' if request.useFallback else 'online',completedChunks=0,totalChunks=0)
        result = {name: value for name, value in state.items() if name not in {'started', 'expires'}} | {
            'elapsedMs': int((time.monotonic()-state['started'])*1000) if state['phase'] not in {'ready','failed'} else state['elapsedMs']}
        if active:
            result['elapsedMs'] = int((time.monotonic()-job['started'])*1000)
            if result['phase'] in {'ready','failed'}:result['phase']='synthesizing'
        elif rendering:
            if result['phase'] in {'ready','failed'}:result['phase']='synthesizing'
        elif job is not None and job['future'].done() and job.get('failed',False):
            result['phase']='failed'
        elif result['phase']=='ready':result.update(phase='waiting',percent=0)
        return result


def prepare_narration(request):
    """Start a bounded owned job; HTTP callers poll instead of waiting for synthesis."""
    session = owned(request)
    key = request_key(request)
    with _cache_lock:
        now=time.monotonic()
        for old,job in list(_public_jobs.items()):
            if job['future'].done() and (job['expires']<=now or len(_public_jobs)>=16):_public_jobs.pop(old)
        cached=_cache.get(key);existing=_public_jobs.get(key)
        running=existing is not None and not existing.get('finished',False) and not existing['future'].done()
        if running and not request.prefetch:
            _promote(key,existing)
        elif not (cached and cached[0]>now) and not running:
            if not _prepare_slots.acquire(blocking=False):raise NarrationBusy()
            job=dict(started=now,expires=session.expires,prefetch=request.prefetch,revision=request.revision,
                     cancel=threading.Event(),hold=False,finished=False)
            try:
                if not request.prefetch:_promote(key,job)
                job['future']=_prepare_executor.submit(_prepare_long,request.model_copy(deep=True),session,now+PREPARATION_TIMEOUT_SECONDS,job)
                _public_jobs[key]=job
            except Exception:
                _release_hold(key,job)
                _prepare_slots.release();raise
    return narration_status(request)


def _promote(key,job):
    # Caller holds _cache_lock. A listener shares this job and its original deadline.
    if job['prefetch'] and job['cancel'].is_set():job['resume_cancelled']=True
    job['prefetch']=False;job['cancel'].clear()
    if not job['hold']:
        job['hold']=True;_foreground_waiters[key]=_foreground_waiters.get(key,0)+1
    if key in _background:_background[key].clear()


def _release_hold(key,job):
    if job['hold']:
        remaining=_foreground_waiters.get(key,0)-1
        if remaining>0:_foreground_waiters[key]=remaining
        else:_foreground_waiters.pop(key,None)
        job['hold']=False


def _prepare_long(request,session,deadline,job):
    def valid():
        # Permission/revision were checked before enqueue. Keep a private result even
        # if the pupil advances while it renders; every public read still calls owned().
        if lesson._sessions.get(request.sessionId) is not session or session.owner!=request.owner or session.expires<=time.monotonic():
            raise lesson.LessonExpired('Bài học đã hết phiên.')
        if job['prefetch'] and (job['cancel'].is_set() or session.revision!=request.revision):
            raise NarrationBusy()
        return session
    try:
        # The WAV lives in the bounded cache, never again in a retained executor result.
        _prepare_until_done(request,session,valid,deadline,job=job)
    except Exception as exc:
        logger.info('Background narration stopped category=%s',type(exc).__name__)
        with _cache_lock:
            job['failed']=True
    finally:
        with _cache_lock:
            job['finished']=True
            _release_hold(request_key(request),job)
        _prepare_slots.release()


def _prepare_until_done(request,session,check,deadline,background=False,job=None):
    attempts=0;last_count=-1
    while attempts<4 and time.monotonic()<deadline:
        check()
        try:
            speculative=job['prefetch'] if job is not None else background
            return _narrate(request,session,check,background=speculative,deadline=deadline,job=job)
        except NarrationBusy:
            if background and job is None:raise
            check()
            time.sleep(.2)
        except TutorUnavailable as error:
            with _cache_lock:
                saved=_checkpoints.get(request_key(request))
                count=len(saved[1]) if saved and saved[0]>time.monotonic() else 0
            if not request.useFallback and isinstance(error,SpeechNoAudio) and attempts==0 and deadline-time.monotonic()>1:
                # One fresh provider turn can repair a short empty response while
                # reading; share the original deadline and never switch voices.
                attempts+=1;last_count=count;time.sleep(.25);continue
            if request.useFallback or not count or count<=last_count:raise
            attempts+=1;last_count=count
    raise TutorUnavailable()


def owned(request):
    session = lesson._sessions.get(request.sessionId)
    if not session or session.owner != request.owner or session.expires < time.monotonic():
        raise lesson.LessonExpired('Bài học đã hết phiên. Em mở lại bài nhé.')
    if session.revision != request.revision:
        raise lesson.StaleTurn('Bước học đã thay đổi. Em mở lại lời giảng nhé.')
    if any(part not in session.narration_texts for part in request.paragraphs):
        raise ValueError('Unpublished narration')
    return session


def validate_audio(data):
    if not 44 < len(data) <= MAX_BYTES:
        raise ValueError('Invalid narration audio')
    with wave.open(io.BytesIO(data), 'rb') as sound:
        if sound.getnchannels() != 1 or sound.getsampwidth() != 2 or sound.getframerate() != 16000 or not .1 < sound.getnframes() / sound.getframerate() < 240:
            raise ValueError('Invalid narration audio')
        frames = sound.readframes(sound.getnframes())
        if len(frames) != sound.getnframes() * 2 or not any(frames):
            raise ValueError('Silent or incomplete narration audio')


def render_audio(paragraphs, voice, on_progress=None, *, fallback=False, cancel_event=None, checkpoint=None, deadline=None):
    deadline = min(time.monotonic()+RENDER_TIMEOUT_SECONDS, deadline) if deadline is not None else time.monotonic()+RENDER_TIMEOUT_SECONDS
    update = on_progress or (lambda *args: None)
    with tempfile.TemporaryDirectory(prefix='mathvision-narration-') as directory:
        output = Path(directory) / 'lesson.wav'
        text = ' '.join(paragraphs)
        if not fallback:
            options = {'cancel_event': cancel_event} if cancel_event is not None else {}
            if checkpoint is not None: options['checkpoint'] = checkpoint
            synthesize_neural(text, output, min(deadline, time.monotonic()+ONLINE_TIMEOUT_SECONDS), max_seconds=240, voice=voice, on_progress=update, **options)
        else:
            update('fallback', 10, 0, 0, 'offline')
            local = Path(directory) / 'local.wav'
            synthesize(text, local, deadline, max_seconds=240)
            update('decoding', 90, 0, 0, 'offline')
            ffmpeg = shutil.which('ffmpeg')
            if not ffmpeg:
                raise TutorUnavailable()
            run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(local),
                 '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', '-threads', '1', str(output)], deadline)
        if output.stat().st_size > MAX_BYTES:
            raise TutorUnavailable()
        return output.read_bytes()


def narrate(request: NarrationRequest) -> bytes:
    session = owned(request)
    deadline = time.monotonic()+PUBLIC_TIMEOUT_SECONDS
    for attempt in range(2):
        try:
            return _narrate(request, session, lambda: owned(request), deadline=deadline)
        except TutorUnavailable as error:
            with _cache_lock:
                saved = _checkpoints.get(request_key(request))
                resumable = isinstance(error,SpeechNoAudio) or saved is not None and saved[0]>time.monotonic() and bool(saved[1])
            if attempt or request.useFallback or not resumable or deadline-time.monotonic()<1:
                raise
            logger.info('Narration resuming completed provider chunks within original request deadline')


def prepare_private(request: NarrationRequest, session) -> bytes:
    """Internal worker only; future text is never added to the public narration allowlist."""
    def valid():
        if lesson._sessions.get(request.sessionId) is not session or session.expires <= time.monotonic() or session.owner != request.owner:
            raise lesson.LessonExpired('Bài học đã hết phiên.')
        return session
    return _prepare_until_done(request,valid(),valid,time.monotonic()+PREPARATION_TIMEOUT_SECONDS,background=True)


def _narrate(request: NarrationRequest, session, check, background=False, deadline=None,job=None) -> bytes:
    global _background_pause_until
    started = time.monotonic()
    check()
    key = request_key(request)
    with _cache_lock:
        now = time.monotonic()
        for old, (expires, _) in list(_cache.items()):
            if expires <= now:
                del _cache[old]
        if key in _cache:
            _cache.move_to_end(key)
            check()
            logger.info('Narration cache hit elapsed_ms=%d', (time.monotonic()-started)*1000)
            return _cache[key][1]
        if deadline is not None and time.monotonic()>=deadline: raise TutorUnavailable()
        pending = _inflight.get(key)
        if pending is None:
            joined = _join_cached(key)
            if joined is not None:
                check();_store_audio(key,session,joined)
                _progress[key]=dict(phase='ready',percent=100,mode='offline' if request.useFallback else 'online',
                    completedChunks=0,totalChunks=0,started=started,elapsedMs=int((time.monotonic()-started)*1000),expires=min(session.expires,time.monotonic()+900))
                logger.info('Narration assembled from cached speech elapsed_ms=%d',(time.monotonic()-started)*1000)
                return joined
        if pending is not None and pending.done() and pending.exception() is not None:
            # Its owner is still releasing the slot. Do not rejoin a completed failed turn.
            raise NarrationBusy()
        if pending is not None and not pending.done() and background and job is None:
            # The single lesson worker can warm another pupil/step while this
            # shared render runs. Foreground and public-job waiters still join it.
            raise NarrationBusy()
        rendering = pending is None
        if rendering:
            if background and time.monotonic() < _background_pause_until: raise NarrationBusy()
            if not _render_slot.acquire(blocking=False):
                if not background:
                    _background_pause_until = time.monotonic()+2
                    for old, cancellation in _background.items():
                        if not _foreground_waiters.get(old): cancellation.set()
                raise NarrationBusy()
            pending = _inflight[key] = Future()
            if background: _background[key] = job['cancel'] if job is not None else threading.Event()
            for old, state in list(_progress.items()):
                if old not in _inflight and (state['expires'] <= now or len(_progress) >= 64):
                    del _progress[old]
                    # Progress history is FIFO metadata. Audio has its own LRU,
                    # byte and expiry limits; pruning metadata must not evict hot WAVs.
            _progress[key] = dict(phase='synthesizing', percent=10, mode='offline' if request.useFallback else 'online', completedChunks=0,
                                  totalChunks=0, started=started, elapsedMs=0, expires=min(session.expires, now+900))
        elif not background:
            _foreground_waiters[key] = _foreground_waiters.get(key, 0)+1
    if not rendering:
        try:
            wait_seconds = min(RENDER_TIMEOUT_SECONDS+2, max(.001, deadline-time.monotonic())) if deadline is not None else RENDER_TIMEOUT_SECONDS+2
            if job is None:data = pending.result(timeout=wait_seconds)
            else:
                until=min(deadline,time.monotonic()+wait_seconds)
                while True:
                    check()
                    remaining=until-time.monotonic()
                    if remaining<=0:raise TutorUnavailable()
                    try:
                        data=pending.result(timeout=min(.1,remaining));break
                    except TimeoutError:
                        if pending.done():raise
            if check() is not session:
                raise lesson.LessonExpired('Em mở lại bài học nhé.')
            return data
        finally:
            if not background:
                with _cache_lock:
                    _foreground_waiters[key] -= 1
                    if not _foreground_waiters[key]: _foreground_waiters.pop(key)
    try:
        def update(phase, percent, completed=0, total=0, mode='online'):
            with _cache_lock:
                state = _progress[key]
                state.update(phase=phase, percent=max(state['percent'], percent), mode=mode, elapsedMs=int((time.monotonic()-started)*1000))
                if total or phase == 'fallback':
                    state.update(completedChunks=completed, totalChunks=total)
        options = {'deadline': deadline} if deadline is not None else {}
        if request.useFallback: options['fallback'] = True
        else: options['checkpoint'] = chunk_checkpoint(request, session)
        if background: options['cancel_event'] = _background[key]
        data = render_audio(request.paragraphs, request.voice, update, **options)
        try:
            validate_audio(data)
        except (ValueError, wave.Error, EOFError):
            with _cache_lock: _checkpoints.pop(key, None)
            raise TutorUnavailable() from None
        if check() is not session:
            raise lesson.LessonExpired('Em mở lại bài học nhé.')
        with _cache_lock:
            _checkpoints.pop(key, None)
            _store_audio(key,session,data)
            _progress[key].update(phase='ready', percent=100, elapsedMs=int((time.monotonic()-started)*1000))
            if job is not None:job.pop('resume_cancelled',None)
        pending.set_result(data)
        logger.info('Narration rendered elapsed_ms=%d bytes=%d voice=%s chars=%d parts=%d background=%s',
            (time.monotonic()-started)*1000,len(data),request.voice,sum(map(len,request.paragraphs)),len(request.paragraphs),background)
        return data
    except Exception as exc:
        with _cache_lock:
            if _progress[key]['phase']=='decoding' or isinstance(exc, (ValueError, wave.Error, EOFError)):
                _checkpoints.pop(key, None)
            _progress[key].update(phase='failed', elapsedMs=int((time.monotonic()-started)*1000))
            if background and (_background[key].is_set() or job is not None and job.pop('resume_cancelled',False)):
                exc = NarrationBusy()
        pending.set_exception(exc)
        logger.warning('Narration failed category=%s elapsed_ms=%d voice=%s chars=%d parts=%d background=%s',
            type(exc).__name__,(time.monotonic()-started)*1000,request.voice,sum(map(len,request.paragraphs)),len(request.paragraphs),background)
        raise exc
    finally:
        with _cache_lock:
            _inflight.pop(key, None)
            _background.pop(key, None)
            _render_slot.release()


def cancel_preparation(owner, session_id, voice=None,older_than_revision=None):
    with _cache_lock:
        for key,job in _public_jobs.items():
            if (key[:2]==(owner,session_id) and (voice is None or key[2]==voice) and job.get('prefetch')
                    and (older_than_revision is None or job['revision']<older_than_revision)):
                job['cancel'].set()
        for key, cancellation in _background.items():
            if key[:2] == (owner, session_id) and (voice is None or key[2]==voice and not _foreground_waiters.get(key)):
                job=_public_jobs.get(key)
                if older_than_revision is not None and job and job.get('prefetch') and job['revision']>=older_than_revision:continue
                cancellation.set()


def cancel_obsolete_prefetch(owner,session_id,revision):
    with _cache_lock:
        for key,job in _public_jobs.items():
            if key[:2]==(owner,session_id) and job.get('prefetch') and job['revision']<revision:
                job['cancel'].set()
