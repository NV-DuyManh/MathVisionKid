"""Private preparation of the validated fixed lesson path. No additional model calls."""
from collections import OrderedDict
from dataclasses import dataclass, field, replace
import logging
import threading
import time
from typing import Literal

from pydantic import Field
from app.tutoring import lesson, narration
from app.tutoring.service import TutorModel
from app.tutoring.speech_render import SPEECH_VOICES, DEFAULT_VOICE

logger = logging.getLogger(__name__)
MAX_LESSONS = 4
MAX_CHARACTERS = 72000  # Shared lesson budget for pre-step speech, checked-step reviews and the summary.


class PrepareRequest(TutorModel):
    owner: str = Field(min_length=1, max_length=200)
    sessionId: str = Field(min_length=20, max_length=100)
    revision: int = Field(ge=0, strict=True)
    voice: Literal['vi-VN-NamMinhNeural', 'vi-VN-HoaiMyNeural'] = DEFAULT_VOICE


@dataclass
class Work:
    session: lesson.Session
    scripts: list[list[str]]
    voice: str
    extra_scripts: dict = field(default_factory=dict)
    attempted: set = field(default_factory=set)
    retry: set = field(default_factory=set)
    voice_failures: dict = field(default_factory=dict)
    ready: set = field(default_factory=set)
    projected_plan: object | None = None
    characters: int = 0
    failures: int = 0
    stopped: bool = False
    working: bool = False
    active_task: tuple | None = None


_jobs: OrderedDict[str, Work] = OrderedDict()
_lock = threading.RLock()
_worker: threading.Thread | None = None


def scripts_for(session):
    return project_scripts(session)[0]


def project_scripts(session):
    # A detached projection can check the private plan without publishing or advancing anything.
    preview = replace(session, answers=[], completed=[], narration_texts=[], revision=0, hint_count=0)
    scripts, reviews = [], {}
    count = len(preview.plan.steps)
    for index, step in enumerate(preview.plan.steps):
        public = lesson.present('private-projection', preview).step
        parts = script_for_step(public)
        narration.NarrationRequest(owner=session.owner, sessionId='private-projection-session', revision=0, paragraphs=parts)
        scripts.append(parts)
        answer = step.correctChoice if step.choices else str(lesson.calculate_exact(lesson.expression_at(step, preview.answers)))
        preview.completed.append(lesson.completed_step(step, preview, answer))
        # Reading-choice reviews use the same player as checked calculations.
        # Prepare them privately too; public reads still require the actual answer.
        reviews[count+index] = script_for_review(preview.completed[-1:])
        preview.answers.append(answer)
        preview.revision += 1
        # Public-step projection must use exactly the same pristine state as real step entry.
        preview.hint_count = 0
    reviews[2*count] = script_for_review([item for item in preview.completed if item.kind != 'UNDERSTAND'])
    # Long written working stays in the lesson; narration uses the checked result and its reason.
    for key, parts in list(reviews.items()):
        try: narration.NarrationRequest(owner=session.owner,sessionId='private-projection-session',revision=0,paragraphs=parts)
        except ValueError: reviews.pop(key)
    return scripts, reviews


def script_for_review(steps):
    parts = []
    for step in steps:
        calculation = f'{step.expression} = {step.answer}' + (f' ({step.unit})' if step.unit else '') if step.expression else step.answer
        parts.extend(' '.join(part.split()) for part in dict.fromkeys(part.strip() for part in
            [step.solutionSentence or step.title, calculation, *([step.explanation] if len(steps) == 1 else [])] if part.strip()))
    return parts


def script_ids(job):
    return [*range(len(job.scripts)), *job.extra_scripts]


def script_for_step(public):
    # Match the client helper's trim/dedup first, then the narration boundary's whitespace normalization.
    issued = dict.fromkeys(part.strip() for part in [*(public.guidance or [public.explanation]), public.question] if part.strip())
    parts = [' '.join(part.split()) for part in issued]
    return parts


