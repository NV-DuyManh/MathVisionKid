"""Fail-closed final V3 metadata adjudication; no corpus rows are opened."""
from __future__ import annotations
from copy import deepcopy
import unittest
import hashlib, json
from pathlib import Path

PASS_LABEL = "CURRENT_CANDIDATE_CHAT_TECHNICAL_PASS_WITH_HASH_BOUND_DIAGNOSTIC_EXCLUSION"
EXPECTED_IDENTITY = "f0332df91020ace0fc48d88491fe97364d08826458d08c71ba4ec60524e25863"
REGRESSION_SAMPLE_ID = "exhaustive_v1_div_1563_43"
REGRESSION_SHA256 = "1729ed713dfedcc0205b130c6573313dcc5784c7eaf5618d0cf32fdc728cf26b"
REGRESSION_MEMBER_KEY = "79765b8281ff64675b4e3826c07b003237875a98d67e898f22f2a4c1f687b0d1"
REGRESSION_ISSUE = {"member": REGRESSION_MEMBER_KEY, "line": 1,
                    "kind": "SOURCE_SPLIT_MISSING_OR_UNKNOWN", "detail": REGRESSION_SAMPLE_ID}
EXPECTED_SPLITS = {"train": 6_502_344, "validation": 24, "test": 24}
EXPECTED_MEMBERS_SHA256 = "b31bede4dd88324a3bbce30a7f14797bb9c4df1df4dc9d719019fc6764478158"


def adjudicate_final_v3_metadata(raw_report: dict, exact_issue_rows: list[dict],
                                 regression_source_meta: dict, zero_linkcounts: dict,
                                 recipe_expected_rowcounts: dict) -> dict:
    """Derive technical pass while retaining V3's raw false completion flag.

    Required recipe metadata contains all 251 exact member ids, roles, and row
    counts, plus expected unique_chat_rows_by_split and modes_per_case=4.
    No question text is accepted or needed.
    """
    if not all(isinstance(x, dict) for x in (raw_report, regression_source_meta,
                                               zero_linkcounts, recipe_expected_rowcounts)):
        raise ValueError("metadata inputs must be objects")
    members = recipe_expected_rowcounts.get("members")
    if not isinstance(members, list) or len(members) != 251:
        raise ValueError("recipe must declare exactly 251 members")
    if any(not isinstance(m, dict) or not isinstance(m.get("id"), str) or not m["id"]
           or not isinstance(m.get("rows"), int) or isinstance(m.get("rows"), bool) or m["rows"] < 0
           or m.get("role") not in ("candidate_source", "candidate_chat") for m in members):
        raise ValueError("recipe member ids, roles, or row counts are malformed")
    if len({m["id"] for m in members}) != 251:
        raise ValueError("recipe member ids are not unique")
    if sum(m["role"] == "candidate_source" for m in members) != 219:
        raise ValueError("recipe must contain exactly 219 source members")
    if sum(m["role"] == "candidate_chat" for m in members) != 32:
        raise ValueError("recipe must contain exactly 32 chat members")
    member_bytes = json.dumps(members, ensure_ascii=False, sort_keys=True,
                              separators=(",", ":")).encode()
    if hashlib.sha256(member_bytes).hexdigest() != EXPECTED_MEMBERS_SHA256:
        raise ValueError("exact pinned member metadata differs")

    source_rows = sum(m["rows"] for m in members if m["role"] == "candidate_source")
    physical_chat_rows = sum(m["rows"] for m in members if m["role"] == "candidate_chat")
    expected_splits = recipe_expected_rowcounts.get("unique_chat_rows_by_split")
    if expected_splits != EXPECTED_SPLITS:
        raise ValueError("recipe split expectations differ from current recipe")
    if source_rows != 1_629_906:
        raise ValueError("recipe source row total differs from 1,629,906")
    if physical_chat_rows != 6_502_392 or sum(expected_splits.values()) != physical_chat_rows:
        raise ValueError("recipe physical chat rows differ from expected split totals")
    if recipe_expected_rowcounts.get("unique_chat_rows") != 6_502_392:
        raise ValueError("expected unique chat rows must equal 6,502,392")
    if recipe_expected_rowcounts.get("modes_per_case") != 4:
        raise ValueError("all four modes must be expected")

    if raw_report.get("schema") != "MathVisionKid.full_current_archive_audit.v3":
        raise ValueError("unexpected raw report schema")
    if raw_report.get("identity") != EXPECTED_IDENTITY:
        raise ValueError("raw report recipe identity differs")
    # V3's raw flag is false by design whenever any issue exists. Preserve that
    # raw outcome and derive this narrower status after validating the only
    # permitted, zero-link regression_only diagnostic below.
    if raw_report.get("full_archive_token_linkage_split_audit_complete") is not False:
        raise ValueError("raw V3 completion flag must remain false with the preserved issue")
    required = {
        "members_expected": 251,
        "members_complete": 251,
        "all_declared_members_scanned": True,
        "source_versions_indexed": 1_629_906,
        "unique_chat_rows_processed": 6_502_392,
        "physical_chat_occurrences_processed": 6_502_392,
        "exact_duplicate_references": 0,
        "source_linkage_unverified_rows": 0,
        "incomplete_four_mode_cases": 0,
        "max_sequence_tokens": ("at_most", 40_960),
    }
    for field, expected in required.items():
        actual = raw_report.get(field)
        if isinstance(expected, tuple):
            if type(actual) is not int or not 0 < actual <= expected[1]:
                raise ValueError(f"raw report {field} must be <= {expected[1]}")
        elif actual != expected:
            raise ValueError(f"raw report {field} expected {expected!r}, got {actual!r}")
    if type(raw_report.get("max_completion_tokens")) is not int or not 0 < raw_report["max_completion_tokens"] <= raw_report["max_sequence_tokens"]:
        raise ValueError("raw report must contain a positive max_completion_tokens")
    if raw_report.get("actual_rows_by_split") != EXPECTED_SPLITS:
        raise ValueError("raw report split counts differ from train/validation/test expectations")
    if raw_report.get("issues") != {REGRESSION_ISSUE["kind"]: 1}:
        raise ValueError("raw issue aggregate must contain exactly one pinned diagnostic")
    if exact_issue_rows != [REGRESSION_ISSUE]:
        raise ValueError("issue rows differ from the one permitted exact diagnostic")
    if regression_source_meta != {
        "sample_id": REGRESSION_SAMPLE_ID,
        "split": "regression_only",
        "raw_sha256": REGRESSION_SHA256,
        "canonical_sha256": REGRESSION_SHA256,
    }:
        raise ValueError("regression source identity or hashes differ from the pinned diagnostic")
    if zero_linkcounts != {REGRESSION_SAMPLE_ID: {"linked_chat_rows": 0}}:
        raise ValueError("diagnostic source must have exactly zero linked chats")
    if raw_report.get("TRAINING_DATASET_READY") is not False:
        raise ValueError("TRAINING_DATASET_READY must remain false")
    if raw_report.get("all_rows_semantically_human_reviewed") is not False or raw_report.get("whole_curriculum_certified") is not False:
        raise ValueError("human-review and whole-curriculum flags must remain false")
    if raw_report.get("training_started") is not False or raw_report.get("gpu_used") is not False or raw_report.get("model_weights_loaded") is not False:
        raise ValueError("unexpected training/weights state in raw report")

    return {
        "status": PASS_LABEL,
        "raw_report_preserved": deepcopy(raw_report),
        "exact_issue_rows_preserved": deepcopy(exact_issue_rows),
        "diagnostic_exclusion": {"sample_id": REGRESSION_SAMPLE_ID,
                                 "raw_sha256": REGRESSION_SHA256,
                                 "canonical_sha256": REGRESSION_SHA256,
                                 "linked_chat_rows": 0},
        "TRAINING_DATASET_READY": False,
        "physical_curriculum_pending": True,
    }


