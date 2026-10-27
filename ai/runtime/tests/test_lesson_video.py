import json
import threading
import time
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI

from app.api import tutor
from app.config import settings
from app.tutoring import lesson


@pytest.fixture
def session():
    from app.tutoring import video
    with video._jobs_lock:
        for video_id in list(video._jobs):video._drop(video_id)
    lesson._sessions.clear()
    plan = lesson.Plan(topic='Phân số', goal='Tìm số cây trong cả vườn', steps=[
        lesson.Step(title='Gộp phần táo và xoài', explanation='Hai loại cây chiếm hai phần khác nhau.',
                    question='Hai loại cây chiếm bao nhiêu phần?', expression='1/3+2/5', fractionNotation=True),
        lesson.Step(title='Tìm phần còn lại', explanation='Cây cam chiếm phần còn lại.',
                    question='Phần cây cam là bao nhiêu?', expression='1-{s0}', fractionNotation=True)])
    value = lesson.Session('pupil-a', plan, time.monotonic()+600, givens=frozenset({'1','3','2','5','16'}),
                           problem_text='Vườn có 1/3 cây táo, 2/5 cây xoài và 16 cây cam.')
    lesson._sessions['video-lesson-session-12345'] = value
    return value


@pytest.mark.asyncio
async def test_video_endpoint_requires_internal_key_and_uses_existing_lesson_without_model(session, monkeypatch):
    from app.tutoring import video
    monkeypatch.setattr(settings, 'internal_api_key', 'video-test-only')
    monkeypatch.setattr(video, 'create_video', lambda request: video.VideoStatus(videoId='v'*32, status='RENDERING', progress=10, title='Bài của em'))
    app = FastAPI(); app.include_router(tutor.router)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
        payload={'owner':'pupil-a','sessionId':'video-lesson-session-12345','revision':0}
        assert (await client.post('/lesson/video', json=payload)).status_code == 401
        result=await client.post('/lesson/video', json=payload, headers={'X-Internal-API-Key':'video-test-only'})
        assert result.status_code == 200 and result.json()['status']=='RENDERING'


def test_storyboard_is_specific_and_contains_only_published_steps(session, monkeypatch):
    from app.tutoring import video
    generate=AsyncMock(); monkeypatch.setattr(lesson, '_generate', generate)
    request=video.VideoRequest(owner='pupil-a',sessionId='video-lesson-session-12345',revision=0)
    scenes=video.storyboard(request)
    text=json.dumps([scene.__dict__ for scene in scenes], ensure_ascii=False)
    assert '1/3+2/5' in text.replace(' ','') and 'Tìm số cây' in text
    assert '11/15' not in text and '1-{0}' not in text and 'correctChoice' not in text
    assert all(scene.spoken.strip() for scene in scenes)
    generate.assert_not_called()
    with pytest.raises(lesson.LessonExpired): video.storyboard(request.model_copy(update={'owner':'other'}))
    with pytest.raises(lesson.StaleTurn): video.storyboard(request.model_copy(update={'revision':1}))
    lesson.answer_lesson(lesson.TurnRequest(owner='pupil-a',sessionId=request.sessionId,revision=0,answer='11/15'))
    request.revision=1
    scenes=video.storyboard(request)
    text=json.dumps([scene.__dict__ for scene in scenes], ensure_ascii=False)
    assert '11/15' in text and '4/15' not in text and '{0}' not in text
    lesson.answer_lesson(lesson.TurnRequest(owner='pupil-a',sessionId=request.sessionId,revision=1,answer='4/15'))
    request.revision=2
    assert '4/15' in json.dumps([scene.__dict__ for scene in video.storyboard(request)])


def test_jobs_are_private_cached_and_do_not_accept_silent_output(session, monkeypatch):
    from app.tutoring import video
    gate=threading.Event()
    def render(scenes, directory, progress):
        gate.wait(2)
        path=directory/'lesson.mp4'; path.write_bytes(b'\x00\x00\x00\x18ftypisom'+b'x'*40)
        return path, 18.0
    monkeypatch.setattr(video, 'render_movie', render)
    request=video.VideoRequest(owner='pupil-a',sessionId='video-lesson-session-12345',revision=0)
    first=video.create_video(request)
    try:
        assert video.create_video(request).videoId==first.videoId
        with pytest.raises(lesson.LessonExpired): video.video_status(video.VideoLookup(owner='other',videoId=first.videoId))
        with pytest.raises(video.VideoBusy): video.video_content(video.VideoLookup(owner='pupil-a',videoId=first.videoId))
    finally: gate.set()
    lookup=video.VideoLookup(owner='pupil-a',videoId=first.videoId)
    for _ in range(200):
        status=video.video_status(lookup)
        if status.status!='RENDERING':break
        time.sleep(.01)
    assert status.status=='READY' and status.hasAudio and status.durationSeconds==18
    assert video.video_content(lookup)[4:8]==b'ftyp'
    session.revision+=1
    with pytest.raises(lesson.StaleTurn): video.video_content(lookup)


