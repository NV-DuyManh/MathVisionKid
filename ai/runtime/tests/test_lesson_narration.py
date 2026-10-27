import io
import time
import wave
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
    return session


def test_private_narration_renders_once_and_replays_without_model_calls(audio_session, monkeypatch):
    from app.tutoring import narration
    rendered = []
    monkeypatch.setattr(narration, 'render_audio', lambda parts, voice: rendered.append((parts, voice)) or pcm())
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
    def render(_, voice):
        audio_session.revision += 1
        return pcm()
    monkeypatch.setattr(narration, 'render_audio', render)
    request = narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'])
    with pytest.raises(lesson.StaleTurn): narration.narrate(request)
    assert not narration._cache


def test_invalid_audio_is_not_cached_and_render_capacity_is_released(audio_session, monkeypatch):
    from app.tutoring import narration
    from app.tutoring.service import TutorUnavailable
    monkeypatch.setattr(narration, 'render_audio', lambda _, voice: b'not audio')
    request = narration.NarrationRequest(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'])
    with pytest.raises(TutorUnavailable): narration.narrate(request)
    assert not narration._cache
    assert narration._render_slot.acquire(blocking=False)
    narration._render_slot.release()


@pytest.mark.parametrize('data', [pcm(silent=True), pcm()[:-10]], ids=['silent', 'truncated'])
def test_silent_or_truncated_audio_is_rejected(data):
    from app.tutoring import narration
    with pytest.raises(ValueError): narration.validate_audio(data)


def test_the_two_voices_have_separate_private_cache_entries(audio_session, monkeypatch):
    from app.tutoring import narration
    from app.tutoring.video_render import SPEECH_VOICES
    rendered = []
    monkeypatch.setattr(narration, 'render_audio', lambda parts, voice: rendered.append(voice) or pcm())
    request = narration.NarrationRequest(owner='pupil-a', sessionId='narration-session-12345', revision=2,
                                         paragraphs=['Em gộp hai nhóm bút.'])
    for voice in SPEECH_VOICES:
        selected = request.model_copy(update={'voice': voice})
        assert narration.narrate(selected) == pcm()
        assert narration.narrate(selected) == pcm()
    assert rendered == list(SPEECH_VOICES)
    audio_session.revision += 1
    with pytest.raises(lesson.StaleTurn): narration.narrate(request)


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
    monkeypatch.setattr(narration,'render_audio',lambda _, voice:pcm())
    request=narration.NarrationRequest(owner='real-pupil',sessionId=key,revision=0,paragraphs=[opened.step.explanation])
    assert narration.narrate(request)[:4]==b'RIFF'
    with pytest.raises(ValueError): narration.narrate(request.model_copy(update={'paragraphs':['11/15']}))


@pytest.mark.asyncio
async def test_audio_route_requires_internal_auth_and_never_returns_a_public_url(audio_session, monkeypatch):
    import httpx
    from fastapi import FastAPI
    from app.api import tutor
    from app.config import settings
    from app.tutoring import narration
    monkeypatch.setattr(settings, 'internal_api_key', 'narration-test-only')
    monkeypatch.setattr(narration, 'render_audio', lambda _, voice: pcm())
    app = FastAPI(); app.include_router(tutor.router)
    payload = dict(owner='pupil-a',sessionId='narration-session-12345',revision=2,paragraphs=['Em gộp hai nhóm bút.'])
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
        assert (await client.post('/lesson/narration',json=payload)).status_code == 401
        response = await client.post('/lesson/narration',json=payload,headers={'X-Internal-API-Key':'narration-test-only'})
        assert response.status_code == 200 and response.headers['content-type'] == 'audio/wav'
        assert response.headers['cache-control'] == 'no-store' and response.content[:4] == b'RIFF'
        payload['owner'] = 'another-pupil'
        assert (await client.post('/lesson/narration',json=payload,headers={'X-Internal-API-Key':'narration-test-only'})).status_code == 410
