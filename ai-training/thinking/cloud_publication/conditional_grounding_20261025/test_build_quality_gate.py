import importlib.util
from pathlib import Path
import json
import tempfile
import unittest

HERE = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location("gate_builder_under_test", HERE / "build_quality_gate.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class GateBuilderValidationTests(unittest.TestCase):
    def test_accepts_exact_frozen_baseline_flags(self):
        gate.validate_baseline_flags(
            {"base_pass": True, "base_hint_leak": False},
            {"base_pass": True, "base_hint_leak": False},
        )

    def test_rejects_baseline_drift(self):
        with self.assertRaisesRegex(ValueError, "frozen review"):
            gate.validate_baseline_flags(
                {"base_pass": False, "base_hint_leak": False},
                {"base_pass": True, "base_hint_leak": False},
            )

    def test_rejects_missing_or_duplicate_ids(self):
        with self.assertRaisesRegex(ValueError, "missing or duplicate"):
            gate.validate_unique_decision_ids([{"fixture_id": "a"}], ["a", "b"])
        with self.assertRaisesRegex(ValueError, "missing or duplicate"):
            gate.validate_unique_decision_ids(
                [{"fixture_id": "a"}, {"fixture_id": "a"}], ["a", "b"]
            )

    def test_rejects_missing_decision_flags(self):
        decision = {"fixture_id": "a", "base_pass": True}
        with self.assertRaisesRegex(ValueError, "hint-leak flag"):
            gate.validate_baseline_flags(decision, {"base_pass": True, "base_hint_leak": False})

    def test_atomic_publish_is_complete_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "gate.json"
            gate.atomic_publish_no_overwrite(target, {"ready": True})
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"ready": True})
            with self.assertRaises(FileExistsError):
                gate.atomic_publish_no_overwrite(target, {"ready": False})
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"ready": True})
            self.assertFalse(target.with_name(target.name + ".lock").exists())
            self.assertEqual(list(Path(temp_dir).glob("*.pending")), [])


if __name__ == "__main__":
    unittest.main()
