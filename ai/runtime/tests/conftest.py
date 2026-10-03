import pytest
from app.config import settings

@pytest.fixture(autouse=True)
def default_fixture_mode(monkeypatch):
    """Ensure unit/regression tests run in FIXTURE mode by default unless explicitly overridden by model tests."""
    monkeypatch.setattr(settings, "runtime_mode", "FIXTURE")


@pytest.fixture(autouse=True)
def isolate_arithmetic_broker(monkeypatch):
    """Unit/in-process integration tests must not create jobs on the user's Redis queue."""
    from app.jobs.tasks import process_submission

    def refuse_live_enqueue(*args, **kwargs):
        raise AssertionError("Mock arithmetic task enqueue explicitly; unit tests cannot write live Redis jobs.")

    monkeypatch.setattr(process_submission, "apply_async", refuse_live_enqueue)
