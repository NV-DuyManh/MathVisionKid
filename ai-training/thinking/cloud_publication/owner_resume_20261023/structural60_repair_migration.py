"""Offline, fail-closed child-DB migration for the exact structural-60 repair.

No import-time work, network access, connector calls, parent writes, or gate
changes. Callers supply the frozen v3 plan identity/linkage functions.
"""
from contextlib import contextmanager
from dataclasses import dataclass
import gzip
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import zipfile

SCHEMA = "MathVisionKid.structural60_hash_group_repair.v1"
MODES = ("worked_solution", "hint_level_1", "hint_level_2", "hint_level_3")
SEMANTIC_CRITERIA = frozenset({
    "math_independent_oracle", "language_and_grade", "units", "step_reasons_and_checks",
    "evidence_grounded_wrong_work_response", "hint_no_answer_leakage", "split_provenance_and_id",
})
CASE_IDS = frozenset({
    "exhaustive_structure_g2_two_sign_bare_expression",
    "exhaustive_structure_g2_two_sign_arrow_machine",
    "exhaustive_structure_g2_two_sign_equal_value_contrast",
    "exhaustive_structure_g2_two_sign_observed_parentheses_error",
    "exhaustive_structure_g2_two_sign_missing_operator",
    "exhaustive_structure_g4_rectangle_stencil_plan",
    "exhaustive_structure_g4_parallel_guide_plan",
    "exhaustive_structure_g4_cube_frame_assembly_plan",
    "exhaustive_structure_g4_cube_faces_observed_count_error",
    "exhaustive_structure_g4_perpendicular_missing_drawing_guard",
    "exhaustive_structure_g5_grid_trapezoid_plan",
    "exhaustive_structure_g5_grid_parallelogram_transfer",
    "exhaustive_structure_g5_grid_rhombus_reflection",
    "exhaustive_structure_g5_grid_observed_rhombus_criterion_error",
    "exhaustive_structure_g5_grid_missing_picture_guard",
})
KNOWN_ISSUE = ("79765b8281ff64675b4e3826c07b003237875a98d67e898f22f2a4c1f687b0d1",
               1, "SOURCE_SPLIT_MISSING_OR_UNKNOWN", "exhaustive_v1_div_1563_43")
PINNED_OLD_MEMBER_KEY = "a707937c3fa962493d5ec4765d31da22f03a44875bd0b840cb38f610da122641"
ISSUE_COUNTS = {"SOURCE_RAW_HASH_NOT_FOUND": 60,
                "SOURCE_CHAT_LINKAGE_UNVERIFIED": 60,
                "SOURCE_SPLIT_MISSING_OR_UNKNOWN": 1}


@dataclass(frozen=True)
class Bounds:
    source_versions: int = 1_629_906
    chat_rows: int = 6_502_392
    physical_occurrences: int = 6_502_392
    members: int = 251
    member_rows: int = 511_420
    prefix_rows: int = 511_360
    target_rows: int = 60
    sequence_limit: int = 40_960
    expected_old_member_key: str | None = PINNED_OLD_MEMBER_KEY


PRODUCTION_BOUNDS = Bounds()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def content_identity(entry):
    return {k: entry.get(k) for k in
            ("sha256", "bytes", "member", "member_sha256", "member_bytes", "role", "rows")}


def member_key(entry):
    return digest(content_identity(entry))


def _file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _db_fingerprint(path):
    path = Path(path)
    return {p.name: _file_hash(p) for p in
            (path, Path(str(path) + "-wal"), Path(str(path) + "-shm")) if p.exists()}


def _line_hash(raw):
    return hashlib.sha256(raw.removesuffix(b"\n").removesuffix(b"\r")).hexdigest()


