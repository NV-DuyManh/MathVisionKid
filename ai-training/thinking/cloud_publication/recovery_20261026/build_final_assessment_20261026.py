"""Build a CPU-only report from completed, hash-bound 2026-10-26 run evidence.

No model, corpus, or sealed/final fixture is loaded. Root semantic decisions
are consumed as evidence only; this module never creates judgments.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import sys
from datetime import datetime, timezone


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path):
    return json.loads(path.read_bytes())


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def canonical_json_sha(value) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import local module {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def summarize_baseline(doc, fixtures, base_rows):
    records = doc.get("records")
    if not isinstance(records, list) or len(records) != 30:
        raise ValueError("Frozen baseline must contain exactly 30 reviews")
    if doc.get("judgments_fixed_before_adapter_outputs_read") is not True or doc.get("human_review_claimed") is not False:
        raise ValueError("Frozen baseline provenance is invalid")
    expected = {f["id"]: f for f in fixtures}
    base_by = {r["fixture_id"]: r for r in base_rows}
    baseline_by = {r["fixture_id"]: r for r in records}
    if len(expected) != 30 or len(baseline_by) != 30 or len(base_by) != 30:
        raise ValueError("Fixture, baseline, or base-output count differs from 30")
    if set(expected) != set(baseline_by) or set(expected) != set(base_by):
        raise ValueError("Baseline/base output fixture IDs differ")
    for fid, fixture in expected.items():
        row = baseline_by[fid]
        if (row.get("grade"), row.get("mode")) != (fixture.get("grade"), fixture.get("mode")):
            raise ValueError("Frozen baseline grade/mode differs: " + fid)
        if type(row.get("base_pass")) is not bool or type(row.get("base_hint_leak")) is not bool:
            raise ValueError("Frozen baseline flags are malformed: " + fid)
        actual = base_by[fid]
        if hashlib.sha256(actual["output"].encode("utf-8")).hexdigest() != row.get("actual_output_sha256"):
            raise ValueError("Frozen baseline decision is not bound to actual base output: " + fid)
    return baseline_by, {
        "fixture_count": 30,
        "full_task_pass": sum(r["base_pass"] for r in records),
        "hint_leaks": sum(r["base_hint_leak"] for r in records),
        "review_sha256": None,
        "human_review_claimed": False,
        "records": records,
    }


def validate_development_gates(root: Path, baseline_path: Path, baseline_by, fixtures, config, policy, worker):
    training = root / "training"
    gates = []
    # Exact regex prevents gate_step_000100_summary.json from being counted as a gate.
    for gate_path in sorted(training.glob("gate_step_*.json")):
        match = re.fullmatch(r"gate_step_([0-9]{6})\.json", gate_path.name)
        if match is None:
            continue
        step = int(match.group(1))
        eval_dir = training / f"eval_step_{step:06d}"
        eval_bind_path = eval_dir / "eval_bindings.json"
        worker_summary_path = eval_dir / "gate_summary.json"
        root_summary_path = training / f"gate_step_{step:06d}_summary.json"
        if not all(p.is_file() for p in (eval_bind_path, worker_summary_path, root_summary_path)):
            raise ValueError(f"Incomplete gate evidence at step {step}")

        gate = read_json(gate_path)
        bindings = read_json(eval_bind_path)
        root_summary = read_json(root_summary_path)
        worker_summary = read_json(worker_summary_path)
        if bindings.get("generation_manifest_sha256") != gate.get("generation_manifest_sha256"):
            raise ValueError(f"Gate/evaluation generation binding differs at step {step}")
        generations = [g for g in training.glob("generation_step_*")
                       if (g / "generation_manifest.json").is_file()
                       and sha(g / "generation_manifest.json") == bindings.get("generation_manifest_sha256")]
        if len(generations) != 1:
            raise ValueError(f"Gate must bind exactly one generation at step {step}")
        generation = generations[0]
        manifest = worker.verify_generation(generation)
        if manifest.get("step") != step:
            raise ValueError(f"Bound generation step differs from gate step {step}")
        metrics = read_json(generation / "metrics.json")
        if metrics.get("step") != step or metrics.get("rows_done") != manifest.get("rows_done"):
            raise ValueError(f"Bound generation metrics differ at step {step}")

        policy.validate_gate(gate, step, bindings)
        decisions = gate["decisions"]
        if len(decisions) != 30:
            raise ValueError(f"Gate is incomplete at step {step}")
        decisions_by_id = {d["fixture_id"]: d for d in decisions}
        if len(decisions_by_id) != 30 or set(decisions_by_id) != set(baseline_by):
            raise ValueError(f"Gate IDs differ from frozen baseline at step {step}")
        for fid, d in decisions_by_id.items():
            frozen = baseline_by[fid]
            if d.get("base_pass") is not frozen["base_pass"] or d.get("base_hint_leak") is not frozen["base_hint_leak"]:
                raise ValueError(f"Frozen baseline flags changed in gate at {step}: {fid}")

        adapter_path = eval_dir / "adapter_generations.jsonl"
        base_path = training / "eval_step_000000" / "base_generations.jsonl"
        base_receipt = read_json(training / "eval_step_000000" / "eval_bindings.json")
        base_rows = read_jsonl(base_path)
        adapter_rows = read_jsonl(adapter_path)
        contract_path = training / "evaluation_contract.json"
        contract = read_json(contract_path)
        fixed = {k: bindings[k] for k in (
            "dev_sha256", "contract_sha256", "source_plan_sha256", "base_output_sha256",
            "generation_manifest_sha256", "fixture_ids", "final_stage")}
        if fixed["source_plan_sha256"] != config.get("source_plan_sha256"):
            raise ValueError(f"Gate source plan differs from run config at step {step}")
        if fixed["dev_sha256"] != config.get("dev_sha256"):
            raise ValueError(f"Gate development fixture binding differs at step {step}")
        canonical_contract_sha = canonical_json_sha(contract)
        if (canonical_contract_sha != fixed["contract_sha256"]
                or canonical_contract_sha != config.get("contract_sha256")
                or canonical_contract_sha != base_receipt.get("contract_sha256")):
            raise ValueError(f"Gate canonical evaluation contract binding differs at step {step}")
        proof = worker.verify_eval_evidence(eval_dir, fixed, fixtures, contract)
        if proof != bindings:
            raise ValueError(f"Worker evaluation verifier disagrees with receipt at step {step}")
        worker.validate_review_metadata(decisions, fixtures)
        worker.validate_review_completion(decisions, base_rows, adapter_rows)

        derived = policy.summarize_decisions(decisions)
        gate_sha = sha(gate_path)
        if (root_summary.get("schema") != "MathVisionKid.recovery_20261026.bound_gate_summary.v1"
                or root_summary.get("step") != step
                or root_summary.get("decision") != gate.get("decision")
                or root_summary.get("summary") != derived
                or root_summary.get("bindings") != bindings
                or root_summary.get("bound_checkpoint") != generation.name
                or root_summary.get("baseline_review_sha256") != sha(baseline_path)
                or not re.fullmatch(r"[0-9a-f]{64}", str(root_summary.get("decisions_sha256", "")))
                or root_summary.get("production_approved") is not False):
            raise ValueError(f"Root utility summary mismatch at step {step}: " + repr({
                "schema": root_summary.get("schema"),
                "summary_matches": root_summary.get("summary") == derived,
                "bindings_match": root_summary.get("bindings") == bindings,
                "baseline_sha_matches": root_summary.get("baseline_review_sha256") == sha(baseline_path),
                "bound_checkpoint_matches": root_summary.get("bound_checkpoint") == generation.name,
                "decisions_sha_valid": bool(re.fullmatch(r"[0-9a-f]{64}", str(root_summary.get("decisions_sha256", "")))),
                "production_approved": root_summary.get("production_approved"),
            }))
        if (worker_summary.get("summary") != derived
                or worker_summary.get("decision") != gate.get("decision")
                or worker_summary.get("gate_sha256") != gate_sha
                or worker_summary.get("bindings") != bindings
                or not isinstance(worker_summary.get("selected_best"), dict)
                or worker_summary["selected_best"].get("production_approval") is True):
            raise ValueError(f"Worker evaldir summary mismatch at step {step}")
        gates.append({
            "step": step,
            "decision": gate["decision"],
            "candidate_eligible": derived["candidate_eligible"],
            "summary": derived,
            "gate_sha256": gate_sha,
            "root_utility_summary_sha256": sha(root_summary_path),
            "worker_evaldir_summary_sha256": sha(worker_summary_path),
            "root_review_sha256": root_summary["decisions_sha256"],
            "baseline_review_sha256": root_summary["baseline_review_sha256"],
            "bindings": bindings,
            "root_review_decisions": decisions,
            "human_review_claimed": False,
        })
    return gates


def validate_selection(root: Path, best, complete, gates):
    training = root / "training"
    kind = best.get("kind")
    eligible = [g for g in gates if g["candidate_eligible"]]
    if kind == "untrained_base":
        if eligible:
            raise ValueError("Base selected despite an eligible development candidate")
        if complete.get("selected_artifact", {}).get("kind") != "untrained_base":
            raise ValueError("Completed artifact differs from base best pointer")
        return None
    if kind != "trained_adapter":
        raise ValueError("Unknown best artifact kind")
    match = next((g for g in eligible if g["step"] == best.get("step") and g["gate_sha256"] == best.get("gate_sha256")), None)
    if match is None:
        raise ValueError("Selected adapter lacks an eligible, hash-matched development gate")
    artifact = complete.get("selected_artifact", {})
    if artifact.get("kind") != "trained_adapter" or artifact.get("generation") != best.get("generation") or artifact.get("selection_evidence") != best:
        raise ValueError("Completed selected artifact differs from best pointer")
    rel = Path(artifact.get("path", ""))
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError("Unsafe selected adapter export path")
    export = training / rel
    if not export.is_file() or sha(export) != artifact.get("sha256") or export.stat().st_size != artifact.get("bytes"):
        raise ValueError("Selected adapter export is missing or hash-mismatched")
    return match


def validate_final_evaluation(root: Path, best, selected_gate):
    """Validate only completed final-evaluation evidence; never load fixtures.

    The final evaluator's generated paired/output files may be hashed here,
    but original sealed fixture files are never opened by this builder.
    """
    final_dir = root / "final_eval"
    attempt_path = final_dir / "attempt_started.json"
    complete_path = final_dir / "complete.json"
    attempt_exists, complete_exists = attempt_path.is_file(), complete_path.is_file()
    if not attempt_exists and not complete_exists:
        return {"status": "NOT_RUN_UNTOUCHED_SEALED_SET", "complete_sha256": None,
                "root_review": None, "quality_accepted": False,
                "sealed_fixture_contents_read": False}
    if best.get("kind") == "untrained_base":
        raise ValueError("Final evaluation attempt is not allowed while the untrained base is selected")
    if not complete_exists:
        return {"status": "INCOMPLETE_FINAL_ATTEMPT_NO_PROMOTION",
                "attempt_sha256": sha(attempt_path) if attempt_exists else None,
                "complete_sha256": None, "root_review": None,
                "quality_accepted": False, "sealed_fixture_contents_read": False}
    if not attempt_exists:
        raise ValueError("Final completion exists without its attempt receipt")

    complete = read_json(complete_path)
    if complete.get("complete") is not True or complete.get("production_approval") is not False:
        raise ValueError("Final evaluation completion is incomplete or asserts production approval")
    if complete.get("selected_generation_manifest_sha256") != best.get("manifest_sha256"):
        raise ValueError("Final evaluation is not bound to the selected eligible generation")
    paired_path = final_dir / "paired_generations.jsonl"
    base_path = final_dir / "base_generations.jsonl"
    candidate_path = final_dir / "adapter_generations.jsonl"
    for path in (paired_path, base_path, candidate_path):
        if not path.is_file():
            raise ValueError("Final completion lacks a required paired/output artifact: " + path.name)
    paired_sha, base_sha, candidate_sha = sha(paired_path), sha(base_path), sha(candidate_path)
    if (complete.get("paired_outputs_sha256") != paired_sha
            or complete.get("base_outputs_sha256") != base_sha
            or complete.get("adapter_outputs_sha256") != candidate_sha):
        raise ValueError("Final completion output hashes differ from actual artifact bytes")
    if not isinstance(complete.get("contract_sha256"), str) or re.fullmatch(r"[0-9a-f]{64}", complete["contract_sha256"]) is None:
        raise ValueError("Final completion lacks a contract hash")

    review_path = root / "root_final_semantic_review.json"
    if not review_path.is_file():
        return {"status": "COMPLETED_AWAITING_ROOT_SEMANTIC_REVIEW",
                "complete_sha256": sha(complete_path), "paired_outputs_sha256": paired_sha,
                "base_outputs_sha256": base_sha, "adapter_outputs_sha256": candidate_sha,
                "contract_sha256": complete["contract_sha256"], "root_review": None,
                "quality_accepted": False, "sealed_fixture_contents_read": False}

    review = read_json(review_path)
    if review.get("human_review_claimed") is not False or review.get("all_actual_outputs_reviewed") is not True:
        raise ValueError("Final root review must cover actual outputs and make no human-review claim")
    bound = {"complete_sha256": sha(complete_path), "paired_outputs_sha256": paired_sha,
             "base_outputs_sha256": base_sha, "adapter_outputs_sha256": candidate_sha,
             "contract_sha256": complete["contract_sha256"]}
    for key, value in bound.items():
        if review.get(key) != value:
            raise ValueError("Final root review does not bind current output: " + key)
    if review.get("decision") not in ("ACCEPT_CANDIDATE", "REJECT_CANDIDATE", "INCONCLUSIVE"):
        raise ValueError("Unsupported final root semantic decision")

    pairs = read_jsonl(paired_path)
    fixture_ids = complete.get("fixture_ids")
    if not isinstance(fixture_ids, list) or len(fixture_ids) != len(pairs) or [p.get("fixture_id") for p in pairs] != fixture_ids:
        raise ValueError("Final paired outputs differ from completed fixture IDs")
    decisions = review.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != len(pairs):
        raise ValueError("Final root review must contain one decision per actual pair")
    pairs_by_id = {p["fixture_id"]: p for p in pairs}
    seen, clean = set(), []
    for d in decisions:
        fid = d.get("fixture_id")
        if not isinstance(fid, str) or fid not in pairs_by_id or fid in seen:
            raise ValueError("Final review has missing, duplicate, or unexpected fixture IDs")
        seen.add(fid)
        pair = pairs_by_id[fid]
        if (d.get("grade"), d.get("mode")) != (pair.get("grade"), pair.get("mode")):
            raise ValueError("Final review grade/mode differs from completed pair")
        flags = ("base_pass", "candidate_pass", "base_hint_leak", "candidate_hint_leak", "critical_candidate_error")
        if any(type(d.get(k)) is not bool for k in flags):
            raise ValueError("Final review requires explicit semantic booleans")
        if d["mode"] != "hint_no_answer" and (d["base_hint_leak"] or d["candidate_hint_leak"]):
            raise ValueError("Final hint-leak flag appears outside hint mode")
        if not all(isinstance(d.get(k), str) and d[k].strip() for k in ("base_reason", "candidate_reason")):
            raise ValueError("Final review requires reasons for both outputs")
        base_output = pair["base"]["output"]
        candidate_output = (pair.get("candidate") or pair.get("adapter"))["output"]
        if hashlib.sha256(base_output.encode("utf-8")).hexdigest() != d.get("base_output_sha256"):
            raise ValueError("Final review base output hash differs")
        if hashlib.sha256(candidate_output.encode("utf-8")).hexdigest() != d.get("candidate_output_sha256"):
            raise ValueError("Final review candidate output hash differs")
        clean.append(d)
    if seen != set(fixture_ids):
        raise ValueError("Final review does not cover every completed pair")

    regressions = [d["fixture_id"] for d in clean if d["base_pass"] and not d["candidate_pass"]]
    new_leaks = [d["fixture_id"] for d in clean if d["candidate_hint_leak"] and not d["base_hint_leak"]]
    critical = [d["fixture_id"] for d in clean if d["critical_candidate_error"]]
    safe = not regressions and not new_leaks and not critical
    accepted = review["decision"] == "ACCEPT_CANDIDATE" and safe
    if not safe:
        status = "COMPLETED_REVIEW_FLAGS_BLOCK_ACCEPTANCE"
    elif review["decision"] == "ACCEPT_CANDIDATE":
        status = "COMPLETED_AND_ROOT_ACCEPTED"
    elif review["decision"] == "REJECT_CANDIDATE":
        status = "COMPLETED_AND_ROOT_REJECTED"
    else:
        status = "COMPLETED_ROOT_REVIEW_INCONCLUSIVE"
    return {"status": status, "complete_sha256": bound["complete_sha256"],
            "paired_outputs_sha256": paired_sha, "base_outputs_sha256": base_sha,
            "adapter_outputs_sha256": candidate_sha, "contract_sha256": complete["contract_sha256"],
            "root_review": {"sha256": sha(review_path), "decision": review["decision"],
                            "all_actual_outputs_reviewed": True, "human_review_claimed": False,
                            "summary": {"baseline_pass_regressions": regressions,
                                        "new_hint_leaks": new_leaks, "new_critical_errors": critical}},
            "quality_accepted": accepted, "sealed_fixture_contents_read": False}


def build_assessment(root: Path):
    root = root.resolve()
    training = root / "training"
    required = [training / name for name in ("run_config.json", "run_complete.json", "progress.json", "best.json")]
    if any(not path.is_file() for path in required):
        missing = [p.name for p in required if not p.is_file()]
        raise FileNotFoundError("Completed-run metadata missing: " + ", ".join(missing))
    cfg_path, complete_path, progress_path, best_path = required
    config, complete, progress, best = map(read_json, required)
    scope_path = root / "owner_run_scope.json"
    scope = read_json(scope_path)
    if config.get("model") != scope.get("model") or config.get("revision") != scope.get("revision"):
        raise ValueError("Run model/revision differs from owner scope")
    if complete.get("complete") is not True or progress.get("state") != "COMPLETE":
        raise ValueError("Training is not complete")
    if complete.get("best") != best or complete.get("production_approval") is not False:
        raise ValueError("Run completion and best pointer disagree or production approval is asserted")
    if complete.get("whole_corpus_training_claimed") is not False or config.get("whole_corpus_training_claimed") is not False:
        raise ValueError("Unsupported whole-corpus training claim")
    if config.get("previous_adapters_loaded") is True or config.get("fresh_base_required") is not True:
        raise ValueError("Run is not bound to the fresh-base-only plan")
    for key in ("source_view_sha256", "source_manifest_sha256", "source_plan_sha256", "dev_sha256"):
        if not isinstance(config.get(key), str) or re.fullmatch(r"[0-9a-f]{64}", config[key]) is None:
            raise ValueError("Run config lacks a valid pinned source/development hash: " + key)

    fixtures_path = root / "new_validation_candidates.jsonl"
    fixture_bytes = fixtures_path.read_bytes()
    fixtures = [json.loads(line) for line in fixture_bytes.decode("utf-8").splitlines() if line.strip()]
    dev_sha = sha(fixtures_path)
    baseline_path = root / "baseline_semantic_review_frozen.json"
    baseline_doc = read_json(baseline_path)
    if dev_sha != baseline_doc.get("fixture_raw_sha256") or dev_sha != config.get("dev_sha256"):
        raise ValueError("Development fixture bytes differ from frozen base/run bindings")
    if len(fixtures) != 30:
        raise ValueError("Development set is not exactly 30 fixtures")
    contract_path = training / "evaluation_contract.json"
    if not contract_path.is_file() or sha(contract_path) != baseline_doc.get("contract_sha256"):
        raise ValueError("Evaluation contract differs from fresh baseline")
    contract = read_json(contract_path)
    canonical_contract_sha = canonical_json_sha(contract)
    base_path = training / "eval_step_000000" / "base_generations.jsonl"
    base_receipt_path = training / "eval_step_000000" / "eval_bindings.json"
    if not base_path.is_file() or not base_receipt_path.is_file():
        raise ValueError("Fresh base evaluation evidence is missing")
    if sha(base_path) != baseline_doc.get("base_output_raw_sha256"):
        raise ValueError("Fresh base output bytes differ from frozen baseline")
    base_receipt = read_json(base_receipt_path)
    if (base_receipt.get("dev_sha256") != dev_sha
            or base_receipt.get("contract_sha256") != canonical_contract_sha
            or canonical_contract_sha != config.get("contract_sha256")
            or base_receipt.get("base_output_sha256") != sha(base_path)
            or base_receipt.get("fixture_ids") != [f["id"] for f in fixtures]):
        raise ValueError("Fresh base evaluation receipt differs from frozen inputs")
    base_rows = read_jsonl(base_path)

    policy = load_module(root / "recovery_policy_20261026.py", "assessment_20261026_policy")
    worker = load_module(root / "recovery_worker_20261026.py", "assessment_20261026_worker")
    baseline_by, baseline = summarize_baseline(baseline_doc, fixtures, base_rows)
    baseline["review_sha256"] = sha(baseline_path)
    gates = validate_development_gates(root, baseline_path, baseline_by, fixtures, config, policy, worker)
    if not gates:
        raise ValueError("No hash-bound completed development gate found")
    selected_gate = validate_selection(root, best, complete, gates)

    metrics = complete.get("metrics", {})
    steps = metrics.get("step")
    rows = complete.get("unique_examples")
    tokens = metrics.get("supervised_tokens")
    derived_rows = complete.get("derived_view_rows", config.get("derived_view_rows"))
    if any(type(v) is not int or v < 0 for v in (steps, rows, tokens, derived_rows)) or derived_rows == 0:
        raise ValueError("Completion is missing actual step/row/token/view counts")
    if metrics.get("rows_done") != rows or progress.get("rows_done") != rows or progress.get("step") != steps:
        raise ValueError("Progress and final successful exposure/update counts disagree")
    if complete.get("source_view_rows") != config.get("source_rows") or complete.get("derived_view_rows") != derived_rows:
        raise ValueError("Completion source/derived row counts disagree with run config")
    epochs = rows / derived_rows
    if not math.isfinite(epochs) or abs(float(complete.get("derived_view_epochs", -1)) - epochs) > 1e-9:
        raise ValueError("Derived-view epoch count differs from successful rows")
    training_seconds = complete.get("training_seconds")
    if not isinstance(training_seconds, (int, float)) or not math.isfinite(training_seconds) or training_seconds < 0:
        raise ValueError("Invalid completed training duration")

    eligible = any(g["candidate_eligible"] for g in gates)
    final_assessment = validate_final_evaluation(root, best, selected_gate)
    if best.get("kind") == "untrained_base":
        recommendation = "RETAIN_PINNED_BASE; NO DEVELOPMENT CANDIDATE PASSED ELIGIBILITY"
    elif final_assessment["quality_accepted"]:
        recommendation = "ROOT_SEMANTIC_REVIEW_ACCEPTED_CANDIDATE_FOR_CONSIDERATION; PRODUCTION_APPROVAL_FALSE"
    elif selected_gate is not None and final_assessment["status"] == "COMPLETED_REVIEW_FLAGS_BLOCK_ACCEPTANCE":
        recommendation = "NO_QUALITY_ACCEPTANCE; FINAL_ROOT_REVIEW_FLAGS_BLOCK_CANDIDATE"
    elif selected_gate is not None and final_assessment["status"] == "COMPLETED_AWAITING_ROOT_SEMANTIC_REVIEW":
        recommendation = "DEVELOPMENT_ELIGIBLE_ONLY; FINAL_ROOT_SEMANTIC_REVIEW_REQUIRED"
    elif selected_gate is not None and final_assessment["status"] == "INCOMPLETE_FINAL_ATTEMPT_NO_PROMOTION":
        recommendation = "DEVELOPMENT_ELIGIBLE_ONLY; FINAL_EVALUATION_INCOMPLETE_NO_PROMOTION"
    elif selected_gate is not None and final_assessment["status"] == "COMPLETED_AND_ROOT_REJECTED":
        recommendation = "RETAIN_BASE; ROOT_SEMANTIC_REVIEW_REJECTED_CANDIDATE"
    elif selected_gate is not None and final_assessment["status"] == "COMPLETED_ROOT_REVIEW_INCONCLUSIVE":
        recommendation = "NO_PROMOTION; ROOT_SEMANTIC_REVIEW_INCONCLUSIVE"
    elif selected_gate is not None:
        recommendation = "DEVELOPMENT_ELIGIBLE_ONLY; SEALED_FINAL_NOT_RUN; NO QUALITY ACCEPTANCE OR PRODUCTION APPROVAL"
    else:
        recommendation = "RETAIN_PINNED_BASE; NO DEVELOPMENT ELIGIBLE CANDIDATE"

    return {
        "schema": "MathVisionKid.recovery_20261026_final_assessment.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ASSESSMENT_FROM_HASH_BOUND_EVIDENCE",
        "recommendation": recommendation,
        "production_approved": False,
        "quality_accepted": final_assessment["quality_accepted"],
        "quality_acceptance_rule": "A candidate must first be development-eligible and then receive a separate root semantic review bound to completed final-evaluation output hashes. ",
        "human_review_claimed": False,
        "owner_scope": scope,
        "training_source_and_scope": {
            "run_config_sha256": sha(cfg_path), "run_complete_sha256": sha(complete_path),
            "progress_sha256": sha(progress_path), "source_view_rows": config.get("source_rows"),
            "source_view_cases": config.get("source_cases"), "derived_training_view_rows": derived_rows,
            "source_view_sha256": config.get("source_view_sha256"),
            "source_manifest_sha256": config.get("source_manifest_sha256"),
            "source_plan_sha256": config.get("source_plan_sha256"),
            "development_fixture_sha256": config.get("dev_sha256"),
            "successful_optimizer_updates": steps, "successful_unique_training_examples": rows,
            "successful_supervised_tokens": tokens, "derived_view_epochs_completed": epochs,
            "training_seconds": training_seconds, "source_or_targets_modified_claimed": False,
            "whole_corpus_training_claimed": False,
        },
        "baseline_review": baseline,
        "development_gates": gates,
        "selected_artifact": {
            "kind": best.get("kind"), "best_pointer_sha256": sha(best_path),
            "selected_generation": best.get("generation"), "selected_generation_manifest_sha256": best.get("manifest_sha256"),
            "selected_gate_file": best.get("gate_file"), "selected_gate_sha256": best.get("gate_sha256"),
            "development_eligible": selected_gate is not None,
            "some_development_gate_eligible": eligible, "quality_accepted": final_assessment["quality_accepted"],
            "production_approved": False,
        },
        "sealed_final_evaluation": {**final_assessment,
            "note": "Original sealed fixture contents are never opened by this builder. Final generated-output hashes and separate root semantic-review hashes are checked only when a completed final-evaluation receipt exists."},
        "limitations": [
            "Counts are derived from successful run completion metadata; this report does not infer unrecorded training work.",
            "The 30-item development set is reused from prior development, not an unseen benchmark or full-curriculum measure.",
            "Agent-authored semantic reviews do not constitute human certification.",
            "Development eligibility does not establish final quality acceptance or production readiness.",
        ],
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
            stream.write(payload); stream.flush(); os.fsync(stream.fileno())
        os.link(temp, path)
        temp.unlink()
        if hasattr(os, "O_DIRECTORY"):
            fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try: os.fsync(fd)
            finally: os.close(fd)
    finally:
        if temp.exists(): temp.unlink()
        if lock.exists(): lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    report = build_assessment(args.root)
    target = args.root / "training" / "final_semantic_assessment.json"
    atomic_write_no_overwrite(target, report)
    print(json.dumps({"assessment_written": str(target), "recommendation": report["recommendation"],
                      "quality_accepted": report["quality_accepted"], "production_approved": False,
                      "sealed_final_status": report["sealed_final_evaluation"]["status"]}))


if __name__ == "__main__":
    main()