def _valid(session_id, job):
    return not job.stopped and lesson._sessions.get(session_id) is job.session and job.session.expires > time.monotonic()


def schedule(request: PrepareRequest):
    session = _owned_session(request)
    narration.cancel_obsolete_prefetch(request.owner,request.sessionId,request.revision)
    with _lock:
        for key, old in list(_jobs.items()):
            if not _valid(key, old): _jobs.pop(key, None)
        job = _jobs.get(request.sessionId)
        previous_characters=0
        if job and job.projected_plan is not session.plan:
            previous_characters=job.characters
            job.stopped=True
            for voice in SPEECH_VOICES:narration.cancel_preparation(request.owner,request.sessionId,voice)
            _jobs.pop(request.sessionId,None);job=None
        if not job:
            # One active lesson per pupil; discard abandoned speculative queues.
            for key, old in list(_jobs.items()):
                if old.session.owner == request.owner:
                    old.stopped = True; narration.cancel_preparation(request.owner, key); _jobs.pop(key, None)
            while len(_jobs) >= MAX_LESSONS:
                old_key, old = _jobs.popitem(last=False); old.stopped = True; narration.cancel_preparation(old.session.owner, old_key)
            scripts, reviews = project_scripts(session)
            job = Work(session, scripts, request.voice, extra_scripts=reviews,
                projected_plan=session.plan,characters=previous_characters)
            _jobs[request.sessionId] = job
        elif job.voice != request.voice:
            # Yield unused speculation in the old voice; completed chunks remain reusable.
            narration.cancel_preparation(request.owner, request.sessionId, job.voice)
        elif job.active_task is not None:
            index,voice=job.active_task;current=len(session.answers);count=len(job.scripts)
            if index<count and index<current or count<=index<2*count and index-count<current-1:
                # Do not finish an unused old step while the pupil is already reading the next.
                narration.cancel_preparation(request.owner,request.sessionId,voice,request.revision)
        job.voice = request.voice
        # Repair only previously prepared nearby assets evicted by the bounded
        # WAV cache. Rebuilding the whole lesson would just churn the same cache.
        current=len(session.answers);count=len(job.scripts)
        nearby={current,current+1,count+current} if current<count else {2*count}
        if 0<current<count:nearby.add(count+current-1)
        if job.voice_failures.get(request.voice,0)<2:
            with narration._cache_lock:
                for index in nearby:
                    task=(index,request.voice)
                    if task not in job.ready:continue
                    parts=job.scripts[index] if index<count else job.extra_scripts[index]
                    entry=narration._cache.get((session.owner,request.sessionId,request.voice,False,tuple(parts)))
                    if entry is None or entry[0]<=time.monotonic():
                        job.ready.discard(task);job.attempted.discard(task)
        _launch()
        return _status(request.sessionId, job)


def _launch():
    global _worker
    if _worker is None or not _worker.is_alive():
        _worker = threading.Thread(target=_run, name='lesson-media-prepare', daemon=True)
        _worker.start()


def refresh_after_plan(session_id,session):
    with _lock:
        old=_jobs.get(session_id)
        # A late plan must not resurrect an abandoned lesson and displace the pupil's newer queue.
        if not old or old.session is not session or old.stopped:return None
        return schedule(PrepareRequest(owner=session.owner,sessionId=session_id,revision=session.revision,voice=old.voice))


def _owned_session(request):
    session = lesson._sessions.get(request.sessionId)
    if not session or session.owner != request.owner or session.expires <= time.monotonic():
        raise lesson.LessonExpired('Bài học đã hết phiên.')
    if request.revision != session.revision:
        raise lesson.StaleTurn('Bước học đã thay đổi.')
    return session


def _status(session_id, job):
    with narration._cache_lock:
        available = sum((entry := narration._cache.get((job.session.owner, session_id, job.voice, False, tuple(parts)))) is not None
            and entry[0] > time.monotonic() for parts in job.scripts)
    return {'totalSteps': len(job.scripts), 'preparedSteps': available,
            'preparedCharacters': job.characters, 'failedItems': job.failures}


