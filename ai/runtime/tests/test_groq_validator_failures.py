"""Service diagnostics stay complete and secret-free during outages."""
import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.integrations.groq import validator


@pytest.mark.asyncio
@pytest.mark.parametrize('failure', ['timeout', 'http', 'catalog'])
async def test_model_validation_never_loses_fields_or_exposes_exception_text(monkeypatch, caplog, failure):
    secret = 'PRIVATE_CREDENTIAL_IN_EXCEPTION'
    monkeypatch.setattr(validator.settings, 'groq_enabled', True)
    monkeypatch.setattr(validator.settings, 'groq_api_keys', secret)
    pool = MagicMock()
    pool.acquire.return_value = SimpleNamespace(raw_key=secret, safe_id='sha256:mock')
    monkeypatch.setattr(validator, 'get_pool', lambda: pool)
    client = AsyncMock()
    client.__aenter__.return_value = client
    if failure == 'timeout':
        client.get.side_effect = httpx.ReadTimeout(secret)
    elif failure == 'http':
        client.get.return_value = httpx.Response(429, json={'error': {'message': secret}})
    else:
        client.get.return_value = httpx.Response(200, json={'data': [{'id': 'primary'}, {'id': 'fallback'}]})
    monkeypatch.setattr(validator.httpx, 'AsyncClient', lambda **kwargs: client)
    with caplog.at_level(logging.INFO, logger=validator.__name__):
        result = await validator.validate_groq_models('primary', 'fallback')
    assert secret not in str(result) + caplog.text
    for role in ('primary', 'fallback'):
        model = result[role]
        assert model['model'] == role
        assert model['liveProbe'] is False
        assert model['vision_capable'] is None
        assert model['probeKind'] is None
        assert 'lastHttpStatus' in model and 'lastErrorClass' in model
        if failure == 'catalog':
            assert model['catalogAvailable'] is True and model['available'] is True
        else:
            assert model['catalogAvailable'] is None and model['available'] is False
            assert model['lastErrorClass'] == ('ReadTimeout' if failure == 'timeout' else 'HTTP_429')
    client.post.assert_not_called()


@pytest.mark.asyncio
async def test_absent_model_never_spends_inference_quota_or_fabricates_a_live_probe(monkeypatch, caplog):
    secret = 'PRIVATE_CREDENTIAL'
    monkeypatch.setattr(validator.settings, 'groq_enabled', True)
    monkeypatch.setattr(validator.settings, 'groq_api_keys', secret)
    pool = MagicMock()
    pool.acquire.return_value = SimpleNamespace(raw_key=secret, safe_id='sha256:mock')
    monkeypatch.setattr(validator, 'get_pool', lambda: pool)
    client = AsyncMock()
    client.__aenter__.return_value = client
    client.get.return_value = httpx.Response(200, json={'data': [{'id': 'primary'}]})
    monkeypatch.setattr(validator.httpx, 'AsyncClient', lambda **kwargs: client)
    with caplog.at_level(logging.INFO, logger=validator.__name__):
        result = await validator.validate_groq_models('primary', 'fallback')
    assert result['primary']['catalogAvailable'] is True
    assert result['primary']['vision_capable'] is None
    fallback = result['fallback']
    assert fallback['probeKind'] is None and fallback['vision_capable'] is None
    assert fallback['liveProbe'] is False and fallback['catalogAvailable'] is False
    assert fallback['lastHttpStatus'] == 200 and fallback['lastErrorClass'] == 'MODEL_NOT_IN_CATALOG'
    assert secret not in str(result) + caplog.text
    client.post.assert_not_called()
