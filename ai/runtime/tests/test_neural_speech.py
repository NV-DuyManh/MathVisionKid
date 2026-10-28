import asyncio
import time
from unittest.mock import AsyncMock

import pytest

from app.tutoring import speech_render as speech
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


@pytest.mark.parametrize('failure', [speech.edge_tts.exceptions.NoAudioReceived, TimeoutError])
def test_no_audio_retries_and_discards_incomplete_attempt(monkeypatch, failure):
    calls = []
    class Communicate:
        def __init__(self, *args, **kwargs): self.attempt = len(calls); calls.append(args)
        async def stream(self):
            if not self.attempt:
                yield {'type': 'audio', 'data': b'old' * 128}
                raise failure('No audio')
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


def test_turn_diagnostics_record_timing_and_failure_without_pupil_text(monkeypatch, caplog):
    calls = []
    class Communicate:
        def __init__(self, *args, **kwargs): self.attempt = len(calls); calls.append(args)
        async def stream(self):
            if self.attempt == 0:
                raise speech.edge_tts.exceptions.NoAudioReceived('secret provider URL and pupil text')
            yield {'type': 'audio', 'data': b'a' * 256}
    monkeypatch.setattr(speech.edge_tts, 'Communicate', Communicate)
    monkeypatch.setattr(speech.asyncio, 'sleep', AsyncMock())
    with caplog.at_level('INFO', logger=speech.__name__):
        assert asyncio.run(speech._neural_chunk('private pupil narration', speech.DEFAULT_VOICE)) == b'a' * 256
    assert 'attempt=1 first_audio_ms=-1' in caplog.text and 'outcome=NoAudioReceived' in caplog.text
    assert 'attempt=2 first_audio_ms=' in caplog.text and 'bytes=256 outcome=ready' in caplog.text
    assert 'pupil' not in caplog.text and 'provider URL' not in caplog.text


@pytest.mark.parametrize('voice', speech.SPEECH_VOICES)
def test_official_route_preserves_voice_math_and_wav_without_mp3_checkpoint(monkeypatch, tmp_path, voice):
    import wave
    monkeypatch.setattr(speech.settings, 'speech_provider', 'azure')
    pcm = b'\x01\x00' * 8000
    provider = AsyncMock(return_value=pcm)
    monkeypatch.setattr(speech, 'azure_pcm', provider)
    def forbidden(*args, **kwargs): raise AssertionError('Official PCM must not enter MP3 rendering')
    monkeypatch.setattr(speech, 'run', forbidden)
    monkeypatch.setattr(speech.shutil, 'which', forbidden)
    monkeypatch.setattr(speech, '_neural_audio', forbidden)
    path = tmp_path/'lesson.wav'
    assert speech.synthesize_neural('1/3 + 2/5', path, time.monotonic()+3, voice=voice,
                                    checkpoint=(forbidden, forbidden)) == .5
    provider.assert_awaited_once_with('1 phần 3 cộng 2 phần 5', voice)
    with wave.open(str(path), 'rb') as audio:
        assert audio.getparams()[:3] == (1, 2, 16000)
        assert audio.readframes(audio.getnframes()) == pcm
    assert not path.with_suffix('.mp3').exists()


def test_official_route_keeps_original_deadline_and_cancels_inflight_request(monkeypatch, tmp_path):
    monkeypatch.setattr(speech.settings, 'speech_provider', 'azure')
    cancelled = []
    async def slow(*args):
        try: await asyncio.sleep(10)
        finally: cancelled.append(True)
    monkeypatch.setattr(speech, 'azure_pcm', slow)
    with pytest.raises(TutorUnavailable):
        speech.synthesize_neural('Chào em!', tmp_path/'lesson.wav', time.monotonic()+.02)
    assert cancelled == [True] and not list(tmp_path.iterdir())


def test_failed_synthesis_is_private_and_removes_temporary_mp3(monkeypatch, tmp_path, caplog):
    monkeypatch.setattr(speech.shutil, 'which', lambda _: 'ffmpeg')
    monkeypatch.setattr(speech, '_neural_audio', AsyncMock(return_value=b'x' * 128))
    def fail(*args, **kwargs): raise RuntimeError('secret pupil text / private provider URL')
    monkeypatch.setattr(speech, 'run', fail)
    with pytest.raises(TutorUnavailable):
        speech.synthesize_neural('1/3 + 2/5', tmp_path/'lesson.wav', time.monotonic()+3)
    assert not (tmp_path/'lesson.mp3').exists()
    assert 'secret pupil' not in caplog.text and 'private provider URL' not in caplog.text


