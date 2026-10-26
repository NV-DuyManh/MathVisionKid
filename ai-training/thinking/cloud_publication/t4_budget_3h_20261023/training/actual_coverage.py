"""CPU metadata-only observed training-view coverage from successful ID logs."""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable

MODES = ("worked_solution", "hint_level_1", "hint_level_2", "hint_level_3")


def summarize_actual_coverage(manifest: dict[str, Any], successful_id_records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Measure optimizer exposure/unique-case mode coverage from logged IDs.

    Uses only selected-case manifest metadata and successful_ids records; never
    opens or reconstructs the training rows. No missing grade/family is inferred.
    """
    selected = manifest.get("selected_cases_manifest")
    if not isinstance(selected, list):
        raise ValueError("selected_cases_manifest is required")
    sample_to_case: dict[str, tuple[str, str]] = {}
    case_metadata: dict[str, dict[str, Any]] = {}
    selected_modes_by_case: dict[str, set[str]] = {}
    for case in selected:
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id or case_id in case_metadata:
            raise ValueError("selected cases require unique nonempty case_id values")
        rows = case.get("rows")
        if not isinstance(rows, dict):
            raise ValueError(f"selected case {case_id} is missing mode row bindings")
        selected_modes_by_case[case_id] = set(rows)
        case_metadata[case_id] = case
        for mode, binding in rows.items():
            sid = binding.get("sample_id") if isinstance(binding, dict) else None
            if mode not in MODES or not isinstance(sid, str) or not sid:
                raise ValueError(f"invalid selected sample binding for {case_id}/{mode}")
            if sid in sample_to_case:
                raise ValueError(f"duplicate selected sample_id {sid}")
            sample_to_case[sid] = (case_id, mode)

    exposure_count = 0
    exposure_by_mode: Counter[str] = Counter()
    exposures_by_grade: Counter[str] = Counter()
    exposures_by_family: Counter[str] = Counter()
    unique_ids: set[str] = set()
    observed_modes_by_case: dict[str, set[str]] = defaultdict(set)
    observed_unique_mode_rows: set[tuple[str, str]] = set()
    for record in successful_id_records:
        sid = record.get("sample_id")
        if not isinstance(sid, str) or sid not in sample_to_case:
            raise ValueError(f"successful sample_id is absent from selected-view manifest: {sid!r}")
        case_id, mode = sample_to_case[sid]
        exposure_count += 1
        unique_ids.add(sid)
        exposure_by_mode[mode] += 1
        observed_unique_mode_rows.add((case_id, mode))
        observed_modes_by_case[case_id].add(mode)
        case = case_metadata[case_id]
        grade = case.get("grade")
        family = case.get("family")
        exposures_by_grade[str(grade) if grade is not None else "unknown"] += 1
        exposures_by_family[str(family) if family is not None else "unknown"] += 1

    observed_cases = set(observed_modes_by_case)
    all_four = sum(set(MODES) <= observed_modes_by_case[cid] for cid in observed_cases)
    per_mode_unique_cases = {mode: len({cid for cid, seen in observed_modes_by_case.items() if mode in seen}) for mode in MODES}
    selected_grade_counts = Counter(str(c.get("grade")) if c.get("grade") is not None else "unknown" for c in selected)
    selected_family_counts = Counter(str(c.get("family")) if c.get("family") is not None else "unknown" for c in selected)
    unique_cases_by_grade = Counter(str(case_metadata[cid].get("grade")) if case_metadata[cid].get("grade") is not None else "unknown" for cid in observed_cases)
    unique_cases_by_family = Counter(str(case_metadata[cid].get("family")) if case_metadata[cid].get("family") is not None else "unknown" for cid in observed_cases)
    return {
        "schema": "MathVisionKid.actual_training_coverage.v1",
        "basis": "successful_ids.jsonl sample_id records joined to selected_cases_manifest; metadata-only, no train row content",
        "selected_view": {
            "cases": len(selected), "chat_rows": len(sample_to_case),
            "all_selected_cases_have_all_four_modes": all(set(MODES) <= modes for modes in selected_modes_by_case.values()),
            "cases_by_grade": dict(selected_grade_counts), "cases_by_family": dict(selected_family_counts),
        },
        "actual_optimizer_coverage": {
            "example_exposures": exposure_count,
            "unique_sample_ids": len(unique_ids),
            "unique_optimizer_cases": len(observed_cases),
            "unique_case_mode_rows": len(observed_unique_mode_rows),
            "cases_with_all_four_modes_observed": all_four,
            "cases_with_partial_mode_coverage": len(observed_cases) - all_four,
            "exposures_by_mode": {mode: exposure_by_mode.get(mode, 0) for mode in MODES},
            "unique_cases_by_mode": per_mode_unique_cases,
            "exposures_by_grade": dict(exposures_by_grade),
            "unique_cases_by_grade": dict(unique_cases_by_grade),
            "exposures_by_family": dict(exposures_by_family),
            "unique_cases_by_family": dict(unique_cases_by_family),
            "coverage_note": "A selected case having four rows does not imply all four modes were encountered by optimizer steps. Repeats count as exposures but not new unique IDs/cases.",
        },
    }
