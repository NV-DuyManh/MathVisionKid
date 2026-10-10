import uuid
import logging
import secrets
from fastapi import APIRouter, HTTPException, Request, Depends
from app.config import settings
from app.schemas.jobs import JobRequest, JobResponse
from app.jobs.tasks import process_submission

logger = logging.getLogger(__name__)
router = APIRouter()


async def require_production_internal_key(request: Request):
    if settings.app_env.lower() not in {"production", "prod"}:
        return
    provided = request.headers.get("X-Internal-API-Key", "")
    if not provided or not secrets.compare_digest(provided.encode(), settings.internal_api_key.encode()):
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("", response_model=JobResponse, dependencies=[Depends(require_production_internal_key)])
async def submit_job(request: JobRequest):
    # Spring Boot owns the jobId lifecycle. jobId is strictly required.
    job_id = str(request.jobId)

    logger.info(
        "Received job",
        extra={"job_id": job_id, "submission_id": request.submissionId}
    )

    # Enqueue Celery task with the authoritative jobId
    process_submission.delay(job_id, request.model_dump(mode="json"))

    return JobResponse(jobId=job_id, status="QUEUED")