class AdjudicationTests(unittest.TestCase):
    def setUp(self):
        # Actual pinned recipe metadata only; no questions or corpus rows.
        self.recipe = {
            "members": json.loads(Path(__file__).with_name("final_recipe_member_metadata.json").read_bytes()),
            "unique_chat_rows": 6_502_392,
            "unique_chat_rows_by_split": dict(EXPECTED_SPLITS),
            "modes_per_case": 4,
        }
        # 218*7442 + 7550 = 1,629,906; 31*203199 + 203223 = 6,502,392.
        self.report = {
            "schema": "MathVisionKid.full_current_archive_audit.v3",
            "identity": EXPECTED_IDENTITY,
            "members_expected": 251, "members_complete": 251,
            "all_declared_members_scanned": True,
            "source_versions_indexed": 1_629_906,
            "unique_chat_rows_processed": 6_502_392,
            "actual_rows_by_split": dict(EXPECTED_SPLITS),
            "physical_chat_occurrences_processed": 6_502_392,
            "exact_duplicate_references": 0,
            "max_sequence_tokens": 40_960,
            "max_completion_tokens": 1_213,
            "source_linkage_unverified_rows": 0,
            "incomplete_four_mode_cases": 0,
            "issues": {"SOURCE_SPLIT_MISSING_OR_UNKNOWN": 1},
            "full_archive_token_linkage_split_audit_complete": False,
            "all_rows_semantically_human_reviewed": False,
            "whole_curriculum_certified": False,
            "TRAINING_DATASET_READY": False,
            "training_started": False, "gpu_used": False, "model_weights_loaded": False,
        }
        self.issues = [dict(REGRESSION_ISSUE)]
        self.source = {"sample_id": REGRESSION_SAMPLE_ID, "split": "regression_only",
                       "raw_sha256": REGRESSION_SHA256, "canonical_sha256": REGRESSION_SHA256}
        self.zero_links = {REGRESSION_SAMPLE_ID: {"linked_chat_rows": 0}}

    def call(self, **overrides):
        args = dict(raw_report=self.report, exact_issue_rows=self.issues,
                    regression_source_meta=self.source, zero_linkcounts=self.zero_links,
                    recipe_expected_rowcounts=self.recipe)
        args.update(overrides)
        return adjudicate_final_v3_metadata(**args)

    def test_accepts_exact_preserved_issue_and_raw_false_flag(self):
        before = deepcopy((self.report, self.issues))
        result = self.call()
        self.assertEqual(result["status"], PASS_LABEL)
        self.assertFalse(result["raw_report_preserved"]["full_archive_token_linkage_split_audit_complete"])
        self.assertEqual(result["exact_issue_rows_preserved"], self.issues)
        self.assertEqual((self.report, self.issues), before)
        self.assertFalse(result["TRAINING_DATASET_READY"])
        self.assertTrue(result["physical_curriculum_pending"])

    def test_rejects_partial_completion(self):
        bad = deepcopy(self.report); bad["members_complete"] = 250
        with self.assertRaisesRegex(ValueError, "members_complete"):
            self.call(raw_report=bad)

    def test_rejects_wrong_identity_and_raw_true_flag(self):
        bad = deepcopy(self.report); bad["identity"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "identity"):
            self.call(raw_report=bad)
        bad = deepcopy(self.report); bad["full_archive_token_linkage_split_audit_complete"] = True
        with self.assertRaisesRegex(ValueError, "raw V3 completion flag"):
            self.call(raw_report=bad)

    def test_rejects_wrong_roles(self):
        bad = deepcopy(self.recipe); bad["members"][0]["role"] = "candidate_chat"
        with self.assertRaisesRegex(ValueError, "219 source members"):
            self.call(recipe_expected_rowcounts=bad)

    def test_rejects_unpinned_member_or_counterbalanced_rows(self):
        bad = deepcopy(self.recipe); bad["members"][0]["id"] = "invented"
        with self.assertRaisesRegex(ValueError, "pinned member"):
            self.call(recipe_expected_rowcounts=bad)
        bad = deepcopy(self.recipe)
        bad["members"][0]["rows"] += 1; bad["members"][1]["rows"] -= 1
        with self.assertRaisesRegex(ValueError, "pinned member"):
            self.call(recipe_expected_rowcounts=bad)

    def test_rejects_bool_or_false_human_claim(self):
        for field in ("max_sequence_tokens", "max_completion_tokens"):
            bad = deepcopy(self.report); bad[field] = True
            with self.assertRaises(ValueError): self.call(raw_report=bad)
        for field in ("all_rows_semantically_human_reviewed", "whole_curriculum_certified"):
            bad = deepcopy(self.report); bad[field] = True
            with self.assertRaises(ValueError): self.call(raw_report=bad)

    def test_rejects_wrong_split_counts(self):
        bad = deepcopy(self.report); bad["actual_rows_by_split"]["validation"] += 1
        with self.assertRaisesRegex(ValueError, "split counts"):
            self.call(raw_report=bad)

    def test_rejects_wrong_source_hash(self):
        bad = deepcopy(self.source); bad["raw_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "regression source identity"):
            self.call(regression_source_meta=bad)

    def test_rejects_linked_diagnostic(self):
        with self.assertRaisesRegex(ValueError, "zero linked chats"):
            self.call(zero_linkcounts={REGRESSION_SAMPLE_ID: {"linked_chat_rows": 1}})

    def test_rejects_extra_issue(self):
        with self.assertRaisesRegex(ValueError, "issue rows differ"):
            self.call(exact_issue_rows=self.issues + [{"member":"x","line":2,"kind":"NEW","detail":"x"}])

    def test_rejects_missing_modes_and_count_mismatch(self):
        bad = deepcopy(self.report); bad["incomplete_four_mode_cases"] = 1
        with self.assertRaisesRegex(ValueError, "incomplete_four_mode_cases"):
            self.call(raw_report=bad)
        bad = deepcopy(self.report); bad["physical_chat_occurrences_processed"] -= 1
        with self.assertRaisesRegex(ValueError, "physical_chat_occurrences_processed"):
            self.call(raw_report=bad)

    def test_rejects_wrong_max_sequence_and_nonpositive_completion(self):
        bad = deepcopy(self.report); bad["max_sequence_tokens"] = 40_961
        with self.assertRaisesRegex(ValueError, "max_sequence_tokens"):
            self.call(raw_report=bad)
        bad = deepcopy(self.report); bad["max_completion_tokens"] = 0
        with self.assertRaisesRegex(ValueError, "max_completion_tokens"):
            self.call(raw_report=bad)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(AdjudicationTests))
    raise SystemExit(0 if result.wasSuccessful() else 1)
