import pytest

from actual_coverage import summarize_actual_coverage


def test_partial_optimizer_mode_coverage_is_distinct_from_complete_selected_view():
    modes = ("worked_solution", "hint_level_1", "hint_level_2", "hint_level_3")
    manifest = {"selected_cases_manifest": [
        {"case_id": "case-a", "grade": 2, "family": "sgk_g2", "rows": {m: {"sample_id": f"a:{m}"} for m in modes}},
        {"case_id": "case-b", "grade": None, "rows": {m: {"sample_id": f"b:{m}"} for m in modes}},
    ]}
    log = [{"sample_id": "a:worked_solution"}, {"sample_id": "a:worked_solution"},
           {"sample_id": "a:hint_level_1"}, {"sample_id": "b:hint_level_2"}]
    result = summarize_actual_coverage(manifest, log)
    assert result["selected_view"]["all_selected_cases_have_all_four_modes"] is True
    observed = result["actual_optimizer_coverage"]
    assert observed["example_exposures"] == 4
    assert observed["unique_sample_ids"] == 3
    assert observed["unique_optimizer_cases"] == 2
    assert observed["cases_with_all_four_modes_observed"] == 0
    assert observed["cases_with_partial_mode_coverage"] == 2
    assert observed["unique_cases_by_grade"] == {"2": 1, "unknown": 1}
    assert observed["exposures_by_mode"]["worked_solution"] == 2


def test_rejects_unbound_successful_id_instead_of_guessing_case():
    manifest = {"selected_cases_manifest": [{"case_id": "c", "rows": {"worked_solution": {"sample_id": "c:worked_solution"}}}]}
    with pytest.raises(ValueError, match="absent from selected-view"):
        summarize_actual_coverage(manifest, [{"sample_id": "c:hint_level_1"}])
