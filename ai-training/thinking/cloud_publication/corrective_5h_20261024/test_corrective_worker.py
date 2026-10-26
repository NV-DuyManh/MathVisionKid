"""Focused CPU-only checks; never imports an installed GPU runtime or Drive."""
from collections import Counter
import importlib.util
import json
from pathlib import Path
import pickle
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("corrective_worker", Path(__file__).with_name("corrective_worker.py"))
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


class Tokenizer:
    pad_token_id = 151643

    def apply_chat_template(self, messages, **kwargs):
        assert kwargs["enable_thinking"] is False
        assert kwargs["add_generation_prompt"] is True
        return list(json.dumps(messages, ensure_ascii=False).encode("utf-8"))


class CorrectiveContractTests(unittest.TestCase):
    def test_actual_five_hour_boundary_has_no_short_step_cap(self):
        start = 123.0
        self.assertEqual(w.TRAIN_SECONDS, 5 * 60 * 60)
        self.assertTrue(w.group_may_start(start, start))
        self.assertTrue(w.group_may_start(start + 17999.999, start))
        self.assertFalse(w.group_may_start(start + 18000, start))
        self.assertFalse(w.group_may_start(start + 18000.001, start))

    def test_wall_scheduler_nonzero_start_exact_peak_and_floor(self):
        self.assertEqual(w.lr_at_elapsed(-1), 1e-6)
        self.assertEqual(w.lr_at_elapsed(0), 1e-6)
        self.assertAlmostEqual(w.lr_at_elapsed(450), (1e-6 + 5e-5) / 2)
        self.assertAlmostEqual(w.lr_at_elapsed(900), 5e-5)
        self.assertAlmostEqual(w.lr_at_elapsed(9450), (5e-5 + 5e-6) / 2)
        self.assertAlmostEqual(w.lr_at_elapsed(18000), 5e-6)
        self.assertAlmostEqual(w.lr_at_elapsed(20000), 5e-6)
        self.assertLess(abs(w.lr_at_elapsed(899.999) - w.lr_at_elapsed(900.001)), 1e-9)
        decay = [w.lr_at_elapsed(i) for i in range(900, 18001, 100)]
        self.assertTrue(all(a >= b for a, b in zip(decay, decay[1:])))

    def test_model_modes_and_reference_answers_never_enter_prompt(self):
        for reporting_mode, model_mode in w.MODE_MAP.items():
            fixture = {"id": "synthetic", "grade": 5, "mode": reporting_mode,
                       "userproblem": "A student wrote 3/5 = 0.3. Check this work.",
                       "exact_reference_answer": {"SECRET": "NEVER_PROMPT_THIS"},
                       "oracle": {"secret": "NEVER_PROMPT_ORACLE"}, "rubric": ["SECRET_RUBRIC"]}
            messages = w.fixture_messages(fixture)
            user = json.loads(messages[1]["content"])
            self.assertEqual(set(user), {"grade", "problem", "mode"})
            self.assertEqual(user["problem"], fixture["userproblem"])
            self.assertEqual(user["mode"], model_mode)
            self.assertEqual(messages[0]["content"], w.SYSTEM)
            self.assertNotIn("SECRET", json.dumps(messages))
            self.assertNotIn("student_work", user)

    def test_contract_changes_when_prompt_changes_and_binds_both_limits(self):
        fixture = {"id": "synthetic", "grade": 2, "mode": "hint_no_answer", "userproblem": "A + B?"}
        contract, sha = w.eval_contract([fixture], Tokenizer())
        self.assertEqual(contract["decoding"]["max_new_tokens"], 1024)
        self.assertEqual(contract["decoding"]["eos_token_id"], 151645)
        self.assertFalse(contract["decoding"]["do_sample"])
        self.assertEqual(w.digest(w.SYSTEM.encode("utf-8")), w.SYSTEM_SHA256)
        self.assertEqual(w.eval_contract([fixture], Tokenizer())[1], sha)
        changed = dict(fixture, userproblem="A - B?")
        self.assertNotEqual(w.eval_contract([changed], Tokenizer())[1], sha)

    def test_epochs_reshuffle_without_repeating_or_dropping_rows(self):
        rows = [{"encoded": {"input_ids": [1] * (i % 11 + 1)}} for i in range(16000)]
        orders = []
        for epoch in range(3):
            batches = w.make_length_batches(rows, epoch)
            self.assertEqual(len(batches), 8000)
            self.assertTrue(all(len(b) == 2 for b in batches))
            flat = [i for batch in batches for i in batch]
            self.assertEqual(sorted(flat), list(range(16000)))
            self.assertTrue(all(sum(len(b) for b in batches[i:i + 8]) == 16 for i in range(0, 8000, 8)))
            orders.append(flat)
        self.assertNotEqual(orders[0], orders[1])
        self.assertEqual(w.make_length_batches(rows, 1), w.make_length_batches(rows, 1))

    def test_rejects_overlength_and_missing_duplicate_or_false_eot(self):
        valid = {"input_ids": [1, 8, w.EOT, 10], "attention_mask": [1] * 4,
                 "labels": [-100, 8, w.EOT, -100]}
        w.validate_encoded(valid)
        variants = [dict(valid, labels=[-100, 8, 9, -100]),
                    dict(valid, labels=[-100, w.EOT, w.EOT, -100]),
                    dict(valid, labels=[1, 8, w.EOT, -100]),
                    {"input_ids": [1] * 2048 + [w.EOT], "attention_mask": [1] * 2049,
                     "labels": [-100] * 2048 + [w.EOT]}]
        for invalid in variants:
            with self.subTest(invalid=invalid["labels"][:3]):
                with self.assertRaises(ValueError):
                    w.validate_encoded(invalid)

    def test_duplicate_target_keys_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            w.strict_json('{"steps": [], "steps": [1]}')

    def test_untrusted_helper_rejected_before_import(self):
        self.assertEqual(w.TOKENIZER_HELPER_SHA256,
                         "9b1287f495e30b85085c6d8c23b2fc273e38fefbf1e730d19b0d95a9d8950a3c")
        with tempfile.TemporaryDirectory() as directory:
            helper = Path(directory) / "untrusted.py"
            helper.write_text("raise RuntimeError('this must never execute')\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "tokenizer helper SHA256"):
                w.load_helper(helper)

    def test_metrics_count_retries_exposures_unique_and_wall_separately(self):
        state = {"step": 2, "rows_done": 32, "supervised_tokens": 72, "nonpadding_tokens": 100,
                 "loss_sum": 6, "total_retries": 3, "unique_ids": {"a", "b"}, "unique_cases": {"case"},
                 "exposures_by_mode": Counter({"worked_solution": 32}),
                 "exposures_by_grade": Counter({"5": 32}), "exposures_by_family": Counter({"family": 32})}
        metrics = w.snapshot_metrics(state, [1] * 16000, 10, 18012)
        self.assertEqual(metrics["training_wall_seconds"], 18002)
        self.assertEqual(metrics["deadline_boundary_overrun_seconds"], 2)
        self.assertEqual(metrics["total_retries"], 3)
        self.assertEqual(metrics["unique_examples"], 2)
        self.assertEqual(metrics["rows_done"], 32)
        self.assertEqual(metrics["mean_loss"], 3)
        self.assertEqual(metrics["completed_view_epochs"], 0.002)
        json.dumps(metrics)

    def test_base_cache_rejects_wrong_model_contract_or_output_hash(self):
        fixtures = [{"id": f"f{i}", "grade": 1, "mode": "answer", "userproblem": f"P{i}"} for i in range(28)]
        contract, contract_sha = w.eval_contract(fixtures, Tokenizer())
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            self.assertIsNone(w.cached_base(out, contract, contract_sha))
            rows = [{"fixture_id": r["id"], "stage": "base_before_training", "contract_sha256": contract_sha,
                     "max_new_tokens": 1024, "timed_out": False,
                     "prompt_token_sha256": contract["prompt_token_sha256"][r["id"]]} for r in fixtures]
            w.atomic_bytes(out / "base_generations.jsonl", "".join(w.canonical(r) + "\n" for r in rows).encode())
            provenance = {"model": w.MODEL, "revision": w.REVISION, "fixture_sha256": w.FIXTURES_SHA256,
                          "system_sha256": w.SYSTEM_SHA256, "contract_sha256": contract_sha,
                          "base_untrained": True, "adapter_loaded": False, "max_new_tokens": 1024,
                          "output_sha256": w.sha_file(out / "base_generations.jsonl")}
            w.atomic_json(out / "base_generation_provenance.json", provenance)
            self.assertEqual(len(w.cached_base(out, contract, contract_sha)), 28)
            with self.assertRaisesRegex(ValueError, "provenance"):
                w.cached_base(out, contract, "wrong-contract")
            w.atomic_json(out / "base_generation_provenance.json", dict(provenance, model="other"))
            with self.assertRaisesRegex(ValueError, "provenance"):
                w.cached_base(out, contract, contract_sha)
            w.atomic_json(out / "base_generation_provenance.json", provenance)
            with (out / "base_generations.jsonl").open("ab") as stream:
                stream.write(b"\n")
            with self.assertRaisesRegex(ValueError, "provenance"):
                w.cached_base(out, contract, contract_sha)

    def test_atomic_generation_contains_recovery_state_and_hash_bound_pointer(self):
        class Saver:
            def save_pretrained(self, path, **kwargs):
                (path / "stub.json").write_text("{}", encoding="utf-8")

            def state_dict(self):
                return {"x": 1}

        def save(value, path):
            with path.open("wb") as stream:
                pickle.dump(value, stream)

        fake_torch = SimpleNamespace(save=save, get_rng_state=lambda: [1, 2],
                                     cuda=SimpleNamespace(get_rng_state_all=lambda: [[3, 4]]))
        with tempfile.TemporaryDirectory() as directory, patch.dict("sys.modules", {"torch": fake_torch}):
            out = Path(directory)
            w.append_jsonl(out / "successful_ids.jsonl", [{"step": 300, "sample_id": "stub"}])
            metrics = {"step": 300, "rows_done": 4800, "training_wall_seconds": 912, "last_lr": 5e-5}
            cursor = {"epoch": 0, "next_microbatch": 2400, "microbatches_per_epoch": 8000}
            path = w.save_generation(Saver(), Saver(), Saver(), Saver(), out, {"fresh_base": True}, metrics, cursor, {})
            manifest = json.loads((path / "generation_manifest.json").read_text())
            pointer = json.loads((out / "latest.json").read_text())
            self.assertTrue(manifest["complete"])
            self.assertEqual(manifest["consumed_train_seconds"], 912)
            self.assertEqual(manifest["cursor"], cursor)
            self.assertEqual(pointer["manifest_sha256"], w.sha_file(path / "generation_manifest.json"))
            for name, sha in manifest["files"].items():
                self.assertEqual(w.sha_file(path / name), sha)
            recovery = pickle.loads((path / "resume_state.pt").read_bytes())
            self.assertFalse(recovery["automatic_resume_implemented"])
            self.assertEqual(recovery["consumed_train_seconds"], 912)
            self.assertIn("optimizer", recovery)
            self.assertIn("torch_cuda_rng", recovery)
            self.assertEqual(w.save_generation(Saver(), Saver(), Saver(), Saver(), out, {}, metrics, cursor, {}), path)
            w.export_adapter(path, out)
            import zipfile
            with zipfile.ZipFile(out / "adapter_export.zip") as archive:
                self.assertNotIn("resume_state.pt", archive.namelist())
                self.assertIn("generation_manifest.json", archive.namelist())


if __name__ == "__main__":
    unittest.main()
