"""Fail-closed final V3 metadata adjudication; no corpus rows are opened."""
from __future__ import annotations
from copy import deepcopy
import unittest
import hashlib, json
from pathlib import Path

PASS_LABEL = "CURRENT_RECIPE_ONLY_TECHNICAL_PASS_WITH_HASH_BOUND_NUMERIC_OVERLAP_AND_REGRESSION_EXCLUSION"
EXPECTED_IDENTITY = "6faccfa8b6cae5ae100cdd4777c3481b6d193cb79acae2679086ec8e25718f56"
REGRESSION_SAMPLE_ID = "exhaustive_v1_div_1563_43"
REGRESSION_SHA256 = "1729ed713dfedcc0205b130c6573313dcc5784c7eaf5618d0cf32fdc728cf26b"
REGRESSION_MEMBER_KEY = "79765b8281ff64675b4e3826c07b003237875a98d67e898f22f2a4c1f687b0d1"
REGRESSION_ISSUE = {"member": REGRESSION_MEMBER_KEY, "line": 1,
                    "kind": "SOURCE_SPLIT_MISSING_OR_UNKNOWN", "detail": REGRESSION_SAMPLE_ID}
EXPECTED_SPLITS = {"train": 6_502_344, "validation": 24, "test": 24}
EXPECTED_MEMBERS_SHA256 = "b31bede4dd88324a3bbce30a7f14797bb9c4df1df4dc9d719019fc6764478158"
TRAIN17_REVIEW_SHA256 = "b4d4e12a0c5d1d72bfe18a11b77194c2cc3c6b1495add76bf497cf23151b39f8"
SIGNATURE_CROSSWALK_SHA256 = "67d07604202aeb53b2b838f9340a0c784a42ff99eab1cca5f4984d487ad05538"
CROSS_SPLIT_DIAGNOSTIC_SHA256 = "87bdecb6117b7156da7cdf322b2a379629152aa108200b866d443fef5cdac249"
NUMERIC_OVERLAP_POLICY_SHA256 = "c9aa008fb84b81e705e540c56d018c9c2d07278edc775fba57a6d28a2309e472"
NUMERIC_CRITERIA = frozenset({
    "math_independent_oracle", "language_and_grade", "units", "step_reasons_and_checks",
    "evidence_grounded_wrong_work_response", "hint_no_answer_leakage", "split_provenance_and_id",
})
EXPECTED_DIAGNOSTIC_PATH = Path(__file__).with_name("diagnostic.json")
EXPECTED_REVIEW_PATH = Path(__file__).with_name("train17_semantic_review.json")
EXPECTED_CROSSWALK_PATH = Path(__file__).with_name("signature_crosswalk.json")
EXPECTED_POLICY_PATH = Path(__file__).parents[2] / "data" / "primary_math_teacher_20261016" / "numeric_overlap_exception_policy.json"


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json_bytes(value, field):
    if not isinstance(value, bytes):
        raise ValueError(f"{field} must be the exact pinned bytes")
    try:
        return json.loads(value.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{field} must be UTF-8 JSON") from exc


def _issue_dicts_from_diagnostic(diagnostic_bytes):
    doc = _json_bytes(diagnostic_bytes, "diagnostic_bytes")
    if (_sha256(diagnostic_bytes) != CROSS_SPLIT_DIAGNOSTIC_SHA256
            or doc.get("question_or_solution_text_read") is not False
            or doc.get("data_mutated") is not False
            or doc.get("training_started") is not False):
        raise ValueError("cross-split diagnostic pin or provenance differs")
    rows = doc.get("diagnostics")
    if not isinstance(rows, list) or len(rows) != 36:
        raise ValueError("diagnostic must contain exactly 36 canonical overlap rows")
    normalized = []
    for row in rows:
        if (not isinstance(row, dict) or row.get("kind") != "CROSS_SPLIT_CANONICAL"
                or not isinstance(row.get("member"), str) or type(row.get("line")) is not int
                or not isinstance(row.get("detail"), str) or len(row["detail"]) != 64):
            raise ValueError("diagnostic contains malformed canonical overlap metadata")
        normalized.append({k: row[k] for k in ("member", "line", "kind", "detail")})
    if len({(r["member"], r["line"], r["kind"], r["detail"]) for r in normalized}) != 36:
        raise ValueError("diagnostic issue rows are not unique")
    return normalized


def _validate_numeric_overlap_evidence(evidence):
    """Validate exact-byte evidence plus current-recipe-only machine bindings.

    `numeric_overlap_evidence` contains exact bytes fields (`train17_semantic_review_bytes`,
    `signature_crosswalk_bytes`, `numeric_overlap_policy_bytes`, `diagnostic_bytes`) and
    bounded metadata fields from the worker: 17 `train_rows`, each with four chat
    bindings; 68 raw/canonical chat bindings; and six current eval source hash rows.
    No question text is consumed by this adjudicator.
    """
    if not isinstance(evidence, dict):
        raise ValueError("numeric_overlap_evidence must be an object")
    review_bytes = evidence.get("train17_semantic_review_bytes")
    crosswalk_bytes = evidence.get("signature_crosswalk_bytes")
    policy_bytes = evidence.get("numeric_overlap_policy_bytes")
    diagnostic_bytes = evidence.get("diagnostic_bytes")
    for field, raw, expected in (
        ("train17_semantic_review_bytes", review_bytes, TRAIN17_REVIEW_SHA256),
        ("signature_crosswalk_bytes", crosswalk_bytes, SIGNATURE_CROSSWALK_SHA256),
        ("numeric_overlap_policy_bytes", policy_bytes, NUMERIC_OVERLAP_POLICY_SHA256),
        ("diagnostic_bytes", diagnostic_bytes, CROSS_SPLIT_DIAGNOSTIC_SHA256),
    ):
        if not isinstance(raw, bytes) or _sha256(raw) != expected:
            raise ValueError(f"{field} hash differs from its exact evidence pin")
    review = _json_bytes(review_bytes, "train17_semantic_review_bytes")
    crosswalk = _json_bytes(crosswalk_bytes, "signature_crosswalk_bytes")
    policy = _json_bytes(policy_bytes, "numeric_overlap_policy_bytes")
    diagnostic_issues = _issue_dicts_from_diagnostic(diagnostic_bytes)
    if (policy.get("schema_version") != "primary_math.numeric_overlap_exception_policy.v1"
            or policy.get("owner_authorized") is not True
            or policy.get("authorization_origin") != "DIRECT_HUMAN_USER_REPLY"
            or policy.get("training_authorized") is not False):
        raise ValueError("numeric overlap policy authority/scope pin differs")
    if (review.get("schema") != "MathVisionKid.CurrentRecipeNumericOverlap17SemanticReview.v1"
            or review.get("overall_semantic_result") != "PASS_WITH_SCOPE_LIMITS"
            or review.get("source_rows_inspected") != 17
            or review.get("new_human_signoffs") != 0
            or review.get("training_started") is not False
            or review.get("whole_curriculum_certified") is not False
            or review.get("TRAINING_DATASET_READY") is not False):
        raise ValueError("train17 review schema, scope, or provenance differs")
    reviewer = review.get("reviewer", {})
    if (reviewer.get("type") != "AI_REVIEWER"
            or reviewer.get("human_verified") is not False
            or reviewer.get("teacher_certified") is not False
            or reviewer.get("owner_human_reviewed") is not False):
        raise ValueError("train17 review must remain explicitly AI-only")
    if (crosswalk.get("question_or_solution_text_read") is not False
            or crosswalk.get("data_mutated") is not False
            or crosswalk.get("training_started") is not False):
        raise ValueError("signature crosswalk provenance differs")

    cross_matches = crosswalk.get("matches")
    if not isinstance(cross_matches, list):
        raise ValueError("signature crosswalk matches are missing")
    train_matches = [r for r in cross_matches
                     if r.get("source_split") == "train_candidate" and r.get("linked_samples")]
    holdout_matches = [r for r in cross_matches
                       if r.get("source_split") in ("validation", "test")]
    if len(train_matches) != 17 or len(holdout_matches) != 6:
        raise ValueError("crosswalk must pin exactly 17 linked train and six current eval sources")
    expected_train = {r["case_id"]: r for r in train_matches}
    if len(expected_train) != 17 or len({r.get("raw_sha256") for r in train_matches}) != 17:
        raise ValueError("crosswalk train case/raw hashes are not unique")
    review_rows = review.get("rows")
    if not isinstance(review_rows, list) or len(review_rows) != 17:
        raise ValueError("train17 semantic review must contain exactly 17 rows")
    review_by_id = {r.get("sample_id"): r for r in review_rows if isinstance(r, dict)}
    if set(review_by_id) != set(expected_train) or len(review_by_id) != 17:
        raise ValueError("train17 review IDs differ from crosswalk train candidates")

    machine_expected = {
        "schema": "MathVisionKid.CurrentRecipeNumericOverlap17MachineEvidence.v1",
        "source_rows": 17, "chat_rows": 68,
        "all_fraction_decimal_oracles_passed": True,
        "all_current_recipe_members_complete": True,
        "current_normalized_question_conflicts": 0,
        "current_group_conflicts": 0,
        "numeric_expression_disjoint": False,
        "source_chat_payload_bytes_changed": 0, "splits_changed": 0,
        "question_or_solution_text_of_eval_read": False,
        "policy_sha256": NUMERIC_OVERLAP_POLICY_SHA256,
        "semantic_review_sha256": TRAIN17_REVIEW_SHA256,
        "signature_crosswalk_sha256": SIGNATURE_CROSSWALK_SHA256,
        "diagnostic_sha256": CROSS_SPLIT_DIAGNOSTIC_SHA256,
        "TRAINING_DATASET_READY": False, "training_started": False,
        "new_human_signoffs": 0,
    }
    for key, expected in machine_expected.items():
        if evidence.get(key) != expected or type(evidence.get(key)) is not type(expected):
            raise ValueError(f"numeric machine evidence {key} differs from required value")
    for field in ("human_verified", "teacher_certified", "owner_human_reviewed"):
        if evidence.get(field, False) is not False:
            raise ValueError(f"machine evidence must not create human signoff: {field}")

    train_rows = evidence.get("train_rows")
    if not isinstance(train_rows, list) or len(train_rows) != 17:
        raise ValueError("machine evidence must contain exactly 17 train source rows")
    by_train_id = {r.get("case_id"): r for r in train_rows if isinstance(r, dict)}
    if set(by_train_id) != set(expected_train) or len(by_train_id) != 17:
        raise ValueError("machine source IDs differ from the exact train crosswalk")
    expected_chat_pairs = set()
    for case_id, match in expected_train.items():
        review_row = review_by_id[case_id]
        machine_row = by_train_id[case_id]
        if (machine_row.get("source_raw_sha256") != review_row.get("source_raw_sha256")
                or machine_row.get("source_canonical_sha256") != review_row.get("source_canonical_sha256")
                or machine_row.get("source_raw_sha256") != match.get("raw_sha256")
                or machine_row.get("source_canonical_sha256") != match.get("canonical_sha256")
                or machine_row.get("source_split") != "train_candidate"
                or machine_row.get("source_signature_metadata_verified") is not True
                or machine_row.get("oracle_passed") is not True):
            raise ValueError("machine source hash/oracle binding differs for " + case_id)
        checks = review_row.get("checks", {})
        if set(checks) != NUMERIC_CRITERIA:
            raise ValueError("seven semantic QA criteria missing for " + case_id)
        for name, check in checks.items():
            expected_status = "PASS_WITH_SCOPE_LIMITS" if name == "split_provenance_and_id" else "PASS"
            if not isinstance(check, dict) or check.get("status") != expected_status:
                raise ValueError("semantic QA criterion failed or has unexpected scope: " + case_id + ":" + name)
        review_chat = review_row.get("chat_canonical_bindings")
        if not isinstance(review_chat, list) or len(review_chat) != 4:
            raise ValueError("semantic review must bind exactly four chat canonical hashes per source")
        linked = match.get("linked_samples")
        if not isinstance(linked, list) or len(linked) != 4:
            raise ValueError("crosswalk must link exactly four train chat rows per source")
        review_canon = {(r.get("sample_id"), r.get("mode"), r.get("split"), r.get("canonical_sha256")) for r in review_chat}
        cross_canon = {(r.get("sample_id"), r.get("mode"), r.get("split"), r.get("canonical_sha256")) for r in linked}
        if review_canon != cross_canon or len(review_canon) != 4:
            raise ValueError("review/chat canonical bindings differ from crosswalk")
        for chat in review_chat:
            if chat.get("split") != "train" or chat.get("mode") not in {
                    "worked_solution", "hint_level_1", "hint_level_2", "hint_level_3"}:
                raise ValueError("train chat split/mode changed")
            expected_chat_pairs.add((case_id, chat["sample_id"], chat["mode"], chat["canonical_sha256"]))

    machine_chats = []
    for source in train_rows:
        for chat in source["chat_bindings"] if isinstance(source.get("chat_bindings"), list) else []:
            machine_chats.append((source["case_id"], chat))
    if len(machine_chats) != 68:
        raise ValueError("machine evidence must provide all 68 exact chat raw/canonical bindings")
    seen_chat_ids = set()
    for case_id, chat in machine_chats:
        if (not isinstance(chat, dict) or chat.get("split") != "train"
                or chat.get("source_raw_sha256") != by_train_id[case_id].get("source_raw_sha256")
                or chat.get("linkage") != 1
                or not isinstance(chat.get("sample_id"), str)
                or chat.get("mode") not in {"worked_solution", "hint_level_1", "hint_level_2", "hint_level_3"}
                or (case_id, chat.get("sample_id"), chat.get("mode"), chat.get("chat_canonical_sha256")) not in expected_chat_pairs):
            raise ValueError("machine chat linkage/split/hash binding differs")
        for field in ("chat_raw_sha256", "chat_canonical_sha256"):
            value = chat.get(field)
            if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                raise ValueError("machine chat row lacks a valid raw/canonical SHA256")
        for field in ("sequence_tokens", "completion_tokens"):
            value = chat.get(field)
            if type(value) is not int or value <= 0 or value > 40_960:
                raise ValueError("machine chat token counts are invalid")
        if chat["completion_tokens"] > chat["sequence_tokens"]:
            raise ValueError("completion token count exceeds sequence token count")
        if chat["sample_id"] in seen_chat_ids:
            raise ValueError("duplicate machine chat sample ID")
        seen_chat_ids.add(chat["sample_id"])

    expected_eval = {}
    for row in holdout_matches:
        case_id = row["case_id"]
        value = (row.get("raw_sha256"), row.get("canonical_sha256"), row.get("source_split"),
                 tuple(row.get("overlapping_signatures", [])))
        if case_id in expected_eval:
            raise ValueError("crosswalk current eval IDs are not unique")
        expected_eval[case_id] = value
    eval_rows = evidence.get("current_eval_sources")
    if not isinstance(eval_rows, list) or len(eval_rows) != 6:
        raise ValueError("machine evidence must pin all six current eval source hashes")
    actual_eval = {}
    for row in eval_rows:
        if not isinstance(row, dict) or row.get("case_id") in actual_eval:
            raise ValueError("current eval source metadata is malformed or duplicated")
        actual_eval[row["case_id"]] = (row.get("source_raw_sha256"), row.get("source_canonical_sha256"),
                                        row.get("split"), tuple(row.get("signatures", [])))
    if actual_eval != expected_eval:
        raise ValueError("current eval source hashes/signatures differ from fixed crosswalk metadata")
    # Diagnostic and file-pin checks happen before accepting the current-recipe scope.
    if len(diagnostic_issues) != 36:
        raise ValueError("cross-split diagnostic residual count changed")
    return {"train_source_rows": 17, "linked_chat_rows": 68,
            "current_eval_source_rows": 6, "diagnostic_canonical_issue_rows": diagnostic_issues,
            "train_source_ids": sorted(expected_train),
            "current_eval_source_ids": sorted(expected_eval)}


def adjudicate_final_v3_metadata(raw_report: dict, exact_issue_rows: list[dict],
                                 regression_source_meta: dict, zero_linkcounts: dict,
                                 recipe_expected_rowcounts: dict,
                                 numeric_overlap_evidence: dict) -> dict:
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
    evidence_summary = _validate_numeric_overlap_evidence(numeric_overlap_evidence)
    expected_issue_aggregate = {"CROSS_SPLIT_CANONICAL": 36,
                                REGRESSION_ISSUE["kind"]: 1}
    if raw_report.get("issues") != expected_issue_aggregate:
        raise ValueError("raw issue aggregate must preserve 36 canonical overlaps and the pinned regression")
    expected_issue_rows = sorted([REGRESSION_ISSUE, *evidence_summary["diagnostic_canonical_issue_rows"]],
                                 key=lambda r: (r["member"], r["line"], r["kind"], r["detail"]))
    if exact_issue_rows != expected_issue_rows:
        raise ValueError("exact raw issue rows differ from pinned 36+1 findings")
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
        "numeric_overlap_adjudication": {
            "scope": "CURRENT_RECIPE_ONLY",
            "linked_train_source_rows": evidence_summary["train_source_rows"],
            "linked_train_chat_rows": evidence_summary["linked_chat_rows"],
            "fixed_current_eval_source_rows": evidence_summary["current_eval_source_rows"],
            "current_normalized_question_conflicts": 0,
            "current_group_conflicts": 0,
            "numeric_expression_disjoint": False,
            "protected_unread_or_global_eval_independence": "NOT_CLAIMED",
            "new_human_signoffs": 0,
            "source_chat_payload_bytes_changed": 0,
            "splits_changed": 0,
        },
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

