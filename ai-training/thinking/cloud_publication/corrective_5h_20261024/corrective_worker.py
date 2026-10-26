#!/usr/bin/env python3
"""Fresh, fixed five-hour T4 corrective branch; local atomic artifacts only.

No throughput benchmark, optimizer pilot, Drive client, old-adapter resume, or
evaluation-based early stopping. The five-hour window starts at the first
optimizer-group entry. An in-flight group finishes at its boundary; no new
group starts after the deadline. Setup/base evaluation precede that window.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import sys
import time
import traceback
import zipfile

MODEL = "Qwen/Qwen3-1.7B"
REVISION = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
VIEW_SHA256 = "14929ba64e5c94d812f1fc3804c771ca8e41fa92285aed3a925282c39b1e4331"
MANIFEST_SHA256 = "444db8845af0c12bb528795b7e441b996571960dd58ab6898eb9394c77031545"
FIXTURES_SHA256 = "81ddf4261063b5832b6f55168ca160bf5cec26a5cabd83b7fedaa00ddecec100"
RECIPE_SHA256 = "1bb69c394c7eaaea7034125c6b3361eebbbe0d77e0715a8454331fbe7cee3ff8"
PROTECTED_HASH_FILE_SHA256 = "9fa1cd11b5bbca2b4a8d63268159ab0d498176bb7d601cf8ae3996f3d2e2f7ae"
SYSTEM = "Bạn là gia sư Toán tiểu học. Trả lời bằng tiếng Việt theo yêu cầu. Chỉ đưa lời giải đầy đủ khi được yêu cầu; gợi ý không điền đáp số. Chỉ nhận xét lời làm thực sự được cung cấp."
SYSTEM_SHA256 = "0137a055ce34116f23604ba029acac937e0ab030be537f561d0a0c2cf54b4933"
TOKENIZER_HELPER_SHA256 = "9b1287f495e30b85085c6d8c23b2fc273e38fefbf1e730d19b0d95a9d8950a3c"
TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
MODES = {"worked_solution", "hint_level_1", "hint_level_2", "hint_level_3"}
MODE_MAP = {"answer": "worked_solution", "student_error": "worked_solution",
            "missing_or_contradictory_info": "worked_solution", "hint_no_answer": "hint_level_1"}
TRAIN_SECONDS = 18000.0
WARMUP_FRACTION = 0.05
PEAK_LR = 5e-5
MIN_LR = 5e-6
WARMUP_START_LR = 1e-6
MICROBATCH = 2
ACCUMULATION = 8
EFFECTIVE_BATCH = 16
MAX_SEQUENCE = 2048
MAX_NEW_TOKENS = 1024
EOT = 151645
SEED = 20261023


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: bytes):
    return hashlib.sha256(value).hexdigest()


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_bytes(path, content):
    path = Path(path)
    pending = path.with_name(path.name + ".pending")
    with pending.open("wb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(pending, path)


def atomic_json(path, value):
    atomic_bytes(path, (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"))


def append_jsonl(path, rows):
    with Path(path).open("a", encoding="utf-8") as stream:
        for row in rows:
            stream.write(canonical(row) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def strict_json(text):
    return json.loads(text, object_pairs_hook=no_duplicate_keys)


def load_helper(path):
    if sha_file(path) != TOKENIZER_HELPER_SHA256:
        raise ValueError("tokenizer helper SHA256 differs from the exact audited EOT/mask implementation")
    spec = importlib.util.spec_from_file_location("corrective_assistant_helper", path)
    if spec is None or spec.loader is None:
        raise ValueError("cannot load required tokenizer helper")
    helper = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = helper
    spec.loader.exec_module(helper)
    return helper


def lr_at_elapsed(elapsed, duration=TRAIN_SECONDS):
    """Time scheduler sampled at group entry, with a fixed 900-second warmup."""
    if duration <= 0:
        raise ValueError("duration must be positive")
    elapsed = min(max(float(elapsed), 0.0), duration)
    warmup = duration * WARMUP_FRACTION
    if elapsed < warmup:
        return WARMUP_START_LR + (PEAK_LR - WARMUP_START_LR) * elapsed / warmup
    fraction = (elapsed - warmup) / (duration - warmup)
    return MIN_LR + (PEAK_LR - MIN_LR) * (1 + math.cos(math.pi * fraction)) / 2


def group_may_start(now_monotonic, start_monotonic):
    return now_monotonic < start_monotonic + TRAIN_SECONDS


def make_length_batches(rows, epoch, seed=SEED):
    order = list(range(len(rows)))
    rng = random.Random(seed + epoch)
    rng.shuffle(order)
    batches = []
    for start in range(0, len(order), 128):
        chunk = order[start:start + 128]
        chunk.sort(key=lambda i: len(rows[i]["encoded"]["input_ids"]))
        local = [chunk[i:i + MICROBATCH] for i in range(0, len(chunk), MICROBATCH)]
        rng.shuffle(local)
        batches.extend(local)
    return batches


def validate_encoded(encoded):
    ids, mask, labels = (encoded[k] for k in ("input_ids", "attention_mask", "labels"))
    if not ids or len(ids) != len(mask) or len(ids) != len(labels):
        raise ValueError("input/mask/label shape mismatch")
    if len(ids) > MAX_SEQUENCE:
        raise ValueError("sequence exceeds 2048; truncation is forbidden")
    if any(m != 1 for m in mask):
        raise ValueError("unpadded training row must have full attention")
    supervised = [label for label in labels if label != -100]
    if not supervised or supervised[-1] != EOT or supervised.count(EOT) != 1:
        raise ValueError("assistant target must supervise exactly one final 151645 EOT")
    if any(label != -100 and label != token for label, token in zip(labels, ids)):
        raise ValueError("labels do not match actual assistant tokens")
    if labels[0] != -100:
        raise ValueError("system prompt must be masked")


def load_view(path, manifest_path, helper, tokenizer):
    if sha_file(path) != VIEW_SHA256 or sha_file(manifest_path) != MANIFEST_SHA256:
        raise ValueError("pinned view/manifest SHA256 mismatch")
    manifest = strict_json(Path(manifest_path).read_text(encoding="utf-8"))
    required = {"selected_chat_rows": 16000, "selected_cases": 4000,
                "all_four_modes_preserved": True, "members_complete": 32,
                "raw_train_rows_scanned": 6502344, "recipe_sha256": RECIPE_SHA256,
                "training_view_sha256": VIEW_SHA256,
                "protected_eval_hash_file_sha256": PROTECTED_HASH_FILE_SHA256}
    for key, expected in required.items():
        if manifest.get(key) != expected:
            raise ValueError(f"manifest binding mismatch: {key}")
    if manifest.get("protected_eval_hash_count", 0) < 28:
        raise ValueError("manifest lacks protected-question exclusion evidence")
    expected = {}
    for case in manifest["selected_cases_manifest"]:
        if set(case["rows"]) != MODES:
            raise ValueError("manifest case lacks all four modes")
        for mode, info in case["rows"].items():
            sid = info["sample_id"]
            if sid in expected:
                raise ValueError("duplicate manifest sample_id")
            expected[sid] = {"sha256": info["row_sha256"], "source_case_id": case["case_id"],
                             "family": case.get("family", "unknown"), "mode": mode}
    if len(expected) != 16000:
        raise ValueError("manifest does not bind exactly 16000 rows")
    rows, seen, systems = [], set(), Counter()
    case_modes = defaultdict(set)
    with Path(path).open("rb") as stream:
        for raw in stream:
            raw = raw.rstrip(b"\r\n")
            if not raw:
                raise ValueError("blank training row")
            row = strict_json(raw.decode("utf-8"))
            sid = row.get("sample_id")
            if row.get("split") != "train" or sid in seen or sid not in expected:
                raise ValueError("non-train, unknown or duplicate training sample")
            binding = expected[sid]
            if digest(raw) != binding["sha256"] or row.get("mode") != binding["mode"]:
                raise ValueError("raw training row hash/mode binding mismatch")
            messages = row["messages"]
            if [m["role"] for m in messages] != ["system", "user", "assistant"]:
                raise ValueError("unexpected training role layout")
            prompt = strict_json(messages[1]["content"])
            target = strict_json(messages[2]["content"])
            if prompt.get("mode") != row["mode"] or not isinstance(target, dict):
                raise ValueError("training prompt/target contract mismatch")
            systems[messages[0]["content"]] += 1
            encoded = helper.tokenize_assistant_only(row, tokenizer, max_sequence_tokens=MAX_SEQUENCE)
            validate_encoded(encoded)
            seen.add(sid)
            case_modes[binding["source_case_id"]].add(row["mode"])
            rows.append({"sample_id": sid, "case_group_id": row["case_group_id"],
                         "source_case_id": binding["source_case_id"], "mode": row["mode"],
                         "grade": row.get("grade"), "family": binding["family"], "encoded": encoded})
    if seen != set(expected) or len(case_modes) != 4000 or any(m != MODES for m in case_modes.values()):
        raise ValueError("materialized view differs from complete manifest case set")
    if digest(SYSTEM.encode("utf-8")) != SYSTEM_SHA256 or systems.most_common(1)[0][0] != SYSTEM:
        raise ValueError("pinned evaluation system is not the actual dominant training system")
    audit = {"rows": len(rows), "source_cases": len(case_modes), "all_four_modes": True,
             "system_counts": [{"sha256": digest(s.encode("utf-8")), "rows": n}
                               for s, n in systems.most_common()],
             "max_sequence_tokens": max(len(r["encoded"]["input_ids"]) for r in rows),
             "supervised_eot": EOT, "silent_truncation": False}
    return rows, audit


def load_fixtures(path):
    if sha_file(path) != FIXTURES_SHA256:
        raise ValueError("frozen evaluation SHA256 mismatch")
    rows = [strict_json(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]
    if len(rows) != 28 or len({r["id"] for r in rows}) != 28:
        raise ValueError("expected exact 28 distinct evaluation fixtures")
    for row in rows:
        if row["mode"] not in MODE_MAP or not isinstance(row["userproblem"], str):
            raise ValueError("unsupported evaluation fixture")
    return rows


def fixture_messages(fixture):
    # Reference answers, oracle and rubric never enter model messages.
    user = {"grade": fixture["grade"], "problem": fixture["userproblem"],
            "mode": MODE_MAP[fixture["mode"]]}
    return [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False)}]


def eval_contract(fixtures, tokenizer):
    prompt_tokens = {}
    for row in fixtures:
        ids = tokenizer.apply_chat_template(fixture_messages(row), tokenize=True,
                  add_generation_prompt=True, enable_thinking=False)
        if hasattr(ids, "keys"):
            ids = ids["input_ids"]
        prompt_tokens[row["id"]] = digest(canonical(ids).encode("utf-8"))
    contract = {"schema": "MathVisionKid.corrective_same_contract_eval.v1", "model": MODEL,
                "revision": REVISION, "fixture_sha256": FIXTURES_SHA256,
                "fixture_ids": [r["id"] for r in fixtures], "system": SYSTEM,
                "system_sha256": SYSTEM_SHA256, "mode_map": MODE_MAP,
                "student_work_policy": "Preserve student work in original problem prose; no invented field.",
                "user_serialization": "json.dumps(grade/problem/mode insertion order, ensure_ascii=False)",
                "enable_thinking": False, "add_generation_prompt": True,
                "prompt_token_sha256": prompt_tokens,
                "decoding": {"do_sample": False, "num_beams": 1, "max_new_tokens": MAX_NEW_TOKENS,
                             "repetition_penalty": 1.0, "use_cache": True,
                             "pad_token_id": tokenizer.pad_token_id, "eos_token_id": EOT}}
    return contract, digest(canonical(contract).encode("utf-8"))


def cached_base(out, contract, contract_sha):
    path, provenance_path = out / "base_generations.jsonl", out / "base_generation_provenance.json"
    if not path.exists() and not provenance_path.exists():
        return None
    if not path.exists() or not provenance_path.exists():
        raise ValueError("partial base cache; refuse reuse")
    provenance = strict_json(provenance_path.read_text(encoding="utf-8"))
    expected = {"model": MODEL, "revision": REVISION, "fixture_sha256": FIXTURES_SHA256,
                "system_sha256": SYSTEM_SHA256, "contract_sha256": contract_sha,
                "base_untrained": True, "adapter_loaded": False, "max_new_tokens": MAX_NEW_TOKENS}
    if any(provenance.get(k) != v for k, v in expected.items()) or provenance.get("output_sha256") != sha_file(path):
        raise ValueError("base cache provenance does not bind exact same model/contract")
    rows = [strict_json(line) for line in path.read_text(encoding="utf-8").splitlines()]
    if len(rows) != 28 or [r["fixture_id"] for r in rows] != contract["fixture_ids"]:
        raise ValueError("base cache fixture mismatch")
    for row in rows:
        if (row.get("stage") != "base_before_training" or row.get("contract_sha256") != contract_sha
                or row.get("max_new_tokens") != MAX_NEW_TOKENS or row.get("timed_out") is not False
                or row.get("prompt_token_sha256") != contract["prompt_token_sha256"][row["fixture_id"]]):
            raise ValueError("base cache row contract mismatch")
    return rows


def generate_fixtures(model, tokenizer, fixtures, out, stage, contract, contract_sha, timeout_seconds, fast_model):
    import torch
    from transformers import GenerationConfig
    path = out / ("base_generations.jsonl" if stage == "base_before_training" else "adapter_generations.jsonl")
    if path.exists():
        raise FileExistsError(path)
    generation_config = GenerationConfig(**contract["decoding"])
    fast_model.for_inference(model)
    model.eval()
    outputs = []
    deadline = time.monotonic() + timeout_seconds
    try:
        for fixture in fixtures:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"{stage} exceeded {timeout_seconds}s evaluation budget")
            ids = tokenizer.apply_chat_template(fixture_messages(fixture), tokenize=True,
                      add_generation_prompt=True, enable_thinking=False, return_tensors="pt").to("cuda")
            if digest(canonical(ids[0].tolist()).encode("utf-8")) != contract["prompt_token_sha256"][fixture["id"]]:
                raise ValueError("actual evaluation prompt differs from bound contract")
            with torch.inference_mode():
                result = model.generate(input_ids=ids, attention_mask=torch.ones_like(ids),
                         generation_config=generation_config, max_time=remaining)
            tokens = result[0, ids.shape[1]:]
            ended_eos = bool(len(tokens) and tokens[-1].item() == EOT)
            timed_out = time.monotonic() >= deadline
            outputs.append({"stage": stage, "fixture_id": fixture["id"], "grade": fixture["grade"],
                "mode": fixture["mode"], "model_mode": MODE_MAP[fixture["mode"]],
                "output": tokenizer.decode(tokens, skip_special_tokens=True), "generated_tokens": len(tokens),
                "max_new_tokens": MAX_NEW_TOKENS, "ended_eos": ended_eos,
                "possibly_truncated": not ended_eos, "timed_out": timed_out,
                "contract_sha256": contract_sha,
                "prompt_token_sha256": contract["prompt_token_sha256"][fixture["id"]]})
            atomic_bytes(path.with_suffix(".partial.jsonl"), "".join(canonical(x) + "\n" for x in outputs).encode("utf-8"))
            if timed_out:
                raise TimeoutError(f"{stage} timed out during {fixture['id']}; partial outputs retained")
        atomic_bytes(path, "".join(canonical(x) + "\n" for x in outputs).encode("utf-8"))
    finally:
        fast_model.for_training(model)
    return outputs


def collate(items, tokenizer, device):
    import torch
    width = max(len(r["encoded"]["input_ids"]) for r in items)
    values = {"input_ids": [], "attention_mask": [], "labels": []}
    for row in items:
        encoded = row["encoded"]
        padding = width - len(encoded["input_ids"])
        values["input_ids"].append(encoded["input_ids"] + [tokenizer.pad_token_id] * padding)
        values["attention_mask"].append(encoded["attention_mask"] + [0] * padding)
        values["labels"].append(encoded["labels"] + [-100] * padding)
    return {key: torch.tensor(value, dtype=torch.long, device=device) for key, value in values.items()}


def snapshot_metrics(state, rows, start_monotonic, now_monotonic=None):
    now_monotonic = time.monotonic() if now_monotonic is None else now_monotonic
    elapsed = max(0.0, now_monotonic - start_monotonic)
    return {**{k: v for k, v in state.items() if k not in ("unique_ids", "unique_cases", "exposures_by_mode", "exposures_by_grade", "exposures_by_family")},
            "unique_examples": len(state["unique_ids"]), "unique_source_cases": len(state["unique_cases"]),
            "exposures_by_mode": dict(state["exposures_by_mode"]),
            "exposures_by_grade": dict(state["exposures_by_grade"]),
            "exposures_by_family": dict(state["exposures_by_family"]),
            "training_wall_seconds": elapsed, "requested_training_wall_seconds": TRAIN_SECONDS,
            "deadline_boundary_overrun_seconds": max(0.0, elapsed - TRAIN_SECONDS),
            "completed_view_epochs": state["rows_done"] / len(rows),
            "view_rows": len(rows), "rows_per_second": state["rows_done"] / max(elapsed, 1e-9),
            "supervised_tokens_per_second": state["supervised_tokens"] / max(elapsed, 1e-9),
            "mean_loss": state["loss_sum"] / max(state["step"], 1),
            "resume_old_734": False}


def save_generation(model, tokenizer, optimizer, scaler, out, cfg, metrics, cursor, clock):
    import torch
    name = f"generation_step_{metrics['step']:06d}_rows_{metrics['rows_done']:08d}"
    final = out / name
    if final.exists():
        pointer = strict_json((out / "latest.json").read_text(encoding="utf-8"))
        if pointer["generation"] != name or sha_file(final / "generation_manifest.json") != pointer["manifest_sha256"]:
            raise ValueError("existing generation/pointer mismatch")
        return final
    pending = out / (name + ".pending")
    pending.mkdir(exist_ok=False)
    model.save_pretrained(pending, safe_serialization=True)
    tokenizer.save_pretrained(pending)
    atomic_json(pending / "run_config.json", cfg)
    atomic_json(pending / "metrics.json", metrics)
    resume = {"schema": "MathVisionKid.corrective5h.resume.v1", "fresh_base_branch": True,
              "step": metrics["step"], "rows_done": metrics["rows_done"], "cursor": cursor,
              "optimizer": optimizer.state_dict(), "scaler": scaler.state_dict(),
              "torch_cpu_rng": torch.get_rng_state(), "torch_cuda_rng": torch.cuda.get_rng_state_all(),
              "python_rng": random.getstate(), "time_scheduler": {"elapsed_seconds": metrics["training_wall_seconds"],
              "duration_seconds": TRAIN_SECONDS, "warmup_fraction": WARMUP_FRACTION,
              "peak_lr": PEAK_LR, "min_lr": MIN_LR, "warmup_start_lr": WARMUP_START_LR,
              "last_group_lr": metrics.get("last_lr")},
              "consumed_train_seconds": metrics["training_wall_seconds"],
              "automatic_resume_implemented": False,
              "resume_note": "Checkpoint contains optimizer/scaler/RNG/cursor, but automatic resume is not implemented.",
              "clock": clock, "successful_ids_log_bytes": (out / "successful_ids.jsonl").stat().st_size}
    torch.save(resume, pending / "resume_state.pt")
    files = {p.name: sha_file(p) for p in sorted(pending.iterdir()) if p.is_file()}
    sizes = {p.name: p.stat().st_size for p in pending.iterdir() if p.is_file()}
    atomic_json(pending / "generation_manifest.json", {"schema": "MathVisionKid.corrective5h.generation.v1",
                "complete": True, "step": metrics["step"], "rows_done": metrics["rows_done"],
                "consumed_train_seconds": metrics["training_wall_seconds"], "cursor": cursor,
                "files": files, "file_bytes": sizes})
    os.replace(pending, final)
    atomic_json(out / "latest.json", {"generation": name, "step": metrics["step"],
                "rows_done": metrics["rows_done"], "manifest_sha256": sha_file(final / "generation_manifest.json")})
    return final


def export_adapter(generation, out):
    pending = out / "adapter_export.zip.pending"
    with zipfile.ZipFile(pending, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(generation.iterdir()):
            if path.is_file() and path.name != "resume_state.pt":
                archive.write(path, arcname=path.name)
    os.replace(pending, out / "adapter_export.zip")


def framework_versions():
    result = {"python": sys.version}
    for name in ("unsloth", "unsloth_zoo", "torch", "transformers", "peft", "bitsandbytes", "triton"):
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = "not_installed"
    return result


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-view", type=Path, required=True)
    parser.add_argument("--view-manifest", type=Path, required=True)
    parser.add_argument("--eval-fixtures", type=Path, required=True)
    parser.add_argument("--tokenizer-helper", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("/content/mathvisionkid_corrective_5h_20261024/training"))
    parser.add_argument("--eval-timeout-seconds", type=int, default=600)
    return parser.parse_args()


def main():
    args = parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    if any((out / name).exists() for name in ("latest.json", "successful_ids.jsonl", "run_complete.json", "error.json")):
        raise FileExistsError("fresh branch refuses existing training state; no implicit resume")
    if args.eval_timeout_seconds <= 0:
        raise ValueError("evaluation timeout must be positive")
    state = None
    train_start = None
    cfg = {"schema": "MathVisionKid.corrective5h.run.v1", "model": MODEL, "revision": REVISION,
           "worker_sha256": sha_file(Path(__file__)), "tokenizer_helper_sha256": sha_file(args.tokenizer_helper),
           "train_view_sha256": VIEW_SHA256, "train_view_manifest_sha256": MANIFEST_SHA256,
           "fixture_sha256": FIXTURES_SHA256, "seed": SEED, "quantization": "NF4 double quant FP16",
           "compute_dtype": "float16", "lora_r": 16, "lora_alpha": 16, "lora_dropout": 0.0,
           "lora_bias": "none", "target_modules": TARGET_MODULES, "gradient_checkpointing": "unsloth",
           "optimizer": "bitsandbytes.optim.AdamW8bit", "adam_betas": [0.9, 0.999], "weight_decay": 0.01,
           "microbatch": MICROBATCH, "grad_accumulation": ACCUMULATION, "effective_batch": EFFECTIVE_BATCH,
           "max_seq_len": MAX_SEQUENCE, "packing": False, "padding_free": False, "flash_attention_2": False,
           "assistant_only_loss": True, "eot_token_id": EOT, "enable_thinking": False,
           "loss_reduction": "ordinary supervised-token mean per physical microbatch, example-count weighted accumulation",
           "scheduler": {"type": "wall_time_linear_warmup_cosine_decay", "duration_seconds": TRAIN_SECONDS,
                         "warmup_fraction": WARMUP_FRACTION, "peak_lr": PEAK_LR, "min_lr": MIN_LR,
                         "warmup_start_lr": WARMUP_START_LR},
           "training_budget_seconds": TRAIN_SECONDS, "benchmark": None, "optimizer_pilot": False,
           "fresh_base": True, "resume_old_734": False, "eval_timeout_seconds": args.eval_timeout_seconds,
           "automatic_resume_implemented": False,
           "resume_note": "Checkpoint contains optimizer/scaler/RNG/cursor, but automatic resume is not implemented.",
           "checkpoint_every_updates": 300, "checkpoint_every_seconds": 900}
    atomic_json(out / "run_config.json", cfg)
    atomic_json(out / "progress.json", {"state": "INITIALIZING_FRESH_BASE", "step": 0,
                "training_started": False, "requested_training_wall_seconds": TRAIN_SECONDS})
    try:
        # Required import ordering: no torch/transformers/model import precedes Unsloth.
        from unsloth import FastLanguageModel
        import torch
        from transformers import BitsAndBytesConfig
        import bitsandbytes as bnb
        if not torch.cuda.is_available() or "t4" not in torch.cuda.get_device_name(0).lower():
            raise RuntimeError("this branch requires a T4 GPU")
        if torch.cuda.is_bf16_supported():
            raise RuntimeError("unexpected BF16 GPU; T4 FP16 contract required")
        random.seed(SEED)
        torch.manual_seed(SEED)
        torch.cuda.manual_seed_all(SEED)
        cfg["framework_versions"] = framework_versions()
        cfg["cuda_runtime"] = torch.version.cuda
        cfg["gpu"] = {"name": torch.cuda.get_device_name(0),
                      "total_memory_bytes": torch.cuda.get_device_properties(0).total_memory}
        atomic_json(out / "runtime_versions.json", {"framework_versions": cfg["framework_versions"],
                    "cuda_runtime": cfg["cuda_runtime"], "gpu": cfg["gpu"]})
        quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                  bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
        model, tokenizer = FastLanguageModel.from_pretrained(model_name=MODEL, revision=REVISION,
            use_exact_model_name=True, max_seq_length=MAX_SEQUENCE, dtype=torch.float16,
            load_in_4bit=True, quantization_config=quant, attn_implementation="sdpa")
        commit = getattr(model.config, "_commit_hash", None)
        if commit != REVISION:
            raise ValueError(f"loaded model config commit is not exact pinned revision: {commit}")
        if tokenizer.eos_token_id != EOT or tokenizer.convert_tokens_to_ids("<|im_end|>") != EOT:
            raise ValueError("tokenizer EOT is not exact Qwen3 151645")
        if tokenizer.pad_token_id is None:
            raise ValueError("tokenizer pad token must be explicit")
        cfg["loaded_model_commit"] = commit
        helper = load_helper(args.tokenizer_helper)
        rows, audit = load_view(args.train_view, args.view_manifest, helper, tokenizer)
        atomic_json(out / "input_audit.json", audit)
        atomic_json(out / "structural_audit.json", {**audit, "train_view_sha256": VIEW_SHA256,
                    "train_view_manifest_sha256": MANIFEST_SHA256,
                    "assistant_only_mask_checked": True, "exactly_one_supervised_eot_checked": True})
        fixtures = load_fixtures(args.eval_fixtures)
        contract, contract_sha = eval_contract(fixtures, tokenizer)
        cfg["evaluation_contract_sha256"] = contract_sha
        cfg["system_sha256"] = SYSTEM_SHA256
        cfg["view_rows"] = len(rows)
        atomic_json(out / "evaluation_contract.json", {**contract, "contract_sha256": contract_sha})
        atomic_json(out / "run_config.json", cfg)
        atomic_json(out / "progress.json", {"state": "BASE_EVALUATION_BEFORE_TRAINING", "step": 0,
                    "training_started": False, "config": cfg})
        base = cached_base(out, contract, contract_sha)
        if base is None:
            base = generate_fixtures(model, tokenizer, fixtures, out, "base_before_training",
                         contract, contract_sha, args.eval_timeout_seconds, FastLanguageModel)
            atomic_json(out / "base_generation_provenance.json", {"model": MODEL, "revision": REVISION,
                "fixture_sha256": FIXTURES_SHA256, "system_sha256": SYSTEM_SHA256,
                "contract_sha256": contract_sha, "base_untrained": True, "adapter_loaded": False,
                "max_new_tokens": MAX_NEW_TOKENS, "output_sha256": sha_file(out / "base_generations.jsonl")})
        model = FastLanguageModel.get_peft_model(model, r=16, lora_alpha=16, lora_dropout=0.0,
            bias="none", target_modules=TARGET_MODULES, use_gradient_checkpointing="unsloth",
            random_state=SEED, use_rslora=False, loftq_config=None)
        FastLanguageModel.for_training(model)
        parameters = [p for p in model.parameters() if p.requires_grad]
        if not parameters:
            raise ValueError("no trainable fresh adapter parameters")
        optimizer = bnb.optim.AdamW8bit(parameters, lr=0.0, betas=(0.9, 0.999), weight_decay=0.01)
        scaler = torch.amp.GradScaler("cuda", enabled=True, init_scale=1024.0)
        # Initialize the lazy FP16 scale for a possible first-group nonfinite retry.
        # This creates no gradient and performs no model forward or optimizer step.
        scaler.scale(torch.zeros((), device="cuda"))
        state = {"step": 0, "rows_done": 0, "supervised_tokens": 0, "nonpadding_tokens": 0,
                 "loss_sum": 0.0, "last_group_loss": None, "last_lr": 0.0,
                 "total_retries": 0, "nonfinite_retries": 0, "oom_retries": 0,
                 "total_failed_group_attempts": 0, "nonfinite_failed_attempts": 0, "oom_failed_attempts": 0,
                 "total_group_attempts": 0, "unique_ids": set(), "unique_cases": set(),
                 "exposures_by_mode": Counter(), "exposures_by_grade": Counter(), "exposures_by_family": Counter()}
        ids_path = out / "successful_ids.jsonl"
        with ids_path.open("x", encoding="utf-8") as stream:
            stream.flush()
            os.fsync(stream.fileno())
        epoch, batch_cursor = 0, 0
        batches = make_length_batches(rows, epoch)
        clock = {"first_optimizer_group_begin_unix": time.time(), "training_budget_seconds": TRAIN_SECONDS}
        train_start = time.monotonic()
        clock["first_optimizer_group_begin_monotonic"] = train_start
        clock["deadline_monotonic"] = train_start + TRAIN_SECONDS
        clock["deadline_unix"] = clock["first_optimizer_group_begin_unix"] + TRAIN_SECONDS
        clock["started_utc"] = datetime.fromtimestamp(clock["first_optimizer_group_begin_unix"], timezone.utc).isoformat()
        cfg["clock"] = clock
        atomic_json(out / "run_config.json", cfg)
        atomic_json(out / "progress.json", {"state": "FIRST_OPTIMIZER_GROUP_BEGIN", "step": 0,
                    "training_started": False, "optimizer_group_entered": True, "clock": clock, "config": cfg})
        last_checkpoint = train_start
        final_generation = None
        optimizer.zero_grad(set_to_none=True)
        try:
            while group_may_start(time.monotonic(), train_start):
                if batch_cursor >= len(batches):
                    epoch += 1
                    batches = make_length_batches(rows, epoch)
                    batch_cursor = 0
                group = batches[batch_cursor:batch_cursor + ACCUMULATION]
                if len(group) != ACCUMULATION or sum(map(len, group)) != EFFECTIVE_BATCH:
                    raise ValueError("pinned 16000-row view must yield full optimizer groups of 16")
                group_ids = [i for batch in group for i in batch]
                group_rows = len(group_ids)
                rng_cpu, rng_cuda = torch.get_rng_state(), torch.cuda.get_rng_state_all()
                retries = 0
                elapsed_at_entry = time.monotonic() - train_start
                if elapsed_at_entry >= TRAIN_SECONDS:
                    break
                lr = lr_at_elapsed(elapsed_at_entry)
                for param_group in optimizer.param_groups:
                    param_group["lr"] = lr
                while True:
                    state["total_group_attempts"] += 1
                    optimizer.zero_grad(set_to_none=True)
                    group_loss = 0.0
                    supervised = nonpadding = 0
                    failure = None
                    try:
                        for indices in group:
                            items = [rows[i] for i in indices]
                            batch = collate(items, tokenizer, "cuda")
                            with torch.autocast("cuda", dtype=torch.float16):
                                loss = model(**batch).loss * (len(items) / group_rows)
                            if not bool(torch.isfinite(loss).item()):
                                raise FloatingPointError("nonfinite loss")
                            scaler.scale(loss).backward()
                            group_loss += float(loss.detach())
                            nonpadding += int(batch["attention_mask"].sum().item())
                            supervised += sum(sum(x != -100 for x in item["encoded"]["labels"]) for item in items)
                        scaler.unscale_(optimizer)
                        grads = [p.grad for p in parameters if p.grad is not None]
                        if not grads or not all(bool(torch.isfinite(g).all().item()) for g in grads):
                            raise FloatingPointError("nonfinite or absent gradients")
                        grad_norm = torch.nn.utils.clip_grad_norm_(parameters, 1.0)
                        if not bool(torch.isfinite(grad_norm).item()):
                            raise FloatingPointError("nonfinite gradient norm")
                        old_scale = scaler.get_scale()
                        scaler.step(optimizer)
                        scaler.update()
                        if scaler.get_scale() < old_scale:
                            raise FloatingPointError("AMP skipped optimizer step")
                        torch.cuda.synchronize()
                    except torch.cuda.OutOfMemoryError:
                        failure = "oom"
                    except FloatingPointError:
                        failure = "nonfinite"
                    if failure is None:
                        break
                    state["total_failed_group_attempts"] += 1
                    state[f"{failure}_failed_attempts"] += 1
                    optimizer.zero_grad(set_to_none=True)
                    torch.set_rng_state(rng_cpu)
                    torch.cuda.set_rng_state_all(rng_cuda)
                    if retries >= 3:
                        raise FloatingPointError(f"same optimizer group failed after 3 retries: {failure}")
                    state["total_retries"] += 1
                    state[f"{failure}_retries"] += 1
                    retries += 1
                    scaler.update(new_scale=max(1.0, scaler.get_scale() / 2))
                    if failure == "oom":
                        torch.cuda.empty_cache()
                    # Retries belong to this in-flight group, never extend the deadline.
                state["step"] += 1
                state["rows_done"] += group_rows
                state["supervised_tokens"] += supervised
                state["nonpadding_tokens"] += nonpadding
                state["loss_sum"] += group_loss
                state["last_group_loss"] = group_loss
                state["last_lr"] = lr
                state["last_group_retries"] = retries
                state["last_gradient_norm"] = float(grad_norm)
                state["scaler_scale"] = float(scaler.get_scale())
                state["gradients_finite_after_optimizer_step"] = True
                state["peak_vram_bytes"] = torch.cuda.max_memory_allocated()
                for i in group_ids:
                    row = rows[i]
                    state["unique_ids"].add(row["sample_id"])
                    state["unique_cases"].add(row["source_case_id"])
                    state["exposures_by_mode"][row["mode"]] += 1
                    state["exposures_by_grade"][str(row["grade"])] += 1
                    state["exposures_by_family"][row["family"]] += 1
                batch_cursor += len(group)
                append_jsonl(ids_path, [{"step": state["step"], "sample_id": rows[i]["sample_id"],
                             "epoch": epoch} for i in group_ids])
                metrics = snapshot_metrics(state, rows, train_start)
                cursor = {"epoch": epoch, "next_microbatch": batch_cursor, "seed": SEED,
                          "microbatches_per_epoch": len(batches)}
                if state["step"] == 1 or state["step"] % 10 == 0:
                    atomic_json(out / "progress.json", {"state": "TRAINING", "training_started": True,
                                **metrics, "clock": clock, "cursor": cursor})
                if not group_may_start(time.monotonic(), train_start):
                    break
                if state["step"] == 1 or state["step"] % 300 == 0 or time.monotonic() - last_checkpoint >= 900:
                    save_start = time.monotonic()
                    final_generation = save_generation(model, tokenizer, optimizer, scaler, out, cfg, metrics, cursor, clock)
                    last_checkpoint = time.monotonic()
                    append_jsonl(out / "checkpoint_timing.jsonl", [{"step": state["step"],
                        "rows_done": state["rows_done"], "generation": final_generation.name,
                        "save_seconds": last_checkpoint - save_start, "measured_unix": time.time()}])
                # No fixed target-step/view-epoch limit: immediately reshuffle on exhaustion.
        except BaseException:
            metrics = snapshot_metrics(state, rows, train_start)
            metrics["stop_reason"] = "ERROR"
            try:
                save_generation(model, tokenizer, optimizer, scaler, out, cfg, metrics,
                    {"epoch": epoch, "next_microbatch": batch_cursor, "seed": SEED,
                     "microbatches_per_epoch": len(batches)}, clock)
            except BaseException as save_error:
                atomic_json(out / "emergency_save_error.json", {"error": repr(save_error)})
            raise
        train_stop = time.monotonic()
        metrics = snapshot_metrics(state, rows, train_start, train_stop)
        metrics["stop_reason"] = "FIVE_HOUR_WALL_DEADLINE_AT_GROUP_BOUNDARY"
        metrics["training_stopped_unix"] = time.time()
        metrics["full_requested_training_window_reached"] = metrics["training_wall_seconds"] >= TRAIN_SECONDS
        atomic_json(out / "final_metrics.json", metrics)
        final_generation = save_generation(model, tokenizer, optimizer, scaler, out, cfg, metrics,
                   {"epoch": epoch, "next_microbatch": batch_cursor, "seed": SEED,
                    "microbatches_per_epoch": len(batches)}, clock)
        # The adapter is safely exported before any after-training generation can fail.
        export_adapter(final_generation, out)
        atomic_json(out / "progress.json", {"state": "TRAINING_COMPLETE_ADAPTER_SAFE_BEGIN_EVAL",
                    "training_started": True, **metrics, "clock": clock,
                    "adapter_zip_sha256": sha_file(out / "adapter_export.zip")})
        after = generate_fixtures(model, tokenizer, fixtures, out, "adapter_after_training",
                     contract, contract_sha, args.eval_timeout_seconds, FastLanguageModel)
        complete = {"schema": "MathVisionKid.corrective5h.complete.v1", "complete": True,
                    "step": state["step"], "rows_done": state["rows_done"], "metrics": metrics,
                    "config": cfg, "base_outputs": len(base), "adapter_outputs": len(after),
                    "eval_fixture_count": 28, "evaluation_contract_sha256": contract_sha,
                    "adapter_zip_sha256": sha_file(out / "adapter_export.zip"),
                    "adapter_zip_bytes": (out / "adapter_export.zip").stat().st_size,
                    "final_checkpoint": strict_json((out / "latest.json").read_text(encoding="utf-8")),
                    "requested_training_wall_seconds": TRAIN_SECONDS,
                    "actual_training_wall_seconds": metrics["training_wall_seconds"],
                    "full_requested_training_window_reached": metrics["full_requested_training_window_reached"],
                    "base_output_sha256": sha_file(out / "base_generations.jsonl"),
                    "adapter_output_sha256": sha_file(out / "adapter_generations.jsonl"),
                    "semantic_quality_claim": False}
        bound_files = ["run_config.json", "runtime_versions.json", "structural_audit.json", "input_audit.json",
                       "final_metrics.json", "successful_ids.jsonl", "checkpoint_timing.jsonl", "latest.json",
                       "evaluation_contract.json", "base_generations.jsonl", "base_generation_provenance.json",
                       "adapter_generations.jsonl", "adapter_export.zip"]
        complete["files"] = {name: sha_file(out / name) for name in bound_files}
        complete["file_bytes"] = {name: (out / name).stat().st_size for name in bound_files}
        atomic_json(out / "run_complete.json", complete)
        atomic_json(out / "progress.json", {"state": "COMPLETE", **complete})
        print(canonical({"state": "COMPLETE", "step": state["step"], "rows_done": state["rows_done"],
                         "training_wall_seconds": metrics["training_wall_seconds"]}), flush=True)
    except BaseException as error:
        report = {"schema": "MathVisionKid.corrective5h.error.v1", "state": "ERROR", "complete": False,
                  "error_type": type(error).__name__, "error": str(error), "traceback": traceback.format_exc(),
                  "observed_unix": time.time(), "step": state["step"] if state else 0,
                  "rows_done": state["rows_done"] if state else 0,
                  "total_retries": state["total_retries"] if state else 0,
                  "total_failed_group_attempts": state["total_failed_group_attempts"] if state else 0,
                  "training_wall_seconds": time.monotonic() - train_start if train_start is not None else 0,
                  "adapter_safe_before_eval": (out / "adapter_export.zip").exists(), "config": cfg}
        atomic_json(out / "error.json", report)
        atomic_json(out / "progress.json", report)
        raise


if __name__ == "__main__":
    main()
