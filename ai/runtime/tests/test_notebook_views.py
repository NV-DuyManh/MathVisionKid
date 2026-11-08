"""Dense-page inputs keep every source pixel, with bounded provider requests."""
import base64
import io
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from PIL import Image

from app.tutoring import notebook, service
from app.integrations.groq import client
from app.integrations.groq.key_pool import GroqKeyPool, KeyState


def test_views_cover_both_ends_with_overlap_without_changing_original():
    image = Image.new('RGB', (1000, 2100), 'white')
    image.paste('red', (0, 0, 1000, 1176))
    image.paste('blue', (0, 1176, 1000, 2100))
    inputs = notebook._reading_images('full-image', image)
    assert isinstance(inputs, tuple) and len(inputs) == 2
    decoded = [Image.open(io.BytesIO(base64.b64decode(value))) for value in inputs]
    assert decoded[0].size == decoded[1].size == (1000, 1176)
    assert decoded[0].getpixel((500, 100))[0] > 240
    assert decoded[1].getpixel((500, 1170))[2] > 240
    assert decoded[1].getpixel((500, 100))[0] > 240  # Repeated overlap.
    assert image.size == (1000, 2100) and image.getpixel((500, 1175)) == (255, 0, 0)
    for size in [(1000, 600), (600, 2000), (2000, 1800)]:
        assert notebook._reading_images('full-image', Image.new('RGB', size)) == 'full-image'


@pytest.mark.asyncio
async def test_both_transports_send_each_view_separately_in_order(monkeypatch):
    pool = GroqKeyPool('mock-key')
    monkeypatch.setattr(service, 'get_pool', lambda: pool)
    transport = AsyncMock(return_value={'kind': 'MULTIPLE'})
    monkeypatch.setattr(service, '_execute_chat_completion', transport)
    await service._call_groq('policy', 'same source in two regions', ('upper', 'lower'))
    content = transport.await_args.args[0]['messages'][1]['content']
    assert [part['image_url']['url'] for part in content[1:]] == [
        'data:image/jpeg;base64,upper', 'data:image/jpeg;base64,lower']

    gemini_pool = MagicMock()
    gemini_pool.lease_key.return_value = SimpleNamespace(raw_key='mock-key', safe_id='mock-id')
    monkeypatch.setattr(service, 'get_gemini_pool', lambda: gemini_pool)
    original_client = httpx.AsyncClient
    requests = []
    def respond(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={'candidates': [{'finishReason': 'STOP', 'content': {'parts': [
            {'text': '{"kind":"MULTIPLE"}'}]}}]})
    monkeypatch.setattr(service.httpx, 'AsyncClient', lambda **kwargs:
        original_client(transport=httpx.MockTransport(respond), **kwargs))
    await service._call_gemini('policy', 'same source', ('upper', 'lower'))
    assert [part['inlineData']['data'] for part in requests[0]['contents'][0]['parts'][1:]] == ['upper', 'lower']


@pytest.mark.asyncio
@pytest.mark.parametrize('images', [(), ('x',) * 4, ('x', ''), ('x', 1), ['x']])
async def test_invalid_bundle_stops_before_spending_provider_quota(monkeypatch, images):
    cloud = AsyncMock()
    monkeypatch.setattr(service, '_call_groq', cloud)
    with pytest.raises(ValueError):
        await service._generate('policy', 'source', images)
    cloud.assert_not_called()


@pytest.mark.asyncio
async def test_dense_page_uses_two_regions_but_keeps_single_question_source(monkeypatch):
    buffer = io.BytesIO()
    Image.new('RGB', (1000, 2100), 'white').save(buffer, 'PNG')
    source = {'kind': 'PROBLEM', 'problemText': 'Tính 1+1=?', 'lines': []}
    cloud = AsyncMock(return_value=service.ProviderResult(source, 'groq'))
    monkeypatch.setattr(notebook, '_generate', cloud)
    result = await notebook.inspect_notebook(buffer.getvalue())
    assert result.kind == 'PROBLEM' and result.problemText == source['problemText']
    assert len(cloud.await_args_list[0].args[2]) == 2
    assert 'ONE photograph' in cloud.await_args_list[0].args[1]
    assert cloud.await_count == 1


