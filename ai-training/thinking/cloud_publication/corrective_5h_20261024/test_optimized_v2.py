"""CPU-only coherence, continuation and budget regression checks."""
from collections import Counter
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

root = Path(__file__).parent
spec = importlib.util.spec_from_file_location("optimized_v2", root / "corrective_worker_optimized_v2.py")
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


class OptimizedResumeTests(unittest.TestCase):
    def test_optimizer_steps_must_all_equal_acknowledged_step(self):
        valid = {"param_groups": [{"params": [0, 1]}], "state": {0: {"step": 120}, 1: {"step": 120}}}
        self.assertTrue(w.optimizer_coherence(valid, 120)["coherent"])
        for invalid in (
            {"param_groups": [{"params": [0, 1]}], "state": {0: {"step": 120}, 1: {"step": 121}}},
            {"param_groups": [{"params": [0, 1]}], "state": {0: {"step": 120}}},
            {"param_groups": [{"params": [0, 1]}], "state": {0: {"step": 120}, 1: {}}},
            {"param_groups": [{"params": [0, 0]}], "state": {0: {"step": 120}}},
            {"param_groups": [{"params": [0]}], "state": {0: {"step": 120, "value": float('nan')}}},
        ):
            with self.assertRaises(ValueError):
                w.optimizer_coherence(invalid, 120)

    def test_replan_lr_continuous_without_restarting_warmup(self):
        prior_elapsed, remaining, prior_lr = 600, 14000, 0.000032
        self.assertEqual(w.replan_lr(600, prior_elapsed, remaining, prior_lr), prior_lr)
        self.assertAlmostEqual(w.replan_lr(900, prior_elapsed, remaining, prior_lr), w.PEAK_LR)
        self.assertAlmostEqual(w.replan_lr(14600, prior_elapsed, remaining, prior_lr), w.MIN_LR)
        self.assertAlmostEqual(w.replan_lr(5000, 5000, 10000, 0.000043), 0.000043)
        self.assertAlmostEqual(w.replan_lr(15000, 5000, 10000, 0.000043), w.MIN_LR)

    def test_hard_deadline_cutoffs_and_reserve_exact(self):
        from datetime import datetime, timezone
        self.assertEqual(datetime.fromtimestamp(w.HARD_DEADLINE_UNIX, timezone.utc).isoformat(), "2026-10-24T05:28:23+00:00")
        self.assertEqual(datetime.fromtimestamp(w.TRAIN_STOP_UNIX, timezone.utc).isoformat(), "2026-10-24T05:13:23+00:00")
        self.assertEqual(w.HARD_DEADLINE_UNIX - w.TRAIN_STOP_UNIX, 900)
        self.assertEqual(w.sha_file(root / "owner_budget_revision_config.json"), w.OWNER_BUDGET_SHA256)

    def test_original_pairs_unchanged_other_objectives_rejected(self):
        group = list(range(16))
        rows = [{"encoded": {"input_ids": [1] * (17 - i)}} for i in group]
        self.assertEqual(w.regroup_same16(group, rows, 2), [[i, i + 1] for i in range(0, 16, 2)])
        for unsupported in (4, 8):
            with self.assertRaisesRegex(ValueError, "original micro2"):
                w.regroup_same16(group, rows, unsupported)

    def test_log_prefix_reconstruction_preserves_counts_cursor_and_no_unacked_suffix(self):
        rows = [{"sample_id": f"r{i}", "source_case_id": f"c{i//4}", "grade": 5,
                 "mode": "worked_solution", "family": "test", "encoded": {
                     "input_ids": [1, 2, w.EOT], "labels": [-100, 2, w.EOT]}} for i in range(32)]
        order = [i for batch in w.make_length_batches(rows, 0) for i in batch]
        entries = [{"step": index // 16 + 1, "sample_id": rows[i]["sample_id"], "epoch": 0}
                   for index, i in enumerate(order)]
        raw = "".join(w.canonical(row) + "\n" for row in entries).encode()
        metrics = {"step": 2, "rows_done": 32, "supervised_tokens": 64, "nonpadding_tokens": 96,
                   "unique_examples": 32, "unique_source_cases": 8,
                   "exposures_by_mode": {"worked_solution": 32}, "exposures_by_grade": {"5": 32},
                   "exposures_by_family": {"test": 32}}
        cursor = {"epoch": 0, "next_microbatch": 16}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ids.jsonl"
            path.write_bytes(raw + b'{"step":3,"unacknowledged":true}\n')
            state, prefix = w.rebuild_acknowledged_state(path, len(raw), metrics, rows, cursor)
            self.assertEqual(prefix, raw)
            self.assertEqual(state["rows_done"], 32)
            self.assertEqual(len(state["unique_ids"]), 32)
            self.assertEqual(state["exposures_by_grade"], Counter({"5": 32}))
            stale = dict(metrics, stop_reason="ERROR", training_stopped_unix=1)
            cleaned, _ = w.rebuild_acknowledged_state(path, len(raw), stale, rows, cursor)
            self.assertNotIn("stop_reason", cleaned)
            self.assertNotIn("training_stopped_unix", cleaned)
            for invalid_cursor, invalid_metrics in (
                (dict(cursor, next_microbatch=8), metrics),
                (cursor, dict(metrics, supervised_tokens=63)),
                (cursor, dict(metrics, exposures_by_family={"test": 31})),
            ):
                with self.assertRaises(ValueError):
                    w.rebuild_acknowledged_state(path, len(raw), invalid_metrics, rows, invalid_cursor)
            changed = list(entries)
            changed[0], changed[1] = changed[1], changed[0]
            path.write_bytes("".join(w.canonical(row) + "\n" for row in changed).encode())
            with self.assertRaisesRegex(ValueError, "optimizer order"):
                w.rebuild_acknowledged_state(path, path.stat().st_size, metrics, rows, cursor)

    def test_signal_only_requests_boundary_stop(self):
        w.STOP_REQUESTED = None
        w.request_boundary_stop(2, None)
        self.assertEqual(w.STOP_REQUESTED["signal"], 2)
        self.assertIn("requested_unix", w.STOP_REQUESTED)
        w.STOP_REQUESTED = None

    def test_oom_fallback_keeps_objective_and_fails_closed_at_limit(self):
        self.assertEqual(w.oom_fallback(8, "off"), (4, "on"))
        self.assertEqual(w.oom_fallback(4, "on"), (2, "on"))
        self.assertEqual(w.oom_fallback(2, "off"), (2, "on"))
        with self.assertRaises(RuntimeError):
            w.oom_fallback(2, "on")


if __name__ == "__main__":
    unittest.main()
