"""Bounded, data-only release selection. Inputs remain immutable full-corpus rows."""
from collections import Counter
from copy import deepcopy
import argparse
import gzip
import io
import json
from pathlib import Path
import shutil

import exhaustive_colab_loader as loader

HERE = Path(__file__).resolve().parent
STAGING = HERE / "cloud_publication/resume_20261018"


def read_rows(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)


def neutral_chats(source):
    """Derive modes from preserved source content; retain original labels/IDs."""
    for mode in loader.MODES:
        payload = {"grade": source["grade"], "problem": source["problem"], "mode": mode}
        if source.get("student_work"):
            payload["student_work"] = source["student_work"]
        if mode == "worked_solution":
            answer = {"can_solve": source["can_solve"], "initial_guidance": source["initial_guidance"],
                      "steps": source["worked_steps"], "answer": source["expected_answer"]}
        else:
            hint = source["hints"][int(mode[-1]) - 1]
            answer = {key: hint[key] for key in ("hint", "question")}
        yield {"sample_id": source["sample_id"] + ":" + mode,
               "source_sample_id": source["sample_id"], "case_group_id": source["case_group_id"],
               "grade": source["grade"], "topic": source["topic"], "mode": mode, "split": "train",
               "schema": "neutral_teacher_chat.v1_not_live_PlanDraft",
               "messages": [{"role": "system", "content": "Bạn là gia sư Toán tiểu học. Dùng đúng dữ kiện, giải thích phép toán, đơn vị và cách kiểm. Chỉ giải đầy đủ khi được yêu cầu; gợi ý không điền đáp số."},
                            {"role": "user", "content": loader.canonical_json(payload)},
                            {"role": "assistant", "content": loader.canonical_json(answer)}],
               "acceptance_status": source.get("acceptance_status", "ACCEPTED_OWNER_PREAUTHORIZED"),
               "provenance": source["provenance"],
               "derivation": {"kind": "SELECTED_VIEW_FROM_PRESERVED_SOURCE",
                              "source_sha256": loader.digest_bytes(loader.canonical_json(source).encode()),
                              "new_human_attestation_claimed": False}}


def input_paths(staging=STAGING):
    baseline = HERE / "data/primary_math_teacher_20261016/exports"
    extensions = staging / "preserved_extensions"
    source = [baseline / "accepted_teacher_cases_polished.jsonl",
              staging / "pedagogy_cases_v3.jsonl", staging / "selected_arithmetic_cases.jsonl",
              staging / "boundary_cases.jsonl", staging / "holdout_arithmetic_cases_v2.jsonl"]
    source.extend(sorted((extensions / "fractions/corpus").glob("*.jsonl.gz")))
    source.extend(sorted((extensions / "decimals/corpus").glob("*.jsonl.gz")))
    source.append(extensions / "structural/curriculum_subskill_cases_v2.jsonl")
    chats = [baseline / "teacher_chat_train_polished.jsonl", staging / "pedagogy_chat_v3.jsonl",
             staging / "selected_arithmetic_chat.jsonl", staging / "boundary_chat.jsonl",
             staging / "holdout_arithmetic_chat_v2.jsonl"]
    return source, chats


