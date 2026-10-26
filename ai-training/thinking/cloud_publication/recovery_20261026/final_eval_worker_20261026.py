"""One-shot sealed native15 matched evaluation. Run only after eligible dev gate and run completion."""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, random, subprocess, sys, time
from datetime import datetime, timezone

LOCKED_NAME = "native_locked15.jsonl"
LOCKED_SHA256 = "0526ec69b5b1730376835c2961d32c79c187f6d1d0fe3057f2d98358b71674f7"
MODEL = "Qwen/Qwen3-1.7B"
REVISION = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
HARD_STOP_UTC = "2026-10-26T11:14:18+00:00"
MAX_EVALUATION_SECONDS = 600
SEED = 20261024
CODE_PINS = {
    "recovery_worker_20261026.py": "B618F2D961DD0D342F006A8B07ABE39268962FC0BDCAB43622C425EE2BF67D4F".lower(),
    "native_backend_20261026.py": "66AA1473BB6835497FB59B16AB0C76E2A609EEC0358D9B7CD03F2662E3F3A046".lower(),
    "recovery_policy_20261026.py": "648A6A8F48DED0BF7CB2615451B895E9B3A7D72BFDD294430EC58CE4029384FD".lower(),
    "inference_contract.py": "a8398e1c6a414aa0c9d343ebaa737f7e744f6892b8298497c317ea83927a0642",
    "conditional_behavior_renderer.py": "78b4a5c9cfff2e33fc7610461ecab6f57447c079205b62668631f2ca4b665982",
    "frozen_training_primitives.py": "d5f4f0bc2df2b9ff8b2999d607f7ab0b773a76e2ececd4cf48bada99ffcc787c",
}

