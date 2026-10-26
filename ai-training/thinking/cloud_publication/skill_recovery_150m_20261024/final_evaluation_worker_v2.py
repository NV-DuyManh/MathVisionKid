"""One-time matched evaluation of the reviewed development winner; no training."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import random
import sys
import time

import recovery_policy_v2 as policy
import recovery_worker_v3 as R
import inference_contract as I
import behavior_renderer as B

MODEL = I.MODEL
REVISION = I.REVISION
LOCKED_SHA = "03ec549a1ee3704b3eb0d814ccd12fee5fe9ba2f66dee6d8f1aaba7c08013615"
RENDERER_SHA = "763da2f7a1931962a9ad1a49b16d4b8dfe5263a09e69603c49959adb02a5ec8f"
CONTRACT_SHA = "6b44ebabad6eeca636142012418e17f126AE9d57539e10b4d1fa5b4314033bc0".lower()
FEWSHOT_POLICY_SHA = "115d05bd975c4b672033dc6637db785c6634d6ee54b0e1914c0c07de6c9ebd70"
SCHEMA = "MathVisionKid.skill_recovery_final_eval.v2"
FIXTURE_KEYS = {"id", "grade", "mode", "userproblem", "exact_reference_answer", "checker", "oracle", "rubric", "not_training_data", "authorship"}
UNCHANGED_INPUTS = (
    "owner_run_scope.json", "owner_scope_binding_v2.json", "locked_test_binding.json",
    "locked_test_candidates.jsonl", "new_validation_candidates.jsonl", "training/run_complete.json",
    "training/best.json", "training/run_config.json", "derived_sampling_plan.json",
    "recovery_worker_v3.py", "recovery_policy_v2.py", "behavior_renderer.py", "inference_contract.py",
    "fewshot_contract.py", "fewshot_selection.json", "fewshot_selection_policy.json",
    "root_fewshot_semantic_review.json", "source_example_bank.json",
    "projection_preflight.json", "source_behavior_samples.json",
    "fewshot_dev/contract.json", "fewshot_dev/complete.json", "fewshot_dev/generations.jsonl",
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key: " + key)
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


def read(path):
    return strict_json(Path(path).read_bytes())


def read_rows(path):
    return [strict_json(line) for line in Path(path).read_text("utf-8").splitlines() if line.strip()]


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".pending")
    with temp.open("w", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def atomic_bytes(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".pending")
    with temp.open("wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def write_jsonl(path, rows):
    data = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows).encode("utf-8")
    atomic_bytes(path, data)


def inside(parent, relative):
    rel = PurePosixPath(relative)
    path = Path(parent).joinpath(*rel.parts)
    if not relative or rel.is_absolute() or ".." in rel.parts or "\\" in relative:
        raise ValueError("Unsafe evidence path")
    if path.is_symlink() or not path.resolve().is_relative_to(Path(parent).resolve()):
        raise ValueError("Evidence path escapes its run")
    return path


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def verify_fixture_bundle(root, scope):
    """Bind exact frozen fixture bytes, order, modes and user-facing schema."""
    path = root / "locked_test_candidates.jsonl"
    binding = read(root / "locked_test_binding.json")
    actual_sha = sha(path)
    if actual_sha != LOCKED_SHA or actual_sha != scope.get("locked_test_sha256"):
        raise ValueError("Frozen locked fixture hash differs from owner scope")
    if binding.get("fixture_sha256") != actual_sha or binding.get("count") != 20 or binding.get("frozen_before_new_candidate_outputs") is not True:
        raise ValueError("Locked fixture binding differs")
    fixtures = read_rows(path)
    if len(fixtures) != 20 or len({x.get("id") for x in fixtures}) != 20:
        raise ValueError("Expected 20 uniquely identified frozen fixtures")
    for row in fixtures:
        if set(row) != FIXTURE_KEYS or type(row.get("grade")) is not int or row["grade"] not in range(1, 6):
            raise ValueError("Fixture fields or grade do not match frozen schema")
        if row.get("mode") not in policy.EVALUATION_MODES or not isinstance(row.get("userproblem"), str) or not row["userproblem"].strip():
            raise ValueError("Invalid fixture mode or userproblem")
        if row.get("not_training_data") is not True:
            raise ValueError("Fixtures must remain explicitly outside training data")
    for grade in range(1, 6):
        rows = [x for x in fixtures if x["grade"] == grade]
        modes = [x["mode"] for x in rows]
        if len(rows) != 4 or modes.count("answer") != 2 or modes.count("hint_no_answer") != 1:
            raise ValueError("Final fixture grade/mode distribution differs")
        if sum(mode in ("student_error", "missing_or_contradictory_info") for mode in modes) != 1:
            raise ValueError("Expected one guard/feedback fixture per grade")
    return fixtures, actual_sha


def validate_outputs(rows, fixtures, contract, contract_sha, stage):
    if [r.get("fixture_id") for r in rows] != [f["id"] for f in fixtures]:
        raise ValueError("Output fixture count/order differs")
    for row, fixture in zip(rows, fixtures):
        if (row.get("grade") != fixture["grade"] or row.get("mode") != fixture["mode"]
                or row.get("stage") != stage or row.get("contract_sha256") != contract_sha
                or row.get("prompt_token_sha256") != contract["prompt_token_sha256"].get(fixture["id"])
                or row.get("max_new_tokens") != contract["decoding"]["max_new_tokens"]
                or not isinstance(row.get("output"), str)
                or row.get("seed") != expected_seed(fixture["id"])):
            raise ValueError("Output does not match frozen per-fixture inference contract")


def expected_seed(fixture_id):
    return (20261024 + int(hashlib.sha256(fixture_id.encode()).hexdigest()[:8], 16)) % (2**31)


def validate_fewshot_outputs(rows, fixtures, contract, contract_sha, full_fixture_ids, full_fixture_sha):
    if [row.get("fixture_id") for row in rows] != [fixture["id"] for fixture in fixtures]:
        raise ValueError("Few-shot selected subset count/order differs")
    if (contract.get("fixture_ids") != [fixture["id"] for fixture in fixtures]
            or contract.get("frozen_fixture_ids") != full_fixture_ids
            or contract.get("fixture_sha256") != full_fixture_sha):
        raise ValueError("Few-shot subset contract lost frozen full-fixture binding")
    for row, fixture in zip(rows, fixtures):
        if (row.get("grade") != fixture["grade"] or row.get("mode") != fixture["mode"]
                or row.get("stage") != "fewshot_selected_after_base_review"
                or row.get("contract_sha256") != contract_sha
                or row.get("prompt_token_sha256") != contract["prompt_token_sha256"].get(fixture["id"])
                or row.get("max_new_tokens") != contract["decoding"]["max_new_tokens"]
                or row.get("seed") != expected_seed(fixture["id"])
                or row.get("fewshot_example_ids") != contract["example_selections_by_fixture"].get(fixture["id"])):
            raise ValueError("Few-shot output differs from its sealed mode/example/seed contract")


def model_sequence_limit(fewshot_modes):
    """Leave room for few-shot prompts (3072 tokens) plus 1024 new tokens."""
    return 4096 if fewshot_modes else 2048


def persist_fewshot_contract(out, contract, contract_sha):
    if hashlib.sha256(canonical(contract).encode()).hexdigest() != contract_sha:
        raise ValueError("Few-shot contract hash mismatch before persistence")
    path = Path(out) / "contract.json"
    atomic(path, {**contract, "contract_sha256": contract_sha})
    return path


def verify_generation(generation):
    manifest = read(generation / "generation_manifest.json")
    if manifest.get("complete") is not True or not manifest.get("files"):
        raise ValueError("Incomplete selected generation")
    for name, digest in manifest["files"].items():
        member = inside(generation, name)
        if sha(member) != digest or member.stat().st_size != manifest["file_bytes"][name]:
            raise ValueError("Selected checkpoint member hash/size mismatch")
    return manifest


def verify_selection(root, scope, fixtures, dev_sha):
    """Replay selection only from hash-bound, reviewed development evidence."""
    out = root / "training"
    cfg = read(out / "run_config.json")
    complete = read(out / "run_complete.json")
    best = read(out / "best.json")
    if complete.get("complete") is not True or complete.get("budget_satisfied") is not True:
        raise ValueError("Training run is incomplete or outside authorized budget")
    if complete.get("best") != best or best.get("semantic_review_pending") is not False:
        raise ValueError("No finalized reviewed selection; stop before locked inference")
    if complete.get("hard_deadline_unix") != scope.get("hard_deadline_unix") or cfg.get("hard_deadline_unix") != scope.get("hard_deadline_unix"):
        raise ValueError("Training deadline differs from owner scope")
    if cfg.get("model") != MODEL or cfg.get("revision") != REVISION or cfg.get("dev_sha256") != dev_sha:
        raise ValueError("Training model/revision/development binding differs")
    pins = {
        "recovery_worker_v3.py": cfg.get("worker_sha256"),
        "recovery_policy_v2.py": cfg.get("policy_sha256"),
        "derived_sampling_plan.json": cfg.get("source_plan_sha256"),
        "behavior_renderer.py": cfg.get("renderer_sha256"),
    }
    for name, expected in pins.items():
        if not isinstance(expected, str) or len(expected) != 64 or sha(root / name) != expected:
            raise ValueError("Training code/plan hash mismatch: " + name)
    if sha(root / "inference_contract.py") != CONTRACT_SHA or sha(root / "behavior_renderer.py") != RENDERER_SHA:
        raise ValueError("Evaluation contract or prompt renderer code pin differs")
    contract = read(out / "evaluation_contract.json")
    contract_sha = hashlib.sha256(canonical(contract).encode()).hexdigest()
    if cfg.get("contract_sha256") != contract_sha or contract.get("fixture_sha256") != dev_sha:
        raise ValueError("Development evaluation contract is not bound")
    base_dir = out / "eval_step_000000"
    base_path = base_dir / "base_generations.jsonl"
    base_rows = read_rows(base_path)
    baseline_binding = {
        "dev_sha256": dev_sha, "contract_sha256": contract_sha,
        "source_plan_sha256": cfg["source_plan_sha256"],
        "base_output_sha256": sha(base_path), "fixture_ids": [x["id"] for x in fixtures],
    }
    if read(base_dir / "eval_bindings.json") != baseline_binding:
        raise ValueError("Development baseline evidence binding differs")
    validate_outputs(base_rows, fixtures, contract, contract_sha, "base_before_training")
    evidence_hashes = {
        "training/evaluation_contract.json": sha(out / "evaluation_contract.json"),
        "training/eval_step_000000/base_generations.jsonl": sha(base_path),
        "training/eval_step_000000/eval_bindings.json": sha(base_dir / "eval_bindings.json"),
    }
    # Pin every completed historical generation, including non-selected ones.
    for generation in sorted(out.glob("generation_step_*")):
        if not generation.is_dir() or generation.name.endswith(".pending"):
            continue
        manifest = verify_generation(generation)
        evidence_hashes[f"training/{generation.name}/generation_manifest.json"] = sha(generation / "generation_manifest.json")
        for member in manifest["files"]:
            evidence_hashes[f"training/{generation.name}/{member}"] = sha(generation / member)
    baseline = {"kind": "untrained_base", "model": MODEL, "revision": REVISION,
                "validation_output_sha256": sha(base_path), "production_approval": False}
    replay = dict(baseline)
    gates = sorted(out.glob("gate_step_*.json"), key=lambda p: read(p)["step"])
    if not gates:
        raise ValueError("No reviewed development gates; stop before locked inference")
    profile = read(out / "base_review_profile.json")
    proofs = []
    for gate_path in gates:
        gate = read(gate_path)
        step = gate.get("step")
        if type(step) is not int or step < 0:
            raise ValueError("Invalid development gate step")
        eval_dir = out / f"eval_step_{step:06d}"
        bindings = read(eval_dir / "eval_bindings.json")
        for key, value in baseline_binding.items():
            if bindings.get(key) != value:
                raise ValueError("Gate does not bind frozen dev baseline")
        R.verify_eval_evidence(eval_dir, {k: v for k, v in bindings.items() if k != "adapter_output_sha256"}, fixtures, contract)
        R.validate_review_metadata(gate["decisions"], fixtures)
        R.validate_review_completion(gate["decisions"], base_rows, read_rows(eval_dir / "adapter_generations.jsonl"))
        policy.validate_gate(gate, step, bindings)
        if profile != {"base_output_sha256": baseline_binding["base_output_sha256"],
                       "dev_sha256": dev_sha, "profile": R.baseline_profile(gate["decisions"])}:
            raise ValueError("Development baseline review profile changed")
        evidence_hashes[f"training/{gate_path.name}"] = sha(gate_path)
        evidence_hashes[f"training/eval_step_{step:06d}/eval_bindings.json"] = sha(eval_dir / "eval_bindings.json")
        evidence_hashes[f"training/eval_step_{step:06d}/adapter_generations.jsonl"] = sha(eval_dir / "adapter_generations.jsonl")
        generations = [p for p in out.glob(f"generation_step_{step:06d}_rows_*") if p.is_dir() and not p.name.endswith(".pending")]
        if len(generations) != 1:
            raise ValueError("Missing or ambiguous reviewed checkpoint")
        generation = generations[0]
        manifest = verify_generation(generation)
        if manifest.get("step") != step or sha(generation / "generation_manifest.json") != bindings["generation_manifest_sha256"]:
            raise ValueError("Reviewed checkpoint manifest differs from gate")
        candidate = {"kind": "trained_adapter", "generation": generation.name,
                     "manifest_sha256": bindings["generation_manifest_sha256"],
                     "gate_file": gate_path.name, "gate_sha256": sha(gate_path), "step": step,
                     "bindings": bindings, "production_approval": False}
        replay = R.choose_best(replay, policy.summarize_decisions(gate["decisions"]), candidate, baseline)
        proofs.append({"step": step, "gate_file": gate_path.name, "gate_sha256": sha(gate_path),
                       "generation": generation.name, "manifest_sha256": sha(generation / "generation_manifest.json")})
    if replay != best:
        raise ValueError("Best pointer differs from reviewed development replay")
    selected = complete.get("selected_artifact", {})
    if selected.get("kind") != best.get("kind") or selected.get("selection_evidence") != best:
        raise ValueError("Completed selected artifact does not bind best evidence")
    if best["kind"] == "trained_adapter":
        if selected.get("generation") != best["generation"]:
            raise ValueError("Selected generation differs from best")
        archive = inside(out, selected["path"])
        if sha(archive) != selected["sha256"] or archive.stat().st_size != selected["bytes"]:
            raise ValueError("Selected adapter archive hash/size mismatch")
        evidence_hashes[f"training/{selected['path']}"] = sha(archive)
        verify_generation(inside(out, best["generation"]))
    elif best["kind"] != "untrained_base" or selected.get("model") != MODEL or selected.get("revision") != REVISION or selected.get("adapter") is not None:
        raise ValueError("Unknown selected artifact; stop before locked inference")
    return {"selected_kind": best["kind"], "best": best, "selected_artifact": selected,
            "baseline_output_sha256": sha(base_path), "gate_proofs": proofs,
            "base_rows": base_rows, "dev_contract_sha256": contract_sha,
            "evidence_hashes": evidence_hashes}


def verify_fewshot_selection(root, dev_fixtures, dev_sha, baseline_output_sha256):
    """Replay whole-model-mode eligibility from root's bound dev judgments."""
    policy_path = root / "fewshot_selection_policy.json"
    selection_path = root / "fewshot_selection.json"
    review_path = root / "root_fewshot_semantic_review.json"
    policy_doc, selected, review = read(policy_path), read(selection_path), read(review_path)
    if sha(policy_path) != FEWSHOT_POLICY_SHA or policy_doc.get("frozen_before_fewshot_outputs") is not True:
        raise ValueError("Few-shot eligibility policy is not the frozen expected revision")
    if selected.get("schema") != "MathVisionKid.mode_context_selection.v1" or selected.get("base_kind") != "untrained_base":
        raise ValueError("Missing or unsupported frozen mode-context selection")
    if policy_doc.get("development_fixture_sha256") != dev_sha:
        raise ValueError("Few-shot selection policy fixture binding differs")
    required_hex = {
        "dev_fixture_sha256": dev_sha, "baseline_output_sha256": baseline_output_sha256,
        "fewshot_output_sha256": None, "fewshot_contract_sha256": None,
        "bank_sha256": None, "root_semantic_review_sha256": sha(review_path),
        "selection_policy_sha256": FEWSHOT_POLICY_SHA,
    }
    for key, expected in required_hex.items():
        value = selected.get(key)
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError("Invalid mode-context selection hash: " + key)
        if expected is not None and value != expected:
            raise ValueError("Mode-context selection binding differs: " + key)
    module_hashes = selected.get("inference_module_sha256")
    expected_modules = {"inference_contract": sha(root / "inference_contract.py"),
                        "fewshot_contract": sha(root / "fewshot_contract.py")}
    if module_hashes != expected_modules:
        raise ValueError("Few-shot/inference module hashes differ from reviewed selection")
    bank_path = root / "source_example_bank.json"
    if sha(bank_path) != selected["bank_sha256"]:
        raise ValueError("Few-shot source bank hash differs")
    proof = read(root / "fewshot_dev" / "complete.json")
    fewshot_contract = read(root / "fewshot_dev" / "contract.json")
    fewshot_outputs = root / "fewshot_dev" / "generations.jsonl"
    if (proof.get("complete") is not True or proof.get("fixture_sha256") != dev_sha
            or proof.get("contract_sha256") != selected["fewshot_contract_sha256"]
            or proof.get("example_bank_sha256") != selected["bank_sha256"]
            or proof.get("outputs_sha256") != selected["fewshot_output_sha256"]
            or sha(fewshot_outputs) != selected["fewshot_output_sha256"]
            or hashlib.sha256(canonical(fewshot_contract).encode()).hexdigest() != selected["fewshot_contract_sha256"]
            or fewshot_contract.get("fixture_sha256") != dev_sha
            or fewshot_contract.get("example_bank_sha256") != selected["bank_sha256"]):
        raise ValueError("Frozen few-shot development proof/contract/output differs")
    if selected.get("baseline_output_sha256") != policy_doc.get("baseline_output_sha256") or selected.get("bank_sha256") != policy_doc.get("source_bank_sha256"):
        raise ValueError("Mode-context selection does not bind frozen policy baseline/source")
    if review.get("all_actual_fields_read") is not True or review.get("human_review_claimed") is not False:
        raise ValueError("Root few-shot semantic review is incomplete or overclaims attestation")
    if review.get("base_output_sha256") != baseline_output_sha256 or review.get("fewshot_output_sha256") != selected["fewshot_output_sha256"]:
        raise ValueError("Root semantic review does not bind exact development output bytes")
    expected = {row["id"]: row for row in dev_fixtures}
    decisions = review.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != len(expected) or len({r.get("fixture_id") for r in decisions}) != len(expected):
        raise ValueError("Root review must cover every frozen development fixture exactly once")
    flags = ("base_pass", "fewshot_pass", "base_hint_leak", "fewshot_hint_leak", "critical_new_error")
    by_mode = {"worked_solution": [], "hint_level_1": []}
    expected_group_modes = policy_doc.get("selection_groups", {})
    if expected_group_modes != {"worked_solution": ["answer", "student_error", "missing_or_contradictory_info"],
                                "hint_level_1": ["hint_no_answer"]}:
        raise ValueError("Frozen few-shot policy model-mode groups differ")
    if policy_doc.get("unvalidated_modes_keep_baseline") != ["hint_level_2", "hint_level_3"]:
        raise ValueError("Frozen few-shot policy unvalidated hint routing differs")
    for decision in decisions:
        fixture = expected.get(decision.get("fixture_id"))
        if fixture is None or any(type(decision.get(flag)) is not bool for flag in flags):
            raise ValueError("Invalid or out-of-set semantic-review decision")
        if decision["base_hint_leak"] or decision["fewshot_hint_leak"]:
            if fixture["mode"] != "hint_no_answer":
                raise ValueError("Hint-leak flags are only valid for hint fixtures")
        if I.MODE_MAP[fixture["mode"]] in by_mode:
            by_mode[I.MODE_MAP[fixture["mode"]]].append(decision)
    eligibility = {}
    group_summaries = {}
    for model_mode, rows in by_mode.items():
        expected_modes = set(expected_group_modes[model_mode])
        expected_count = sum(fixture["mode"] in expected_modes for fixture in dev_fixtures)
        if len(rows) != expected_count or not rows or any(expected[decision["fixture_id"]]["mode"] not in expected_modes for decision in rows):
            raise ValueError("Review rows do not exactly cover policy mode group " + model_mode)
        regressions = sum(r["base_pass"] and not r["fewshot_pass"] for r in rows)
        critical = sum(r["critical_new_error"] for r in rows)
        leaks = sum(r["fewshot_hint_leak"] and not r["base_hint_leak"] for r in rows)
        gain = sum(r["fewshot_pass"] for r in rows) - sum(r["base_pass"] for r in rows)
        base_answers = sum(r["base_pass"] for r in rows if expected[r["fixture_id"]]["mode"] == "answer")
        fewshot_answers = sum(r["fewshot_pass"] for r in rows if expected[r["fixture_id"]]["mode"] == "answer")
        eligibility[model_mode] = (regressions == 0 and critical == 0 and leaks == 0 and gain > 0
                                   and fewshot_answers >= base_answers)
        group_summaries[model_mode] = {"fixtures": len(rows), "full_task_gain": gain,
                                       "baseline_pass_regressions": regressions,
                                       "new_critical_errors": critical, "new_hint_leaks": leaks,
                                       "base_answer_passes": base_answers,
                                       "fewshot_answer_passes": fewshot_answers,
                                       "eligible": eligibility[model_mode]}
    eligibility.update({"hint_level_2": False, "hint_level_3": False})
    if selected.get("eligible_by_model_mode") != eligibility:
        raise ValueError("Declared group eligibility differs from full-task dev replay")
    choices = selected.get("mode_selection")
    expected_modes = {"worked_solution", "hint_level_1", "hint_level_2", "hint_level_3"}
    if not isinstance(choices, dict) or set(choices) != expected_modes or any(x not in ("inference_contract", "fewshot_contract") for x in choices.values()):
        raise ValueError("Invalid mode-level inference-module selection")
    if any(choices.get(mode) == "fewshot_contract" and not eligibility[mode]
           for mode in ("worked_solution", "hint_level_1")):
        raise ValueError("Few-shot selected for a mode group that failed frozen eligibility")
    if any(choices.get(mode) == "fewshot_contract" for mode in ("hint_level_2", "hint_level_3")):
        raise ValueError("Few-shot routing is not validated for hint levels 2 or 3")
    evidence = {
        "fewshot_selection.json": sha(selection_path),
        "fewshot_selection_policy.json": sha(policy_path),
        "root_fewshot_semantic_review.json": sha(review_path),
        "fewshot_contract.py": sha(root / "fewshot_contract.py"),
        "source_example_bank.json": sha(bank_path),
        "fewshot_dev/contract.json": sha(root / "fewshot_dev" / "contract.json"),
        "fewshot_dev/complete.json": sha(root / "fewshot_dev" / "complete.json"),
        "fewshot_dev/generations.jsonl": sha(fewshot_outputs),
    }
    bank = read(bank_path)
    for filename, metadata in bank.get("source_files", {}).items():
        if not isinstance(metadata, dict) or "sha256" not in metadata:
            continue
        source = root / filename
        if not source.is_file() or sha(source) != metadata.get("sha256"):
            raise ValueError("Few-shot bank source file pin mismatch: " + filename)
        evidence[filename] = sha(source)
    return {"mode_selection": choices, "eligible_by_model_mode": eligibility,
            "group_summaries": group_summaries, "selection_sha256": sha(selection_path),
            "fewshot_contract_sha256": selected["fewshot_contract_sha256"],
            "bank_sha256": selected["bank_sha256"], "evidence_hashes": evidence}


