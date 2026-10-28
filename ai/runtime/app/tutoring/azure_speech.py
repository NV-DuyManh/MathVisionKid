"""Explicitly configured official Speech route for the two selected Vietnamese voices."""
import re
from xml.sax.saxutils import escape

import httpx

from app.config import settings

SPEECH_VOICES = ("vi-VN-NamMinhNeural", "vi-VN-HoaiMyNeural")
SAMPLE_RATE = 16_000
MAX_PCM_BYTES = SAMPLE_RATE * 2 * 240
MAX_SSML_BYTES = 64 * 1024
_CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\ud800-\udfff\ufffe\uffff]")
_REGION = re.compile(r"[a-z][a-z0-9]{1,39}\Z")


class AzureSpeechError(RuntimeError):
    """Safe category only: never retain the request, key or student's narration."""

    def __init__(self, category: str):
        self.category = category
        super().__init__(f"Speech synthesis unavailable ({category})")


async def azure_pcm(text: str, voice: str) -> bytes:
    """Return complete signed little-endian 16-bit mono PCM at 16 kHz.

    The caller owns the single overall deadline and wraps these frames as WAV.
    Task cancellation propagates; failures never return a partial recording.
    """
    key = settings.azure_speech_key.get_secret_value().strip()
    region = settings.azure_speech_region.strip()
    if (settings.speech_provider != "azure" or not key or not key.isascii()
            or any(ord(char) < 33 or ord(char) > 126 for char in key)
            or not _REGION.fullmatch(region)):
        raise AzureSpeechError("configuration")
    if (voice not in SPEECH_VOICES or not isinstance(text, str)
            or not 1 <= len(text) <= MAX_SSML_BYTES):
        raise AzureSpeechError("invalid_input")
    text = _CONTROL_CHARACTERS.sub("", text).strip()
    if not text:
        raise AzureSpeechError("invalid_input")
    body = ("<speak version='1.0' xml:lang='vi-VN'><voice name='" + voice
            + "'>" + escape(text) + "</voice></speak>").encode("utf-8")
    if len(body) > MAX_SSML_BYTES:
        raise AzureSpeechError("invalid_input")
    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "raw-16khz-16bit-mono-pcm",
        "User-Agent": "MathVisionKid",
        "Accept-Encoding": "identity",
    }
    data = bytearray()
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(25, connect=5),
                                     follow_redirects=False, trust_env=False) as client:
            async with client.stream("POST", f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1",
                                     headers=headers, content=body) as response:
                if response.status_code in (401, 403):
                    raise AzureSpeechError("authentication")
                if response.status_code == 429:
                    raise AzureSpeechError("rate_limited")
                if response.status_code != 200:
                    raise AzureSpeechError("provider")
                content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                if (content_type not in {"audio/pcm", "audio/raw", "audio/x-raw", "audio/wav",
                                         "audio/x-wav", "application/octet-stream"}
                        or response.headers.get("content-encoding", "identity").lower() != "identity"):
                    raise AzureSpeechError("invalid_audio")
                length = response.headers.get("content-length")
                if length and (not re.fullmatch(r"[0-9]{1,8}", length) or int(length) > MAX_PCM_BYTES):
                    raise AzureSpeechError("invalid_audio")
                async for chunk in response.aiter_bytes():
                    if len(data) + len(chunk) > MAX_PCM_BYTES:
                        raise AzureSpeechError("invalid_audio")
                    data.extend(chunk)
                if length and len(data) != int(length):
                    raise AzureSpeechError("invalid_audio")
    except httpx.TimeoutException:
        raise AzureSpeechError("timeout") from None
    except httpx.HTTPError:
        raise AzureSpeechError("transport") from None
    if (len(data) < SAMPLE_RATE // 5 or len(data) % 2 or not any(data)
            or data[:4] in (b"RIFF", b"OggS") or data[:3] == b"ID3"):
        raise AzureSpeechError("invalid_audio")
    return bytes(data)
