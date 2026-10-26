"""Safely publish four prepared controls to their existing Google Drive IDs.

This module is intended for an authenticated Colab Drive API client. It never
creates Drive files and never reads corpus/training payloads.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Mapping

KINDS = ("progress", "chat", "context", "state")
MAX_CONTROL_BYTES = 32 * 1024 * 1024


def _digest_file(path: Path) -> tuple[int, str]:
    h = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            size += len(chunk)
            h.update(chunk)
    return size, h.hexdigest()


def _pin(ref: Mapping[str, Any], label: str) -> tuple[str, int, str]:
    try:
        file_id, size, digest = ref["id"], int(ref["bytes"]), ref["sha256"]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid {label} pin") from exc
    if not isinstance(file_id, str) or not file_id or size < 0 or size > MAX_CONTROL_BYTES:
        raise ValueError(f"invalid or oversized {label} pin")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError(f"invalid {label} SHA-256")
    return file_id, size, digest.lower()


def _download(api: Any, file_id: str, dest: Path, expected_size: int | set[int]) -> tuple[int, str]:
    """Stream Drive media to a bounded temporary runtime file and hash it."""
    try:
        from googleapiclient.http import MediaIoBaseDownload
    except ImportError as exc:  # pragma: no cover - only authenticated Colab needs this
        raise RuntimeError("google-api-python-client is required in Colab") from exc
    metadata = api.files().get(fileId=file_id, fields="id,size", supportsAllDrives=True).execute()
    if metadata.get("id") != file_id:
        raise ValueError("Drive returned a different file ID")
    remote_size = int(metadata.get("size", -1))
    allowed_sizes = expected_size if isinstance(expected_size, set) else {expected_size}
    if remote_size < 0 or remote_size > MAX_CONTROL_BYTES or remote_size not in allowed_sizes:
        raise ValueError(f"Drive metadata size mismatch for {file_id}")
    h = hashlib.sha256()
    count = 0
    with dest.open("wb") as out:
        request = api.files().get_media(fileId=file_id)
        downloader = MediaIoBaseDownload(out, request, chunksize=1024 * 1024)
        done = False
        while not done:
            _, done = downloader.next_chunk()
            count = out.tell()
            if count > MAX_CONTROL_BYTES or count > remote_size:
                raise ValueError(f"Drive media exceeded pinned size for {file_id}")
        out.flush()
        os.fsync(out.fileno())
    # Hash in a separate pass so this works with the standard Drive downloader.
    size, digest = _digest_file(dest)
    if count != size:
        raise ValueError("streamed byte count mismatch")
    return size, digest


def _validate_prepared(prepared: Mapping[str, Any], parent_paths: Mapping[str, Path]) -> dict[str, dict[str, Any]]:
    if set(prepared) != set(KINDS):
        raise ValueError("prepared controls must contain exactly progress/chat/context/state")
    pins: dict[str, dict[str, Any]] = {}
    for kind in KINDS:
        entry = prepared[kind]
        file_id, size, digest = _pin(entry, f"prepared {kind}")
        path = Path(entry["path"]).expanduser().resolve(strict=True)
        actual_size, actual_digest = _digest_file(path)
        if actual_size != size or actual_digest != digest:
            raise ValueError(f"prepared {kind} bytes do not match the pinned hash")
        pins[kind] = {"id": file_id, "bytes": size, "sha256": digest, "path": path}

    # Existing controls are pinned to their Drive IDs; no new ID can enter a transaction.
    for kind in KINDS:
        parent_id, _, _ = _pin(parent_paths[kind], f"parent {kind}")
        if pins[kind]["id"] != parent_id:
            raise ValueError(f"prepared {kind} targets a different Drive ID")

    # Validate all local invariants before the first remote write.
    old_context = Path(parent_paths["context"]["path"]).read_bytes()
    new_context = pins["context"]["path"].read_bytes()
    if not new_context.startswith(old_context):
        raise ValueError("prepared context does not preserve the full old context prefix")

    with zipfile.ZipFile(parent_paths["progress"]["path"], "r") as old_zip, zipfile.ZipFile(pins["progress"]["path"], "r") as new_zip:
        old_names = old_zip.namelist()
        new_names = new_zip.namelist()
        if len(old_names) != len(set(old_names)) or len(new_names) != len(set(new_names)):
            raise ValueError("progress ZIP contains duplicate member names")
        if not set(old_names).issubset(new_names):
            raise ValueError("prepared progress ZIP removed an old member")
        for name in old_names:
            if old_zip.read(name) != new_zip.read(name):
                raise ValueError(f"prepared progress ZIP changed old member {name!r}")

    state = json.loads(pins["state"]["path"].read_text(encoding="utf-8"))
    chat = json.loads(pins["chat"]["path"].read_text(encoding="utf-8"))
    if state.get("accepted_cases") != 1629922 or state.get("training_chat_rows") != 6502344:
        raise ValueError("prepared state has unexpected accepted-case/chat counts")
    chat_rows = chat.get("chat_rows")
    reconciliation = chat.get("count_reconciliation", {})
    if chat_rows != 6502344 or reconciliation.get("declared_candidate_chat_rows") != 6502344 or reconciliation.get("historical_accepted_case_counter_preserved") != 1629922:
        raise ValueError("prepared chat manifest has unexpected accepted-case/chat counts")
    for label, obj in (("state", state), ("chat", chat)):
        if obj.get("TRAINING_DATASET_READY") is not False or obj.get("training_started") is not False:
            raise ValueError(f"prepared {label} must explicitly keep training disabled")
    return pins


def publish_controls(
    drive_api: Any,
    expected_parent_refs: Mapping[str, Mapping[str, Any]],
    prepared_paths: Mapping[str, Mapping[str, Any]],
    runtime_dir: str | os.PathLike[str],
    *,
    receipt_path: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Publish controls in safe order; caller supplies an authenticated Drive v3 API.

    ``expected_parent_refs`` maps each kind to {id, bytes, sha256, path}; path is
    the locally retained verified raw parent used for ZIP/context invariants.
    ``prepared_paths`` maps each kind to {id, bytes, sha256, path}.
    """
    if set(expected_parent_refs) != set(KINDS):
        raise ValueError("expected parents must contain exactly the four control kinds")
    parent_pins = {kind: _pin(expected_parent_refs[kind], f"parent {kind}") for kind in KINDS}
    if len({p[0] for p in parent_pins.values()}) != 4:
        raise ValueError("the four controls must use four distinct existing Drive IDs")

    runtime = Path(runtime_dir).resolve()
    runtime.mkdir(parents=True, exist_ok=True)
    receipt = Path(receipt_path).resolve() if receipt_path else runtime / "cloud_control_transaction_receipt.json"
    if receipt.parent != runtime and runtime not in receipt.parents:
        raise ValueError("receipt must remain inside the runtime directory")
    pins = _validate_prepared(prepared_paths, {k: {**expected_parent_refs[k], "path": expected_parent_refs[k]["path"]} for k in KINDS})

    # Fetch and hash all four current remote controls before any write. A file can
    # be at its expected parent or at our prepared digest from a prior partial run.
    with tempfile.TemporaryDirectory(prefix="control-preflight-", dir=runtime) as temp:
        tempdir = Path(temp)
        for kind in KINDS:
            old_id, old_size, old_hash = parent_pins[kind]
            local = tempdir / f"{kind}.raw"
            size, digest = _download(drive_api, old_id, local, {old_size, pins[kind]["bytes"]})
            # Allow either the exact pinned parent or this same prepared output.
            if (size, digest) not in ((old_size, old_hash), (pins[kind]["bytes"], pins[kind]["sha256"])):
                raise RuntimeError(f"remote {kind} changed from both expected parent and prepared bytes")

    order = ("progress", "chat", "context", "state")
    completed: list[dict[str, Any]] = []
    if receipt.exists():
        prior = json.loads(receipt.read_text(encoding="utf-8"))
        if prior.get("prepared_hashes") != {k: pins[k]["sha256"] for k in KINDS}:
            raise RuntimeError("existing transaction receipt belongs to different prepared bytes")
        completed = list(prior.get("verified_writes", []))

    for kind in order:
        pin = pins[kind]
        old_id, old_size, old_hash = parent_pins[kind]
        # Recheck immediately before this write to catch concurrent changes.
        with tempfile.TemporaryDirectory(prefix=f"control-{kind}-guard-", dir=runtime) as temp:
            guard = Path(temp) / "current.raw"
            size, digest = _download(drive_api, old_id, guard, {old_size, pin["bytes"]})
        if (size, digest) == (pin["bytes"], pin["sha256"]):
            pass  # Resume after an already completed write, still verified by raw read.
        elif (size, digest) == (old_size, old_hash):
            try:
                from googleapiclient.http import MediaFileUpload
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError("google-api-python-client is required in Colab") from exc
            drive_api.files().update(
                fileId=old_id,
                media_body=MediaFileUpload(str(pin["path"]), resumable=True),
                fields="id,size",
                supportsAllDrives=True,
            ).execute()
        else:
            raise RuntimeError(f"remote {kind} changed before its write")

        # Fresh raw-media download after every update (including resumed updates).
        with tempfile.TemporaryDirectory(prefix=f"control-{kind}-readback-", dir=runtime) as temp:
            readback = Path(temp) / "readback.raw"
            rb_size, rb_hash = _download(drive_api, old_id, readback, pin["bytes"])
        if (rb_size, rb_hash) != (pin["bytes"], pin["sha256"]):
            raise RuntimeError(f"fresh raw readback failed for {kind}")
        completed = [item for item in completed if item.get("kind") != kind]
        completed.append({"kind": kind, "id": old_id, "bytes": rb_size, "sha256": rb_hash, "fresh_raw_readback_verified": True})
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(json.dumps({
            "transaction": "four_existing_controls",
            "order": list(order),
            "prepared_hashes": {k: pins[k]["sha256"] for k in KINDS},
            "verified_writes": completed,
            "TRAINING_DATASET_READY": False,
            "training_started": False,
        }, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    return json.loads(receipt.read_text(encoding="utf-8"))

