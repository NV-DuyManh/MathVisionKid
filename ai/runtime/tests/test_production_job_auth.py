"""Production queue ingress requires the shared backend secret before enqueueing."""
import uuid
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


@pytest.mark.parametrize("provided,expected_status", [
    (None, 403), ("wrong-key", 403), ("unit-test-internal-secret-123456789", 200),
])
def test_production_job_auth_before_enqueue(monkeypatch, mocker, provided, expected_status):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "internal_api_key", "unit-test-internal-secret-123456789")
    enqueue = mocker.patch("app.api.jobs.process_submission.delay")
    job_id = str(uuid.uuid4())
    payload = {
        "jobId": job_id,
        "submissionId": "unit-submission",
        "imageReference": "minio://mathvision/unit-image.jpg",
        "allowedOperations": ["VERTICAL_ADDITION"],
    }
    headers = {"X-Internal-API-Key": provided} if provided is not None else {}
    response = TestClient(app).post("/internal/v1/jobs", json=payload, headers=headers)
    assert response.status_code == expected_status
    if expected_status == 200:
        assert enqueue.call_args.args[0] == job_id
    else:
        enqueue.assert_not_called()
