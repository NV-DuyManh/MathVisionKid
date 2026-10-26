"""Build a small, exact-source few-shot bank. This is inference-only context."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
PROJECTION = ROOT / "projection_preflight.json"
BEHAVIOR = ROOT / "source_behavior_samples.json"
OUTPUT = ROOT / "source_example_bank.json"

# Order is fixed and selection for inference consumes only the requested mode.
SELECTED_IDS = {
    "worked_solution": [
        "exhaustive_v1_sub_565_103:worked_solution",
        "primary_20261018_finish_g5_decimal_read_compare_more_digits_not_larger:worked_solution",
        "sgk_gap_20261019_g4_data_reconstruction_guard:worked_solution",
    ],
    "hint_level_1": [
        "exhaustive_v1_sub_565_103:hint_level_1",
        "exhaustive_v1_div_788_1:hint_level_1",
    ],
    "hint_level_2": [
        "exhaustive_v1_sub_565_103:hint_level_2",
        "exhaustive_v1_div_788_1:hint_level_2",
    ],
    "hint_level_3": [
        "exhaustive_v1_sub_565_103:hint_level_3",
        "exhaustive_v1_div_788_1:hint_level_3",
    ],
}


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_json(path: Path) -> tuple[Any, str]:
    raw = path.read_bytes()
    return json.loads(raw), sha_bytes(raw)


def _index(examples: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out = {}
    for item in examples:
        sample_id = item["sample_id"]
        if sample_id in out:
            raise ValueError(f"Duplicate sample_id in allowed source files: {sample_id}")
        out[sample_id] = item
    return out


def build_bank() -> dict[str, Any]:
    projection, projection_sha = read_json(PROJECTION)
    behavior, behavior_sha = read_json(BEHAVIOR)
    # Restrict inputs to the two explicitly approved actual-train sample lists.
    all_items = _index(projection["samples"] + behavior["samples"])
    if len(all_items) != 24:
        raise ValueError(f"Expected 24 combined approved samples, found {len(all_items)}")

    entries: list[dict[str, Any]] = []
    for mode, ids in SELECTED_IDS.items():
        for sample_id in ids:
            source = all_items.get(sample_id)
            if source is None:
                raise ValueError(f"Selected actual-train source is missing: {sample_id}")
            if source["mode"] != mode:
                raise ValueError(f"Selected source mode mismatch: {sample_id}")
            source_hash = source.get("source_original_raw_row_sha256")
            if not isinstance(source_hash, str) or len(source_hash) != 64:
                raise ValueError(f"Missing original source-row SHA256: {sample_id}")
            prompt = source["actual_prompt"]
            target = source["actual_target"]
            if not isinstance(prompt, str) or not isinstance(target, str) or not prompt or not target:
                raise ValueError(f"Empty/malformed source example: {sample_id}")
            entries.append({
                "sample_id": sample_id,
                "mode": mode,
                "source_raw_row_sha256": source_hash,
                "actual_prompt": prompt,
                "actual_target": target,
                "prompt_sha256": sha_bytes(prompt.encode("utf-8")),
                "target_sha256": sha_bytes(target.encode("utf-8")),
                "prompt_chars": len(prompt),
                "target_chars": len(target),
                "combined_example_chars": len(prompt) + len(target),
            })

    return {
        "schema": "MathVisionKid.source_fewshot_example_bank.v1",
        "purpose": "Optional inference-time demonstrations only; not new weight training or evidence of improved model behavior.",
        "selection_policy": "Fixed order; selector reads requested mode only; no behavior/oracle flag is included in entries.",
        "source_files": {
            "projection_preflight.json": {"sha256": projection_sha, "sample_count": len(projection["samples"])},
            "source_behavior_samples.json": {"sha256": behavior_sha, "sample_count": len(behavior["samples"])},
            "combined_approved_samples": len(all_items),
        },
        "entries": entries,
        "mode_counts": {mode: len(ids) for mode, ids in SELECTED_IDS.items()},
        "size_summary_chars": {
            mode: {
                "prompt_chars": sum(e["prompt_chars"] for e in entries if e["mode"] == mode),
                "target_chars": sum(e["target_chars"] for e in entries if e["mode"] == mode),
                "combined_example_chars": sum(e["combined_example_chars"] for e in entries if e["mode"] == mode),
            }
            for mode in SELECTED_IDS
        },
        "token_count": None,
        "token_count_note": "No tokenizer was used; character counts are not token estimates.",
        "human_or_teacher_attestation": None,
    }


def select_examples(bank: dict[str, Any], mode: str) -> list[dict[str, Any]]:
    """Return exact examples in bank order, consulting only mode."""
    if mode not in SELECTED_IDS:
        raise ValueError(f"Unsupported mode: {mode}")
    selected = [entry for entry in bank["entries"] if entry["mode"] == mode]
    if len(selected) != len(SELECTED_IDS[mode]):
        raise ValueError("Bank has wrong number of examples for requested mode")
    return selected


def messages_for_mode(bank: dict[str, Any], mode: str, system: str) -> list[dict[str, str]]:
    """Fixed system, then user/assistant example pairs in stable bank order."""
    messages = [{"role": "system", "content": system}]
    for entry in select_examples(bank, mode):
        messages.append({"role": "user", "content": entry["actual_prompt"]})
        messages.append({"role": "assistant", "content": entry["actual_target"]})
    return messages


def main() -> None:
    bank = build_bank()
    OUTPUT.write_text(json.dumps(bank, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