@pytest.mark.asyncio
async def test_legible_two_view_worksheet_returns_without_a_slow_comparison_but_requires_confirmation(monkeypatch):
    monkeypatch.setattr(service.settings, 'gemini_enabled', True)
    monkeypatch.setattr(service.settings, 'gemini_api_keys', 'mock-key')
    buffer = io.BytesIO()
    Image.new('RGB', (1000, 2100), 'white').save(buffer, 'PNG')
    source = {'kind': 'MULTIPLE', 'questions': [
        {'label': 'Câu 1', 'problemText': 'Tính 1+1=?'},
        {'label': 'Câu 2', 'problemText': 'Tính 2+2=?'}]}
    cloud = AsyncMock(return_value=service.ProviderResult(source, 'groq'))
    monkeypatch.setattr(notebook, '_generate', cloud)
    result = await notebook.inspect_notebook(buffer.getvalue())
    assert cloud.await_count == 1 and len(result.questions) == 2
    assert all(question.uncertain for question in result.questions)


@pytest.mark.asyncio
async def test_http_413_is_payload_limit_not_transient_network_or_bad_key(monkeypatch):
    original_client = httpx.AsyncClient
    calls = []
    def respond(request):
        calls.append(request)
        return httpx.Response(413, json={'error': {'code': 'rate_limit_exceeded',
            'message': 'PRIVATE_UPSTREAM_DETAILS'}})
    monkeypatch.setattr(client.httpx, 'AsyncClient', lambda **kwargs:
        original_client(transport=httpx.MockTransport(respond), **kwargs))
    pool = GroqKeyPool('mock-one,mock-two')
    monkeypatch.setattr(service, 'get_pool', lambda: pool)
    with pytest.raises(service.TutorUnavailable):
        await service._call_groq('policy', 'source', 'photo')
    assert len(calls) == 1
    assert all(entry.state == KeyState.HEALTHY for entry in pool._entries)
    with pytest.raises(client.GroqError) as caught:
        await client._execute_chat_completion({'model': 'mock-model'}, pool._entries[0])
    assert caught.value.error_class == 'REQUEST_TOO_LARGE'
    assert 'PRIVATE_UPSTREAM_DETAILS' not in str(caught.value)


@pytest.mark.asyncio
async def test_independent_reader_cannot_fall_back_to_the_source_being_checked(monkeypatch):
    monkeypatch.setattr(service.settings, 'gemini_enabled', True)
    monkeypatch.setattr(service.settings, 'gemini_api_keys', 'mock-key')
    original = AsyncMock(return_value={'reading': 'same source'})
    independent = AsyncMock(side_effect=service.TutorUnavailable('configuration'))
    monkeypatch.setattr(service, '_call_groq', original)
    monkeypatch.setattr(service, '_call_gemini', independent)
    with pytest.raises(service.TutorUnavailable):
        await service._generate('policy', 'source', only_provider='gemini')
    assert independent.await_count == 1
    original.assert_not_called()


@pytest.mark.asyncio
async def test_legacy_line_reader_does_not_retry_an_oversize_payload(monkeypatch):
    import numpy as np
    from app.integrations.groq import line_analyzer
    monkeypatch.setattr(line_analyzer, 'get_pool', lambda: GroqKeyPool('mock-one,mock-two'))
    transport = AsyncMock(side_effect=client.GroqError('REQUEST_TOO_LARGE', 'limit'))
    monkeypatch.setattr(line_analyzer, 'call_groq_vision', transport)
    result = await line_analyzer.analyze_with_groq(np.full((200, 200, 3), 255, np.uint8), [],
        primary_model='primary', fallback_model='fallback', max_attempts=3)
    assert result is None and transport.await_count == 1


@pytest.mark.asyncio
async def test_fresh_catalog_absence_skips_retired_model_without_disabling_unknown_models(monkeypatch):
    import time
    import numpy as np
    from app.integrations.groq import line_analyzer, validator
    monkeypatch.setattr(line_analyzer, 'get_pool', lambda: GroqKeyPool('mock-key'))
    missing = {'primary': {'model': 'primary', 'catalogAvailable': False},
        'fallback': {'model': 'fallback', 'catalogAvailable': False}, 'checked_at': time.time()}
    monkeypatch.setattr(validator, '_validation_cache', missing)
    transport = AsyncMock(side_effect=client.GroqError('MODEL_UNAVAILABLE', 'missing'))
    monkeypatch.setattr(line_analyzer, 'call_groq_vision', transport)
    pixels = __import__('numpy').full((200, 201, 3), 255, np.uint8)
    assert await line_analyzer.analyze_with_groq(pixels, [], 'primary', 'fallback') is None
    transport.assert_not_called()
    missing['checked_at'] -= 301  # Stale evidence cannot disable a model indefinitely.
    assert await line_analyzer.analyze_with_groq(pixels, [], 'primary', 'fallback') is None
    assert transport.await_count == 2