def test_spoken_math_preserves_fraction_and_operation_meaning():
    from app.tutoring.video_render import spoken_math
    assert spoken_math('1/3 + 2/5 = 11/15')=='1 phần 3 cộng 2 phần 5 bằng 11 phần 15'
    assert 'chia' in spoken_math('16 : (4/15)')
    assert spoken_math('(12 + 6) / 3 = 6')=='mở ngoặc 12 cộng 6 đóng ngoặc chia 3 bằng 6'
    assert 'mở ngoặc 1 phần 3 cộng 2 phần 5 đóng ngoặc' in spoken_math('1 - (1/3+2/5)')
    assert spoken_math('-5 + 8')=='âm 5 cộng 8'
    assert 'xăng ti mét vuông' in spoken_math('Diện tích là 32 cm².')


@pytest.mark.parametrize('source, expected', [
    ('5 × -2 = -10', '5 nhân âm 2 bằng âm 10'),
    ('5 * -2 = -10', '5 nhân âm 2 bằng âm 10'),
    ('12 ÷ -3 = -4', '12 chia âm 3 bằng âm 4'),
    ('5 + -2 = 3', '5 cộng âm 2 bằng 3'),
    ('3 kg và 15 cm', '3 ki lô gam và 15 xăng ti mét'),
    ('5dm² và 3 mm³', '5 đề xi mét vuông và 3 mi li mét khối'),
    ('8 (cm²)', '8 xăng ti mét vuông'),
    ('250 ml và 2 l', '250 mi li lít và 2 lít'),
    ('(12 + 8) × 2 = 40', 'mở ngoặc 12 cộng 8 đóng ngoặc nhân 2 bằng 40'),
    ('Điểm (M) nằm trong hình', 'Điểm mở ngoặc M đóng ngoặc nằm trong hình'),
    ('gam, làm, lớp và 3kg', 'gam, làm, lớp và 3 ki lô gam'),
])
def test_nam_pronunciation_selection_preserves_operands_and_word_boundaries(source, expected):
    from app.tutoring.video_render import spoken_math
    assert spoken_math(source) == expected


def test_system_font_fallback_does_not_assume_deep_repository_path(monkeypatch):
    from pathlib import Path
    from app.tutoring import video_render
    monkeypatch.setattr(video_render,'__file__','/app/app/tutoring/video_render.py')
    monkeypatch.setattr(Path,'is_file',lambda path:path.name=='DejaVuSans.ttf')
    monkeypatch.setattr(video_render.ImageFont,'truetype',lambda path,size: (path,size))
    assert 'DejaVuSans.ttf' in video_render.font(23)[0]


def test_expiry_removes_private_artifacts_without_another_request(session, monkeypatch):
    from app.tutoring import video
    from pathlib import Path
    def render(scenes,directory,progress):
        file=directory/'lesson.mp4';file.write_bytes(b'video');return file,3
    monkeypatch.setattr(video,'render_movie',render)
    session.expires=time.monotonic()+.25
    first=video.create_video(video.VideoRequest(owner='pupil-a',sessionId='video-lesson-session-12345',revision=0))
    path=Path(video._jobs[first.videoId].temp.name)
    for _ in range(100):
        if not path.exists():break
        time.sleep(.01)
    assert not path.exists()


def test_failed_worker_submission_cleans_job_and_encoder_lock(session,monkeypatch):
    from app.tutoring import video
    def unavailable(*args):raise RuntimeError('Worker stopping')
    monkeypatch.setattr(video._executor,'submit',unavailable)
    with pytest.raises(RuntimeError):
        video.create_video(video.VideoRequest(owner='pupil-a',sessionId='video-lesson-session-12345',revision=0))
    assert not video._jobs
    assert not video._render_lock.locked()