def _next(session_id,job):
    current = len(job.session.answers)
    count = len(job.scripts)
    indexes = []
    if current==count: indexes.append(2*count)
    elif current and count+current-1 in job.extra_scripts: indexes.append(count+current-1)
    near = sorted(range(count),key=lambda index:(index<current,abs(index-current)))
    # Warm the next readable steps before spending provider turns on solved variants.
    indexes.extend(near)
    if current<count and count+current in job.extra_scripts:
        # The pupil can open this review immediately after answering. Warm it
        # before distant steps, retaining current/next and the current alternate.
        indexes.insert(min(2,len(indexes)),count+current)
    indexes.extend(count+index for index in near)
    indexes.append(2*count)
    indexes = list(dict.fromkeys(index for index in indexes if index in script_ids(job)))
    voices = [job.voice, *[voice for voice in SPEECH_VOICES if voice != job.voice]]
    # Protect the current/next selected speech first, then the alternative for
    # the current content. Switching voice need not wait for the entire lesson.
    primary=[(index,job.voice) for index in indexes]
    alternative=[(index,voices[1]) for index in indexes]
    order=primary[:2]+alternative[:1]+primary[2:]+alternative[1:]
    eligible=[task for task in order if task not in job.attempted]
    eligible.extend(task for task in order if task in job.retry and task in job.attempted)
    with narration._cache_lock:
        for task in eligible:
            index,voice=task
            parts=job.scripts[index] if index<count else job.extra_scripts[index]
            pending=narration._inflight.get((job.session.owner,session_id,voice,False,tuple(parts)))
            if pending is None or pending.done():return task
    # Stay scheduled when every candidate is already rendering; do not generate
    # a duplicate or abandon the queue before its shared results arrive.
    return eligible[0] if eligible else None


def _run():
    global _worker
    while True:
        with _lock:
            for key, old in list(_jobs.items()):
                if not _valid(key, old): _jobs.pop(key, None)
            selected = next(((key, job, task) for key, job in _jobs.items() if (task:=_next(key,job)) is not None), None)
            if not selected:
                _worker = None; return
            session_id, job, task = selected
            index, voice = task
            job.working = True
            job.active_task = task
            _jobs.move_to_end(session_id)
        parts = job.scripts[index] if index<len(job.scripts) else job.extra_scripts[index]
        try:
            if not _valid(session_id, job): continue
            if job.characters + sum(map(len, parts)) > MAX_CHARACTERS:
                with _lock:
                    job.attempted.add(task); job.retry.discard(task)
                continue
            request = narration.NarrationRequest(owner=job.session.owner, sessionId=session_id, revision=job.session.revision,
                paragraphs=parts, voice=voice)
            data = narration.prepare_private(request, job.session)
            with _lock:
                if not _valid(session_id, job): continue
                job.voice_failures[voice] = 0
                job.attempted.add(task); job.retry.discard(task); job.ready.add(task); job.characters += sum(map(len, parts))
        except (narration.NarrationBusy, lesson.StaleTurn):
            time.sleep(.2)
        except Exception as exc:
            logger.info('Lesson media preparation skipped category=%s', type(exc).__name__)
            with _lock:
                job.attempted.add(task); job.failures += 1
                job.voice_failures[voice] = job.voice_failures.get(voice, 0)+1
                if job.voice_failures[voice] >= 2:
                    # Stop after two consecutive failures in this voice. Public retries remain available.
                    job.attempted.update((i, voice) for i in script_ids(job))
                    job.retry.difference_update((i, voice) for i in script_ids(job))
                else:
                    # Retry this one missing asset only after untouched lesson steps and the other voice.
                    job.retry.add(task)
        finally:
            with _lock: job.working = False;job.active_task=None
