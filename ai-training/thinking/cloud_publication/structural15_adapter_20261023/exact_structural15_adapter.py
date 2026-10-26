"""Exact read-time neutral-export bindings for the 15 Structural source rows."""
from pathlib import Path
import hashlib
import json

import math_data_archive_audit as A
import exhaustive_colab_loader as L
from math_data_portable_resume import canonical, digest

HERE = Path(__file__).resolve().parent
BINDINGS_PATH = HERE / "bindings.json"
BINDINGS_SHA256 = "95d9fbf8536b908a6456256d8ff04175e8bd017cd34a406e190513844d316e87"
ADAPTER_KIND = "EXACT_STRUCTURAL15_NEUTRAL_EXPORT_BINDING_V1"
VERIFICATION_DIGEST = "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a"


def _load_bindings():
    raw = BINDINGS_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != BINDINGS_SHA256:
        raise ValueError("Structural15 pinned bindings file hash differs")
    data = json.loads(raw)
    if data.get("schema") != "MathVisionKid.Structural15ExactReadTimeBindings.v1":
        raise ValueError("Unexpected Structural15 bindings schema")
    if data.get("parent_auditor_sha256") != "02431da433060a6574127f9a8e14d90cabffe85d8d0150c3b2a331dc15b4be1f":
        raise ValueError("Structural15 bindings target a different frozen auditor")
    rows = data.get("source_rows")
    if not isinstance(rows, dict) or len(rows) != 15:
        raise ValueError("Structural15 bindings must contain exactly 15 source IDs")
    return data, rows


BINDING_DOCUMENT, BINDINGS = _load_bindings()


def _projection(row, binding):
    # Preserve the source projection byte-for-byte semantically; only its group
    # key is projected to the normalized chat_records group at read time.
    projection = A.source_projection(row)
    if digest(projection) != binding["source_projection_sha256"]:
        raise ValueError("Structural15 original source projection hash differs")
    projected = dict(projection)
    projected["case_group_id"] = binding["chat_group_id"]
    if digest(projected) != binding["adapted_projection_sha256"]:
        raise ValueError("Structural15 adapted projection hash differs")
    return projected


def binding_source(row, source_raw_sha):
    """Return (adapted projection, pinned binding); reject any unpinned source."""
    sid = row.get("sample_id")
    binding = BINDINGS.get(sid)
    if binding is None:
        raise ValueError("Unknown Structural15 source ID")
    if source_raw_sha != binding["source_raw_sha256"]:
        raise ValueError("Structural15 source raw hash differs")
    if digest(row) != binding["source_canonical_sha256"]:
        raise ValueError("Structural15 source canonical hash differs")
    if row.get("split") != binding["source_split"]:
        raise ValueError("Structural15 source split differs")
    if row.get("case_group_id") != binding["source_group_id"]:
        raise ValueError("Structural15 original source group differs")
    if binding.get("verification_digest") != VERIFICATION_DIGEST:
        raise ValueError("Structural15 verification digest differs")
    return _projection(row, binding), binding


def validate_chat(row, actual_raw_sha):
    """Verify an exact pinned chat row and return its source binding."""
    try:
        sid = L.case_id(row)
    except (KeyError, TypeError):
        raise ValueError("Unknown Structural15 chat source ID") from None
    binding = BINDINGS.get(sid)
    if binding is None:
        raise ValueError("Unknown Structural15 chat source ID")
    chat = next((v for v in binding["chats"].values() if v["sample_id"] == row.get("sample_id")), None)
    if chat is None:
        raise ValueError("Structural15 chat sample ID is not pinned")
    if actual_raw_sha != chat["raw_sha256"]:
        raise ValueError("Structural15 chat raw hash differs")
    if digest(row) != chat["canonical_sha256"]:
        raise ValueError("Structural15 chat canonical hash differs")
    if row.get("case_group_id") != binding["chat_group_id"]:
        raise ValueError("Structural15 normalized chat group differs")
    if row.get("mode") not in binding["chats"] or row.get("split") != "train":
        raise ValueError("Structural15 chat mode or split differs")
    if row.get("source_row_sha256") != binding["source_canonical_sha256"]:
        raise ValueError("Structural15 chat source canonical pointer differs")
    if row.get("row_sha256") != binding["source_canonical_sha256"]:
        raise ValueError("Structural15 chat row pointer differs")
    if digest(row.get("verification")) != binding["verification_digest"]:
        raise ValueError("Structural15 chat verification digest differs")
    return binding