def build(staging=STAGING, run_token_audit=True, allow_missing_arithmetic=False):
    sources, chats = input_paths(staging)
    absent = [str(path) for path in sources + chats if not path.exists()]
    if absent and (not allow_missing_arithmetic or any("selected_arithmetic_" not in p for p in absent)):
        raise ValueError("required release inputs absent: " + repr(absent))
    sources, chats = [p for p in sources if p.exists()], [p for p in chats if p.exists()]
    index = loader.load_source_index(sources)
    origin = {}
    for path in sources:
        family = ("preserved_fraction" if "fractions" in path.parts else
                  "preserved_decimal" if "decimals" in path.parts else
                  "preserved_structural" if "structural" in path.parts else
                  "new_pedagogic" if path.name.startswith("pedagogy_") else
                  "new_multidigit_boundary" if path.name.startswith("boundary_") else
                  "new_arithmetic_holdout" if path.name.startswith("holdout_arithmetic_") else
                  "new_finite_arithmetic" if path.name.startswith("selected_arithmetic_") else
                  "preserved_782_curriculum_baseline")
        for source in read_rows(path):
            origin[source["sample_id"]] = family
    preserved_paths = [p for p in sources if "preserved_extensions" in p.parts]
    mandatory = {row["sample_id"] for p in sources[:2] for row in read_rows(p)}
    mandatory.update(row["sample_id"] for p in sources if p.name == "boundary_cases.jsonl" for row in read_rows(p))
    mandatory.update(row["sample_id"] for p in preserved_paths if "structural" in p.parts for row in read_rows(p))
    protected_path = staging / "metadata/thinking/data/exhaustive_math_v1/protected_numeric_signatures.json"
    protected = json.loads(protected_path.read_text("utf-8"))["signatures"]

    def rows():
        for path in chats:
            yield from read_rows(path)
        for path in preserved_paths:
            for source in read_rows(path):
                yield from neutral_chats(source)

    selected, selection = loader.selected_view(rows, index, protected, mandatory, optional_cases_per_category=32)
    selection.update({"input_hashes": [{"name": str(p.relative_to(HERE.parent)), "bytes": p.stat().st_size,
                                       "sha256": loader.file_hash(p)} for p in sources + chats],
                      "protected_blind_index_sha256": loader.file_hash(protected_path),
                      "protected_blind_signatures": len(protected), "preserved_base_cases": 782,
                      "selection_cap_optional_cases_per_topic": 32, "missing_inputs": absent})
    output = staging / ("balanced_preflight" if absent else "balanced_release")
    output.mkdir(parents=True, exist_ok=True)
    selected_ids = set(selection["selected_case_ids"])
    counts = {key: Counter() for key in ("by_split", "by_grade", "by_topic", "by_case_kind", "by_mode", "by_origin")}
    case_seen = set()
    for row in selected():
        sid = loader.case_id(row)
        if sid in case_seen:
            continue
        case_seen.add(sid)
        counts["by_split"][row.get("split", "train")] += 1
        counts["by_grade"][str(row.get("grade", index[sid]["grade"]))] += 1
        counts["by_topic"][index[sid]["topic"]] += 1
        counts["by_case_kind"][index[sid]["case_kind"]] += 1
        counts["by_origin"][origin[sid]] += 1
    selection.update({key: dict(value) for key, value in counts.items() if key != "by_mode"})
    selection.update({"cases_with_actual_student_work": sum(index[sid]["student_work_present"] for sid in selected_ids),
                      "cases_requesting_missing_information": sum(not index[sid]["can_solve"] for sid in selected_ids),
                      "selected_release_independence_scope": "This selected release only; preserved archived overlaps remain disclosed separately."})
    loader.save_json(output / "selection_receipt.json", selection)
    handles, binaries, raws = {}, {}, {}
    try:
        for split in ("train", "validation", "test"):
            raws[split] = (output / f"{split}.jsonl.gz").open("wb")
            binaries[split] = gzip.GzipFile(filename="", mode="wb", fileobj=raws[split], mtime=0)
            handles[split] = io.TextIOWrapper(binaries[split], encoding="utf-8", newline="\n")
        for original in selected():
            row = deepcopy(original)
            sid = loader.case_id(row)
            row["canonical_signatures"] = index[sid]["canonical_signatures"]
            row["selection_category"] = index[sid]["topic"]
            row["selected_view_origin_chat_sha256"] = loader.digest_bytes(loader.canonical_json(original).encode())
            if row.get("row_sha256"):
                row["selected_view_origin_declared_row_sha256"] = row["row_sha256"]
            row.pop("row_sha256", None)
            row["row_sha256"] = loader.digest_bytes(loader.canonical_json(row).encode())
            handles[row.get("split", "train")].write(loader.canonical_json(row) + "\n")
            counts["by_mode"][row["mode"]] += 1
    finally:
        for stream in handles.values():
            stream.close()
        for stream in raws.values():
            stream.close()
    with (output / "selected_sources.jsonl").open("w", encoding="utf-8", newline="\n") as stream:
        for path in sources:
            for row in read_rows(path):
                if row["sample_id"] in selected_ids:
                    stream.write(loader.canonical_json(row) + "\n")
    manifest = {"schema": "MathVisionKid.balanced_training_manifest.v1", "release_scope": "BALANCED_SELECTED_VIEW",
                "full_corpus_changed": False, "model": loader.MODEL, "revision": loader.REVISION,
                "shards": [{"kind": "selected_chat", "file_name": f"{split}.jsonl.gz", "split": split,
                            "bytes": (output / f"{split}.jsonl.gz").stat().st_size,
                            "sha256": loader.file_hash(output / f"{split}.jsonl.gz"),
                            "chat_rows": counts["by_split"][split] * 4}
                           for split in ("train", "validation", "test")],
                "all_four_modes": list(loader.MODES), "source_cases": len(selected_ids),
                "chat_rows": sum(counts["by_mode"].values()), "TRAINING_DATASET_READY": False,
                "arithmetic_input_missing": bool(absent), "no_training_invoked": True,
                "archived_six_million_chat_fully_token_audited": False}
    if run_token_audit:
        tokenizer = loader.load_qwen_tokenizer(Path.home() / ".cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots" / loader.REVISION)
        receipt = loader.full_token_audit(loader.ManifestStream(manifest, output), tokenizer, index)
        loader.save_json(output / "qwen_full_selected_token_audit.json", receipt)
        if not all(receipt["by_split"].get(split, 0) for split in ("train", "validation", "test")):
            raise ValueError("balanced release requires nonempty independent train/validation/test")
        stream = loader.ManifestStream(manifest, output).for_split("train")
        iterator = stream.iter_with_cursors()
        first, cursor = next(iterator)
        expected_second, _ = next(iterator)
        iterator.close()
        resumed = stream.iter_with_cursors(cursor)
        actual_second, _ = next(resumed)
        resumed.close()
        if actual_second != expected_second or first["sample_id"] == actual_second["sample_id"]:
            raise AssertionError("actual selected view resume changed sample order")
        if any(loader.file_hash(HERE.parent / item["name"]) != item["sha256"] for item in selection["input_hashes"]):
            raise ValueError("release input changed while selecting/auditing")
        loader.save_json(output / "data_smoke_receipt.json", {
            "status": "PASSED", "all_selected_rows_tokenized": receipt["unique_samples"],
            "actual_selected_stream_resume_checked": True, "all_input_hashes_unchanged": True,
            "three_nonempty_splits": True, "all_gzip_crc_trailers_read": True,
            "first_sample_id": first["sample_id"], "next_sample_id": actual_second["sample_id"],
            "no_gpu_or_training_started": True, "remote_colab_execution_claimed": False})
        manifest["TRAINING_DATASET_READY"] = not absent
        manifest["token_audit_sha256"] = loader.file_hash(output / "qwen_full_selected_token_audit.json")
    loader.save_json(output / "MathVisionKid_BALANCED_TRAINING_MANIFEST.json", manifest)
    shutil.copy2(HERE / "exhaustive_colab_loader.py", output / "exhaustive_colab_loader.py")
    return {"output": str(output), "selected_cases": len(selected_ids), "chat_rows": manifest["chat_rows"],
            "by_split_cases": dict(counts["by_split"]), "excluded_cases": len(selection["excluded_cases"]),
            "TRAINING_DATASET_READY": manifest["TRAINING_DATASET_READY"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--no-token-audit", action="store_true")
    args = parser.parse_args()
    print(loader.canonical_json(build(run_token_audit=not args.no_token_audit, allow_missing_arithmetic=args.preflight)))
