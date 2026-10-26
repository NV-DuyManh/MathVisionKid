"""Behavior-aligned prompt projection built on the frozen V3 target renderer."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

_LOCAL_V3 = Path(__file__).resolve().with_name("verbal_training_renderer_v3.py")
_V3_PATH = _LOCAL_V3 if _LOCAL_V3.is_file() else Path(__file__).resolve().parents[1] / "verbal_recovery_20261024" / "verbal_training_renderer_v3.py"
if hashlib.sha256(_V3_PATH.read_bytes()).hexdigest() != "6b15233ae253eed7825864413edbdf3f8553ad955ef248e045c05f64e4473057":
    raise ValueError("Frozen target renderer hash changed")
_spec = importlib.util.spec_from_file_location("behavior_renderer_v3", _V3_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load frozen sibling renderer: {_V3_PATH}")
V3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(V3)

VERSION = "behavior_render.v1"
SYSTEM = (
    "Bạn là gia sư Toán tiểu học. Chỉ dùng dữ kiện trong đề và lời làm thực sự được cung cấp; "
    "không tự tạo lời làm của học sinh. Giải thích ngắn gọn, nhất quán với chế độ được yêu cầu; "
    "với lời giải đầy đủ, hãy kiểm tra kết quả. Không bịa dữ kiện khi đề thiếu thông tin."
)

_MODE_HEADERS = {
    "worked_solution": "Chế độ: Giải đầy đủ",
    "hint_level_1": "Chế độ: Gợi ý bước đầu",
    "hint_level_2": "Chế độ: Gợi ý thêm một bước",
    "hint_level_3": "Chế độ: Gợi ý cách kiểm tra và hoàn thiện",
}
_MODE_INSTRUCTIONS = {
    "worked_solution": "Giải đầy đủ, giải thích cách làm và kiểm tra kết quả.",
    "hint_level_1": "Gợi ý bước đầu để em tự làm; không nêu đáp số cuối hoặc chọn đáp án thay em.",
    "hint_level_2": "Gợi ý thêm một bước để em tự làm; không nêu đáp số cuối hoặc chọn đáp án thay em.",
    "hint_level_3": "Gợi ý cách kiểm tra và hoàn thiện; không nêu đáp số cuối hoặc chọn đáp án thay em.",
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha(raw)


def _append_once(parts: list[str], prior: str, label: str, value: str) -> str:
    """Append only when exact source text is not already present; no fuzzy matching."""
    if value and value not in prior:
        parts.extend((label, value))
        return prior + "\n\n" + label + "\n\n" + value
    return prior


def prompt(value: dict[str, Any]) -> str:
    """Shared train/eval user prompt. Input schema is validated by the V3 renderer."""
    # V3.prompt is the fail-closed schema/type validator for prompt source fields.
    V3.prompt(value)
    mode = value["mode"]
    if mode not in _MODE_HEADERS:
        raise ValueError("Unknown tutor mode")
    parts = [f"Toán lớp {value['grade']}.", _MODE_HEADERS[mode], value["problem"]]
    prior = "\n\n".join(parts)

    if value.get("givens"):
        parts.append("Dữ kiện đã cho:")
        prior += "\n\nDữ kiện đã cho:"
        for given in value["givens"]:
            prior = _append_once(parts, prior, "", given["text"])
            if given.get("value") is not None:
                rendered = "Giá trị đã cho: " + str(given["value"])
                if rendered not in prior:
                    parts.append(rendered)
                    prior += "\n\n" + rendered
            if given.get("unit"):
                rendered = "Đơn vị dữ kiện: " + given["unit"]
                if rendered not in prior:
                    parts.append(rendered)
                    prior += "\n\n" + rendered

    if value.get("requested_quantity"):
        rendered = "Cần tìm: " + value["requested_quantity"]
        if rendered not in prior:
            parts.append(rendered)
            prior += "\n\n" + rendered

    work = value.get("student_work")
    if work is not None:
        if isinstance(work, str):
            work_texts = [("Lời làm em đã cung cấp:", work)]
        else:
            work_texts = []
            if "text" in work:
                work_texts.append(("Lời làm em đã cung cấp:", work["text"]))
            work_texts.extend(("Trích lời làm đã cung cấp:", item["excerpt"]) for item in work.get("observations", []))
        for label, text in work_texts:
            prior = _append_once(parts, prior, label, text)

    parts.extend(("Yêu cầu:", _MODE_INSTRUCTIONS[mode]))
    return "\n\n".join(parts)


def render(row: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Project neutral messages and provenance; source row and old attestations are not copied."""
    if not isinstance(row, dict) or not isinstance(row.get("messages"), list) or len(row["messages"]) < 3:
        raise ValueError("Expected source row with system, user, and assistant messages")
    source_prompt = json.loads(row["messages"][1]["content"])
    source_target = json.loads(row["messages"][2]["content"])
    mode = row["mode"]
    if source_prompt.get("mode") != mode:
        raise ValueError("Source mode mismatch")
    user_prompt = prompt(source_prompt)
    target, target_proof = V3.target(source_target, mode)
    projected = {
        "sample_id": row["sample_id"],
        "case_group_id": row["case_group_id"],
        "mode": mode,
        "split": row["split"],
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": target},
        ],
    }
    proof = {
        "renderer_version": VERSION,
        "source_canonical_sha256": _canonical_hash(row),
        "source_system_sha256": _sha(row["messages"][0]["content"].encode("utf-8")),
        "target_sha256": _sha(target.encode("utf-8")),
        "target_renderer_version": target_proof["version"],
        "source_row_modified": False,
        "source_attestation_carried_forward": False,
        "fields": target_proof["fields"],
        "target_unchanged_from_v3": True,
    }
    return projected, proof

