import copy
from contextlib import closing
import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import structural60_repair_migration as M


def sha(data):
    return hashlib.sha256(data).hexdigest()


def row_bytes(row):
    return (json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def fixture_projection(source):
    h = lambda value: M.digest(value)
    return {
        "fields": {key: h(source[key]) for key in
                   ("problem", "grade", "givens", "requested_quantity", "student_work")},
        "fields_student_work_present": bool(source.get("student_work")),
        "targets": {
            "worked_solution": h({"can_solve": source["can_solve"],
                                  "initial_guidance": source["initial_guidance"],
                                  "steps": source["worked_steps"],
                                  "answer": source["expected_answer"]}),
            **{f"hint_level_{n}": h({"hint": source["hints"][n-1]["hint"],
                                     "question": source["hints"][n-1]["question"]})
               for n in range(1, 4)},
        },
        "case_group_id": source["case_group_id"],
        "student_work_present": bool(source.get("student_work")),
    }


def fixture_linkage_errors(row, projection):
    errors = []
    if row["case_group_id"] != projection["case_group_id"]:
        errors.append("case_group_id")
    case_id = row.get("source_sample_id")
    if row["sample_id"] != case_id + ":" + row["mode"]:
        errors.append("source_sample_id")
    prompt = json.loads(row["messages"][1]["content"])
    target = json.loads(row["messages"][2]["content"])
    fields = projection["fields"]
    for key in ("problem", "grade"):
        if M.digest(prompt.get(key)) != fields[key]:
            errors.append("prompt." + key)
    if prompt.get("mode") != row["mode"]:
        errors.append("prompt.mode")
    if M.digest(target) != projection["targets"][row["mode"]]:
        errors.append("assistant.target")
    return errors


def chat_row(source, mode, *, old=True):
    prompt = {"grade": source["grade"], "problem": source["problem"], "mode": mode}
    if source.get("student_work"):
        prompt["student_work"] = source["student_work"]["text"]
    if mode == "worked_solution":
        target = {"can_solve": source["can_solve"], "initial_guidance": source["initial_guidance"],
                  "steps": source["worked_steps"], "answer": source["expected_answer"]}
    else:
        hint = source["hints"][int(mode[-1])-1]
        target = {"hint": hint["hint"], "question": hint["question"]}
    source_raw = source["_raw"]
    source_canonical = source["_canonical"]
    return {
        "sample_id": source["sample_id"] + ":" + mode,
        "source_sample_id": source["sample_id"],
        "case_group_id": source["_old_group"] if old else source["_new_group"],
        "grade": source["grade"], "mode": mode, "split": "train",
        "messages": [{"role": "system", "content": "system"},
                     {"role": "user", "content": M.canonical(prompt)},
                     {"role": "assistant", "content": M.canonical(target)}],
        "source_row_sha256": source_canonical if old else source_raw,
        "row_sha256": source_canonical,
    }


class Structural60MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.old_known_issue = M.KNOWN_ISSUE
        self.bounds = M.Bounds(source_versions=15, chat_rows=62, physical_occurrences=62,
                               members=2, member_rows=62, prefix_rows=2, target_rows=60,
                               sequence_limit=40960, expected_old_member_key=None)
        M.KNOWN_ISSUE = ("source-key", 1, "SOURCE_SPLIT_MISSING_OR_UNKNOWN", "unrelated-source-row")
        self.sources = []
        self.old_target_rows = []
        self.new_target_rows = []
        self.projections = {}
        for n, case_id in enumerate(sorted(M.CASE_IDS), 1):
            source = {
                "sample_id": case_id, "case_group_id": "approved-group-" + str(n),
                "grade": 2, "problem": "problem " + str(n), "givens": [],
                "requested_quantity": "answer", "student_work": None,
                "can_solve": True, "initial_guidance": ["start"],
                "worked_steps": [{"step_id": "s", "result": str(n)}],
                "expected_answer": [{"result": str(n)}],
                "hints": [{"level": i, "hint": "hint " + str(i), "question": "q" + str(i)}
                          for i in range(1, 4)],
                "split": "train",
            }
            raw = sha(("raw-source-" + case_id).encode())
            canonical = M.digest(source)
            source["_raw"], source["_canonical"] = raw, canonical
            source["_old_group"] = "legacy-group-" + str(n)
            source["_new_group"] = "approved-group-" + str(n)
            self.sources.append((source, raw, canonical))
            self.projections[case_id] = fixture_projection(source)
            for mode in M.MODES:
                old = chat_row(source, mode, old=True)
                new = chat_row(source, mode, old=False)
                self.old_target_rows.append(old)
                self.new_target_rows.append(new)
        self.old_target_rows.sort(key=lambda r: (r["source_sample_id"], M.MODES.index(r["mode"])))
        self.new_target_rows.sort(key=lambda r: (r["source_sample_id"], M.MODES.index(r["mode"])))
        # Two unchanged prefix rows plus the exact 60 target rows.
        self.prefix = [{"sample_id": "prefix:one", "sample_group": "prefix"},
                       {"sample_id": "prefix:two", "sample_group": "prefix"}]
        old_bytes = b"".join(row_bytes(x) for x in self.prefix + self.old_target_rows)
        new_bytes = b"".join(row_bytes(x) for x in self.prefix + self.new_target_rows)
        self.old_path, self.new_path = self.root / "old.jsonl", self.root / "new.jsonl"
        self.old_path.write_bytes(old_bytes)
        self.new_path.write_bytes(new_bytes)
        self.source_entry = self.entry(b"source-payload", "candidate_source", 15)
        self.source_entry.update(file_name="source.jsonl", file_id="source-drive-id")
        self.old_entry = self.entry(old_bytes, "candidate_chat", 62)
        self.old_entry["file_name"] = "MathVisionKid_CHAT_part_07_of_07.jsonl"
        self.old_entry["file_id"] = "old-drive-id"
        self.new_entry = self.entry(new_bytes, "candidate_chat", 62)
        self.new_entry.update(file_name="derived_CHAT_part_07.jsonl", file_id="new-drive-id",
                              family="derived_original_chat_structural60_hash_group_repair")
        def artifact(entry):
            return {entry["sha256"]: {"sha256": entry["sha256"], "bytes": entry["bytes"],
                                      "file_ids": [entry["file_id"]],
                                      "file_names": [entry["file_name"]]}}
        old_artifacts = artifact(self.source_entry) | artifact(self.old_entry)
        new_artifacts = old_artifacts | artifact(self.new_entry)
        self.old_recipe = {"source_members": [self.source_entry], "chat_members": [self.old_entry],
                           "artifacts": old_artifacts}
        self.new_recipe = {"source_members": [self.source_entry], "chat_members": [self.new_entry],
                           "artifacts": new_artifacts}
        self.old_key, self.new_key = M.member_key(self.old_entry), M.member_key(self.new_entry)
        self.source_key = M.member_key(self.source_entry)
        self.db_path = self.root / "parent.sqlite"
        self.child_path = self.root / "child.sqlite"
        self.make_parent_db(self.prefix, self.old_target_rows)
        self.semantic = self.semantic_receipt()
        self.receipt = self.make_repair_receipt()

    def tearDown(self):
        M.KNOWN_ISSUE = self.old_known_issue
        self.temp.cleanup()

    @staticmethod
    def entry(raw, role, rows):
        return {"sha256": sha(raw), "bytes": len(raw), "member": None,
                "member_sha256": None, "member_bytes": None, "role": role,
                "rows": rows, "file_name": role + ".jsonl"}

    def semantic_receipt(self):
        rows = []
        for source, raw, canonical in self.sources:
            rows.append({
                "sample_id": source["sample_id"], "current_raw_line_sha256": raw,
                "current_canonical_row_sha256": canonical, "findings": [],
                "checks": {name: {"status": "PASS"} for name in
                           ("math_independent_oracle", "language_and_grade", "units",
                            "step_reasons_and_checks", "evidence_grounded_wrong_work_response",
                            "hint_no_answer_leakage",
                            "split_provenance_and_id")},
            })
        return {"schema": "MathVisionKid.Structural15SemanticReview.v1",
                "overall_semantic_result": "PASS_WITH_SCOPE_LIMITS",
                "reviewer": {"type": "AI_REVIEWER", "authority": "OWNER_PREAUTHORIZED",
                             "human_verified": False, "teacher_certified": False,
                             "owner_human_reviewed": False},
                "rows": rows}

    def make_parent_db(self, prefix, old_rows):
        db = sqlite3.connect(self.db_path)
        db.executescript("""
        CREATE TABLE config(identity TEXT PRIMARY KEY,sequence_limit INTEGER);
        CREATE TABLE members(id TEXT PRIMARY KEY,role TEXT,next_line INTEGER,complete INTEGER,expected_rows INTEGER);
        CREATE TABLE source_versions(id TEXT,raw_sha TEXT,canonical_sha TEXT,projection TEXT,signatures TEXT,
          source_split TEXT,original_source_sha TEXT,adapter_kind TEXT,verification_digest TEXT,PRIMARY KEY(id,raw_sha));
        CREATE TABLE samples(id TEXT PRIMARY KEY,canonical_sha TEXT,case_id TEXT,mode TEXT,split TEXT,
          source_raw_sha TEXT,linkage INTEGER,raw_hash_origin TEXT,sequence_tokens INTEGER,completion_tokens INTEGER,
          UNIQUE(case_id,mode));
        CREATE TABLE occurrences(member TEXT,line INTEGER,sample_id TEXT,raw_sha TEXT,kind TEXT,PRIMARY KEY(member,line));
        CREATE TABLE split_keys(kind TEXT,key TEXT,split TEXT,PRIMARY KEY(kind,key));
        CREATE TABLE issues(member TEXT,line INTEGER,kind TEXT,detail TEXT,PRIMARY KEY(member,line,kind,detail));
        """)
        db.execute("INSERT INTO config VALUES (?,?)", ("old-identity", 40960))
        db.executemany("INSERT INTO source_versions VALUES (?,?,?,?,?,?,?,?,?)",
                       [(s["sample_id"], raw, canonical, M.canonical(self.projections[s["sample_id"]]), "[]",
                         "train", None, None, None) for s, raw, canonical in self.sources])
        db.executemany("INSERT INTO members VALUES (?,?,?,?,?)",
                       [(self.source_key, "candidate_source", 15, 1, 15),
                        (self.old_key, "candidate_chat", 62, 1, 62)])
        # Prefix rows must be retained as active samples/occurrences.
        for i, row in enumerate(prefix, 1):
            raw = row_bytes(row).rstrip(b"\n")
            db.execute("INSERT INTO samples VALUES (?,?,?,?,?,?,?,?,?,?)",
                       (row["sample_id"], M.digest(row), row["sample_id"], "worked_solution",
                        "train", None, 0, "UNVERIFIED", 10, 3))
            db.execute("INSERT INTO occurrences VALUES (?,?,?,?,?)",
                       (self.old_key, i, row["sample_id"], sha(raw), "CURRENT_CANDIDATE"))
        for offset, (row, old_raw) in enumerate(zip(old_rows, [row_bytes(x).rstrip(b"\n") for x in old_rows]), 3):
            # Source sample table stores canonical chat hash and token counts only.
            db.execute("INSERT INTO samples VALUES (?,?,?,?,?,?,?,?,?,?)",
                       (row["sample_id"], M.digest(row), row["source_sample_id"], row["mode"],
                        "train", None, 0, "UNVERIFIED", 100 + offset, 20 + offset))
            db.execute("INSERT INTO occurrences VALUES (?,?,?,?,?)",
                       (self.old_key, offset, row["sample_id"], sha(old_raw), "CURRENT_CANDIDATE"))
            db.execute("INSERT INTO issues VALUES (?,?,?,?)",
                       (self.old_key, offset, "SOURCE_RAW_HASH_NOT_FOUND", row["source_sample_id"]))
            db.execute("INSERT INTO issues VALUES (?,?,?,?)",
                       (self.old_key, offset, "SOURCE_CHAT_LINKAGE_UNVERIFIED", row["source_sample_id"]))
        db.execute("INSERT INTO issues VALUES (?,?,?,?)", M.KNOWN_ISSUE)
        db.execute("INSERT INTO split_keys VALUES (?,?,?)", ("group", "some-group", "train"))
        db.commit()
        db.close()

    def make_repair_receipt(self):
        old_prefix = b"".join(row_bytes(x) for x in self.prefix)
        proofs = []
        for i, (old, new) in enumerate(zip(self.old_target_rows, self.new_target_rows), 3):
            case_id = new["source_sample_id"]
            source, raw_source, canonical_source = next(x for x in self.sources if x[0]["sample_id"] == case_id)
            old_raw, new_raw = row_bytes(old).rstrip(b"\n"), row_bytes(new).rstrip(b"\n")
            proofs.append({
                "line": i, "sample_id": new["sample_id"], "case_id": case_id, "mode": new["mode"],
                "old_raw_sha256": sha(old_raw), "new_raw_sha256": sha(new_raw),
                "old_canonical_sha256": M.digest(old), "new_canonical_sha256": M.digest(new),
                "changed_fields": ["case_group_id", "source_row_sha256"],
                "old_case_group_id": old["case_group_id"], "new_case_group_id": new["case_group_id"],
                "old_source_row_sha256": old["source_row_sha256"],
                "new_source_row_sha256": new["source_row_sha256"],
                "source_canonical_sha256": canonical_source,
                "messages_sha256": M.digest(old["messages"]),
                "full_projection_match_after_repair": True,
            })
        prefix_sha = sha(old_prefix)
        semantic_bytes = json.dumps(self.semantic, ensure_ascii=False, indent=2).encode("utf-8")
        return {"schema": M.SCHEMA, "parent_recipe_identity": "old-identity",
                "parent_recipe_sha256": "parent-recipe-hash", "parent_entry": self.old_entry,
                "prefix_rows_unchanged": 2, "changed_chat_rows": 60, "case_ids": 15,
                "changed_fields": ["case_group_id", "source_row_sha256"],
                "semantic_qa_sha256": sha(semantic_bytes),
                "messages_answers_hints_unchanged": True, "source_rows_modified": False,
                "human_signoffs_created": 0, "parent_original_preserved": True,
                "merged_or_published": False, "training_started": False,
                "prefix_bytes_sha256": prefix_sha, "derived_prefix_bytes_sha256": prefix_sha,
                "derived_file": {"name": self.new_entry["file_name"],
                                 "bytes": self.new_entry["bytes"],
                                 "sha256": self.new_entry["sha256"], "rows": 62},
                "rows": proofs}

    def plan_identity(self, recipe):
        return "old-identity" if recipe is self.old_recipe else "new-identity"

    def run_migration(self):
        return M.prepare_migration(
            self.db_path, self.child_path, self.old_recipe, self.new_recipe,
            self.semantic, self.receipt, self.old_path, self.new_path,
            plan_identity=self.plan_identity, linkage_errors=fixture_linkage_errors,
            parent_recipe_sha256="parent-recipe-hash",
            semantic_review_bytes=json.dumps(self.semantic, ensure_ascii=False, indent=2).encode("utf-8"),
            repair_receipt_bytes=json.dumps(self.receipt, ensure_ascii=False, sort_keys=True,
                                            separators=(",", ":")).encode("utf-8"),
            bounds=self.bounds)

    def test_migration_removes_only_targets_and_preserves_parent_and_histories(self):
        before = sha(self.db_path.read_bytes())
        result = self.run_migration()
        self.assertEqual(sha(self.db_path.read_bytes()), before)
        self.assertEqual(result["target_rows_requeued"], 60)
        with closing(sqlite3.connect(self.child_path)) as db:
            self.assertEqual(db.execute("SELECT identity FROM config").fetchone()[0], "new-identity")
            self.assertEqual(db.execute("SELECT count(*) FROM samples").fetchone()[0], 2)
            self.assertEqual(db.execute("SELECT count(*) FROM occurrences").fetchone()[0], 2)
            self.assertEqual(db.execute("SELECT count(*) FROM structural60_sample_history").fetchone()[0], 60)
            self.assertEqual(db.execute("SELECT count(*) FROM structural60_occurrence_history").fetchone()[0], 60)
            self.assertEqual(db.execute("SELECT count(*) FROM structural60_issue_history").fetchone()[0], 121)
            self.assertEqual(db.execute("SELECT next_line,complete,expected_rows FROM members WHERE id=?",
                                        (self.new_key,)).fetchone(), (2, 0, 62))
            self.assertEqual(db.execute("SELECT count(*) FROM source_versions").fetchone()[0], 15)
            self.assertEqual(db.execute("SELECT count(*) FROM split_keys").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT count(*) FROM issues").fetchone()[0], 1)

    def test_refuses_unapproved_row_field_change_without_creating_child(self):
        tampered = copy.deepcopy(self.receipt)
        tampered["rows"][0]["changed_fields"] = ["case_group_id", "source_row_sha256", "grade"]
        with self.assertRaises(ValueError):
            M.prepare_migration(self.db_path, self.child_path, self.old_recipe, self.new_recipe,
                                self.semantic, tampered, self.old_path, self.new_path,
                                plan_identity=self.plan_identity, linkage_errors=fixture_linkage_errors,
                                parent_recipe_sha256="parent-recipe-hash",
                                semantic_review_bytes=json.dumps(self.semantic, ensure_ascii=False, indent=2).encode("utf-8"),
                                repair_receipt_bytes=json.dumps(tampered, ensure_ascii=False, sort_keys=True,
                                                                separators=(",", ":")).encode("utf-8"),
                                bounds=self.bounds)
        self.assertFalse(self.child_path.exists())

    def test_refuses_issue_retargeting(self):
        with closing(sqlite3.connect(self.db_path)) as db:
            db.execute("UPDATE issues SET detail='different-case' WHERE member=? AND kind=?",
                       (self.old_key, "SOURCE_RAW_HASH_NOT_FOUND"))
            db.commit()
        with self.assertRaises(ValueError):
            self.run_migration()
        self.assertFalse(self.child_path.exists())

    def test_refuses_recipe_change_and_prefix_byte_change(self):
        changed_recipe = copy.deepcopy(self.new_recipe)
        changed_recipe["other_metadata"] = True
        with self.assertRaises(ValueError):
            M.prepare_migration(self.db_path, self.child_path, self.old_recipe, changed_recipe,
                                self.semantic, self.receipt, self.old_path, self.new_path,
                                plan_identity=lambda recipe: "old-identity" if "other_metadata" not in recipe else "new-identity",
                                linkage_errors=fixture_linkage_errors,
                                parent_recipe_sha256="parent-recipe-hash",
                                semantic_review_bytes=json.dumps(self.semantic, ensure_ascii=False, indent=2).encode("utf-8"),
                                repair_receipt_bytes=json.dumps(self.receipt, ensure_ascii=False, sort_keys=True,
                                                                separators=(",", ":")).encode("utf-8"),
                                bounds=self.bounds)
        changed = bytearray(self.new_path.read_bytes())
        changed[15] ^= 1
        self.new_path.write_bytes(changed)
        with self.assertRaises(ValueError):
            self.run_migration()
        self.assertFalse(self.child_path.exists())

    def test_finalize_requires_original_gate_report_and_preserved_token_lengths(self):
        result = self.run_migration()
        with closing(sqlite3.connect(self.child_path)) as db:
            # Synthetic stand-in for original v3.consume() of the exact window.
            for n, row in enumerate(self.new_target_rows, 3):
                source = self.projections[row["source_sample_id"]]
                raw = row_bytes(row).rstrip(b"\n")
                previous = db.execute("SELECT sequence_tokens,completion_tokens FROM structural60_sample_history WHERE id=?",
                                      (row["sample_id"],)).fetchone()
                db.execute("INSERT INTO samples VALUES (?,?,?,?,?,?,?,?,?,?)",
                           (row["sample_id"], M.digest(row), row["source_sample_id"], row["mode"], "train",
                            next(s[1] for s in self.sources if s[0]["sample_id"] == row["source_sample_id"]),
                            1, "ORIGINAL_RAW_HASH_VERIFIED", previous[0], previous[1]))
                db.execute("INSERT INTO occurrences VALUES (?,?,?,?,?)",
                           (self.new_key, n, row["sample_id"], sha(raw), "CURRENT_CANDIDATE"))
            db.execute("UPDATE members SET next_line=62,complete=1 WHERE id=?", (self.new_key,))
            db.commit()

        class FakeAuditor:
            def __init__(self, path):
                self.db = sqlite3.connect(path)
            def report(self):
                return {"unique_chat_rows_processed": 62, "physical_chat_occurrences_processed": 62,
                        "source_linkage_unverified_rows": 0, "incomplete_four_mode_cases": 0,
                        "TRAINING_DATASET_READY": False,
                        "full_archive_token_linkage_split_audit_complete": False,
                        "training_started": False, "gpu_used": False, "model_weights_loaded": False}

        audit = FakeAuditor(self.child_path)
        try:
            verified = M.verify_finalized(audit, result["migration_id"], bounds=self.bounds)
            self.assertEqual(verified["status"], "PASS_REAUDIT_COMPLETE_WITH_ONE_KNOWN_ISSUE")
            self.assertIs(verified["TRAINING_DATASET_READY"], False)
        finally:
            audit.db.close()


if __name__ == "__main__":
    unittest.main()
