"""Synthetic completed-run test; no real corpus/model/sealed data is used."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

HERE = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location("assessment_20261026_test", HERE / "build_final_assessment_20261026.py")
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def fake_completed_base(root: Path):
    shutil.copyfile(HERE / "recovery_worker_20261026.py", root / "recovery_worker_20261026.py")
    shutil.copyfile(HERE / "recovery_policy_20261026.py", root / "recovery_policy_20261026.py")
    training = root / "training"
    ids = [f"devfake_{i:02d}" for i in range(30)]
    fixtures = [{"id": fid, "grade": i % 5 + 1, "mode": "answer", "userproblem": "synthetic only"}
                for i, fid in enumerate(ids)]
    fixture_path = root / "new_validation_candidates.jsonl"
    write_jsonl(fixture_path, fixtures)
    contract = {"prompt_token_sha256": {fid: "a" * 64 for fid in ids},
                "decoding": {"max_new_tokens": 64}}
    contract_path = training / "evaluation_contract.json"
    write_json(contract_path, contract)
    raw_contract_sha = sha(contract_path)
    contract_sha = canonical_sha(contract)
    assert raw_contract_sha != contract_sha
    source_plan_sha = "b" * 64
    base_rows, adapter_rows = [], []
    for fixture in fixtures:
        base_rows.append({"fixture_id": fixture["id"], "grade": fixture["grade"], "mode": fixture["mode"],
                          "stage": "base_before_training", "contract_sha256": contract_sha,
                          "prompt_token_sha256": "a" * 64, "max_new_tokens": 64,
                          "output": "synthetic base response", "ended_eos": True,
                          "possibly_truncated": False, "timed_out": False})
        adapter_rows.append({"fixture_id": fixture["id"], "grade": fixture["grade"], "mode": fixture["mode"],
                             "stage": "adapter_after_training", "contract_sha256": contract_sha,
                             "prompt_token_sha256": "a" * 64, "max_new_tokens": 64,
                             "output": "synthetic candidate response", "ended_eos": True,
                             "possibly_truncated": False, "timed_out": False})
    base_path = training / "eval_step_000000" / "base_generations.jsonl"
    write_jsonl(base_path, base_rows)
    base_receipt = {"dev_sha256": sha(fixture_path), "contract_sha256": contract_sha,
                    "source_plan_sha256": source_plan_sha, "base_output_sha256": sha(base_path),
                    "fixture_ids": ids}
    write_json(training / "eval_step_000000" / "eval_bindings.json", base_receipt)
    baseline = {"fixture_raw_sha256": sha(fixture_path), "base_output_raw_sha256": sha(base_path),
                "contract_sha256": raw_contract_sha, "judgments_fixed_before_adapter_outputs_read": True,
                "human_review_claimed": False,
                "records": [{"fixture_id": f["id"], "grade": f["grade"], "mode": f["mode"],
                             "base_pass": True, "base_hint_leak": False,
                             "actual_output_sha256": hashlib.sha256(base_rows[i]["output"].encode()).hexdigest()}
                            for i, f in enumerate(fixtures)]}
    write_json(root / "baseline_semantic_review_frozen.json", baseline)

    step = 100
    generation = training / "generation_step_000100_rows_00000016"
    metrics = {"step": step, "rows_done": 16, "supervised_tokens": 123,
               "unique_examples": 16, "training_seconds": 88.0}
    write_json(generation / "metrics.json", metrics)
    write_json(generation / "run_config.json", {"fixture_only": True})
    members = {name: sha(generation / name) for name in ("metrics.json", "run_config.json")}
    manifest = {"schema": "MathVisionKid.quality_recovery_generation.v1", "complete": True,
                "step": step, "rows_done": 16, "files": members,
                "file_bytes": {name: (generation / name).stat().st_size for name in members}}
    manifest_path = generation / "generation_manifest.json"
    write_json(manifest_path, manifest)

    eval_dir = training / f"eval_step_{step:06d}"
    adapter_path = eval_dir / "adapter_generations.jsonl"
    write_jsonl(adapter_path, adapter_rows)
    bindings = {**base_receipt, "generation_manifest_sha256": sha(manifest_path),
                "final_stage": True, "adapter_output_sha256": sha(adapter_path)}
    write_json(eval_dir / "eval_bindings.json", bindings)
    decisions = [{"fixture_id": f["id"], "grade": f["grade"], "mode": f["mode"],
                  "base_pass": True, "adapter_pass": False,
                  "base_hint_leak": False, "adapter_hint_leak": False,
                  "critical_new_error": False} for f in fixtures]
    gate = {**bindings, "step": step, "decision": "STOP", "all_actual_outputs_reviewed": True,
            "human_review_claimed": False, "decisions": decisions}
    gate_path = training / f"gate_step_{step:06d}.json"
    write_json(gate_path, gate)
    policy_spec = importlib.util.spec_from_file_location("test_gate_policy", HERE / "recovery_policy_20261026.py")
    policy = importlib.util.module_from_spec(policy_spec)
    policy_spec.loader.exec_module(policy)
    summary = policy.summarize_decisions(decisions)
    write_json(training / f"gate_step_{step:06d}_summary.json", {
        "schema": "MathVisionKid.recovery_20261026.bound_gate_summary.v1", "step": step,
        "decision": "STOP", "summary": summary, "bindings": bindings,
        "baseline_review_sha256": sha(root / "baseline_semantic_review_frozen.json"),
        "decisions_sha256": "c" * 64, "bound_checkpoint": generation.name,
        "production_approved": False})
    write_json(eval_dir / "gate_summary.json", {
        "summary": summary, "decision": "STOP", "gate_sha256": sha(gate_path),
        "bindings": bindings, "selected_best": {"kind": "untrained_base", "production_approval": False}})

    # The valid root summary's suffix must not be counted as a second gate.
    best = {"kind": "untrained_base", "model": "Qwen/Qwen3-1.7B",
            "revision": "pinned-test-revision", "production_approval": False}
    write_json(training / "best.json", best)
    config = {"model": best["model"], "revision": best["revision"], "dev_sha256": sha(fixture_path),
              "source_view_sha256": "d" * 64, "source_manifest_sha256": "e" * 64,
              "source_plan_sha256": source_plan_sha, "contract_sha256": contract_sha,
              "source_rows": 16000, "source_cases": 4000,
              "derived_view_rows": 16, "fresh_base_required": True,
              "previous_adapters_loaded": False, "whole_corpus_training_claimed": False}
    write_json(training / "run_config.json", config)
    complete = {"complete": True, "best": best, "production_approval": False,
                "whole_corpus_training_claimed": False, "metrics": metrics,
                "unique_examples": 16, "source_view_rows": 16000, "derived_view_rows": 16,
                "derived_view_epochs": 1.0, "training_seconds": 88.0,
                "selected_artifact": {"kind": "untrained_base"}}
    write_json(training / "run_complete.json", complete)
    write_json(training / "progress.json", {"state": "COMPLETE", "step": step, "rows_done": 16,
                                               "unique_examples": 16, "training_started": True})
    write_json(root / "owner_run_scope.json", {"model": best["model"], "revision": best["revision"],
                                                 "hard_deadline_utc": "synthetic"})


class FinalAssessmentTests(unittest.TestCase):
    def test_completed_base_with_exact_30_decision_gate_and_summary_glob(self):
        with tempfile.TemporaryDirectory(prefix="recovery_assessment_fake_") as td:
            root = Path(td)
            fake_completed_base(root)
            report = A.build_assessment(root)
            self.assertEqual(len(report["development_gates"]), 1)
            self.assertEqual(report["development_gates"][0]["step"], 100)
            self.assertFalse(report["development_gates"][0]["candidate_eligible"])
            self.assertEqual(report["training_source_and_scope"]["successful_unique_training_examples"], 16)
            self.assertEqual(report["training_source_and_scope"]["successful_supervised_tokens"], 123)
            self.assertEqual(report["training_source_and_scope"]["derived_view_epochs_completed"], 1.0)
            self.assertEqual(report["selected_artifact"]["kind"], "untrained_base")
            self.assertEqual(report["sealed_final_evaluation"]["status"], "NOT_RUN_UNTOUCHED_SEALED_SET")
            self.assertFalse(report["sealed_final_evaluation"]["sealed_fixture_contents_read"])
            self.assertFalse((root / "native15.jsonl").exists())

    def test_rejects_baseline_flag_drift_in_completed_gate(self):
        with tempfile.TemporaryDirectory(prefix="recovery_assessment_drift_") as td:
            root = Path(td)
            fake_completed_base(root)
            gate_path = root / "training" / "gate_step_000100.json"
            gate = json.loads(gate_path.read_text(encoding="utf-8"))
            gate["decisions"][0]["base_pass"] = False
            write_json(gate_path, gate)
            with self.assertRaisesRegex(ValueError, "Frozen baseline flags changed"):
                A.build_assessment(root)

    def test_completed_final_eval_requires_hash_bound_root_review_for_acceptance(self):
        with tempfile.TemporaryDirectory(prefix="recovery_final_review_") as td:
            root = Path(td)
            final = root / "final_eval"
            final.mkdir()
            write_json(final / "attempt_started.json", {"attempt": "synthetic"})
            base_text, candidate_text = "synthetic final base", "synthetic final candidate"
            pair = {"fixture_id": "sealed_synthetic_01", "grade": 2, "mode": "answer",
                    "base": {"output": base_text}, "candidate": {"output": candidate_text}}
            paired_path = final / "paired_generations.jsonl"
            base_path = final / "base_generations.jsonl"
            candidate_path = final / "adapter_generations.jsonl"
            write_jsonl(paired_path, [pair])
            write_jsonl(base_path, [{"output": base_text}])
            write_jsonl(candidate_path, [{"output": candidate_text}])
            complete = {"complete": True, "production_approval": False,
                        "selected_generation_manifest_sha256": "a" * 64,
                        "paired_outputs_sha256": sha(paired_path), "base_outputs_sha256": sha(base_path),
                        "adapter_outputs_sha256": sha(candidate_path), "contract_sha256": "b" * 64,
                        "fixture_ids": [pair["fixture_id"]]}
            complete_path = final / "complete.json"
            write_json(complete_path, complete)
            best = {"kind": "trained_adapter", "manifest_sha256": "a" * 64}
            no_review = A.validate_final_evaluation(root, best, {"candidate_eligible": True})
            self.assertEqual(no_review["status"], "COMPLETED_AWAITING_ROOT_SEMANTIC_REVIEW")
            self.assertFalse(no_review["quality_accepted"])

            decision = {"fixture_id": pair["fixture_id"], "grade": 2, "mode": "answer",
                        "base_pass": True, "candidate_pass": True, "base_hint_leak": False,
                        "candidate_hint_leak": False, "critical_candidate_error": False,
                        "base_reason": "synthetic reason", "candidate_reason": "synthetic reason",
                        "base_output_sha256": hashlib.sha256(base_text.encode()).hexdigest(),
                        "candidate_output_sha256": hashlib.sha256(candidate_text.encode()).hexdigest()}
            review = {"complete_sha256": sha(complete_path),
                      "paired_outputs_sha256": sha(paired_path), "base_outputs_sha256": sha(base_path),
                      "adapter_outputs_sha256": sha(candidate_path), "contract_sha256": complete["contract_sha256"],
                      "all_actual_outputs_reviewed": True, "human_review_claimed": False,
                      "decision": "ACCEPT_CANDIDATE", "decisions": [decision]}
            write_json(root / "root_final_semantic_review.json", review)
            accepted = A.validate_final_evaluation(root, best, {"candidate_eligible": True})
            self.assertEqual(accepted["status"], "COMPLETED_AND_ROOT_ACCEPTED")
            self.assertTrue(accepted["quality_accepted"])
            self.assertFalse(accepted["sealed_fixture_contents_read"])


if __name__ == "__main__":
    unittest.main()
