import ast
import hashlib
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace

from status_report_cache import (
    EXPECTED_WORKER_SHA256,
    STATUS_REFRESH_ROWS,
    StatusReportCache,
)


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows

    def fetchone(self):
        return (self.rows,)

    def __iter__(self):
        return iter(self.rows)


class FakeDb:
    def __init__(self):
        self.rows = 10
        self.issues = {}

    def execute(self, sql):
        if sql == "SELECT coalesce(sum(next_line),0) FROM members WHERE role='candidate_chat'":
            return FakeCursor(self.rows)
        if sql == "SELECT kind,count(*) FROM issues GROUP BY kind":
            return FakeCursor(sorted(self.issues.items()))
        raise AssertionError(f"Unexpected cache probe SQL: {sql}")


def frozen_worker_fixture():
    pass


class StatusReportCacheTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeDb()
        self.audit = SimpleNamespace(db=self.db)
        self.calls = 0

        def original(auditor):
            self.calls += 1
            return {
                "schema": "MathVisionKid.full_current_archive_audit.v3",
                "unique_chat_rows_processed": auditor.db.rows,
                "issues": dict(auditor.db.issues),
                "TRAINING_DATASET_READY": False,
            }

        self.worker = frozen_worker_fixture
        self.cache = StatusReportCache(original, self.worker, status_line=2)
        self.status_caller = SimpleNamespace(f_code=self.worker.__code__, f_lineno=self.worker.__code__.co_firstlineno + 1)
        self.wrong_line_caller = SimpleNamespace(f_code=self.worker.__code__, f_lineno=self.worker.__code__.co_firstlineno + 2)
        self.other_caller = SimpleNamespace(f_code=(lambda: None).__code__, f_lineno=2)

    def test_status_cache_can_be_stale_but_only_until_row_threshold(self):
        first = self.cache.dispatch(self.audit, self.status_caller)
        self.assertEqual(first["unique_chat_rows_processed"], 10)
        self.db.rows += STATUS_REFRESH_ROWS - 1
        stale = self.cache.dispatch(self.audit, self.status_caller)
        self.assertEqual(stale["unique_chat_rows_processed"], 10)
        self.assertEqual(self.calls, 1)
        self.assertEqual(self.cache.metadata["last_report_source"], "cached_status_only")
        self.assertFalse(self.cache.metadata["last_report_fresh"])

        self.db.rows += 1
        refreshed = self.cache.dispatch(self.audit, self.status_caller)
        self.assertEqual(refreshed["unique_chat_rows_processed"], 10 + STATUS_REFRESH_ROWS)
        self.assertEqual(self.calls, 2)
        self.assertTrue(self.cache.metadata["last_report_fresh"])

    def test_issue_count_change_forces_fresh_status_report(self):
        self.cache.dispatch(self.audit, self.status_caller)
        self.db.issues["NEW_FINDING"] = 1
        result = self.cache.dispatch(self.audit, self.status_caller)
        self.assertEqual(result["issues"], {"NEW_FINDING": 1})
        self.assertEqual(self.calls, 2)

    def test_non_status_call_is_always_fresh_and_refreshes_cache(self):
        self.cache.dispatch(self.audit, self.status_caller)
        self.db.rows += 7
        self.db.issues["CHECKPOINT_FINDING"] = 1
        checkpoint = self.cache.dispatch(self.audit, self.other_caller)
        self.assertEqual(checkpoint["unique_chat_rows_processed"], 17)
        self.assertEqual(checkpoint["issues"], {"CHECKPOINT_FINDING": 1})
        self.assertEqual(self.cache.metadata["last_report_source"], "original_fresh_non_status")
        self.assertTrue(self.cache.metadata["last_report_fresh"])
        self.db.rows += 3
        status = self.cache.dispatch(self.audit, self.status_caller)
        self.assertEqual(status["unique_chat_rows_processed"], 17)
        self.assertEqual(self.calls, 2)

    def test_same_worker_code_at_wrong_line_is_fresh(self):
        self.cache.dispatch(self.audit, self.status_caller)
        self.db.rows += 8
        fresh = self.cache.dispatch(self.audit, self.wrong_line_caller)
        self.assertEqual(fresh["unique_chat_rows_processed"], 18)
        self.assertEqual(self.cache.metadata["last_report_source"], "original_fresh_non_status")
        self.db.rows += 4
        status = self.cache.dispatch(self.audit, self.status_caller)
        self.assertEqual(status["unique_chat_rows_processed"], 18)
        self.assertEqual(self.calls, 2)

    def test_foreign_thread_non_status_report_is_fresh_without_cache_mutation(self):
        self.cache.dispatch(self.audit, self.status_caller)
        owner = self.cache.owner_thread_id
        previous_report = self.cache.state.report
        previous_rows = self.cache.state.rows_at_refresh
        previous_metadata = dict(self.cache.metadata)
        self.db.rows += 12
        outcome = []

        def finalizer_call():
            outcome.append(self.cache.dispatch(self.audit, self.other_caller))

        thread = threading.Thread(target=finalizer_call)
        thread.start()
        thread.join()
        self.assertEqual(outcome[0]["unique_chat_rows_processed"], 22)
        self.assertEqual(self.cache.owner_thread_id, owner)
        self.assertIs(self.cache.state.report, previous_report)
        self.assertEqual(self.cache.state.rows_at_refresh, previous_rows)
        self.assertEqual(self.cache.metadata, previous_metadata)
        status = self.cache.dispatch(self.audit, self.status_caller)
        self.assertEqual(status["unique_chat_rows_processed"], 10)
        self.assertEqual(self.calls, 2)

    def test_non_status_call_does_not_establish_cache_owner(self):
        result = self.cache.dispatch(self.audit, self.other_caller)
        self.assertEqual(result["unique_chat_rows_processed"], 10)
        self.assertIsNone(self.cache.owner_thread_id)
        self.assertIsNone(self.cache.state.report)

    def test_mutating_cached_status_copy_does_not_mutate_cache(self):
        self.cache.dispatch(self.audit, self.status_caller)
        stale = self.cache.dispatch(self.audit, self.status_caller)
        stale["issues"]["caller_mutation"] = 99
        again = self.cache.dispatch(self.audit, self.status_caller)
        self.assertEqual(again["issues"], {})

    def test_frozen_worker_source_pin_and_unique_status_callsite(self):
        launch = Path(__file__).with_name("launch_single_worker.py")
        source = launch.read_text(encoding="utf-8")
        tree = ast.parse(source)
        worker = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                      and node.name == "finite_full_data_audit_worker_v3")
        worker_text = "\n".join(source.splitlines()[worker.lineno - 1:worker.end_lineno]) + "\n"
        self.assertEqual(hashlib.sha256(worker_text.encode("utf-8")).hexdigest(), EXPECTED_WORKER_SHA256)
        sites = []
        for node in ast.walk(worker):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute) or node.func.attr != "update":
                continue
            if not isinstance(node.func.value, ast.Name) or node.func.value.id != "full_audit_worker_state":
                continue
            if any(k.arg == "report" and isinstance(k.value, ast.Call)
                   and isinstance(k.value.func, ast.Attribute) and k.value.func.attr == "report"
                   and isinstance(k.value.func.value, ast.Name) and k.value.func.value.id == "auditor"
                   for k in node.keywords):
                sites.append(node.lineno)
        self.assertEqual(len(sites), 1)
        self.assertEqual(sites[0] - worker.lineno + 1, 57)


if __name__ == "__main__":
    unittest.main()
