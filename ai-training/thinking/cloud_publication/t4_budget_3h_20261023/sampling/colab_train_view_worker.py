"""Read-only CPU scan and deterministic stratified view builder for Colab.

Caller supplies a read-only Drive v3 client, pinned metadata receipt, and an
evaluation-question-hash file. Only accepted current candidate_chat members
are opened. Non-train records are classified by their split field and dropped
before user/assistant content is accessed. No tokenizer or model is imported.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import gzip
import hashlib
import heapq
import io
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import tempfile
import time
import unicodedata
import zipfile

ACCEPTED = {"ACCEPTED_OWNER_PREAUTHORIZED", "ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED", "OWNER_HUMAN_CERTIFIED"}
MODES = ("worked_solution", "hint_level_1", "hint_level_2", "hint_level_3")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_ROWS = {"train": 6_502_344, "validation": 24, "test": 24}
EXPECTED_RECIPE_SHA = "1bb69c394c7eaaea7034125c6b3361eebbbe0d77e0715a8454331fbe7cee3ff8"
EXPECTED_RECIPE_ID = "6faccfa8b6cae5ae100cdd4777c3481b6d193cb79acae2679086ec8e25718f56"


def _sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _norm(s: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", s).casefold().split())


def question_sha256(problem: str) -> str:
    return hashlib.sha256(_norm(problem).encode("utf-8")).hexdigest()


def _skip_json_value(text: str, index: int) -> int:
    """Skip one JSON value without decoding or retaining nested strings/objects."""
    while index < len(text) and text[index].isspace():
        index += 1
    if index >= len(text):
        raise ValueError("truncated JSON value")
    if text[index] == '"':
        index += 1; escaped = False
        while index < len(text):
            char = text[index]; index += 1
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                return index
        raise ValueError("unterminated JSON string")
    if text[index] in "[{":
        opening = text[index]; closing = "]" if opening == "[" else "}"
        depth = 0; in_string = escaped = False
        while index < len(text):
            char = text[index]; index += 1
            if in_string:
                if escaped: escaped = False
                elif char == "\\": escaped = True
                elif char == '"': in_string = False
            elif char == '"': in_string = True
            elif char == opening: depth += 1
            elif char == closing:
                depth -= 1
                if depth == 0: return index
        raise ValueError("unterminated JSON container")
    start = index
    while index < len(text) and text[index] not in ",}] \t\r\n":
        index += 1
    if index == start:
        raise ValueError("invalid JSON scalar")
    return index


def _peek_top_level_split(raw_line: bytes) -> str | None:
    """Extract only top-level split; nested eval payload fields stay opaque."""
    text = raw_line.decode("utf-8")
    decoder = json.JSONDecoder()
    index = 0
    while index < len(text) and text[index].isspace(): index += 1
    if index >= len(text) or text[index] != "{":
        raise ValueError("candidate row must be a JSON object")
    index += 1
    while index < len(text):
        while index < len(text) and (text[index].isspace() or text[index] == ","): index += 1
        if index >= len(text) or text[index] == "}": return None
        key, index = decoder.raw_decode(text, index)
        if not isinstance(key, str): raise ValueError("non-string top-level JSON key")
        while index < len(text) and text[index].isspace(): index += 1
        if index >= len(text) or text[index] != ":": raise ValueError("invalid JSON object delimiter")
        index += 1
        while index < len(text) and text[index].isspace(): index += 1
        if key == "split":
            value, _ = decoder.raw_decode(text, index)
            return value if isinstance(value, str) else None
        index = _skip_json_value(text, index)
    return None


def _decode_chat_metadata(row: dict) -> dict:
    """Feature extraction; output fields are explicitly weak proxies."""
    try:
        prompt = json.loads(row["messages"][1]["content"])
    except (ValueError, TypeError):
        prompt = {}
    grade = str(row.get("grade", prompt.get("grade", "unknown")))
    if grade not in {"1", "2", "3", "4", "5"}:
        grade = "unknown"
    problem = str(prompt.get("problem", prompt.get("question", row["messages"][1]["content"])))
    text = _norm(problem)
    topic = _norm(str(row.get("topic", row.get("selection_category", ""))))
    source_skill = row.get("skill", row.get("subskill"))
    if isinstance(source_skill, str) and source_skill.strip():
        skill = _norm(source_skill)
        skill_origin = "explicit_chat_metadata"
    elif topic:
        skill = topic
        skill_origin = "explicit_chat_topic_proxy"
    else:
        rules = (
            ("student_error_detection_correction", ("sai", "lỗi", "nhầm", "sửa", "đúng hay sai", "kiểm tra")),
            ("missing_or_contradictory_information", ("thiếu dữ kiện", "chưa đủ", "mâu thuẫn", "không xác định", "cần hỏi")),
            ("geometry_measurement", ("hình", "góc", "đường", "chu vi", "diện tích", "độ dài", "cm", "mét", "kg", "lít", "đồng hồ", "thời gian")),
            ("patterns_logic", ("quy luật", "dãy số", "liệt kê", "khả năng", "có bao nhiêu cách", "logic", "mẫu số")),
            ("fraction_decimal", ("phân số", "tử số", "mẫu số", "thập phân", "0.", "%")),
            ("word_problem", ("mỗi", "còn lại", "tất cả", "nhiều hơn", "ít hơn", "gấp", "chia đều", "cửa hàng", "bạn", "hỏi")),
            ("multi_digit_multiplication_division", ("nhân", "chia", "tích", "thương", "\u00d7", "÷")),
        )
        skill = next((label for label, needles in rules if any(x in text for x in needles)), "natural_number_operations")
        skill_origin = "problem_text_heuristic_proxy"
    answer = {}
    try:
        answer = json.loads(row["messages"][2]["content"])
    except (ValueError, TypeError):
        pass
    steps = answer.get("steps", []) if isinstance(answer, dict) else []
    expressions = [str(s.get("expression")) for s in steps if isinstance(s, dict) and s.get("expression")]
    if any(k in text for k in ("lỗi", "sai", "nhầm", "sửa")):
        method = "error_analysis_proxy"
    elif any(k in text for k in ("liệt kê", "quy luật", "có bao nhiêu cách", "mọi trường hợp")):
        method = "enumeration_or_pattern_proxy"
    elif len(steps) >= 3 or len(expressions) >= 2:
        method = "multi_step_solution_proxy"
    elif steps:
        method = "direct_or_short_solution_proxy"
    else:
        method = "unknown_method_proxy"
    magnitude = sum(int(x) for x in re.findall(r"\d+", text)[:8])
    if len(steps) >= 4 or len(expressions) >= 3 or magnitude > 10000:
        difficulty = "challenge_proxy"
    elif len(steps) >= 2 or len(expressions) >= 1 or magnitude > 100:
        difficulty = "intermediate_proxy"
    else:
        difficulty = "foundation_proxy"
    return {"grade": grade, "skill": skill, "skill_origin": skill_origin,
            "method": method, "difficulty": difficulty,
            "question_sha256": question_sha256(problem)}


def load_protected_question_hashes(path: str | Path) -> set[str]:
    """Read only the hash field from root-provided protected-eval metadata."""
    hashes = set()
    with Path(path).open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            value = row.get("question_sha256")
            if not isinstance(value, str) or not HASH_RE.fullmatch(value):
                raise ValueError(f"protected eval metadata missing question_sha256 at line {line_number}")
            hashes.add(value)
    return hashes


def _verified_download(api, ref: dict, cache_dir: Path, cache_roots=()) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{ref['sha256']}.archive"
    if path.exists() and path.stat().st_size == int(ref["bytes"]) and _sha_file(path) == ref["sha256"]:
        return path
    for root in cache_roots:
        root = Path(root)
        if not root.is_dir():
            continue
        for candidate in root.glob(ref["sha256"] + "*"):
            if candidate.is_file() and candidate.stat().st_size == int(ref["bytes"]) and _sha_file(candidate) == ref["sha256"]:
                return candidate
    if path.exists():
        path.unlink()
    from googleapiclient.http import MediaIoBaseDownload
    metadata = api.files().get(fileId=ref["file_id"], fields="id,size,trashed").execute()
    if metadata.get("id") != ref["file_id"] or metadata.get("trashed") or int(metadata["size"]) != int(ref["bytes"]):
        raise ValueError("Drive artifact metadata differs from pinned release")
    temporary = path.with_suffix(".partial")
    with temporary.open("wb") as output:
        downloader = MediaIoBaseDownload(output, api.files().get_media(fileId=ref["file_id"]), chunksize=8 * 1024 * 1024)
        done = False
        while not done:
            _, done = downloader.next_chunk(num_retries=3)
    if temporary.stat().st_size != int(ref["bytes"]) or _sha_file(temporary) != ref["sha256"]:
        temporary.unlink(missing_ok=True)
        raise ValueError("downloaded archive SHA/size differs from pinned release")
    temporary.replace(path)
    return path


def _iter_member_lines(archive_path: Path, member: dict):
    if member.get("member"):
        with zipfile.ZipFile(archive_path) as archive:
            info = archive.getinfo(member["member"])
            if info.file_size != int(member["member_bytes"]):
                raise ValueError("ZIP member size mismatch")
            with archive.open(info, "r") as binary:
                digest = hashlib.sha256()
                byte_count = 0
                if member["member"].endswith(".gz"):
                    reader = gzip.GzipFile(fileobj=binary)
                    for line in reader:
                        digest.update(line); byte_count += len(line)
                        yield line
                else:
                    for line in binary:
                        digest.update(line); byte_count += len(line)
                        yield line
                # Digest here is decompressed JSONL; member_sha256 pins the
                # compressed member bytes, so validate it in a separate pass.
            with archive.open(info, "r") as binary:
                compressed = hashlib.sha256()
                for block in iter(lambda: binary.read(4 * 1024 * 1024), b""):
                    compressed.update(block)
            if compressed.hexdigest() != member["member_sha256"]:
                raise ValueError("ZIP chat member SHA256 mismatch")
    else:
        opener = gzip.open if member["file_name"].endswith(".gz") else open
        with opener(archive_path, "rb") as stream:
            for line in stream:
                yield line


def _accepted_from_pinned_recipe(row: dict) -> bool:
    status = row.get("acceptance_status")
    return status is None or status in ACCEPTED


def _schema(db: sqlite3.Connection) -> None:
    db.executescript("""
    PRAGMA journal_mode=WAL;
    PRAGMA synchronous=NORMAL;
    CREATE TABLE IF NOT EXISTS cases(
      case_id TEXT PRIMARY KEY, family TEXT, grade TEXT, skill TEXT, skill_origin TEXT,
      method TEXT, difficulty TEXT, question_sha256 TEXT, modes_json TEXT, metadata_json TEXT,
      eligible INTEGER NOT NULL, exclusion TEXT);
    CREATE TABLE IF NOT EXISTS train_questions(
      question_sha256 TEXT PRIMARY KEY, case_id TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS scan_state(
      member_sha256 TEXT PRIMARY KEY, rows_seen INTEGER NOT NULL, train_rows INTEGER NOT NULL,
      member_complete INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS member_scan_state(
      member_key TEXT PRIMARY KEY, rows_seen INTEGER NOT NULL, train_rows INTEGER NOT NULL,
      validation_rows INTEGER NOT NULL, test_rows INTEGER NOT NULL, member_complete INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS scan_counts(kind TEXT PRIMARY KEY, n INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS strata(case_id TEXT NOT NULL, label TEXT NOT NULL, rank TEXT NOT NULL,
      PRIMARY KEY(case_id,label));
    CREATE INDEX IF NOT EXISTS strata_order ON strata(label,rank,case_id);
    """)


def scan_and_sample(api, receipt: dict, protected_eval_hashes_path: str | Path,
                    work_dir: str | Path, *, target_cases: int = 4000,
                    seed: int = 20261023, time_limit_s: int = 1200,
                    progress_callback=None, preexisting_cache_dirs=()) -> dict:
    """Scan hash-pinned accepted train members, build <=target whole-case view.

    ``receipt`` is the structured JSON object stored in the local sampling
    metadata receipt's stdout. This routine is CPU-only and read-only to Drive.
    It intentionally does not load validation/test payload contents.
    """
    started = time.monotonic()
    work = Path(work_dir); work.mkdir(parents=True, exist_ok=True)
    release = receipt["release"]
    if (release.get("TEXT_TRAINING_DATASET_READY") is not True
            or release.get("recipe_sha256") != EXPECTED_RECIPE_SHA
            or release.get("recipe_identity") != EXPECTED_RECIPE_ID
            or release.get("rows_by_split") != EXPECTED_ROWS
            or release.get("all_declared_members_scanned") is not True):
        raise ValueError("release readiness metadata does not match pinned text scope")
    members = receipt["chat_member_metadata"]
    if len(members) != 32 or any(m.get("role") != "candidate_chat" for m in members):
        raise ValueError("expected exactly 32 pinned candidate_chat members")
    if sum(int(m["rows"]) for m in members) != sum(EXPECTED_ROWS.values()):
        raise ValueError("candidate chat member totals do not match all split totals")
    blocked = load_protected_question_hashes(protected_eval_hashes_path)
    db_path = work / "stratified_sampling.sqlite3"
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    _schema(db)
    counts = Counter()
    archive_cache = work / "archive_cache"
    artifacts = receipt["artifact_metadata"]
    try:
        for mi, member in enumerate(members):
            if time.monotonic() - started > time_limit_s:
                raise TimeoutError("metadata scan exceeded its hard wall-clock budget; no manifest emitted")
            member_key = hashlib.sha256(json.dumps(
                {k: member[k] for k in ("sha256", "file_name", "file_id", "bytes", "rows")},
                sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            prior_scan = db.execute("SELECT * FROM member_scan_state WHERE member_key=? AND member_complete=1", (member_key,)).fetchone()
            if prior_scan:
                counts["train_rows_scanned"] += int(prior_scan["train_rows"])
                counts["nontrain_validation"] += int(prior_scan["validation_rows"])
                counts["nontrain_test"] += int(prior_scan["test_rows"])
                counts["members_complete"] += 1
                continue
            archive_ref = artifacts[member["sha256"]]
            if int(archive_ref["bytes"]) != int(member["bytes"]) or member["file_id"] not in archive_ref["file_ids"]:
                raise ValueError("chat member does not bind to its pinned archive descriptor")
            archive_ref = {**archive_ref, "file_id": member["file_id"]}
            archive_path = _verified_download(api, archive_ref, archive_cache, preexisting_cache_dirs)
            seen = train_seen = validation_seen = test_seen = 0
            member_row_hashes = hashlib.sha256()
            for line in _iter_member_lines(archive_path, member):
                seen += 1
                if not line.strip():
                    raise ValueError("blank JSONL row in pinned candidate chat member")
                split = _peek_top_level_split(line)
                if split not in ("train", "validation", "test"):
                    raise ValueError("candidate row has no explicit known split")
                if split != "train":
                    counts[f"nontrain_{split}"] += 1
                    if split == "validation": validation_seen += 1
                    else: test_seen += 1
                    continue
                row = json.loads(line)
                train_seen += 1; counts["train_rows_scanned"] += 1
                if not _accepted_from_pinned_recipe(row):
                    counts["explicitly_unaccepted_train_rows"] += 1
                    continue
                mode = row.get("mode")
                if mode not in MODES:
                    counts["invalid_mode_rows"] += 1
                    continue
                case_id = row.get("source_sample_id") or row.get("sample_id", "").removesuffix(":" + mode)
                if not case_id or not row.get("sample_id"):
                    counts["missing_identity_rows"] += 1
                    continue
                features = _decode_chat_metadata(row)
                if features["question_sha256"] in blocked:
                    counts["protected_eval_question_collisions"] += 1
                    db.execute("INSERT OR REPLACE INTO cases VALUES (?,?,?,?,?,?,?,?,?,?,0,?)",
                      (case_id, member.get("family", "unknown"), features["grade"], features["skill"], features["skill_origin"],
                       features["method"], features["difficulty"], features["question_sha256"], "{}", "{}", "protected_eval_question_hash"))
                    continue
                q_owner = db.execute("SELECT case_id FROM train_questions WHERE question_sha256=?", (features["question_sha256"],)).fetchone()
                if q_owner and q_owner[0] != case_id:
                    prior = db.execute("SELECT * FROM cases WHERE case_id=?", (case_id,)).fetchone()
                    owner = db.execute("SELECT family FROM cases WHERE case_id=?", (q_owner[0],)).fetchone()
                    current_family = member.get("family", "unknown")
                    prefer_current = current_family.startswith("sgk_") and owner and not owner["family"].startswith("sgk_")
                    counts["duplicate_train_question_cases_excluded"] += 1
                    if prefer_current:
                        db.execute("UPDATE cases SET eligible=0,exclusion='duplicate_train_question_sgk_priority' WHERE case_id=?", (q_owner[0],))
                        db.execute("UPDATE train_questions SET case_id=? WHERE question_sha256=?", (case_id, features["question_sha256"]))
                    else:
                        if not prior:
                            db.execute("INSERT INTO cases VALUES (?,?,?,?,?,?,?,?,?,?,0,?)",
                              (case_id, current_family, features["grade"], features["skill"], features["skill_origin"],
                               features["method"], features["difficulty"], features["question_sha256"], "{}", "{}", "duplicate_train_question"))
                        continue
                db.execute("INSERT OR IGNORE INTO train_questions VALUES (?,?)", (features["question_sha256"], case_id))
                raw_hash = hashlib.sha256(line.rstrip(b"\r\n")).hexdigest()
                member_row_hashes.update(raw_hash.encode())
                previous = db.execute("SELECT question_sha256,modes_json,metadata_json FROM cases WHERE case_id=?", (case_id,)).fetchone()
                mode_map = json.loads(previous["modes_json"]) if previous else {}
                if mode in mode_map:
                    if mode_map[mode]["sample_id"] != row["sample_id"] or mode_map[mode]["row_sha256"] != raw_hash:
                        raise ValueError("conflicting duplicate case/mode identity")
                    counts["duplicate_case_mode_rows"] += 1
                    continue
                mode_map[mode] = {"sample_id": row["sample_id"], "row_sha256": raw_hash}
                meta = {k: features[k] for k in ("grade", "skill", "skill_origin", "method", "difficulty", "question_sha256")}
                if previous:
                    if json.loads(previous["metadata_json"]) != meta:
                        # Method is derived from the worked_solution; recompute
                        # only once it arrives and permit provisional unknowns.
                        old = json.loads(previous["metadata_json"])
                        for key in ("grade", "skill", "question_sha256"):
                            if old[key] != meta[key]:
                                raise ValueError(f"case modes disagree on {key}")
                        if mode != "worked_solution" and old["method"] != meta["method"]:
                            meta["method"] = old["method"]
                            meta["difficulty"] = old["difficulty"]
                db.execute("INSERT OR REPLACE INTO cases VALUES (?,?,?,?,?,?,?,?,?,?,1,NULL)",
                    (case_id, member.get("family", "unknown"), meta["grade"], meta["skill"], meta["skill_origin"],
                     meta["method"], meta["difficulty"], meta["question_sha256"], json.dumps(mode_map, sort_keys=True), json.dumps(meta, sort_keys=True)))
                counts[f"mode_{mode}"] += 1
                if train_seen % 5000 == 0:
                    db.commit()
                    if progress_callback:
                        progress_callback({"member_index": mi, "member_rows": seen, "train_rows": counts["train_rows_scanned"], "elapsed_seconds": round(time.monotonic()-started, 1)})
                    if time.monotonic() - started > time_limit_s:
                        raise TimeoutError("metadata scan exceeded its hard wall-clock budget; no manifest emitted")
            if seen != int(member["rows"]):
                raise ValueError(f"member row count mismatch for {member['file_name']}")
            db.commit()
            counts["members_complete"] += 1
            db.execute("INSERT OR REPLACE INTO scan_state VALUES (?,?,?,1)", (member["sha256"], seen, train_seen))
            db.execute("INSERT OR REPLACE INTO member_scan_state VALUES (?,?,?,?,?,1)",
                       (member_key, seen, train_seen, validation_seen, test_seen))
            db.commit()

        # Fail closed if accepted case modes are not complete. Split totals
        # above are exact; accepted training rows may be fewer only on explicit
        # owner/adjudication rejection, which is surfaced in the receipt.
        incomplete = db.execute("SELECT COUNT(*) FROM cases WHERE eligible=1 AND (SELECT COUNT(*) FROM json_each(cases.modes_json))!=4").fetchone()[0]
        if incomplete:
            raise ValueError(f"{incomplete} eligible cases do not contain all four modes")
        if counts["members_complete"] != len(members):
            raise ValueError("not every declared candidate chat member completed")
        observed_split_counts = {"train": counts["train_rows_scanned"],
            "validation": counts["nontrain_validation"], "test": counts["nontrain_test"]}
        if observed_split_counts != EXPECTED_ROWS:
            raise ValueError(f"candidate split counts differ from pinned release: {observed_split_counts}")
        # Per-mode counts are descriptive; resume may have replayed part of a
        # member before its completion marker. Recompute from canonical cases.
        for mode in MODES:
            counts[f"mode_{mode}"] = int(db.execute(
                "SELECT COUNT(*) FROM cases WHERE eligible=1 AND json_extract(modes_json, ? ) IS NOT NULL",
                ("$." + mode,)).fetchone()[0])

        eligible = int(db.execute("SELECT COUNT(*) FROM cases WHERE eligible=1").fetchone()[0])
        mandatory_sgk = [r[0] for r in db.execute("SELECT case_id FROM cases WHERE eligible=1 AND family LIKE 'sgk_%' ORDER BY case_id")]
        if len(mandatory_sgk) > target_cases:
            raise ValueError("target_cases is below the complete SGK supplemental case count")
        chosen = set(mandatory_sgk)
        # Keep only the best bounded case ranks per stratum in memory. The
        # corpus contains millions of cases, so persisting 4-6M rank rows in
        # SQLite is both unnecessary and extremely slow.
        top_by_label = defaultdict(list)
        for case in db.execute("SELECT case_id,grade,skill,method,difficulty FROM cases WHERE eligible=1"):
            labels = {f"grade:{case['grade']}", f"skill:{case['skill']}",
                      f"method:{case['method']}", f"difficulty:{case['difficulty']}"}
            for label in labels:
                rank = int.from_bytes(hashlib.sha256(f"{seed}\0{label}\0{case['case_id']}".encode()).digest(), "big")
                heap = top_by_label[label]
                item = (-rank, case["case_id"])
                if len(heap) < target_cases:
                    heapq.heappush(heap, item)
                elif item > heap[0]:
                    heapq.heapreplace(heap, item)
        labels = sorted(top_by_label, key=lambda label: (0 if label.startswith("grade:") else 1 if label.startswith("skill:") else 2 if label.startswith("method:") else 3, label))
        ranked = {label: [cid for _, cid in sorted(((-neg_rank, cid) for neg_rank, cid in top_by_label[label]))] for label in labels}
        offsets = {label: 0 for label in labels}
        while len(chosen) < min(target_cases, eligible):
            changed = False
            for label in labels:
                values = ranked[label]
                while offsets[label] < len(values) and values[offsets[label]] in chosen:
                    offsets[label] += 1
                if offsets[label] < len(values):
                    chosen.add(values[offsets[label]]); offsets[label] += 1; changed = True
                    if len(chosen) >= min(target_cases, eligible):
                        break
            if not changed:
                break

        counts_by = {k: Counter() for k in ("grade", "skill", "method", "difficulty", "family")}
        distributions = {k: dict(db.execute(f"SELECT {field},COUNT(*) FROM cases WHERE eligible=1 GROUP BY {field} ORDER BY {field}"))
          for k,field in (("grade","grade"),("skill","skill"),("method_proxy","method"),("difficulty_proxy","difficulty"),("family","family"))}
        selected = []
        for cid in sorted(chosen):
            case = db.execute("SELECT * FROM cases WHERE case_id=? AND eligible=1", (cid,)).fetchone()
            if not case:
                raise ValueError("selected case absent or ineligible")
            for key in counts_by:
                counts_by[key][case[key]] += 1
            selected.append({"case_id": cid, "family": case["family"], "grade": case["grade"],
              "skill": case["skill"], "skill_label_origin": case["skill_origin"],
              "method_proxy": case["method"], "difficulty_proxy": case["difficulty"],
              "question_sha256": case["question_sha256"], "rows": json.loads(case["modes_json"])})
        # Materialize the selected whole-case chat rows remotely. This second
        # pass is over the already hash-verified local archive cache; it never
        # sends row contents back to the controller or writes to Drive.
        selected_rows = {case["case_id"]: case["rows"] for case in selected}
        required_row_hashes = {
            (case_id, mode): info["row_sha256"]
            for case_id, modes in selected_rows.items() for mode, info in modes.items()
        }
        found_row_hashes = set()
        selected_raw_rows = {}
        view_path = work / "training_view.jsonl"
        view_pending = view_path.with_suffix(".pending")
        with view_pending.open("wb") as view_out:
            for member in members:
                if time.monotonic() - started > time_limit_s:
                    raise TimeoutError("selected-row materialization exceeded hard wall-clock budget")
                archive_ref = artifacts[member["sha256"]]
                archive_ref = {**archive_ref, "file_id": member["file_id"]}
                archive_path = _verified_download(api, archive_ref, archive_cache, preexisting_cache_dirs)
                for line in _iter_member_lines(archive_path, member):
                    if not line.strip() or _peek_top_level_split(line) != "train":
                        continue
                    row = json.loads(line)
                    mode = row.get("mode")
                    case_id = row.get("source_sample_id") or row.get("sample_id", "").removesuffix(":" + str(mode))
                    key = (case_id, mode)
                    if key not in required_row_hashes or key in found_row_hashes:
                        continue
                    raw_hash = hashlib.sha256(line.rstrip(b"\r\n")).hexdigest()
                    if raw_hash != required_row_hashes[key]:
                        raise ValueError("selected training row changed since metadata scan")
                    selected_raw_rows.setdefault(case_id, {})[mode] = line.rstrip(b"\r\n")
                    found_row_hashes.add(key)
        if found_row_hashes != set(required_row_hashes):
            view_pending.unlink(missing_ok=True)
            raise ValueError("could not materialize every selected row from the pinned train members")
        # Deterministically shuffle whole cases only after stratification, then
        # keep the four teaching modes contiguous in each case group.
        with view_pending.open("wb") as view_out:
            shuffled_case_ids = sorted(chosen, key=lambda cid: hashlib.sha256(f"{seed}\0case-order\0{cid}".encode()).digest())
            for cid in shuffled_case_ids:
                modes = selected_raw_rows.get(cid, {})
                if set(modes) != set(MODES):
                    raise ValueError("selected case does not have all four raw mode rows")
                for mode in MODES:
                    view_out.write(modes[mode] + b"\n")
        view_pending.replace(view_path)
        manifest = {"schema": "MathVisionKid.t4_stratified_train_view.v1", "seed": seed,
          "recipe_sha256": EXPECTED_RECIPE_SHA, "recipe_identity": EXPECTED_RECIPE_ID,
          "protected_eval_hash_file_sha256": _sha_file(Path(protected_eval_hashes_path)),
          "protected_eval_hash_count": len(blocked), "split": "train",
          "target_cases": target_cases, "eligible_complete_cases": eligible,
          "selected_cases": len(selected), "selected_chat_rows": 4*len(selected),
          "all_four_modes_preserved": True, "members_complete": counts["members_complete"],
          "training_view_jsonl": str(view_path), "training_view_rows": len(found_row_hashes),
          "training_view_sha256": _sha_file(view_path),
          "raw_train_rows_scanned": counts["train_rows_scanned"],
          "by_grade_cases": dict(counts_by["grade"]), "by_skill_cases": dict(counts_by["skill"]),
          "by_method_proxy_cases": dict(counts_by["method"]), "by_difficulty_proxy_cases": dict(counts_by["difficulty"]),
          "by_family_cases": dict(counts_by["family"]),
          "all_eligible_train_case_distributions": distributions,
          "heuristics_are_semantic_QA": False, "source_quality_or_human_review_claim": False,
          "counts": dict(counts), "selected_cases_manifest": selected,
          "elapsed_seconds": round(time.monotonic()-started, 2), "training_started": False,
          "gpu_used": False, "drive_mutated": False, "eval_payload_content_used": False}
        target = work / "training_view_manifest.json"
        temp = target.with_suffix(".pending")
        temp.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2)+"\n", encoding="utf-8")
        temp.replace(target)
        manifest["manifest_sha256"] = _sha_file(target)
        return manifest
    finally:
        db.commit(); db.close()


def load_receipt(path: str | Path) -> dict:
    """Unwrap local list-tools-probe receipt without displaying payload rows."""
    outer = json.loads(Path(path).read_text(encoding="utf-8"))
    for output in outer.get("result", {}).get("outputs", []):
        for text in output.get("text", []):
            if isinstance(text, str):
                parsed = json.loads(text)
                if {"release", "chat_member_metadata", "artifact_metadata"} <= set(parsed):
                    return parsed
    raise ValueError("receipt does not contain pinned sampling metadata")
