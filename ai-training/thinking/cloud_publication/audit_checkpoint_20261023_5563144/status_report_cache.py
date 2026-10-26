"""Status-only cache for the exact frozen full-audit worker progress call."""

from __future__ import annotations

import ast
import copy
import hashlib
import inspect
import textwrap
import threading
from dataclasses import dataclass
from pathlib import Path
from types import FunctionType
from typing import Any, Callable


EXPECTED_WORKER_SHA256 = "a99c102e1c23e520da1e3ca23eb5a7ca6e0e32a0ef8f7ec5321c3ef8474f20d9"
EXPECTED_AUDIT_SHA256 = "02431da433060a6574127f9a8e14d90cabffe85d8d0150c3b2a331dc15b4be1f"
EXPECTED_BATCH_SHA256 = "8d978eceeabebda9103ae23a16c23beab5b8cf5f2248984eda0b584facbedf92"
STATUS_REFRESH_ROWS = 200_000


def _file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _status_report_relative_line(worker: FunctionType) -> int:
    """Find the single frozen progress-only report call in the worker AST."""
    source = textwrap.dedent(inspect.getsource(worker))
    tree = ast.parse(source)
    candidates: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute) or node.func.attr != "update":
            continue
        if not isinstance(node.func.value, ast.Name) or node.func.value.id != "full_audit_worker_state":
            continue
        for keyword in node.keywords:
            value = keyword.value
            if (keyword.arg == "report" and isinstance(value, ast.Call)
                    and isinstance(value.func, ast.Attribute) and value.func.attr == "report"
                    and isinstance(value.func.value, ast.Name) and value.func.value.id == "auditor"):
                candidates.append(node.lineno)
    if len(candidates) != 1:
        raise RuntimeError(f"Expected one frozen status report call, found {len(candidates)}")
    return candidates[0]


@dataclass
class _CacheState:
    report: dict[str, Any] | None = None
    rows_at_refresh: int | None = None
    issue_counts: tuple[tuple[str, int], ...] | None = None


class StatusReportCache:
    """Cache only calls from the exact worker progress-update source line.

    Every other caller invokes the preserved original report method and refreshes
    the status cache from that fresh result. Cursor/issue probes run in the
    scanner thread using its existing SQLite connection.
    """

    def __init__(self, original_report: Callable[..., dict[str, Any]], worker: FunctionType,
                 status_line: int | None = None):
        self.original_report = original_report
        self.worker_code = worker.__code__
        self.worker_status_line = worker.__code__.co_firstlineno + (
            (status_line if status_line is not None else _status_report_relative_line(worker)) - 1
        )
        self.state = _CacheState()
        self.owner_thread_id: int | None = None
        self.metadata: dict[str, Any] = {
            "status_report_cache_hits": 0,
            "fresh_original_reports": 0,
            "last_report_source": None,
            "last_report_fresh": None,
            "last_refresh_rows": None,
        }

    @staticmethod
    def _cursor_and_issues(auditor: Any) -> tuple[int, tuple[tuple[str, int], ...]]:
        # members.role identifies candidate_chat versus candidate_source in v3;
        # next_line is the durable per-member physical cursor.
        row = auditor.db.execute(
            "SELECT coalesce(sum(next_line),0) FROM members WHERE role='candidate_chat'"
        ).fetchone()
        rows = int(row[0])
        issue_counts = tuple(sorted((str(kind), int(count)) for kind, count in auditor.db.execute(
            "SELECT kind,count(*) FROM issues GROUP BY kind")))
        return rows, issue_counts

    def _is_status_site(self, caller: Any) -> bool:
        return (caller is not None and caller.f_code is self.worker_code
                and caller.f_lineno == self.worker_status_line)

    def dispatch(self, auditor: Any, caller: Any) -> dict[str, Any]:
        thread_id = threading.get_ident()
        status_site = self._is_status_site(caller)
        if not status_site:
            # Checkpoint/final/error callers always receive the original fresh
            # report. A foreign finalizer thread must never touch worker cache
            # state or the worker-owned SQLite connection.
            fresh = self.original_report(auditor)
            if self.owner_thread_id is None or self.owner_thread_id != thread_id:
                return fresh
            rows, _ = self._cursor_and_issues(auditor)
            self.state.report = copy.deepcopy(fresh)
            self.state.rows_at_refresh = rows
            self.state.issue_counts = tuple(sorted(
                (str(kind), int(count)) for kind, count in fresh["issues"].items()))
            self.metadata.update(fresh_original_reports=self.metadata["fresh_original_reports"] + 1,
                                 last_report_source="original_fresh_non_status",
                                 last_report_fresh=True, last_refresh_rows=self.state.rows_at_refresh)
            return fresh

        if self.owner_thread_id is None:
            self.owner_thread_id = thread_id
        elif self.owner_thread_id != thread_id:
            raise RuntimeError("Status report cache status site ran outside its owning scanner thread")

        rows, issue_counts = self._cursor_and_issues(auditor)
        state = self.state
        can_reuse = (status_site and state.report is not None and state.rows_at_refresh is not None
                     and 0 <= rows - state.rows_at_refresh < STATUS_REFRESH_ROWS
                     and issue_counts == state.issue_counts)
        if can_reuse:
            self.metadata.update(status_report_cache_hits=self.metadata["status_report_cache_hits"] + 1,
                                 last_report_source="cached_status_only", last_report_fresh=False,
                                 last_refresh_rows=state.rows_at_refresh)
            return copy.deepcopy(state.report)

        fresh = self.original_report(auditor)
        # Preserve the original report mapping unchanged for its caller. Keep a
        # defensive copy separately so status consumers cannot mutate the cache.
        state.report = copy.deepcopy(fresh)
        state.rows_at_refresh = rows
        state.issue_counts = issue_counts
        self.metadata.update(fresh_original_reports=self.metadata["fresh_original_reports"] + 1,
                             last_report_source="original_fresh_status", last_report_fresh=True,
                             last_refresh_rows=rows)
        return fresh


