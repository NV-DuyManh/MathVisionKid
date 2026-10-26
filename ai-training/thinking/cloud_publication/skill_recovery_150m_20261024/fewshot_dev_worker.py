"""Prepare one base-only few-shot dev pass on T4; no adapter/optimizer path."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import time
import traceback
from datetime import datetime, timezone
import sys

import fewshot_contract as F

MODEL = F.I.MODEL
REVISION = F.I.REVISION


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path: pathlib.Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".pending")
    with temp.open("w", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        stream.flush()
        import os
        os.fsync(stream.fileno())
    temp.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, required=True, help="Authorized mounted run directory")
    parser.add_argument("--runtime-seconds", type=int, default=1200)
    args = parser.parse_args()
    if not 1 <= args.runtime_seconds <= 1200:
        raise ValueError("Runtime budget must be 1..1200 seconds")

    root = args.root
    sys.path.insert(0, str(root))
    import recovery_worker_v3 as training_worker
    scope = training_worker.load_scope(root)
    training_complete_path = root / "training" / "run_complete.json"
    if not training_complete_path.exists():
        raise RuntimeError("Training has not published a completion receipt; refusing to load base")
    training_complete = json.loads(training_complete_path.read_bytes())
    if training_complete.get("complete") is not True or training_complete.get("stop_reason") not in (
        "QUALITY_GATE_STOP", "QUALITY_GATE_STOP_ON_RESUME",
    ):
        raise RuntimeError("Training completion receipt does not show the authorized quality-gate stop")
    deadline = float(scope["hard_deadline_unix"])
    stop_at = min(time.time() + args.runtime_seconds, deadline - 60)
    if stop_at <= time.time() + 30:
        raise TimeoutError("Insufficient authorized time remains for one inference pass")
    fixtures_path = root / "new_validation_candidates.jsonl"
    fixtures = [json.loads(line) for line in fixtures_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    fixture_sha = sha(fixtures_path)
    if fixture_sha != scope["dev_sha256"] or len(fixtures) != 30:
        raise ValueError("Frozen development fixture hash/count mismatch")
    bank, bank_sha = F.load_and_validate_bank()
    output = root / "fewshot_dev"
    output.mkdir(exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    atomic(output / "runtime_progress.json", {
        "state": "STARTED", "started_utc": started, "fixture_count": 30,
        "training_performed": False, "optimizer_loaded": False,
        "locked_test_accessed": False, "model_loaded": False,
    })
    try:
        import torch
        from transformers import BitsAndBytesConfig
        from unsloth import FastLanguageModel

        if not torch.cuda.is_available() or "t4" not in torch.cuda.get_device_name(0).lower():
            raise RuntimeError("Expected authorized T4 GPU")
        atomic(output / "runtime_progress.json", {
            "state": "LOADING_FRESH_BASE", "started_utc": started, "fixture_count": 30,
            "training_performed": False, "optimizer_loaded": False,
            "locked_test_accessed": False, "model_loaded": False,
        })
        quant = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True,
        )
        model, tok = FastLanguageModel.from_pretrained(
            model_name=MODEL, revision=REVISION, use_exact_model_name=True,
            max_seq_length=4096, dtype=torch.float16, load_in_4bit=True,
            quantization_config=quant, attn_implementation="sdpa",
        )
        if getattr(model.config, "_commit_hash", None) != REVISION or tok.eos_token_id != 151645:
            raise ValueError("Model/tokenizer revision mismatch")
        contract, contract_sha = F.eval_contract(
            fixtures, tok, fixture_sha256=fixture_sha,
            frozen_fixture_ids=[fixture["id"] for fixture in fixtures],
        )
        if contract["example_bank_sha256"] != bank_sha:
            raise ValueError("Few-shot bank changed between preflight and contract")
        atomic(output / "contract.json", contract)
        atomic(output / "runtime_progress.json", {
            "state": "GENERATING_BASE_FEWSHOT", "started_utc": started,
            "fixture_count": 30, "completed": 0,
            "training_performed": False, "optimizer_loaded": False,
            "locked_test_accessed": False, "model_loaded": True,
            "contract_sha256": contract_sha,
        })
        proof = F.generate_fixtures(
            model, tok, fixtures, output, "base_fewshot_dev", contract,
            contract_sha, stop_at - time.time(), FastLanguageModel,
        )
        proof.update({"started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat()})
        atomic(output / "complete.json", proof)
        atomic(output / "runtime_progress.json", {"state": "COMPLETE", **proof})
    except BaseException as exc:
        atomic(output / "error.json", {
            "error": repr(exc), "traceback": traceback.format_exc(),
            "training_performed": False, "optimizer_loaded": False,
            "locked_test_accessed": False,
        })
        atomic(output / "runtime_progress.json", {
            "state": "FAILED", "started_utc": started,
            "training_performed": False, "optimizer_loaded": False,
            "locked_test_accessed": False,
        })
        raise


if __name__ == "__main__":
    main()
