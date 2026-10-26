import asyncio
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI

from app.api import tutor
from app.config import settings
from app.tutoring import speech
from app.tutoring.service import TutorUnavailable


@pytest.mark.asyncio
async def test_nam_minh_speech_uses_requested_voice_and_returns_bounded_audio(monkeypatch):
    calls = []
    class Provider:
        def __init__(self, text, voice, **options): calls.append((text, voice, options))
        async def stream(self):
            yield {'type': 'SentenceBoundary', 'text': 'not audio'}
            yield {'type': 'audio', 'data': b'\xff\xf3' + bytes(126)}
    monkeypatch.setattr(speech.edge_tts, 'Communicate', Provider)
    result = await speech.synthesize(speech.SpeechRequest(text='Chào em.', rate=.9))
    assert len(result) == 128
    assert calls[0][:2] == ('Chào em.', 'vi-VN-NamMinhNeural')
    assert calls[0][2]['rate'] == '-10%'


@pytest.mark.asyncio
@pytest.mark.parametrize('failure', ['empty', 'oversized', 'provider'])
async def test_failures_do_not_return_partial_or_unbounded_audio(failure, monkeypatch, caplog):
    class Provider:
        def __init__(self, *args, **kwargs): pass
        async def stream(self):
            if failure == 'provider': raise RuntimeError('private-url-and-text')
            yield {'type': 'audio', 'data': bytes(speech.MAX_SPEECH_BYTES + 1) if failure == 'oversized' else b''}
    monkeypatch.setattr(speech.edge_tts, 'Communicate', Provider)
    with pytest.raises(TutorUnavailable): await speech.synthesize(speech.SpeechRequest(text='Chào em.'))
    assert 'private-url-and-text' not in caplog.text


@pytest.mark.asyncio
async def test_cancel_releases_speech_capacity(monkeypatch):
    entered = asyncio.Event()
    slots = asyncio.Semaphore(1)
    monkeypatch.setattr(speech, '_slots', slots)
    class Provider:
        def __init__(self, *args, **kwargs): pass
        async def stream(self):
            entered.set()
            await asyncio.Event().wait()
            yield {'type': 'audio', 'data': b''}
    monkeypatch.setattr(speech.edge_tts, 'Communicate', Provider)
    task = asyncio.create_task(speech.synthesize(speech.SpeechRequest(text='Chào em.')))
    await entered.wait(); task.cancel()
    with pytest.raises(asyncio.CancelledError): await task
    assert not slots.locked()


@pytest.mark.asyncio
async def test_speech_boundary_requires_auth_and_never_caches_private_narration(monkeypatch):
    app = FastAPI(); app.include_router(tutor.router, prefix='/internal/v1/tutor')
    synthesize = AsyncMock(return_value=b'\xff\xf3' + bytes(126))
    monkeypatch.setattr(speech, 'synthesize', synthesize)
    headers = {'X-Internal-API-Key': settings.internal_api_key}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
        assert (await client.post('/internal/v1/tutor/speech', json={'text': 'Chào em.'})).status_code == 401
        for payload in [{'text': ' '}, {'text': 'x' * 2001}, {'text': 'Chào em.', 'voice': 'en-US-test'}, {'text': 'Chào em.', 'rate': 2}]:
            assert (await client.post('/internal/v1/tutor/speech', json=payload, headers=headers)).status_code == 422
        response = await client.post('/internal/v1/tutor/speech', json={'text': 'Chào em.'}, headers=headers)
    assert response.status_code == 200
    assert response.headers['content-type'] == 'audio/mpeg'
    assert response.headers['cache-control'] == 'no-store'
    assert len(response.content) == 128
    assert synthesize.await_count == 1
