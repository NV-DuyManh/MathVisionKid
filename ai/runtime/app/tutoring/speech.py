"""Bounded Vietnamese narration through Microsoft's online Edge voices."""
import asyncio
import logging
from typing import Literal

import edge_tts
from pydantic import Field

from app.tutoring.service import TutorModel, TutorUnavailable

logger = logging.getLogger(__name__)
MAX_SPEECH_BYTES = 2 * 1024 * 1024
_slots = asyncio.Semaphore(2)


class SpeechRequest(TutorModel):
    text: str = Field(min_length=1, max_length=2000)
    voice: Literal['vi-VN-NamMinhNeural', 'vi-VN-HoaiMyNeural'] = 'vi-VN-NamMinhNeural'
    rate: float = Field(default=0.9, ge=0.75, le=1.05)


async def synthesize(request: SpeechRequest) -> bytes:
    async def collect():
        result = bytearray()
        speech = edge_tts.Communicate(request.text, request.voice,
            rate=f'{round((request.rate - 1) * 100):+d}%', connect_timeout=5, receive_timeout=15)
        async for chunk in speech.stream():
            if chunk['type'] == 'audio':
                result.extend(chunk['data'])
                if len(result) > MAX_SPEECH_BYTES:
                    raise ValueError('Speech exceeds audio limit')
        if len(result) < 128:
            raise ValueError('Empty speech response')
        return bytes(result)

    acquired = False
    try:
        await asyncio.wait_for(_slots.acquire(), timeout=0.25)
        acquired = True
        return await asyncio.wait_for(collect(), timeout=25)
    except Exception as exc:
        # Provider errors can include request URLs. Log only the exception class.
        logger.warning('Vietnamese narration unavailable category=%s', type(exc).__name__)
        raise TutorUnavailable() from None
    finally:
        if acquired:
            _slots.release()
