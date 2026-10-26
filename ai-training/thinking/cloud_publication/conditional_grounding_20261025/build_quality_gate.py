"""Bind root-authored paired reviews to frozen baseline and actual eval bytes.

This utility never generates or edits semantic judgments. It writes a gate only
when invoked with a complete root decision JSON and matching actual artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

FLAGS = ("base_pass", "adapter_pass", "base_hint_leak", "adapter_hint_leak", "critical_new_error")


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_bytes())


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def atomic_publish_no_overwrite(path: Path, document):
    """Stage/fsync beside destination and atomically publish without clobbering.

    An exclusive lock serializes this utility's writers; the destination is
    rechecked immediately before replace. A stale lock fails closed.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_name(path.name + ".lock")
    temp = path.with_name(path.name + f".{os.getpid()}.pending")
    payload = (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite {path}")
    lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.close(lock_fd)
        with temp.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite {path}")
        os.replace(temp, path)
        if hasattr(os, "O_DIRECTORY"):
            dir_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
    finally:
        if temp.exists():
            temp.unlink()
        if lock.exists():
            lock.unlink()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def validate_baseline_flags(decision, frozen_record):
    if decision.get("base_pass") is not frozen_record.get("base_pass"):
        raise ValueError("root baseline pass differs from frozen review")
    if decision.get("base_hint_leak") is not frozen_record.get("base_hint_leak"):
        raise ValueError("root baseline hint-leak flag differs from frozen review")


def validate_unique_decision_ids(decisions, expected_ids):
    ids = [d.get("fixture_id") for d in decisions]
    if len(ids) != len(expected_ids) or len(set(ids)) != len(ids) or set(ids) != set(expected_ids):
        raise ValueError("missing or duplicate fixture decision IDs")


def validate_pairwise_decisions(decisions, fixtures, frozen_records, base_rows, adapter_rows):
    """Validate root judgments and add byte hashes; never infer a judgment."""
    ids = [f["id"] for f in fixtures]
    if len(ids) != 30 or len(set(ids)) != 30:
        raise ValueError("frozen fixture set must contain exactly 30 unique IDs")
    if not isinstance(decisions, list) or len(decisions) != 30:
        raise ValueError("root decisions must contain exactly 30 records")
    validate_unique_decision_ids(decisions, ids)
    frozen = {r["fixture_id"]: r for r in frozen_records}
    base = {r["fixture_id"]: r for r in base_rows}
    candidate = {r["fixture_id"]: r for r in adapter_rows}
    if len(frozen) != 30 or len(base) != 30 or len(candidate) != 30:
        raise ValueError("frozen baseline or generation output fixture count differs")
    if set(frozen) != set(ids) or set(base) != set(ids) or set(candidate) != set(ids):
        raise ValueError("baseline/output fixture IDs differ from frozen fixtures")

    by_fixture = {f["id"]: f for f in fixtures}
    enriched = []
    for d in decisions:
        fid = d["fixture_id"]
        f, fr, br, ar = by_fixture[fid], frozen[fid], base[fid], candidate[fid]
        if d.get("grade") != f["grade"] or d.get("mode") != f["mode"]:
            raise ValueError("root review grade/mode differs for " + fid)
        if any(type(d.get(k)) is not bool for k in FLAGS):
            raise ValueError("all five review flags must be explicit booleans for " + fid)
        try:
            validate_baseline_flags(d, fr)
        except ValueError as exc:
            raise ValueError(str(exc) + " for " + fid) from exc
        if d["mode"] != "hint_no_answer" and (d["base_hint_leak"] or d["adapter_hint_leak"]):
            raise ValueError("hint leak flags are only valid for hint fixtures")
        if d["mode"] == "hint_no_answer" and ((d["base_pass"] and d["base_hint_leak"]) or (d["adapter_pass"] and d["adapter_hint_leak"])):
            raise ValueError("leaking hint cannot pass full-task review")
        if br.get("stage") != "base_before_training" or ar.get("stage") != "adapter_after_training":
            raise ValueError("generation stages differ for " + fid)
        if br.get("ended_eos") is not True or br.get("possibly_truncated") is not False or br.get("timed_out") is not False:
            if d["base_pass"]:
                raise ValueError("truncated/timed-out baseline cannot pass: " + fid)
        if ar.get("ended_eos") is not True or ar.get("possibly_truncated") is not False or ar.get("timed_out") is not False:
            if d["adapter_pass"]:
                raise ValueError("truncated/timed-out candidate cannot pass: " + fid)
        base_hash = sha_bytes(br["output"].encode("utf-8"))
        adapter_hash = sha_bytes(ar["output"].encode("utf-8"))
        if base_hash != fr["actual_output_sha256"]:
            raise ValueError("actual baseline output differs from frozen review: " + fid)
        base_reason = d.get("base_reason")
        adapter_reason = d.get("adapter_reason")
        if not isinstance(base_reason, str) or not base_reason.strip() or not isinstance(adapter_reason, str) or not adapter_reason.strip():
            raise ValueError("both base_reason and adapter_reason are required for " + fid)
        enriched.append({**d, "base_output_sha256": base_hash,
                         "adapter_output_sha256": adapter_hash})
    return enriched


def build_gate(root: Path, decisions_path: Path, step: int):
    training = root / "training"
    baseline_review = read_json(root / "baseline_semantic_review_frozen.json")
    if baseline_review.get("judgments_fixed_before_adapter_outputs_read") is not True or baseline_review.get("human_review_claimed") is not False:
        raise ValueError("baseline review is not frozen or makes an unsupported human-review claim")
    fixtures_path = root / "new_validation_candidates.jsonl"
    fixtures = read_jsonl(fixtures_path)
    if sha_bytes(fixtures_path.read_bytes()) != baseline_review["fixture_raw_sha256"]:
        raise ValueError("fixture bytes differ from frozen baseline review")
    cfg = read_json(training / "run_config.json")
    if cfg.get("dev_sha256") != baseline_review["fixture_raw_sha256"]:
        raise ValueError("run config dev hash differs from frozen baseline")

    base_dir = training / "eval_step_000000"
    base_path = base_dir / "base_generations.jsonl"
    base_eval_receipt = read_json(base_dir / "eval_bindings.json")
    if sha_bytes(base_path.read_bytes()) != baseline_review["base_output_raw_sha256"]:
        raise ValueError("base output file differs from frozen baseline")
    base_rows = read_jsonl(base_path)

    evaldir = training / f"eval_step_{step:06d}"
    adapter_path = evaldir / "adapter_generations.jsonl"
    eval_receipt = read_json(evaldir / "eval_bindings.json")
    if sha_bytes(adapter_path.read_bytes()) != eval_receipt.get("adapter_output_sha256"):
        raise ValueError("adapter outputs do not match eval binding hash")
    generation_name = eval_receipt.get("generation_manifest_sha256")
    if not isinstance(generation_name, str):
        raise ValueError("eval receipt lacks generation manifest binding")
    generation = next((p for p in training.glob("generation_step_*")
                       if (p / "generation_manifest.json").is_file()
                       and sha_bytes((p / "generation_manifest.json").read_bytes()) == generation_name), None)
    if generation is None:
        raise ValueError("bound checkpoint generation manifest not found")

    fixed = {k: eval_receipt[k] for k in (
        "dev_sha256", "contract_sha256", "source_plan_sha256",
        "base_output_sha256", "generation_manifest_sha256", "fixture_ids", "final_stage")}
    if fixed["dev_sha256"] != baseline_review["fixture_raw_sha256"]:
        raise ValueError("evaluation dev binding differs from baseline")
    if fixed["base_output_sha256"] != baseline_review["base_output_raw_sha256"]:
        raise ValueError("evaluation baseline output binding differs")
    contract_path = training / "evaluation_contract.json"
    if sha_bytes(contract_path.read_bytes()) != baseline_review["contract_sha256"]:
        raise ValueError("raw evaluation contract differs from frozen baseline")
    if fixed["contract_sha256"] != base_eval_receipt.get("contract_sha256"):
        raise ValueError("adapter contract binding differs from frozen baseline eval binding")
    if fixed["source_plan_sha256"] != cfg.get("source_plan_sha256"):
        raise ValueError("evaluation source plan differs from run config")
    if fixed["fixture_ids"] != [f["id"] for f in fixtures]:
        raise ValueError("eval fixture IDs/order differ")
    if eval_receipt.get("adapter_output_sha256") != sha_bytes(adapter_path.read_bytes()):
        raise ValueError("adapter output SHA mismatch")

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    worker = load_module(root / "recovery_worker_v5.py", "quality_gate_worker")
    policy = load_module(root / "recovery_policy_v2.py", "quality_gate_policy")
    contract = read_json(training / "evaluation_contract.json")
    verified = worker.verify_eval_evidence(evaldir, fixed, fixtures, contract)
    if verified != eval_receipt:
        raise ValueError("worker eval verifier and receipt disagree")
    adapter_rows = read_jsonl(adapter_path)

    incoming = read_json(decisions_path)
    if incoming.get("step") != step or incoming.get("all_actual_outputs_reviewed") is not True or incoming.get("human_review_claimed") is not False:
        raise ValueError("root decision file must bind this step, complete review, and no human claim")
    decisions = validate_pairwise_decisions(incoming.get("decisions"), fixtures,
        baseline_review["records"], base_rows, adapter_rows)
    worker.validate_review_metadata(decisions, fixtures)
    worker.validate_review_completion(decisions, base_rows, adapter_rows)

    bindings = {**fixed, "adapter_output_sha256": sha_bytes(adapter_path.read_bytes())}
    gate = {**bindings, "step": step, "decision": incoming.get("decision"),
            "all_actual_outputs_reviewed": True, "human_review_claimed": False,
            "decisions": decisions}
    policy.validate_gate(gate, step, bindings)
    summary = policy.summarize_decisions(decisions)
    summary_doc = {"schema": "MathVisionKid.bound_gate_summary.v1", "step": step,
                   "decision": gate["decision"], "summary": summary,
                   "bindings": bindings,
                   "baseline_review_sha256": sha_bytes((root / "baseline_semantic_review_frozen.json").read_bytes()),
                   "decisions_sha256": sha_bytes(decisions_path.read_bytes()),
                   "bound_checkpoint": generation.name,
                   "production_approved": False}
    return gate, summary_doc, training / f"gate_step_{step:06d}.json", training / f"gate_step_{step:06d}_summary.json"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True, help="Run root containing training/ and frozen review inputs")
    ap.add_argument("--decisions", type=Path, required=True, help="Root-authored paired decision JSON; no judgments are generated here")
    ap.add_argument("--step", type=int, required=True)
    args = ap.parse_args()
    gate, summary, gate_path, summary_path = build_gate(args.root, args.decisions, args.step)
    if gate_path.exists() or summary_path.exists():
        raise FileExistsError("Refusing to overwrite an existing gate or summary")
    atomic_publish_no_overwrite(summary_path, summary)
    # Gate is the worker's commit signal, so publish it only after summary bytes
    # are durable and visible.
    atomic_publish_no_overwrite(gate_path, gate)
    print(json.dumps({"gate": str(gate_path), "summary": str(summary_path),
                      "decision": gate["decision"], "candidate_eligible": summary["summary"]["candidate_eligible"]}))


if __name__ == "__main__":
    main()