def install_status_report_cache(namespace: dict[str, Any]) -> StatusReportCache:
    """Install the guarded wrapper into the exact frozen audit class namespace."""
    audit_module = namespace["audit_v3"]
    batch_module = namespace["batch_module"]
    if _file_sha256(audit_module.__file__) != EXPECTED_AUDIT_SHA256:
        raise RuntimeError("Frozen v3 audit source hash mismatch")
    if _file_sha256(batch_module.__file__) != EXPECTED_BATCH_SHA256:
        raise RuntimeError("Frozen batch adapter source hash mismatch")
    worker = namespace["finite_full_data_audit_worker_v3"]
    if not isinstance(worker, FunctionType) or worker.__name__ != "finite_full_data_audit_worker_v3":
        raise RuntimeError("Expected the exact frozen finite audit worker function")
    worker_source = textwrap.dedent(inspect.getsource(worker)).encode("utf-8")
    if hashlib.sha256(worker_source).hexdigest() != EXPECTED_WORKER_SHA256:
        raise RuntimeError("Frozen worker source hash mismatch")
    audit_type = audit_module.FullArchiveAudit
    if getattr(audit_type, "_status_report_cache_installed", False):
        raise RuntimeError("Status-only report cache is already installed")

    original = audit_type.report
    cache = StatusReportCache(original, worker)

    def report_with_status_cache(auditor: Any) -> dict[str, Any]:
        caller = inspect.currentframe().f_back
        if type(auditor) is not audit_type:
            return original(auditor)
        return cache.dispatch(auditor, caller)

    report_with_status_cache.__name__ = original.__name__
    report_with_status_cache.__doc__ = original.__doc__
    report_with_status_cache.__status_cache_original__ = original
    audit_type.report = report_with_status_cache
    audit_type._status_report_cache_installed = True
    namespace["_status_report_cache"] = cache
    namespace["_status_report_cache_original"] = original
    return cache


def restore_status_report_cache(namespace: dict[str, Any]) -> None:
    """Restore the original method after the original worker has stopped."""
    worker_thread = namespace.get("full_audit_worker")
    if worker_thread is not None and worker_thread.is_alive():
        raise RuntimeError("Cannot restore the report method while the worker is alive")
    audit_type = namespace["audit_v3"].FullArchiveAudit
    original = namespace.get("_status_report_cache_original")
    if original is None or not getattr(audit_type, "_status_report_cache_installed", False):
        raise RuntimeError("Status-only report cache is not installed")
    audit_type.report = original
    delattr(audit_type, "_status_report_cache_installed")
    namespace.pop("_status_report_cache", None)
    namespace.pop("_status_report_cache_original", None)
