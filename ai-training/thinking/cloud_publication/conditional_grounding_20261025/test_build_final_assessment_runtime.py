"""Offline fake-file regression test; does not create sealed fixtures or model data."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("assessment_under_test", HERE / "build_final_assessment_runtime.py")
ASSESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ASSESS)
POLICY_SPEC = importlib.util.spec_from_file_location("policy_under_test", HERE / "recovery_policy_v2.py")
POLICY = importlib.util.module_from_spec(POLICY_SPEC)
POLICY_SPEC.loader.exec_module(POLICY)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_fake_completed_base_after_100():
    with tempfile.TemporaryDirectory(prefix="assessment_fake_") as temporary:
        root = Path(temporary)
        shutil.copyfile(HERE / "recovery_policy_v2.py", root / "recovery_policy_v2.py")
        training = root / "training"
        step, ids = 100, [f"devfake_{i:02d}" for i in range(30)]
        baseline_path = root / "baseline_semantic_review_frozen.json"
        write_json(baseline_path, {
            "judgments_fixed_before_adapter_outputs_read": True,
            "human_review_claimed": False,
            "records": [{"fixture_id": fid, "grade": i % 5 + 1, "mode": "answer",
                         "base_pass": True, "base_hint_leak": False} for i, fid in enumerate(ids)],
        })
        gated_generation = training / "generation_step_000100_rows_00000016"
        write_json(gated_generation / "generation_manifest.json", {"complete": True, "step": 100})
        bindings = {
            "dev_sha256": "1" * 64, "contract_sha256": "2" * 64,
            "source_plan_sha256": "3" * 64, "base_output_sha256": "4" * 64,
            "adapter_output_sha256": "5" * 64, "generation_manifest_sha256": sha(gated_generation / "generation_manifest.json"),
            "fixture_ids": ids, "final_stage": True,
        }
        decisions = [{"fixture_id": fid, "grade": i % 5 + 1, "mode": "answer",
                      "base_pass": True, "adapter_pass": False,
                      "base_hint_leak": False, "adapter_hint_leak": False,
                      "critical_new_error": False} for i, fid in enumerate(ids)]
        gate = {**bindings, "step": step, "decision": "STOP",
                "all_actual_outputs_reviewed": True, "human_review_claimed": False,
                "decisions": decisions}
        write_json(training / f"gate_step_{step:06d}.json", gate)
        derived = POLICY.summarize_decisions(decisions)
        eval_dir = training / f"eval_step_{step:06d}"
        write_json(eval_dir / "eval_bindings.json", bindings)
        # Root utility summary intentionally has no gate_sha256.
        write_json(training / f"gate_step_{step:06d}_summary.json", {
            "schema": "MathVisionKid.bound_gate_summary.v1", "step": step,
            "decision": "STOP", "summary": derived, "bindings": bindings,
            "baseline_review_sha256": sha(baseline_path), "decisions_sha256": "7" * 64,
            "bound_checkpoint": gated_generation.name,
            "production_approved": False,
        })
        # Worker summary lives in eval_step_... and DOES carry gate_sha256.
        write_json(eval_dir / "gate_summary.json", {
            "summary": derived, "decision": "STOP",
            "gate_sha256": sha(training / f"gate_step_{step:06d}.json"),
            "bindings": bindings, "selected_best": {"kind": "untrained_base"},
        })

        (root / "recovery_worker_v5.py").write_text("# fake pinned worker bytes\n", encoding="utf-8")
        (root / "native_backend_v3.py").write_text("# fake pinned backend bytes\n", encoding="utf-8")
        (training / "generation_step_000001_rows_00000016").mkdir(parents=True)
        parent_manifest = training / "generation_step_000001_rows_00000016" / "generation_manifest.json"
        write_json(parent_manifest, {"complete": True})
        migration = {
            "schema": "MathVisionKid.explicit_memory_resume_migration.v1",
            "parent_checkpoint_generation": "generation_step_000001_rows_00000016",
            "parent_generation_manifest_sha256": sha(parent_manifest),
            "parent_checkpoint_archive_sha256": "8" * 64,
            "resumed_worker_sha256": sha(root / "recovery_worker_v5.py"),
            "resumed_backend_sha256": sha(root / "native_backend_v3.py"),
            "actual_weight_updates_in_lost_tail": 5,
            "physical_extra_exposures_in_failed_attempt_not_claimed_unique": 80,
            "targets_or_source_changed": False,
        }
        migration_path = root / "memory_resume_migration.json"
        write_json(migration_path, migration)
        code_proofs = {name: {"sha256": sha(root / name), "fresh_raw_readback_verified": True}
                       for name in ("memory_resume_migration.json", "recovery_worker_v5.py", "native_backend_v3.py")}
        active_proof = {
            "files": code_proofs,
            "parent_checkpoint": {"sha256": "8" * 64, "fresh_raw_readback_verified": True},
        }
        active_path = root / "active_memory_code_raw_verified.json"
        write_json(active_path, active_proof)
        # Captured receipt wrapper's actual keys: code_proofs,
        # parent_checkpoint_raw_reverified, and active_code_proof.
        captured = {
            "code_proofs": code_proofs,
            "parent_checkpoint_raw_reverified": {"sha256": "8" * 64, "fresh_raw_readback_verified": True},
            "active_code_proof": {"sha256": sha(active_path), "fresh_raw_readback_verified": True},
        }
        write_json(root / "memory_resume_receipt.json", {
            "result": {"outputs": [{"output_type": "stream", "text": json.dumps(captured)}]},
        })
        write_json(training / "actual_memory_resume_binding.json", {
            "parent_manifest_sha256": sha(parent_manifest),
            "worker_sha256": sha(root / "recovery_worker_v5.py"),
            "backend_sha256": sha(root / "native_backend_v3.py"), "worker_alive": True,
        })
        best = {"kind": "untrained_base", "model": ASSESS.PINNED_MODEL,
                "revision": ASSESS.PINNED_REVISION, "production_approval": False}
        write_json(training / "best.json", best)
        config = {"model": ASSESS.PINNED_MODEL, "revision": ASSESS.PINNED_REVISION,
                  "source_rows": 16000, "source_cases": 4000, "derived_view_rows": 16,
                  "explicit_memory_resume_migration_sha256": sha(migration_path),
                  "whole_corpus_training_claimed": False, "backend": "native Transformers/PEFT/bitsandbytes"}
        write_json(training / "run_config.json", config)
        write_json(training / "progress.json", {"state": "COMPLETE", "step": 100,
                                                   "rows_done": 16, "supervised_tokens": 123})
        write_json(training / "run_complete.json", {
            "complete": True, "best": best, "production_approval": False,
            "whole_corpus_training_claimed": False, "metrics": {"step": 100, "supervised_tokens": 123},
            "unique_examples": 16, "source_view_rows": 16000, "derived_view_rows": 16,
            "derived_view_epochs": 1.0, "training_seconds": 88.0,
        })
        report = ASSESS.build_assessment(root)
        assert report["locked_final_evaluation"]["status"] == "NOT_RUN_UNTOUCHED_SEALED_SET"
        assert report["selected_artifact"]["kind"] == "untrained_base"
        assert report["memory_resume"]["lost_tail_not_committed"] == {
            "weight_updates": 5, "extra_exposures_not_unique_training_examples": 80,
            "counted_in_final_successful_update_count": False,
            "counted_in_final_unique_examples": False,
        }
        assert report["memory_resume"]["active_memory_proof_map_key"] == "files"
        assert report["memory_resume"]["captured_memory_resume_receipt_sha256"]
        assert len(report["development_gates"]) == 1
        gate_report = report["development_gates"][0]
        assert gate_report["candidate_eligible"] is False
        assert len(gate_report["root_review_decisions"]) == 30
        assert gate_report["root_utility_summary_sha256"]
        assert gate_report["worker_evaldir_summary_sha256"]
        assert report["training_source_and_scope"]["successful_optimizer_updates"] == 100
        assert report["training_source_and_scope"]["successful_unique_training_examples"] == 16
        assert not (root / "native_locked15.jsonl").exists()


if __name__ == "__main__":
    run_fake_completed_base_after_100()
    print("fake completed-base-after-step-100 assessment test passed; no sealed fixture used")
