"""Fail-closed, offline child-database migration for the exact structural-15 adapter.

This migration preserves every original corpus member and byte.  It archives the
parent state, installs hash-pinned source read-time projections for 15 source
IDs, and removes only the 60 original chat ledger rows so the caller can consume
the original cached shard through its frozen auditor.
"""
from contextlib import closing
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import sqlite3

SCHEMA = "MathVisionKid.structural15_exact_adapter_migration.v1"
ADAPTER_KIND = "EXACT_STRUCTURAL15_NEUTRAL_EXPORT_BINDING_V1"
SEMANTIC_SCHEMA = "MathVisionKid.Structural15SemanticReview.v1"
SOURCE_INDEX_IDENTITY = "f0332df91020ace0fc48d88491fe97364d08826458d08c71ba4ec60524e25863"
OLD_CHAT_MEMBER = "a707937c3fa962493d5ec4765d31da22f03a44875bd0b840cb38f610da122641"
KNOWN_ISSUE = ("79765b8281ff64675b4e3826c07b003237875a98d67e898f22f2a4c1f687b0d1",
               1, "SOURCE_SPLIT_MISSING_OR_UNKNOWN", "exhaustive_v1_div_1563_43")
ISSUE_COUNTS = {"SOURCE_RAW_HASH_NOT_FOUND": 60,
                "SOURCE_CHAT_LINKAGE_UNVERIFIED": 60,
                "SOURCE_SPLIT_MISSING_OR_UNKNOWN": 1}
MODES = {"worked_solution", "hint_level_1", "hint_level_2", "hint_level_3"}
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
SEMANTIC_CRITERIA = frozenset({
    "math_independent_oracle", "language_and_grade", "units", "step_reasons_and_checks",
    "evidence_grounded_wrong_work_response", "hint_no_answer_leakage", "split_provenance_and_id",
})


@dataclass(frozen=True)
class Bounds:
    source_versions: int = 1_629_906
    samples: int = 6_502_392
    occurrences: int = 6_502_392
    members: int = 251
    target_cases: int = 15
    target_rows: int = 60
    old_member_rows: int = 511_420
    old_prefix_rows: int = 511_360
    sequence_limit: int = 40_960
    source_index_identity: str = SOURCE_INDEX_IDENTITY
    old_chat_member: str = OLD_CHAT_MEMBER


PRODUCTION_BOUNDS = Bounds()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


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


def _member_key(entry):
    identity = {k: entry.get(k) for k in
                ("sha256", "bytes", "member", "member_sha256", "member_bytes", "role", "rows")}
    return digest(identity)


