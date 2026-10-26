import hashlib
import pytest

from stratified_training_view import MODES, select_training_view, canonical_manifest_sha256

RECIPE = "1" * 64
FEATURES = "2" * 64


def rows(n=8):
    result = []
    skills = ["whole_number", "fraction_decimal", "word_problem", "geometry_measurement"]
    for i in range(n):
        case = f"case-{i:03d}"
        for mode in MODES:
            body = f"{case}:{mode}".encode()
            result.append({
                "case_id": case,
                "sample_id": f"{case}:{mode}",
                "split": "train",
                "mode": mode,
                "row_sha256": hashlib.sha256(body).hexdigest(),
                "grade": str(i % 5 + 1),
                "skills": [skills[i % len(skills)]],
                "method": ["direct", "multi_step", "visual_reasoning", "error_analysis"][i % 4],
                "difficulty": ["foundation", "intermediate", "challenge"][i % 3],
            })
    return result


def test_selection_is_deterministic_train_only_and_preserves_four_modes():
    manifest = select_training_view(rows(), target_cases=5, seed=20261023,
                                    recipe_sha256=RECIPE, feature_index_sha256=FEATURES)
    repeated = select_training_view(reversed(rows()), target_cases=5, seed=20261023,
                                    recipe_sha256=RECIPE, feature_index_sha256=FEATURES)
    assert manifest == repeated
    assert manifest["cases_selected"] == 5
    assert manifest["chat_rows_selected"] == 20
    assert manifest["validation_or_test_rows_accepted"] == 0
    assert all(set(case["rows"]) == set(MODES) for case in manifest["selected_cases"])
    assert all(len({v["row_sha256"] for v in case["rows"].values()}) == 4
               for case in manifest["selected_cases"])
    assert canonical_manifest_sha256(manifest) == canonical_manifest_sha256(repeated)


@pytest.mark.parametrize("change,match", [
    ({"split": "validation"}, "train rows only"),
    ({"row_sha256": "bad"}, "SHA256"),
    ({"mode": "hint_level_4"}, "known mode"),
])
def test_rejects_nontrain_or_unpinned_rows(change, match):
    data = rows()
    data[0] = {**data[0], **change}
    with pytest.raises(ValueError, match=match):
        select_training_view(data, target_cases=2, seed=1,
                             recipe_sha256=RECIPE, feature_index_sha256=FEATURES)


def test_rejects_incomplete_case_and_inconsistent_features():
    data = rows()
    data.pop()
    with pytest.raises(ValueError, match="incomplete four-mode"):
        select_training_view(data, target_cases=2, seed=1,
                             recipe_sha256=RECIPE, feature_index_sha256=FEATURES)
    data = rows()
    data[1] = {**data[1], "grade": "5"}
    with pytest.raises(ValueError, match="inconsistent stratum"):
        select_training_view(data, target_cases=2, seed=1,
                             recipe_sha256=RECIPE, feature_index_sha256=FEATURES)
