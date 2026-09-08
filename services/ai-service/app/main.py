import logging
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.config import settings
from app.api import jobs
from app.observability.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="MathVision Kids AI Service")

app.include_router(jobs.router, prefix="/internal/v1/jobs", tags=["Jobs"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "mathvision-ai-service"}

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

    is_ready = redis_ok and model_ok
    return {
        "status": "ready" if is_ready else "NOT_READY",
        "redis_connected": redis_ok,
        "model_loaded": model_ok,
        "mode": settings.runtime_mode
    }