def _read_bindings(bindings):
    """Accept the documented compact shape and fail closed on duplicate IDs/lines.

    Expected keys: schema, source_index_identity, chat_member_key, sources and
    chat_rows. Each source carries sample_id/raw_sha256/canonical_sha256 and
    adapter_projection. Each chat row carries line/sample_id/case_id/mode and
    chat_raw_sha256/chat_canonical_sha256.
    """
    if bindings.get("schema") != "MathVisionKid.Structural15ExactReadTimeBindings.v1":
        raise ValueError("bindings schema mismatch")
    sources = bindings.get("source_rows")
    if not isinstance(sources, dict):
        raise ValueError("bindings must include source_rows mapping")
    by_source = sources
    by_line = {}
    for sid, source in sources.items():
        if not isinstance(source, dict) or not isinstance(source.get("chats"), dict):
            raise ValueError("source binding missing chat modes: " + sid)
        for mode, chat in source["chats"].items():
            row = dict(chat, case_id=sid, mode=mode)
            # Binding file lists rows in natural line order; the source/case order
            # is not used to infer lines. Recover them from the pinned crosswalk.
            row["line"] = chat.get("line")
            if row["line"] is None:
                raise ValueError("chat binding missing exact member line: " + sid)
            row["chat_raw_sha256"] = chat.get("raw_sha256")
            row["chat_canonical_sha256"] = chat.get("canonical_sha256")
            by_line[row["line"]] = row
    if len(by_source) != len(sources) or set(by_source) != CASE_IDS:
        raise ValueError("bindings must name exactly 15 unique source IDs")
    if len(by_line) != 60:
        raise ValueError("bindings must name exactly 60 unique chat lines")
    if bindings.get("parent_audit_identity") != SOURCE_INDEX_IDENTITY:
        raise ValueError("bindings source index identity mismatch")
    if bindings.get("chat_member_key") != OLD_CHAT_MEMBER:
        raise ValueError("bindings do not pin original chat shard 7")
    if (bindings.get("normalized_chat_groups_preserved") is not True
            or bindings.get("corpus_rows_changed") != 0
            or bindings.get("human_signoffs_created") != 0
            or any(not r.get("builder_replay_full_messages_verified") for r in by_source.values())):
        raise ValueError("bindings do not prove unchanged corpus and full message replay")
    modes = {}
    for row in by_line.values():
        sid = row.get("case_id")
        if sid not in by_source or row.get("mode") not in MODES:
            raise ValueError("chat binding has unknown source or mode")
        modes.setdefault(sid, []).append(row["mode"])
        if row.get("sample_id") != sid + ":" + row["mode"]:
            raise ValueError("chat sample ID does not match case ID and mode")
    if set(modes) != set(by_source) or any(set(v) != MODES or len(v) != 4 for v in modes.values()):
        raise ValueError("bindings must cover four distinct modes for each exact source")
    return by_source, by_line


def _check_semantic_review(review, source_rows):
    if review.get("schema") != SEMANTIC_SCHEMA or review.get("overall_semantic_result") != "PASS_WITH_SCOPE_LIMITS":
        raise ValueError("semantic review schema/result mismatch")
    reviewer = review.get("reviewer", {})
    if (reviewer.get("type") != "AI_REVIEWER" or reviewer.get("authority") != "OWNER_PREAUTHORIZED"
            or reviewer.get("human_verified") is not False
            or reviewer.get("teacher_certified") is not False
            or reviewer.get("owner_human_reviewed") is not False):
        raise ValueError("semantic review provenance is invalid or overclaimed")
    rows = review.get("rows")
    by_id = {r.get("sample_id"): r for r in rows} if isinstance(rows, list) else {}
    if len(by_id) != 15 or set(by_id) != set(source_rows):
        raise ValueError("semantic review must cover the exact 15 source IDs")
    for sid, row in by_id.items():
        source = source_rows[sid]
        raw = source.get("source_raw_sha256")
        can = source.get("source_canonical_sha256")
        if (row.get("current_raw_line_sha256"), row.get("current_canonical_row_sha256")) != (raw, can):
            raise ValueError("semantic review source hashes differ from bindings: " + sid)
        checks = row.get("checks", {})
        if set(checks) != SEMANTIC_CRITERIA or any(
                result.get("status") not in ("PASS", "NOT_APPLICABLE") for result in checks.values()):
            raise ValueError("semantic review criteria incomplete or failed: " + sid)


def _verify_recipe_identity(old_recipe, new_recipe):
    if old_recipe != new_recipe:
        raise ValueError("derived plan must retain the exact frozen corpus recipe")
    if old_recipe.get("source_members") != new_recipe.get("source_members"):
        raise ValueError("source recipe/member bytes changed")
    if old_recipe.get("chat_members") != new_recipe.get("chat_members"):
        raise ValueError("chat recipe/member bytes changed")
    if old_recipe.get("artifacts") != new_recipe.get("artifacts"):
        raise ValueError("artifact registry changed")


