import asyncio
import time
from unittest.mock import AsyncMock

import pytest

from app.tutoring import video_render as speech
from app.tutoring.service import TutorUnavailable


def test_provider_stream_is_bounded_and_uses_the_selected_voice(monkeypatch):
    calls = []
    class Communicate:
        def __init__(self, text, voice, **options): calls.append((text, voice, options))
        async def stream(self):
            yield {'type': 'SentenceBoundary', 'text': 'ignored'}
            yield {'type': 'audio', 'data': b'a' * 128}
            yield {'type': 'audio', 'data': b'b' * 128}
    monkeypatch.setattr(speech.edge_tts, 'Communicate', Communicate)
    assert asyncio.run(speech._neural_audio('Một phần ba.', speech.SPEECH_VOICES[1])) == b'a' * 128 + b'b' * 128
    assert calls[0][1] == 'vi-VN-HoaiMyNeural'
    assert calls[0][2]['connect_timeout'] == 5


@pytest.mark.parametrize('payload', [b'', b'x' * (2 * 1024 * 1024 + 1)], ids=['empty', 'oversize'])
def test_empty_and_oversized_streams_are_not_playable(monkeypatch, payload):
    class Communicate:
        def __init__(self, *args, **kwargs): pass
        async def stream(self): yield {'type': 'audio', 'data': payload}
    monkeypatch.setattr(speech.edge_tts, 'Communicate', Communicate)
    with pytest.raises(ValueError): asyncio.run(speech._neural_audio('Chào em!', speech.DEFAULT_VOICE))


def test_no_audio_retries_and_discards_incomplete_attempt(monkeypatch):
    calls = []
    class Communicate:
        def __init__(self, *args, **kwargs): self.attempt = len(calls); calls.append(args)
        async def stream(self):
            if not self.attempt:
                yield {'type': 'audio', 'data': b'old' * 128}
                raise speech.edge_tts.exceptions.NoAudioReceived('No audio')
            yield {'type': 'audio', 'data': b'new' * 128}
    monkeypatch.setattr(speech.edge_tts, 'Communicate', Communicate)
    monkeypatch.setattr(speech.asyncio, 'sleep', AsyncMock())
    assert asyncio.run(speech._neural_audio('Chào em!', speech.DEFAULT_VOICE)) == b'new' * 128
    assert len(calls) == 2


def test_persistent_no_audio_is_not_retried_forever(monkeypatch):
    calls = []
    class Communicate:
        def __init__(self, *args, **kwargs): calls.append(args)
        async def stream(self):
            raise speech.edge_tts.exceptions.NoAudioReceived('No audio')
            yield
    monkeypatch.setattr(speech.edge_tts, 'Communicate', Communicate)
    monkeypatch.setattr(speech.asyncio, 'sleep', AsyncMock())
    with pytest.raises(speech.edge_tts.exceptions.NoAudioReceived):
        asyncio.run(speech._neural_audio('Chào em!', speech.DEFAULT_VOICE))
    assert len(calls) == 3


def test_failed_synthesis_is_private_and_removes_temporary_mp3(monkeypatch, tmp_path, caplog):
    monkeypatch.setattr(speech.shutil, 'which', lambda _: 'ffmpeg')
    monkeypatch.setattr(speech, '_neural_audio', AsyncMock(return_value=b'x' * 128))
    def fail(*args, **kwargs): raise RuntimeError('secret pupil text / private provider URL')
    monkeypatch.setattr(speech, 'run', fail)
    with pytest.raises(TutorUnavailable):
        speech.synthesize_neural('1/3 + 2/5', tmp_path/'lesson.wav', time.monotonic()+3)
    assert not (tmp_path/'lesson.mp3').exists()
    assert 'secret pupil' not in caplog.text and 'private provider URL' not in caplog.text


def test_total_deadline_cancels_provider_and_never_starts_encoder(monkeypatch, tmp_path):
    monkeypatch.setattr(speech.shutil, 'which', lambda _: 'ffmpeg')
    cancelled = []
    async def slow(*args):
        try: await asyncio.sleep(1)
        finally: cancelled.append(True)
    monkeypatch.setattr(speech, '_neural_audio', slow)
    with pytest.raises(TutorUnavailable):
        speech.synthesize_neural('Chào em!', tmp_path/'lesson.wav', time.monotonic()+.02)
    assert cancelled == [True] and not list(tmp_path.iterdir())
