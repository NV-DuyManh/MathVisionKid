import asyncio
import gzip
from xml.etree import ElementTree

import httpx
from pydantic import SecretStr
import pytest

from app.config import Settings
from app.tutoring import azure_speech as speech

PCM = b"\x01\x00\xff\xff" * 1600


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setattr(speech.settings, "speech_provider", "azure")
    monkeypatch.setattr(speech.settings, "azure_speech_key", SecretStr("private-test-key"))
    monkeypatch.setattr(speech.settings, "azure_speech_region", "southeastasia")


def mock_provider(monkeypatch, handler):
    client = httpx.AsyncClient
    monkeypatch.setattr(speech.httpx, "AsyncClient",
                        lambda **kwargs: client(transport=httpx.MockTransport(handler), **kwargs))


@pytest.mark.parametrize("voice", speech.SPEECH_VOICES)
def test_exact_voice_auth_and_escaped_ssml(monkeypatch, configured, voice):
    requests = []
    def respond(request):
        requests.append(request)
        assert request.url == "https://southeastasia.tts.speech.microsoft.com/cognitiveservices/v1"
        assert request.headers["Ocp-Apim-Subscription-Key"] == "private-test-key"
        assert request.headers["X-Microsoft-OutputFormat"] == "raw-16khz-16bit-mono-pcm"
        assert request.headers["content-type"] == "application/ssml+xml"
        xml = ElementTree.fromstring(request.content)
        assert xml[0].attrib["name"] == voice
        assert xml[0].text == "Một < hai & ba > hai."
        return httpx.Response(200, content=PCM, headers={"content-type": "application/octet-stream"})
    mock_provider(monkeypatch, respond)
    result = asyncio.run(speech.azure_pcm("Một < hai & ba > hai.\x00\ud800", voice))
    assert result == PCM and len(requests) == 1


@pytest.mark.parametrize("field,value", [
    ("speech_provider", "edge"), ("azure_speech_key", SecretStr("")),
    ("azure_speech_key", SecretStr("private\r\nkey")),
    ("azure_speech_region", "southeastasia.evil.example/path"),
    ("azure_speech_region", "http://127.0.0.1"),
])
def test_unconfigured_or_invalid_host_never_reaches_network(monkeypatch, configured, field, value):
    monkeypatch.setattr(speech.settings, field, value)
    def no_network(_): raise AssertionError("Unexpected network request")
    mock_provider(monkeypatch, no_network)
    with pytest.raises(speech.AzureSpeechError, match="configuration"):
        asyncio.run(speech.azure_pcm("Chào em.", speech.SPEECH_VOICES[0]))


@pytest.mark.parametrize("text,voice", [
    ("", speech.SPEECH_VOICES[0]), ("\x00\x01", speech.SPEECH_VOICES[0]),
    ("x" * 65536, speech.SPEECH_VOICES[0]), ("Chào em.", "another-voice"),
    ("&" * 14000, speech.SPEECH_VOICES[0]),
], ids=["empty", "controls", "oversized", "wrong-voice", "escaped-oversized"])
def test_invalid_narration_never_reaches_network(monkeypatch, configured, text, voice):
    def no_network(_): raise AssertionError("Unexpected network request")
    mock_provider(monkeypatch, no_network)
    with pytest.raises(speech.AzureSpeechError, match="invalid_input"):
        asyncio.run(speech.azure_pcm(text, voice))


@pytest.mark.parametrize("status,category", [
    (401, "authentication"), (403, "authentication"), (429, "rate_limited"),
    (400, "provider"), (503, "provider"), (302, "provider"),
])
def test_failures_are_sanitized_and_not_automatically_retried(monkeypatch, configured, status, category):
    calls = []
    def respond(request):
        calls.append(request)
        return httpx.Response(status, content=b"private provider response and pupil text",
                              headers={"location": "https://evil.example"})
    mock_provider(monkeypatch, respond)
    with pytest.raises(speech.AzureSpeechError) as error:
        asyncio.run(speech.azure_pcm("private pupil text", speech.SPEECH_VOICES[0]))
    assert error.value.category == category and len(calls) == 1
    assert "private" not in str(error.value)


