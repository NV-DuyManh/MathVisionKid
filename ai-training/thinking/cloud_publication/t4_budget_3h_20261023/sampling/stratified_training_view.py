"""Deterministic train-only case sampler over a precomputed metadata index.

This module never opens corpus payloads, tokenizes examples, or accesses eval
rows. The caller must supply row IDs, row hashes, and source-bound strata from
the accepted current training release's metadata-only index.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import re
from typing import Iterable

MODES = ("worked_solution", "hint_level_1", "hint_level_2", "hint_level_3")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _rank(seed: int, stratum: str, case_id: str) -> str:
    payload = f"{seed}\0{stratum}\0{case_id}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _feature_tuple(row: dict) -> tuple:
    grade = str(row.get("grade", "unknown"))
    if grade not in {"1", "2", "3", "4", "5"}:
        grade = "unknown"
    skills = row.get("skills") or ["unknown"]
    if not isinstance(skills, list) or any(not isinstance(x, str) or not x for x in skills):
        raise ValueError("skills must be a nonempty list of explicit metadata labels")
    skills = tuple(sorted(set(skills))) or ("unknown",)
    method = row.get("method") or "unknown"
    difficulty = row.get("difficulty") or "unknown"
    if not isinstance(method, str) or not isinstance(difficulty, str):
        raise ValueError("method and difficulty must be explicit string labels")
    return grade, skills, method, difficulty


def select_training_view(
    rows: Iterable[dict],
    *,
    target_cases: int,
    seed: int,
    recipe_sha256: str,
    feature_index_sha256: str,
) -> dict:
    """Select whole four-mode cases from accepted train metadata only.

    Feature rows are one-per-chat and must include ``case_id``, ``sample_id``,
    ``split``, ``mode``, ``row_sha256``, ``grade``, ``skills``, ``method`` and
    ``difficulty``. Skills/method/difficulty are trusted only as labels from a
    pinned, source-bound metadata index; this function does no content QA.
    """
    if type(target_cases) is not int or target_cases <= 0:
        raise ValueError("target_cases must be a positive integer")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if not SHA256_RE.fullmatch(recipe_sha256) or not SHA256_RE.fullmatch(feature_index_sha256):
        raise ValueError("recipe and feature-index SHA256 pins are required")

    cases: dict[str, dict] = {}
    for row in rows:
        if row.get("split") != "train":
            raise ValueError("training view accepts train rows only")
        case_id, sample_id, mode = row.get("case_id"), row.get("sample_id"), row.get("mode")
        row_sha = row.get("row_sha256")
        if not all(isinstance(v, str) and v for v in (case_id, sample_id)):
            raise ValueError("case_id and sample_id are required")
        if mode not in MODES or not isinstance(row_sha, str) or not SHA256_RE.fullmatch(row_sha):
            raise ValueError("known mode and row SHA256 required")
        features = _feature_tuple(row)
        case = cases.setdefault(case_id, {"rows": {}, "features": features})
        if case["features"] != features:
            raise ValueError(f"inconsistent stratum labels across modes for case {case_id}")
        if mode in case["rows"]:
            raise ValueError(f"duplicate case/mode: {case_id}/{mode}")
        case["rows"][mode] = {"sample_id": sample_id, "row_sha256": row_sha}

    for case_id, case in cases.items():
        if set(case["rows"]) != set(MODES):
            raise ValueError(f"incomplete four-mode case: {case_id}")

    buckets: dict[str, list[str]] = defaultdict(list)
    for case_id, case in cases.items():
        grade, skills, method, difficulty = case["features"]
        labels = {f"grade:{grade}", f"method:{method}", f"difficulty:{difficulty}"}
        labels.update(f"skill:{skill}" for skill in skills)
        labels.update(f"grade_skill:{grade}|{skill}" for skill in skills)
        for label in labels:
            buckets[label].append(case_id)
    ordered_buckets = {
        label: sorted(ids, key=lambda cid: (_rank(seed, label, cid), cid))
        for label, ids in sorted(buckets.items())
    }

    # Deterministic round-robin over grade, grade-skill, skill, method, then
    # difficulty buckets; each case is added once despite multi-label overlap.
    priority = {"grade": 0, "grade_skill": 1, "skill": 2, "method": 3, "difficulty": 4}
    labels = sorted(ordered_buckets, key=lambda x: (priority[x.split(":", 1)[0]], x))
    selected: set[str] = set()
    offsets = {label: 0 for label in labels}
    while len(selected) < min(target_cases, len(cases)):
        progressed = False
        for label in labels:
            bucket = ordered_buckets[label]
            while offsets[label] < len(bucket) and bucket[offsets[label]] in selected:
                offsets[label] += 1
            if offsets[label] < len(bucket):
                selected.add(bucket[offsets[label]])
                offsets[label] += 1
                progressed = True
                if len(selected) >= min(target_cases, len(cases)):
                    break
        if not progressed:
            break

    by_grade = Counter()
    by_skill = Counter()
    by_method = Counter()
    by_difficulty = Counter()
    selected_cases = []
    for case_id in sorted(selected):
        case = cases[case_id]
        grade, skills, method, difficulty = case["features"]
        by_grade[grade] += 1
        by_skill.update(skills)
        by_method[method] += 1
        by_difficulty[difficulty] += 1
        selected_cases.append({
            "case_id": case_id,
            "grade": grade,
            "skills": list(skills),
            "method": method,
            "difficulty": difficulty,
            "rows": {mode: case["rows"][mode] for mode in MODES},
        })
    manifest = {
        "schema": "MathVisionKid.deterministic_train_view.v1",
        "seed": seed,
        "recipe_sha256": recipe_sha256,
        "feature_index_sha256": feature_index_sha256,
        "split": "train",
        "selection_method": "seeded_hash_round_robin_grade_skill_method_difficulty_whole_case",
        "cases_available_in_index": len(cases),
        "cases_selected": len(selected),
        "chat_rows_selected": len(selected) * len(MODES),
        "all_four_modes_preserved": True,
        "validation_or_test_rows_accepted": 0,
        "by_grade_cases": dict(sorted(by_grade.items())),
        "by_skill_cases": dict(sorted(by_skill.items())),
        "by_method_cases": dict(sorted(by_method.items())),
        "by_difficulty_cases": dict(sorted(by_difficulty.items())),
        "selected_cases": selected_cases,
        "semantic_or_content_quality_claim": False,
    }
    return manifest


def canonical_manifest_sha256(manifest: dict) -> str:
    raw = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
