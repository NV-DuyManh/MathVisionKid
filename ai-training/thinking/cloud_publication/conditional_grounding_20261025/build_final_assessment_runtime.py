"""Build a hash-bound semantic assessment from completed cloud-run metadata.

CPU-only. This module never invents review decisions. If locked final evaluation
completed, it requires a separately authored root agent review bound to those
exact output bytes before writing training/final_semantic_assessment.json.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone

ROOT_FINAL_REVIEW = "root_final_semantic_review.json"
LOCKED_SHA256 = "0526ec69b5b1730376835c2961d32c79c187f6d1d0fe3057f2d98358b71674f7"
PINNED_MODEL = "Qwen/Qwen3-1.7B"
PINNED_REVISION = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
REVIEW_FLAGS = ("base_pass", "candidate_pass", "base_hint_leak", "candidate_hint_leak", "critical_candidate_error")
CONFIG_FIELDS = (
    "backend", "model", "revision", "source_view_sha256", "source_manifest_sha256",
    "source_plan_sha256", "source_cases", "source_rows", "derived_view_rows",
    "learning_rate", "warmup_updates", "lora_r", "lora_alpha", "target_modules",
    "microbatch", "effective_batch", "gradient_checkpointing", "max_sequence",
    "assistant_only_loss", "enable_thinking", "packing", "padding_free", "precision",
    "quantization", "gate_steps", "max_successful_updates", "max_derived_view_epochs",
    "whole_corpus_training_claimed", "hard_deadline_unix",
)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path):
    return json.loads(path.read_bytes())


def canonical_bytes(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def summarize_flags(records, left: str, right: str, left_leak: str, right_leak: str, critical: str):
    regressions = [r["fixture_id"] for r in records if r[left] and not r[right]]
    new_leaks = [r["fixture_id"] for r in records if r[right_leak] and not r[left_leak]]
    critical_ids = [r["fixture_id"] for r in records if r[critical]]
    return {
        "items_reviewed": len(records),
        "base_pass": sum(r[left] for r in records),
        "candidate_pass": sum(r[right] for r in records),
        "candidate_minus_base_pass": sum(r[right] for r in records) - sum(r[left] for r in records),
        "baseline_pass_regressions": regressions,
        "new_hint_leaks": new_leaks,
        "new_critical_errors": critical_ids,
        "by_mode": {
            mode: {
                "items": sum(r["mode"] == mode for r in records),
                "base_pass": sum(r[left] and r["mode"] == mode for r in records),
                "candidate_pass": sum(r[right] and r["mode"] == mode for r in records),
            }
            for mode in sorted({r["mode"] for r in records})
        },
    }


def baseline_summary(doc):
    records = doc.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("Frozen baseline review has no records")
    if doc.get("judgments_fixed_before_adapter_outputs_read") is not True or doc.get("human_review_claimed") is not False:
        raise ValueError("Frozen baseline review provenance is invalid")
    seen = set()
    for row in records:
        fid = row.get("fixture_id")
        if not isinstance(fid, str) or not fid or fid in seen or type(row.get("base_pass")) is not bool or type(row.get("base_hint_leak")) is not bool:
            raise ValueError("Frozen baseline review records are malformed")
        seen.add(fid)
    return {
        "fixture_count": len(records),
        "full_task_pass": sum(row["base_pass"] for row in records),
        "hint_leaks": sum(row["base_hint_leak"] for row in records),
        "by_mode": {
            mode: {"items": sum(r.get("mode") == mode for r in records),
                   "full_task_pass": sum(r["base_pass"] and r.get("mode") == mode for r in records),
                   "hint_leaks": sum(r["base_hint_leak"] and r.get("mode") == mode for r in records)}
            for mode in sorted({r.get("mode") for r in records})
        },
        "review_sha256": None,
        "review_method_claimed": "frozen root review; human_review_claimed=false",
        "root_review_decisions": records,
    }


def validate_development_gates(root: Path, policy):
    training = root / "training"
    gates = []
    for gate_path in sorted(training.glob("gate_step_*.json")):
        match = re.fullmatch(r"gate_step_([0-9]{6})\.json", gate_path.name)
        if not match:
            continue  # Exclude root utility's gate_step_NNNNNN_summary.json.
        step = int(match.group(1))
        root_summary_path = training / f"gate_step_{step:06d}_summary.json"
        eval_dir = training / f"eval_step_{step:06d}"
        binding_path = eval_dir / "eval_bindings.json"
        worker_summary_path = eval_dir / "gate_summary.json"
        if not root_summary_path.is_file() or not worker_summary_path.is_file() or not binding_path.is_file():
            raise ValueError(f"Incomplete gate/evaluation evidence at step {step}")
        gate = read_json(gate_path)
        root_summary = read_json(root_summary_path)
        worker_summary = read_json(worker_summary_path)
        bindings = read_json(binding_path)
        bound_generations = [p for p in training.glob("generation_step_*")
                             if (p / "generation_manifest.json").is_file()
                             and sha(p / "generation_manifest.json") == bindings.get("generation_manifest_sha256")]
        if len(bound_generations) != 1:
            raise ValueError(f"Gate does not bind exactly one checkpoint generation at step {step}")
        policy.validate_gate(gate, step, bindings)
        derived = policy.summarize_decisions(gate["decisions"])
        gate_sha = sha(gate_path)
        if (root_summary.get("schema") != "MathVisionKid.bound_gate_summary.v1"
                or root_summary.get("step") != step
                or root_summary.get("decision") != gate.get("decision")
                or root_summary.get("summary") != derived
                or root_summary.get("bindings") != bindings
                or root_summary.get("bound_checkpoint") != bound_generations[0].name
                or root_summary.get("baseline_review_sha256") != sha(root / "baseline_semantic_review_frozen.json")
                or not re.fullmatch(r"[0-9a-f]{64}", str(root_summary.get("decisions_sha256", "")))
                or root_summary.get("production_approved") is not False):
            raise ValueError(f"Root utility gate summary differs from actual gate evidence at step {step}")
        if (worker_summary.get("summary") != derived
                or worker_summary.get("decision") != gate.get("decision")
                or worker_summary.get("gate_sha256") != gate_sha
                or worker_summary.get("bindings") != bindings
                or not isinstance(worker_summary.get("selected_best"), dict)
                or worker_summary["selected_best"].get("production_approval") is True):
            raise ValueError(f"Worker evaldir summary differs from actual gate evidence at step {step}")
        if gate.get("human_review_claimed") is not False:
            raise ValueError(f"Gate has an unsupported human-review claim at step {step}")
        gates.append({
            "step": step,
            "decision": gate["decision"],
            "candidate_eligible": derived["candidate_eligible"],
            "summary": derived,
            "gate_sha256": gate_sha,
            "root_utility_summary_sha256": sha(root_summary_path),
            "worker_evaldir_summary_sha256": sha(worker_summary_path),
            "root_review_sha256": root_summary.get("decisions_sha256"),
            "root_review_decisions": gate["decisions"],
            "baseline_review_sha256": root_summary.get("baseline_review_sha256"),
            "bindings": bindings,
            "quality_regressions": {
                "baseline_pass_regressions": derived["baseline_pass_regressions"],
                "new_hint_leaks": derived["new_hint_leaks"],
                "new_critical_errors": derived["new_critical_errors"],
            },
            "root_review_claims_human_review": False,
        })
    return gates


def validate_resume_evidence(root: Path, config: dict):
    training = root / "training"
    migration_path = root / "memory_resume_migration.json"
    active_proof_path = root / "active_memory_code_raw_verified.json"
    actual_proof_path = training / "actual_memory_resume_binding.json"
    migration = read_json(migration_path)
    active_proof = read_json(active_proof_path)
    actual_proof = read_json(actual_proof_path)
    migration_sha = sha(migration_path)
    if config.get("explicit_memory_resume_migration_sha256") != migration_sha:
        raise ValueError("Run config does not bind the explicit memory-resume migration")
    # The staged runtime file uses {files: {name: DriveStore proof},
    # parent_checkpoint: DriveStore proof}; the captured stdout receipt uses
    # {code_proofs: ..., parent_checkpoint_raw_reverified: ..., active_code_proof: ...}.
    file_proofs = active_proof.get("files")
    proof_shape = "files"
    if not isinstance(file_proofs, dict):
        file_proofs = active_proof.get("code_proofs")
        proof_shape = "code_proofs"
    if not isinstance(file_proofs, dict):
        raise ValueError("Active memory proof lacks the staged files/code_proofs map")
    for filename in ("memory_resume_migration.json", "recovery_worker_v5.py", "native_backend_v3.py"):
        proof = file_proofs.get(filename)
        if not isinstance(proof, dict) or proof.get("sha256") != sha(root / filename) or proof.get("fresh_raw_readback_verified") is not True:
            raise ValueError("Active memory-code raw proof is missing or mismatched: " + filename)
    if migration.get("resumed_worker_sha256") != sha(root / "recovery_worker_v5.py") or migration.get("resumed_backend_sha256") != sha(root / "native_backend_v3.py"):
        raise ValueError("Memory-resume migration code hashes differ from active code")
    parent = migration.get("parent_checkpoint_generation")
    manifest_path = training / parent / "generation_manifest.json"
    if not isinstance(parent, str) or PurePosixPath(parent).name != parent or sha(manifest_path) != migration.get("parent_generation_manifest_sha256"):
        raise ValueError("Memory-resume parent checkpoint manifest proof mismatch")
    if actual_proof.get("parent_manifest_sha256") != migration.get("parent_generation_manifest_sha256"):
        raise ValueError("Actual memory-resume proof binds a different parent manifest")
    if actual_proof.get("worker_sha256") != migration.get("resumed_worker_sha256") or actual_proof.get("backend_sha256") != migration.get("resumed_backend_sha256"):
        raise ValueError("Actual memory-resume proof binds different active code")
    parent_drive_proof = active_proof.get("parent_checkpoint") or active_proof.get("parent_checkpoint_raw_reverified")
    if (not isinstance(parent_drive_proof, dict)
            or parent_drive_proof.get("sha256") != migration.get("parent_checkpoint_archive_sha256")
            or parent_drive_proof.get("fresh_raw_readback_verified") is not True):
        raise ValueError("Memory active proof lacks the fresh parent checkpoint raw-readback proof")
    receipt_path = root / "memory_resume_receipt.json"
    receipt_sha = None
    if receipt_path.is_file():
        capture = read_json(receipt_path)
        if isinstance(capture.get("result"), dict):
            text = "".join("".join(x.get("text", [])) if isinstance(x.get("text"), list)
                           else x.get("text", "") for x in capture["result"].get("outputs", [])
                           if x.get("output_type") == "stream")
            capture = json.loads(text)
        captured_active = capture.get("active_code_proof")
        if (not isinstance(captured_active, dict)
                or captured_active.get("sha256") != sha(active_proof_path)
                or captured_active.get("fresh_raw_readback_verified") is not True):
            raise ValueError("Captured memory receipt does not bind active proof bytes")
        if capture.get("parent_checkpoint_raw_reverified", {}).get("sha256") != migration.get("parent_checkpoint_archive_sha256"):
            raise ValueError("Captured memory receipt binds a different parent archive")
        receipt_sha = sha(receipt_path)
    lost_updates = migration.get("actual_weight_updates_in_lost_tail")
    lost_exposures = migration.get("physical_extra_exposures_in_failed_attempt_not_claimed_unique")
    if type(lost_updates) is not int or type(lost_exposures) is not int or lost_updates != 5 or lost_exposures != 80:
        raise ValueError("Memory migration lacks explicit lost-tail accounting")
    if migration.get("targets_or_source_changed") is not False:
        raise ValueError("Memory migration does not affirm unchanged source/targets")
    return {
        "migration_sha256": migration_sha,
        "migration_schema": migration.get("schema"),
        "parent_checkpoint_generation": parent,
        "parent_generation_manifest_sha256": migration["parent_generation_manifest_sha256"],
        "active_memory_code_proof_sha256": sha(active_proof_path),
        "active_memory_proof_map_key": proof_shape,
        "active_memory_parent_proof_sha256": parent_drive_proof.get("sha256"),
        "captured_memory_resume_receipt_sha256": receipt_sha,
        "actual_runtime_binding_proof_sha256": sha(actual_proof_path),
        "actual_runtime_binding_was_live_at_capture": actual_proof.get("worker_alive") is True,
        "lost_tail_not_committed": {
            "weight_updates": lost_updates,
            "extra_exposures_not_unique_training_examples": lost_exposures,
            "counted_in_final_successful_update_count": False,
            "counted_in_final_unique_examples": False,
        },
        "source_or_targets_changed": migration["targets_or_source_changed"],
        "production_approved": False,
    }


def read_final_review(root: Path, final_complete_path: Path, complete: dict):
    review_path = root / ROOT_FINAL_REVIEW
    if not review_path.is_file():
        raise FileNotFoundError(f"Completed final_eval requires {ROOT_FINAL_REVIEW}")
    review = read_json(review_path)
    complete_sha = sha(final_complete_path)
    paired_path = final_complete_path.parent / "paired_generations.jsonl"
    paired_sha = sha(paired_path)
    if complete.get("paired_outputs_sha256") != paired_sha:
        raise ValueError("Final completion paired-output SHA differs from actual bytes")
    for filename, key in (("base_generations.jsonl", "base_outputs_sha256"),
                          ("adapter_generations.jsonl", "adapter_outputs_sha256")):
        if sha(final_complete_path.parent / filename) != complete.get(key):
            raise ValueError("Final completion generation SHA differs: " + filename)
    if complete.get("locked_fixture_raw_sha256") != LOCKED_SHA256:
        raise ValueError("Final completion fixture SHA differs from the sealed native15 binding")
    if review.get("schema") != "MathVisionKid.conditional_native15_agent_semantic_review.v1":
        raise ValueError("Final review schema differs")
    if review.get("review_method") != "root_agent_ai_semantic_review" or review.get("human_review_claimed") is not False:
        raise ValueError("Final review must accurately identify agent review and not claim human review")
    for key, expected in (("complete_sha256", complete_sha),
                          ("paired_outputs_sha256", paired_sha),
                          ("contract_sha256", complete.get("contract_sha256")),
                          ("locked_fixture_sha256", LOCKED_SHA256)):
        if review.get(key) != expected:
            raise ValueError("Final review is not bound to current final output: " + key)
    if review.get("all_actual_outputs_reviewed") is not True:
        raise ValueError("Final review does not attest to reviewing all actual outputs")
    reviewer = review.get("reviewer")
    if not isinstance(reviewer, dict) or not all(isinstance(reviewer.get(k), str) and reviewer[k].strip() for k in ("label", "model")):
        raise ValueError("Final review must identify its agent/model accurately")
    if not isinstance(review.get("reviewed_at_utc"), str) or not review["reviewed_at_utc"].strip():
        raise ValueError("Final review must record its review timestamp")
    if review.get("decision") not in ("ACCEPT_CANDIDATE", "REJECT_CANDIDATE", "INCONCLUSIVE"):
        raise ValueError("Unsupported final semantic decision")
    pairs = [json.loads(line) for line in paired_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(pairs) != 15 or [row.get("fixture_id") for row in pairs] != complete.get("fixture_ids"):
        raise ValueError("Final paired outputs do not match completed fixture IDs")
    decisions = review.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != len(pairs):
        raise ValueError("Final semantic review must contain one decision per paired output")
    pair_by_id = {row["fixture_id"]: row for row in pairs}
    seen = set()
    clean = []
    for decision in decisions:
        fid = decision.get("fixture_id")
        if not isinstance(fid, str) or fid not in pair_by_id or fid in seen:
            raise ValueError("Final review has missing, duplicate, or unexpected fixture ID")
        seen.add(fid)
        pair = pair_by_id[fid]
        if (decision.get("grade"), decision.get("mode")) != (pair.get("grade"), pair.get("mode")):
            raise ValueError("Final review grade/mode differs from actual paired output")
        if any(type(decision.get(flag)) is not bool for flag in REVIEW_FLAGS):
            raise ValueError("Final review requires all explicit semantic flags")
        if not all(isinstance(decision.get(k), str) and decision[k].strip() for k in ("base_reason", "candidate_reason")):
            raise ValueError("Final review requires reasons for both actual outputs")
        if decision.get("base_output_sha256") != hashlib.sha256(pair["base"]["output"].encode("utf-8")).hexdigest():
            raise ValueError("Final review base-output hash differs")
        if decision.get("candidate_output_sha256") != hashlib.sha256(pair["candidate"]["output"].encode("utf-8")).hexdigest():
            raise ValueError("Final review candidate-output hash differs")
        if decision["mode"] != "hint_no_answer" and (decision["base_hint_leak"] or decision["candidate_hint_leak"]):
            raise ValueError("Hint-leak flags only apply to hint fixtures")
        clean.append(decision)
    if seen != set(complete.get("fixture_ids", [])):
        raise ValueError("Final review does not cover every completed fixture")
    return {
        "review_sha256": sha(review_path),
        "review_method": review["review_method"],
        "reviewer": reviewer,
        "reviewed_at_utc": review.get("reviewed_at_utc"),
        "decision": review["decision"],
        "all_actual_outputs_reviewed": True,
        "human_review_claimed": False,
        "output_bindings": {"complete_sha256": complete_sha, "paired_outputs_sha256": paired_sha,
                            "contract_sha256": complete["contract_sha256"], "locked_fixture_sha256": LOCKED_SHA256},
        "summary": summarize_flags(clean, "base_pass", "candidate_pass", "base_hint_leak", "candidate_hint_leak", "critical_candidate_error"),
        "decisions": clean,
        "production_approved": False,
    }


def atomic_write_no_overwrite(path: Path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_name(path.name + ".lock")
    temp = path.with_name(path.name + f".{os.getpid()}.pending")
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite {path}")
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.close(fd)
        payload = (json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
        with temp.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite {path}")
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()
        if lock.exists():
            lock.unlink()


def build_assessment(root: Path):
    training = root / "training"
    run_config_path = training / "run_config.json"
    run_complete_path = training / "run_complete.json"
    progress_path = training / "progress.json"
    best_path = training / "best.json"
    for path in (run_config_path, run_complete_path, progress_path, best_path):
        if not path.is_file():
            raise FileNotFoundError(f"Required completed-run metadata missing: {path.name}")
    config, complete, progress, best = map(read_json, (run_config_path, run_complete_path, progress_path, best_path))
    if config.get("model") != PINNED_MODEL or config.get("revision") != PINNED_REVISION:
        raise ValueError("Completed run model/revision differs from the pinned source")
    if complete.get("complete") is not True or progress.get("state") != "COMPLETE":
        raise ValueError("Training run is not complete")
    if complete.get("best") != best or complete.get("production_approval") is not False:
        raise ValueError("Run completion and selected-best pointer disagree")
    if complete.get("whole_corpus_training_claimed") is not False:
        raise ValueError("Run completion makes an unsupported whole-corpus training claim")
    policy_path = root / "recovery_policy_v2.py"
    import importlib.util
    spec = importlib.util.spec_from_file_location("final_assessment_policy", policy_path)
    policy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(policy)
    baseline_path = root / "baseline_semantic_review_frozen.json"
    baseline = baseline_summary(read_json(baseline_path))
    baseline["review_sha256"] = sha(baseline_path)
    gates = validate_development_gates(root, policy)
    if not gates:
        raise ValueError("No hash-bound development gates found")
    best_kind = best.get("kind")
    selected_gate = None
    if best_kind == "trained_adapter":
        for item in gates:
            if item["step"] == best.get("step") and item["gate_sha256"] == best.get("gate_sha256"):
                selected_gate = item
                break
        if selected_gate is None or not selected_gate["candidate_eligible"]:
            raise ValueError("Selected adapter lacks an eligible, hash-matched development gate")
        artifact = complete.get("selected_artifact", {})
        if artifact.get("kind") != "trained_adapter" or artifact.get("generation") != best.get("generation") or artifact.get("selection_evidence") != best:
            raise ValueError("Completed selected artifact differs from eligible best checkpoint")
        artifact_rel = PurePosixPath(artifact.get("path", ""))
        if artifact_rel.is_absolute() or ".." in artifact_rel.parts:
            raise ValueError("Unsafe selected adapter export path")
        artifact_path = training / Path(*artifact_rel.parts)
        if not artifact_path.is_file() or sha(artifact_path) != artifact.get("sha256") or artifact_path.stat().st_size != artifact.get("bytes"):
            raise ValueError("Selected adapter export is missing or differs from run_complete")
    elif best_kind != "untrained_base":
        raise ValueError("Unknown selected artifact kind")
    elif any(g["candidate_eligible"] for g in gates):
        raise ValueError("Best points to base despite an eligible development candidate")

    metrics = complete.get("metrics", {})
    successful_steps = metrics.get("step")
    successful_examples = complete.get("unique_examples")
    supervised_tokens = metrics.get("supervised_tokens")
    derived_rows = complete.get("derived_view_rows")
    if derived_rows is None:
        derived_rows = config.get("derived_view_rows")
    if any(type(v) is not int or v < 0 for v in (successful_steps, successful_examples, supervised_tokens, derived_rows)) or not derived_rows:
        raise ValueError("Run completion lacks actual update/exposure/token/view counts")
    epochs = successful_examples / derived_rows
    if abs(float(complete.get("derived_view_epochs", epochs)) - epochs) > 1e-9:
        raise ValueError("Run-complete epoch summary differs from actual example count")
    progress_examples = progress.get("unique_examples", progress.get("rows_done"))
    if progress.get("step") != successful_steps or progress_examples != successful_examples:
        raise ValueError("Final progress and completion counts disagree")

    resume = validate_resume_evidence(root, config)
    final_dir = root / "final_eval"
    final_attempt = final_dir / "attempt_started.json"
    final_complete_path = final_dir / "complete.json"
    final_complete = None
    final_review = None
    final_status = "NOT_RUN"
    if best_kind == "untrained_base":
        if final_attempt.exists():
            raise ValueError("Base selected after failed development eligibility but sealed final attempt exists")
        final_status = "NOT_RUN_UNTOUCHED_SEALED_SET"
    elif final_complete_path.is_file():
        final_complete = read_json(final_complete_path)
        if final_complete.get("complete") is not True or final_complete.get("production_approval") is not False:
            raise ValueError("Final evaluation completion is invalid")
        if final_complete.get("selected_generation_manifest_sha256") != best.get("manifest_sha256"):
            raise ValueError("Final evaluation is not bound to selected candidate")
        final_review = read_final_review(root, final_complete_path, final_complete)
        final_status = "COMPLETED_AND_AGENT_REVIEWED"
    elif final_attempt.exists():
        final_status = "INCOMPLETE_ATTEMPT_NO_PROMOTION"
    else:
        final_status = "NOT_RUN"

    if best_kind == "untrained_base":
        recommendation = "RETAIN_UNTRAINED_PINNED_BASE; NO ADAPTER PASSED DEVELOPMENT ELIGIBILITY"
        final_status = "NOT_RUN_UNTOUCHED_SEALED_SET"
    elif final_review and final_review["decision"] == "ACCEPT_CANDIDATE":
        recommendation = "ROOT_AGENT_SEMANTIC_REVIEW_ACCEPTED_CANDIDATE_FOR_CONSIDERATION; PRODUCTION_APPROVAL_FALSE"
    elif final_review and final_review["decision"] == "REJECT_CANDIDATE":
        recommendation = "RETAIN_BASE; ROOT_AGENT_SEMANTIC_REVIEW_REJECTED_CANDIDATE"
    elif final_review:
        recommendation = "NO_PROMOTION; ROOT_AGENT_SEMANTIC_REVIEW_INCONCLUSIVE"
    else:
        recommendation = "CANDIDATE_DEVELOPMENT_ELIGIBLE_ONLY; FINAL_SEMANTIC_REVIEW_NOT_COMPLETE"

    scope_path = root / "owner_run_scope.json"
    scope = read_json(scope_path) if scope_path.is_file() else None
    report = {
        "schema": "MathVisionKid.conditional_grounding_final_semantic_assessment.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ASSESSMENT_FROM_HASH_BOUND_EVIDENCE",
        "recommendation": recommendation,
        "production_approved": False,
        "human_review_claimed": False,
        "source_human_labels_preserved": True,
        "review_provenance": "Development decisions are root-authored semantic reviews with human_review_claimed=false. Native15 review, when present, is separately root-authorized agent/AI review, accurately labeled. No human credential/certification is asserted.",
        "owner_scope": scope,
        "training_source_and_scope": {
            "run_config": {key: config.get(key) for key in CONFIG_FIELDS if key in config},
            "run_config_sha256": sha(run_config_path),
            "run_complete_sha256": sha(run_complete_path),
            "progress_sha256": sha(progress_path),
            "source_view_rows": config.get("source_rows"),
            "source_view_cases": config.get("source_cases"),
            "derived_training_view_rows": derived_rows,
            "successful_optimizer_updates": successful_steps,
            "successful_unique_training_examples": successful_examples,
            "successful_supervised_tokens": supervised_tokens,
            "derived_view_epochs_completed": epochs,
            "training_seconds": complete.get("training_seconds"),
            "full_corpus_training_claimed": False,
            "source_or_targets_modified_claimed": False,
        },
        "memory_resume": resume,
        "baseline_review": baseline,
        "development_gates": gates,
        "selected_artifact": {
            "kind": best_kind,
            "best_pointer_sha256": sha(best_path),
            "selected_generation": best.get("generation"),
            "selected_generation_manifest_sha256": best.get("manifest_sha256"),
            "selected_gate_file": best.get("gate_file"),
            "selected_gate_sha256": best.get("gate_sha256"),
            "development_eligible": bool(selected_gate and selected_gate["candidate_eligible"]),
            "production_approved": False,
        },
        "locked_final_evaluation": {
            "status": final_status,
            "expected_sealed_fixture_sha256": LOCKED_SHA256,
            "sealed_fixture_contents_read_by_assessment_builder": False,
            "completion": final_complete,
            "root_agent_semantic_review": final_review,
            "promotion_uses_final_review_only_if_complete_and_output_bound": True,
        },
        "limitations": [
            "Successful examples, updates, tokens and epochs come from run_complete/progress; failed-attempt tail work is listed separately and is not added to successful counts.",
            "Training scope is the recorded 16K source view and derived view only; this report does not claim full-corpus training, whole-curriculum coverage, or 6.5M examples trained.",
            "Semantic review provenance is not human verification or external certification. Source human labels remain source data and are not transferred as new attestations.",
            "A development gate, arithmetic/count metric, or raw publication proof alone does not establish semantic acceptance or production readiness.",
        ],
    }
    if final_complete is not None:
        report["locked_final_evaluation"].update({
            "complete_sha256": sha(final_complete_path),
            "paired_outputs_sha256": final_complete.get("paired_outputs_sha256"),
            "contract_sha256": final_complete.get("contract_sha256"),
            "selected_generation_manifest_sha256": final_complete.get("selected_generation_manifest_sha256"),
        })
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    report = build_assessment(root)
    target = root / "training" / "final_semantic_assessment.json"
    atomic_write_no_overwrite(target, report)
    print(json.dumps({"assessment_written": str(target),
                      "recommendation": report["recommendation"],
                      "production_approved": False,
                      "locked_final_status": report["locked_final_evaluation"]["status"]}))


if __name__ == "__main__":
    main()
