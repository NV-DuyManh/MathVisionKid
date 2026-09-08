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
    # In a real scenario, check Redis connectivity and model loaded state
    from app.jobs.celery_app import celery_app
    redis_ok = False
    try:
        with celery_app.connection() as conn:
            conn.ensure_connection(max_retries=1)
        redis_ok = True
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
        
    return {
        "status": "ready" if redis_ok else "degraded",
        "redis_connected": redis_ok,
        "mode": settings.runtime_mode
    }
