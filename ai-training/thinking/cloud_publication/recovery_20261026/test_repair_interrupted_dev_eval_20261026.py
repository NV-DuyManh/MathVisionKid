import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "repair_interrupted_dev_eval_20261026.py"
SPEC = importlib.util.spec_from_file_location("repair_eval_test", SCRIPT)
repair = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(repair)


def fake_rows(count=30):
    fixtures = [{"id": f"f{i:02}", "grade": 1, "mode": "answer"} for i in range(count)]
    contract = {"prompt_token_sha256": {f["id"]: f"p{i}" for i, f in enumerate(fixtures)},
                "decoding": {"max_new_tokens": 1024}}
    rows = []
    for i, fixture in enumerate(fixtures):
        rows.append({"fixture_id": fixture["id"], "grade": 1, "mode": "answer",
                     "stage": "adapter_after_training", "contract_sha256": "c",
                     "prompt_token_sha256": f"p{i}", "max_new_tokens": 1024,
                     "seed": (20261024 + int(hashlib.sha256(fixture["id"].encode()).hexdigest()[:8], 16)) % (2**31),
                     "timed_out": i == 0, "ended_eos": False, "possibly_truncated": True})
    return fixtures, contract, rows


class RepairPrefixTests(unittest.TestCase):
    def test_timed_out_prefix_row_still_consumes_fixture(self):
        fixtures, contract, rows = fake_rows()
        remaining = repair.validate_prefix(rows[:1], fixtures, contract, "c")
        self.assertEqual(remaining, [f["id"] for f in fixtures[1:]])

    def test_rejects_duplicate_or_skipped_prefix_id(self):
        fixtures, contract, rows = fake_rows()
        broken = [dict(rows[0]), dict(rows[0])]
        with self.assertRaises(ValueError):
            repair.validate_prefix(broken, fixtures, contract, "c")
        with self.assertRaises(ValueError):
            repair.validate_prefix([rows[1]], fixtures, contract, "c")

    def test_rejects_contract_or_prompt_drift(self):
        fixtures, contract, rows = fake_rows()
        with self.assertRaises(ValueError):
            repair.validate_prefix(rows[:1], fixtures, contract, "different")
        bad = dict(rows[0], prompt_token_sha256="wrong")
        with self.assertRaises(ValueError):
            repair.validate_prefix([bad], fixtures, contract, "c")

    def test_import_does_not_load_training_or_gpu_libraries(self):
        self.assertNotIn("torch", sys.modules)
        self.assertNotIn("bitsandbytes", sys.modules)

    def test_combined_bytes_preserve_original_prefix_hash(self):
        prefix = b'{"fixture_id":"f00"}\n'
        suffix = b'{"fixture_id":"f01"}\n'
        merged = prefix + suffix
        self.assertEqual(hashlib.sha256(merged[:len(prefix)]).hexdigest(),
                         hashlib.sha256(prefix).hexdigest())
        self.assertEqual([r["fixture_id"] for r in repair.read_jsonl_bytes(merged)], ["f00", "f01"])


if __name__ == "__main__":
    unittest.main()
