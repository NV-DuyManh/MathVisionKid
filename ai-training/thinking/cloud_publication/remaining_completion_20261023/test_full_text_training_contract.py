import hashlib
import json

import pytest

import full_text_training_contract as contract


def _bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _evidence(monkeypatch):
    recipe = {"pending_discovery": [], "chat_members": [{}] * 32, "source_members": [{}] * 219,
              "declared_candidate_chat_rows": 6_502_344,
              "current_pedagogy_validation_test_rows_separate": 48}
    recipe_raw = _bytes(recipe)
    recipe_sha = hashlib.sha256(recipe_raw).hexdigest()
    monkeypatch.setattr(contract, "RECIPE_SHA256", recipe_sha)

    snapshot = {
        "identity": contract.RECIPE_IDENTITY,
        "actual_rows_by_split": dict(contract.EXPECTED_ROWS),
        "all_declared_members_scanned": True,
        "members_complete": 251, "members_expected": 251,
        "source_linkage_unverified_rows": 0,
        "incomplete_four_mode_cases": 0, "exact_duplicate_references": 0,
        "max_sequence_tokens": contract.OBSERVED_RELEASE_MAX_SEQUENCE_TOKENS,
        "full_archive_token_linkage_split_audit_complete": False,
    }
    checkpoint = {"fresh_raw_readback_verified": True, "report_at_snapshot": snapshot}
    technical = {
        "status": contract.TECHNICAL_STATUS,
        "TRAINING_DATASET_READY": False,
        "training_started": False,
        "checkpoint": checkpoint,
        "raw_report_preserved": snapshot,
        "machine_evidence_sha256": contract.MACHINE_EVIDENCE_SHA256,
        "numeric_overlap_adjudication": {
            "scope": "CURRENT_RECIPE_ONLY", "numeric_expression_disjoint": False,
            "current_group_conflicts": 0, "current_normalized_question_conflicts": 0,
            "splits_changed": 0, "source_chat_payload_bytes_changed": 0,
            "new_human_signoffs": 0, "protected_unread_or_global_eval_independence": "NOT_CLAIMED",
        },
        "exact_issue_rows_preserved": ([{"kind": "CROSS_SPLIT_CANONICAL"}] * 36
                                       + [{"kind": "SOURCE_SPLIT_MISSING_OR_UNKNOWN"}]),
        "diagnostic_exclusion": {
            "sample_id": contract.REGRESSION_SAMPLE_ID, "linked_chat_rows": 0,
            "raw_sha256": "a" * 64, "canonical_sha256": "a" * 64,
        },
    }
    technical_raw = _bytes(technical)
    manifest = {
        "schema": "MathVisionKid.current_text_candidate_view_final_metadata.v1",
        "recipe_sha256": recipe_sha, "recipe_identity": contract.RECIPE_IDENTITY,
        "selection": "ALL_CURRENT_TRAIN_CANDIDATES_WITH_EVALUATION_SPLITS_RETAINED_SEPARATELY",
        "status": contract.TECHNICAL_STATUS, "TRAINING_DATASET_READY": False,
        "training_started": False, "candidate_chat_rows": 6_502_344,
        "validation_chat_rows": 24, "test_chat_rows": 24,
        "raw_chat_rows_all_current_splits": 6_502_392,
        "technical_adjudication": {
            "name": "final_candidate_chat_technical_adjudication.json",
            "bytes": len(technical_raw), "sha256": hashlib.sha256(technical_raw).hexdigest(),
        },
        "checkpoint": checkpoint,
    }
    manifest_raw = _bytes(manifest)
    text_readiness = {
        "schema": "MathVisionKid.text_training_readiness.v1",
        "TEXT_TRAINING_DATASET_READY": True,
        "recipe_sha256": recipe_sha,
        "recipe_identity": contract.RECIPE_IDENTITY,
        "rows_by_split": dict(contract.EXPECTED_ROWS),
        "status": contract.TECHNICAL_STATUS,
        "readiness_status": "READY_FOR_FULL_TEXT_TRAINING",
        "scope": "TEXT_ONLY_ALL_CURRENT_TRAIN_CANDIDATES", "modality": "text",
        "sampling": False, "train_row_limit": None, "balanced_subset_selected": False,
        "silent_truncation_allowed": False, "max_sequence_tokens": 2048,
        "audited_max_sequence_tokens": 1481,
        "loss_mask": "ASSISTANT_COMPLETION_ONLY_INCLUDING_SINGLE_EOT",
        "acceptance_basis": "OWNER_PREAUTHORIZED_ACCEPTANCE_AND_COMPLETED_CURRENT_RECIPE_TECHNICAL_ADJUDICATION",
        "all_declared_members_scanned": True, "candidate_source_linkage_unverified_rows": 0,
        "checkpoint": checkpoint,
        "source_candidate_manifest": {"bytes": len(manifest_raw),
                                       "sha256": hashlib.sha256(manifest_raw).hexdigest()},
        "technical_adjudication": {"bytes": len(technical_raw),
                                   "sha256": hashlib.sha256(technical_raw).hexdigest()},
    }
    return manifest_raw, technical_raw, recipe_raw, _bytes(text_readiness)


