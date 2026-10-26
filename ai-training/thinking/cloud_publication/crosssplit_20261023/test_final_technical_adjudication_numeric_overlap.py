"""Focused tests for current-recipe numeric-overlap adjudication metadata."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import final_technical_adjudication_numeric_overlap as M


class NumericOverlapAdjudicationTests(unittest.TestCase):
    def setUp(self):
        self.review_bytes = (HERE / "train17_semantic_review.json").read_bytes()
        self.crosswalk_bytes = (HERE / "signature_crosswalk.json").read_bytes()
        self.diag_bytes = (HERE / "diagnostic.json").read_bytes()
        self.policy_bytes = (HERE.parent.parent / "data" / "primary_math_teacher_20261016" /
                             "numeric_overlap_exception_policy.json").read_bytes()
        self.review = json.loads(self.review_bytes)
        self.crosswalk = json.loads(self.crosswalk_bytes)
        train_matches = [r for r in self.crosswalk["matches"]
                         if r["source_split"] == "train_candidate" and r["linked_samples"]]
        review_by_id = {r["sample_id"]: r for r in self.review["rows"]}
        self.machine = {
            "schema": "MathVisionKid.CurrentRecipeNumericOverlap17MachineEvidence.v1",
            "source_rows": 17, "chat_rows": 68,
            "all_fraction_decimal_oracles_passed": True,
            "all_current_recipe_members_complete": True,
            "current_normalized_question_conflicts": 0,
            "current_group_conflicts": 0,
            "numeric_expression_disjoint": False,
            "source_chat_payload_bytes_changed": 0, "splits_changed": 0,
            "question_or_solution_text_of_eval_read": False,
            "policy_sha256": M.NUMERIC_OVERLAP_POLICY_SHA256,
            "semantic_review_sha256": M.TRAIN17_REVIEW_SHA256,
            "signature_crosswalk_sha256": M.SIGNATURE_CROSSWALK_SHA256,
            "diagnostic_sha256": M.CROSS_SPLIT_DIAGNOSTIC_SHA256,
            "TRAINING_DATASET_READY": False, "training_started": False,
            "new_human_signoffs": 0,
            "train17_semantic_review_bytes": self.review_bytes,
            "signature_crosswalk_bytes": self.crosswalk_bytes,
            "numeric_overlap_policy_bytes": self.policy_bytes,
            "diagnostic_bytes": self.diag_bytes,
            "train_rows": [], "current_eval_sources": [],
        }
        for match in train_matches:
            case_id = match["case_id"]
            review_row = review_by_id[case_id]
            chats = []
            for chat in review_row["chat_canonical_bindings"]:
                chats.append({
                    "sample_id": chat["sample_id"], "mode": chat["mode"], "split": "train",
                    "chat_raw_sha256": hashlib.sha256(chat["sample_id"].encode()).hexdigest(),
                    "chat_canonical_sha256": chat["canonical_sha256"],
                    "source_raw_sha256": review_row["source_raw_sha256"], "linkage": 1,
                    "sequence_tokens": 120, "completion_tokens": 20,
                })
            self.machine["train_rows"].append({
                "case_id": case_id,
                "source_raw_sha256": review_row["source_raw_sha256"],
                "source_canonical_sha256": review_row["source_canonical_sha256"],
                "source_split": "train_candidate",
                "source_signature_metadata_verified": True,
                "oracle_passed": True,
                "chat_bindings": chats,
            })
        for match in self.crosswalk["matches"]:
            if match["source_split"] in ("validation", "test"):
                self.machine["current_eval_sources"].append({
                    "case_id": match["case_id"],
                    "source_raw_sha256": match["raw_sha256"],
                    "source_canonical_sha256": match["canonical_sha256"],
                    "split": match["source_split"],
                    "signatures": match["overlapping_signatures"],
                })
        self.raw = {
            "schema": "MathVisionKid.full_current_archive_audit.v3",
            "identity": M.EXPECTED_IDENTITY,
            "members_expected": 251, "members_complete": 251,
            "all_declared_members_scanned": True,
            "source_versions_indexed": 1_629_906,
            "unique_chat_rows_processed": 6_502_392,
            "actual_rows_by_split": dict(M.EXPECTED_SPLITS),
            "physical_chat_occurrences_processed": 6_502_392,
            "exact_duplicate_references": 0,
            "max_sequence_tokens": 40_960, "max_completion_tokens": 1213,
            "source_linkage_unverified_rows": 0, "incomplete_four_mode_cases": 0,
            "issues": {"CROSS_SPLIT_CANONICAL": 36, "SOURCE_SPLIT_MISSING_OR_UNKNOWN": 1},
            "full_archive_token_linkage_split_audit_complete": False,
            "all_rows_semantically_human_reviewed": False, "whole_curriculum_certified": False,
            "TRAINING_DATASET_READY": False,
            "training_started": False, "gpu_used": False, "model_weights_loaded": False,
        }
        diagnostic = json.loads(self.diag_bytes)
        self.issues = [{k: r[k] for k in ("member", "line", "kind", "detail")}
                       for r in diagnostic["diagnostics"]]
        self.issues.append(dict(M.REGRESSION_ISSUE))
        self.issues.sort(key=lambda r: (r["member"], r["line"], r["kind"], r["detail"]))
        self.source = {"sample_id": M.REGRESSION_SAMPLE_ID, "split": "regression_only",
                       "raw_sha256": M.REGRESSION_SHA256, "canonical_sha256": M.REGRESSION_SHA256}
        self.zero_links = {M.REGRESSION_SAMPLE_ID: {"linked_chat_rows": 0}}
        self.recipe = {
            "members": json.loads((HERE.parent / "structural15_adapter_20261023" /
                                   "final_recipe_member_metadata.json").read_bytes()),
            "unique_chat_rows": 6_502_392,
            "unique_chat_rows_by_split": dict(M.EXPECTED_SPLITS), "modes_per_case": 4,
        }

    def call(self, **overrides):
        args = dict(raw_report=self.raw, exact_issue_rows=self.issues,
                    regression_source_meta=self.source, zero_linkcounts=self.zero_links,
                    recipe_expected_rowcounts=self.recipe,
                    numeric_overlap_evidence=self.machine)
        args.update(overrides)
        return M.adjudicate_final_v3_metadata(**args)

    def test_accepts_scoped_current_recipe_evidence_and_preserves_raw_issues(self):
        result = self.call()
        self.assertEqual(result["status"], M.PASS_LABEL)
        self.assertFalse(result["raw_report_preserved"]["full_archive_token_linkage_split_audit_complete"])
        self.assertEqual(len(result["exact_issue_rows_preserved"]), 37)
        detail = result["numeric_overlap_adjudication"]
        self.assertEqual(detail["scope"], "CURRENT_RECIPE_ONLY")
        self.assertEqual(detail["linked_train_source_rows"], 17)
        self.assertEqual(detail["linked_train_chat_rows"], 68)
        self.assertFalse(detail["numeric_expression_disjoint"])
        self.assertEqual(detail["protected_unread_or_global_eval_independence"], "NOT_CLAIMED")
        self.assertFalse(result["TRAINING_DATASET_READY"])

    def test_rejects_missing_extra_or_changed_exact_issue(self):
        with self.assertRaisesRegex(ValueError, "exact raw issue rows"):
            self.call(exact_issue_rows=self.issues[:-1])
        with self.assertRaisesRegex(ValueError, "exact raw issue rows"):
            self.call(exact_issue_rows=self.issues + [dict(self.issues[0], detail="extra")])
        bad = deepcopy(self.issues); bad[0]["detail"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "exact raw issue rows"):
            self.call(exact_issue_rows=bad)

    def test_rejects_changed_hash_failed_oracle_and_missing_chat_binding(self):
        bad = deepcopy(self.machine); bad["train_rows"][0]["source_raw_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source hash/oracle binding"):
            self.call(numeric_overlap_evidence=bad)
        bad = deepcopy(self.machine); bad["train_rows"][0]["oracle_passed"] = False
        with self.assertRaisesRegex(ValueError, "source hash/oracle binding"):
            self.call(numeric_overlap_evidence=bad)
        bad = deepcopy(self.machine); bad["train_rows"][0]["chat_bindings"].pop()
        with self.assertRaisesRegex(ValueError, "all 68 exact chat"):
            self.call(numeric_overlap_evidence=bad)

    def test_rejects_missing_qa_false_human_claim_and_conflicts(self):
        bad = deepcopy(self.machine); bad["new_human_signoffs"] = 1
        with self.assertRaisesRegex(ValueError, "new_human_signoffs"):
            self.call(numeric_overlap_evidence=bad)
        bad = deepcopy(self.machine); bad["owner_human_reviewed"] = True
        with self.assertRaisesRegex(ValueError, "must not create human signoff"):
            self.call(numeric_overlap_evidence=bad)
        bad = deepcopy(self.machine); bad["current_group_conflicts"] = 1
        with self.assertRaisesRegex(ValueError, "current_group_conflicts"):
            self.call(numeric_overlap_evidence=bad)
        # Exact-byte pin ensures a QA criterion cannot be removed or downgraded silently.
        review = json.loads(self.review_bytes); review["rows"][0]["checks"].pop("units")
        bad = deepcopy(self.machine)
        bad["train17_semantic_review_bytes"] = json.dumps(review).encode()
        with self.assertRaisesRegex(ValueError, "exact evidence pin"):
            self.call(numeric_overlap_evidence=bad)

    def test_rejects_wrong_pinned_docs_and_eval_hash(self):
        bad = deepcopy(self.machine); bad["current_eval_sources"][0]["source_raw_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "current eval source hashes"):
            self.call(numeric_overlap_evidence=bad)
        bad = deepcopy(self.machine); bad["signature_crosswalk_bytes"] += b" "
        with self.assertRaisesRegex(ValueError, "signature_crosswalk_bytes hash"):
            self.call(numeric_overlap_evidence=bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)

