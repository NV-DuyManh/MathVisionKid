"""CPU-only final-evaluation contract tests; no inference, GPU or network."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import recovery_policy_v2 as policy
import recovery_worker_v3 as R
import final_evaluation_worker_v2 as F


class FinalEvaluationWorkerV2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="final_eval_v2_cpu_")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, path, value):
        F.atomic(path, value)

    def write_rows(self, path, rows):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(F.canonical(row) + "\n" for row in rows), encoding="utf-8")

    def test_owner_binding_overrides_only_frozen_fixture_hashes(self):
        base = {"hard_deadline_unix": 9000, "dev_sha256": "old-dev", "locked_test_sha256": "old-locked",
                "authorization": "owner", "reserve_seconds": 1800}
        base_path = self.root / "owner_run_scope.json"
        self.write(base_path, base)
        binding = {"original_scope_sha256": F.sha(base_path), "dev_sha256": "a" * 64,
                   "locked_test_sha256": "b" * 64, "repair_reason": "bind frozen fixture bytes"}
        self.write(self.root / "owner_scope_binding_v2.json", binding)
        loaded = R.load_scope(self.root)
        self.assertEqual(loaded["hard_deadline_unix"], 9000)
        self.assertEqual(loaded["authorization"], "owner")
        self.assertEqual(loaded["dev_sha256"], "a" * 64)
        self.assertEqual(loaded["locked_test_sha256"], "b" * 64)
        binding["hard_deadline_unix"] = 1
        self.write(self.root / "owner_scope_binding_v2.json", binding)
        with self.assertRaises(ValueError):
            R.load_scope(self.root)

    def test_final_input_pins_match_worker_source_plan_path(self):
        self.assertIn("derived_sampling_plan.json", F.UNCHANGED_INPUTS)
        self.assertNotIn("training/derived_sampling_plan.json", F.UNCHANGED_INPUTS)
        plan = self.root / "derived_sampling_plan.json"
        plan.write_text("frozen plan", encoding="utf-8")
        self.assertEqual(F.sha(plan), hashlib.sha256(b"frozen plan").hexdigest())

    def test_fewshot_capacity_and_active_contract_are_persisted(self):
        self.assertEqual(F.model_sequence_limit({"worked_solution"}), 4096)
        self.assertEqual(F.model_sequence_limit(set()), 2048)
        contract = {"schema": "synthetic", "fixture_sha256": "a" * 64,
                    "fixture_ids": ["active-1"], "frozen_fixture_ids": ["active-1", "inactive-2"],
                    "prompt_token_limit": 3072, "prompt_token_sha256": {"active-1": "b" * 64}}
        csha = hashlib.sha256(F.canonical(contract).encode()).hexdigest()
        path = F.persist_fewshot_contract(self.root / "fewshot_selected", contract, csha)
        saved = F.read(path)
        self.assertEqual(saved["contract_sha256"], csha)
        self.assertEqual(saved["fixture_sha256"], "a" * 64)
        self.assertEqual(saved["fixture_ids"], ["active-1"])
        self.assertEqual(saved["frozen_fixture_ids"], ["active-1", "inactive-2"])
        with self.assertRaises(ValueError):
            F.persist_fewshot_contract(self.root / "other", contract, "0" * 64)

    def test_frozen_fixture_contract_and_sha(self):
        canonical_root = HERE
        shutil.copyfile(canonical_root / "locked_test_candidates.jsonl", self.root / "locked_test_candidates.jsonl")
        frozen_sha = F.sha(self.root / "locked_test_candidates.jsonl")
        self.assertEqual(frozen_sha, F.LOCKED_SHA)
        self.write(self.root / "locked_test_binding.json", {"fixture_sha256": frozen_sha, "count": 20,
                    "frozen_before_new_candidate_outputs": True})
        fixtures, got = F.verify_fixture_bundle(self.root, {"locked_test_sha256": frozen_sha})
        self.assertEqual(got, frozen_sha)
        self.assertEqual(len(fixtures), 20)
        self.assertTrue(all(x["not_training_data"] is True for x in fixtures))
        with self.assertRaises(ValueError):
            F.verify_fixture_bundle(self.root, {"locked_test_sha256": "0" * 64})

    def _selection_scaffold(self, trained):
        out = self.root / "training"
        eval0 = out / "eval_step_000000"
        eval100 = out / "eval_step_000100"
        out.mkdir()
        (self.root / "derived_sampling_plan.json").write_text("synthetic plan", encoding="utf-8")
        plan_sha = F.sha(self.root / "derived_sampling_plan.json")
        for name in ("recovery_worker_v3.py", "recovery_policy_v2.py", "behavior_renderer.py", "inference_contract.py"):
            shutil.copyfile(HERE / name, self.root / name)
        fixtures = []
        modes = ["answer", "hint_no_answer", "missing_or_contradictory_info", "student_error"]
        for i in range(30):
            fixtures.append({"id": f"dev-{i:02}", "grade": (i % 5) + 1, "mode": modes[i % 4]})
        contract = {"fixture_sha256": "d" * 64, "fixture_ids": [x["id"] for x in fixtures],
                    "prompt_token_sha256": {x["id"]: "c" * 64 for x in fixtures},
                    "decoding": {"max_new_tokens": 1024}}
        csha = hashlib.sha256(F.canonical(contract).encode()).hexdigest()
        self.write(out / "evaluation_contract.json", contract)

        def output(fixture, stage):
            return {"fixture_id": fixture["id"], "grade": fixture["grade"], "mode": fixture["mode"],
                    "stage": stage, "contract_sha256": csha, "prompt_token_sha256": "c" * 64,
                    "max_new_tokens": 1024, "output": "cpu synthetic output",
                    "seed": F.expected_seed(fixture["id"]), "ended_eos": True,
                    "possibly_truncated": False, "timed_out": False}

        base_rows = [output(f, "base_before_training") for f in fixtures]
        candidate_rows = [output(f, "adapter_after_training") for f in fixtures]
        self.write_rows(eval0 / "base_generations.jsonl", base_rows)
        base_binding = {"dev_sha256": "d" * 64, "contract_sha256": csha,
                        "source_plan_sha256": plan_sha,
                        "base_output_sha256": F.sha(eval0 / "base_generations.jsonl"),
                        "fixture_ids": [x["id"] for x in fixtures]}
        self.write(eval0 / "eval_bindings.json", base_binding)
        baseline = {"kind": "untrained_base", "model": F.MODEL, "revision": F.REVISION,
                    "validation_output_sha256": base_binding["base_output_sha256"], "production_approval": False}
        decisions = []
        for i, fixture in enumerate(fixtures):
            base_pass = not (fixture["mode"] == "answer" and i == 0)
            decisions.append({"fixture_id": fixture["id"], "grade": fixture["grade"], "mode": fixture["mode"],
                              "base_pass": base_pass, "adapter_pass": True if trained else base_pass,
                              "base_hint_leak": False, "adapter_hint_leak": False, "critical_new_error": False})
        generation = out / "generation_step_000100_rows_00001600"
        generation.mkdir()
        (generation / "adapter.bin").write_bytes(b"synthetic adapter weights")
        self.write(generation / "generation_manifest.json", {"complete": True, "step": 100,
                    "files": {"adapter.bin": F.sha(generation / "adapter.bin")},
                    "file_bytes": {"adapter.bin": (generation / "adapter.bin").stat().st_size}})
        manifest_sha = F.sha(generation / "generation_manifest.json")
        self.write_rows(eval100 / "adapter_generations.jsonl", candidate_rows)
        bindings = {**base_binding, "generation_manifest_sha256": manifest_sha,
                    "adapter_output_sha256": F.sha(eval100 / "adapter_generations.jsonl")}
        self.write(eval100 / "eval_bindings.json", bindings)
        gate = {**bindings, "step": 100, "all_actual_outputs_reviewed": True,
                "human_review_claimed": False, "decision": "CONTINUE_IMPROVED" if trained else "STOP",
                "decisions": decisions}
        gate_path = out / "gate_step_000100.json"
        self.write(gate_path, gate)
        self.write(out / "base_review_profile.json", {"base_output_sha256": base_binding["base_output_sha256"],
                    "dev_sha256": "d" * 64, "profile": R.baseline_profile(decisions)})
        candidate = {"kind": "trained_adapter", "generation": generation.name,
                     "manifest_sha256": manifest_sha, "gate_file": gate_path.name,
                     "gate_sha256": F.sha(gate_path), "step": 100, "bindings": bindings,
                     "production_approval": False}
        best = R.choose_best(baseline, policy.summarize_decisions(decisions), candidate, baseline)
        if not trained:
            # In the base-winner case every adapter decision equals baseline;
            # make best the exact baseline alias with the same output bytes.
            best = {**baseline, "selection_key": list(policy.selection_key(policy.summarize_decisions(decisions), "base")),
                    "semantic_review_pending": False}
        selected = {"kind": best["kind"], "selection_evidence": best}
        if best["kind"] == "trained_adapter":
            archive = out / "selected_adapter_export.zip"
            archive.write_bytes(b"synthetic export")
            selected.update(generation=generation.name, path=archive.name,
                            sha256=F.sha(archive), bytes=archive.stat().st_size)
        else:
            selected.update(model=F.MODEL, revision=F.REVISION, adapter=None)
        self.write(out / "best.json", best)
        cfg = {"model": F.MODEL, "revision": F.REVISION, "dev_sha256": "d" * 64,
               "hard_deadline_unix": 9999999999, "contract_sha256": csha,
               "source_plan_sha256": plan_sha,
               "worker_sha256": F.sha(self.root / "recovery_worker_v3.py"),
               "policy_sha256": F.sha(self.root / "recovery_policy_v2.py"),
               "renderer_sha256": F.sha(self.root / "behavior_renderer.py")}
        self.write(out / "run_config.json", cfg)
        complete = {"complete": True, "budget_satisfied": True,
                    "hard_deadline_unix": cfg["hard_deadline_unix"], "best": best,
                    "selected_artifact": selected}
        self.write(out / "run_complete.json", complete)
        return fixtures, cfg, complete

    def test_selection_replay_accepts_base_alias_and_dev_review_only(self):
        fixtures, _, _ = self._selection_scaffold(False)
        scope = {"hard_deadline_unix": 9999999999}
        proof = F.verify_selection(self.root, scope, fixtures, "d" * 64)
        self.assertEqual(proof["selected_kind"], "untrained_base")
        self.assertEqual(proof["best"]["validation_output_sha256"], proof["baseline_output_sha256"])

    def test_selection_replay_accepts_only_eligible_reviewed_adapter(self):
        fixtures, _, _ = self._selection_scaffold(True)
        proof = F.verify_selection(self.root, {"hard_deadline_unix": 9999999999}, fixtures, "d" * 64)
        self.assertEqual(proof["selected_kind"], "trained_adapter")
        self.assertEqual(proof["best"]["step"], 100)

    def test_mode_context_selection_replays_group_eligibility_and_module_hashes(self):
        shutil.copyfile(HERE / "fewshot_selection_policy.json", self.root / "fewshot_selection_policy.json")
        shutil.copyfile(HERE / "source_example_bank.json", self.root / "source_example_bank.json")
        shutil.copyfile(HERE / "inference_contract.py", self.root / "inference_contract.py")
        shutil.copyfile(HERE / "fewshot_contract.py", self.root / "fewshot_contract.py")
        bank_path = self.root / "source_example_bank.json"
        bank = F.read(bank_path)
        for name, metadata in bank["source_files"].items():
            if isinstance(metadata, dict) and "sha256" in metadata:
                shutil.copyfile(HERE / name, self.root / name)
        policy_doc = F.read(self.root / "fewshot_selection_policy.json")
        dev_sha = policy_doc["development_fixture_sha256"]
        baseline_sha = policy_doc["baseline_output_sha256"]
        dev = [{"id": f"d{i:02}", "grade": (i % 5) + 1,
                "mode": "hint_no_answer" if i < 5 else ("answer", "student_error", "missing_or_contradictory_info")[(i - 5) % 3]}
               for i in range(30)]
        out = self.root / "fewshot_dev"
        out.mkdir()
        contract = {"fixture_sha256": dev_sha, "example_bank_sha256": F.sha(bank_path),
                    "fixture_ids": [f["id"] for f in dev]}
        contract_sha = hashlib.sha256(F.canonical(contract).encode()).hexdigest()
        self.write(out / "contract.json", contract)
        outputs = out / "generations.jsonl"
        outputs.write_text("synthetic bytes\n", encoding="utf-8")
        output_sha = F.sha(outputs)
        self.write(out / "complete.json", {"complete": True, "fixture_sha256": dev_sha,
                    "contract_sha256": contract_sha, "example_bank_sha256": F.sha(bank_path),
                    "outputs_sha256": output_sha})
        decisions = []
        for i, fixture in enumerate(dev):
            decisions.append({"fixture_id": fixture["id"],
                              "base_pass": i != 5, "fewshot_pass": True,
                              "base_hint_leak": False, "fewshot_hint_leak": False,
                              "critical_new_error": False,
                              "base_reason": "synthetic", "fewshot_reason": "synthetic"})
        review = {"all_actual_fields_read": True, "human_review_claimed": False,
                  "base_output_sha256": baseline_sha, "fewshot_output_sha256": output_sha,
                  "decisions": decisions}
        review_path = self.root / "root_fewshot_semantic_review.json"
        self.write(review_path, review)
        selection = {
            "schema": "MathVisionKid.mode_context_selection.v1", "base_kind": "untrained_base",
            "dev_fixture_sha256": dev_sha, "baseline_output_sha256": baseline_sha,
            "fewshot_output_sha256": output_sha, "fewshot_contract_sha256": contract_sha,
            "bank_sha256": F.sha(bank_path),
            "inference_module_sha256": {"inference_contract": F.sha(HERE / "inference_contract.py"),
                                         "fewshot_contract": F.sha(HERE / "fewshot_contract.py")},
            "eligible_by_model_mode": {"worked_solution": True, "hint_level_1": False,
                                       "hint_level_2": False, "hint_level_3": False},
            "mode_selection": {"worked_solution": "fewshot_contract", "hint_level_1": "inference_contract",
                               "hint_level_2": "inference_contract", "hint_level_3": "inference_contract"},
            "root_semantic_review_sha256": F.sha(review_path),
            "selection_policy_sha256": F.sha(self.root / "fewshot_selection_policy.json"),
        }
        self.write(self.root / "fewshot_selection.json", selection)
        proof = F.verify_fewshot_selection(self.root, dev, dev_sha, baseline_sha)
        self.assertEqual(proof["mode_selection"]["worked_solution"], "fewshot_contract")
        self.assertTrue(proof["eligible_by_model_mode"]["worked_solution"])
        selection["eligible_by_model_mode"]["worked_solution"] = False
        self.write(self.root / "fewshot_selection.json", selection)
        with self.assertRaises(ValueError):
            F.verify_fewshot_selection(self.root, dev, dev_sha, baseline_sha)


if __name__ == "__main__":
    unittest.main()
