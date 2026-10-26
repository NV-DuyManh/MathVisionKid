import gzip
import hashlib
import json
from pathlib import Path
import zipfile

from colab_train_view_worker import (
    _decode_chat_metadata,
    _iter_member_lines,
    _peek_top_level_split,
    load_protected_question_hashes,
    question_sha256,
)


def _fake_row(mode="worked_solution"):
    answer = {"can_solve": True, "steps": [{"expression": "2+3"}], "answer": "5"}
    if mode.startswith("hint_"):
        level = int(mode[-1])
        answer = {"hint": "Think of the operation.", "question": "What is known?", "level": level}
    return {
        "sample_id": f"case-1:{mode}", "source_sample_id": "case-1",
        "case_group_id": "group-1", "grade": 2, "mode": mode,
        "messages": [
            {"role": "system", "content": "teacher"},
            {"role": "user", "content": json.dumps({"grade": 2, "problem": "Bạn Lan có 2 quả táo và được thêm 3 quả.", "mode": mode})},
            {"role": "assistant", "content": json.dumps(answer)},
        ],
    }


def test_proxy_labels_are_deterministic_and_row_content_is_not_claimed_as_qa():
    features = _decode_chat_metadata(_fake_row())
    assert features == _decode_chat_metadata(_fake_row())
    assert features["grade"] == "2"
    assert features["skill"] == "word_problem"
    assert features["skill_origin"] == "problem_text_heuristic_proxy"
    assert features["method"] == "direct_or_short_solution_proxy"
    assert len(features["question_sha256"]) == 64
    assert question_sha256("A   B") == question_sha256("a b")


def test_protected_eval_file_reads_only_question_hash_fields(tmp_path):
    qhash = "a" * 64
    path = tmp_path / "protected.jsonl"
    path.write_text(json.dumps({"sample_id": "opaque", "question_sha256": qhash}) + "\n", encoding="utf-8")
    assert load_protected_question_hashes(path) == {qhash}


def test_eval_split_peek_leaves_nested_prompt_and_answer_opaque():
    raw = b'{"metadata":{"split":"train"},"messages":[{"content":"private"}],"split":"test"}'
    assert _peek_top_level_split(raw) == "test"


def test_streams_gzip_and_verifies_zip_member_metadata_without_extracting(tmp_path):
    lines = [json.dumps({"split": "train", "sample_id": "opaque"}).encode() + b"\n"]
    gz_path = tmp_path / "one.jsonl.gz"
    with gzip.open(gz_path, "wb") as stream:
        stream.writelines(lines)
    direct = {"file_name": gz_path.name, "member": None}
    assert list(_iter_member_lines(gz_path, direct)) == lines

    inner = tmp_path / "member.gz"
    with gzip.open(inner, "wb") as stream:
        stream.writelines(lines)
    compressed = inner.read_bytes()
    zip_path = tmp_path / "bundle.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("chat.jsonl.gz", compressed)
    descriptor = {
        "member": "chat.jsonl.gz", "member_bytes": len(compressed),
        "member_sha256": hashlib.sha256(compressed).hexdigest(),
    }
    assert list(_iter_member_lines(zip_path, descriptor)) == lines