def check_environment(root):
    pinned = {"torch": "2.11.0", "transformers": "5.16.1", "unsloth": "2026.10.7",
              "unsloth_zoo": "2026.10.7", "peft": "0.21.2", "accelerate": "1.15.0", "bitsandbytes": "0.50.2"}
    actual = {name: importlib.metadata.version(name) for name in pinned}
    if any(actual[name].split("+")[0] != value for name, value in pinned.items()):
        raise ValueError("Inference environment differs from frozen package pins")
    install = read(root / "install_status.json")["versions"]["packages"]
    if any(actual[name] != install[name] for name in pinned):
        raise ValueError("Actual inference packages differ from install receipt")
    if Path(sys.prefix).resolve() != (root / "venv").resolve():
        raise ValueError("Must run from this cloud run's exact venv")
    return actual


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    scope = R.load_scope(root)
    if Path(sys.prefix).resolve() != (root / "venv").resolve():
        raise ValueError("Must run in this cloud run's exact venv")
    if not (root / "owner_scope_binding_v2.json").is_file():
        raise ValueError("Owner scope binding is required")
    fixtures, locked_sha = verify_fixture_bundle(root, scope)
    dev_path = root / "new_validation_candidates.jsonl"
    dev_sha = sha(dev_path)
    if dev_sha != scope.get("dev_sha256"):
        raise ValueError("Frozen development fixture hash differs from owner scope")
    dev = read_rows(dev_path)
    if len(dev) != 30 or len({x.get("id") for x in dev}) != 30:
        raise ValueError("Expected 30 bound development fixtures")
    selection = verify_selection(root, scope, dev, dev_sha)
    if not selection.get("selected_kind"):
        raise ValueError("No reviewed selection; stopping before locked inference")
    mode_context = verify_fewshot_selection(root, dev, dev_sha, selection["baseline_output_sha256"])
    fewshot_modes = {mode for mode, module in mode_context["mode_selection"].items() if module == "fewshot_contract"}
    if fewshot_modes and selection["selected_kind"] != "untrained_base":
        raise ValueError("Few-shot source-only eligibility was established only for the untrained base")

    final = root / "final_eval"
    final.mkdir(exist_ok=False)  # Immutable one-shot attempt marker.
    started = time.time()
    deadline = min(started + 900, float(scope["hard_deadline_unix"]) - 300)
    if deadline <= started:
        raise TimeoutError("No authorized inference window remains")
    input_hashes = {name: sha(root / name) for name in UNCHANGED_INPUTS}
    packages = check_environment(root)
    atomic(final / "attempt_started.json", {"schema": SCHEMA, "started_unix": started,
           "deadline_unix": deadline, "locked_test_sha256": locked_sha, "run_once": True,
           "selection_change_allowed": False, "training_performed": False})
    atomic(final / "input_hashes.json", input_hashes)
    atomic(final / "selection_before_test.json", {k: v for k, v in selection.items() if k != "base_rows"} | {
           "selected_before_locked_inference": True, "test_results_used_for_selection": False})
    atomic(final / "mode_context_selection.json", {k: v for k, v in mode_context.items() if k != "evidence_hashes"} | {
           "evidence_hashes": mode_context["evidence_hashes"], "selected_before_locked_inference": True,
           "test_results_used_for_selection": False, "identical_prompt_claim_for_fewshot": False})
    atomic(final / "environment.json", {"python": sys.version, "prefix": sys.prefix, "packages": packages})

    import torch
    from transformers import BitsAndBytesConfig
    from unsloth import FastLanguageModel
    if not torch.cuda.is_available() or "t4" not in torch.cuda.get_device_name(0).lower():
        raise RuntimeError("Expected the authorized T4 inference environment")
    random.seed(20261024)
    torch.manual_seed(20261024)
    torch.cuda.manual_seed_all(20261024)
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL, revision=REVISION, use_exact_model_name=True,
        max_seq_length=model_sequence_limit(fewshot_modes),
        dtype=torch.float16, load_in_4bit=True,
        quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True), attn_implementation="sdpa")
    if getattr(model.config, "_commit_hash", None) != REVISION or tokenizer.eos_token_id != 151645 or tokenizer.convert_tokens_to_ids("<|im_end|>") != 151645:
        raise ValueError("Fresh base revision/tokenizer end-token differs")
    contract, csha = I.eval_contract(fixtures, tokenizer, locked_sha)
    if contract["fixture_ids"] != [x["id"] for x in fixtures] or contract["enable_thinking"] is not False:
        raise ValueError("Locked contract IDs or thinking setting differs")
    atomic(final / "evaluation_contract.json", {**contract, "contract_sha256": csha})

    class InferenceOnlyMode:
        @staticmethod
        def for_inference(target):
            return FastLanguageModel.for_inference(target)
        @staticmethod
        def for_training(target):
            return FastLanguageModel.for_inference(target)

    I.generate_fixtures(model, tokenizer, fixtures, final, "base_before_training", contract, csha,
                        max(1, deadline - time.time()), InferenceOnlyMode)
    base_path = final / "base_generations.jsonl"
    base_rows = read_rows(base_path)
    validate_outputs(base_rows, fixtures, contract, csha, "base_before_training")
    atomic(final / "base_generation_provenance.json", {"model": MODEL, "revision": REVISION,
           "fresh_base": True, "adapter_loaded": False, "locked_test_sha256": locked_sha,
           "contract_sha256": csha, "outputs_sha256": sha(base_path), "output_rows": len(base_rows)})

    selected_by_id = {row["fixture_id"]: {**row, "selected_protocol": "inference_contract",
                                          "source_output_sha256": sha(base_path)} for row in base_rows}
    fewshot_outputs = {}
    if fewshot_modes:
        F = load(root / "fewshot_contract.py", "locked_final_fewshot_contract")
        selected_fixtures = [fixture for fixture in fixtures
                             if I.MODE_MAP[fixture["mode"]] in fewshot_modes]
        fewshot_contract, fewshot_csha = F.eval_contract(
            selected_fixtures, tokenizer, fixture_sha256=locked_sha,
            frozen_fixture_ids=[fixture["id"] for fixture in fixtures])
        fewshot_dir = final / "fewshot_selected"
        persist_fewshot_contract(fewshot_dir, fewshot_contract, fewshot_csha)
        F.generate_fixtures(model, tokenizer, selected_fixtures, fewshot_dir,
                            "fewshot_selected_after_base_review", fewshot_contract,
                            fewshot_csha, max(1, deadline - time.time()), InferenceOnlyMode)
        fewshot_path = fewshot_dir / "generations.jsonl"
        fewshot_outputs = read_rows(fewshot_path)
        validate_fewshot_outputs(fewshot_outputs, selected_fixtures, fewshot_contract,
                                 fewshot_csha, [fixture["id"] for fixture in fixtures], locked_sha)
        for row in fewshot_outputs:
            selected_by_id[row["fixture_id"]] = {**row, "selected_protocol": "fewshot_contract",
                                                   "source_output_sha256": sha(fewshot_path)}
        atomic(final / "fewshot_generation_provenance.json", {
            "module_sha256": sha(root / "fewshot_contract.py"),
            "bank_sha256": mode_context["bank_sha256"],
            "contract_sha256": fewshot_csha,
            "full_fixture_sha256": locked_sha,
            "active_fixture_ids": [fixture["id"] for fixture in selected_fixtures],
            "frozen_fixture_ids": [fixture["id"] for fixture in fixtures],
            "outputs_sha256": sha(fewshot_path), "output_rows": len(fewshot_outputs),
            "training_performed": False, "identical_prompt_claim": False})

    if selection["selected_kind"] == "trained_adapter":
        from peft import PeftModel, get_peft_model_state_dict
        from peft.utils.save_and_load import load_peft_weights
        generation = inside(root / "training", selection["best"]["generation"])
        model = PeftModel.from_pretrained(model, str(generation), is_trainable=False)
        expected = load_peft_weights(str(generation), device="cpu")
        actual = get_peft_model_state_dict(model)
        if set(actual) != set(expected):
            raise ValueError("Loaded adapter key set differs from selected checkpoint")
        for key, tensor in actual.items():
            wanted = expected[key].to(device="cpu", dtype=tensor.dtype)
            if tensor.shape != wanted.shape or not torch.equal(tensor.detach().cpu(), wanted):
                raise ValueError("Loaded adapter tensors differ from selected checkpoint")
        del expected, actual
        I.generate_fixtures(model, tokenizer, fixtures, final, "adapter_after_training", contract, csha,
                            max(1, deadline - time.time()), InferenceOnlyMode)
        selected_path = final / "adapter_generations.jsonl"
        selected_rows = read_rows(selected_path)
        validate_outputs(selected_rows, fixtures, contract, csha, "adapter_after_training")
        selected_by_id = {row["fixture_id"]: {**row, "selected_protocol": "inference_contract",
                                               "source_output_sha256": sha(selected_path)} for row in selected_rows}
        reused_base = False
    else:
        selected_rows = [selected_by_id[fixture["id"]] for fixture in fixtures]
        if fewshot_modes:
            selected_path = final / "selected_generations.jsonl"
            write_jsonl(selected_path, selected_rows)
            reused_base = False
        else:
            selected_path, selected_rows, reused_base = base_path, base_rows, True
    atomic(final / "selected_output_reference.json", {"selected_kind": selection["selected_kind"],
           "file": selected_path.name, "sha256": sha(selected_path), "outputs": len(selected_rows),
           "reuses_exact_fresh_base_outputs": reused_base,
           "fewshot_modes": sorted(fewshot_modes), "fewshot_rows": len(fewshot_outputs),
           "duplicate_selected_generation_performed": False})
    for name, digest in input_hashes.items():
        if sha(root / name) != digest:
            raise ValueError("Frozen selection/input changed during evaluation: " + name)
    for name, digest in selection["evidence_hashes"].items():
        if sha(root / name) != digest:
            raise ValueError("Reviewed dev evidence or old checkpoint changed during evaluation: " + name)
    for name, digest in mode_context["evidence_hashes"].items():
        if sha(root / name) != digest:
            raise ValueError("Few-shot dev selection/source evidence changed during evaluation: " + name)
    outputs = {p.relative_to(final).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size}
               for p in final.rglob("*") if p.is_file() and p.name != "complete.json" and not p.name.endswith(".partial.jsonl")}
    atomic(final / "complete.json", {"schema": SCHEMA, "complete": True,
           "completed_unix": time.time(), "deadline_unix": deadline, "owner_hard_deadline_unix": scope["hard_deadline_unix"],
           "locked_test_sha256": locked_sha, "fixture_count": len(fixtures), "contract_sha256": csha,
           "selected_kind": selection["selected_kind"], "selection_before_test": {k: v for k, v in selection.items() if k != "base_rows"},
           "mode_context_selection": {k: v for k, v in mode_context.items() if k != "evidence_hashes"},
           "input_hashes": input_hashes, "packages": packages, "base_outputs": len(base_rows),
           "selected_outputs": len(selected_rows), "selected_file": selected_path.name,
           "selected_reuses_base_outputs": reused_base, "fewshot_outputs": len(fewshot_outputs),
           "fewshot_modes": sorted(fewshot_modes), "identical_prompt_claim_for_fewshot": False,
           "files": outputs, "test_run_count": 1,
           "selection_changed": False, "training_performed": False, "optimizer_loaded": False,
           "semantic_results_reviewed": False, "human_certification": False, "production_approval": False,
           "full_corpus_test_independence": "UNPROVEN"})


if __name__ == "__main__":
    main()