def test_empty_provider_failure_is_classified_without_exposing_text(monkeypatch,tmp_path,caplog):
    monkeypatch.setattr(speech.shutil,'which',lambda _:'ffmpeg')
    monkeypatch.setattr(speech,'_neural_audio',AsyncMock(side_effect=speech.edge_tts.exceptions.NoAudioReceived('private pupil text')))
    with pytest.raises(speech.SpeechNoAudio):speech.synthesize_neural('Chào em!',tmp_path/'lesson.wav',time.monotonic()+3)
    assert 'private pupil text' not in caplog.text and not list(tmp_path.iterdir())


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


def test_long_narration_preserves_words_order_and_voice_with_two_bounded_streams(monkeypatch):
    text = ' '.join(f'Từ{i}.' for i in range(100))
    calls, active, peak = [], 0, 0
    async def chunk(part, voice):
        nonlocal active, peak
        calls.append((part, voice))
        active += 1; peak = max(peak, active)
        await asyncio.sleep(.001 if len(calls) % 2 else 0)
        active -= 1
        return part.encode('utf-8') + b'\n'
    monkeypatch.setattr(speech, '_neural_chunk', chunk)
    result = asyncio.run(speech._neural_audio(text, speech.SPEECH_VOICES[1]))
    assert ' '.join(result.decode('utf-8').split()) == text
    assert all(len(part) <= 220 and voice == speech.SPEECH_VOICES[1] for part, voice in calls)
    assert peak == 2 and active == 0


def test_cancelled_long_narration_releases_all_streams(monkeypatch):
    active = []
    async def chunk(part, voice):
        active.append(part)
        try: await asyncio.sleep(1)
        finally: active.remove(part)
    monkeypatch.setattr(speech, '_neural_chunk', chunk)
    async def cancel():
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(speech._neural_audio('Em học từng bước. ' * 60, speech.DEFAULT_VOICE), .02)
        assert not active
    asyncio.run(cancel())


def test_failed_chunk_cancels_other_chunks_and_never_returns_partial_speech(monkeypatch):
    active = []
    async def chunk(part, voice):
        active.append(part)
        try:
            if len(active) == 2:
                raise ValueError('provider failed')
            await asyncio.sleep(1)
            return b'x' * 128
        finally: active.remove(part)
    monkeypatch.setattr(speech, '_neural_chunk', chunk)
    async def fail():
        with pytest.raises(ValueError):
            await speech._neural_audio('Em học từng bước. ' * 60, speech.DEFAULT_VOICE)
        assert not active
    asyncio.run(fail())


def test_speculative_speech_yields_promptly_without_running_encoder(monkeypatch, tmp_path):
    import threading
    cancelled=[]
    async def slow(*args):
        try: await asyncio.sleep(10)
        finally: cancelled.append(True)
    monkeypatch.setattr(speech.shutil,'which',lambda _: 'ffmpeg')
    monkeypatch.setattr(speech,'_neural_audio',slow)
    encode=AsyncMock();monkeypatch.setattr(speech,'run',encode)
    cancellation=threading.Event();timer=threading.Timer(.03,cancellation.set);timer.start()
    began=time.monotonic()
    try:
        with pytest.raises(TutorUnavailable):speech.synthesize_neural('Giữ nguyên giọng em chọn.',tmp_path/'lesson.wav',time.monotonic()+5,cancel_event=cancellation)
        assert time.monotonic()-began<1 and cancelled==[True]
        encode.assert_not_called()
    finally:timer.cancel()


def test_failed_long_speech_resumes_only_missing_chunks_and_keeps_original_order(monkeypatch):
    import textwrap
    text=' '.join(f'word{index}.' for index in range(80))
    parts=textwrap.wrap(text,width=220,break_long_words=False,break_on_hyphens=False)
    cached={};calls=[];failed=False
    async def render(part,voice):
        nonlocal failed
        calls.append((part,voice))
        if part==parts[1] and not failed:
            failed=True;await asyncio.sleep(.01);raise TimeoutError()
        return part.encode()+b'\0'*128
    monkeypatch.setattr(speech,'_neural_chunk',render)
    checkpoint=(cached.get,lambda index,data:cached.__setitem__(index,data))
    with pytest.raises(TimeoutError):asyncio.run(speech._neural_audio(text,speech.DEFAULT_VOICE,checkpoint=checkpoint))
    assert 0 in cached and 1 not in cached
    previously_ready=set(cached)
    before=len(calls);progress=[]
    result=asyncio.run(speech._neural_audio(text,speech.DEFAULT_VOICE,lambda *args:progress.append(args),checkpoint))
    assert result==b''.join(part.encode()+b'\0'*128 for part in parts)
    assert [part for part,_ in calls[before:]]==[part for index,part in enumerate(parts) if index not in previously_ready]
    assert progress[-1][2:]==(len(parts),len(parts))
