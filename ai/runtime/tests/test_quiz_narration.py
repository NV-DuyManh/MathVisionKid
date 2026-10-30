"""Quiz speech boundary, cache, single flight and exact published text; no cloud calls."""
import io
import threading
import time
import wave
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import httpx
import pytest
from pydantic import ValidationError
from app.tutoring import quiz_narration as speech
from app.tutoring.service import TutorUnavailable
from app.tutoring.speech_render import spoken_math


def pcm():
    output = io.BytesIO()
    with wave.open(output, 'wb') as sound:
        sound.setnchannels(1); sound.setsampwidth(2); sound.setframerate(16000)
        sound.writeframes(b'\x01\x00' * 16000)
    return output.getvalue()


@pytest.fixture(autouse=True)
def clear_cache():
    speech._cache.clear()
    assert not speech._active
    yield
    speech._cache.clear()
    assert not speech._active


def request(**overrides):
    return speech.QuizNarrationRequest(**dict(owner='student-a', quizId=uuid4(),
        text='Phần còn lại là: 1 − 5/8 = 3/8. Tổng số sách là: 18 ÷ (3/8) = 48 quyển sách.',
        voice='vi-VN-NamMinhNeural') | overrides)


def test_speech_reads_exact_authorized_solution_and_replay_never_regenerates_explanation(monkeypatch):
    calls = []
    monkeypatch.setattr(speech.narration, 'render_audio', lambda paragraphs, voice: calls.append((paragraphs, voice)) or pcm())
    source = request()
    assert speech.narrate(source) == speech.narrate(source)
    assert calls == [([source.text], source.voice)]
    speech.narrate(source.model_copy(update={'owner': 'student-b'}))
    speech.narrate(source.model_copy(update={'voice': 'vi-VN-HoaiMyNeural'}))
    assert len(calls) == 3
    spoken = spoken_math(source.text)
    assert '5 phần 8' in spoken and '3 phần 8' in spoken and '48 quyển sách' in spoken and ' chia ' in spoken


def test_simultaneous_identical_requests_render_once_and_busy_work_is_bounded(monkeypatch):
    entered, release = threading.Event(), threading.Event()
    calls = []
    def render(parts, voice):
        calls.append(parts); entered.set(); assert release.wait(5)
        return pcm()
    monkeypatch.setattr(speech.narration, 'render_audio', render)
    source = request()
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(speech.narrate, source)
        assert entered.wait(2)
        second = pool.submit(speech.narrate, source)
        with pytest.raises(speech.SpeechBusy): speech.narrate(request())
        release.set()
        assert first.result(timeout=5) == second.result(timeout=5)
    assert len(calls) == 1


def test_failed_tts_has_no_cache_entry_and_can_retry_without_changing_solution(monkeypatch):
    source = request()
    monkeypatch.setattr(speech.narration, 'render_audio', lambda *_: (_ for _ in ()).throw(TutorUnavailable()))
    with pytest.raises(TutorUnavailable): speech.narrate(source)
    assert not speech._cache and not speech._active
    monkeypatch.setattr(speech.narration, 'render_audio', lambda *_: pcm())
    assert speech.narrate(source).startswith(b'RIFF')


def test_silent_or_invalid_audio_is_not_published(monkeypatch):
    monkeypatch.setattr(speech.narration, 'render_audio', lambda *_: b'RIFF')
    with pytest.raises(ValueError): speech.narrate(request())
    assert not speech._cache


def test_no_arbitrary_voice_images_or_fake_lesson_sessions():
    with pytest.raises(ValidationError): request(voice='en-US-untrusted')
    with pytest.raises(ValidationError): request(sessionId='fake-session', image='private-image')


@pytest.mark.asyncio
async def test_internal_auth_required_and_runtime_does_not_replace_spring_ownership(monkeypatch):
    from app.main import app
    from app.config import settings
    monkeypatch.setattr(speech.narration, 'render_audio', lambda *_: pcm())
    source = request()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
        result = await client.post('/internal/v1/tutor/quiz/narration', json=source.model_dump(mode='json'))
        assert result.status_code == 401
        result = await client.post('/internal/v1/tutor/quiz/narration', json=source.model_dump(mode='json'), headers={'X-Internal-API-Key': settings.internal_api_key})
        assert result.status_code == 200 and result.headers['cache-control'] == 'no-store'
        assert result.content[:4] == b'RIFF'