@contextmanager
def raw_payload(entry, path):
    """Verify recipe-pinned bytes, then yield decompressed exact JSONL bytes."""
    path = Path(path)
    if path.stat().st_size != entry["bytes"] or _file_hash(path) != entry["sha256"]:
        raise ValueError("outer payload bytes/hash mismatch")
    archive = None
    if entry.get("member"):
        archive = zipfile.ZipFile(path)
        if archive.namelist().count(entry["member"]) != 1:
            archive.close()
            raise ValueError("inner member missing or ambiguous")
        h = hashlib.sha256()
        size = 0
        with archive.open(entry["member"]) as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                h.update(block)
                size += len(block)
        if size != entry.get("member_bytes") or h.hexdigest() != entry.get("member_sha256"):
            archive.close()
            raise ValueError("inner member bytes/hash mismatch")
        binary = archive.open(entry["member"])
        name = entry["member"]
    else:
        binary = path.open("rb")
        name = path.name
    decoded = None
    try:
        if name.casefold().endswith(".gz"):
            decoded = gzip.GzipFile(fileobj=binary, mode="rb")
            yield decoded
        else:
            yield binary
    finally:
        if decoded is not None:
            decoded.close()
        if not binary.closed:
            binary.close()
        if archive is not None:
            archive.close()


def _recipe_replacement(old_recipe, new_recipe, old_key):
    if old_recipe.get("pending_discovery") or new_recipe.get("pending_discovery"):
        raise ValueError("unresolved member discovery")
    if old_recipe.get("source_members") != new_recipe.get("source_members"):
        raise ValueError("source recipe changed")
    old = old_recipe.get("chat_members")
    new = new_recipe.get("chat_members")
    if not isinstance(old, list) or not isinstance(new, list) or len(old) != len(new):
        raise ValueError("chat recipe cardinality changed")
    positions = [i for i, e in enumerate(old) if member_key(e) == old_key]
    if len(positions) != 1:
        raise ValueError("old target member is not unique")
    ix = positions[0]
    new_key = member_key(new[ix])
    if any(old[i] != new[i] for i in range(len(old)) if i != ix):
        raise ValueError("another chat recipe entry changed")
    if old[ix].get("role") != "candidate_chat" or new[ix].get("role") != "candidate_chat":
        raise ValueError("target role changed")
    if old[ix].get("rows") != new[ix].get("rows"):
        raise ValueError("target declared row count changed")
    old_entry, new_entry = old[ix], new[ix]
    if (new_entry.get("member"), new_entry.get("member_sha256"), new_entry.get("member_bytes"),
            new_entry.get("rows"), new_entry.get("role")) != (
            old_entry.get("member"), old_entry.get("member_sha256"), old_entry.get("member_bytes"),
            old_entry.get("rows"), old_entry.get("role")):
        raise ValueError("derived member changed the inner member/row role")
    if new_entry.get("file_id") == old_entry.get("file_id"):
        raise ValueError("derived artifact must have a distinct Drive identity")
    if new_entry.get("family") != "derived_original_chat_structural60_hash_group_repair":
        raise ValueError("derived member family marker mismatch")
    allowed_top = set(old_recipe)
    if set(new_recipe) != allowed_top:
        raise ValueError("recipe top-level fields changed")
    for key in old_recipe:
        if key not in ("chat_members", "artifacts") and old_recipe[key] != new_recipe[key]:
            raise ValueError("unrelated recipe field changed: " + key)
    # Existing artifacts remain byte-for-byte registered; exactly the new shard
    # adds one artifact descriptor.
    old_artifacts, new_artifacts = old_recipe.get("artifacts"), new_recipe.get("artifacts")
    if not isinstance(old_artifacts, dict) or not isinstance(new_artifacts, dict):
        raise ValueError("recipe artifacts map required")
    added = set(new_artifacts) - set(old_artifacts)
    if len(added) != 1 or not set(old_artifacts).issubset(new_artifacts):
        raise ValueError("artifact registry must add exactly one derived artifact")
    if any(new_artifacts[k] != v for k, v in old_artifacts.items()):
        raise ValueError("prior artifact registry entries changed")
    new_sha = new_entry.get("sha256")
    if added != {new_sha}:
        raise ValueError("artifact registry key differs from derived member hash")
    artifact = new_artifacts[new_sha]
    if (artifact.get("sha256"), artifact.get("bytes"), artifact.get("file_ids"), artifact.get("file_names")) != (
            new_entry.get("sha256"), new_entry.get("bytes"), [new_entry.get("file_id")],
            [new_entry.get("file_name")]):
        raise ValueError("new artifact registry entry differs from member")
    return ix, old_entry, new_entry, new_key


