"""Bounded, private video jobs over published lesson data only."""
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import logging
import math
from pathlib import Path
import re
import secrets
import tempfile
import threading
import time
from typing import Literal

from pydantic import Field
from app.tutoring import lesson
from app.tutoring.service import TutorModel
from app.tutoring.video_render import Scene, render_movie, MAX_BYTES

logger=logging.getLogger(__name__)


class VideoRequest(TutorModel):
    owner: str = Field(min_length=1,max_length=200)
    sessionId: str = Field(min_length=20,max_length=100)
    revision: int = Field(ge=0,strict=True)


class VideoLookup(TutorModel):
    owner: str = Field(min_length=1,max_length=200)
    videoId: str = Field(pattern=r'^[A-Za-z0-9_-]{24,64}$')


class VideoStatus(TutorModel):
    videoId: str
    status: Literal['RENDERING','READY','FAILED']
    progress: int = 0
    durationSeconds: int = 0
    hasAudio: bool = False
    title: str


class VideoBusy(ValueError):
    pass


def owned(request):
    session=lesson._sessions.get(request.sessionId)
    if not session or session.owner!=request.owner or session.expires<time.monotonic():
        raise lesson.LessonExpired('Em mở lại bài học nhé.')
    if request.revision!=session.revision:
        raise lesson.StaleTurn('Bước học đã thay đổi. Em mở video của bước mới nhé.')
    return session


def brief(text):
    if len(text.strip())<=240:return text.strip()
    sentences=re.split(r'(?<=[.!?])\s+',text.strip())
    return sentences[0] if len(sentences[0])<=240 else ' '.join(sentences[0].split()[:32])+'…'


def storyboard(request: VideoRequest) -> list[Scene]:
    public=lesson.present(request.sessionId,owned(request))
    scenes=[Scene('Bài toán của em',public.goal,spoken=f'Mình cùng xem lại bài toán. {public.goal}.')]
    for index,step in enumerate(public.completed):
        text=brief(step.explanation)
        expression=step.expression
        answer=step.answer+(' '+step.unit if step.unit else '')
        if step.kind=='UNDERSTAND':
            text=f'{text} {step.answer}';expression='';answer=''
        spoken=f'Bước {index+1}. {step.title}. {text.rstrip(".!?") }.'
        if expression:spoken+=f' {expression} bằng {answer}.'
        scenes.append(Scene(f'{index+1}. {step.title}',text,expression,answer,spoken))
    if public.step:
        step=public.step; text=brief(step.explanation)
        scenes.append(Scene('Cùng hiểu: '+step.title,text,step.expression,spoken=f'{text} {step.question}'))
        scenes.append(Scene('Đến lượt em thử',step.question,spoken=f'{step.question} Em tạm dừng video để tự làm nhé.'))
    else:
        scenes.append(Scene('Nhìn lại cách làm',public.conclusion or public.goal,spoken=f'{public.conclusion or public.goal}. Em thử nói lại vì sao mình làm theo cách này nhé.'))
    for scene in scenes:
        for text in (scene.title,scene.text,scene.expression,scene.answer,scene.spoken):lesson.safe_public(text)
    return scenes


@dataclass
class Job:
    request: VideoRequest
    temp: tempfile.TemporaryDirectory
    expires: float
    status: VideoStatus
    path: Path | None = None
    expiry_timer: threading.Timer | None = None


_jobs: OrderedDict[str,Job]=OrderedDict()
_jobs_lock=threading.RLock()
# ponytail: one CPU encoder per process; use the existing task queue if video demand grows.
_render_lock=threading.Lock()
_executor=ThreadPoolExecutor(max_workers=1,thread_name_prefix='lesson-video')


def _drop(video_id):
    job=_jobs.pop(video_id,None)
    if job:
        if job.expiry_timer:job.expiry_timer.cancel()
        job.temp.cleanup()


def _schedule_expiry(video_id,job,delay):
    job.expiry_timer=threading.Timer(max(.01,delay),_expire,args=(video_id,))
    job.expiry_timer.daemon=True;job.expiry_timer.start()


def _expire(video_id):
    with _jobs_lock:
        job=_jobs.get(video_id)
        if not job:return
        if job.status.status=='RENDERING':_schedule_expiry(video_id,job,1)
        else:_drop(video_id)


def create_video(request: VideoRequest) -> VideoStatus:
    session=owned(request)
    with _jobs_lock:
        now=time.monotonic()
        for video_id,job in list(_jobs.items()):
            if job.status.status!='RENDERING' and job.expires<now:
                _drop(video_id)
        for video_id,job in list(_jobs.items()):
            if job.request==request:
                if job.status.status!='FAILED':return job.status.model_copy()
                _drop(video_id)
        scenes=storyboard(request)
        if not _render_lock.acquire(blocking=False):raise VideoBusy('Em chờ video đang dựng một chút nhé.')
        video_id=None
        try:
            if len(_jobs)>=8:
                _drop(next(iter(_jobs)))
            video_id=secrets.token_urlsafe(24)
            job=Job(request.model_copy(deep=True),tempfile.TemporaryDirectory(prefix='mathvision-video-'),min(session.expires,now+900),
                    VideoStatus(videoId=video_id,status='RENDERING',title=scenes[0].text))
            _jobs[video_id]=job
            _schedule_expiry(video_id,job,job.expires-now)
            _executor.submit(_render,job,scenes)
            return job.status.model_copy()
        except Exception:
            if video_id:_drop(video_id)
            _render_lock.release();raise


def _render(job,scenes):
    try:
        def progress(value):
            with _jobs_lock:job.status.progress=value
        path,duration=render_movie(scenes,Path(job.temp.name),progress)
        owned(job.request)
        with _jobs_lock:
            job.path=path;job.status=job.status.model_copy(update={'status':'READY','progress':100,'durationSeconds':math.ceil(duration),'hasAudio':True})
    except Exception as exc:
        logger.warning('Lesson video failed: %s',type(exc).__name__)
        with _jobs_lock:
            job.path=None;job.status=job.status.model_copy(update={'status':'FAILED','progress':0})
            job.temp.cleanup()
    finally:_render_lock.release()


def _lookup(request):
    job=_jobs.get(request.videoId)
    if not job or job.request.owner!=request.owner or job.expires<time.monotonic():
        raise lesson.LessonExpired('Video đã hết phiên. Em mở lại từ bài học nhé.')
    owned(job.request)
    return job


def video_status(request: VideoLookup) -> VideoStatus:
    with _jobs_lock:return _lookup(request).status.model_copy()


def video_content(request: VideoLookup) -> bytes:
    with _jobs_lock:
        job=_lookup(request)
        if job.status.status!='READY' or not job.path:raise VideoBusy('Video đang được chuẩn bị nhé.')
        if job.path.stat().st_size>MAX_BYTES:raise ValueError('Video too large')
        return job.path.read_bytes()
