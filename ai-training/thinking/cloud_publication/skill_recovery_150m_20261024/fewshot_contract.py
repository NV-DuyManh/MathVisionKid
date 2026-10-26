"""Few-shot prompt contract: examples are selected by requested tutor mode only."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
import random
import time

import behavior_renderer as B
import inference_contract as I

ROOT = Path(__file__).resolve().parent
BANK_PATH = ROOT / "source_example_bank.json"
SOURCE_PATHS = {
    "projection_preflight.json": ROOT / "projection_preflight.json",
    "source_behavior_samples.json": ROOT / "source_behavior_samples.json",
}
MAX_PROMPT_TOKENS = 3072
MAX_NEW_TOKENS = 1024
EXPECTED_SOURCE_IDS = {
    "worked_solution": [
        "exhaustive_v1_sub_565_103:worked_solution",
        "primary_20261018_finish_g5_decimal_read_compare_more_digits_not_larger:worked_solution",
        "sgk_gap_20261019_g4_data_reconstruction_guard:worked_solution",
    ],
    "hint_level_1": ["exhaustive_v1_sub_565_103:hint_level_1", "exhaustive_v1_div_788_1:hint_level_1"],
    "hint_level_2": ["exhaustive_v1_sub_565_103:hint_level_2", "exhaustive_v1_div_788_1:hint_level_2"],
    "hint_level_3": ["exhaustive_v1_sub_565_103:hint_level_3", "exhaustive_v1_div_788_1:hint_level_3"],
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_and_validate_bank(bank_path: Path = BANK_PATH) -> tuple[dict[str, Any], str]:
    raw = bank_path.read_bytes()
    bank = json.loads(raw)
    bank_sha = digest(raw)
    if bank.get("schema") != "MathVisionKid.source_fewshot_example_bank.v1":
        raise ValueError("Unexpected example bank schema")
    if bank.get("purpose", "").find("inference-time") < 0:
        raise ValueError("Bank purpose is not inference-only")
    for name, path in SOURCE_PATHS.items():
        expected = bank.get("source_files", {}).get(name, {}).get("sha256")
        if expected != digest(path.read_bytes()):
            raise ValueError(f"Approved source file hash mismatch: {name}")
    entries = bank.get("entries")
    if not isinstance(entries, list) or len(entries) != 9:
        raise ValueError("Expected exactly 9 frozen few-shot entries")
    seen: set[str] = set()
    source_rows: dict[str, dict[str, Any]] = {}
    for path in SOURCE_PATHS.values():
        source = json.loads(path.read_bytes())
        for row in source["samples"]:
            if row["sample_id"] in source_rows:
                raise ValueError("Duplicate sample ID across allowed source files")
            source_rows[row["sample_id"]] = row
    expected_counts = {"worked_solution": 3, "hint_level_1": 2, "hint_level_2": 2, "hint_level_3": 2}
    counts = {mode: 0 for mode in expected_counts}
    ordered_ids = {mode: [] for mode in expected_counts}
    for item in entries:
        sid = item.get("sample_id")
        if sid in seen:
            raise ValueError("Duplicate example source ID")
        seen.add(sid)
        if item.get("mode") not in expected_counts:
            raise ValueError("Unsupported example mode")
        counts[item["mode"]] += 1
        ordered_ids[item["mode"]].append(sid)
        source = source_rows.get(sid)
        if source is None or source.get("mode") != item["mode"]:
            raise ValueError(f"Example is not bound to an approved actual-train source: {sid}")
        for field, hash_field in (("actual_prompt", "prompt_sha256"), ("actual_target", "target_sha256")):
            text = item.get(field)
            if not isinstance(text, str) or not text or text != source.get(field):
                raise ValueError(f"Few-shot {field} differs from source: {sid}")
            if item.get(hash_field) != digest(text.encode("utf-8")):
                raise ValueError(f"Few-shot {field} hash mismatch: {sid}")
        if item.get("source_raw_row_sha256") != source.get("source_original_raw_row_sha256"):
            raise ValueError(f"Source raw-row binding mismatch: {sid}")
    if counts != expected_counts:
        raise ValueError("Example bank mode counts differ from frozen contract")
    if bank.get("mode_counts") != expected_counts or ordered_ids != EXPECTED_SOURCE_IDS:
        raise ValueError("Example bank source IDs/order differ from frozen contract")
    return bank, bank_sha


def messages_with_examples(fixture: dict[str, Any], bank: dict[str, Any] | None = None) -> tuple[list[dict[str, str]], list[str]]:
    """Return prompt messages and IDs; selected examples depend only on requested mode."""
    if bank is None:
        bank, _ = load_and_validate_bank()
    if fixture.get("mode") not in I.MODE_MAP:
        raise ValueError("Unsupported requested evaluation mode")
    mode = I.MODE_MAP[fixture["mode"]]
    examples = [entry for entry in bank["entries"] if entry["mode"] == mode]
    expected_count = bank["mode_counts"].get(mode)
    if len(examples) != expected_count:
        raise ValueError("Few-shot mode selection count mismatch")
    # This shared base/evaluation builder preserves the entire original request as the final user message.
    final_user = I.messages(fixture)[-1]
    out = [{"role": "system", "content": B.SYSTEM}]
    for example in examples:
        out.extend((
            {"role": "user", "content": example["actual_prompt"]},
            {"role": "assistant", "content": example["actual_target"]},
        ))
    out.append(final_user)
    return out, [entry["sample_id"] for entry in examples]


def messages(fixture: dict[str, Any], bank: dict[str, Any] | None = None) -> list[dict[str, str]]:
    """I-compatible message builder: one list, with no fixture metadata in messages."""
    return messages_with_examples(fixture, bank)[0]


def tokenize(tok: Any, fixture: dict[str, Any], bank: dict[str, Any], max_prompt_tokens: int = MAX_PROMPT_TOKENS) -> tuple[Any, list[dict[str, str]], list[str], str]:
    msgs, example_ids = messages_with_examples(fixture, bank)
    encoded = tok.apply_chat_template(msgs, tokenize=True, add_generation_prompt=True, enable_thinking=False)
    ids = encoded["input_ids"] if hasattr(encoded, "keys") else encoded
    if hasattr(ids, "tolist"):
        ids = ids.tolist()
    if ids and isinstance(ids[0], list):
        ids = ids[0]
    if len(ids) > max_prompt_tokens:
        raise ValueError(f"Few-shot prompt too long ({len(ids)} > {max_prompt_tokens}); refusing truncation")
    return encoded, msgs, example_ids, digest(canonical(ids).encode())


def eval_contract(fixtures: list[dict[str, Any]], tok: Any, fixture_sha256: str | None = None,
                  bank_path: Path = BANK_PATH, max_prompt_tokens: int = MAX_PROMPT_TOKENS,
                  frozen_fixture_ids: list[str] | None = None) -> tuple[dict[str, Any], str]:
    bank, bank_sha = load_and_validate_bank(bank_path)
    prompt_hashes: dict[str, str] = {}
    selections: dict[str, list[str]] = {}
    for fixture in fixtures:
        if fixture["id"] in prompt_hashes:
            raise ValueError("Duplicate fixture ID")
        _, _, selected, token_sha = tokenize(tok, fixture, bank, max_prompt_tokens)
        prompt_hashes[fixture["id"]] = token_sha
        selections[fixture["id"]] = selected
    active_ids = [f["id"] for f in fixtures]
    frozen_ids = list(frozen_fixture_ids) if frozen_fixture_ids is not None else active_ids
    if len(set(frozen_ids)) != len(frozen_ids) or not set(active_ids).issubset(frozen_ids):
        raise ValueError("Active fixture IDs must be unique members of the frozen fixture set")
    if fixture_sha256 is not None and (len(fixture_sha256) != 64 or any(c not in "0123456789abcdef" for c in fixture_sha256)):
        raise ValueError("Explicit frozen fixture raw SHA required")
    contract = {
        "schema": "MathVisionKid.fewshot_matched_dev_eval.v1",
        "model": I.MODEL,
        "revision": I.REVISION,
        "fixture_sha256": fixture_sha256 or digest(("\n".join(I.canonical(f) for f in fixtures) + "\n").encode()),
        "fixture_ids": active_ids,
        "frozen_fixture_ids": frozen_ids,
        "system": B.SYSTEM,
        "system_sha256": digest(B.SYSTEM.encode()),
        "mode_map": I.MODE_MAP,
        "selection_policy": "Examples selected only by requested mode; oracle labels and fixture metadata are excluded from prompt messages.",
        "renderer_version": B.VERSION,
        "example_bank_sha256": bank_sha,
        "example_bank_source_files": bank["source_files"],
        "example_selections_by_fixture": selections,
        "prompt_token_sha256": prompt_hashes,
        "prompt_token_limit": max_prompt_tokens,
        "truncation": "forbidden; over-limit prompts fail before generation",
        "enable_thinking": False,
        "add_generation_prompt": True,
        "seed_policy": "20261024 + first8hex fixtureID SHA modulo2^31; reset per fixture",
        "decoding": {"do_sample": True, "temperature": .7, "top_p": .8, "top_k": 20, "min_p": 0., "num_beams": 1, "max_new_tokens": MAX_NEW_TOKENS, "repetition_penalty": 1., "use_cache": True},
    }
    return contract, digest(canonical(contract).encode())


def generate_fixtures(model: Any, tok: Any, fixtures: list[dict[str, Any]], out: Path,
                      stage: str, contract: dict[str, Any], csha: str,
                      timeout_seconds: float, fast_model: Any) -> dict[str, Any]:
    """Generate one all-fixture base-only pass; never applies an adapter or reruns evidence."""
    if stage not in ("base_fewshot_dev", "fewshot_selected_after_base_review"):
        raise ValueError("Few-shot worker only supports labeled untrained-base stages")
    if digest(canonical(contract).encode()) != csha:
        raise ValueError("Few-shot contract hash mismatch")
    if contract.get("fixture_ids") != [fixture["id"] for fixture in fixtures]:
        raise ValueError("Few-shot fixture order differs from contract")
    import torch
    from transformers import GenerationConfig
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "generations.jsonl"
    partial = out / "generations.partial.jsonl"
    if path.exists() or partial.exists():
        raise FileExistsError("Few-shot evidence exists; preserve it and do not silently rerun")
    bank, bank_sha = load_and_validate_bank()
    if bank_sha != contract.get("example_bank_sha256"):
        raise ValueError("Few-shot bank hash differs from contract")
    fast_model.for_inference(model)
    model.eval()
    cutoff = time.monotonic() + max(0., timeout_seconds)
    config = GenerationConfig(**contract["decoding"], eos_token_id=151645, pad_token_id=tok.pad_token_id)
    for index, fixture in enumerate(fixtures, start=1):
        left = cutoff - time.monotonic()
        if left <= 1:
            raise TimeoutError("Few-shot development inference budget exhausted; partial evidence retained")
        seed = (20261024 + int(digest(fixture["id"].encode())[:8], 16)) % (2**31)
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        random.seed(seed)
        msgs, example_ids = messages_with_examples(fixture, bank)
        ids = tok.apply_chat_template(
            msgs, tokenize=True, add_generation_prompt=True, enable_thinking=False,
            return_tensors="pt", return_dict=True,
        ).to("cuda")
        prompt_ids = ids["input_ids"][0].tolist()
        prompt_sha = digest(canonical(prompt_ids).encode())
        if prompt_sha != contract["prompt_token_sha256"].get(fixture["id"]):
            raise ValueError("Prompt token hash differs from frozen few-shot contract")
        prompt_tokens = len(prompt_ids)
        if prompt_tokens > contract["prompt_token_limit"]:
            raise ValueError(f"Few-shot prompt too long ({prompt_tokens}); truncation is forbidden")
        started = time.monotonic()
        with torch.inference_mode():
            result = model.generate(**ids, generation_config=config, max_time=left)
        tokens = result[0, ids["input_ids"].shape[1]:]
        ended_eos = bool(len(tokens) and int(tokens[-1]) == 151645)
        row = {
            "fixture_id": fixture["id"], "grade": fixture["grade"], "mode": fixture["mode"],
            "model_mode": I.MODE_MAP[fixture["mode"]], "stage": stage,
            "contract_sha256": csha, "prompt_token_sha256": prompt_sha,
            "fewshot_example_ids": example_ids, "max_new_tokens": MAX_NEW_TOKENS,
            "prompt_tokens": prompt_tokens, "generated_tokens": int(len(tokens)),
            "output": tok.decode(tokens, skip_special_tokens=True).strip(),
            "ended_eos": ended_eos, "possibly_truncated": not ended_eos,
            "timed_out": time.monotonic() >= cutoff, "seed": seed,
            "generation_seconds": time.monotonic() - started,
        }
        with partial.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            stream.flush()
        progress_path = out / "runtime_progress.json"
        progress_path.write_text(json.dumps({
            "state": "GENERATING_BASE_FEWSHOT", "completed": index,
            "fixture_count": len(fixtures), "last_fixture_id": fixture["id"],
            "last_ended_eos": ended_eos, "training_performed": False,
            "optimizer_loaded": False, "locked_test_accessed": False,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    partial.replace(path)
    proof = {
        "complete": True, "fixture_count": len(fixtures),
        "fixture_sha256": contract["fixture_sha256"], "model": I.MODEL,
        "revision": I.REVISION, "stage": stage, "contract_sha256": csha,
        "example_bank_sha256": bank_sha, "outputs_sha256": digest(path.read_bytes()),
        "training_performed": False, "optimizer_loaded": False,
        "locked_test_accessed": False,
    }
    (out / "complete.json").write_text(json.dumps(proof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return proof
