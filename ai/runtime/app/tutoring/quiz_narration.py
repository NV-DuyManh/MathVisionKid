"""Speech for a Quiz solution authorized by Spring, using the existing speech engine.

This internal endpoint never accepts images, creates Tutor sessions, or calls an LLM.
Spring owns persistent Quiz authorization; its internal credential is required at the route.
"""
from collections import OrderedDict
import hashlib
import threading
import time
from typing import Literal
from uuid import UUID

from pydantic import Field
from app.tutoring.service import TutorModel, TutorUnavailable
from app.tutoring import narration


class QuizNarrationRequest(TutorModel):
    owner: str = Field(min_length=1, max_length=200)
    quizId: UUID
    text: str = Field(min_length=1, max_length=4000)
    voice: Literal['vi-VN-NamMinhNeural', 'vi-VN-HoaiMyNeural']


class SpeechBusy(Exception):
    pass


_cache: OrderedDict[tuple, tuple[float, bytes]] = OrderedDict()
# A single bounded render prevents unbounded TTS work. Identical concurrent requests
# wait for the first render and reuse it; unrelated work receives 429 immediately.
_lock = threading.Lock()
_active: dict[tuple, threading.Event] = {}


def narrate(request: QuizNarrationRequest) -> bytes:
    key = (request.owner, str(request.quizId), request.voice,
           hashlib.sha256(request.text.encode()).hexdigest())
    with _lock:
        now = time.monotonic()
        for old, (expiry, _) in list(_cache.items()):
            if expiry <= now:
                del _cache[old]
        if key in _cache:
            return _cache[key][1]
        if key in _active:
            event = _active[key]
            creator = False
        else:
            if _active:
                raise SpeechBusy()
            event = _active[key] = threading.Event()
            creator = True
    if not creator:
        if not event.wait(timeout=35):
            raise TutorUnavailable()
        with _lock:
            if key in _cache:
                return _cache[key][1]
        raise TutorUnavailable()
    try:
        # render_audio reuses synthesize_neural, spoken_math, deadlines and WAV encoding.
        data = narration.render_audio([request.text], request.voice)
        narration.validate_audio(data)
        with _lock:
            # Bound both entry count and total memory, including long explanations.
            while _cache and (len(_cache) >= 8 or sum(len(entry[1]) for entry in _cache.values()) + len(data) > 24 * 1024 * 1024):
                _cache.popitem(last=False)
            _cache[key] = (time.monotonic() + 900, data)
        return data
    finally:
        with _lock:
            _active.pop(key, None)
            event.set()
