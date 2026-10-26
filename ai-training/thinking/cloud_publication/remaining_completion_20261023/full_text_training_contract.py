"""Data-only contract for the current full-text MathVisionKid release.

This module validates a pinned release and streams assistant-only batches. It
does not load a model, import torch, mutate Drive, sample rows, or change the
global corpus readiness fields. A training caller must observe the terminal
``complete`` batch for every train epoch and must reserve test rows.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping

# The existing data-only streaming modules live directly under ``thinking``.
_THINKING_DIR = str(Path(__file__).resolve().parents[2])
if _THINKING_DIR not in sys.path:
    sys.path.insert(0, _THINKING_DIR)

from exhaustive_colab_loader import pad_batch, tokenized_stream
from math_data_candidate_stream import CandidateStream


RECIPE_SHA256 = "1bb69c394c7eaaea7034125c6b3361eebbbe0d77e0715a8454331fbe7cee3ff8"
RECIPE_IDENTITY = "6faccfa8b6cae5ae100cdd4777c3481b6d193cb79acae2679086ec8e25718f56"
MODEL_ID = "Qwen/Qwen3-1.7B"
MODEL_REVISION = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
MACHINE_EVIDENCE_SHA256 = "e33cd3c47840ccdeb44bdb4efc118e3e03f830b0140ed762d5e9fc15efc5578d"
MAX_SEQUENCE_TOKENS = 2048
OBSERVED_RELEASE_MAX_SEQUENCE_TOKENS = 1481
EXPECTED_ROWS = {"train": 6_502_344, "validation": 24, "test": 24}
OWNER_SCOPE = "ALL_CURRENT_TEXT_CANDIDATES_THEN_ADD_IMAGES_AND_PRACTICE_LATER"
TECHNICAL_STATUS = (
    "CURRENT_RECIPE_ONLY_TECHNICAL_PASS_WITH_HASH_BOUND_NUMERIC_OVERLAP_"
    "AND_REGRESSION_EXCLUSION"
)
REGRESSION_SAMPLE_ID = "exhaustive_v1_div_1563_43"


class ContractError(ValueError):
    """The supplied release evidence or stream violates the pinned contract."""


@dataclass(frozen=True)
class ValidatedRelease:
    recipe: Mapping[str, Any]
    report: Mapping[str, Any]


def _json_object(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be a JSON object")
    return value


def validate_release_evidence(
    candidate_manifest_bytes: bytes,
    technical_adjudication_bytes: bytes,
    recipe_bytes: bytes,
    text_readiness_bytes: bytes,
    *,
    owner_scope: str,
) -> ValidatedRelease:
    """Verify the exact current text release without promoting global READY.

    ``owner_scope`` is the direct user selection for this training phase. The
    stored global readiness and human-review flags remain unchanged in report.
    """
    if owner_scope != OWNER_SCOPE:
        raise ContractError("explicit full-text-only owner scope is required")
    recipe_sha = hashlib.sha256(recipe_bytes).hexdigest()
    if recipe_sha != RECIPE_SHA256:
        raise ContractError("recipe bytes do not match the pinned current release")

    manifest = _json_object(candidate_manifest_bytes, "candidate manifest")
    technical = _json_object(technical_adjudication_bytes, "technical adjudication")
    recipe = _json_object(recipe_bytes, "recipe")
    text_readiness = _json_object(text_readiness_bytes, "text readiness manifest")

    if (text_readiness.get("schema") != "MathVisionKid.text_training_readiness.v1"
            or text_readiness.get("TEXT_TRAINING_DATASET_READY") is not True
            or text_readiness.get("recipe_sha256") != RECIPE_SHA256
            or text_readiness.get("recipe_identity") != RECIPE_IDENTITY
            or text_readiness.get("rows_by_split") != EXPECTED_ROWS
            or text_readiness.get("status") != TECHNICAL_STATUS
            or text_readiness.get("readiness_status") != "READY_FOR_FULL_TEXT_TRAINING"
            or text_readiness.get("scope") != "TEXT_ONLY_ALL_CURRENT_TRAIN_CANDIDATES"
            or text_readiness.get("modality") != "text"
            or text_readiness.get("sampling") is not False
            or text_readiness.get("train_row_limit") is not None
            or text_readiness.get("balanced_subset_selected") is not False
            or text_readiness.get("silent_truncation_allowed") is not False
            or text_readiness.get("max_sequence_tokens") != MAX_SEQUENCE_TOKENS
            or text_readiness.get("audited_max_sequence_tokens") != OBSERVED_RELEASE_MAX_SEQUENCE_TOKENS
            or text_readiness.get("loss_mask") != "ASSISTANT_COMPLETION_ONLY_INCLUDING_SINGLE_EOT"
            or text_readiness.get("acceptance_basis") != "OWNER_PREAUTHORIZED_ACCEPTANCE_AND_COMPLETED_CURRENT_RECIPE_TECHNICAL_ADJUDICATION"):
        raise ContractError("scoped text-readiness manifest is absent, false, or does not match this release")

    if manifest.get("schema") != "MathVisionKid.current_text_candidate_view_final_metadata.v1":
        raise ContractError("unexpected candidate manifest schema")
    if manifest.get("recipe_sha256") != RECIPE_SHA256 or manifest.get("recipe_identity") != RECIPE_IDENTITY:
        raise ContractError("candidate manifest does not bind the pinned recipe")
    if manifest.get("selection") != "ALL_CURRENT_TRAIN_CANDIDATES_WITH_EVALUATION_SPLITS_RETAINED_SEPARATELY":
        raise ContractError("candidate selection is not the full current text release")
    if manifest.get("status") != TECHNICAL_STATUS or technical.get("status") != TECHNICAL_STATUS:
        raise ContractError("technical status differs from the approved current-recipe scope")
    if manifest.get("training_started") is not False or technical.get("training_started") is not False:
        raise ContractError("release evidence already records training as started")

    candidate_hash = hashlib.sha256(candidate_manifest_bytes).hexdigest()
    candidate_ref = text_readiness.get("source_candidate_manifest") or {}
    if (candidate_ref.get("bytes") != len(candidate_manifest_bytes)
            or candidate_ref.get("sha256") != candidate_hash):
        raise ContractError("candidate manifest does not match the scoped readiness pin")
    technical_ref = manifest.get("technical_adjudication") or {}
    technical_hash = hashlib.sha256(technical_adjudication_bytes).hexdigest()
    if (technical_ref.get("name") != "final_candidate_chat_technical_adjudication.json"
            or technical_ref.get("bytes") != len(technical_adjudication_bytes)
            or technical_ref.get("sha256") != technical_hash):
        raise ContractError("technical adjudication bytes do not match the manifest pin")
    readiness_technical_ref = text_readiness.get("technical_adjudication") or {}
    if (readiness_technical_ref.get("bytes") != len(technical_adjudication_bytes)
            or readiness_technical_ref.get("sha256") != technical_hash):
        raise ContractError("technical adjudication does not match the scoped readiness pin")

    expected_total = sum(EXPECTED_ROWS.values())
    if (manifest.get("candidate_chat_rows") != EXPECTED_ROWS["train"]
            or manifest.get("validation_chat_rows") != EXPECTED_ROWS["validation"]
            or manifest.get("test_chat_rows") != EXPECTED_ROWS["test"]
            or manifest.get("raw_chat_rows_all_current_splits") != expected_total):
        raise ContractError("release row totals changed; refusing a subset or stale manifest")

    checkpoint = manifest.get("checkpoint")
    if not isinstance(checkpoint, dict) or technical.get("checkpoint") != checkpoint:
        raise ContractError("candidate and technical checkpoint objects differ")
    if text_readiness.get("checkpoint") != checkpoint:
        raise ContractError("scoped readiness checkpoint differs from the audited checkpoint")
    snapshot = checkpoint.get("report_at_snapshot") or {}
    preserved_report = technical.get("raw_report_preserved") or {}
    if (checkpoint.get("fresh_raw_readback_verified") is not True
            or snapshot.get("identity") != RECIPE_IDENTITY
            or snapshot.get("actual_rows_by_split") != EXPECTED_ROWS
            or snapshot.get("all_declared_members_scanned") is not True
            or snapshot.get("members_complete") != 251
            or snapshot.get("members_expected") != 251
            or snapshot.get("source_linkage_unverified_rows") != 0
            or snapshot.get("incomplete_four_mode_cases") != 0
            or snapshot.get("exact_duplicate_references") != 0
            or snapshot.get("max_sequence_tokens") != OBSERVED_RELEASE_MAX_SEQUENCE_TOKENS
            or snapshot.get("full_archive_token_linkage_split_audit_complete") is not False
            or preserved_report != snapshot):
        raise ContractError("checkpoint snapshot no longer matches the pinned text-release evidence")
    if technical.get("machine_evidence_sha256") != MACHINE_EVIDENCE_SHA256:
        raise ContractError("machine-evidence SHA256 pin changed")
    if (text_readiness.get("all_declared_members_scanned") is not True
            or text_readiness.get("candidate_source_linkage_unverified_rows") != 0):
        raise ContractError("scoped readiness does not bind the complete linked source scan")

    overlap = technical.get("numeric_overlap_adjudication") or {}
    if (overlap.get("scope") != "CURRENT_RECIPE_ONLY"
            or overlap.get("numeric_expression_disjoint") is not False
            or overlap.get("current_group_conflicts") != 0
            or overlap.get("current_normalized_question_conflicts") != 0
            or overlap.get("splits_changed") != 0
            or overlap.get("source_chat_payload_bytes_changed") != 0
            or overlap.get("new_human_signoffs") != 0
            or overlap.get("protected_unread_or_global_eval_independence") != "NOT_CLAIMED"):
        raise ContractError("numeric-overlap exception policy or its scope changed")
    issue_kinds = Counter(item.get("kind") for item in technical.get("exact_issue_rows_preserved", []))
    if issue_kinds != Counter({"CROSS_SPLIT_CANONICAL": 36, "SOURCE_SPLIT_MISSING_OR_UNKNOWN": 1}):
        raise ContractError("the 37 raw findings are missing or changed")
    excluded = technical.get("diagnostic_exclusion") or {}
    if (excluded.get("sample_id") != REGRESSION_SAMPLE_ID
            or excluded.get("linked_chat_rows") != 0
            or excluded.get("raw_sha256") != excluded.get("canonical_sha256")):
        raise ContractError("zero-chat regression exclusion is missing or changed")
    if recipe.get("pending_discovery"):
        raise ContractError("recipe has pending member discovery")
    members = recipe.get("chat_members")
    sources = recipe.get("source_members")
    if (not isinstance(members, list) or len(members) != 32
            or not isinstance(sources, list) or len(sources) != 219):
        raise ContractError("recipe members do not match the full 32-chat/219-source release")
    if (recipe.get("declared_candidate_chat_rows") != EXPECTED_ROWS["train"]
            or recipe.get("current_pedagogy_validation_test_rows_separate") != 48):
        raise ContractError("recipe row totals or evaluation separation changed")

    report = {
        "status": "CURRENT_TEXT_RELEASE_EVIDENCE_VALIDATED",
        "scope": "CURRENT_RECIPE_ONLY_FULL_TEXT_TRAINING_INPUT",
        "recipe_sha256": recipe_sha,
        "recipe_identity": RECIPE_IDENTITY,
        "expected_rows_by_split": dict(EXPECTED_ROWS),
        "max_sequence_tokens": MAX_SEQUENCE_TOKENS,
        "observed_release_max_sequence_tokens": OBSERVED_RELEASE_MAX_SEQUENCE_TOKENS,
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "text_training_dataset_ready": True,
        "global_training_dataset_ready": manifest.get("TRAINING_DATASET_READY"),
        "all_rows_semantically_human_reviewed": manifest.get("all_rows_semantically_human_reviewed"),
        "numeric_expression_disjoint": False,
        "raw_current_recipe_findings_preserved": {"CROSS_SPLIT_CANONICAL": 36,
                                                   "SOURCE_SPLIT_MISSING_OR_UNKNOWN": 1},
        "regression_only_sample_excluded_with_zero_linked_chat_rows": True,
        "test_split_reserved_from_training": True,
        "training_started": False,
    }
    return ValidatedRelease(recipe=recipe, report=report)


def training_config() -> dict[str, Any]:
    """Return pinned text-only settings; there is no sample/subset limit."""
    return {
        "model_id": MODEL_ID,
        "revision": MODEL_REVISION,
        "max_length": MAX_SEQUENCE_TOKENS,
        "truncate": False,
        "rows_by_split": dict(EXPECTED_ROWS),
        "train_scope": "all current text candidates",
        "validation_scope": "all 24 validation rows",
        "test_scope": "reserved; not used by optimizer or model selection",
        "subset_limit": None,
    }


def make_split_streams(release: ValidatedRelease, paths: Mapping[str, str]) -> dict[str, CandidateStream]:
    """Create separate, explicit streams; no subset or row limit is exposed."""
    return {
        split: CandidateStream(release.recipe, paths, split)
        for split in ("train", "validation", "test")
    }


def iter_assistant_only_batches(
    stream: CandidateStream,
    tokenizer: Any,
    *,
    batch_size: int,
) -> Iterator[dict[str, Any]]:
    """Yield complete, untruncated split batches; final batch carries a receipt.

    A caller must consume through ``complete=True``. Validation can be passed to
    evaluation; test batches should remain sealed until a separate final eval.
    """
    split = stream.split
    if split not in EXPECTED_ROWS:
        raise ContractError("stream must name train, validation, or test explicitly")
    if not isinstance(batch_size, int) or batch_size <= 0:
        raise ContractError("batch_size must be a positive integer")
    expected = EXPECTED_ROWS[split]
    pending = []
    last_batch = None
    seen = 0
    for encoded, _cursor in tokenized_stream(stream, tokenizer,
                                             max_sequence_tokens=MAX_SEQUENCE_TOKENS):
        seen += 1
        if seen > expected:
            raise ContractError(f"{split} stream exceeded {expected} rows")
        if encoded.get("split") != split:
            raise ContractError("stream yielded a row from another split")
        if encoded.get("sample_id") == REGRESSION_SAMPLE_ID:
            raise ContractError("regression-only zero-chat diagnostic entered a chat split")
        if len(encoded["input_ids"]) > MAX_SEQUENCE_TOKENS:
            raise ContractError("tokenizer output exceeds the fixed sequence limit")
        if len(encoded["input_ids"]) != len(encoded["labels"]):
            raise ContractError("assistant-only labels do not align with input tokens")
        if not any(label != -100 for label in encoded["labels"]):
            raise ContractError("row has no assistant-only supervised tokens")
        pending.append(encoded)
        if len(pending) == batch_size:
            if last_batch is not None:
                yield last_batch
            last_batch = {"split": split, "data": pad_batch(pending), "rows_seen": seen,
                          "expected_rows": expected, "complete": False}
            pending = []
    if pending:
        if last_batch is not None:
            yield last_batch
        last_batch = {"split": split, "data": pad_batch(pending), "rows_seen": seen,
                      "expected_rows": expected, "complete": False}
    if seen != expected:
        raise ContractError(f"{split} stream ended at {seen} rows; expected {expected}")
    if last_batch is not None:
        last_batch["complete"] = True
        yield last_batch


def require_complete_batch_receipt(batch: Mapping[str, Any], split: str) -> None:
    """Fail closed unless the final full-split batch marker was observed."""
    if (batch.get("split") != split or batch.get("complete") is not True
            or batch.get("rows_seen") != EXPECTED_ROWS.get(split)):
        raise ContractError(f"missing complete {split} batch receipt")
