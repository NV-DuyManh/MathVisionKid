"""
Startup Groq Model Validator.
Validates configured Groq vision models at application startup.
Never crashes application if Groq is unavailable.
"""

import httpx
import logging
import time
from typing import Dict, Any, Optional
from app.config import settings
from app.integrations.groq.line_analyzer import get_pool

logger = logging.getLogger(__name__)

# Cached validation state
_validation_cache: Optional[Dict[str, Any]] = None


async def validate_groq_models(
    primary_model: Optional[str] = None,
    fallback_model: Optional[str] = None,
    timeout_seconds: float = 10.0,
) -> Dict[str, Any]:
    """
    Validate configured models with Groq API.
    Checks catalog/text availability, not image inference capability. Logs safe status.
    Never raises an exception.
    """
    global _validation_cache

    primary = primary_model or settings.groq_primary_vision_model
    fallback = fallback_model or settings.groq_fallback_vision_model

    result: Dict[str, Any] = {
        "primary": {
            "model": primary,
            "status": "UNAVAILABLE",
            "available": False,
            "vision_capable": None,
            "probeKind": None,
            "catalogAvailable": None,
            "liveProbe": False,
            "lastHttpStatus": None,
            "lastErrorClass": None,
        },
        "fallback": {
            "model": fallback,
            "status": "UNAVAILABLE",
            "available": False,
            "vision_capable": None,
            "probeKind": None,
            "catalogAvailable": None,
            "liveProbe": False,
            "lastHttpStatus": None,
            "lastErrorClass": None,
        },
        "checked_at": time.time(),
        "error": None,
    }

    if not settings.groq_enabled or not settings.groq_api_keys:
        result["primary"]["status"] = "DISABLED"
        result["fallback"]["status"] = "DISABLED"
        _validation_cache = result
        logger.info(
            f"Groq Vision Models:\n"
            f"primary:\n{primary}\nDISABLED\n"
            f"fallback:\n{fallback}\nDISABLED\n"
            f"Fallback: LOCAL_CV_CRNN"
        )
        return result

    pool = get_pool()
    entry = pool.acquire() if pool else None
    if not entry:
        result["primary"]["status"] = "NO_KEYS"
        result["fallback"]["status"] = "NO_KEYS"
        _validation_cache = result
        logger.warning(
            f"Groq Vision Models:\n"
            f"primary:\n{primary}\nNO_KEYS\n"
            f"fallback:\n{fallback}\nNO_KEYS\n"
            f"Fallback: LOCAL_CV_CRNN"
        )
        return result

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            resp = await client.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {entry.raw_key}"},
            )
            if resp.status_code == 200:
                pool.report_success(entry)
                data = resp.json().get("data", [])
                available_ids = {m.get("id") for m in data if "id" in m}

                primary_in_catalog = primary in available_ids
                fallback_in_catalog = fallback in available_ids

                result["primary"]["catalogAvailable"] = primary_in_catalog
                result["primary"]["available"] = primary_in_catalog
                result["primary"]["status"] = "AVAILABLE" if primary_in_catalog else "UNAVAILABLE"
                result["primary"]["lastHttpStatus"] = 200
                # Catalog membership does not establish image input support.

                result["fallback"]["catalogAvailable"] = fallback_in_catalog

                # A missing model cannot become an image fallback after a text
                # "ping". Do not spend inference quota or mislabel catalog checks
                # as live image evidence. The HTTP status belongs to GET /models.
                result["fallback"]["status"] = "AVAILABLE" if fallback_in_catalog else "UNAVAILABLE"
                result["fallback"]["available"] = fallback_in_catalog
                result["fallback"]["lastHttpStatus"] = 200
                for role in ('primary', 'fallback'):
                    if result[role]['catalogAvailable'] is False:
                        result[role]['lastErrorClass'] = 'MODEL_NOT_IN_CATALOG'
            else:
                result["error"] = f"HTTP {resp.status_code}"
                for role in ('primary', 'fallback'):
                    result[role]['lastHttpStatus'] = resp.status_code
                    result[role]['lastErrorClass'] = f'HTTP_{resp.status_code}'
    except Exception as e:
        # Exception bodies can carry request credentials or provider text.
        result["error"] = type(e).__name__
        for role in ('primary', 'fallback'):
            result[role]['lastErrorClass'] = type(e).__name__
        logger.warning('Groq model validation unavailable: %s', type(e).__name__)

    _validation_cache = result

    # Log safe model status
    logger.info(
        f"Groq Vision Models:\n\n"
        f"primary:\n"
        f"{primary}\n"
        f"{result['primary']['status']} (catalog={result['primary'].get('catalogAvailable', False)}, live={result['primary'].get('liveProbe', False)})\n\n"
        f"fallback:\n"
        f"{fallback}\n"
        f"{result['fallback']['status']} (catalog={result['fallback'].get('catalogAvailable', False)}, live={result['fallback'].get('liveProbe', False)}, error={result['fallback'].get('lastErrorClass')})\n\n"
        f"Fallback:\n"
        f"LOCAL_CV_CRNN"
    )

    return result


def get_model_validation_status() -> Dict[str, Any]:
    """Return the cached validation status or a default offline status."""
    global _validation_cache
    if _validation_cache is not None:
        return _validation_cache
    return {
        "primary": {
            "model": settings.groq_primary_vision_model,
            "status": "NOT_CHECKED",
            "available": False,
            "vision_capable": None,
            "probeKind": None,
            "catalogAvailable": None,
            "liveProbe": False,
            "lastHttpStatus": None,
            "lastErrorClass": None,
        },
        "fallback": {
            "model": settings.groq_fallback_vision_model,
            "status": "NOT_CHECKED",
            "available": False,
            "vision_capable": None,
            "probeKind": None,
            "catalogAvailable": None,
            "liveProbe": False,
            "lastHttpStatus": None,
            "lastErrorClass": None,
        },
        "checked_at": 0.0,
        "error": None,
    }