@pytest.mark.parametrize("payload,headers", [
    (b"", {"content-type": "audio/pcm"}),
    (b"\0" * 6400, {"content-type": "audio/pcm"}),
    (PCM + b"x", {"content-type": "audio/pcm"}),
    (PCM[:100], {"content-type": "audio/pcm"}),
    (PCM, {"content-type": "application/json"}),
    (PCM, {"content-type": "audio/mpeg"}),
    (gzip.compress(PCM), {"content-type": "audio/pcm", "content-encoding": "gzip"}),
    (PCM, {"content-type": "audio/pcm", "content-length": "7680001"}),
    (PCM, {"content-type": "audio/pcm", "content-length": "invalid"}),
    (PCM, {"content-type": "audio/pcm", "content-length": "9" * 5000}),
    (b"RIFF" + PCM, {"content-type": "audio/wav"}),
    (PCM, {"content-type": "audio/pcm", "content-length": "7000"}),
], ids=["empty", "silent", "unaligned", "short", "json", "mp3", "compressed",
         "oversized-header", "invalid-header", "giant-header", "wrong-container", "truncated"])
def test_invalid_or_wrong_format_audio_is_never_returned(monkeypatch, configured, payload, headers):
    mock_provider(monkeypatch, lambda _: httpx.Response(200, content=payload, headers=headers))
    with pytest.raises(speech.AzureSpeechError, match="invalid_audio"):
        asyncio.run(speech.azure_pcm("Chào em.", speech.SPEECH_VOICES[0]))


def test_stream_is_bounded_even_without_content_length(monkeypatch, configured):
    monkeypatch.setattr(speech, "MAX_PCM_BYTES", len(PCM))
    class Chunks(httpx.AsyncByteStream):
        async def __aiter__(self):
            yield PCM
            yield PCM
    mock_provider(monkeypatch, lambda _: httpx.Response(200, stream=Chunks(), headers={"content-type": "audio/pcm"}))
    with pytest.raises(speech.AzureSpeechError, match="invalid_audio"):
        asyncio.run(speech.azure_pcm("Chào em.", speech.SPEECH_VOICES[0]))


@pytest.mark.parametrize("failure,category", [
    (httpx.ReadTimeout, "timeout"), (httpx.ConnectError, "transport"),
])
def test_transport_failure_discards_partial_audio(monkeypatch, configured, failure, category):
    class Chunks(httpx.AsyncByteStream):
        async def __aiter__(self):
            yield PCM
            raise failure("private provider details")
    mock_provider(monkeypatch, lambda _: httpx.Response(200, stream=Chunks(), headers={"content-type": "audio/pcm"}))
    with pytest.raises(speech.AzureSpeechError) as error:
        asyncio.run(speech.azure_pcm("Chào em.", speech.SPEECH_VOICES[0]))
    assert error.value.category == category and "private" not in str(error.value)


def test_task_cancellation_closes_response_without_returning_partial_audio(monkeypatch, configured):
    closed = []
    class Chunks(httpx.AsyncByteStream):
        async def __aiter__(self):
            yield PCM
            await asyncio.sleep(10)
        async def aclose(self): closed.append(True)
    mock_provider(monkeypatch, lambda _: httpx.Response(200, stream=Chunks(), headers={"content-type": "audio/pcm"}))
    async def cancel():
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(speech.azure_pcm("Chào em.", speech.SPEECH_VOICES[0]), .02)
    asyncio.run(cancel())
    assert closed == [True]


def test_settings_default_to_edge_and_hide_azure_key(monkeypatch):
    monkeypatch.delenv("SPEECH_PROVIDER", raising=False)
    config = Settings(_env_file=None, azure_speech_key="private-test-key")
    assert config.speech_provider == "edge"
    assert "private-test-key" not in repr(config)
    assert "private-test-key" not in config.model_dump_json()


def test_valid_source_can_expand_past_4000_spoken_characters(monkeypatch, configured):
    from app.tutoring.speech_render import spoken_math
    source = "1/2 + 3/4 = 5/6. " * 200
    text = spoken_math(source)
    assert len(source) <= 4000 < len(text)
    def respond(request):
        assert len(request.content) <= speech.MAX_SSML_BYTES
        assert ElementTree.fromstring(request.content)[0].text == text
        return httpx.Response(200, content=PCM, headers={"content-type": "audio/pcm"})
    mock_provider(monkeypatch, respond)
    assert asyncio.run(speech.azure_pcm(text, speech.SPEECH_VOICES[0])) == PCM
