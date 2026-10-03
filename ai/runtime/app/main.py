import logging
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from app.config import settings
from app.api import jobs, ocr
from app.observability.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="MathVision Kids AI Service")

@app.on_event("startup")
async def on_startup():
    if settings.groq_enabled and settings.groq_api_keys:
        from app.integrations.groq.validator import validate_groq_models
        try:
            await validate_groq_models()
        except Exception as e:
            logger.warning(f"Groq startup model validation error: {e}")

app.include_router(jobs.router, prefix="/internal/v1/jobs", tags=["Jobs"])
app.include_router(ocr.router, prefix="/internal/v1/ocr", tags=["OCR"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "mathvision-ai-service"}

@app.get("/internal/v1/groq-health")
async def groq_health_check():
    from app.integrations.groq.health import groq_health
    return groq_health()

@app.get("/ready")
async def readiness_check():
    from app.jobs.celery_app import celery_app
    redis_ok = False
    try:
        with celery_app.connection() as conn:
            conn.ensure_connection(max_retries=1)
        redis_ok = True
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")

    model_ok = True
    if settings.runtime_mode == "MODEL":
        from app.recognition.model_engine import ModelRecognitionEngine
        try:
            engine = ModelRecognitionEngine()
            model_ok = engine.is_ready
        except Exception as e:
            logger.warning(f"Model readiness check failed: {e}")
            model_ok = False

    workers = []
    if redis_ok:
        from app.jobs.celery_app import active_mathvision_workers
        try:
            workers = active_mathvision_workers()
        except Exception as e:
            logger.warning(f"Worker readiness check failed: {type(e).__name__}")

    is_ready = redis_ok and model_ok and bool(workers)
    return JSONResponse(status_code=200 if is_ready else 503, content={
        "status": "ready" if is_ready else "NOT_READY",
        "redis_connected": redis_ok,
        "model_loaded": model_ok,
        "worker_available": bool(workers),
        "arithmetic_ready": is_ready,
        "mode": settings.runtime_mode,
    })