def raw_sha(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def read_json(path: pathlib.Path):
    return json.loads(path.read_bytes())


def read_jsonl(path: pathlib.Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def atomic(path: pathlib.Path, value):
    tmp = path.with_name(path.name + ".pending")
    data = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    with tmp.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)


def require_no_training_worker():
    try:
        import psutil
    except ImportError as exc:
        raise RuntimeError("psutil required to prove the training worker exited") from exc
    active = []
    for proc in psutil.process_iter(["pid", "cmdline"]):
        if proc.info["pid"] == os.getpid():
            continue
        command = " ".join(proc.info.get("cmdline") or [])
        if "recovery_worker_20261026.py" in command:
            active.append({"pid": proc.info["pid"], "cmdline": command[:500]})
    if active:
        raise RuntimeError("Training worker is still active; refusing same-GPU final inference")


def verify_export_zip(artifact_path: pathlib.Path, generation: pathlib.Path,
                      manifest: dict, manifest_sha: str):
    import zipfile
    if not zipfile.is_zipfile(artifact_path):
        raise ValueError("Selected adapter export is not a valid ZIP")
    expected=set(manifest.get("files",{}))-{"resume_state.pt"}
    expected.add("generation_manifest.json")
    manifest_path=generation/"generation_manifest.json"
    if raw_sha(manifest_path)!=manifest_sha:
        raise ValueError("Generation manifest changed before ZIP verification")
    expected_hashes={name:digest for name,digest in manifest["files"].items() if name!="resume_state.pt"}
    expected_hashes["generation_manifest.json"]=manifest_sha
    expected_sizes={name:size for name,size in manifest.get("file_bytes",{}).items() if name!="resume_state.pt"}
    expected_sizes["generation_manifest.json"]=manifest_path.stat().st_size
    with zipfile.ZipFile(artifact_path) as archive:
        names=archive.namelist()
        if len(names)!=len(set(names)) or set(names)!=expected:
            raise ValueError("Selected ZIP members differ from the immutable generation")
        for name in names:
            if pathlib.PurePosixPath(name).name!=name:
                raise ValueError("Unsafe selected ZIP member name")
            data=archive.read(name)
            if hashlib.sha256(data).hexdigest()!=expected_hashes[name] or len(data)!=expected_sizes.get(name):
                raise ValueError("Selected ZIP member differs from immutable generation: "+name)


def verify_gate_and_run(root: pathlib.Path):
    training = root / "training"
    config = read_json(training / "run_config.json")
    progress = read_json(training / "progress.json")
    complete = read_json(training / "run_complete.json")
    best = read_json(training / "best.json")
    if progress.get("state") != "COMPLETE" or complete.get("complete") is not True:
        raise ValueError("Training run is not complete")
    if complete.get("budget_satisfied") is not True:
        raise ValueError("Completed run did not satisfy its owner time budget")
    if complete.get("production_approval") is not False or best.get("production_approval") is not False:
        raise ValueError("Unexpected production approval field")
    if config.get("model") != MODEL or config.get("revision") != REVISION:
        raise ValueError("Run model/revision differs from frozen evaluator")
    if best.get("kind") != "trained_adapter" or best.get("semantic_review_pending") is True:
        raise ValueError("No trained candidate selected")
    if complete.get("best") != best or complete.get("selected_artifact", {}).get("selection_evidence") != best:
        raise ValueError("run_complete does not bind the current selected-best pointer")
    artifact = complete.get("selected_artifact", {})
    artifact_rel = pathlib.PurePosixPath(artifact.get("path", ""))
    if artifact.get("kind") != "trained_adapter" or artifact_rel.is_absolute() or ".." in artifact_rel.parts or artifact_rel.suffix.lower() != ".zip":
        raise ValueError("run_complete lacks a safe selected-adapter export")
    artifact_path = training / pathlib.Path(*artifact_rel.parts)
    if not artifact_path.is_file() or raw_sha(artifact_path) != artifact.get("sha256") or artifact_path.stat().st_size != artifact.get("bytes"):
        raise ValueError("Selected adapter export is missing or fails its run_complete hash")
    generation_name = best.get("generation")
    if not isinstance(generation_name, str) or pathlib.PurePosixPath(generation_name).name != generation_name:
        raise ValueError("Unsafe or missing selected generation name")
    generation = training / generation_name
    manifest_path = generation / "generation_manifest.json"
    manifest_sha = raw_sha(manifest_path)
    if manifest_sha != best.get("manifest_sha256"):
        raise ValueError("Selected generation manifest hash mismatch")
    manifest = read_json(manifest_path)
    if manifest.get("complete") is not True:
        raise ValueError("Selected checkpoint generation is incomplete")
    if not manifest.get("files") or not manifest.get("file_bytes"):
        raise ValueError("Selected generation manifest lacks member hashes/sizes")
    for name, digest in manifest.get("files", {}).items():
        if pathlib.PurePosixPath(name).name != name or raw_sha(generation / name) != digest:
            raise ValueError("Checkpoint member hash mismatch: " + str(name))
        if (generation / name).stat().st_size != manifest.get("file_bytes", {}).get(name):
            raise ValueError("Checkpoint member size mismatch: " + str(name))
    verify_export_zip(artifact_path,generation,manifest,manifest_sha)

    step = best.get("step")
    if type(step) is not int or step <= 0:
        raise ValueError("Selected candidate lacks a trained step")
    eval_dir = training / f"eval_step_{step:06d}"
    eval_bindings_path = eval_dir / "eval_bindings.json"
    eval_bindings = read_json(eval_bindings_path)
    if best.get("bindings") != eval_bindings:
        raise ValueError("Selected best does not bind the exact stored development evaluation")
    if eval_bindings.get("generation_manifest_sha256") != manifest_sha:
        raise ValueError("Stored development evaluation binds a different checkpoint")
    gate_path = training / f"gate_step_{step:06d}.json"
    if raw_sha(gate_path) != best.get("gate_sha256") or gate_path.name != best.get("gate_file"):
        raise ValueError("Selected development gate hash mismatch")
    gate = read_json(gate_path)
    import recovery_policy_20261026 as policy
    policy.validate_gate(gate, step, eval_bindings)
    summary = policy.summarize_decisions(gate.get("decisions"))
    if gate.get("decision") not in ("STOP", "CONTINUE_IMPROVED") or summary.get("candidate_eligible") is not True:
        raise ValueError("Selected checkpoint lacks an eligible development gate")
    if best.get("selection_key") != list(policy.selection_key(summary, "candidate")):
        raise ValueError("Selected checkpoint score differs from development gate")
    if gate.get("generation_manifest_sha256") != manifest_sha:
        raise ValueError("Development gate binds a different selected generation")
    return config, best, generation, manifest_sha, gate_path, raw_sha(gate_path)


def verify_code_pins(root: pathlib.Path, config: dict):
    actual = {name: raw_sha(root / name) for name in CODE_PINS}
    if actual != CODE_PINS:
        raise ValueError("Frozen active code hash mismatch")
    if config.get("worker_sha256") != CODE_PINS["recovery_worker_20261026.py"]:
        raise ValueError("Run config worker hash differs from the pinned worker")
    if config.get("policy_sha256") != CODE_PINS["recovery_policy_20261026.py"]:
        raise ValueError("Run config policy hash differs from the pinned policy")
    if config.get("renderer_sha256") != CODE_PINS["conditional_behavior_renderer.py"]:
        raise ValueError("Run config renderer hash differs from the pinned conditional renderer")
    if config.get("worker_sha256") != actual["recovery_worker_20261026.py"]:
        raise ValueError("Run config worker hash differs from the pinned new worker")
    if config.get("policy_sha256") != actual["recovery_policy_20261026.py"]:
        raise ValueError("Run config policy hash differs from the pinned new policy")
    if config.get("renderer_sha256") != actual["conditional_behavior_renderer.py"]:
        raise ValueError("Run config renderer hash differs from the pinned renderer")
    if config.get("branch") != "recovery_20261026" or config.get("fresh_base_required") is not True or config.get("previous_adapters_loaded") is not False:
        raise ValueError("Run config does not identify the approved fresh-base branch")
    return actual


def verify_scope_binding(root: pathlib.Path, config: dict):
    scope_path=root/"owner_run_scope.json"
    binding_path=root/"owner_scope_binding_v2.json"
    scope=read_json(scope_path);binding=read_json(binding_path)
    if set(binding)!={"original_scope_sha256","dev_sha256","locked_test_sha256","repair_reason"}:
        raise ValueError("Owner scope binding fields differ from expected schema")
    if raw_sha(scope_path)!=binding["original_scope_sha256"]:
        raise ValueError("Owner scope changed after binding")
    if config.get("hard_deadline_unix")!=scope.get("hard_deadline_unix") or config.get("reserve_seconds")!=scope.get("reserve_seconds"):
        raise ValueError("Run deadline/reserve differs from the current owner scope")
    if config.get("dev_sha256")!=binding["dev_sha256"] or binding["locked_test_sha256"]!=LOCKED_SHA256:
        raise ValueError("Run dev or locked-test binding differs from evaluator scope")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    expected_venv = (root / "venv").resolve()
    if pathlib.Path(sys.prefix).resolve() != expected_venv:
        raise ValueError("Must run in this cloud run's frozen venv")
    from importlib.metadata import version
    package_pins = {"transformers": "5.20.2", "peft": "0.21.2",
                    "bitsandbytes": "0.50.2", "accelerate": "1.15.0"}
    actual_versions = {name: version(name) for name in package_pins}
    if any(actual_versions[name].split("+")[0] != pin for name, pin in package_pins.items()):
        raise ValueError("Inference package versions differ from the run pins")
    config, best, generation, manifest_sha, gate_path, gate_sha = verify_gate_and_run(root)
    code_hashes = verify_code_pins(root, config)
    best_sha = raw_sha(root / "training" / "best.json")
    require_no_training_worker()
    verify_scope_binding(root, config)
    absolute_deadline = min(datetime.fromisoformat(HARD_STOP_UTC).timestamp(), float(config["hard_deadline_unix"]))
    start_now=time.time()
    if start_now >= absolute_deadline:
        raise TimeoutError("Final inference deadline has passed")
    if absolute_deadline-start_now < MAX_EVALUATION_SECONDS:
        raise TimeoutError("A full bounded 10-minute matched evaluation window is unavailable")
    hard_stop=min(absolute_deadline,start_now+MAX_EVALUATION_SECONDS)
    final = root / "final_eval"
    final.mkdir(exist_ok=False)  # Permanent one-shot attempt marker; never retry sealed inference.
    started = time.time()
    atomic(final / "attempt_started.json", {
        "schema": "MathVisionKid.conditional_native15_attempt.v1",
        "started_unix": started,
        "deadline_unix": hard_stop,
        "locked_fixture_name": LOCKED_NAME,
        "locked_fixture_raw_sha256_expected": LOCKED_SHA256,
        "selected_generation": generation.name,
        "selected_generation_manifest_sha256": manifest_sha,
        "development_gate": gate_path.name,
        "development_gate_sha256": gate_sha,
        "training_performed": False,
        "selection_changes_allowed": False,
        "selected_best_sha256": best_sha,
        "run_once": True
    })

    fixture_path = root / LOCKED_NAME
    fixture_raw_sha = raw_sha(fixture_path)
    if fixture_raw_sha != LOCKED_SHA256:
        raise ValueError("Sealed fixture raw SHA mismatch; no fixture rows consumed")
    fixtures = read_jsonl(fixture_path)
    if len(fixtures) != 15 or len({f.get("id") for f in fixtures}) != 15:
        raise ValueError("Sealed fixture set must contain exactly 15 unique rows")
    required_modes = {"answer", "hint_no_answer", "student_error", "missing_or_contradictory_info"}
    for row in fixtures:
        if type(row.get("grade")) is not int or row["grade"] not in range(1, 6) or row.get("mode") not in required_modes or not isinstance(row.get("userproblem"), str):
            raise ValueError("Sealed fixture row schema mismatch")

    import torch
    from transformers import BitsAndBytesConfig
    from native_backend_20261026 import NativeBackend
    from inference_contract import eval_contract, generate_fixtures
    from peft import PeftModel, get_peft_model_state_dict
    from peft.utils.save_and_load import load_peft_weights

    if not torch.cuda.is_available() or "t4" not in torch.cuda.get_device_name(0).lower():
        raise RuntimeError("Expected the same free T4 inference environment")
    random.seed(SEED)
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    model, tokenizer = NativeBackend.from_pretrained(
        model_name=MODEL,
        revision=REVISION,
        use_exact_model_name=True,
        max_seq_length=2048,
        dtype=torch.float16,
        load_in_4bit=True,
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True),
        attn_implementation="sdpa")
    artifact_proof = getattr(model, "_mathvisionkid_artifact_proof", None)
    if getattr(model, "_mathvisionkid_artifact_revision", None) != REVISION or not isinstance(artifact_proof, dict):
        raise ValueError("Base model was not loaded from the pinned revision")
    if tokenizer.eos_token_id != 151645 or tokenizer.convert_tokens_to_ids("<|im_end|>") != 151645:
        raise ValueError("Tokenizer end token differs from frozen inference contract")

    contract, contract_sha = eval_contract(fixtures, tokenizer, LOCKED_SHA256)
    if contract.get("fixture_sha256") != LOCKED_SHA256 or contract.get("enable_thinking") is not False:
        raise ValueError("Final contract does not bind sealed fixture or thinking setting")
    atomic(final / "input_bindings.json", {
        "locked_fixture_name": LOCKED_NAME,
        "locked_fixture_raw_sha256": fixture_raw_sha,
        "fixture_count": len(fixtures),
        "fixture_ids": [f["id"] for f in fixtures],
        "run_config_sha256": raw_sha(root / "training" / "run_config.json"),
        "selected_best_sha256": best_sha,
        "selected_generation_manifest_sha256": manifest_sha,
        "development_gate_sha256": gate_sha,
        "active_code_hashes": code_hashes,
        "base_model_artifact_proof": artifact_proof,
        "selection_changed_after_gate": False,
        "training_performed": False
    })
    atomic(final / "evaluation_contract.json", {**contract, "contract_sha256": contract_sha})

    class NativeInference:
        @staticmethod
        def for_inference(target):
            NativeBackend.for_inference(target)
        @staticmethod
        def for_training(target):
            raise RuntimeError("Training is forbidden during final evaluation")

    timeout = hard_stop - time.time() - 30
    if timeout <= 0:
        raise TimeoutError("No bounded final inference time remains")
    generate_fixtures(model, tokenizer, fixtures, final, "base_before_training",
                      contract, contract_sha, timeout / 2, NativeInference)
    base_path = final / "base_generations.jsonl"
    base_rows = read_jsonl(base_path)

    # Attach only the gate-selected immutable checkpoint after fresh-base generation.
    model = PeftModel.from_pretrained(model, str(generation), is_trainable=False)
    expected = load_peft_weights(str(generation), device="cpu")
    actual = get_peft_model_state_dict(model)
    if set(actual) != set(expected):
        raise ValueError("Loaded adapter key set differs from selected checkpoint")
    for key, tensor in actual.items():
        wanted = expected[key].to(device="cpu", dtype=tensor.dtype)
        if tensor.shape != wanted.shape or not torch.equal(tensor.detach().cpu(), wanted):
            raise ValueError("Loaded adapter tensor differs from selected checkpoint")
    del expected, actual
    if time.time() >= hard_stop:
        raise TimeoutError("Final inference deadline reached before candidate generation")
    generate_fixtures(model, tokenizer, fixtures, final, "adapter_after_training",
                      contract, contract_sha, hard_stop - time.time() - 20, NativeInference)
    adapter_path = final / "adapter_generations.jsonl"
    adapter_rows = read_jsonl(adapter_path)
    expected_ids = [f["id"] for f in fixtures]
    for rows, stage in ((base_rows, "base_before_training"), (adapter_rows, "adapter_after_training")):
        if len(rows) != 15 or [r.get("fixture_id") for r in rows] != expected_ids:
            raise ValueError("Generation output fixture IDs/order differ")
        if any(r.get("stage") != stage or r.get("contract_sha256") != contract_sha for r in rows):
            raise ValueError("Generation output does not bind the final contract")
    paired = []
    for fixture, base, candidate in zip(fixtures, base_rows, adapter_rows):
        if base.get("prompt_token_sha256") != candidate.get("prompt_token_sha256") or base.get("seed") != candidate.get("seed"):
            raise ValueError("Base/candidate prompt or seed differs")
        paired.append({"fixture_id": fixture["id"], "grade": fixture["grade"], "mode": fixture["mode"],
                       "base": base, "candidate": candidate})
    paired_path = final / "paired_generations.jsonl"
    with paired_path.open("xb", encoding="utf-8") as stream:
        for row in paired:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    if (raw_sha(fixture_path) != LOCKED_SHA256
            or raw_sha(generation / "generation_manifest.json") != manifest_sha
            or raw_sha(root / "training" / "best.json") != best_sha
            or read_json(root / "training" / "best.json") != best
            or time.time() >= hard_stop):
        raise ValueError("Sealed fixture or selected checkpoint changed during inference")
    names = ["attempt_started.json", "input_bindings.json", "evaluation_contract.json",
             "base_generations.jsonl", "base_generation_provenance.json",
             "adapter_generations.jsonl", "adapter_generation_provenance.json", "paired_generations.jsonl"]
    files = {name: {"sha256": raw_sha(final / name), "bytes": (final / name).stat().st_size} for name in names}
    atomic(final / "complete.json", {
        "schema": "MathVisionKid.conditional_native15_complete.v1",
        "complete": True,
        "completed_unix": time.time(),
        "deadline_unix": hard_stop,
        "budget_satisfied": time.time() < hard_stop,
        "locked_fixture_raw_sha256": LOCKED_SHA256,
        "fixture_count": 15,
        "fixture_ids": expected_ids,
        "contract_sha256": contract_sha,
        "base_outputs_sha256": raw_sha(base_path),
        "adapter_outputs_sha256": raw_sha(adapter_path),
        "paired_outputs_sha256": raw_sha(paired_path),
        "selected_generation": generation.name,
        "selected_generation_manifest_sha256": manifest_sha,
        "development_gate": gate_path.name,
        "development_gate_sha256": gate_sha,
        "model": MODEL,
        "revision": REVISION,
        "base_model_artifact_proof": artifact_proof,
        "packages": {name: __import__("importlib.metadata", fromlist=["version"]).version(name)
                     for name in ("torch", "transformers", "peft", "bitsandbytes", "accelerate")},
        "files": files,
        "training_performed": False,
        "selection_changed": False,
        "semantic_review_complete": False,
        "production_approval": False
    })
    print(json.dumps({"complete": True, "contract_sha256": contract_sha,
                      "locked_fixture_sha256": LOCKED_SHA256,
                      "selected_generation_manifest_sha256": manifest_sha,
                      "paired_outputs": str(paired_path), "production_approval": False}))


if __name__ == "__main__":
    main()
