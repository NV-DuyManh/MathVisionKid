"""Prepare four conservative closeout controls from verified offline exports.

This module performs local validation and file preparation only. It has no
Drive, Colab, corpus, SQLite, or training access. Publication is a separate,
explicit operation through cloud_control_transaction.publish_controls.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import zipfile
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parent
PREFIX = "crosssplit_final_closeout_20261023/"
KINDS = ("progress", "chat", "context", "state")
CONTROL_IDS = {
    "progress": "1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX",
    "chat": "1tkSQoAlxXXRUg2AwYfvqsFKVEmM_LmR6",
    "context": "13gdIPQTFKcekoQQtgo0TXc7RgeadzIN9",
    "state": "1TLoQIbrRVmgsg-2uiUujCfM3HrK62Yme",
}
RECIPE_SHA256 = "1bb69c394c7eaaea7034125c6b3361eebbbe0d77e0715a8454331fbe7cee3ff8"
IDENTITY = "6faccfa8b6cae5ae100cdd4777c3481b6d193cb79acae2679086ec8e25718f56"
TECHNICAL_STATUS = "CURRENT_RECIPE_ONLY_TECHNICAL_PASS_WITH_HASH_BOUND_NUMERIC_OVERLAP_AND_REGRESSION_EXCLUSION"
REGRESSION_ID = "exhaustive_v1_div_1563_43"
REGRESSION_SHA256 = "1729ed713dfedcc0205b130c6573313dcc5784c7eaf5618d0cf32fdc728cf26b"
EXPECTED_ISSUES = {"CROSS_SPLIT_CANONICAL": 36, "SOURCE_SPLIT_MISSING_OR_UNKNOWN": 1}
SPLITS = {"train": 6_502_344, "validation": 24, "test": 24}
MAX_EVIDENCE_BYTES = 32 * 1024 * 1024
MAX_TOTAL_EVIDENCE_BYTES = 32 * 1024 * 1024


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _atomic(path: Path, data: bytes) -> None:
    temp = path.with_suffix(path.suffix + ".writing")
    temp.write_bytes(data)
    os.replace(temp, path)


def _check_pin(ref: Mapping[str, Any], kind: str, *, raw: bool = False) -> bytes:
    if ref.get("id") != CONTROL_IDS[kind] or type(ref.get("bytes")) is not int:
        raise ValueError(f"{kind} control ID/byte pin is invalid")
    path = Path(ref["path"]).expanduser().resolve(strict=True)
    data = path.read_bytes()
    if len(data) != ref["bytes"] or _sha(data) != ref.get("sha256"):
        raise ValueError(f"{kind} control differs from its supplied byte/hash pin")
    if raw and ref.get("fresh_raw_readback_verified") is not True:
        raise ValueError(f"{kind} parent lacks a fresh raw-readback proof")
    if len(data) > MAX_EVIDENCE_BYTES:
        raise ValueError(f"{kind} control exceeds the local size bound")
    return data


def _validate_child_checkpoint(parentcp: Mapping[str, Any], childcp: Mapping[str, Any]) -> None:
    if parentcp.get("id") != "16Q9ft9xhcioconk-5zpxmdRv1ZDNxqFI":
        raise ValueError("parent checkpoint must be the original audit checkpoint")
    if (parentcp.get('fresh_raw_readback_verified') is not True
            or parentcp.get('bytes') != 9128976384
            or parentcp.get('sha256') != '586904f37ad439e6c5ab5e00c5ccf5e494cccf8d7def09f4d4db9e9dba697fee'):
        raise ValueError('parent checkpoint must retain its exact completed raw-readback pin')
    if (childcp.get("fresh_raw_readback_verified") is not True
            or not isinstance(childcp.get("id"), str) or not childcp["id"]
            or childcp.get("id") == parentcp.get("id")
            or type(childcp.get("bytes")) is not int or childcp["bytes"] <= 0
            or not isinstance(childcp.get("sha256"), str)
            or len(childcp["sha256"]) != 64
            or any(c not in "0123456789abcdef" for c in childcp["sha256"])):
        raise ValueError("child checkpoint must have a dynamic ID and fresh raw-readback proof")


def _assert_conservative(report: Mapping[str, Any], technical: Mapping[str, Any]) -> None:
    for obj in (report, technical):
        if (obj.get("TRAINING_DATASET_READY") is not False
                or obj.get("training_started") is True
                or obj.get("whole_curriculum_certified") is True
                or obj.get("all_rows_semantically_human_reviewed") is True):
            raise ValueError("readiness, training, certification, and human-review claims must remain false")


def _assert_old_zip_preserved(old_path: Path, new_path: Path) -> None:
    with zipfile.ZipFile(old_path) as oldzip, zipfile.ZipFile(new_path) as newzip:
        old_names, new_names = oldzip.namelist(), newzip.namelist()
        if len(old_names) != len(set(old_names)) or len(new_names) != len(set(new_names)):
            raise ValueError("progress ZIP contains duplicate member names")
        if new_names[:len(old_names)] != old_names:
            raise ValueError("prepared progress ZIP changed old member order or removed members")
        if any(oldzip.read(name) != newzip.read(name) for name in old_names):
            raise ValueError("an old PROGRESS member changed")


def _validate_actual(final_runtime: Mapping[str, Any], technical: Mapping[str, Any],
                     antijoin: Mapping[str, Any], parentcp: Mapping[str, Any],
                     childcp: Mapping[str, Any]) -> dict[str, Any]:
    _validate_child_checkpoint(parentcp, childcp)
    report = final_runtime.get("report")
    if not isinstance(report, dict) or final_runtime.get("worker_alive") is not False:
        raise ValueError("final stopped runtime observation/report is required")
    if final_runtime.get("final_metadata_alive") is not False:
        raise ValueError("metadata finalizer must be stopped before preparation")
    if final_runtime.get("checkpoint") != childcp:
        raise ValueError("runtime checkpoint differs from fresh child checkpoint proof")
    if childcp.get("report_at_snapshot") != report:
        raise ValueError("child checkpoint report snapshot differs from final raw report")
    if report.get("identity") != IDENTITY or report.get("issues") != EXPECTED_ISSUES:
        raise ValueError("final report recipe identity or retained 37-finding aggregate differs")
    if (report.get("members_expected") != 251 or report.get("members_complete") != 251
            or report.get("source_versions_indexed") != 1_629_906
            or report.get("unique_chat_rows_processed") != 6_502_392
            or report.get("physical_chat_occurrences_processed") != 6_502_392
            or report.get("actual_rows_by_split") != SPLITS
            or report.get("full_archive_token_linkage_split_audit_complete") is not False):
        raise ValueError("final report is incomplete or changes the raw scan outcome")
    if (report.get('all_declared_members_scanned') is not True
            or report.get('source_linkage_unverified_rows') != 0
            or report.get('incomplete_four_mode_cases') != 0
            or report.get('exact_duplicate_references') != 0
            or report.get('source_hash_origins', {}).get('STRUCTURAL15_RAW_CANONICAL_AND_CHAT_HASH_VERIFIED') != 60):
        raise ValueError('final exact60 linkage, modes, or full-ledger verification is incomplete')
    if (report.get("TRAINING_DATASET_READY") is not False
            or report.get("training_started") is not False
            or report.get("whole_curriculum_certified") is not False
            or report.get("all_rows_semantically_human_reviewed") is not False):
        raise ValueError("raw report must retain all conservative false flags")
    _assert_conservative(report, technical)
    if (technical.get("status") != TECHNICAL_STATUS
            or technical.get("raw_report_preserved") != report
            or technical.get("TRAINING_DATASET_READY") is not False
            or technical.get("physical_curriculum_pending") is not True):
        raise ValueError("technical adjudication must preserve raw report and exact current-recipe-only status")
    overlap = technical.get("numeric_overlap_adjudication", {})
    if (overlap.get("scope") != "CURRENT_RECIPE_ONLY"
            or overlap.get("numeric_expression_disjoint") is not False
            or overlap.get("current_normalized_question_conflicts") != 0
            or overlap.get("current_group_conflicts") != 0):
        raise ValueError("numeric-overlap adjudication scope or findings differ")
    issue_rows = technical.get("exact_issue_rows_preserved")
    if not isinstance(issue_rows, list) or len(issue_rows) != 37:
        raise ValueError("technical adjudication must preserve all 37 raw finding rows")
    reg = technical.get("diagnostic_exclusion", {})
    if (reg.get("sample_id") != REGRESSION_ID or reg.get("raw_sha256") != REGRESSION_SHA256
            or reg.get("canonical_sha256") != REGRESSION_SHA256 or reg.get("linked_chat_rows") != 0):
        raise ValueError("zero-link regression diagnostic is not pinned")
    if antijoin.get("read_only") is not True or not isinstance(antijoin.get("counts"), dict):
        raise ValueError("read-only source/chat anti-join evidence is required")
    # The immutable anti-join report has no readiness fields; missing fields are
    # not fabricated as false claims. Validate its actual read-only schema and
    # finite classifications while readiness is asserted on report/technical.
    if (antijoin.get('schema') != 'source_chat_antijoin_classification.v1'
            or antijoin.get('payload_or_question_content_read') is not False
            or antijoin['counts'].get('unlinked_source_versions') != 4308
            or antijoin['counts'].get('classifications', {}).get('UNRESOLVED_QUARANTINE', 0) != 0
            or antijoin.get('TRAINING_DATASET_READY') is True
            or antijoin.get('training_started') is True):
        raise ValueError('anti-join schema, classifications, or read-only limits differ')
    return report


def prepare_controls(parent_refs: Mapping[str, Mapping[str, Any]], metadata_dir: str | os.PathLike[str],
                     evidence_paths: Mapping[str, str | os.PathLike[str]], outputdir: str | os.PathLike[str],
                     final_runtime: Mapping[str, Any], technical: Mapping[str, Any],
                     antijoin: Mapping[str, Any], parentcp: Mapping[str, Any],
                     childcp: Mapping[str, Any]) -> dict[str, Any]:
    """Create local progress/chat/context/state files from already exported evidence.

    ``parent_refs`` maps control kind to {id, bytes, sha256, path,
    fresh_raw_readback_verified}. ``evidence_paths`` maps safe relative archive
    names to local evidence paths. No network access or remote writes occur.
    """
    if set(parent_refs) != set(KINDS):
        raise ValueError("exactly four parent control refs are required")
    if len({parent_refs[k]["id"] for k in KINDS}) != 4:
        raise ValueError("parent control IDs must be distinct")
    raw = {k: _check_pin(parent_refs[k], k, raw=True) for k in KINDS}
    state, chat = json.loads(raw["state"]), json.loads(raw["chat"])
    if (state.get("latest_all_data_union_recipe", {}).get("sha256") != RECIPE_SHA256
            or state.get("accepted_cases") != 1_629_922
            or state.get("training_chat_rows") != 6_502_344
            or state.get("TRAINING_DATASET_READY") is not False
            or state.get("training_started") is not False):
        raise ValueError("historical state/recipe pins or readiness guards changed")
    if state.get("pending_checkpoint_append") is not None:
        raise ValueError("pending checkpoint append must be resolved before closeout")
    report = _validate_actual(final_runtime, technical, antijoin, parentcp, childcp)

    metadata_root = Path(metadata_dir).expanduser().resolve(strict=True)
    if not metadata_root.is_dir():
        raise ValueError("metadata_dir must be an existing local directory")
    out = Path(outputdir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    output_names = {k: out / f"next_{k}{'.zip' if k == 'progress' else '.md' if k == 'context' else '.json'}" for k in KINDS}
    manifest_path = out / "prepared_control_updates.json"
    if any(p.exists() for p in [*output_names.values(), manifest_path]):
        raise FileExistsError("prepared output exists; use a clean output directory")

    old_context = raw["context"]
    marker = "### Nhật ký 23/10/2026 — closeout audit cross-split current recipe"
    if marker.encode() in old_context:
        raise ValueError("context already contains the closeout marker")
    parent_cp = deepcopy(parentcp)
    child = deepcopy(childcp)
    old_runtime = deepcopy(state.get("latest_colab_runtime_observation", {}))
    latest = dict(old_runtime, observed_utc=final_runtime.get("observed_utc"),
                  worker_alive_at_observation=False, runtime_status="AUDIT_FINISHED_WITH_FINDINGS",
                  checkpoint=child, source_versions_indexed=1_629_906,
                  unique_chat_rows_committed=6_502_392, committed_physical_chat_rows=6_502_392,
                  last_verified_checkpoint_unique_chat_rows=6_502_392,
                  live_report=report, current_issues=report["issues"],
                  full_archive_audit_complete=False, TRAINING_DATASET_READY=False,
                  training_started=False, evidence_member=PREFIX + "final_runtime_observation.json")
    # The old observation is archived below; stale intermediate batch counters
    # must not be presented as current final-snapshot evidence.
    latest.pop("batch_adapter_stats", None)
    latest.update(report=report, worker_alive=False, final_metadata_alive=False,
                  structural15_repair_alive=False, structural15_repair2_alive=False)
    for obj in (state, chat):
        obj.setdefault("parent_checkpoint_history", []).append(parent_cp)
        obj.setdefault("data_only_colab_observation_history", []).append(deepcopy(obj.get("latest_colab_runtime_observation", {})))
        obj["latest_colab_runtime_observation"] = deepcopy(latest)
        obj.setdefault("verified_v3_checkpoint_history", []).append(deepcopy(obj.get("latest_verified_v3_checkpoint", {})))
        obj["latest_verified_v3_checkpoint"] = child
        if "pending_structural15_adapter" in obj:
            obj.setdefault("structural15_adapter_preparation_history", []).append(
                deepcopy(obj["pending_structural15_adapter"]))
        obj["pending_structural15_adapter"] = {
            "status": "EXACT_ORIGINAL60_REAUDITED_IN_SEPARATE_CHILD_CHECKPOINT",
            "source_cases": 15, "chat_rows": 60,
            "source_chat_payload_bytes_changed": 0, "new_human_signoffs": 0,
            "child_checkpoint": child,
            "raw_numeric_overlap_findings_preserved": 36,
            "held_two_field_artifact": "1DtwpVgFAiyyOIHxgFbQgnlDGWr75m6DQ",
            "held_artifact_status": "NOT_SELECTED_DO_NOT_MERGE_GROUP_POLICY_WOULD_CHANGE",
        }
        obj["latest_current_text_closeout"] = {
            "status": TECHNICAL_STATUS, "checkpoint": child,
            "recipe_identity": IDENTITY, "recipe_sha256": RECIPE_SHA256,
            "issues": report["issues"], "exact_raw_finding_count": 37,
            "numeric_expression_disjoint": False, "scope": "CURRENT_RECIPE_ONLY",
            "unique_chat_rows": 6_502_392, "candidate_chat_rows": 6_502_344,
            "source_versions_indexed": 1_629_906,
            "historical_accepted_cases": 1_629_922,
            "historical_training_chat_rows": 6_502_344,
            "historical_source_counter_difference": 16,
            "actual_case_counts_by_split": {"train": 1_625_586, "validation": 6, "test": 6},
            "evaluation_chat_rows": {"validation": 24, "test": 24},
            "physical_observation_tasks_pending": 5, "constraints_pending": 7,
            "asset_masters_pending": 10, "g3_source_locator_pending": 1,
            "human_signoffs_created": 0,
            "TRAINING_DATASET_READY": False, "training_started": False,
            "whole_curriculum_certified": False, "all_rows_semantically_human_reviewed": False,
        }
        obj["TRAINING_DATASET_READY"] = False
        obj["training_started"] = False
        obj["full_archive_audit_complete"] = False
    state["latest_colab_runtime_observation"] = latest
    state["updated_utc"] = datetime.now(timezone.utc).isoformat()
    state["status"] = "CURRENT_TEXT_TECHNICAL_AUDIT_WITH_NUMERIC_OVERLAP_PHYSICAL_IMAGE_SOURCE_PENDING"
    state["next_action"] = (
        "Preserve the 37 raw V3 findings and the current-recipe-only numeric overlap adjudication. "
        "numeric_expression_disjoint=false; do not claim overall READY, human review, or curriculum certification. "
        "Continue 5 physical observation tasks, 7 constraints, 10 asset masters, and 1 G3 locator. "
        "Keep the historical accepted/source discrepancy of 16 unresolved; do not train or create data."
    )

    anti_counts = json.dumps(antijoin["counts"], ensure_ascii=False, sort_keys=True)
    delta = (f"\n\n{marker}\n"
             f"Current recipe audit checkpoint {child['id']} was independently raw-readback verified ({child['bytes']} bytes, SHA256 {child['sha256']}). "
             "Recipe SHA256 remains 1bb69c394c7eaaea7034125c6b3361eebbbe0d77e0715a8454331fbe7cee3ff8; all 251 members, 1,629,906 source versions, and 6,502,392 unique/physical chat rows were scanned. "
             "Train contains 6,502,344 chat rows; validation and test each contain 24. Raw V3 findings are retained in full (36 CROSS_SPLIT_CANONICAL plus one regression_only SOURCE_SPLIT_MISSING_OR_UNKNOWN), and its whole-audit completion flag remains false. "
             f"Technical status is {TECHNICAL_STATUS}; numeric overlap scope is CURRENT_RECIPE_ONLY, with numeric_expression_disjoint=false, zero current normalized-question/group conflicts, and no global or protected unread/evaluation independence claim. "
             f"Read-only anti-join counts are preserved: {anti_counts}. No source/chat bytes, splits, or dataset rows were changed; no cases or chat rows were added. "
             "Historical accepted_cases=1,629,922 remains preserved against 1,629,906 indexed sources (difference 16 unresolved); training_chat_rows=6,502,344 remains preserved. "
             "All 299 human signoffs remain frozen; no signoffs were added. Keep 5 physical observation tasks, 7 constraints, 10 asset masters, and 1 G3 locator pending. "
             "TRAINING_DATASET_READY=false, training_started=false, whole_curriculum_certified=false, all_rows_semantically_human_reviewed=false.\n")
    pending_journals = [source for rel, source in evidence_paths.items()
                        if PurePosixPath(rel).name == 'local_context_pending_delta.md']
    if len(pending_journals) > 1:
        raise ValueError('ambiguous pending local context journal')
    pending_bytes = b''
    if pending_journals:
        pending_path = Path(pending_journals[0])
        if not pending_path.is_absolute():
            pending_path = metadata_root / pending_path
        pending_bytes = pending_path.read_bytes()
        if len(pending_bytes) > 128 * 1024:
            raise ValueError('pending local context journal exceeds bounded metadata scope')
        pending_bytes.decode('utf-8')
        if pending_bytes in old_context:
            pending_bytes = b''
    context = old_context + pending_bytes + delta.encode("utf-8")

    # Evidence archive accepts only bounded metadata/source-code note files.
    additions: dict[str, bytes] = {}
    for rel, source in evidence_paths.items():
        p = PurePosixPath(rel)
        if p.is_absolute() or ".." in p.parts or not p.parts or p.suffix.lower() not in {".py", ".json", ".md"}:
            raise ValueError(f"unsafe evidence archive path: {rel}")
        member = PREFIX + p.as_posix()
        if member in additions:
            raise ValueError("duplicate closeout evidence path")
        source_path = Path(source).expanduser()
        if not source_path.is_absolute():
            source_path = metadata_root / source_path
        data = source_path.resolve(strict=True).read_bytes()
        if len(data) > MAX_EVIDENCE_BYTES:
            raise ValueError(f"evidence file exceeds bounded size: {rel}")
        additions[member] = data
    if sum(map(len, additions.values())) > MAX_TOTAL_EVIDENCE_BYTES:
        raise ValueError("closeout evidence exceeds total bounded size")
    with zipfile.ZipFile(parent_refs["progress"]["path"]) as oldzip:
        old_names = oldzip.namelist()
        if len(old_names) != len(set(old_names)):
            raise ValueError("parent PROGRESS contains duplicate members")
        old_members = {name: oldzip.read(name) for name in old_names}
    if set(additions) & set(old_members):
        raise ValueError("PROGRESS already contains one or more closeout evidence members")

    # Use an intermediate archive outside output_names, then atomically place it.
    tmp_zip = out / ".next_progress.zip.writing"
    with zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in old_members.items():
            archive.writestr(name, data)
        for name, data in additions.items():
            archive.writestr(name, data)
    with zipfile.ZipFile(tmp_zip) as check:
        if check.namelist()[:len(old_names)] != old_names or len(check.namelist()) != len(set(check.namelist())):
            raise ValueError("prepared PROGRESS member order/uniqueness changed")
        if any(check.read(n) != d for n, d in old_members.items()):
            raise ValueError("an old PROGRESS member changed")
        if any(check.read(n) != d for n, d in additions.items()):
            raise ValueError("new evidence bytes differ")
    _assert_old_zip_preserved(Path(parent_refs["progress"]["path"]), tmp_zip)
    os.replace(tmp_zip, output_names["progress"])
    _atomic(output_names["chat"], _json_bytes(chat))
    _atomic(output_names["context"], context)
    # STATE is emitted last, after all other prepared controls have been written.
    _atomic(output_names["state"], _json_bytes(state))
    controls = {}
    for kind, path in output_names.items():
        data = path.read_bytes()
        controls[kind] = {"id": CONTROL_IDS[kind], "path": str(path), "bytes": len(data), "sha256": _sha(data)}
    prepared = {"controls": controls, "state_must_be_written_last": True,
                "parent_controls_raw_readback_verified": True,
                "old_progress_members_byte_identical": True,
                "raw_finding_rows_preserved": 37, "new_cases": 0, "new_chat_rows": 0,
                "TRAINING_DATASET_READY": False, "training_started": False,
                "remote_publication_performed": False}
    _atomic(manifest_path, _json_bytes(prepared))
    return prepared


if __name__ == "__main__":
    raise SystemExit("Import prepare_controls and pass verified local evidence; this script does not probe or publish remotely.")