def prepare_migration(parent_database, destination_database, old_recipe, new_recipe,
                      bindings, semantic_review, *, parent_identity, child_identity,
                      bindings_bytes=None, expected_bindings_sha256=None,
                      semantic_review_bytes=None, parent_auditor_sha256=None,
                      recipe_sha256=None,
                      bounds=PRODUCTION_BOUNDS):
    """Copy a frozen parent DB into a new child and requeue exactly 60 original rows.

    The actual adapter projection is the exact frozen parent projection with only
    `case_group_id` changed to the builder-replayed chat group.
    """
    parent_path, child_path = Path(parent_database), Path(destination_database)
    if parent_path.resolve() == child_path.resolve():
        raise ValueError("destination must be a separate child database")
    if child_path.exists():
        raise FileExistsError(child_path)
    _verify_recipe_identity(old_recipe, new_recipe)
    if bounds.old_member_rows == PRODUCTION_BOUNDS.old_member_rows:
        recipe_members = old_recipe.get("source_members", []) + old_recipe.get("chat_members", [])
        if sum(_member_key(entry) == bounds.old_chat_member for entry in recipe_members) != 1:
            raise ValueError("frozen recipe does not uniquely pin original chat shard 7")
    old_identity, new_identity = parent_identity, child_identity
    if old_identity == new_identity:
        raise ValueError("child adapter identity must differ from parent identity")
    if old_identity != bindings.get("parent_audit_identity"):
        raise ValueError("parent identity differs from exact bindings")
    source_bindings, chat_bindings = _read_bindings(bindings)
    _check_semantic_review(semantic_review, source_bindings)
    if bindings_bytes is not None and json.loads(bindings_bytes.decode("utf-8")) != bindings:
        raise ValueError("bindings bytes do not encode supplied binding object")
    if semantic_review_bytes is not None and json.loads(semantic_review_bytes.decode("utf-8")) != semantic_review:
        raise ValueError("semantic review bytes differ from supplied object")
    if semantic_review_bytes is None or hashlib.sha256(semantic_review_bytes).hexdigest() != bindings.get("semantic_review_sha256"):
        raise ValueError("semantic review bytes hash differs from binding pin")
    if bindings_bytes is None or expected_bindings_sha256 is None:
        raise ValueError("exact binding file bytes and caller-pinned SHA-256 are required")
    if hashlib.sha256(bindings_bytes).hexdigest() != expected_bindings_sha256:
        raise ValueError("bindings bytes hash differs from caller-pinned binding hash")
    if parent_auditor_sha256 is None or parent_auditor_sha256 != bindings.get("parent_auditor_sha256"):
        raise ValueError("parent auditor source hash pin mismatch")
    if recipe_sha256 is None or recipe_sha256 != bindings.get("recipe_sha256"):
        raise ValueError("frozen recipe hash pin mismatch")
    parent_before = _db_fingerprint(parent_path)
    if not parent_before:
        raise FileNotFoundError(parent_path)
    child_path.parent.mkdir(parents=True, exist_ok=True)
    temp = child_path.with_name(child_path.name + ".building")
    if temp.exists():
        raise FileExistsError(temp)
    parent = sqlite3.connect(f"file:{parent_path.as_posix()}?mode=ro", uri=True, timeout=60)
    parent.execute("PRAGMA query_only=ON")
    child = sqlite3.connect(temp, timeout=60)
    try:
        parent.backup(child)
        config = child.execute("SELECT identity,sequence_limit FROM config").fetchone()
        if config != (old_identity, bounds.sequence_limit):
            raise ValueError("parent identity or frozen sequence limit mismatch")
        counts = {t: child.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
                  for t in ("source_versions", "samples", "occurrences", "members")}
        expected = {"source_versions": bounds.source_versions, "samples": bounds.samples,
                    "occurrences": bounds.occurrences, "members": bounds.members}
        if counts != expected:
            raise ValueError("parent ledger counts differ from frozen checkpoint")
        members = {r[0]: (r[1], r[2], r[3], r[4]) for r in child.execute(
            "SELECT id,role,next_line,complete,expected_rows FROM members")}
        if len(members) != bounds.members:
            raise ValueError("parent member cardinality mismatch")
        if bounds.old_member_rows == PRODUCTION_BOUNDS.old_member_rows:
            expected_members = {_member_key(row): (row["role"], row["rows"])
                                for row in recipe_members}
            actual_members = {member: (role, rows) for member, (role, next_line, complete, rows)
                              in members.items() if complete == 1 and next_line == rows}
            if len(expected_members) != bounds.members or actual_members != expected_members:
                raise ValueError("parent member set/cursors differ from complete frozen recipe")
        if members.get(bounds.old_chat_member) != ("candidate_chat", bounds.old_member_rows, 1, bounds.old_member_rows):
            raise ValueError("original chat member cursor is not complete at frozen EOF")
        if bindings.get("chat_member_key") != bounds.old_chat_member:
            raise ValueError("chat member key differs from frozen target")
        expected_lines = set(range(bounds.old_prefix_rows + 1, bounds.old_member_rows + 1))
        if set(chat_bindings) != expected_lines:
            raise ValueError("binding lines do not match the exact original final-60 window")
        if (bindings.get("first_target_line"), bindings.get("last_target_line")) != (
                bounds.old_prefix_rows + 1, bounds.old_member_rows):
            raise ValueError("binding declared line window differs from frozen target")
        active_issues = dict(child.execute("SELECT kind,count(*) FROM issues GROUP BY kind"))
        if active_issues != ISSUE_COUNTS:
            raise ValueError("parent issue counts differ from diagnosed state")
        if child.execute("SELECT member,line,kind,detail FROM issues WHERE kind=?",
                         ("SOURCE_SPLIT_MISSING_OR_UNKNOWN",)).fetchall() != [KNOWN_ISSUE]:
            raise ValueError("known unrelated split issue changed")

        source_old = {}
        for sid, binding in source_bindings.items():
            found = child.execute("SELECT raw_sha,canonical_sha,projection,signatures,source_split,"
                                  "original_source_sha,adapter_kind,verification_digest "
                                  "FROM source_versions WHERE id=?", (sid,)).fetchall()
            if len(found) != 1:
                raise ValueError("source ID must identify one parent source version: " + sid)
            raw_sha, canonical_sha, projection_text, signatures, split, original_sha, kind, verification = found[0]
            if (raw_sha, canonical_sha) != (binding["source_raw_sha256"], binding["source_canonical_sha256"]):
                raise ValueError("source hash binding mismatch: " + sid)
            old_projection = json.loads(projection_text)
            if digest(old_projection) != binding.get("source_projection_sha256"):
                raise ValueError("frozen parent projection digest mismatch: " + sid)
            if binding.get("verification_digest") != digest({}):
                raise ValueError("adapter verification digest is not the frozen empty digest: " + sid)
            desired = dict(old_projection)
            desired["case_group_id"] = binding["chat_group_id"]
            if not isinstance(desired, dict) or not desired.get("case_group_id"):
                raise ValueError("adapter projection missing canonical case group: " + sid)
            if binding.get("adapted_projection_sha256") != digest(desired):
                raise ValueError("adapter projection digest mismatch: " + sid)
            if (split != "train" or binding.get("source_split") != split
                    or old_projection.get("case_group_id") != binding.get("source_group_id")):
                raise ValueError("source split/group not eligible for projection: " + sid)
            source_old[sid] = (raw_sha, canonical_sha, projection_text, signatures, split,
                               original_sha, kind, verification)

        target_rows = []
        for line, binding in sorted(chat_bindings.items()):
            if not bounds.old_prefix_rows < line <= bounds.old_member_rows:
                raise ValueError("target line is outside pinned final 60-row window")
            sid = binding["sample_id"]
            old_sample = child.execute("SELECT id,canonical_sha,case_id,mode,split,source_raw_sha,linkage,"
                                       "raw_hash_origin,sequence_tokens,completion_tokens FROM samples WHERE id=?",
                                       (sid,)).fetchone()
            occurrence = child.execute("SELECT member,line,sample_id,raw_sha,kind FROM occurrences WHERE member=? AND line=?",
                                       (bounds.old_chat_member, line)).fetchone()
            if old_sample is None or occurrence is None:
                raise ValueError("target parent sample/occurrence is missing")
            if (old_sample[0], old_sample[2], old_sample[3], old_sample[4], old_sample[5], old_sample[6]) != (
                    sid, binding["case_id"], binding["mode"], "train", None, 0):
                raise ValueError("target sample state differs from exact unlinked chat row")
            if (occurrence[0], occurrence[1], occurrence[2], occurrence[3], occurrence[4]) != (
                    bounds.old_chat_member, line, sid, binding["chat_raw_sha256"], "CURRENT_CANDIDATE"):
                raise ValueError("target physical occurrence differs from hash-pinned binding")
            if old_sample[1] != binding["chat_canonical_sha256"]:
                raise ValueError("target canonical chat hash differs from binding")
            source = source_bindings[binding["case_id"]]
            if not source.get("builder_replay_full_messages_verified"):
                raise ValueError("full message replay was not verified")
            target_rows.append((line, binding, old_sample, occurrence))

        expected_issue_rows = []
        for line, binding, *_ in target_rows:
            sid = binding["case_id"]
            expected_issue_rows.extend([(bounds.old_chat_member, line, "SOURCE_RAW_HASH_NOT_FOUND", sid),
                                        (bounds.old_chat_member, line, "SOURCE_CHAT_LINKAGE_UNVERIFIED", sid)])
        found_issue_rows = child.execute("SELECT member,line,kind,detail FROM issues WHERE member=? ORDER BY line,kind,detail",
                                         (bounds.old_chat_member,)).fetchall()
        if found_issue_rows != sorted(expected_issue_rows):
            raise ValueError("target issue rows differ from the exact 120 diagnosed rows")

        migration_id = digest({"schema": SCHEMA, "parent_identity": old_identity,
                               "child_identity": new_identity, "bindings": digest(bindings),
                               "semantic_review": digest(semantic_review),
                               "parent_db": parent_before})
        with child:
            child.executescript("""
              CREATE TABLE IF NOT EXISTS structural15_adapter_source_history(
                migration_id TEXT,id TEXT,raw_sha TEXT,canonical_sha TEXT,projection TEXT,signatures TEXT,
                source_split TEXT,original_source_sha TEXT,adapter_kind TEXT,verification_digest TEXT);
              CREATE TABLE IF NOT EXISTS structural15_adapter_sample_history(
                migration_id TEXT,id TEXT,canonical_sha TEXT,case_id TEXT,mode TEXT,split TEXT,
                source_raw_sha TEXT,linkage INTEGER,raw_hash_origin TEXT,sequence_tokens INTEGER,completion_tokens INTEGER);
              CREATE TABLE IF NOT EXISTS structural15_adapter_occurrence_history(
                migration_id TEXT,member TEXT,line INTEGER,sample_id TEXT,raw_sha TEXT,kind TEXT);
              CREATE TABLE IF NOT EXISTS structural15_adapter_issue_history(
                migration_id TEXT,member TEXT,line INTEGER,kind TEXT,detail TEXT);
              CREATE TABLE IF NOT EXISTS structural15_adapter_migration_history(
                migration_id TEXT PRIMARY KEY,parent_identity TEXT,child_identity TEXT,old_member TEXT,
                bindings_digest TEXT,semantic_review_digest TEXT,parent_db_fingerprint TEXT,provenance TEXT);
              CREATE TABLE IF NOT EXISTS recipe_history(
                previous_identity TEXT,next_identity TEXT,PRIMARY KEY(previous_identity,next_identity));
            """)
            child.executemany("INSERT INTO structural15_adapter_issue_history VALUES (?,?,?,?,?)",
                [(migration_id, *r) for r in child.execute("SELECT member,line,kind,detail FROM issues").fetchall()])
            child.executemany("INSERT INTO structural15_adapter_sample_history VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                [(migration_id, *row) for _, _, row, _ in target_rows])
            child.executemany("INSERT INTO structural15_adapter_occurrence_history VALUES (?,?,?,?,?,?)",
                [(migration_id, *row) for _, _, _, row in target_rows])
            child.executemany("INSERT INTO structural15_adapter_source_history VALUES (?,?,?,?,?,?,?,?,?,?)",
                [(migration_id, sid, *row) for sid, row in source_old.items()])
            provenance = {"adapter_kind": ADAPTER_KIND, "source_index_identity": bounds.source_index_identity,
                          "parent_identity": old_identity, "child_identity": new_identity,
                          "bindings_digest": digest(bindings), "semantic_review_digest": digest(semantic_review),
                          "parent_db_fingerprint": parent_before,
                          "parent_auditor_sha256": parent_auditor_sha256,
                          "recipe_sha256": recipe_sha256,
                          "builder_code_sha256": bindings.get("builder_code_sha256"),
                          "builder_chat_records_function_sha256": bindings.get("builder_chat_records_function_sha256"),
                          "migration_code_sha256": _file_hash(__file__),
                          "bindings": bindings,
                          "human_verified": False, "teacher_certified": False,
                          "owner_human_reviewed": False, "training_started": False,
                          "gpu_used": False, "network_used": False}
            child.execute("INSERT INTO structural15_adapter_migration_history VALUES (?,?,?,?,?,?,?,?)",
                (migration_id, old_identity, new_identity, bounds.old_chat_member, digest(bindings),
                 digest(semantic_review), canonical(parent_before), canonical(provenance)))
            child.execute("INSERT INTO recipe_history VALUES (?,?)", (old_identity, new_identity))
            for line, binding, sample, occurrence in target_rows:
                child.execute("DELETE FROM samples WHERE id=?", (binding["sample_id"],))
                child.execute("DELETE FROM occurrences WHERE member=? AND line=?", (bounds.old_chat_member, line))
                child.execute("DELETE FROM issues WHERE member=? AND line=? AND kind IN (?,?)",
                             (bounds.old_chat_member, line, "SOURCE_RAW_HASH_NOT_FOUND", "SOURCE_CHAT_LINKAGE_UNVERIFIED"))
            for sid, binding in source_bindings.items():
                old = source_old[sid]
                desired = json.loads(old[2])
                desired["case_group_id"] = binding["chat_group_id"]
                if digest(desired) != binding["adapted_projection_sha256"]:
                    raise ValueError("adapter projection digest changed during migration")
                child.execute("UPDATE source_versions SET projection=?,original_source_sha=?,adapter_kind=?,"
                              "verification_digest=? WHERE id=?",
                              (canonical(desired), binding["source_canonical_sha256"], ADAPTER_KIND,
                               binding["verification_digest"], sid))
            child.execute("UPDATE members SET next_line=?,complete=0 WHERE id=?",
                          (bounds.old_prefix_rows, bounds.old_chat_member))
            child.execute("UPDATE config SET identity=? WHERE identity=?", (new_identity, old_identity))

        if child.execute("SELECT count(*) FROM samples").fetchone()[0] != bounds.samples - bounds.target_rows:
            raise ValueError("migration removed a non-exact number of samples")
        if child.execute("SELECT count(*) FROM occurrences").fetchone()[0] != bounds.occurrences - bounds.target_rows:
            raise ValueError("migration removed a non-exact number of occurrences")
        if child.execute("SELECT count(*) FROM structural15_adapter_source_history WHERE migration_id=?",
                         (migration_id,)).fetchone()[0] != bounds.target_cases:
            raise ValueError("source history archive incomplete")
        if child.execute("SELECT count(*) FROM structural15_adapter_sample_history WHERE migration_id=?",
                         (migration_id,)).fetchone()[0] != bounds.target_rows:
            raise ValueError("sample history archive incomplete")
        if child.execute("SELECT count(*) FROM structural15_adapter_occurrence_history WHERE migration_id=?",
                         (migration_id,)).fetchone()[0] != bounds.target_rows:
            raise ValueError("occurrence history archive incomplete")
        if child.execute("SELECT count(*) FROM structural15_adapter_issue_history WHERE migration_id=?",
                         (migration_id,)).fetchone()[0] != sum(ISSUE_COUNTS.values()):
            raise ValueError("issue history archive incomplete")
        if child.execute("SELECT member,line,kind,detail FROM issues").fetchall() != [KNOWN_ISSUE]:
            raise ValueError("active issues must retain only the known unrelated split issue")
        if child.execute("SELECT next_line,complete,expected_rows FROM members WHERE id=?",
                         (bounds.old_chat_member,)).fetchone() != (bounds.old_prefix_rows, 0, bounds.old_member_rows):
            raise ValueError("original member cursor was not reset exactly to the preserved prefix")
        if child.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise ValueError("child SQLite quick_check failed")
        child.commit()
        child.close()
        parent.close()
        if _db_fingerprint(parent_path) != parent_before:
            raise ValueError("parent database changed during migration")
        os.replace(temp, child_path)
    except Exception:
        child.close()
        parent.close()
        if temp.exists():
            temp.unlink()
        raise
    return {"migration_id": migration_id, "destination": str(child_path),
            "parent_identity": old_identity, "child_identity": new_identity,
            "member_key": bounds.old_chat_member, "target_rows_requeued": bounds.target_rows,
            "target_cases_adapted": bounds.target_cases, "parent_unchanged": True,
            "parent_issues_archived": sum(ISSUE_COUNTS.values()),
            "samples_archived": bounds.target_rows, "occurrences_archived": bounds.target_rows,
            "source_versions_archived": bounds.target_cases, "training_started": False}


def verify_finalized(auditor, migration_id, *, bounds=PRODUCTION_BOUNDS):
    """Verify full original-member re-consumption and the one honest residual issue."""
    db = auditor.db
    report = auditor.report()
    counts = {t: db.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
              for t in ("source_versions", "samples", "occurrences", "members")}
    if counts != {"source_versions": bounds.source_versions, "samples": bounds.samples,
                  "occurrences": bounds.occurrences, "members": bounds.members}:
        raise ValueError("final full-ledger counts mismatch")
    record = db.execute("SELECT old_member FROM structural15_adapter_migration_history WHERE migration_id=?",
                        (migration_id,)).fetchone()
    if record is None or record[0] != bounds.old_chat_member:
        raise ValueError("migration history missing or member identity changed")
    if db.execute("SELECT next_line,complete,expected_rows FROM members WHERE id=?",
                  (bounds.old_chat_member,)).fetchone() != (bounds.old_member_rows, 1, bounds.old_member_rows):
        raise ValueError("original member not consumed through exact EOF")
    if db.execute("SELECT count(*) FROM members WHERE complete=1 AND next_line=expected_rows").fetchone()[0] != bounds.members:
        raise ValueError("not all original member cursors are complete at exact EOF")
    if db.execute("SELECT member,line,kind,detail FROM issues").fetchall() != [KNOWN_ISSUE]:
        raise ValueError("final active issue set differs from known single issue")
    if (report.get("source_linkage_unverified_rows") != 0
            or report.get("unique_chat_rows_processed") != bounds.samples
            or report.get("physical_chat_occurrences_processed") != bounds.occurrences
            or report.get("TRAINING_DATASET_READY") is not False
            or report.get("full_archive_token_linkage_split_audit_complete") is not False
            or report.get("training_started") is not False
            or report.get("gpu_used") is not False
            or report.get("model_weights_loaded") is not False):
        raise ValueError("final report counts, gates, or provenance mismatch")
    provenance_text = db.execute("SELECT provenance FROM structural15_adapter_migration_history WHERE migration_id=?",
                                 (migration_id,)).fetchone()[0]
    provenance = json.loads(provenance_text)
    bindings = provenance.get("bindings", {})
    source_bindings = bindings.get("source_rows", {})
    if set(source_bindings) != CASE_IDS:
        raise ValueError("archived binding source IDs changed")
    adapted = db.execute("SELECT id,raw_sha,canonical_sha,projection,signatures,source_split,original_source_sha,"
                         "adapter_kind,verification_digest FROM source_versions WHERE adapter_kind=?",
                         (ADAPTER_KIND,)).fetchall()
    if len(adapted) != bounds.target_cases:
        raise ValueError("adapter source projections absent")
    target_ids = {r[0] for r in adapted}
    if target_ids != CASE_IDS:
        raise ValueError("adapted source IDs do not match exact structural-15 set")
    source_history = {r[0]: r[1:] for r in db.execute(
        "SELECT id,raw_sha,canonical_sha,projection,signatures,source_split,original_source_sha,adapter_kind,verification_digest "
        "FROM structural15_adapter_source_history WHERE migration_id=?", (migration_id,))}
    current_sources = {r[0]: r[1:] for r in adapted}
    for sid, binding in source_bindings.items():
        old = source_history.get(sid)
        current = current_sources[sid]
        if old is None or current[0] != binding["source_raw_sha256"] or current[1] != binding["source_canonical_sha256"]:
            raise ValueError("source raw/canonical identity changed after adaptation: " + sid)
        old_projection = json.loads(old[2])
        adapted_projection = json.loads(current[2])
        expected_projection = dict(old_projection, case_group_id=binding["chat_group_id"])
        if (digest(old_projection) != binding["source_projection_sha256"]
                or digest(adapted_projection) != binding["adapted_projection_sha256"]
                or adapted_projection != expected_projection):
            raise ValueError("final source projection differs from exact adapter mapping: " + sid)
        if (current[3] != old[3] or current[4] != old[4] or current[4] != "train"
                or current[5] != binding["source_canonical_sha256"]):
            raise ValueError("source signatures/split/canonical pointer changed: " + sid)
        if current[6] != ADAPTER_KIND or current[7] != binding["verification_digest"]:
            raise ValueError("final adapter metadata mismatch: " + sid)
    target_rows = db.execute("SELECT s.id,s.canonical_sha,s.source_raw_sha,s.linkage,s.raw_hash_origin,"
                             "s.sequence_tokens,s.completion_tokens,o.line "
                             "FROM samples s JOIN occurrences o ON o.sample_id=s.id "
                             "WHERE o.member=? AND o.line>? ORDER BY o.line",
                             (bounds.old_chat_member, bounds.old_prefix_rows)).fetchall()
    if len(target_rows) != bounds.target_rows:
        raise ValueError("final target row window is not exactly 60")
    chats = {sid: source["chats"] for sid, source in source_bindings.items()}
    for sample_id, canonical_sha, raw_sha, linkage, origin, _, _, line in target_rows:
        sid = sample_id.rsplit(":", 1)[0]
        mode = sample_id.rsplit(":", 1)[1]
        binding = chats[sid][mode]
        if sid not in target_ids or not linkage or raw_sha is None or origin != "STRUCTURAL15_RAW_CANONICAL_AND_CHAT_HASH_VERIFIED":
            raise ValueError("target row lacks exact linked original-hash provenance")
        if (canonical_sha != binding["canonical_sha256"]
                or raw_sha != source_bindings[sid]["source_raw_sha256"]
                or line != binding["line"]):
            raise ValueError("final row hashes or physical line differ from binding")
    archived_tokens = {r[0]: (r[1], r[2]) for r in db.execute(
        "SELECT id,sequence_tokens,completion_tokens FROM structural15_adapter_sample_history WHERE migration_id=?",
        (migration_id,))}
    if any(archived_tokens.get(r[0]) != (r[5], r[6]) for r in target_rows):
        raise ValueError("token lengths changed across source projection adapter")
    return {"status": "PASS_REAUDIT_COMPLETE_WITH_ONE_KNOWN_ISSUE", "report": report,
            "relinked_rows": bounds.target_rows, "token_lengths_preserved": True,
            "TRAINING_DATASET_READY": False, "human_review_claimed": False}
