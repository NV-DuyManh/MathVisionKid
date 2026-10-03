from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.jobs.celery_app import active_mathvision_workers
import pytest


def test_worker_ping_rejects_unrelated_worker(mocker):
    ping = mocker.patch("app.jobs.celery_app.celery_app.control.ping",
                        return_value=[{"other@host": {"ok": "pong"}}])
    assert active_mathvision_workers() == []
    ping.return_value.append({"mathvision@host": {"ok": "pong"}})
    assert active_mathvision_workers() == ["mathvision@host"]


def test_unit_task_enqueue_cannot_write_the_live_broker():
    from app.jobs.tasks import process_submission
    with pytest.raises(AssertionError, match="cannot write live Redis"):
        process_submission.delay("must-not-queue", {})


def test_readiness_requires_arithmetic_worker_but_health_remains_available(mocker):
    mocker.patch("app.jobs.celery_app.celery_app.connection")
    workers = mocker.patch("app.jobs.celery_app.active_mathvision_workers", return_value=[])
    client = TestClient(app)
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["redis_connected"] is True
    assert response.json()["worker_available"] is False
    assert response.json()["arithmetic_ready"] is False
    assert client.get("/health").status_code == 200
    workers.return_value = ["mathvision@host"]
    assert client.get("/ready").status_code == 200


def test_readiness_does_not_claim_corrupt_model_loaded(mocker, monkeypatch):
    monkeypatch.setattr(settings, "runtime_mode", "MODEL")
    mocker.patch("app.jobs.celery_app.celery_app.connection")
    mocker.patch("app.jobs.celery_app.active_mathvision_workers", return_value=["mathvision@host"])
    mocker.patch("app.recognition.model_engine.ModelRecognitionEngine", return_value=mocker.Mock(is_ready=False))
    response = TestClient(app).get("/ready")
    assert response.status_code == 503
    assert response.json()["model_loaded"] is False
