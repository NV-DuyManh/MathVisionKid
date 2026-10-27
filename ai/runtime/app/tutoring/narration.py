"""Private, bounded WAV narration of text already issued to the learner. No model calls."""
from collections import OrderedDict
import io
from pathlib import Path
import tempfile
import threading
import time
import wave
from typing import Literal

from pydantic import Field, field_validator
from app.tutoring import lesson
from app.tutoring.service import TutorModel, TutorUnavailable
from app.tutoring.video_render import DEFAULT_VOICE, synthesize_neural

MAX_BYTES = 8 * 1024 * 1024


class NarrationRequest(TutorModel):
    owner: str = Field(min_length=1, max_length=200)
    sessionId: str = Field(min_length=20, max_length=100)
    revision: int = Field(ge=0, strict=True)
    paragraphs: list[str] = Field(min_length=1, max_length=80)
    voice: Literal['vi-VN-NamMinhNeural', 'vi-VN-HoaiMyNeural'] = DEFAULT_VOICE

    @field_validator('paragraphs')
    @classmethod
    def bounded_text(cls, parts):
        if not 1 <= sum(len(part) for part in parts) <= 4000 or any(not part.strip() or len(part) > 1600 for part in parts):
            raise ValueError('Invalid narration length')
        return [' '.join(part.split()) for part in parts]


_cache: OrderedDict[tuple, tuple[float, bytes]] = OrderedDict()
_cache_lock = threading.Lock()
# One bounded speech request at a time; use the existing task queue if demand grows.
_render_slot = threading.Lock()


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


def render_audio(paragraphs, voice):
    deadline = time.monotonic() + 32
    with tempfile.TemporaryDirectory(prefix='mathvision-narration-') as directory:
        output = Path(directory) / 'lesson.wav'
        synthesize_neural(' '.join(paragraphs), output, deadline, max_seconds=240, voice=voice)
        if output.stat().st_size > MAX_BYTES:
            raise TutorUnavailable()
        return output.read_bytes()


def narrate(request: NarrationRequest) -> bytes:
    session = owned(request)
    key = (request.owner, request.sessionId, request.revision, request.voice, tuple(request.paragraphs))
    with _cache_lock:
        now = time.monotonic()
        for old, (expires, _) in list(_cache.items()):
            if expires <= now:
                del _cache[old]
        if key in _cache:
            return _cache[key][1]
    if not _render_slot.acquire(blocking=False):
        raise TutorUnavailable()
    try:
        data = render_audio(request.paragraphs, request.voice)
        try:
            validate_audio(data)
        except (ValueError, wave.Error, EOFError):
            raise TutorUnavailable() from None
        if owned(request) is not session:
            raise lesson.LessonExpired('Em mở lại bài học nhé.')
        with _cache_lock:
            if len(_cache) >= 8:
                _cache.popitem(last=False)
            _cache[key] = (min(session.expires, time.monotonic()+900), data)
        return data
    finally:
        _render_slot.release()
