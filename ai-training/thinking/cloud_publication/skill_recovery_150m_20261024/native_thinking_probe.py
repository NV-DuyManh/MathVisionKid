"""Base-only native-thinking probe on authorized dev, then separately gated new final15."""
from __future__ import annotations
import argparse, hashlib, json, pathlib, random, sys, time, traceback
from datetime import datetime, timezone

import behavior_renderer as B
import inference_contract as I

MODEL = I.MODEL
REVISION = I.REVISION
DEV_INDICES = [0, 1, 5, 6, 7, 10, 12, 13, 16, 18, 19, 22, 24, 25, 29]
DEV_MAX_NEW = 1536
FINAL_BASE_MAX_NEW = 1024
PROMPT_MAX_TOKENS = 3072


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha_file(path: pathlib.Path) -> str:
    return sha_bytes(path.read_bytes())


def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def atomic(path: pathlib.Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".pending")
    with temp.open("w", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        stream.flush()
        import os
        os.fsync(stream.fileno())
    temp.replace(path)


def select_dev(fixtures: list[dict]) -> list[dict]:
    if len(fixtures) != 30 or len({x["id"] for x in fixtures}) != 30:
        raise ValueError("Expected exactly 30 unique existing development fixtures")
    selected = [fixtures[i] for i in DEV_INDICES]
    for grade in range(1, 6):
        group = [fixture for fixture in selected if fixture.get("grade") == grade]
        if len(group) != 3 or sum(f.get("mode") == "answer" for f in group) != 2:
            raise ValueError("Frozen dev subset must have two answer tasks and one guard/feedback per grade")
        if sum(f.get("mode") in ("missing_or_contradictory_info", "student_error") for f in group) != 1:
            raise ValueError("Frozen dev subset guard/feedback mode differs")
    return selected


def build_messages(fixture: dict) -> list[dict[str, str]]:
    return I.messages(fixture)


def prompt_hashes(tok, fixtures: list[dict], thinking: bool) -> dict[str, str]:
    hashes = {}
    for fixture in fixtures:
        ids = tok.apply_chat_template(build_messages(fixture), tokenize=True,
                                      add_generation_prompt=True, enable_thinking=thinking)
        ids = ids["input_ids"] if hasattr(ids, "keys") else ids
        if hasattr(ids, "tolist"):
            ids = ids.tolist()
        if ids and isinstance(ids[0], list):
            ids = ids[0]
        if len(ids) > PROMPT_MAX_TOKENS:
            raise ValueError(f"Prompt too long ({len(ids)} > {PROMPT_MAX_TOKENS}); truncation forbidden")
        hashes[fixture["id"]] = I.digest(I.canonical(ids).encode())
    return hashes


def extract_final(raw: str, thinking: bool, ended_eos: bool, timed_out: bool,
                  reached_token_limit: bool = False) -> str:
    if timed_out:
        raise TimeoutError("Generation timed out")
    if reached_token_limit:
        raise ValueError("Generation reached max_new_tokens; truncation is possible")
    if not ended_eos:
        raise ValueError("Generation did not end with EOS; output may be truncated")
    if thinking:
        marker = "</think>"
        if marker not in raw:
            raise ValueError("Native thinking output has no closed final-answer section")
        answer = raw.rsplit(marker, 1)[1]
    else:
        answer = raw
    answer = answer.replace("<|im_end|>", "").strip()
    if not answer:
        raise ValueError("Generation has no final answer")
    return answer


def validate_scope(scope: dict, phase: str) -> None:
    if not isinstance(scope, dict) or scope.get("schema") != "MathVisionKid.native_probe_scope.v1":
        raise ValueError("Native probe scope schema mismatch")
    required = {"dev_fixture_sha256", "selection_policy_sha256"}
    if phase == "final":
        required.add("native_locked15_sha256")
    if not required.issubset(scope):
        raise ValueError("Native probe scope is missing required frozen hashes")
    for key in required:
        value = scope.get(key)
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError("Invalid scope SHA256: " + key)


def validate_final_gate(gate: dict, scope: dict, dev_output_sha256: str) -> None:
    if not isinstance(gate, dict) or gate.get("schema") != "MathVisionKid.native_probe_gate.v1":
        raise ValueError("Native final gate schema mismatch")
    if gate.get("candidate_eligible") is not True:
        raise ValueError("Native thinking candidate is not eligible")
    if gate.get("dev_output_sha256") != dev_output_sha256:
        raise ValueError("Native final gate does not bind completed dev output")
    if gate.get("policy_sha256") != scope.get("selection_policy_sha256"):
        raise ValueError("Native final gate policy hash differs from frozen scope")


def make_contract(fixtures: list[dict], raw_fixture_sha: str, phase: str) -> dict:
    mode = "thinking" if phase == "dev" else "paired_final"
    return {
        "schema": "MathVisionKid.native_thinking_probe.v1",
        "phase": phase, "protocol": mode, "model": MODEL, "revision": REVISION,
        "fixture_sha256": raw_fixture_sha, "fixture_ids": [f["id"] for f in fixtures],
        "system": B.SYSTEM, "system_sha256": I.digest(B.SYSTEM.encode()),
        "message_builder": "inference_contract.messages; same original user request text for all configs",
        "thinking_max_new_tokens": DEV_MAX_NEW,
        "base_max_new_tokens": FINAL_BASE_MAX_NEW if phase == "final" else None,
        "thinking_decoding": {"do_sample": True, "temperature": 0.6, "top_p": 0.95, "top_k": 20, "min_p": 0.0,
                              "num_beams": 1, "max_new_tokens": DEV_MAX_NEW, "repetition_penalty": 1.0, "use_cache": True},
        "base_decoding": ({"do_sample": True, "temperature": 0.7, "top_p": 0.8, "top_k": 20, "min_p": 0.0,
                           "num_beams": 1, "max_new_tokens": FINAL_BASE_MAX_NEW, "repetition_penalty": 1.0, "use_cache": True}
                          if phase == "final" else None),
        "seed_policy": "I per-fixture seed: 20261024 + first8hex SHA256(fixture_id) modulo2^31, reset for each config",
        "enable_thinking": (False, True) if phase == "final" else True,
        "prompt_max_tokens": PROMPT_MAX_TOKENS, "truncation": "forbidden",
        "training_performed": False, "optimizer_loaded": False,
        "raw_thinking_is_training_target": False,
    }


def run_generation(model, tok, fixtures, out: pathlib.Path, config_name: str,
                   thinking: bool, decoding: dict, contract: dict, contract_sha: str, cutoff: float,
                   progress: dict) -> tuple[list[dict], str]:
    if I.digest(I.canonical(contract).encode()) != contract_sha:
        raise ValueError("Native probe contract hash mismatch")
    import torch
    from transformers import GenerationConfig
    records = []
    raw_path = out / (config_name + "_raw.partial.jsonl")
    final_path = out / (config_name + "_final.partial.jsonl")
    if raw_path.exists() or final_path.exists():
        raise FileExistsError("Native probe partial output exists; preserve and do not rerun")
    for index, fixture in enumerate(fixtures, start=1):
        left = cutoff - time.time()
        if left < 5:
            raise TimeoutError("Native probe phase budget exhausted; partial output retained")
        seed = (20261024 + int(I.digest(fixture["id"].encode())[:8], 16)) % (2**31)
        torch.manual_seed(seed); torch.cuda.manual_seed_all(seed); random.seed(seed)
        messages = build_messages(fixture)
        tokenized = tok.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                           enable_thinking=thinking, return_tensors="pt", return_dict=True).to("cuda")
        prompt_ids = tokenized["input_ids"][0].tolist()
        if len(prompt_ids) > PROMPT_MAX_TOKENS:
            raise ValueError(f"Prompt too long ({len(prompt_ids)} > {PROMPT_MAX_TOKENS}); truncation forbidden")
        prompt_sha = I.digest(I.canonical(prompt_ids).encode())
        expected_sha = contract["prompt_token_sha256"][config_name][fixture["id"]]
        if prompt_sha != expected_sha:
            raise ValueError("Prompt token hash differs from frozen native probe contract")
        started = time.monotonic()
        gc = GenerationConfig(**decoding, eos_token_id=151645, pad_token_id=tok.pad_token_id)
        with torch.inference_mode():
            result = model.generate(**tokenized, generation_config=gc, max_time=left)
        tokens = result[0, tokenized["input_ids"].shape[1]:]
        raw = tok.decode(tokens, skip_special_tokens=False)
        eos = bool(len(tokens) and int(tokens[-1]) == 151645)
        timed_out = time.time() >= cutoff
        row = {
            "fixture_id": fixture["id"], "grade": fixture["grade"], "mode": fixture["mode"],
            "configuration": config_name, "thinking": thinking, "stage": progress["phase"],
            "contract_sha256": contract_sha, "prompt_token_sha256": prompt_sha,
            "seed": seed, "max_new_tokens": decoding["max_new_tokens"],
            "generated_tokens": int(len(tokens)), "ended_eos": eos, "timed_out": timed_out,
            "possibly_truncated": not eos, "generation_seconds": time.monotonic() - started,
            "raw_output_sha256": I.digest(raw.encode("utf-8")), "training_performed": False,
        }
        with raw_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({**row, "raw_output": raw}, ensure_ascii=False) + "\n"); stream.flush()
        # Chain-of-thought remains in raw cloud-only file; surface only a closed final section.
        answer = extract_final(raw, thinking, eos, timed_out,
                               reached_token_limit=len(tokens) >= decoding["max_new_tokens"])
        final_row = {**row, "final_output": answer}
        with final_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(final_row, ensure_ascii=False) + "\n"); stream.flush()
        records.append(final_row)
        atomic(out / "runtime_progress.json", {**progress, "state": "GENERATING", "completed": len(records),
                                                "total": len(fixtures), "last_fixture_id": fixture["id"],
                                                "last_ended_eos": eos, "last_generation_seconds": row["generation_seconds"]})
    raw_final = out / (config_name + "_raw.jsonl")
    final_final = out / (config_name + "_final.jsonl")
    raw_path.replace(raw_final); final_path.replace(final_final)
    return records, I.digest(final_final.read_bytes())