def _window(entry, path, bounds):
    prefix_hash = hashlib.sha256()
    rows = []
    count = 0
    with raw_payload(entry, path) as stream:
        for count, raw in enumerate(stream, 1):
            if count <= bounds.prefix_rows:
                prefix_hash.update(raw)
            elif count <= bounds.prefix_rows + bounds.target_rows:
                if not raw.strip():
                    raise ValueError("blank target line")
                row = json.loads(raw.decode("utf-8"))
                if not isinstance(row, dict):
                    raise ValueError("target line must be a JSON object")
                rows.append((count, raw, row))
        if count != entry["rows"]:
            raise ValueError("actual row count differs from recipe")
    if entry["rows"] != bounds.member_rows or len(rows) != bounds.target_rows:
        raise ValueError("member/prefix/target dimensions differ from frozen bounds")
    return prefix_hash.hexdigest(), rows


def _check_semantic_review(review, source_hashes):
    if review.get("schema") != "MathVisionKid.Structural15SemanticReview.v1":
        raise ValueError("semantic review schema mismatch")
    if review.get("overall_semantic_result") != "PASS_WITH_SCOPE_LIMITS":
        raise ValueError("semantic review is not a scoped pass")
    reviewer = review.get("reviewer", {})
    if (reviewer.get("type") != "AI_REVIEWER"
            or reviewer.get("authority") != "OWNER_PREAUTHORIZED"
            or reviewer.get("human_verified") is not False
            or reviewer.get("teacher_certified") is not False
            or reviewer.get("owner_human_reviewed") is not False):
        raise ValueError("semantic reviewer provenance invalid/overstated")
    rows = review.get("rows")
    by_id = {r.get("sample_id"): r for r in rows} if isinstance(rows, list) else {}
    if len(rows or []) != 15 or set(by_id) != CASE_IDS:
        raise ValueError("semantic review must cover exact structural-15 ID set")
    for sid, row in by_id.items():
        raw_sha, canonical_sha = source_hashes[sid]
        if (row.get("current_raw_line_sha256"), row.get("current_canonical_row_sha256")) != (raw_sha, canonical_sha):
            raise ValueError("semantic source hash differs from indexed source: " + sid)
        if set(row.get("checks", {})) != SEMANTIC_CRITERIA:
            raise ValueError("semantic review criteria set incomplete: " + sid)
        if any(result.get("status") not in ("PASS", "NOT_APPLICABLE")
               for result in row.get("checks", {}).values()):
            raise ValueError("semantic review has failed or unknown check: " + sid)


def _parent_issue_proof(db, old_key, old_rows, bounds):
    counts = dict(db.execute("SELECT kind,count(*) FROM issues GROUP BY kind"))
    if counts != ISSUE_COUNTS:
        raise ValueError("parent issue counts differ from exact diagnosed state")
    if db.execute("SELECT member,line,kind,detail FROM issues WHERE kind='SOURCE_SPLIT_MISSING_OR_UNKNOWN'").fetchall() != [KNOWN_ISSUE]:
        raise ValueError("known unrelated issue changed")
    found = db.execute("SELECT line,kind,detail FROM issues WHERE member=? ORDER BY line,kind,detail",
                       (old_key,)).fetchall()
    expected = sorted((line, kind, row.get("source_sample_id") or row["sample_id"].rsplit(":", 1)[0])
                      for line, _, row in old_rows
                      for kind in ("SOURCE_RAW_HASH_NOT_FOUND", "SOURCE_CHAT_LINKAGE_UNVERIFIED"))
    if found != expected or len(expected) != bounds.target_rows * 2:
        raise ValueError("target member has unexpected issue rows")


