"""Offline checks of the real document transport boundary, including cold startup."""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import numpy as np
import pytest

from app.config import settings
from app.integrations.gemini import document_corrector, key_pool
from app.integrations.gemini.client import GeminiError


def test_cold_pool_is_initialized_once_from_enabled_settings(monkeypatch):
    monkeypatch.setattr(key_pool, "_gemini_pool", None)
    monkeypatch.setattr(settings, "gemini_enabled", True)
    monkeypatch.setattr(settings, "gemini_api_keys", "offline-test-key")
    pool = key_pool.get_gemini_pool()
    assert pool.total_keys == 1
    assert key_pool.get_gemini_pool() is pool


def test_disabled_settings_do_not_initialize_pool(monkeypatch):
    monkeypatch.setattr(key_pool, "_gemini_pool", None)
    monkeypatch.setattr(settings, "gemini_enabled", False)
    assert key_pool.get_gemini_pool() is None


@pytest.mark.asyncio
@pytest.mark.parametrize("status,error_class", [(400, "BAD_REQUEST"), (401, "AUTH_ERROR"),
    (403, "AUTH_ERROR"), (404, "MODEL_UNAVAILABLE"), (429, "RATE_LIMIT_429"), (503, "SERVER_ERROR_5XX")])
async def test_document_transport_uses_raw_key_and_classifies_failure(monkeypatch, status, error_class):
    post = AsyncMock(return_value=httpx.Response(status, json={"error": {}}, headers={"Retry-After": "12"}))
    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    entry = key_pool.GeminiKeyEntry("offline-credential", 0)
    with pytest.raises(GeminiError) as error:
        await document_corrector._execute_gemini_chat_completion("configured-model", [], entry)
    assert post.call_args.kwargs["headers"]["x-goog-api-key"] == "offline-credential"
    assert error.value.error_class == error_class
    assert error.value.status_code == status
    assert error.value.retry_after == 12


@pytest.mark.asyncio
async def test_document_wrapper_uses_configured_model(monkeypatch):
    monkeypatch.setattr(settings, "gemini_model", "configured-document-model")
    call = AsyncMock(return_value=None)
    monkeypatch.setattr(document_corrector, "request_document_gemini_correction", call)
    result = await document_corrector.request_gemini_document_correction(
        [{"rawOcrText": "xin chao"}], np.zeros((20, 50, 3), dtype=np.uint8))
    assert call.call_args.kwargs["model"] == "configured-document-model"
    assert result[0]["model"] == "configured-document-model"
