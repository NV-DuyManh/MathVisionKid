"""Synthetic CPU tests for the local gate-binding helper; no run data is read."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location("recovery_gate_builder_test", HERE / "build_quality_gate_20261026.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


def synthetic_pairs():
    fixtures, frozen, decisions, base, adapter = [], [], [], [], []
    for i in range(30):
        fid = f"fx{i:02d}"
        mode = "answer" if i < 10 else "hint_no_answer" if i < 20 else "missing_or_contradictory_info" if i < 25 else "student_error"
        fixture = {"id": fid, "grade": i % 5 + 1, "mode": mode}
        base_text = f"base-output-{fid}"
        adapter_text = f"adapter-output-{fid}"
        base_pass = mode == "answer"
        leak = mode == "hint_no_answer"
        fixtures.append(fixture)
        frozen.append({"fixture_id": fid, "grade": fixture["grade"], "mode": mode,
                       "base_pass": base_pass, "base_hint_leak": leak,
                       "actual_output_sha256": gate.sha_bytes(base_text.encode("utf-8"))})
        decisions.append({"fixture_id": fid, "grade": fixture["grade"], "mode": mode,
                          "base_pass": base_pass, "base_hint_leak": leak,
                          "adapter_pass": base_pass, "adapter_hint_leak": leak,
                          "critical_new_error": False, "base_reason": "base reason", "adapter_reason": "candidate reason"})
        base.append({"fixture_id": fid, "stage": "base_before_training", "output": base_text,
                     "ended_eos": True, "possibly_truncated": False, "timed_out": False})
        adapter.append({"fixture_id": fid, "stage": "adapter_after_training", "output": adapter_text,
                        "ended_eos": True, "possibly_truncated": False, "timed_out": False})
    return fixtures, frozen, decisions, base, adapter


class GateBuilderTests(unittest.TestCase):
    def test_accepts_exact_frozen_flags_and_binds_output_hashes(self):
        fixtures, frozen, decisions, base, adapter = synthetic_pairs()
        enriched = gate.validate_pairwise_decisions(decisions, fixtures, frozen, base, adapter)
        self.assertEqual(len(enriched), 30)
        self.assertEqual(enriched[0]["base_output_sha256"], frozen[0]["actual_output_sha256"])
        self.assertEqual(enriched[0]["adapter_output_sha256"], gate.sha_bytes(adapter[0]["output"].encode()))

    def test_rejects_frozen_baseline_flag_drift(self):
        fixtures, frozen, decisions, base, adapter = synthetic_pairs()
        decisions[0]["base_pass"] = False
        with self.assertRaisesRegex(ValueError, "baseline pass differs from frozen"):
            gate.validate_pairwise_decisions(decisions, fixtures, frozen, base, adapter)

    def test_rejects_missing_or_duplicate_fixture_decisions(self):
        with self.assertRaisesRegex(ValueError, "missing or duplicate"):
            gate.validate_unique_decision_ids([{"fixture_id": "a"}], ["a", "b"])
        with self.assertRaisesRegex(ValueError, "missing or duplicate"):
            gate.validate_unique_decision_ids([{"fixture_id": "a"}, {"fixture_id": "a"}], ["a", "b"])

    def test_rejects_missing_semantic_flags(self):
        with self.assertRaisesRegex(ValueError, "baseline pass differs"):
            gate.validate_baseline_flags({"base_hint_leak": False}, {"base_pass": True, "base_hint_leak": False})

    def test_rejects_truncated_candidate_marked_as_pass(self):
        fixtures, frozen, decisions, base, adapter = synthetic_pairs()
        # Make the row a non-leaking hint that the candidate is judged to pass.
        decisions[20]["adapter_pass"] = True
        adapter[20]["ended_eos"] = False
        with self.assertRaisesRegex(ValueError, "truncated/timed-out"):
            gate.validate_pairwise_decisions(decisions, fixtures, frozen, base, adapter)

    def test_atomic_publish_is_no_overwrite_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "gate.json"
            gate.atomic_publish_no_overwrite(target, {"ready": True})
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"ready": True})
            with self.assertRaises(FileExistsError):
                gate.atomic_publish_no_overwrite(target, {"ready": False})
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"ready": True})
            self.assertFalse(target.with_name(target.name + ".lock").exists())
            self.assertEqual(list(Path(directory).glob("*.pending")), [])

    def test_import_does_not_load_worker_or_policy(self):
        self.assertNotIn("recovery_20261026_gate_worker", sys.modules)
        self.assertNotIn("recovery_20261026_gate_policy", sys.modules)


if __name__ == "__main__":
    unittest.main()