def prepare_migration(parent_database, destination_database, old_recipe, new_recipe,
                      semantic_review, repair_receipt, old_payload_path, new_payload_path,
                      *, plan_identity, linkage_errors, parent_recipe_sha256,
                      semantic_review_bytes, repair_receipt_bytes,
                      bounds=PRODUCTION_BOUNDS):
    """Back up a complete parent into a separate child and requeue only exact 60.

    Repair receipt shape is documented in the returned file's module docstring
    below and checked against the actual old/new payload bytes and source index.
    """
    parent_path, child_path = Path(parent_database), Path(destination_database)
    if parent_path.resolve() == child_path.resolve():
        raise ValueError("child database must be separate from parent")
    if child_path.exists():
        raise FileExistsError("child destination already exists")
    if repair_receipt.get("schema") != SCHEMA:
        raise ValueError("repair receipt schema mismatch")
    if repair_receipt.get("changed_fields") != ["case_group_id", "source_row_sha256"]:
        raise ValueError("only source_row_sha256 and case_group_id may change")
    old_identity, new_identity = plan_identity(old_recipe), plan_identity(new_recipe)
    if repair_receipt.get("parent_recipe_identity") != old_identity:
        raise ValueError("repair receipt parent recipe identity mismatch")
    if repair_receipt.get("parent_recipe_sha256") != parent_recipe_sha256:
        raise ValueError("repair receipt parent recipe bytes hash mismatch")
    if hashlib.sha256(semantic_review_bytes).hexdigest() != repair_receipt.get("semantic_qa_sha256"):
        raise ValueError("semantic QA file hash mismatch")
    if repair_receipt.get("messages_answers_hints_unchanged") is not True:
        raise ValueError("repair receipt does not prove message/answer/hint preservation")
    if repair_receipt.get("source_rows_modified") is not False or repair_receipt.get("human_signoffs_created") != 0:
        raise ValueError("source rows or human-signoff history was altered")
    if repair_receipt.get("parent_original_preserved") is not True or repair_receipt.get("training_started") is not False:
        raise ValueError("repair receipt preservation/training provenance invalid")
    if repair_receipt.get("merged_or_published") is not False:
        raise ValueError("repair receipt claims publication/merge before migration")
    old_key = repair_receipt.get("parent_entry", {}).get("sha256")
    # The receipt's parent entry carries artifact content identity; the unique
    # recipe key is matched below from the known original file descriptor.
    candidates = [e for e in old_recipe["chat_members"]
                  if e.get("file_name") == repair_receipt.get("parent_entry", {}).get("file_name")
                  and e.get("sha256") == old_key]
    if len(candidates) != 1:
        raise ValueError("receipt parent entry is not unique in parent recipe")
    old_key = member_key(candidates[0])
    index, old_entry, new_entry, new_key = _recipe_replacement(old_recipe, new_recipe, old_key)
    if bounds.expected_old_member_key and old_key != bounds.expected_old_member_key:
        raise ValueError("target member is not the pinned original chat shard 7")
    if "MathVisionKid_CHAT_part_07_of_07" not in str(old_entry.get("file_name", "")):
        raise ValueError("old member filename is not the pinned shard 7")
    if old_key != member_key(old_entry) or new_key != member_key(new_entry):
        raise ValueError("receipt member keys differ from recipes")
    if repair_receipt.get("parent_entry") != old_entry:
        raise ValueError("receipt parent member descriptor differs from parent recipe")
    if (repair_receipt.get("prefix_rows_unchanged"), repair_receipt.get("changed_chat_rows"),
            repair_receipt.get("case_ids")) != (bounds.prefix_rows, bounds.target_rows, len(CASE_IDS)):
        raise ValueError("receipt row window differs from frozen bounds")
    if repair_receipt.get("changed_fields") != ["case_group_id", "source_row_sha256"]:
        raise ValueError("receipt change set differs from exact two metadata fields")
    derived_file = repair_receipt.get("derived_file", {})
    if (derived_file.get("sha256"), derived_file.get("bytes"), derived_file.get("rows"),
            derived_file.get("name")) != (new_entry.get("sha256"), new_entry.get("bytes"),
                                          bounds.member_rows, new_entry.get("file_name")):
        raise ValueError("derived artifact descriptor differs from new recipe member")
    if json.loads(repair_receipt_bytes.decode("utf-8")) != repair_receipt:
        raise ValueError("repair receipt bytes do not encode supplied receipt")
    old_prefix, old_rows = _window(old_entry, old_payload_path, bounds)
    new_prefix, new_rows = _window(new_entry, new_payload_path, bounds)
    if old_prefix != new_prefix:
        raise ValueError("raw byte stream prefix changed")
    if (repair_receipt.get("prefix_bytes_sha256"), repair_receipt.get("derived_prefix_bytes_sha256")) != (old_prefix, new_prefix):
        raise ValueError("receipt prefix hash proof mismatch")
    proofs = repair_receipt.get("rows")
    if not isinstance(proofs, list) or len(proofs) != bounds.target_rows:
        raise ValueError("receipt must contain exact per-row proof set")
    by_line = {proof.get("line"): proof for proof in proofs}
    expected_lines = set(range(bounds.prefix_rows + 1, bounds.member_rows + 1))
    if len(by_line) != bounds.target_rows or set(by_line) != expected_lines:
        raise ValueError("repair proof line set mismatch")

    parent_before = _db_fingerprint(parent_path)
    if not parent_before:
        raise ValueError("parent database not found")
    child_path.parent.mkdir(parents=True, exist_ok=True)
    temp = child_path.with_name(child_path.name + ".building")
    if temp.exists():
        raise FileExistsError("temporary child path already exists")
    parent = sqlite3.connect(f"file:{parent_path.as_posix()}?mode=ro", uri=True, timeout=60)
    parent.execute("PRAGMA query_only=ON")
    child = sqlite3.connect(temp, timeout=60)
    try:
        parent.backup(child)
        config = child.execute("SELECT identity,sequence_limit FROM config").fetchone()
        if config != (old_identity, bounds.sequence_limit):
            raise ValueError("parent immutable identity/sequence limit mismatch")
        counts = {t: child.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
                  for t in ("source_versions", "samples", "occurrences", "members")}
        if counts != {"source_versions": bounds.source_versions, "samples": bounds.chat_rows,
                      "occurrences": bounds.physical_occurrences, "members": bounds.members}:
            raise ValueError("parent database counts mismatch")
        expected_members = {member_key(e): (e["role"], e["rows"])
                            for e in old_recipe["source_members"] + old_recipe["chat_members"]}
        actual_members = {key: (role, rows) for key, role, _, complete, rows in
                          child.execute("SELECT id,role,next_line,complete,expected_rows FROM members")
                          if complete == 1 and _ == rows}
        if len(expected_members) != bounds.members or actual_members != expected_members:
            raise ValueError("parent members are not all complete at their exact declared cursors")
        member = child.execute("SELECT role,next_line,complete,expected_rows FROM members WHERE id=?",
                               (old_key,)).fetchone()
        if member != ("candidate_chat", bounds.member_rows, 1, bounds.member_rows):
            raise ValueError("old target member cursor is not complete at exact EOF")
        _parent_issue_proof(child, old_key, old_rows, bounds)

        sources = {}
        for sid in CASE_IDS:
            found = child.execute("SELECT raw_sha,canonical_sha,projection,source_split FROM source_versions WHERE id=?",
                                  (sid,)).fetchall()
            if len(found) != 1:
                raise ValueError("approved source not unique: " + sid)
            raw_sha, canonical_sha, projection_text, split = found[0]
            projection = json.loads(projection_text)
            if split != "train" or not projection.get("case_group_id"):
                raise ValueError("approved source split/group mismatch: " + sid)
            sources[sid] = (raw_sha, canonical_sha, projection)
        _check_semantic_review(semantic_review, {sid: (x[0], x[1]) for sid, x in sources.items()})
        target_samples, target_occurrences = [], []
        modes = {}
        checked_lines = []
        for old_item, new_item in zip(old_rows, new_rows):
            old_line, old_raw, old_row = old_item
            new_line, new_raw, new_row = new_item
            if old_line != new_line:
                raise ValueError("old/new row line alignment changed")
            proof = by_line[old_line]
            sid = new_row.get("sample_id")
            case_id = new_row.get("source_sample_id") or sid.rsplit(":", 1)[0]
            if case_id not in CASE_IDS or case_id not in sources:
                raise ValueError("row references unapproved source")
            raw_sha, canonical_sha, projection = sources[case_id]
            changed = sorted(k for k in old_row.keys() | new_row.keys() if old_row.get(k) != new_row.get(k))
            if changed != ["case_group_id", "source_row_sha256"]:
                raise ValueError(f"row {old_line} changed fields outside exact metadata pair: {changed}")
            old_raw_sha, new_raw_sha = _line_hash(old_raw), _line_hash(new_raw)
            old_can, new_can = digest(old_row), digest(new_row)
            if (old_row.get("source_row_sha256") != canonical_sha
                    or old_row.get("row_sha256") != canonical_sha
                    or new_row.get("row_sha256") != canonical_sha
                    or new_row.get("source_row_sha256") != raw_sha
                    or new_row.get("case_group_id") != projection["case_group_id"]):
                raise ValueError("source raw/canonical/group binding does not match indexed source")
            if new_row.get("split") != "train" or new_row.get("mode") not in MODES:
                raise ValueError("new row split or mode invalid")
            old_errors = linkage_errors(old_row, projection)
            if old_errors != ["case_group_id"]:
                raise ValueError("old row did not have the exact diagnosed group-only linkage failure")
            errors = linkage_errors(new_row, projection)
            if errors:
                raise ValueError("original frozen linkage gates fail: " + repr(errors))
            expected_proof = {
                "line": old_line, "sample_id": sid, "case_id": case_id, "mode": new_row["mode"],
                "old_raw_sha256": old_raw_sha, "new_raw_sha256": new_raw_sha,
                "old_canonical_sha256": old_can, "new_canonical_sha256": new_can,
                "changed_fields": ["case_group_id", "source_row_sha256"],
                "old_case_group_id": old_row.get("case_group_id"),
                "new_case_group_id": new_row.get("case_group_id"),
                "old_source_row_sha256": old_row.get("source_row_sha256"),
                "new_source_row_sha256": new_row.get("source_row_sha256"),
                "source_canonical_sha256": canonical_sha,
                "messages_sha256": digest(old_row["messages"]),
                "full_projection_match_after_repair": True,
            }
            for key, val in expected_proof.items():
                if proof.get(key) != val:
                    raise ValueError(f"row proof mismatch at line {old_line}, field {key}")
            modes.setdefault(case_id, []).append(new_row["mode"])
            sample = child.execute("SELECT * FROM samples WHERE id=?", (sid,)).fetchone()
            occurrence = child.execute("SELECT * FROM occurrences WHERE member=? AND line=?",
                                        (old_key, old_line)).fetchone()
            if sample is None or occurrence is None:
                raise ValueError("old target sample/occurrence missing")
            if (sample[1], sample[2], sample[3], sample[4], sample[5], sample[6]) != (
                    old_can, case_id, new_row["mode"], "train", None, 0):
                raise ValueError("old sample differs from source chat or unlinked state")
            if (occurrence[2], occurrence[3], occurrence[4]) != (
                    sid, old_raw_sha, "CURRENT_CANDIDATE"):
                raise ValueError("old physical occurrence differs from old payload")
            target_samples.append(sample)
            target_occurrences.append(occurrence)
            checked_lines.append(old_line)
        if set(modes) != CASE_IDS or any(sorted(v) != sorted(MODES) or len(v) != 4 for v in modes.values()):
            raise ValueError("must be exact 15 cases with four modes each")
        if repair_receipt.get("changed_chat_rows") != bounds.target_rows:
            raise ValueError("receipt target row count mismatch")
        if repair_receipt.get("parent_database_sha256") not in (None, _file_hash(parent_path)):
            raise ValueError("parent DB hash in receipt mismatch")

        migration_id = digest({"old_identity": old_identity, "new_identity": new_identity,
                               "old_member": old_key, "new_member": new_key,
                               "receipt": digest(repair_receipt)})
        with child:
            child.executescript("""
                CREATE TABLE IF NOT EXISTS structural60_sample_history(
                  migration_id TEXT,id TEXT,canonical_sha TEXT,case_id TEXT,mode TEXT,split TEXT,
                  source_raw_sha TEXT,linkage INTEGER,raw_hash_origin TEXT,sequence_tokens INTEGER,completion_tokens INTEGER);
                CREATE TABLE IF NOT EXISTS structural60_occurrence_history(
                  migration_id TEXT,member TEXT,line INTEGER,sample_id TEXT,raw_sha TEXT,kind TEXT);
                CREATE TABLE IF NOT EXISTS structural60_issue_history(
                  migration_id TEXT,member TEXT,line INTEGER,kind TEXT,detail TEXT);
                CREATE TABLE IF NOT EXISTS structural60_migration_history(
                  migration_id TEXT PRIMARY KEY,parent_identity TEXT,child_identity TEXT,
                  old_member TEXT,new_member TEXT,receipt TEXT);
                CREATE TABLE IF NOT EXISTS recipe_history(
                  previous_identity TEXT,next_identity TEXT,PRIMARY KEY(previous_identity,next_identity));
            """)
            child.executemany("INSERT INTO structural60_issue_history VALUES (?,?,?,?,?)",
                [(migration_id, *r) for r in child.execute("SELECT member,line,kind,detail FROM issues").fetchall()])
            child.executemany("INSERT INTO structural60_sample_history VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                [(migration_id, *r) for r in target_samples])
            child.executemany("INSERT INTO structural60_occurrence_history VALUES (?,?,?,?,?,?)",
                [(migration_id, *r) for r in target_occurrences])
            child.execute("INSERT INTO structural60_migration_history VALUES (?,?,?,?,?,?)",
                (migration_id, old_identity, new_identity, old_key, new_key, canonical(repair_receipt)))
            child.execute("INSERT INTO recipe_history VALUES (?,?)", (old_identity, new_identity))
            child.executemany("DELETE FROM samples WHERE id=?", [(r[0],) for r in target_samples])
            child.executemany("DELETE FROM occurrences WHERE member=? AND line=?",
                              [(old_key, r[1]) for r in target_occurrences])
            child.executemany("DELETE FROM issues WHERE member=? AND line=? AND kind IN (?,?)",
                [(old_key, line, "SOURCE_RAW_HASH_NOT_FOUND", "SOURCE_CHAT_LINKAGE_UNVERIFIED")
                 for line in checked_lines])
            child.execute("UPDATE occurrences SET member=? WHERE member=?", (new_key, old_key))
            child.execute("UPDATE issues SET member=? WHERE member=?", (new_key, old_key))
            child.execute("UPDATE members SET id=?,next_line=?,complete=0,expected_rows=? WHERE id=?",
                          (new_key, bounds.prefix_rows, bounds.member_rows, old_key))
            child.execute("UPDATE config SET identity=? WHERE identity=?", (new_identity, old_identity))
        if child.execute("SELECT count(*) FROM samples").fetchone()[0] != bounds.chat_rows - bounds.target_rows:
            raise ValueError("child removed a non-exact number of samples")
        if child.execute("SELECT count(*) FROM occurrences").fetchone()[0] != bounds.physical_occurrences - bounds.target_rows:
            raise ValueError("child removed a non-exact number of occurrences")
        if child.execute("SELECT count(*) FROM structural60_sample_history WHERE migration_id=?",
                         (migration_id,)).fetchone()[0] != bounds.target_rows:
            raise ValueError("child sample history incomplete")
        if child.execute("SELECT count(*) FROM structural60_occurrence_history WHERE migration_id=?",
                         (migration_id,)).fetchone()[0] != bounds.target_rows:
            raise ValueError("child occurrence history incomplete")
        if child.execute("SELECT count(*) FROM structural60_issue_history WHERE migration_id=?",
                         (migration_id,)).fetchone()[0] != sum(ISSUE_COUNTS.values()):
            raise ValueError("parent issue history incomplete")
        if child.execute("SELECT member,line,kind,detail FROM issues").fetchall() != [KNOWN_ISSUE]:
            raise ValueError("child must retain only the one known unrelated issue before re-audit")
        if child.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise ValueError("child quick_check failed")
        child.commit()
        child.close()
        parent.close()
        if _db_fingerprint(parent_path) != parent_before:
            raise ValueError("parent bytes changed")
        os.replace(temp, child_path)
    except Exception:
        child.close()
        parent.close()
        if temp.exists():
            temp.unlink()
        raise
    return {"migration_id": migration_id, "destination": str(child_path),
            "old_identity": old_identity, "new_identity": new_identity,
            "old_member_key": old_key, "new_member_key": new_key,
            "prefix_rows_preserved": bounds.prefix_rows, "target_rows_requeued": bounds.target_rows,
            "parent_database_unchanged": True, "parent_issues_archived": sum(ISSUE_COUNTS.values()),
            "target_samples_archived": bounds.target_rows, "target_occurrences_archived": bounds.target_rows,
            "training_started": False, "raw_gate_bypassed": False}


def verify_finalized(auditor, migration_id, *, bounds=PRODUCTION_BOUNDS):
    """Verify frozen v3 consume completed the repaired member and report remains honest."""
    db = auditor.db
    report = auditor.report()
    counts = {t: db.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
              for t in ("source_versions", "samples", "occurrences", "members")}
    if counts != {"source_versions": bounds.source_versions, "samples": bounds.chat_rows,
                  "occurrences": bounds.physical_occurrences, "members": bounds.members}:
        raise ValueError("final ledger counts mismatch")
    if db.execute("SELECT count(*) FROM members WHERE complete=1").fetchone()[0] != bounds.members:
        raise ValueError("not all members complete")
    migration = db.execute("SELECT old_member,new_member FROM structural60_migration_history WHERE migration_id=?",
                           (migration_id,)).fetchone()
    if migration is None:
        raise ValueError("migration history missing")
    old_key, new_key = migration
    if db.execute("SELECT count(*) FROM occurrences WHERE member=?", (old_key,)).fetchone()[0]:
        raise ValueError("old target occurrences remain active")
    if db.execute("SELECT next_line,complete,expected_rows FROM members WHERE id=?", (new_key,)).fetchone() != (
            bounds.member_rows, 1, bounds.member_rows):
        raise ValueError("new member was not consumed to exact EOF")
    targets = db.execute("""SELECT s.id,s.linkage,s.source_raw_sha,s.sequence_tokens,s.completion_tokens,
                                   o.line
                            FROM samples s JOIN occurrences o ON o.sample_id=s.id
                            WHERE o.member=? AND o.kind='CURRENT_CANDIDATE' AND o.line>?
                            ORDER BY o.line""", (new_key, bounds.prefix_rows)).fetchall()
    if len(targets) != bounds.target_rows or any(not x[1] or x[2] is None for x in targets):
        raise ValueError("re-audited rows are missing or unlinked")
    old_tokens = {r[0]: (r[1], r[2]) for r in db.execute(
        "SELECT id,sequence_tokens,completion_tokens FROM structural60_sample_history WHERE migration_id=?",
        (migration_id,))}
    for row in targets:
        if old_tokens.get(row[0]) != (row[3], row[4]):
            raise ValueError("token counts changed across metadata-only repair")
    if db.execute("SELECT member,line,kind,detail FROM issues").fetchall() != [KNOWN_ISSUE]:
        raise ValueError("final active issue set changed")
    if (report.get("unique_chat_rows_processed") != bounds.chat_rows
            or report.get("physical_chat_occurrences_processed") != bounds.physical_occurrences
            or report.get("source_linkage_unverified_rows") != 0
            or report.get("incomplete_four_mode_cases") != 0):
        raise ValueError("final v3 report totals/linkage are not exact")
    if (report.get("TRAINING_DATASET_READY") is not False
            or report.get("full_archive_token_linkage_split_audit_complete") is not False
            or report.get("training_started") is not False
            or report.get("gpu_used") is not False
            or report.get("model_weights_loaded") is not False):
        raise ValueError("final report overstates readiness or changes audit provenance")
    return {"status": "PASS_REAUDIT_COMPLETE_WITH_ONE_KNOWN_ISSUE",
            "report": report, "repaired_rows": bounds.target_rows,
            "token_lengths_preserved": True, "TRAINING_DATASET_READY": False,
            "full_archive_token_linkage_split_audit_complete": False}
