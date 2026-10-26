import json
from pathlib import Path

import pytest

from review_aggregation import compare_reviews, load_review, summarize


ROOT = Path(__file__).parent
BASE = load_review(ROOT / "base_semantic_review.json")
FIXTURE_IDS = {x["fixture_id"] for x in BASE["fixtures"]}
FIXTURE_SHA = BASE["source_sha256"]["new_eval_candidates.jsonl"]
BASE_SHA = BASE["provenance"]["remote_uploaded_raw_file"]["sha256"]


def test_base_frozen_summary_matches_previously_reported_mode_counts():
    result = summarize(BASE)
    assert {mode: (value["strict_math_behavior_pass"], value["denominator"])
            for mode, value in result["per_mode_strict_math_behavior"].items()} == {
                "answer": (8, 13), "hint_no_answer": (3, 5),
                "missing_or_contradictory_info": (4, 6), "student_error": (2, 4)}
    assert result["answer_mode_numeric_answer_pass"] == {"pass": 10, "denominator": 13}
    assert result["hint_withholding_pass"] == {"pass": 3, "denominator": 5}


def test_comparison_requires_exact_frozen_fixture_and_source_bindings():
    result = compare_reviews(BASE, BASE, expected_fixture_ids=FIXTURE_IDS,
        expected_fixture_sha256=FIXTURE_SHA, expected_base_source_sha256=BASE_SHA,
        expected_adapter_source_sha256=BASE_SHA)
    assert result["status_changes"] == []
    assert result["review_aggregation_frozen_before_adapter_comparison"] is True
    with pytest.raises(ValueError, match="exactly 28"):
        compare_reviews(BASE, BASE, expected_fixture_ids=FIXTURE_IDS - {"g1_add_objects"},
            expected_fixture_sha256=FIXTURE_SHA, expected_base_source_sha256=BASE_SHA,
            expected_adapter_source_sha256=BASE_SHA)


def test_comparison_rejects_changed_na_applicability_or_source_hash():
    altered = json.loads(json.dumps(BASE))
    altered["fixtures"][0]["criteria"]["student_error"]["applicable"] = True
    with pytest.raises(ValueError, match="NA and applicability disagree"):
        summarize(altered)
    with pytest.raises(ValueError, match="fixture-source SHA"):
        compare_reviews(BASE, BASE, expected_fixture_ids=FIXTURE_IDS,
            expected_fixture_sha256="0" * 64, expected_base_source_sha256=BASE_SHA,
            expected_adapter_source_sha256=BASE_SHA)