def load_base():
    import torch
    from transformers import BitsAndBytesConfig
    from unsloth import FastLanguageModel
    if not torch.cuda.is_available() or "t4" not in torch.cuda.get_device_name(0).lower():
        raise RuntimeError("Expected authorized T4 GPU")
    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                               bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
    model, tok = FastLanguageModel.from_pretrained(
        model_name=MODEL, revision=REVISION, use_exact_model_name=True,
        max_seq_length=4096, dtype=torch.float16, load_in_4bit=True,
        quantization_config=quant, attn_implementation="sdpa")
    if getattr(model.config, "_commit_hash", None) != REVISION or tok.eos_token_id != 151645:
        raise ValueError("Pinned model/tokenizer mismatch")
    FastLanguageModel.for_inference(model); model.eval()
    return model, tok, FastLanguageModel


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, required=True)
    parser.add_argument("--phase", choices=("dev", "final"), default="dev")
    args = parser.parse_args()
    root = args.root
    sys.path.insert(0, str(root))
    import recovery_worker_v3 as training_worker
    owner_scope = training_worker.load_scope(root)
    training_receipt = json.loads((root / "training" / "run_complete.json").read_bytes())
    if training_receipt.get("complete") is not True or training_receipt.get("stop_reason") not in ("QUALITY_GATE_STOP", "QUALITY_GATE_STOP_ON_RESUME"):
        raise RuntimeError("Training must have completed at the quality gate before base inference")
    scope_path = root / "native_probe_scope.json"
    scope = json.loads(scope_path.read_bytes())
    validate_scope(scope, args.phase)
    deadline = float(owner_scope["hard_deadline_unix"])
    if args.phase == "dev":
        fixture_path = root / "new_validation_candidates.jsonl"
        raw_fixture_sha = sha_file(fixture_path)
        if raw_fixture_sha != scope["dev_fixture_sha256"]:
            raise ValueError("Dev fixture bytes differ from native probe scope")
        all_fixtures = [json.loads(line) for line in fixture_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        fixtures = select_dev(all_fixtures)
        # Original base output is comparator only; this probe never regenerates it.
        comparator = root / "training" / "eval_step_000000" / "base_generations.jsonl"
        if not comparator.is_file():
            raise FileNotFoundError("Original I-contract dev base comparator is missing")
        cutoff = min(time.time() + 900, deadline - 900)
        out = root / "native_probe" / "dev"
        stage = "dev"
    else:
        gate_path = root / "native_probe_gate.json"
        if not gate_path.is_file():
            raise FileNotFoundError("Native final gate is required before reading final fixtures")
        dev_complete = root / "native_probe" / "dev" / "complete.json"
        if not dev_complete.is_file():
            raise RuntimeError("Native dev phase must complete before final gate validation")
        dev_proof = json.loads(dev_complete.read_bytes())
        gate = json.loads(gate_path.read_bytes())
        validate_final_gate(gate, scope, dev_proof["dev_output_sha256"])
        fixture_path = root / "native_locked15.jsonl"
        raw_fixture_sha = sha_file(fixture_path)
        if raw_fixture_sha != scope["native_locked15_sha256"]:
            raise ValueError("Native final fixture bytes differ from frozen scope")
        fixtures = [json.loads(line) for line in fixture_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(fixtures) != 15 or len({f["id"] for f in fixtures}) != 15:
            raise ValueError("Native final evaluation requires exactly 15 unique frozen fixtures")
        cutoff = min(time.time() + 900, deadline - 600)
        out = root / "native_probe" / "final"
        stage = "final"
    if cutoff <= time.time() + 30:
        raise TimeoutError("Insufficient phase time remains; reserve window preserved")
    out.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    atomic(out / "runtime_progress.json", {"state": "STARTED", "phase": stage, "started_utc": started,
                                            "fixture_count": len(fixtures), "training_performed": False,
                                            "optimizer_loaded": False, "locked_test_accessed": stage == "final"})
    try:
        model, tok, fast = load_base()
        contract = make_contract(fixtures, raw_fixture_sha, stage)
        contract["selection_policy_sha256"] = scope["selection_policy_sha256"]
        contract["original_dev_comparator_sha256"] = sha_file(comparator) if stage == "dev" else None
        contract["final_gate_sha256"] = sha_file(root / "native_probe_gate.json") if stage == "final" else None
        contract["prompt_token_sha256"] = {
            "native_thinking": prompt_hashes(tok, fixtures, True),
        }
        if stage == "final":
            contract["prompt_token_sha256"]["baseline_nonthinking"] = prompt_hashes(tok, fixtures, False)
        contract_sha = I.digest(I.canonical(contract).encode())
        atomic(out / "contract.json", contract)
        atomic(out / "runtime_progress.json", {"state": "GENERATING", "phase": stage,
                                                "started_utc": started, "fixture_count": len(fixtures),
                                                "completed": 0, "contract_sha256": contract_sha,
                                                "training_performed": False, "optimizer_loaded": False,
                                                "locked_test_accessed": stage == "final"})
        if stage == "dev":
            cfg = {"do_sample": True, "temperature": .6, "top_p": .95, "top_k": 20, "min_p": 0.0,
                   "num_beams": 1, "max_new_tokens": DEV_MAX_NEW, "repetition_penalty": 1.0, "use_cache": True}
            _, final_sha = run_generation(model, tok, fixtures, out, "native_thinking", True, cfg,
                                          contract, contract_sha, cutoff, {"phase": stage})
            dev_output_sha = final_sha
        else:
            base_cfg = contract["base_decoding"]
            think_cfg = contract["thinking_decoding"]
            _, base_sha = run_generation(model, tok, fixtures, out, "baseline_nonthinking", False, base_cfg,
                                         contract, contract_sha, cutoff, {"phase": stage})
            _, final_sha = run_generation(model, tok, fixtures, out, "native_thinking", True, think_cfg,
                                          contract, contract_sha, cutoff, {"phase": stage})
            dev_output_sha = None
        proof = {"schema": "MathVisionKid.native_probe_completion.v1", "complete": True,
                 "phase": stage, "fixture_count": len(fixtures), "fixture_sha256": raw_fixture_sha,
                 "model": MODEL, "revision": REVISION, "contract_sha256": contract_sha,
                 "native_output_sha256": final_sha, "dev_output_sha256": dev_output_sha,
                 "baseline_output_sha256": base_sha if stage == "final" else None,
                 "selection_policy_sha256": scope["selection_policy_sha256"],
                 "training_performed": False, "optimizer_loaded": False,
                 "locked_test_accessed": stage == "final", "started_utc": started,
                 "finished_utc": datetime.now(timezone.utc).isoformat()}
        atomic(out / "complete.json", proof)
        atomic(out / "runtime_progress.json", {"state": "COMPLETE", **proof})
    except BaseException as exc:
        atomic(out / "error.json", {"error": repr(exc), "traceback": traceback.format_exc(),
                                    "training_performed": False, "optimizer_loaded": False,
                                    "locked_test_accessed": stage == "final"})
        atomic(out / "runtime_progress.json", {"state": "FAILED", "phase": stage,
                                                "training_performed": False, "optimizer_loaded": False,
                                                "locked_test_accessed": stage == "final"})
        raise


if __name__ == "__main__":
    main()
