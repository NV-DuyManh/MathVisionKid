"""Prepare (but never publish) final current-text audit controls.

This script consumes bounded phase evidence already exported from Colab. It
does not connect to Drive, download corpus data, create examples, or train.
The caller reviews the four prepared controls before any remote publication.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parent
PREFIX = "final_current_text_closeout_20261023/"
IDENTITY = "f0332df91020ace0fc48d88491fe97364d08826458d08c71ba4ec60524e25863"
RECIPE_SHA256 = "1bb69c394c7eaaea7034125c6b3361eebbbe0d77e0715a8454331fbe7cee3ff8"
CHECKPOINT_ID = "16Q9ft9xhcioconk-5zpxmdRv1ZDNxqFI"
PAUSED_CHECKPOINT_SHA256 = "3c7cb05061c0040812111a6bb73a0709cc59a244493dc135a3b95aa389bf0648"
PAUSED_CHECKPOINT_BYTES = 7_083_466_752
REGRESSION_ID = "exhaustive_v1_div_1563_43"
REGRESSION_MEMBER = "79765b8281ff64675b4e3826c07b003237875a98d67e898f22f2a4c1f687b0d1"
REGRESSION_SHA256 = "1729ed713dfedcc0205b130c6573313dcc5784c7eaf5618d0cf32fdc728cf26b"
PASS_STATUS = "CURRENT_CANDIDATE_CHAT_TECHNICAL_PASS_WITH_HASH_BOUND_DIAGNOSTIC_EXCLUSION"
FINALIZER_STATUS = "FINAL_TEXT_TECHNICAL_EVIDENCE_COMPLETE_PENDING_CONTROL_PUBLICATION"
CONTROL_IDS = {
    "progress": "1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX",
    "chat": "1tkSQoAlxXXRUg2AwYfvqsFKVEmM_LmR6",
    "context": "13gdIPQTFKcekoQQtgo0TXc7RgeadzIN9",
    "state": "1TLoQIbrRVmgsg-2uiUujCfM3HrK62Yme",
}
MAX_JSON_BYTES = 24 * 1024 * 1024
MAX_EVIDENCE_BYTES = 32 * 1024 * 1024


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_bytes(name: str, maximum: int = MAX_JSON_BYTES) -> bytes:
    path = ROOT / name
    data = path.read_bytes()
    if len(data) > maximum:
        raise ValueError(f"{name} exceeds the bounded {maximum}-byte input limit")
    return data


def decode_export(value):
    """Unwrap common Colab/MCP output envelopes, then parse their JSON text."""
    for _ in range(5):
        if isinstance(value, dict) and "outputs" in value and isinstance(value["outputs"], list):
            streams = []
            for item in value["outputs"]:
                if not isinstance(item, dict):
                    continue
                for text in item.get("text", []) if isinstance(item.get("text"), list) else [item.get("text", "")]:
                    if isinstance(text, str):
                        streams.append(text)
            candidates = [s for s in streams if s.lstrip().startswith(("{", "["))]
            if not candidates:
                raise ValueError("export envelope contains no JSON output")
            value = json.loads(candidates[-1])
        elif isinstance(value, str):
            value = json.loads(value)
        else:
            return value
    raise ValueError("too many nested export wrappers")


def load_json(name: str):
    return decode_export(json.loads(load_bytes(name).decode("utf-8")))


def write_atomic(name: str, data: bytes) -> dict:
    path = ROOT / name
    temp = path.with_suffix(path.suffix + ".writing")
    temp.write_bytes(data)
    os.replace(temp, path)
    return {"name": name, "bytes": len(data), "sha256": digest(data)}


def save_json(name: str, value) -> dict:
    data = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    return write_atomic(name, data)


def validate_parent_controls() -> tuple[dict, dict, dict, bytes]:
    expected = load_json("parent_controls_raw_verified.json")
    if not isinstance(expected, list):
        raise ValueError("parent_controls_raw_verified.json must be a list of raw-readback proofs")
    proofs = {x.get("kind"): x for x in expected if isinstance(x, dict)}
    if set(proofs) != set(CONTROL_IDS):
        raise ValueError("fresh raw-readback proofs for all four parent controls are required")
    actual = {}
    for kind, filename in (("progress", "parent_progress.zip"), ("state", "parent_state.json"),
                           ("chat", "parent_chat.json"), ("context", "parent_context.md")):
        proof = proofs[kind]
        if proof.get("id") != CONTROL_IDS[kind] or proof.get("fresh_raw_readback_verified") is not True:
            raise ValueError(f"{kind} parent control lacks the expected ID/fresh raw readback")
        data = load_bytes(filename, MAX_EVIDENCE_BYTES)
        if len(data) != proof.get("bytes") or digest(data) != proof.get("sha256"):
            raise ValueError(f"{kind} parent control differs from its fresh raw-readback proof")
        actual[kind] = data
    state = json.loads(actual["state"])
    chat = json.loads(actual["chat"])
    with zipfile.ZipFile(ROOT / "parent_progress.zip") as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("parent PROGRESS contains duplicate member names")
        old_members = {name: archive.read(name) for name in names}
    if state.get("latest_all_data_union_recipe", {}).get("sha256") != RECIPE_SHA256:
        raise ValueError("parent STATE no longer points to the exact current recipe")
    if state.get("accepted_cases") != 1_629_922 or state.get("training_chat_rows") != 6_502_344:
        raise ValueError("historical STATE counters changed; preserve and review before proceeding")
    if state.get("pending_checkpoint_append") is not None:
        raise ValueError("pending checkpoint append remains; do not prepare closeout controls")
    plan = state.get("latest_g2_finite_preparation_plan", {})
    sgk = state.get("latest_sgk_accepted_reconciliation", {}).get("counts", {})
    if (plan.get("finite_tasks_pending") != 5 or plan.get("candidate_constraints_pending") != 7
            or sgk.get("asset_only_masters_separate") != 10 or sgk.get("source_locator_only_tasks") != 1):
        raise ValueError("historical physical/constraint/asset/locator work counters changed")
    return state, chat, proofs, actual["context"]


def validate_final_evidence(state: dict) -> tuple[dict, dict, dict, dict, dict, dict]:
    runtime = load_json("final_runtime_observation.json")
    status = load_json("final_metadata_status.json")
    technical = load_json("final_candidate_chat_technical_adjudication.json")
    manifest = load_json("final_current_text_candidate_manifest.json")
    antijoin = load_json("final_source_chat_antijoin.json")
    raw_export = load_json("final_raw_v3_report_preserved.json")

    if runtime.get("worker_alive") is not False or runtime.get("final_metadata_alive") is not False:
        raise ValueError("scanner and finalizer must both be stopped before preparing controls")
    if runtime.get("worker_state") != "AUDIT_FINISHED_WITH_FINDINGS":
        raise ValueError("the original scanner did not finish with its preserved finding")
    if status.get("state") != FINALIZER_STATUS:
        raise ValueError("finalizer did not reach the expected technical-evidence-complete state")
    if status.get("recipe_identity") != IDENTITY or status.get("recipe_sha256") != RECIPE_SHA256:
        raise ValueError("finalizer status is bound to another recipe")
    if status.get("training_started") is not False or status.get("new_cases") != 0 or status.get("new_chat_rows") != 0:
        raise ValueError("finalizer status indicates training or data generation")

    checkpoint = runtime.get("checkpoint")
    report = runtime.get("report")
    if not isinstance(checkpoint, dict) or not isinstance(report, dict):
        raise ValueError("runtime observation lacks final checkpoint/report objects")
    checkpoint_sha = checkpoint.get("sha256")
    checkpoint_bytes = checkpoint.get("bytes")
    if (checkpoint.get("id") != CHECKPOINT_ID or type(checkpoint_bytes) is not int or checkpoint_bytes <= 0
            or not isinstance(checkpoint_sha, str) or len(checkpoint_sha) != 64
            or any(c not in "0123456789abcdef" for c in checkpoint_sha)
            or checkpoint.get("fresh_raw_readback_verified") is not True):
        raise ValueError("final checkpoint is not the required fresh raw-readback proof")
    if checkpoint_sha == PAUSED_CHECKPOINT_SHA256 or checkpoint_bytes == PAUSED_CHECKPOINT_BYTES:
        raise ValueError("final checkpoint still matches the earlier partial owner-pause snapshot")
    if status.get("checkpoint") != checkpoint or manifest.get("checkpoint") != checkpoint:
        raise ValueError("runtime, finalizer status, and manifest checkpoint proofs differ")
    if checkpoint.get("report_at_snapshot") != report or raw_export != report:
        raise ValueError("final raw report differs from checkpoint/runtime/export evidence")
    if (report.get("identity") != IDENTITY or report.get("full_archive_token_linkage_split_audit_complete") is not False
            or report.get("TRAINING_DATASET_READY") is not False
            or report.get("all_rows_semantically_human_reviewed") is not False
            or report.get("whole_curriculum_certified") is not False
            or report.get("training_started") is not False):
        raise ValueError("raw report identity or conservative readiness flags changed")
    expected_report = {
        "members_expected": 251, "members_complete": 251,
        "all_declared_members_scanned": True, "source_versions_indexed": 1_629_906,
        "unique_chat_rows_processed": 6_502_392, "physical_chat_occurrences_processed": 6_502_392,
        "exact_duplicate_references": 0, "source_linkage_unverified_rows": 0,
        "incomplete_four_mode_cases": 0,
        "issues": {"SOURCE_SPLIT_MISSING_OR_UNKNOWN": 1},
        "actual_rows_by_split": {"train": 6_502_344, "validation": 24, "test": 24},
    }
    if any(report.get(k) != v for k, v in expected_report.items()):
        raise ValueError("final raw report is partial or differs from the exact expected scan")
    if runtime.get("committed_physical_chat_rows") != 6_502_392:
        raise ValueError("runtime physical chat row count is incomplete")
    if runtime.get("unique_chat_rows_processed", report.get("unique_chat_rows_processed")) != 6_502_392:
        raise ValueError("runtime unique chat row count is incomplete")
    if runtime.get("members_complete", 251) != 251 or runtime.get("members_expected", 251) != 251:
        raise ValueError("runtime all-member completion counters are incomplete")
    if runtime.get("expected_raw_chat_rows", 6_502_392) != 6_502_392:
        raise ValueError("runtime expected raw chat row total changed")

    if technical.get("status") != PASS_STATUS:
        raise ValueError("technical adjudication lacks its exact hash-bound diagnostic status")
    if technical.get("TRAINING_DATASET_READY") is not False or technical.get("physical_curriculum_pending") is not True:
        raise ValueError("technical status improperly claims dataset readiness")
    if technical.get("raw_report_preserved") != report:
        raise ValueError("technical adjudication does not preserve the raw report verbatim")
    expected_issue = [{"member": REGRESSION_MEMBER, "line": 1,
                       "kind": "SOURCE_SPLIT_MISSING_OR_UNKNOWN", "detail": REGRESSION_ID}]
    if technical.get("exact_issue_rows_preserved") != expected_issue:
        raise ValueError("technical adjudication does not preserve the exact raw issue row")
    if technical.get("diagnostic_exclusion") != {
        "sample_id": REGRESSION_ID, "raw_sha256": REGRESSION_SHA256,
        "canonical_sha256": REGRESSION_SHA256, "linked_chat_rows": 0,
    }:
        raise ValueError("technical diagnostic exclusion is not hash-bound to the zero-link source")
    if technical.get("raw_report_artifact", {}).get("name") != "final_raw_v3_report_preserved.json":
        raise ValueError("technical adjudication raw-report artifact name differs")
    if technical.get("actual_cases_by_split") != {"train": 1_625_586, "validation": 6, "test": 6}:
        raise ValueError("technical adjudication case counts by split differ")
    if (manifest.get("schema") != "MathVisionKid.current_text_candidate_view_final_metadata.v1"
            or manifest.get("status") != "CURRENT_TEXT_CANDIDATE_VIEW_TECHNICALLY_VERIFIED"):
        raise ValueError("current-text manifest lacks the expected technical-only status")
    if (manifest.get("recipe_identity") != IDENTITY or manifest.get("recipe_sha256") != RECIPE_SHA256
            or manifest.get("candidate_chat_rows") != 6_502_344
            or manifest.get("candidate_case_ids") != 1_625_586
            or manifest.get("validation_chat_rows") != 24 or manifest.get("test_chat_rows") != 24
            or manifest.get("raw_chat_rows_all_current_splits") != 6_502_392
            or manifest.get("source_versions_retained") != 1_629_906
            or manifest.get("source_only_audit_rows_retained") != 4_308):
        raise ValueError("current-text manifest totals differ from the verified full scan")
    if (manifest.get("physical_observation_tasks_pending") != 5 or manifest.get("asset_masters_pending") != 10
            or manifest.get("g3_source_locator_pending") != 1
            or manifest.get("core_cases") != 495 or manifest.get("core_nodes") != 165
            or manifest.get("core_chat_rows") != 1_980
            or manifest.get("whole_curriculum_certified") is not False
            or manifest.get("all_rows_semantically_human_reviewed") is not False
            or manifest.get("TRAINING_DATASET_READY") is not False
            or manifest.get("training_started") is not False):
        raise ValueError("manifest closes physical/human acceptance gates or claims readiness")

    if antijoin.get("schema") != "source_chat_antijoin_classification.v1" or antijoin.get("read_only") is not True:
        raise ValueError("source/chat anti-join evidence has an unexpected schema")
    counts = antijoin.get("counts", {})
    classes = counts.get("classifications", {})
    unlinked = counts.get("unlinked_source_versions")
    if (unlinked != 4_308 or sum(classes.values()) != unlinked
            or manifest.get("source_only_audit_rows_retained") != unlinked):
        raise ValueError("source-only anti-join totals do not reconcile; preserve evidence and stop")
    # Preserve every returned bucket; ensure the completed finalizer obeyed its zero-unresolved guard.
    if classes.get("regression_only") != 1:
        raise ValueError("anti-join report does not preserve the sole regression-only source")
    if classes.get("UNRESOLVED_QUARANTINE", 0) != 0:
        raise ValueError("actual finalizer does not complete while unresolved quarantine rows remain")
    by_source_split = {}
    for item in antijoin.get("unlinked", []):
        split = item.get("source_split") or "<missing>"
        by_source_split[split] = by_source_split.get(split, 0) + 1
    if by_source_split != {"train_candidate": 4_307, "regression_only": 1}:
        raise ValueError("source-only split totals differ from 4,307 candidates plus the one diagnostic")
    if (status.get("manifest", {}).get("name") != "final_current_text_candidate_manifest.json"
            or status.get("manifest", {}).get("sha256") is None):
        raise ValueError("finalizer status lacks a hash-bound manifest reference")
    manifest_bytes = load_bytes("final_current_text_candidate_manifest.json")
    technical_bytes = load_bytes("final_candidate_chat_technical_adjudication.json")
    if (status["manifest"].get("sha256") != digest(manifest_bytes)
            or status["manifest"].get("bytes") != len(manifest_bytes)):
        raise ValueError("finalizer manifest reference hash does not match exported bytes")
    if (manifest.get("technical_adjudication", {}).get("sha256") != digest(technical_bytes)
            or manifest.get("technical_adjudication", {}).get("bytes") != len(technical_bytes)
            or manifest.get("technical_adjudication", {}).get("name") != "final_candidate_chat_technical_adjudication.json"):
        raise ValueError("manifest technical-adjudication reference does not match exported bytes")
    if (technical.get("raw_report_artifact", {}).get("sha256") != digest(load_bytes("final_raw_v3_report_preserved.json"))
            or technical.get("raw_report_artifact", {}).get("bytes") != len(load_bytes("final_raw_v3_report_preserved.json"))):
        raise ValueError("technical adjudication raw-report reference does not match exported bytes")
    if status.get("source_only_classifications") != antijoin.get("counts", {}).get("classifications"):
        raise ValueError("finalizer status anti-join buckets differ from exported report")

    pause = state.get("owner_requested_pause", {})
    if pause.get("checkpoint", {}).get("id") != CHECKPOINT_ID:
        raise ValueError("historical owner-pause checkpoint evidence is absent")
    if state.get("TRAINING_DATASET_READY") is not False or state.get("training_started") is not False:
        raise ValueError("parent STATE readiness/training guard changed")
    return runtime, status, technical, manifest, antijoin, report


def main() -> None:
    output_names = ["next_progress.zip", "next_chat.json", "next_context.md", "next_state.json", "prepared_control_updates.json"]
    if any((ROOT / name).exists() for name in output_names):
        raise FileExistsError("prepared output exists; inspect it and choose a clean phase directory")

    state, chat, parent_proofs, parent_context = validate_parent_controls()
    runtime, final_status, technical, manifest, antijoin, raw_report = validate_final_evidence(state)
    notebook = load_json("notebook_remote_verified.json")
    if notebook.get("fresh_raw_readback_verified") is not True or notebook.get("id") != "1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l":
        raise ValueError("notebook control lacks its exact fresh raw-readback proof")

    # Reopen the parent archive only after all inputs validate; retain every old byte.
    with zipfile.ZipFile(ROOT / "parent_progress.zip") as old:
        old_names = old.namelist()
        old_members = {name: old.read(name) for name in old_names}
    evidence_names = [
        "prepare_final_controls.py", "parent_controls_raw_verified.json", "notebook_remote_verified.json",
        "final_runtime_observation.json", "final_metadata_status.json",
        "final_candidate_chat_technical_adjudication.json", "final_current_text_candidate_manifest.json",
        "final_source_chat_antijoin.json", "final_raw_v3_report_preserved.json",
        "finalizer_setup.py", "finalize_current_candidate_metadata.py",
        "final_technical_adjudication.py", "final_source_chat_antijoin.py",
        "final_recipe_member_metadata.json",
        "final_antijoin_execution.json", "export_final_metadata.py",
        "source_index_ledger_check.py", "source_index_ledger_receipt.json",
        "runtime_read_cache.py", "read_cache_receipt.json",
        "status_report_cache.py", "test_status_report_cache.py",
        "status_report_cache_receipt.json", "status_report_cache_final_usage.json",
        "bounded_metadata_agent_review.json", "remaining_evidence_handoff.json", "prepare_notebook_savepoint.py",
        "notebook_prepared.json", "metadata_export_receipt.json",
    ]
    additions = {}
    for name in evidence_names:
        path = ROOT / name
        if not path.is_file():
            if name in evidence_names[:9]:
                raise FileNotFoundError(f"required evidence/code input is absent: {name}")
            continue
        data = load_bytes(name, MAX_EVIDENCE_BYTES)
        member = PREFIX + name
        if member in old_members:
            raise ValueError(f"PROGRESS already contains {member}; refusing a duplicate closeout")
        additions[member] = data
    if sum(map(len, additions.values())) > MAX_EVIDENCE_BYTES:
        raise ValueError("closeout evidence additions exceed the bounded total")

    checkpoint = runtime["checkpoint"]
    technical_ref = {"name": "final_candidate_chat_technical_adjudication.json",
                     "sha256": digest(load_bytes("final_candidate_chat_technical_adjudication.json"))}
    manifest_ref = {"name": "final_current_text_candidate_manifest.json",
                    "sha256": digest(load_bytes("final_current_text_candidate_manifest.json"))}
    closeout = {
        "state": FINALIZER_STATUS,
        "observed_utc": runtime["observed_utc"],
        "recipe_identity": IDENTITY,
        "recipe_sha256": RECIPE_SHA256,
        "checkpoint": checkpoint,
        "current_text_technical_status": technical["status"],
        "raw_full_archive_flag_preserved_false": True,
        "TRAINING_DATASET_READY": False,
        "training_started": False,
        "new_cases": 0,
        "new_chat_rows": 0,
        "source_versions_indexed": 1_629_906,
        "unique_chat_rows_processed": 6_502_392,
        "physical_chat_occurrences_processed": 6_502_392,
        "members_complete": 251,
        "members_expected": 251,
        "actual_case_counts_by_split": {"train": 1_625_586, "validation": 6, "test": 6},
        "candidate_chat_rows": 6_502_344,
        "evaluation_chat_rows": {"validation": 24, "test": 24},
        "source_only_rows": 4_308,
        "source_only_classifications": deepcopy(antijoin["counts"]["classifications"]),
        "source_only_antijoin_preserved": True,
        "historical_accepted_cases": state["accepted_cases"],
        "historical_training_chat_rows": state["training_chat_rows"],
        "historical_source_counter_difference": 16,
        "physical_observation_tasks_pending": 5,
        "constraints_pending": 7,
        "asset_masters_pending": 10,
        "g3_source_locator_pending": 1,
        "human_signoffs_created": 0,
        "human_review_claim": False,
        "whole_curriculum_certified": False,
        "technical_adjudication": technical_ref,
        "current_text_manifest": manifest_ref,
        "evidence_member_prefix": PREFIX,
    }
    latest_runtime = dict(state.get("latest_colab_runtime_observation", {}),
        observed_utc=runtime["observed_utc"], worker_alive_at_observation=False,
        runtime_status="AUDIT_FINISHED_WITH_FINDINGS", checkpoint=checkpoint,
        source_versions_indexed=1_629_906, unique_chat_rows_committed=6_502_392,
        committed_physical_chat_rows=6_502_392, members_complete=251, members_expected=251,
        last_verified_checkpoint_unique_chat_rows=6_502_392, live_report=raw_report,
        current_issues=raw_report["issues"], current_text_technical_metadata_complete=True,
        full_archive_audit_complete=False, TRAINING_DATASET_READY=False, training_started=False,
        evidence_member=PREFIX + "final_runtime_observation.json")

    # Prior adapter counters are preserved in observation history, not represented as current.
    latest_runtime.pop("batch_adapter_stats", None)
    for control in (state, chat):
        control.setdefault("data_only_colab_observation_history", []).append(
            deepcopy(control.get("latest_colab_runtime_observation", {})))
        control["latest_colab_runtime_observation"] = latest_runtime
        control.setdefault("verified_v3_checkpoint_history", []).append(deepcopy(control.get("latest_verified_v3_checkpoint", {})))
        control["latest_verified_v3_checkpoint"] = checkpoint
        control["latest_current_text_closeout"] = closeout
        control.setdefault("final_metadata_check_history", []).append(
            deepcopy(control.get("final_metadata_check", {})))
        control["final_metadata_check"] = {
            "state": FINALIZER_STATUS, "technical_evidence_complete": True,
            "raw_finding_preserved": True, "physical_curriculum_pending": True,
            "TRAINING_DATASET_READY": False, "training_started": False,
            "technical_adjudication": technical_ref, "manifest": manifest_ref,
        }
        control["TRAINING_DATASET_READY"] = False
        control["training_started"] = False
        control["full_archive_audit_complete"] = False
    state["latest_data_only_notebook"] = notebook
    state["status"] = "CURRENT_TEXT_TECHNICAL_AUDIT_COMPLETE_PHYSICAL_IMAGE_SOURCE_PENDING"
    state["updated_utc"] = datetime.now(timezone.utc).isoformat()
    state["next_action"] = (
        "Current full text candidate view has technical metadata evidence only. Preserve its raw V3 completion=false flag and the one regression_only issue. "
        "Continue the five physical observation tasks, seven constraints, ten asset masters, and one G3 source locator; retain all 299 human signoffs without adding any. "
        "The historical accepted counter remains 1629922 while current source index is 1629906; the difference of 16 remains unexplained. "
        "Do not mark TRAINING_DATASET_READY or whole-curriculum certification true. No training was launched."
    )

    marker = "### Nhật ký 23/10/2026 — kiểm tra kỹ thuật toàn bộ current text candidate"
    if marker.encode("utf-8") in parent_context:
        raise ValueError("context already contains this closeout marker")
    anti_counts = json.dumps(antijoin["counts"]["classifications"], ensure_ascii=False, sort_keys=True)
    text = (
        f"\n\n{marker}\n"
        f"Finalizer đã kết thúc sau khi scanner hoàn tất; raw checkpoint cùng ID{CHECKPOINT_ID} có {checkpoint['bytes']} byte, SHA256 {checkpoint['sha256']}, fresh raw readback đã xác nhận. "
        f"Recipe giữ nguyên identity {IDENTITY} / SHA256 {RECIPE_SHA256}; 251/251 member hoàn tất, nguồn 1,629,906, chat unique/vật lý 6,502,392. "
        "Raw V3 report vẫn giữ đúng một issue SOURCE_SPLIT_MISSING_OR_UNKNOWN cho regression_only; full_archive_token_linkage_split_audit_complete=false. "
        f"Adjudication kỹ thuật current-text: {technical['status']}; candidate train 6,502,344 chat / 1,625,586 case; validation và test mỗi split 24 chat / 6 case. "
        f"Anti-join giữ nguyên 4,308 source-only rows và buckets {anti_counts}; không đổi nhãn hoặc thêm nguồn/chat. "
        "Bộ đếm lịch sử accepted_cases=1,629,922 và training_chat_rows=6,502,344 được giữ; chênh 16 giữa lịch sử và nguồn thực 1,629,906 chưa được giải thích. "
        "Đây là kiểm tra kỹ thuật của current text candidate view; còn 5 physical observation tasks, 7 constraints, 10 asset masters và 1 G3 locator. "
        "Giữ 299 human signoffs, không tạo signoff mới. whole_curriculum_certified=false, all_rows_semantically_human_reviewed=false, TRAINING_DATASET_READY=false; không train/GPU/weights. "
        f"Evidence được thêm vào PROGRESS dưới {PREFIX}; mọi member cũ được giữ nguyên byte. STATE được chuẩn bị riêng để root ghi sau khi các control còn lại đã có raw readback.\n"
    )
    context = parent_context + text.encode("utf-8")

    progress_path = ROOT / "next_progress.zip"
    with zipfile.ZipFile(progress_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in old_members.items():
            archive.writestr(name, data)
        for name, data in additions.items():
            archive.writestr(name, data)
    with zipfile.ZipFile(progress_path) as archive:
        if archive.namelist()[:len(old_names)] != old_names or len(archive.namelist()) != len(set(archive.namelist())):
            raise ValueError("prepared PROGRESS order/uniqueness changed")
        if any(archive.read(name) != data for name, data in old_members.items()):
            raise ValueError("an existing PROGRESS member changed")
        if any(archive.read(name) != data for name, data in additions.items()):
            raise ValueError("a new bounded evidence member differs")

    # The output directory is local preparation only; STATE is emitted last.
    chat_bytes = (json.dumps(chat, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    context_bytes = context
    state_bytes = (json.dumps(state, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    progress_bytes = progress_path.read_bytes()
    write_atomic("next_chat.json", chat_bytes)
    write_atomic("next_context.md", context_bytes)
    progress_ref = write_atomic("next_progress.zip", progress_bytes)
    state_ref = write_atomic("next_state.json", state_bytes)
    controls = {
        "progress": {"id": CONTROL_IDS["progress"], **progress_ref},
        "chat": {"id": CONTROL_IDS["chat"], "name": "next_chat.json", "bytes": len(chat_bytes), "sha256": digest(chat_bytes)},
        "context": {"id": CONTROL_IDS["context"], "name": "next_context.md", "bytes": len(context_bytes), "sha256": digest(context_bytes)},
        "state": {"id": CONTROL_IDS["state"], **state_ref},
    }
    save_json("prepared_control_updates.json", {
        "controls": controls, "state_must_be_written_last": True,
        "parent_control_raw_readbacks_verified": True,
        "old_progress_members_byte_identical": True,
        "source_only_classifications_preserved": antijoin["counts"]["classifications"],
        "TRAINING_DATASET_READY": False, "training_started": False,
        "remote_publication_performed": False,
    })
    print(json.dumps({"prepared": True, "controls": controls,
                      "training_started": False, "TRAINING_DATASET_READY": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
