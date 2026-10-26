"""Aggregate already-reviewed frozen-fixture evaluations.

This module never inspects model-output text or assigns a semantic status.
Reviewer JSON is the sole source of PASS/FAIL/PARTIAL/NA judgments.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any

STATUS = {"PASS", "FAIL", "PARTIAL", "NA"}
CRITERIA = ("answer", "unit", "steps", "reason", "hint_safety", "student_error", "missing_info", "gradefit")
MODE_GUARDS = {
    "answer": (),
    "hint_no_answer": ("hint_safety",),
    "student_error": ("student_error",),
    "missing_or_contradictory_info": ("missing_info",),
}
MATH_BASE = ("answer", "unit", "steps", "reason")


def _rows(review: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = review.get("fixtures")
    if not isinstance(rows, list):
        raise ValueError("review fixtures must be a list")
    by_id = {}
    for row in rows:
        fid = row.get("fixture_id")
        if not isinstance(fid, str) or fid in by_id:
            raise ValueError("fixture IDs must be unique nonempty strings")
        if not isinstance(row.get("grade"), int) or not isinstance(row.get("mode"), str):
            raise ValueError(f"fixture {fid} must include integer grade and mode")
        criteria = row.get("criteria")
        if not isinstance(criteria, dict):
            raise ValueError(f"fixture {fid} criteria must be an object")
        for name in CRITERIA:
            item = criteria.get(name)
            if not isinstance(item, dict) or item.get("status") not in STATUS:
                raise ValueError(f"fixture {fid} has invalid/missing {name} status")
            if not isinstance(item.get("applicable"), bool):
                raise ValueError(f"fixture {fid} has invalid {name} applicability")
            if item["applicable"] == (item["status"] == "NA"):
                raise ValueError(f"fixture {fid} {name}: NA and applicability disagree")
        by_id[fid] = row
    if review.get("fixture_count") != len(by_id):
        raise ValueError("fixture_count does not equal unique reviewed fixtures")
    return by_id


def _source_binding(review: dict[str, Any], expected_hash: str, role: str) -> None:
    candidates = []
    source_sha = review.get("source_sha256", {})
    if isinstance(source_sha, dict):
        candidates.extend(source_sha.values())
    provenance = review.get("provenance", {})
    if isinstance(provenance, dict):
        remote = provenance.get("remote_uploaded_raw_file", {})
        if isinstance(remote, dict):
            candidates.append(remote.get("sha256"))
        artifacts = provenance.get("source_artifacts", {})
        if isinstance(artifacts, dict):
            candidates.extend(v.get("sha256") for v in artifacts.values() if isinstance(v, dict))
    if expected_hash not in candidates:
        raise ValueError(f"{role} review is not bound to expected source SHA256 {expected_hash}")


def summarize(review: dict[str, Any]) -> dict[str, Any]:
    rows = _rows(review)
    modes = sorted({r["mode"] for r in rows.values()})
    per_mode = {}
    grade_mode_criterion = defaultdict(Counter)
    for row in rows.values():
        for criterion in CRITERIA:
            item = row["criteria"][criterion]
            if item["applicable"]:
                grade_mode_criterion[(row["grade"], row["mode"], criterion)][item["status"]] += 1
    for mode in modes:
        group = [r for r in rows.values() if r["mode"] == mode]
        required = MATH_BASE + MODE_GUARDS.get(mode, ())
        all_pass = 0
        for row in group:
            states = [row["criteria"][k]["status"] for k in required if row["criteria"][k]["applicable"]]
            if states and all(state == "PASS" for state in states):
                all_pass += 1
        per_mode[mode] = {"strict_math_behavior_pass": all_pass, "denominator": len(group),
                          "required_criteria": list(required), "gradefit_excluded": True}
    answer = [r for r in rows.values() if r["mode"] == "answer"]
    hints = [r for r in rows.values() if r["mode"] == "hint_no_answer"]
    return {
        "per_mode_strict_math_behavior": per_mode,
        "answer_mode_numeric_answer_pass": {
            "pass": sum(r["criteria"]["answer"]["applicable"] and r["criteria"]["answer"]["status"] == "PASS" for r in answer),
            "denominator": len(answer),
        },
        "hint_withholding_pass": {
            "pass": sum(r["criteria"]["answer"]["status"] == "PASS" and r["criteria"]["hint_safety"]["status"] == "PASS" for r in hints),
            "denominator": len(hints),
        },
        "grade_mode_criterion_status_counts_excluding_NA": {
            f"grade_{grade}|{mode}|{criterion}": dict(counts)
            for (grade, mode, criterion), counts in sorted(grade_mode_criterion.items())
        },
        "gradefit_status_counts_excluding_NA": dict(Counter(
            r["criteria"]["gradefit"]["status"] for r in rows.values() if r["criteria"]["gradefit"]["applicable"])),
    }


def compare_reviews(base: dict[str, Any], adapter: dict[str, Any], *,
                    expected_fixture_ids: set[str], expected_fixture_sha256: str,
                    expected_base_source_sha256: str,
                    expected_adapter_source_sha256: str) -> dict[str, Any]:
    """Compare two explicit reviewer outputs, fail-closed on IDs/provenance."""
    if len(expected_fixture_ids) != 28:
        raise ValueError("expected frozen evaluation ID set must contain exactly 28 fixtures")
    b, a = _rows(base), _rows(adapter)
    if set(b) != expected_fixture_ids or set(a) != expected_fixture_ids:
        raise ValueError("both reviews must cover exactly the frozen 28 fixture IDs")
    if base.get("source_sha256", {}).get("new_eval_candidates.jsonl") != expected_fixture_sha256:
        raise ValueError("base review fixture-source SHA does not match frozen fixtures")
    if adapter.get("source_sha256", {}).get("new_eval_candidates.jsonl") != expected_fixture_sha256:
        raise ValueError("adapter review fixture-source SHA does not match frozen fixtures")
    _source_binding(base, expected_base_source_sha256, "base")
    _source_binding(adapter, expected_adapter_source_sha256, "adapter")
    for fid in expected_fixture_ids:
        if (b[fid]["grade"], b[fid]["mode"]) != (a[fid]["grade"], a[fid]["mode"]):
            raise ValueError(f"fixture metadata changed for {fid}")
    changes = []
    for fid in sorted(expected_fixture_ids):
        for criterion in CRITERIA:
            before, after = b[fid]["criteria"][criterion], a[fid]["criteria"][criterion]
            if before["applicable"] != after["applicable"]:
                raise ValueError(f"applicability changed for {fid}/{criterion}")
            if before["status"] != after["status"]:
                changes.append({"fixture_id": fid, "grade": b[fid]["grade"], "mode": b[fid]["mode"],
                                "criterion": criterion, "base": before["status"], "adapter": after["status"]})
    return {
        "schema": "MathVisionKid.frozen_eval_review_comparison.v1",
        "review_type": "LLM semantic review aggregation of explicit reviewer statuses; no human reviewer attestation or independent external validation",
        "fixture_count": len(expected_fixture_ids),
        "fixture_source_sha256": expected_fixture_sha256,
        "base_source_sha256": expected_base_source_sha256,
        "adapter_source_sha256": expected_adapter_source_sha256,
        "review_aggregation_frozen_before_adapter_comparison": True,
        "no_output_text_keyword_scoring": True,
        "base_summary": summarize(base),
        "adapter_summary": summarize(adapter),
        "status_changes": changes,
        "status_change_count": len(changes),
        "overall_aggregation": "No pooled accuracy score. NA is excluded per criterion/mode; numeric-answer result applies only to answer mode; hint withholding is separate; grade fit is separate from mathematical behavior.",
    }


def load_review(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
