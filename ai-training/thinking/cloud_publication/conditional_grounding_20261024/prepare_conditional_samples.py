"""Project exactly 24 archived rendered examples; never load the full corpus.

The archived examples contain rendered text and inherited original-row hashes,
not original raw JSONL bytes. This script verifies those archived inputs, changes
only the worked instruction suffix, and makes no semantic/human QA attestation.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / "skill_recovery_150m_20261024"
INPUT_PINS = {
    "projection_preflight.json": "880b5c5fd4be98f296d0a9c5e4f3828e86cff8c0bf77cdb09f97b648f1857022",
    "source_behavior_samples.json": "b2194ad27400b985fa96e45c4ef9c25cacd444d01863a4f34e38a14737ecac18",
}
RENDERER_PIN = "78b4a5c9cfff2e33fc7610461ecab6f57447c079205b62668631f2ca4b665982"
EXPECTED_COUNTS = {"projection_preflight.json": 14, "source_behavior_samples.json": 10}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def text_sha(value: str) -> str:
    return sha(value.encode("utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_inputs():
    values = {}
    for name, expected in INPUT_PINS.items():
        raw = (OLD / name).read_bytes()
        require(sha(raw) == expected, "Archived input hash mismatch: " + name)
        value = json.loads(raw)
        require(isinstance(value, dict) and isinstance(value.get("samples"), list), "Missing archived samples")
        require(len(value["samples"]) == EXPECTED_COUNTS[name], "Unexpected archived sample count")
        values[name] = value
    first, second = values.values()
    require(first["plan_sha256"] == second["source_plan_sha256"], "Archived source plans differ")
    require(second["source_modified"] is False, "Archived input does not confirm original preservation")
    return values


def load_renderer():
    path = HERE / "conditional_behavior_renderer.py"
    require(sha(path.read_bytes()) == RENDERER_PIN, "Conditional renderer pin mismatch")
    spec = importlib.util.spec_from_file_location("conditional_sample_renderer", path)
    require(spec is not None and spec.loader is not None, "Cannot load pinned renderer")
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    require(renderer.VERSION == "conditional_behavior_render.v1", "Unexpected renderer version")
    return renderer


def project_archived_sample(sample, renderer):
    """Use only mode for routing, never target contents or behavior/oracle labels."""
    required = ("sample_id", "grade", "mode", "behavior", "source_original_raw_row_sha256", "actual_prompt", "actual_target")
    require(isinstance(sample, dict) and all(key in sample for key in required), "Incomplete archived sample")
    require(type(sample["grade"]) is int and sample["grade"] in range(1, 6), "Invalid sample grade")
    require(all(isinstance(sample[key], str) for key in required if key != "grade"), "Invalid archived sample field types")
    raw_hash = sample["source_original_raw_row_sha256"]
    require(re.fullmatch(r"[0-9a-f]{64}", raw_hash) is not None, "Invalid inherited original raw-row hash")
    mode = sample["mode"]
    require(mode in renderer.BASE._MODE_INSTRUCTIONS, "Invalid archived mode")
    old_prompt, target = sample["actual_prompt"], sample["actual_target"]
    old_suffix = "\n\nYêu cầu:\n\n" + renderer.BASE._MODE_INSTRUCTIONS[mode]
    require(old_prompt.endswith(old_suffix), "Archived prompt does not end in pinned mode instruction")
    prefix = old_prompt[:-len(old_suffix)]
    if mode == "worked_solution":
        new_suffix = "\n\nYêu cầu:\n\n" + renderer.WORKED_INSTRUCTION
        new_prompt = prefix + new_suffix
        require(new_prompt != old_prompt and new_prompt[:-len(new_suffix)] == prefix, "Worked prefix changed")
    else:
        new_prompt = old_prompt
        require(new_prompt.encode("utf-8") == old_prompt.encode("utf-8"), "Hint prompt changed")
    row = {
        "schema": "MathVisionKid.conditional_archived_sample.v1",
        "artifact_role": "24_sample_sanity_projection_only",
        "sample_id": sample["sample_id"], "grade": sample["grade"], "mode": mode,
        "behavior": sample["behavior"],
        "source_original_raw_row_sha256": raw_hash,
        "messages": [
            {"role": "system", "content": renderer.SYSTEM},
            {"role": "user", "content": new_prompt},
            {"role": "assistant", "content": target},
        ],
    }
    require(row["messages"][2]["content"].encode("utf-8") == target.encode("utf-8"), "Target bytes changed")
    require(row["source_original_raw_row_sha256"] == raw_hash, "Original source hash changed")
    proof = {
        "sample_id": sample["sample_id"], "mode": mode,
        "source_original_raw_row_sha256": raw_hash,
        "archived_rendered_sample_canonical_sha256": sha(json.dumps(sample, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")),
        "old_prompt_sha256": text_sha(old_prompt), "conditional_prompt_sha256": text_sha(new_prompt),
        "old_target_sha256": text_sha(target), "conditional_target_sha256": text_sha(row["messages"][2]["content"]),
        "unchanged_prompt_prefix_sha256": text_sha(prefix),
        "prompt_prefix_unchanged": True, "target_bytes_unchanged": True,
        "hint_prompt_bytes_unchanged": mode != "worked_solution",
        "worked_suffix_only_changed": mode == "worked_solution",
        "inherited_source_hash_unchanged": True,
    }
    return row, proof


def main():
    inputs = load_inputs()
    renderer = load_renderer()
    require(inputs["projection_preflight.json"]["renderer_sha256"] == renderer.BASE_SHA, "Archived renderer pin differs")
    require(inputs["projection_preflight.json"]["new_train_eval_system_sha256"] == text_sha(renderer.SYSTEM), "Neutral system changed")
    rows, proofs, seen = [], [], set()
    for name, data in inputs.items():
        for sample in data["samples"]:
            require(sample["sample_id"] not in seen, "Duplicate sample ID across archived inputs")
            seen.add(sample["sample_id"])
            snapshot = json.dumps(sample, ensure_ascii=False, sort_keys=True)
            row, proof = project_archived_sample(sample, renderer)
            require(json.dumps(sample, ensure_ascii=False, sort_keys=True) == snapshot, "Archived parsed sample mutated")
            proof["archived_input_file"] = name
            rows.append(row)
            proofs.append(proof)
    require(len(rows) == 24, "Only the specified 24 samples are permitted")
    # Round-trip and individually rebind every saved prompt/target before writing.
    encoded = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows).encode("utf-8")
    decoded = [json.loads(line) for line in encoded.decode("utf-8").splitlines()]
    for row, proof in zip(decoded, proofs):
        require(text_sha(row["messages"][1]["content"]) == proof["conditional_prompt_sha256"], "Serialized prompt mismatch")
        require(text_sha(row["messages"][2]["content"]) == proof["old_target_sha256"], "Serialized target mismatch")
        require(row["source_original_raw_row_sha256"] == proof["source_original_raw_row_sha256"], "Serialized raw hash mismatch")
    code_pins = {
        "prepare_conditional_samples.py": sha(Path(__file__).read_bytes()),
        "conditional_behavior_renderer.py": RENDERER_PIN,
        "frozen_behavior_renderer.py": sha(renderer.BASE_PATH.read_bytes()),
        "frozen_target_renderer.py": sha(renderer.BASE._V3_PATH.read_bytes()),
    }
    report = {
        "schema": "MathVisionKid.conditional_sample_preflight.v1",
        "sample_count": len(rows), "archived_input_counts": EXPECTED_COUNTS,
        "input_file_sha256": INPUT_PINS, "code_sha256": code_pins,
        "source_plan_sha256": inputs["projection_preflight.json"]["plan_sha256"],
        "renderer_version": renderer.VERSION, "system_sha256": text_sha(renderer.SYSTEM),
        "mode_counts": dict(Counter(row["mode"] for row in rows)),
        "behavior_counts": dict(Counter(row["behavior"] for row in rows)),
        "worked_prompt_suffix_changes": sum(proof["worked_suffix_only_changed"] for proof in proofs),
        "hint_prompts_byte_identical": True, "all_prompt_prefixes_byte_identical": True,
        "all_targets_byte_identical": True, "all_inherited_raw_source_hashes_identical": True,
        "samples_jsonl_sha256": sha(encoded), "samples_jsonl_bytes": len(encoded),
        "source_files_unchanged": True, "source_rows_or_labels_modified": False,
        "raw_source_row_bytes_read_or_verified": False,
        "full_16000_training_view_built": False, "full_corpus_qa_performed": False,
        "training_performed": False, "model_inference_performed": False,
        "human_review_claimed": False, "new_acceptance_or_credentials_created": False,
        "scope": "Exactly 24 archived rendered samples (14+10), suffix-only prompt sanity projection. Inherited raw source hashes are carried unchanged; original raw JSONL rows were not read or independently rehashed. No model quality or full-corpus QA claim.",
        "records": proofs,
    }
    # Recheck original file pins immediately before and after output writes.
    load_inputs()
    (HERE / "conditional_samples.jsonl").write_bytes(encoded)
    (HERE / "conditional_sample_preflight.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    load_inputs()
    print(json.dumps({"sample_count": len(rows), "worked_suffix_changes": report["worked_prompt_suffix_changes"], "mode_counts": report["mode_counts"], "output_sha256": report["samples_jsonl_sha256"]}))


if __name__ == "__main__":
    main()
