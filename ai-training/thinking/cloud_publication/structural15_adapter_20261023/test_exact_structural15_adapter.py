import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "thinking"))
sys.path.insert(0, str(HERE))
import exact_structural15_adapter as adapter
import build_derived_auditor as builder
from math_data_portable_resume import digest


def test_pinned_bindings_and_frozen_parent_hashes():
    assert hashlib.sha256(adapter.BINDINGS_PATH.read_bytes()).hexdigest() == adapter.BINDINGS_SHA256
    assert hashlib.sha256(builder.PARENT.read_bytes()).hexdigest() == builder.PARENT_SHA256
    assert len(adapter.BINDINGS) == 15


def test_tampered_bindings_file_is_rejected(tmp_path, monkeypatch):
    altered = tmp_path / "bindings.json"
    altered.write_bytes(adapter.BINDINGS_PATH.read_bytes() + b" ")
    monkeypatch.setattr(adapter, "BINDINGS_PATH", altered)
    with pytest.raises(ValueError, match="bindings file hash"):
        adapter._load_bindings()


def _chat_fixture(monkeypatch):
    row = {
        "sample_id": "fixture:worked_solution", "source_sample_id": "fixture", "mode": "worked_solution",
        "split": "train",
        "case_group_id": "normalized_fixture", "source_row_sha256": "a" * 64,
        "row_sha256": "a" * 64, "verification": {"ok": True}, "body": "untouched",
    }
    raw = "b" * 64
    binding = {
        "source_canonical_sha256": "a" * 64,
        "chat_group_id": "normalized_fixture",
        "verification_digest": digest(row["verification"]),
        "chats": {"worked_solution": {"sample_id": row["sample_id"], "raw_sha256": raw}},
    }
    # Keep this fixture self-consistent with the adapter's canonical check.
    binding["chats"]["worked_solution"]["canonical_sha256"] = digest(row)
    monkeypatch.setitem(adapter.BINDINGS, "fixture", binding)
    return row, raw


def test_chat_exact_binding_accepts_and_rejects_raw_canonical_group_and_body(monkeypatch):
    row, raw = _chat_fixture(monkeypatch)
    assert adapter.validate_chat(row, raw)["chat_group_id"] == "normalized_fixture"
    with pytest.raises(ValueError, match="raw hash"):
        adapter.validate_chat(row, "c" * 64)
    wrong_group = dict(row, case_group_id="wrong")
    with pytest.raises(ValueError, match="canonical hash"):
        adapter.validate_chat(wrong_group, raw)
    changed_body = dict(row, body="changed")
    with pytest.raises(ValueError, match="canonical hash"):
        adapter.validate_chat(changed_body, raw)


def test_unknown_chat_and_source_ids_are_refused():
    with pytest.raises(ValueError, match="Unknown Structural15 chat"):
        adapter.validate_chat({"source_sample_id": "not-pinned"}, "0" * 64)
    with pytest.raises(ValueError, match="Unknown Structural15 source"):
        adapter.binding_source({"sample_id": "not-pinned"}, "0" * 64)


def test_source_projection_only_changes_normalized_group(monkeypatch):
    source = {"case_group_id": "original-group", "payload": "same"}
    projected = {"case_group_id": "chat-group", "payload": "same"}
    binding = {
        "source_projection_sha256": digest(source),
        "adapted_projection_sha256": digest(projected),
        "chat_group_id": "chat-group",
    }
    monkeypatch.setattr(adapter.A, "source_projection", lambda _row: dict(source))
    result = adapter._projection({}, binding)
    assert result == projected
    assert {k: v for k, v in result.items() if k != "case_group_id"} == {
        k: v for k, v in source.items() if k != "case_group_id"
    }


def test_builder_derives_and_compiles_without_changing_frozen_parent(tmp_path):
    before = hashlib.sha256(builder.PARENT.read_bytes()).hexdigest()
    output = builder.derive(tmp_path / "derived_auditor.py")
    source = output.read_text(encoding="utf-8")
    compile(source, str(output), "exec")
    assert "STRUCTURAL.validate_chat(row,rawhash(text))" in source
    assert "STRUCTURAL15_RAW_CANONICAL_AND_CHAT_HASH_VERIFIED" in source
    assert "structural15_bindings_sha256" in source
    assert "def verify_structural_bindings()" in source
    assert "L.validate_chat(row)" in source
    assert "STRUCTURAL.validate_chat(row,rawhash(text))" in source
    assert hashlib.sha256(builder.PARENT.read_bytes()).hexdigest() == before == builder.PARENT_SHA256


def test_generated_runtime_verifier_rejects_tampered_adapter(tmp_path, monkeypatch):
    output = builder.derive(tmp_path / "derived_auditor.py")
    spec = importlib.util.spec_from_file_location("structural15_derived_test", output)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.verify_structural_bindings()
    tampered = tmp_path / "tampered_adapter.py"
    tampered.write_bytes(Path(adapter.__file__).read_bytes() + b"\n# modified\n")
    monkeypatch.setattr(adapter, "__file__", str(tampered))
    with pytest.raises(ValueError, match="adapter code hash"):
        module.verify_structural_bindings()


def test_actual_builder_chat_records_use_archive_shape_and_bound_group():
    import exhaustive_primary_math as producer
    import exhaustive_colab_loader as loader

    source_path = ROOT / "thinking" / "cloud_publication" / "sgk_page_audit_20261019" / "extensions" / "structural.jsonl"
    seen = set()
    with source_path.open(encoding="utf-8") as stream:
        for line in stream:
            source = json.loads(line)
            if source.get("sample_id") not in adapter.BINDINGS:
                continue
            sid = source["sample_id"]
            projection, binding = adapter.binding_source(source, binding_raw(source_path, line))
            assert projection["case_group_id"] == binding["chat_group_id"]
            chats = list(producer.chat_records(source))
            assert len(chats) == 4
            for chat in chats:
                assert "case_id" not in chat
                assert loader.case_id(chat) == sid
                # The archive export applies its pinned normalized group during
                # read-time projection; chat_records itself emits source IDs.
                assert chat["case_group_id"] == sid
                projected_chat = dict(chat, case_group_id=binding["chat_group_id"])
                assert projected_chat["case_group_id"] == projection["case_group_id"]
                assert chat["messages"]
                pin = binding["chats"][chat["mode"]]
                assert pin["sample_id"] == chat["sample_id"]
                assert len(pin["raw_sha256"]) == len(pin["canonical_sha256"]) == 64
            seen.add(sid)
    assert seen == set(adapter.BINDINGS)


def binding_raw(path, line):
    # bindings pin the source JSONL raw hash without the line terminator.
    row = json.loads(line)
    return hashlib.sha256(line.removesuffix("\n").removesuffix("\r").encode("utf-8")).hexdigest()