def test_release_evidence_accepts_scoped_text_release_without_promoting_global_ready(monkeypatch):
    manifest, technical, recipe, text_readiness = _evidence(monkeypatch)
    release = contract.validate_release_evidence(
        manifest, technical, recipe, text_readiness, owner_scope=contract.OWNER_SCOPE)
    assert release.report["expected_rows_by_split"] == {
        "train": 6_502_344, "validation": 24, "test": 24}
    assert release.report["text_training_dataset_ready"] is True
    assert release.report["global_training_dataset_ready"] is False
    assert release.report["numeric_expression_disjoint"] is False
    assert release.report["training_started"] is False


def test_release_evidence_rejects_subset_counts_and_wrong_owner_scope(monkeypatch):
    manifest, technical, recipe, text_readiness = _evidence(monkeypatch)
    value = json.loads(manifest)
    value["candidate_chat_rows"] = 5_024
    altered_manifest = _bytes(value)
    readiness = json.loads(text_readiness)
    readiness["source_candidate_manifest"] = {
        "bytes": len(altered_manifest), "sha256": hashlib.sha256(altered_manifest).hexdigest()}
    with pytest.raises(contract.ContractError, match="row totals"):
        contract.validate_release_evidence(altered_manifest, technical, recipe, _bytes(readiness),
                                           owner_scope=contract.OWNER_SCOPE)
    with pytest.raises(contract.ContractError, match="owner scope"):
        contract.validate_release_evidence(manifest, technical, recipe, text_readiness,
                                           owner_scope="small subset")
    scoped = json.loads(text_readiness)
    scoped["TEXT_TRAINING_DATASET_READY"] = False
    with pytest.raises(contract.ContractError, match="scoped text-readiness"):
        contract.validate_release_evidence(manifest, technical, recipe, _bytes(scoped),
                                           owner_scope=contract.OWNER_SCOPE)


def test_training_config_pins_full_text_model_and_no_truncation():
    config = contract.training_config()
    assert config["model_id"] == "Qwen/Qwen3-1.7B"
    assert config["revision"] == "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
    assert config["max_length"] == 2048 and config["truncate"] is False
    assert config["rows_by_split"] == {"train": 6_502_344, "validation": 24, "test": 24}
    assert config["subset_limit"] is None


def test_batch_stream_only_marks_complete_after_exact_full_split(monkeypatch):
    monkeypatch.setattr(contract, "EXPECTED_ROWS", {"train": 3, "validation": 1, "test": 1})
    observed_limits = []

    def encode_stream(stream, tokenizer, max_sequence_tokens):
        observed_limits.append(max_sequence_tokens)
        for row, cursor in stream.iter_with_cursors():
            yield {"split": row["split"], "sample_id": row["sample_id"],
                   "input_ids": [10, row["id"]], "attention_mask": [1, 1],
                   "labels": [-100, row["id"]]}, cursor

    monkeypatch.setattr(contract, "tokenized_stream", encode_stream)

    class Stream:
        split = "train"

        def iter_with_cursors(self):
            for row_id in (1, 2, 3):
                yield {"split": "train", "sample_id": str(row_id), "id": row_id}, None

    batches = list(contract.iter_assistant_only_batches(Stream(), object(), batch_size=2))
    assert [batch["rows_seen"] for batch in batches] == [2, 3]
    assert [batch["complete"] for batch in batches] == [False, True]
    assert observed_limits == [2048]
    contract.require_complete_batch_receipt(batches[-1], "train")
    with pytest.raises(contract.ContractError, match="complete train"):
        contract.require_complete_batch_receipt(batches[0], "train")


def test_batch_stream_rejects_short_or_cross_split_stream(monkeypatch):
    monkeypatch.setattr(contract, "EXPECTED_ROWS", {"train": 2, "validation": 1, "test": 1})
    def encode_stream(stream, tokenizer, max_sequence_tokens):
        for row, cursor in stream.iter_with_cursors():
            yield {"split": row["split"], "sample_id": row["sample_id"],
                   "input_ids": [1], "attention_mask": [1], "labels": [1]}, cursor

    monkeypatch.setattr(contract, "tokenized_stream", encode_stream)

    class ShortStream:
        split = "train"

        def iter_with_cursors(self):
            yield {"split": "train", "sample_id": "one"}, None

    batches = contract.iter_assistant_only_batches(ShortStream(), object(), batch_size=1)
    with pytest.raises(contract.ContractError, match="expected 2"):
        list(batches)

    class MixedStream:
        split = "train"

        def iter_with_cursors(self):
            yield {"split": "validation", "sample_id": "bad"}, None

    with pytest.raises(contract.ContractError, match="another split"):
        list(contract.iter_assistant_only_batches(MixedStream(), object(), batch_size=1))
