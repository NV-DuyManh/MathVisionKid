"""Production must never start with fixture recognition or development secrets."""
import pytest
from pydantic import ValidationError

from app.config import Settings


@pytest.fixture
def production_settings():
    return {
        "app_env": "production",
        "runtime_mode": "MODEL",
        "ocr_provider": "crnn_vi_handwriting_v1",
        "canonical_runtime_override_enabled": False,
        "internal_api_key": "unit-test-internal-secret-123456789",
        "minio_access_key": "unit-test-storage-access",
        "minio_secret_key": "unit-test-storage-secret",
        "groq_enabled": True,
        "groq_api_keys": "unit-test-groq",
        "gemini_enabled": True,
        "gemini_api_keys": "unit-test-gemini",
    }


def test_production_accepts_real_runtime(production_settings):
    configured = Settings(_env_file=None, **production_settings)
    assert configured.runtime_mode == "MODEL"
    assert configured.ocr_provider == "crnn_vi_handwriting_v1"


def test_disabled_cloud_providers_do_not_require_keys(production_settings):
    configured = Settings(_env_file=None, **(production_settings | {
        "groq_enabled": False, "groq_api_keys": "",
        "gemini_enabled": False, "gemini_api_keys": "",
    }))
    assert configured.runtime_mode == "MODEL"


@pytest.mark.parametrize("override,message", [
    ({"runtime_mode": "FIXTURE"}, "RUNTIME_MODE=MODEL"),
    ({"ocr_provider": "noop"}, "real CRNN OCR_PROVIDER"),
    ({"canonical_runtime_override_enabled": True}, "CANONICAL_RUNTIME_OVERRIDE_ENABLED"),
    ({"internal_api_key": "secret-key-default"}, "INTERNAL_API_KEY"),
    ({"internal_api_key": ""}, "INTERNAL_API_KEY"),
    ({"internal_api_key": "too-short"}, "INTERNAL_API_KEY"),
    ({"internal_api_key": "x" * 40}, "INTERNAL_API_KEY"),
    ({"minio_access_key": "minioadmin"}, "MINIO_ACCESS_KEY"),
    ({"minio_secret_key": "minioadmin123"}, "MINIO_SECRET_KEY"),
    ({"groq_api_keys": " , "}, "GROQ_API_KEYS"),
    ({"gemini_api_keys": ""}, "GEMINI_API_KEYS"),
])
def test_production_rejects_incomplete_or_fake_runtime(production_settings, override, message):
    with pytest.raises(ValidationError, match=message) as error:
        Settings(_env_file=None, **(production_settings | override))
    # An invalid deployment must not leak other configured credentials in diagnostics.
    assert "unit-test-storage-secret" not in str(error.value)
    assert "unit-test-groq" not in str(error.value)
    assert "unit-test-gemini" not in str(error.value)


def test_development_keeps_fixture_configuration(production_settings):
    configured = Settings(_env_file=None, **(production_settings | {
        "app_env": "development", "runtime_mode": "FIXTURE", "ocr_provider": "noop",
        "internal_api_key": "secret-key-default",
    }))
    assert configured.runtime_mode == "FIXTURE"
