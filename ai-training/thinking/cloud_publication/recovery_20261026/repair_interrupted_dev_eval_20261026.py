"""One-shot, hash-bound repair for an interrupted step-100 development eval.

Preparation code only. It is not run by this task. It never updates weights,
repeats a completed fixture, edits the original partial, or reads locked tests.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import re
import sys
import time


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def read_json(path: Path):
    return json.loads(path.read_bytes())


def read_jsonl_bytes(raw: bytes):
    if raw and not raw.endswith(b"\n"):
        raise ValueError("JSONL evidence ends in a partial line")
    return [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]


def read_jsonl(path: Path):
    return read_jsonl_bytes(path.read_bytes())


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load local module {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def atomic_exclusive(path: Path, raw: bytes):
    """Atomically create a file without replacing any prior evidence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".{os.getpid()}.pending")
    if path.exists():
        raise FileExistsError(f"Refuse to overwrite {path}")
    with temp.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def atomic_json_exclusive(path: Path, doc):
    atomic_exclusive(path, (json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"))


def validate_exit_proof(root: Path, config: dict, proof_path: Path):
    proof = read_json(proof_path)
    error_path = root / "training" / "error.json"
    if not error_path.is_file():
        raise FileNotFoundError("Original worker error receipt is missing")
    error = read_json(error_path)
    if (proof.get("worker_exit_code") != 1 or proof.get("worker_alive") is not False
            or proof.get("worker_sha256") != config.get("worker_sha256")
            or proof.get("error_sha256") != sha(error_path)
            or "TimeoutError" not in repr(error.get("error")) + repr(error.get("traceback"))):
        raise ValueError("Repair requires a fresh process-exit proof bound to the original TimeoutError")
    return proof, error_path


def validate_prefix(rows, fixtures, contract, csha, stage="adapter_after_training"):
    ids = [f["id"] for f in fixtures]
    if len(ids) != 30 or len(set(ids)) != 30:
        raise ValueError("Expected exactly 30 unique frozen development fixture IDs")
    if not isinstance(rows, list) or not rows or len(rows) >= len(ids):
        raise ValueError("Expected a nonempty incomplete prefix shorter than the full fixture list")
    expected_ids = ids[:len(rows)]
    if [r.get("fixture_id") for r in rows] != expected_ids:
        raise ValueError("Original partial is not the exact contiguous fixture prefix")
    by_id = {f["id"]: f for f in fixtures}
    for row in rows:
        f = by_id[row["fixture_id"]]
        seed = (20261024 + int(sha_bytes(f["id"].encode())[:8], 16)) % (2**31)
        if ((row.get("grade"), row.get("mode"), row.get("stage")) != (f["grade"], f["mode"], stage)
                or row.get("contract_sha256") != csha
                or row.get("prompt_token_sha256") != contract["prompt_token_sha256"].get(f["id"])
                or row.get("max_new_tokens") != contract["decoding"]["max_new_tokens"]
                or row.get("seed") != seed
                or type(row.get("timed_out")) is not bool
                or type(row.get("ended_eos")) is not bool
                or row.get("possibly_truncated") is not (not row.get("ended_eos"))):
            raise ValueError("Original partial row differs from frozen contract/protocol: " + f["id"])
    return ids[len(rows):]


def validate_suffix(rows, fixtures, remaining_ids, contract, csha):
    ids = [f["id"] for f in fixtures]
    by_id = {f["id"]: f for f in fixtures}
    if [r.get("fixture_id") for r in rows] != list(remaining_ids):
        raise ValueError("Repair fragment must cover each remaining fixture exactly once and in order")
    for row in rows:
        f = by_id[row["fixture_id"]]
        seed = (20261024 + int(sha_bytes(f["id"].encode())[:8], 16)) % (2**31)
        if ((row.get("grade"), row.get("mode"), row.get("stage")) != (f["grade"], f["mode"], "adapter_after_training")
                or row.get("contract_sha256") != csha
                or row.get("prompt_token_sha256") != contract["prompt_token_sha256"].get(f["id"])
                or row.get("max_new_tokens") != contract["decoding"]["max_new_tokens"]
                or row.get("seed") != seed
                or type(row.get("timed_out")) is not bool
                or type(row.get("ended_eos")) is not bool
                or row.get("possibly_truncated") is not (not row.get("ended_eos"))):
            raise ValueError("Repair fragment row differs from frozen contract/protocol: " + f["id"])


def prepare_eval_repair(root: Path, exit_proof_path: Path):
    """Restore base+CP100 for inference only, then generate unsaved suffix rows."""
    root = root.resolve()
    training = root / "training"
    cfg = read_json(training / "run_config.json")
    if cfg.get("branch") != "recovery_20261026" or cfg.get("fresh_base_required") is not True or cfg.get("previous_adapters_loaded") is not False:
        raise ValueError("Wrong run branch or non-fresh-base config")
    if (training / "run_complete.json").exists() or (training / "gate_step_000100.json").exists():
        raise ValueError("Run is already completed/gated; repair may only precede root review")
    worker_path = root / "recovery_worker_20261026.py"
    backend_path = root / "native_backend_20261026.py"
    contract_path = training / "evaluation_contract.json"
    fixture_path = root / "new_validation_candidates.jsonl"
    baseline_path = root / "baseline_semantic_review_frozen.json"
    step_dir = training / "eval_step_000100"
    partial_path = step_dir / "adapter_generations.partial.jsonl"
    for path in (worker_path, backend_path, contract_path, fixture_path, baseline_path, partial_path):
        if not path.is_file():
            raise FileNotFoundError(f"Required interrupted-evaluation evidence missing: {path.name}")
    if cfg.get("worker_sha256") != sha(worker_path):
        raise ValueError("Run-config worker hash differs from active worker bytes")
    if cfg.get("renderer_sha256") != sha(root / "conditional_behavior_renderer.py"):
        raise ValueError("Run-config renderer hash differs from active renderer")
    if cfg.get("policy_sha256") != sha(root / "recovery_policy_20261026.py"):
        raise ValueError("Run-config policy hash differs from active policy")
    if cfg.get("dev_sha256") != sha(fixture_path):
        raise ValueError("Development fixture bytes differ from run config")
    baseline = read_json(baseline_path)
    if baseline.get("fixture_raw_sha256") != sha(fixture_path) or baseline.get("human_review_claimed") is not False:
        raise ValueError("Frozen baseline does not bind current development fixtures")
    contract_raw_sha = sha(contract_path)
    if contract_raw_sha != baseline.get("contract_sha256"):
        raise ValueError("Raw evaluation-contract bytes differ from frozen baseline")
    contract = read_json(contract_path)
    csha = hashlib.sha256(canonical(contract).encode("utf-8")).hexdigest()
    if csha != cfg.get("contract_sha256"):
        raise ValueError("Canonical contract digest differs from run config")
    fixtures = read_jsonl(fixture_path)
    if len(fixtures) != 30 or contract.get("fixture_ids") != [f["id"] for f in fixtures]:
        raise ValueError("Contract fixture order differs from the frozen 30-fixture list")

    proof, error_path = validate_exit_proof(root, cfg, exit_proof_path)
    original_partial = partial_path.read_bytes()
    prefix_rows = read_jsonl_bytes(original_partial)
    remaining_ids = validate_prefix(prefix_rows, fixtures, contract, csha)
    if not remaining_ids:
        raise ValueError("No remaining fixture IDs; do not regenerate any completed fixture")

    base_dir = training / "eval_step_000000"
    base_path = base_dir / "base_generations.jsonl"
    base_receipt_path = base_dir / "eval_bindings.json"
    base_receipt = read_json(base_receipt_path)
    if (sha(base_path) != baseline.get("base_output_raw_sha256")
            or sha(base_path) != base_receipt.get("base_output_sha256")
            or base_receipt.get("dev_sha256") != cfg.get("dev_sha256")
            or base_receipt.get("contract_sha256") != csha
            or base_receipt.get("source_plan_sha256") != cfg.get("source_plan_sha256")
            or base_receipt.get("fixture_ids") != [f["id"] for f in fixtures]):
        raise ValueError("Fresh base evidence no longer matches its frozen bindings")
    if len(read_jsonl(base_path)) != 30:
        raise ValueError("Fresh base generation is not complete; this repair never re-runs it")

    generations = [g for g in training.glob("generation_step_000100_rows_*")
                   if (g / "generation_manifest.json").is_file()]
    if len(generations) != 1:
        raise ValueError("Expected exactly one immutable step-100 checkpoint generation")
    generation = generations[0]
    if (training / "best.json").exists() and read_json(training / "best.json").get("kind") != "untrained_base":
        raise ValueError("No prior gate may have selected an adapter before this repaired review")

    repair_dir = step_dir / "repair_attempt_001"
    repair_dir.mkdir(exist_ok=False)
    prefix_copy = repair_dir / "original_adapter_partial.jsonl"
    atomic_exclusive(prefix_copy, original_partial)
    manifest = {
        "schema": "MathVisionKid.interrupted_dev_eval_repair.v1",
        "phase": "SUFFIX_GENERATION_PENDING",
        "original_error_sha256": sha(error_path),
        "worker_exit_proof_sha256": sha(exit_proof_path),
        "worker_sha256": sha(worker_path), "backend_sha256": sha(backend_path),
        "run_config_sha256": sha(training / "run_config.json"),
        "fixture_sha256": sha(fixture_path), "contract_raw_sha256": contract_raw_sha,
        "contract_canonical_sha256": csha, "source_plan_sha256": cfg["source_plan_sha256"],
        "base_output_sha256": sha(base_path),
        "generation": generation.name,
        "generation_manifest_sha256": sha(generation / "generation_manifest.json"),
        "original_partial_path": str(partial_path.relative_to(root)),
        "original_partial_sha256": sha_bytes(original_partial),
        "preserved_partial_copy_sha256": sha(prefix_copy),
        "completed_prefix_ids": [r["fixture_id"] for r in prefix_rows],
        "prefix_rows_with_timeout_flag_still_counted_once": [r["fixture_id"] for r in prefix_rows if r["timed_out"]],
        "remaining_ids_to_generate_once": remaining_ids,
        "additional_optimizer_updates": 0,
        "base_evaluation_repeated": False,
        "sealed_final_read": False,
        "human_review_claimed": False,
    }
    atomic_json_exclusive(repair_dir / "repair_manifest.json", manifest)

    # Heavy imports are confined to explicit execution after the owner/root verifies timeout evidence.
    import torch
    import bitsandbytes  # noqa: F401
    from transformers import BitsAndBytesConfig, GenerationConfig
    from peft import PeftModel, get_peft_model_state_dict, load_peft_weights, prepare_model_for_kbit_training

    if not torch.cuda.is_available() or "t4" not in torch.cuda.get_device_name(0).lower():
        raise RuntimeError("Expected the same free T4 runtime")
    if cfg.get("model") != "Qwen/Qwen3-1.7B" or cfg.get("revision") != "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e":
        raise ValueError("Model/revision differs from the frozen run")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    backend = load_module(backend_path, "eval_repair_native_backend")
    inference = load_module(root / "inference_contract.py", "eval_repair_inference_contract")
    if sha(root / "inference_contract.py") != "a8398e1c6a414aa0c9d343ebaa737f7e744f6892b8298497c317ea83927a0642":
        raise ValueError("Inference contract code is not the root-approved pinned bytes")

    model, tok = backend.NativeBackend.from_pretrained(
        model_name=cfg["model"], revision=cfg["revision"], use_exact_model_name=True,
        max_seq_length=cfg["max_sequence"], dtype=torch.float16, load_in_4bit=True,
        quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True),
        attn_implementation="sdpa")
    if tok.eos_token_id != contract["decoding"]["eos_token_id"] or model._mathvisionkid_artifact_revision != cfg["revision"]:
        raise ValueError("Restored base model/tokenizer differs from run binding")

    # Match the original candidate path's bitsandbytes preparation/casts, but do not enable GC or training.
    prepared = prepare_model_for_kbit_training(model, use_gradient_checkpointing=False)
    nonquant_dtypes = {name: str(param.dtype) for name, param in prepared.named_parameters()
                       if not getattr(param, "is_quantized", False) and not param.__class__.__name__.lower().startswith("params4bit")}
    atomic_json_exclusive(repair_dir / "precision_preparation.json", {
        "prepare_model_for_kbit_training_called": True,
        "use_gradient_checkpointing": False,
        "purpose": "Match original QLoRA nonquantized FP32 preparation for inference-only adapter restore; no gradient or optimizer.",
        "nonquantized_parameter_dtype_sha256": sha_bytes(canonical(nonquant_dtypes).encode("utf-8")),
        "nonquantized_parameter_count": len(nonquant_dtypes),
        "parameter_dtypes": nonquant_dtypes,
        "lora_weights_loaded_from_generation": generation.name,
        "weights_updated": False,
    })
    model = PeftModel.from_pretrained(prepared, str(generation), is_trainable=False)
    expected = load_peft_weights(str(generation), device="cpu")
    actual = get_peft_model_state_dict(model)
    if set(actual) != set(expected):
        raise ValueError("Restored adapter keys differ from immutable CP100")
    for key, tensor in actual.items():
        wanted = expected[key].to(device="cpu", dtype=tensor.dtype)
        if tensor.shape != wanted.shape or not torch.equal(tensor.detach().cpu(), wanted):
            raise ValueError("Restored adapter tensor differs from immutable CP100: " + key)
    del expected, actual
    backend.NativeBackend.for_inference(model)
    model.eval()

    fragment = repair_dir / "adapter_remaining_fragment.jsonl"
    if fragment.exists():
        raise FileExistsError("Refuse to regenerate an existing suffix fragment")
    cutoff = min(time.monotonic() + 900.0, float(cfg["hard_deadline_unix"]) - time.time() + time.monotonic() - 600.0)
    for fid in remaining_ids:
        left = cutoff - time.monotonic()
        if left <= 1:
            raise TimeoutError("Repair window exhausted; preserve this one-shot fragment and do not retry IDs")
        fixture = next(f for f in fixtures if f["id"] == fid)
        seed = (20261024 + int(sha_bytes(fid.encode())[:8], 16)) % (2**31)
        torch.manual_seed(seed); torch.cuda.manual_seed_all(seed); random.seed(seed)
        messages = inference.messages(fixture)
        inputs = tok.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
            enable_thinking=False, return_tensors="pt", return_dict=True).to("cuda")
        prompt_sha = sha_bytes(canonical(inputs["input_ids"][0].tolist()).encode("utf-8"))
        if prompt_sha != contract["prompt_token_sha256"][fid]:
            raise ValueError("Prompt tokens differ from the frozen contract: " + fid)
        tick = time.monotonic()
        with torch.inference_mode():
            output = model.generate(**inputs, generation_config=GenerationConfig(**contract["decoding"]), max_time=left)
        tokens = output[0, inputs["input_ids"].shape[1]:]
        ended_eos = bool(len(tokens) and int(tokens[-1]) == contract["decoding"]["eos_token_id"])
        row = {"fixture_id": fid, "grade": fixture["grade"], "mode": fixture["mode"],
               "model_mode": contract["mode_map"][fixture["mode"]], "stage": "adapter_after_training",
               "contract_sha256": csha, "prompt_token_sha256": prompt_sha,
               "max_new_tokens": contract["decoding"]["max_new_tokens"], "generated_tokens": len(tokens),
               "output": tok.decode(tokens, skip_special_tokens=True).strip(), "ended_eos": ended_eos,
               "possibly_truncated": not ended_eos, "timed_out": time.monotonic() >= cutoff,
               "seed": seed, "generation_seconds": time.monotonic() - tick,
               "repair_attempt": 1, "weights_generation": generation.name}
        with fragment.open("ab") as stream:
            stream.write((json.dumps(row, ensure_ascii=False) + "\n").encode("utf-8"))
            stream.flush(); os.fsync(stream.fileno())

    suffix_bytes = fragment.read_bytes()
    suffix_rows = read_jsonl_bytes(suffix_bytes)
    validate_suffix(suffix_rows, fixtures, remaining_ids, contract, csha)
    combined_bytes = original_partial + suffix_bytes
    combined_rows = read_jsonl_bytes(combined_bytes)
    if [r["fixture_id"] for r in combined_rows] != [f["id"] for f in fixtures]:
        raise ValueError("Combined adapter bytes do not cover exact 30-fixture order")
    out_path = step_dir / "adapter_generations.jsonl"
    bindings = {"dev_sha256": cfg["dev_sha256"], "contract_sha256": csha,
        "source_plan_sha256": cfg["source_plan_sha256"], "base_output_sha256": sha(base_path),
        "generation_manifest_sha256": sha(generation / "generation_manifest.json"),
        "fixture_ids": [f["id"] for f in fixtures], "final_stage": False,
        "adapter_output_sha256": sha_bytes(combined_bytes)}
    worker = load_module(worker_path, "eval_repair_worker")
    fixed = {k: v for k, v in bindings.items() if k != "adapter_output_sha256"}
    receipt_path = step_dir / "eval_bindings.json"
    if receipt_path.exists() or out_path.exists() or (step_dir / "adapter_generation_provenance.json").exists():
        raise FileExistsError("Refuse to overwrite any existing completed evaluation artifact")
    # Verify in a separate staging directory so a failed worker verifier cannot
    # leave a falsely completed adapter output or receipt in the live eval dir.
    verify_dir = repair_dir / "worker_verify_stage"
    verify_dir.mkdir(exist_ok=False)
    atomic_exclusive(verify_dir / "adapter_generations.jsonl", combined_bytes)
    atomic_json_exclusive(verify_dir / "eval_bindings.json", bindings)
    if worker.verify_eval_evidence(verify_dir, fixed, fixtures, contract) != bindings:
        raise ValueError("Branch worker rejects repaired output/evaluation binding")

    atomic_exclusive(out_path, combined_bytes)
    atomic_json_exclusive(receipt_path, bindings)
    proof_path = step_dir / "adapter_generation_provenance.json"
    atomic_json_exclusive(proof_path, {"schema": "MathVisionKid.repaired_eval_output.v1",
        "stage": "adapter_after_training", "contract_sha256": csha,
        "generation_manifest_sha256": bindings["generation_manifest_sha256"],
        "original_partial_sha256": sha_bytes(original_partial),
        "repair_fragment_sha256": sha(fragment), "merged_output_sha256": sha(out_path),
        "completed_fixture_ids": [f["id"] for f in fixtures],
        "additional_optimizer_updates": 0, "base_evaluation_repeated": False,
        "sealed_final_read": False, "human_review_claimed": False})
    manifest["phase"] = "COMPLETE_AWAITING_ROOT_SEMANTIC_REVIEW"
    manifest["repair_fragment_sha256"] = sha(fragment)
    manifest["merged_output_sha256"] = sha(out_path)
    manifest["eval_binding_sha256"] = sha(receipt_path)
    atomic_json_exclusive(repair_dir / "repair_complete.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="Exact staged 2026-10-26 run root")
    parser.add_argument("--exit-proof", type=Path, required=True, help="Fresh CPU-captured worker exit-1/TimeoutError proof")
    args = parser.parse_args()
    result = prepare_eval_repair(args.root, args.exit_proof)
    print(json.dumps({"evaluation_repaired": True, "phase": result["phase"],
                      "completed_prefix_count": len(result["completed_prefix_ids"]),
                      "repaired_suffix_count": len(result["remaining_ids_to_generate_once"]),
                      "additional_optimizer_updates": 0, "gate_created": False,
                      "training_complete_claimed": False}))


if __name__ == "__main__":
    main()
