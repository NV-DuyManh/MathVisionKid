#!/usr/bin/env python3
"""Resume the current corrective branch under the owner's revised Colab deadline.

Original worker/checkpoints remain preserved. Tuning makes no optimizer updates.
All training uses the exact original micro2 pair loss and same16 sample order.
No new group starts after 05:13:23Z; final export/eval must finish by05:28:23Z.
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
import signal
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
    """Original scheduler retained for provenance; production v2 uses replan_lr."""
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
            "training_wall_seconds": elapsed, "requested_training_wall_seconds": None,
            "budget_scope": BUDGET_SCOPE,
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
    resume = {"schema": "MathVisionKid.corrective5h.resume.v1", "fresh_base_branch": False,
              "step": metrics["step"], "rows_done": metrics["rows_done"], "cursor": cursor,
              "optimizer": optimizer.state_dict(), "scaler": scaler.state_dict(),
              "optimizer_parameter_names": cfg.get("optimizer_parameter_names"),
              "torch_cpu_rng": torch.get_rng_state(), "torch_cuda_rng": torch.cuda.get_rng_state_all(),
              "python_rng": random.getstate(), "time_scheduler": {"elapsed_seconds": metrics["training_wall_seconds"],
              "duration_seconds": TRAIN_SECONDS, "warmup_fraction": WARMUP_FRACTION,
              "peak_lr": PEAK_LR, "min_lr": MIN_LR, "warmup_start_lr": WARMUP_START_LR,
              "last_group_lr": metrics.get("last_lr")},
              "consumed_train_seconds": metrics["training_wall_seconds"],
              "automatic_resume_implemented": True,
              "resume_note": "Explicit v2 resume requires coherent optimizer state, hash-bound generation and acknowledged log prefix.",
              "clock": clock, "successful_ids_log_bytes": (out / "successful_ids.jsonl").stat().st_size}
    resume["time_scheduler"]["replanned_scheduler"] = cfg.get("scheduler")
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
    parser.add_argument("--resume-generation", type=Path, required=True)
    parser.add_argument("--resume-successful-ids", type=Path, required=True)
    parser.add_argument("--resume-base-dir", type=Path, required=True)
    parser.add_argument("--owner-budget-revision", type=Path, required=True)
    parser.add_argument("--resume-source-error", type=Path)
    parser.add_argument("--pair-loss-helper", type=Path)
    return parser.parse_args()



HARD_DEADLINE_UNIX = 1792819703.0
TRAIN_STOP_UNIX = 1792818803.0
RESERVE_SECONDS = 900
BUDGET_SCOPE = "OWNER_REVISED_REMAINING_COLAB_WINDOW_V2"
OWNER_BUDGET_SHA256 = "e3e5b960b65e618909329e18bbf2656e4d80435a445b60e3102a176f254aab00"
STOP_REQUESTED = None
PAIRLOSS_HELPER = None
PAIRLOSS_HELPER_SHA256 = "6c737d6ea42a92800b3df469ab9dac2909cef21c52701777fee8da97c5f0b6fb"


def request_boundary_stop(signum, frame):
    global STOP_REQUESTED
    STOP_REQUESTED = {"signal": signum, "requested_unix": time.time()}


def optimizer_coherence(optimizer_state, acknowledged_step, parameters=None):
    """Reject interrupted AdamW updates, partial initialization and mixed steps."""
    expected_ids = [pid for group in optimizer_state["param_groups"] for pid in group["params"]]
    states = optimizer_state["state"]
    if len(set(expected_ids)) != len(expected_ids) or set(states) != set(expected_ids):
        raise ValueError("optimizer parameter state set is incomplete or ambiguous")
    steps = []
    parameter_list = list(parameters) if parameters is not None else None
    if parameter_list is not None and len(parameter_list) != len(expected_ids):
        raise ValueError("optimizer/model trainable parameter counts differ")
    def finite_state(value):
        if isinstance(value, dict):
            for nested in value.values():
                finite_state(nested)
        elif isinstance(value, (tuple, list)):
            for nested in value:
                finite_state(nested)
        elif hasattr(value, "is_floating_point") and value.is_floating_point():
            import torch
            if not bool(torch.isfinite(value).all().item()):
                raise ValueError("nonfinite floating optimizer state")
        elif isinstance(value, float) and not math.isfinite(value):
            raise ValueError("nonfinite scalar optimizer state")
    for index, pid in enumerate(expected_ids):
        finite_state(states[pid])
        if parameter_list is not None:
            for key in ("state1", "state2"):
                tensor = states[pid].get(key)
                if tensor is None or tensor.numel() != parameter_list[index].numel():
                    raise ValueError(f"optimizer {key} shape does not match parameter index {index}")
        value = states[pid].get("step")
        if hasattr(value, "item"):
            value = value.item()
        if value is None or int(value) != value or int(value) != acknowledged_step:
            raise ValueError(f"incoherent AdamW step for parameter {pid}: {value} vs {acknowledged_step}")
        steps.append(int(value))
    if not steps:
        raise ValueError("empty optimizer state")
    return {"parameter_states": len(steps), "all_parameter_steps": acknowledged_step, "coherent": True}


def validate_resume_files(generation):
    manifest = strict_json((generation / "generation_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("complete") is not True:
        raise ValueError("resume generation is not complete")
    for name, expected_sha in manifest["files"].items():
        if Path(name).name != name or sha_file(generation / name) != expected_sha:
            raise ValueError(f"resume file/hash mismatch: {name}")
        if (generation / name).stat().st_size != manifest["file_bytes"][name]:
            raise ValueError(f"resume file size mismatch: {name}")
    metrics = strict_json((generation / "metrics.json").read_text(encoding="utf-8"))
    cfg = strict_json((generation / "run_config.json").read_text(encoding="utf-8"))
    pins = {"model": MODEL, "revision": REVISION, "train_view_sha256": VIEW_SHA256,
            "train_view_manifest_sha256": MANIFEST_SHA256, "fixture_sha256": FIXTURES_SHA256,
            "tokenizer_helper_sha256": TOKENIZER_HELPER_SHA256, "seed": SEED,
            "effective_batch": EFFECTIVE_BATCH, "lora_r": 16, "lora_alpha": 16,
            "lora_dropout": 0.0, "target_modules": TARGET_MODULES}
    if any(cfg.get(k) != v for k, v in pins.items()):
        raise ValueError("resume configuration differs from pinned training contract")
    if manifest["step"] != metrics["step"] or manifest["rows_done"] != metrics["rows_done"]:
        raise ValueError("checkpoint metrics/manifest step disagreement")
    if metrics["rows_done"] != metrics["step"] * EFFECTIVE_BATCH:
        raise ValueError("checkpoint exposures are not full optimizer groups")
    return manifest, metrics, cfg


def rebuild_acknowledged_state(log_path, prefix_bytes, metrics, rows, cursor):
    """Copy only the CP-bound log prefix; verify exact original same16 sequence."""
    raw = Path(log_path).read_bytes()[:prefix_bytes]
    if len(raw) != prefix_bytes or (raw and not raw.endswith(b"\n")):
        raise ValueError("successful-ID log checkpoint prefix is missing or partial")
    entries = [strict_json(line) for line in raw.decode("utf-8").splitlines()]
    if len(entries) != metrics["rows_done"]:
        raise ValueError("acknowledged log length differs from checkpoint exposures")
    by_id = {row["sample_id"]: row for row in rows}
    expected_epoch, expected_cursor, order = 0, 0, make_length_batches(rows, 0)
    sup = nonpad = 0
    unique, cases = set(), set()
    counts = {key: Counter() for key in ("mode", "grade", "family")}
    for offset in range(0, len(entries), EFFECTIVE_BATCH):
        if expected_cursor >= len(order):
            expected_epoch += 1
            expected_cursor = 0
            order = make_length_batches(rows, expected_epoch)
        ids = [rows[i]["sample_id"] for batch in order[expected_cursor:expected_cursor + ACCUMULATION] for i in batch]
        actual = entries[offset:offset + EFFECTIVE_BATCH]
        if [entry.get("sample_id") for entry in actual] != ids:
            raise ValueError("acknowledged log differs from deterministic original optimizer order")
        if any(entry.get("step") != offset // EFFECTIVE_BATCH + 1 or entry.get("epoch") != expected_epoch for entry in actual):
            raise ValueError("acknowledged log step/epoch disagreement")
        expected_cursor += ACCUMULATION
        for entry in actual:
            row = by_id[entry["sample_id"]]
            unique.add(row["sample_id"])
            cases.add(row["source_case_id"])
            sup += sum(label != -100 for label in row["encoded"]["labels"])
            nonpad += len(row["encoded"]["input_ids"])
            for key in counts:
                counts[key][str(row[key])] += 1
    if (cursor.get("epoch"), cursor.get("next_microbatch")) != (expected_epoch, expected_cursor):
        raise ValueError("checkpoint cursor disagrees with acknowledged log")
    if sup != metrics["supervised_tokens"] or nonpad != metrics["nonpadding_tokens"]:
        raise ValueError("checkpoint token counters disagree with acknowledged IDs")
    if len(unique) != metrics["unique_examples"] or len(cases) != metrics["unique_source_cases"]:
        raise ValueError("checkpoint unique counts disagree with acknowledged IDs")
    for key in counts:
        if dict(counts[key]) != metrics[f"exposures_by_{key}"]:
            raise ValueError(f"checkpoint exposure distribution disagreement: {key}")
    state = {k: v for k, v in metrics.items() if k not in (
        "unique_examples", "unique_source_cases", "exposures_by_mode", "exposures_by_grade", "exposures_by_family")}
    state.update(unique_ids=unique, unique_cases=cases, exposures_by_mode=counts["mode"],
                 exposures_by_grade=counts["grade"], exposures_by_family=counts["family"])
    for stale in ("stop_reason", "training_stopped_unix", "full_requested_training_window_reached",
                  "revised_training_cutoff_reached", "deadline_boundary_overrun_seconds"):
        state.pop(stale, None)
    return state, raw


def replan_lr(elapsed, prior_elapsed, remaining, prior_lr):
    """Continue warmup once if needed; then cosine to floor by revised cutoff."""
    active = max(0.0, elapsed - prior_elapsed)
    warmup_left = max(0.0, TRAIN_SECONDS * WARMUP_FRACTION - prior_elapsed)
    warmup_left = min(warmup_left, max(0.0, remaining * 0.2))
    if warmup_left and active < warmup_left:
        return prior_lr + (PEAK_LR - prior_lr) * active / warmup_left
    start_lr = PEAK_LR if warmup_left else max(MIN_LR, prior_lr)
    fraction = min(1.0, max(0.0, (active - warmup_left) / max(remaining - warmup_left, 1e-6)))
    return MIN_LR + (start_lr - MIN_LR) * (1 + math.cos(math.pi * fraction)) / 2


def regroup_same16(group_ids, rows, physical):
    if physical not in (2, 4, 8) or len(group_ids) != EFFECTIVE_BATCH or (physical != 2 and PAIRLOSS_HELPER is None):
        raise ValueError("only exact original micro2 pair-loss objective is implemented")
    ordered = list(group_ids)
    return [ordered[i:i + physical] for i in range(0, len(ordered), physical)]


def exact_pair_forward_loss(model, batch, physical):
    if physical == 2:
        return model(**batch).loss * (2 / EFFECTIVE_BATCH)
    if PAIRLOSS_HELPER is None:
        raise ValueError("larger physical batches require exact pair loss helper")
    previous = os.environ.get("UNSLOTH_RETURN_LOGITS")
    os.environ["UNSLOTH_RETURN_LOGITS"] = "1"
    try:
        return PAIRLOSS_HELPER.pair_weighted_forward_loss(model, batch, group_rows=EFFECTIVE_BATCH)
    finally:
        if previous is None:
            os.environ.pop("UNSLOTH_RETURN_LOGITS", None)
        else:
            os.environ["UNSLOTH_RETURN_LOGITS"] = previous


def oom_fallback(physical, checkpointing):
    if physical in (8, 4):
        return physical // 2, "on"
    if physical == 2 and checkpointing == "off":
        return 2, "on"
    raise RuntimeError("micro2 with checkpointing already on; no smaller objective-preserving OOM fallback")


def measure_physical_batches(model, tokenizer, rows, group_ids, optimizer, scaler, cutoff_unix):
    """Measure checkpointing on/off at exact original micro2 objective; no updates."""
    import copy
    import torch
    parameters = [p for p in model.parameters() if p.requires_grad]
    cpu_rng, cuda_rng, python_rng = torch.get_rng_state(), torch.cuda.get_rng_state_all(), random.getstate()
    scale_state = copy.deepcopy(scaler.state_dict())
    budget_end = min(time.monotonic() + 240, time.monotonic() + max(0, cutoff_unix - time.time() - 90))
    stress_ids = sorted(range(len(rows)), key=lambda i: len(rows[i]["encoded"]["input_ids"]), reverse=True)[:16]
    sorted_ids = sorted(range(len(rows)), key=lambda i: len(rows[i]["encoded"]["input_ids"]))
    representative = [sorted_ids[:16], sorted_ids[len(rows)//2 - 8:len(rows)//2 + 8], sorted_ids[-16:]]
    results, selected = [], "on"
    def set_checkpointing(mode):
        if mode == "off":
            model.gradient_checkpointing_disable()
            if bool(model.is_gradient_checkpointing):
                raise RuntimeError("checkpointing disable did not take effect")
        else:
            model.gradient_checkpointing_enable()
    def run(ids, physical):
        optimizer.zero_grad(set_to_none=True)
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()
        started = time.monotonic()
        total_loss = 0.0
        for indices in regroup_same16(ids, rows, physical):
            batch = collate([rows[i] for i in indices], tokenizer, "cuda")
            with torch.autocast("cuda", dtype=torch.float16):
                loss = exact_pair_forward_loss(model, batch, physical)
            if not bool(torch.isfinite(loss).item()):
                raise FloatingPointError("nonfinite benchmark loss")
            scaler.scale(loss).backward()
            total_loss += float(loss.detach())
        grads = [p.grad for p in parameters if p.grad is not None]
        if not grads:
            raise FloatingPointError("nonfinite benchmark gradients")
        # Single aggregate norm check; benchmark gradients are discarded afterward.
        norm = torch.nn.utils.clip_grad_norm_(parameters, float("inf"), foreach=True)
        if not bool(torch.isfinite(norm).item()):
            raise FloatingPointError("nonfinite benchmark gradient norm")
        torch.cuda.synchronize()
        return time.monotonic() - started, torch.cuda.max_memory_allocated(), total_loss
    try:
        candidates = [(2, "on"), (2, "off")]
        if PAIRLOSS_HELPER is not None:
            candidates.extend([(4, "on"), (8, "on")])
        for physical, mode in candidates:
            if time.monotonic() >= budget_end:
                break
            result = {"microbatch": physical, "optimizer_updates": 0, "gradient_checkpointing": mode}
            try:
                set_checkpointing(mode)
                torch.set_rng_state(cpu_rng)
                torch.cuda.set_rng_state_all(cuda_rng)
                _, _, parity_loss = run(group_ids, physical)
                if mode == "on" and physical == 2:
                    reference_loss = parity_loss
                    reference_grads = [p.grad.detach().float().cpu().clone() if p.grad is not None else None for p in parameters]
                    relative_error = 0.0
                else:
                    numerator = denominator = 0.0
                    for param, ref in zip(parameters, reference_grads):
                        if (param.grad is None) != (ref is None):
                            raise FloatingPointError("gradient presence differs in checkpointing parity")
                        if ref is not None:
                            current = param.grad.detach().float().cpu()
                            numerator += float((current - ref).square().sum())
                            denominator += float(ref.square().sum())
                    relative_error = math.sqrt(numerator / max(denominator, 1e-30))
                    if abs(parity_loss - reference_loss) > 0.002 + abs(reference_loss) * 0.002 or relative_error > 0.02:
                        raise FloatingPointError("checkpointing loss/gradient parity exceeded tolerance")
                reps, peaks = [], []
                for ids in representative:
                    if time.monotonic() >= budget_end:
                        raise TimeoutError("bounded tuning budget reached")
                    torch.set_rng_state(cpu_rng)
                    torch.cuda.set_rng_state_all(cuda_rng)
                    seconds, peak, _ = run(ids, physical)
                    reps.append(seconds)
                    peaks.append(peak)
                memory_margin = torch.cuda.get_device_properties(0).total_memory - max(peaks)
                result.update(state="PASS" if memory_margin >= 1024 ** 3 else "REJECT_MEMORY_MARGIN",
                              repeat_seconds=reps, mean_group_seconds=sum(reps) / len(reps),
                              representative_groups=["short16", "median16", "longest16"],
                              peak_vram_bytes=max(peaks), memory_margin_bytes=memory_margin,
                              worst16_length_stress=True, parity_loss=parity_loss,
                              gradient_relative_l2_error=relative_error,
                              parity_tolerances={"loss_atol": 0.002, "loss_rtol": 0.002, "gradient_relative_l2": 0.02})
            except (torch.cuda.OutOfMemoryError, FloatingPointError, RuntimeError, TimeoutError, NotImplementedError, AttributeError, TypeError, ValueError) as error:
                result.update(state="REJECT", error=type(error).__name__)
            finally:
                optimizer.zero_grad(set_to_none=True)
                torch.cuda.empty_cache()
            results.append(result)
        passing = [result for result in results if result.get("state") == "PASS"]
        if not passing:
            raise RuntimeError("no finite physical batch with 1GiB worst-length memory margin")
        baseline = next((r for r in passing if r["gradient_checkpointing"] == "on" and r["microbatch"] == 2), None)
        chosen = min(passing, key=lambda r: r["mean_group_seconds"])
        if baseline and chosen["mean_group_seconds"] > baseline["mean_group_seconds"] * 0.97:
            chosen = baseline
        selected = chosen["gradient_checkpointing"]
        return chosen["microbatch"], {"selected_microbatch": chosen["microbatch"], "selected_gradient_checkpointing": selected, "candidates": results,
                "same16_sample_ids": [rows[i]["sample_id"] for i in group_ids],
                "optimizer_updates": 0, "rng_scaler_gradients_restored": True,
                "physical4_8": "Optional hash-pinned exact original pair CE; eligible only after actual model loss/gradient parity and representative/worst-length memory checks.",
                "loss_objective": "Exact unchanged original micro2 pair mean weighted2/16, original pair order retained."}
    finally:
        set_checkpointing(selected)
        optimizer.zero_grad(set_to_none=True)
        scaler.load_state_dict(scale_state)
        torch.set_rng_state(cpu_rng)
        torch.cuda.set_rng_state_all(cuda_rng)
        random.setstate(python_rng)


def main():
    global PAIRLOSS_HELPER
    args = parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    if any((out / name).exists() for name in ("latest.json", "successful_ids.jsonl", "run_complete.json", "error.json")):
        raise FileExistsError("fresh branch refuses existing training state; no implicit resume")
    if args.eval_timeout_seconds <= 0:
        raise ValueError("evaluation timeout must be positive")
    manifest_before, prior_metrics, prior_config = validate_resume_files(args.resume_generation)
    if sha_file(args.owner_budget_revision) != OWNER_BUDGET_SHA256:
        raise ValueError("owner budget revision exact file SHA mismatch")
    if args.pair_loss_helper is not None:
        if sha_file(args.pair_loss_helper) != PAIRLOSS_HELPER_SHA256:
            raise ValueError("exact pair loss helper SHA mismatch")
        spec = importlib.util.spec_from_file_location("exact_pair_loss_helper", args.pair_loss_helper)
        PAIRLOSS_HELPER = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(PAIRLOSS_HELPER)
    if prior_metrics.get("stop_reason") == "ERROR":
        if args.resume_source_error is None:
            raise ValueError("emergency checkpoint requires explicit source interruption traceback")
        interruption = strict_json(args.resume_source_error.read_text(encoding="utf-8"))
        trace = interruption.get("traceback", "")
        if (interruption.get("error_type") != "KeyboardInterrupt" or ".backward()" not in trace
                or "scaler.step(optimizer)" in trace or "optimizer.step(" in trace):
            raise ValueError("emergency interruption was not verified inside pre-update backward; use last regular generation")
    if time.time() >= TRAIN_STOP_UNIX - 120:
        raise TimeoutError("insufficient revised owner budget to load and resume")
    prior_consumed = float(prior_metrics["training_wall_seconds"])
    state = None
    train_start = None
    cfg = {"schema": "MathVisionKid.corrective_optimized_v2.run.v1", "model": MODEL, "revision": REVISION,
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
    cfg.update(budget_scope=BUDGET_SCOPE, hard_deadline_unix=HARD_DEADLINE_UNIX,
               hard_deadline_utc="2026-10-24T05:28:23Z", train_stop_unix=TRAIN_STOP_UNIX,
               train_stop_utc="2026-10-24T05:13:23Z", reserve_seconds=RESERVE_SECONDS,
               prior_training_consumed_seconds=prior_consumed, fresh_base=False,
               owner_budget_revision_sha256=OWNER_BUDGET_SHA256,
               pair_loss_helper_sha256=PAIRLOSS_HELPER_SHA256 if PAIRLOSS_HELPER is not None else None,
               automatic_resume_implemented=True, resume_generation=str(args.resume_generation),
               resume_generation_manifest_sha256=sha_file(args.resume_generation / "generation_manifest.json"),
               resume_note="Explicit coherent optimizer/scaler/RNG/cursor/log-prefix resume of current corrective branch.")
    atomic_bytes(out / "owner_budget_revision_config.json", args.owner_budget_revision.read_bytes())
    atomic_json(out / "run_config.json", cfg)
    atomic_json(out / "progress.json", {"state": "INITIALIZING_EXPLICIT_RESUME", "step": 0,
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
        import shutil
        for name in ("base_generations.jsonl", "base_generation_provenance.json"):
            shutil.copyfile(args.resume_base_dir / name, out / name)
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
        from peft import set_peft_model_state_dict, get_peft_model_state_dict
        from peft.utils.save_and_load import load_peft_weights
        adapter_state = load_peft_weights(str(args.resume_generation), device="cpu")
        loaded = set_peft_model_state_dict(model, adapter_state)
        if (getattr(loaded, "unexpected_keys", []) or
                any("lora_" in key for key in getattr(loaded, "missing_keys", []))):
            raise ValueError("missing or unexpected adapter weight keys on resume")
        actual_adapter = get_peft_model_state_dict(model)
        if set(actual_adapter) != set(adapter_state):
            raise ValueError("resume adapter keys do not equal the exact expected LoRA key set")
        for key, tensor in actual_adapter.items():
            expected = adapter_state[key].to(device="cpu", dtype=tensor.dtype)
            if tensor.shape != expected.shape or not torch.equal(tensor.detach().cpu(), expected):
                raise ValueError(f"resume adapter tensor differs after loading: {key}")
        del actual_adapter, adapter_state
        FastLanguageModel.for_training(model)
        parameters = [p for p in model.parameters() if p.requires_grad]
        if not parameters:
            raise ValueError("no trainable fresh adapter parameters")
        optimizer = bnb.optim.AdamW8bit(parameters, lr=0.0, betas=(0.9, 0.999), weight_decay=0.01)
        scaler = torch.amp.GradScaler("cuda", enabled=True, init_scale=1024.0)
        # Initialize the lazy FP16 scale for a possible first-group nonfinite retry.
        # This creates no gradient and performs no model forward or optimizer step.
        scaler.scale(torch.zeros((), device="cuda"))
        resume = torch.load(args.resume_generation / "resume_state.pt", map_location="cpu", weights_only=False)
        if resume["step"] != prior_metrics["step"] or resume["rows_done"] != prior_metrics["rows_done"]:
            raise ValueError("resume tensor state/metrics disagreement")
        coherent = optimizer_coherence(resume["optimizer"], prior_metrics["step"], parameters)
        parameter_names = [name for name, param in model.named_parameters() if param.requires_grad]
        if resume.get("optimizer_parameter_names", parameter_names) != parameter_names:
            raise ValueError("recorded optimizer parameter name/order differs on resume")
        cfg["optimizer_parameter_names"] = parameter_names
        state, prefix = rebuild_acknowledged_state(args.resume_successful_ids,
            resume["successful_ids_log_bytes"], prior_metrics, rows, resume["cursor"])
        optimizer.load_state_dict(resume["optimizer"])
        scaler.load_state_dict(resume["scaler"])
        atomic_bytes(out / "successful_ids.jsonl", prefix)
        ids_path = out / "successful_ids.jsonl"
        atomic_json(out / "resume_validation.json", {"coherence": coherent,
            "source_generation_manifest_sha256": cfg["resume_generation_manifest_sha256"],
            "acknowledged_log_prefix_sha256": digest(prefix), "acknowledged_log_prefix_bytes": len(prefix),
            "step": state["step"], "rows_done": state["rows_done"], "prior_training_consumed_seconds": prior_consumed,
            "interruption_traceback_sha256": sha_file(args.resume_source_error) if args.resume_source_error else None,
            "trajectory_note": "Emergency RNG may be from partial backward; no exact-trajectory or RNG-rewind guarantee.",
            "optimizer_step_equality_necessary_not_general_atomicity_proof": True})
        epoch, batch_cursor = resume["cursor"]["epoch"], resume["cursor"]["next_microbatch"]
        batches = make_length_batches(rows, epoch)
        if batch_cursor == len(batches):
            epoch += 1
            batch_cursor = 0
            batches = make_length_batches(rows, epoch)
        torch.set_rng_state(resume["torch_cpu_rng"])
        torch.cuda.set_rng_state_all(resume["torch_cuda_rng"])
        random.setstate(resume["python_rng"])
        next_ids = [i for batch in batches[batch_cursor:batch_cursor + ACCUMULATION] for i in batch]
        physical, tuning = measure_physical_batches(model, tokenizer, rows, next_ids, optimizer, scaler, TRAIN_STOP_UNIX)
        atomic_json(out / "physical_batch_tuning.json", tuning)
        cfg.update(microbatch=physical, grad_accumulation=EFFECTIVE_BATCH // physical,
                   physical_batch_tuning=tuning, ordering="Original micro2 shuffled groups-of16 retained",
                   gradient_checkpointing=tuning["selected_gradient_checkpointing"],
                   cpu_sync_optimization="foreach aggregate finite-norm check replaces per-parameter item sync",
                   loss_reduction="Original micro2 pair supervised-token mean times2/16; larger chunks sum exact original pair means.")
        # Offline/setup/benchmark time is excluded from consumed train seconds.
        segment_start = time.monotonic()
        segment_start_unix = time.time()
        train_start = segment_start - prior_consumed
        replanned_remaining = max(0.0, TRAIN_STOP_UNIX - segment_start_unix)
        prior_lr = float(prior_metrics["last_lr"])
        clock = {"segment_begin_unix": segment_start_unix, "segment_begin_monotonic": segment_start,
                 "prior_training_consumed_seconds": prior_consumed, "budget_scope": BUDGET_SCOPE,
                 "deadline_unix": TRAIN_STOP_UNIX, "hard_deadline_unix": HARD_DEADLINE_UNIX,
                 "deadline_monotonic": segment_start + replanned_remaining,
                 "offline_time_excluded": True}
        cfg["clock"] = clock
        cfg["scheduler"] = {"type": "continue_remaining_warmup_then_replanned_cosine",
            "prior_elapsed_seconds": prior_consumed, "prior_lr": prior_lr,
            "segment_remaining_seconds": replanned_remaining, "floor_lr": MIN_LR,
            "warmup_restarted": False}
        atomic_json(out / "run_config.json", cfg)
        atomic_json(out / "progress.json", {"state": "RESUMED_OPTIMIZER_GROUP_BEGIN", "step": state["step"],
            "rows_done": state["rows_done"], "training_started": True, "clock": clock, "config": cfg})
        last_checkpoint = segment_start
        resumed_step = state["step"]
        for name in ("SIGINT", "SIGTERM", "SIGUSR1"):
            if hasattr(signal, name):
                signal.signal(getattr(signal, name), request_boundary_stop)
        final_generation = None
        optimizer.zero_grad(set_to_none=True)
        try:
            while time.time() < TRAIN_STOP_UNIX and time.monotonic() < clock["deadline_monotonic"]:
                if STOP_REQUESTED is not None or (out / "stop_after_current_group.json").exists():
                    break
                if batch_cursor >= len(batches):
                    epoch += 1
                    batches = make_length_batches(rows, epoch)
                    batch_cursor = 0
                group = batches[batch_cursor:batch_cursor + ACCUMULATION]
                if len(group) != ACCUMULATION or sum(map(len, group)) != EFFECTIVE_BATCH:
                    raise ValueError("pinned 16000-row view must yield full optimizer groups of 16")
                group_ids = [i for batch in group for i in batch]
                group_rows = len(group_ids)
                physical_group = regroup_same16(group_ids, rows, physical)
                rng_cpu, rng_cuda = torch.get_rng_state(), torch.cuda.get_rng_state_all()
                retries = 0
                elapsed_at_entry = time.monotonic() - train_start
                if time.time() >= TRAIN_STOP_UNIX or time.monotonic() >= clock["deadline_monotonic"]:
                    break
                lr = replan_lr(elapsed_at_entry, prior_consumed, replanned_remaining, prior_lr)
                for param_group in optimizer.param_groups:
                    param_group["lr"] = lr
                while True:
                    state["total_group_attempts"] += 1
                    optimizer.zero_grad(set_to_none=True)
                    group_loss = 0.0
                    supervised = nonpadding = 0
                    failure = None
                    phase = "forward_backward"
                    try:
                        for indices in physical_group:
                            items = [rows[i] for i in indices]
                            batch = collate(items, tokenizer, "cuda")
                            with torch.autocast("cuda", dtype=torch.float16):
                                loss = exact_pair_forward_loss(model, batch, physical)
                            if not bool(torch.isfinite(loss).item()):
                                raise FloatingPointError("nonfinite loss")
                            scaler.scale(loss).backward()
                            group_loss += float(loss.detach())
                            nonpadding += int(batch["attention_mask"].sum().item())
                            supervised += sum(sum(x != -100 for x in item["encoded"]["labels"]) for item in items)
                        scaler.unscale_(optimizer)
                        grads = [p.grad for p in parameters if p.grad is not None]
                        if not grads:
                            raise FloatingPointError("absent gradients")
                        try:
                            grad_norm = torch.nn.utils.clip_grad_norm_(parameters, 1.0,
                                        error_if_nonfinite=True, foreach=True)
                        except RuntimeError as error:
                            if "non-finite" in str(error).lower() or "nonfinite" in str(error).lower():
                                raise FloatingPointError("nonfinite gradient norm") from error
                            raise
                        old_scale = scaler.get_scale()
                        phase = "optimizer_step"
                        scaler.step(optimizer)
                        scaler.update()
                        if scaler.get_scale() < old_scale:
                            raise FloatingPointError("AMP skipped optimizer step")
                        torch.cuda.synchronize()
                        phase = "optimizer_step_complete"
                    except torch.cuda.OutOfMemoryError:
                        if phase != "forward_backward":
                            raise RuntimeError("OOM during optimizer step; possible partial update, refuse retry/resume from this attempt")
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
                    if failure == "oom":
                        old_physical = physical
                        physical, checkpointing = oom_fallback(physical, cfg["gradient_checkpointing"])
                        model.gradient_checkpointing_enable()
                        cfg.update(microbatch=physical, grad_accumulation=EFFECTIVE_BATCH // physical,
                                   gradient_checkpointing=checkpointing)
                        physical_group = regroup_same16(group_ids, rows, physical)
                        state.setdefault("runtime_fallback_events", []).append({
                            "step_to_retry": state["step"] + 1, "from_microbatch": old_physical,
                            "to_microbatch": physical, "gradient_checkpointing": checkpointing,
                            "reason": "forward_backward_OOM", "same16_ids": [rows[i]["sample_id"] for i in group_ids],
                            "lr_unchanged": lr, "scaler_scale_unchanged": scaler.get_scale()})
                        atomic_json(out / "run_config.json", cfg)
                        # Reset any scaler per-optimizer stage without changing AMP scale.
                        scaler.update(new_scale=scaler.get_scale())
                        torch.cuda.empty_cache()
                    else:
                        scaler.update(new_scale=max(1.0, scaler.get_scale() / 2))
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
                if time.time() >= TRAIN_STOP_UNIX or time.monotonic() >= clock["deadline_monotonic"]:
                    break
                if state["step"] == resumed_step + 1 or state["step"] % 300 == 0 or time.monotonic() - last_checkpoint >= 900:
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
                if phase == "optimizer_step":
                    raise RuntimeError("emergency checkpoint refused after possible partial optimizer update; use last regular generation")
                optimizer_coherence(optimizer.state_dict(), state["step"], parameters)
                save_generation(model, tokenizer, optimizer, scaler, out, cfg, metrics,
                    {"epoch": epoch, "next_microbatch": batch_cursor, "seed": SEED,
                     "microbatches_per_epoch": len(batches)}, clock)
            except BaseException as save_error:
                atomic_json(out / "emergency_save_error.json", {"error": repr(save_error)})
            raise
        train_stop = time.monotonic()
        metrics = snapshot_metrics(state, rows, train_start, train_stop)
        metrics["stop_reason"] = "OWNER_REVISED_ABSOLUTE_TRAIN_CUTOFF_AT_GROUP_BOUNDARY"
        metrics["budget_scope"] = BUDGET_SCOPE
        metrics["prior_training_consumed_seconds"] = prior_consumed
        metrics["current_segment_training_wall_seconds"] = train_stop - segment_start
        metrics["hard_deadline_unix"] = HARD_DEADLINE_UNIX
        metrics["train_stop_unix"] = TRAIN_STOP_UNIX
        metrics["deadline_boundary_overrun_seconds"] = max(0.0, time.time() - TRAIN_STOP_UNIX)
        metrics["training_stopped_unix"] = time.time()
        metrics["full_requested_training_window_reached"] = False
        metrics["revised_training_cutoff_reached"] = time.time() >= TRAIN_STOP_UNIX
        optimizer_coherence(optimizer.state_dict(), state["step"], parameters)
        atomic_json(out / "final_metrics.json", metrics)
        final_generation = save_generation(model, tokenizer, optimizer, scaler, out, cfg, metrics,
                   {"epoch": epoch, "next_microbatch": batch_cursor, "seed": SEED,
                    "microbatches_per_epoch": len(batches)}, clock)
        # The adapter is safely exported before any after-training generation can fail.
        export_adapter(final_generation, out)
        if STOP_REQUESTED is not None or (out / "stop_after_current_group.json").exists():
            atomic_json(out / "progress.json", {"state": "PAUSED_AT_OPTIMIZER_BOUNDARY",
                "complete": False, **metrics, "stop_request": STOP_REQUESTED,
                "latest_checkpoint": strict_json((out / "latest.json").read_text(encoding="utf-8")),
                "adapter_safe": True, "evaluation_run": False})
            return
        atomic_json(out / "progress.json", {"state": "TRAINING_COMPLETE_ADAPTER_SAFE_BEGIN_EVAL",
                    "training_started": True, **metrics, "clock": clock,
                    "adapter_zip_sha256": sha_file(out / "adapter_export.zip")})
        remaining_eval = min(args.eval_timeout_seconds, HARD_DEADLINE_UNIX - time.time() - 45)
        if remaining_eval <= 0:
            raise TimeoutError("hard deadline reserve exhausted after safe adapter export")
        after = generate_fixtures(model, tokenizer, fixtures, out, "adapter_after_training",
                     contract, contract_sha, remaining_eval, FastLanguageModel)
        if time.time() >= HARD_DEADLINE_UNIX:
            raise TimeoutError("revised owner hard deadline exceeded; adapter preserved")
        complete = {"schema": "MathVisionKid.corrective_optimized_v2.complete.v1", "complete": True,
                    "step": state["step"], "rows_done": state["rows_done"], "metrics": metrics,
                    "config": cfg, "base_outputs": len(base), "adapter_outputs": len(after),
                    "eval_fixture_count": 28, "evaluation_contract_sha256": contract_sha,
                    "adapter_zip_sha256": sha_file(out / "adapter_export.zip"),
                    "adapter_zip_bytes": (out / "adapter_export.zip").stat().st_size,
                    "final_checkpoint": strict_json((out / "latest.json").read_text(encoding="utf-8")),
                    "requested_training_wall_seconds": None,
                    "budget_scope": BUDGET_SCOPE, "hard_deadline_unix": HARD_DEADLINE_UNIX,
                    "owner_budget_revision_sha256": OWNER_BUDGET_SHA256,
                    "hard_deadline_utc": "2026-10-24T05:28:23Z", "train_stop_unix": TRAIN_STOP_UNIX,
                    "train_stop_utc": "2026-10-24T05:13:23Z", "reserve_seconds": RESERVE_SECONDS,
                    "budget_satisfied": time.time() < HARD_DEADLINE_UNIX,
                    "revised_training_cutoff_reached": metrics["revised_training_cutoff_reached"],
                    "prior_training_consumed_seconds": prior_consumed,
                    "current_segment_training_wall_seconds": metrics["current_segment_training_wall_seconds"],
                    "training_stopped_unix": metrics["training_stopped_unix"],
                    "actual_training_wall_seconds": metrics["training_wall_seconds"],
                    "full_requested_training_window_reached": metrics["full_requested_training_window_reached"],
                    "base_output_sha256": sha_file(out / "base_generations.jsonl"),
                    "adapter_output_sha256": sha_file(out / "adapter_generations.jsonl"),
                    "semantic_quality_claim": False}
        bound_files = ["run_config.json", "runtime_versions.json", "structural_audit.json", "input_audit.json",
                       "final_metrics.json", "successful_ids.jsonl", "checkpoint_timing.jsonl", "latest.json",
                       "evaluation_contract.json", "base_generations.jsonl", "base_generation_provenance.json",
                       "adapter_generations.jsonl", "adapter_export.zip", "resume_validation.json", "physical_batch_tuning.json"]
        bound_files.append("owner_budget_revision_config.json")
        complete["files"] = {name: sha_file(out / name) for name in bound_files}
        complete["file_bytes"] = {name: (out / name).stat().st_size for name in bound_files}
        complete["completed_unix"] = time.time()
        complete["budget_satisfied"] = complete["completed_unix"] < HARD_DEADLINE_UNIX
        if not complete["budget_satisfied"]:
            raise TimeoutError("hard deadline exceeded while hashing completion artifacts")
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
