"""Synthetic checks for exact structural-15 child migration behavior."""
import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import migrate_adapter_checkpoint_preserve_split as M


IDS = (
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
)
MODES = ("worked_solution", "hint_level_1", "hint_level_2", "hint_level_3")


class MigrationFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.parent_path = self.root / "parent.sqlite"
        self.child_path = self.root / "child.sqlite"
        self.bounds = M.Bounds(source_versions=15, samples=62, occurrences=62, members=2,
                               old_member_rows=62, old_prefix_rows=2)
        self.recipe = {"source_members": [], "chat_members": [], "artifacts": {}}
        self.bindings, self.semantic = self.make_inputs()
        self.create_parent()

    def tearDown(self):
        self.temp.cleanup()

    def make_inputs(self):
        sources = {}
        review_rows = []
        for index, sid in enumerate(IDS):
            raw_sha = f"source-raw-{index}"
            canonical_sha = f"source-canonical-{index}"
            old_projection = {"sample_id": sid, "case_group_id": sid, "grade": 4, "split": "train"}
            chat_group = "math-group-" + str(index)
            adapted = dict(old_projection, case_group_id=chat_group)
            chats = {}
            for mode_ix, mode in enumerate(MODES):
                line = 3 + index * 4 + mode_ix
                chats[mode] = {"line": line, "sample_id": sid + ":" + mode,
                               "raw_sha256": f"chat-raw-{line}",
                               "canonical_sha256": f"chat-canonical-{line}",
                               "messages_sha256": f"messages-{line}"}
            sources[sid] = {
                "source_raw_sha256": raw_sha, "source_canonical_sha256": canonical_sha,
                "source_group_id": sid, "chat_group_id": chat_group,
                "source_projection_sha256": M.digest(old_projection),
                "adapted_projection_sha256": M.digest(adapted),
                "verification_digest": M.digest({}), "source_split": "train",
                "builder_replay_full_messages_verified": True, "chats": chats,
            }
            review_rows.append({"sample_id": sid, "current_raw_line_sha256": raw_sha,
                                "current_canonical_row_sha256": canonical_sha,
                                "checks": {name: {"status": "PASS"} for name in M.SEMANTIC_CRITERIA}})
        bindings = {"schema": "MathVisionKid.Structural15ExactReadTimeBindings.v1",
                    "parent_audit_identity": M.SOURCE_INDEX_IDENTITY,
                    "chat_member_key": M.OLD_CHAT_MEMBER,
                    "first_target_line": 3, "last_target_line": 62,
                    "parent_auditor_sha256": "auditor-code-sha",
                    "recipe_sha256": "recipe-sha",
                    "semantic_review_sha256": "pending",
                    "normalized_chat_groups_preserved": True,
                    "corpus_rows_changed": 0,
                    "human_signoffs_created": 0,
                    "source_rows": sources}
        semantic = {"schema": M.SEMANTIC_SCHEMA, "overall_semantic_result": "PASS_WITH_SCOPE_LIMITS",
                    "reviewer": {"type": "AI_REVIEWER", "authority": "OWNER_PREAUTHORIZED",
                                 "human_verified": False, "teacher_certified": False,
                                 "owner_human_reviewed": False}, "rows": review_rows}
        semantic_bytes = json.dumps(semantic, ensure_ascii=False, indent=2).encode("utf-8")
        bindings["semantic_review_sha256"] = hashlib.sha256(semantic_bytes).hexdigest()
        return bindings, semantic

    def create_parent(self):
        db = sqlite3.connect(self.parent_path)
        db.executescript("""
          CREATE TABLE config(identity TEXT,sequence_limit INTEGER);
          CREATE TABLE members(id TEXT,role TEXT,next_line INTEGER,complete INTEGER,expected_rows INTEGER);
          CREATE TABLE source_versions(id TEXT,raw_sha TEXT,canonical_sha TEXT,projection TEXT,signatures TEXT,
            source_split TEXT,original_source_sha TEXT,adapter_kind TEXT,verification_digest TEXT);
          CREATE TABLE samples(id TEXT,canonical_sha TEXT,case_id TEXT,mode TEXT,split TEXT,source_raw_sha TEXT,
            linkage INTEGER,raw_hash_origin TEXT,sequence_tokens INTEGER,completion_tokens INTEGER);
          CREATE TABLE occurrences(member TEXT,line INTEGER,sample_id TEXT,raw_sha TEXT,kind TEXT);
          CREATE TABLE split_keys(kind TEXT,key TEXT,split TEXT);
          CREATE TABLE issues(member TEXT,line INTEGER,kind TEXT,detail TEXT);
        """)
        db.execute("INSERT INTO config VALUES (?,?)", (M.SOURCE_INDEX_IDENTITY, 40960))
        db.executemany("INSERT INTO members VALUES (?,?,?,?,?)", [
            (M.OLD_CHAT_MEMBER, "candidate_chat", 62, 1, 62),
            ("source-member", "candidate_source", 15, 1, 15)])
        for index, (sid, source) in enumerate(self.bindings["source_rows"].items()):
            projection = {"sample_id": sid, "case_group_id": sid, "grade": 4, "split": "train"}
            db.execute("INSERT INTO source_versions VALUES (?,?,?,?,?,?,?,?,?)",
                       (sid, source["source_raw_sha256"], source["source_canonical_sha256"],
                        M.canonical(projection), "[]", "train", None, None, None))
        for line in (1, 2):
            db.execute("INSERT INTO samples VALUES (?,?,?,?,?,?,?,?,?,?)",
                       (f"prefix-{line}", f"prefix-can-{line}", "prefix", "worked_solution", "train",
                        None, 0, "UNVERIFIED", 7, 2))
            db.execute("INSERT INTO occurrences VALUES (?,?,?,?,?)",
                       (M.OLD_CHAT_MEMBER, line, f"prefix-{line}", f"prefix-raw-{line}", "CURRENT_CANDIDATE"))
        for sid, source in self.bindings["source_rows"].items():
            for mode, chat in source["chats"].items():
                line = chat["line"]
                db.execute("INSERT INTO samples VALUES (?,?,?,?,?,?,?,?,?,?)",
                           (chat["sample_id"], chat["canonical_sha256"], sid, mode, "train", None, 0,
                            "UNVERIFIED", 100 + line, 20 + line))
                db.execute("INSERT INTO occurrences VALUES (?,?,?,?,?)",
                           (M.OLD_CHAT_MEMBER, line, chat["sample_id"], chat["raw_sha256"], "CURRENT_CANDIDATE"))
                for kind in ("SOURCE_RAW_HASH_NOT_FOUND", "SOURCE_CHAT_LINKAGE_UNVERIFIED"):
                    db.execute("INSERT INTO issues VALUES (?,?,?,?)", (M.OLD_CHAT_MEMBER, line, kind, sid))
        db.execute("INSERT INTO issues VALUES (?,?,?,?)", M.KNOWN_ISSUE)
        db.executemany("INSERT INTO issues VALUES (?,?,?,?)", M.CROSS_SPLIT_CANONICAL_ISSUES)
        db.execute("INSERT INTO split_keys VALUES (?,?,?)", ("group", "keep-this", "train"))
        db.commit()
        db.close()

    def migrate(self, bindings=None, semantic=None):
        bindings = bindings or self.bindings
        semantic = semantic or self.semantic
        bindings_bytes = json.dumps(bindings, ensure_ascii=False, indent=2).encode("utf-8")
        semantic_bytes = json.dumps(semantic, ensure_ascii=False, indent=2).encode("utf-8")
        return M.prepare_migration(self.parent_path, self.child_path, self.recipe, self.recipe,
            bindings, semantic, parent_identity=M.SOURCE_INDEX_IDENTITY, child_identity="child",
            bindings_bytes=bindings_bytes, expected_bindings_sha256=hashlib.sha256(bindings_bytes).hexdigest(),
            semantic_review_bytes=semantic_bytes, parent_auditor_sha256="auditor-code-sha",
            recipe_sha256="recipe-sha", bounds=self.bounds)

    def test_archive_exact_records_and_leave_parent_unchanged(self):
        before = hashlib.sha256(self.parent_path.read_bytes()).hexdigest()
        result = self.migrate()
        self.assertEqual(hashlib.sha256(self.parent_path.read_bytes()).hexdigest(), before)
        self.assertEqual(result["target_rows_requeued"], 60)
        db = sqlite3.connect(self.child_path)
        self.assertEqual(db.execute("SELECT identity FROM config").fetchone()[0], "child")
        self.assertEqual(db.execute("SELECT count(*) FROM samples").fetchone()[0], 2)
        self.assertEqual(db.execute("SELECT count(*) FROM occurrences").fetchone()[0], 2)
        self.assertEqual(db.execute("SELECT count(*) FROM structural15_adapter_sample_history").fetchone()[0], 60)
        self.assertEqual(db.execute("SELECT count(*) FROM structural15_adapter_occurrence_history").fetchone()[0], 60)
        self.assertEqual(db.execute("SELECT count(*) FROM structural15_adapter_issue_history").fetchone()[0], 157)
        self.assertEqual(db.execute("SELECT count(*) FROM structural15_adapter_source_history").fetchone()[0], 15)
        self.assertEqual(db.execute("SELECT count(*) FROM split_keys").fetchone()[0], 1)
        self.assertEqual(db.execute("SELECT count(*) FROM issues WHERE kind='CROSS_SPLIT_CANONICAL'").fetchone()[0], 36)
        self.assertEqual(db.execute("SELECT count(*) FROM issues").fetchone()[0], 37)
        self.assertEqual(db.execute("SELECT next_line,complete,expected_rows FROM members WHERE id=?",
                                    (M.OLD_CHAT_MEMBER,)).fetchone(), (2, 0, 62))
        adapted = db.execute("SELECT projection,original_source_sha,adapter_kind,verification_digest "
                             "FROM source_versions WHERE id=?", (IDS[0],)).fetchone()
        self.assertEqual(json.loads(adapted[0])["case_group_id"], self.bindings["source_rows"][IDS[0]]["chat_group_id"])
        self.assertEqual(adapted[1], self.bindings["source_rows"][IDS[0]]["source_canonical_sha256"])
        self.assertEqual(adapted[2], M.ADAPTER_KIND)
        self.assertEqual(adapted[3], M.digest({}))
        db.close()

    def test_exact_cross_split_findings_are_required_and_preserved(self):
        result = self.migrate()
        db = sqlite3.connect(self.child_path)
        rows = db.execute("SELECT member,line,kind,detail FROM issues "
                          "WHERE kind='CROSS_SPLIT_CANONICAL' ORDER BY member,line,kind,detail").fetchall()
        self.assertEqual(rows, sorted(M.CROSS_SPLIT_CANONICAL_ISSUES))
        self.assertEqual(result["parent_issues_archived"], 157)
        db.close()

    def test_rejects_missing_or_modified_cross_split_finding(self):
        for sql in (
            "DELETE FROM issues WHERE kind='CROSS_SPLIT_CANONICAL' AND line=(SELECT min(line) FROM issues WHERE kind='CROSS_SPLIT_CANONICAL')",
            "UPDATE issues SET detail='tampered' WHERE kind='CROSS_SPLIT_CANONICAL' AND line=(SELECT min(line) FROM issues WHERE kind='CROSS_SPLIT_CANONICAL')",
        ):
            self.tearDown()
            self.setUp()
            db = sqlite3.connect(self.parent_path)
            db.execute(sql)
            db.commit()
            db.close()
            with self.assertRaises(ValueError):
                self.migrate()
            self.assertFalse(self.child_path.exists())

    def test_diagnostic_hash_and_target_guards_remain_pinned(self):
        self.assertEqual(len(M._expected_cross_split_issues()), 36)
        self.assertEqual(M.CROSS_SPLIT_DIAGNOSTIC_SHA256,
                         "87bdecb6117b7156da7cdf322b2a379629152aa108200b866d443fef5cdac249")
        self.assertEqual(M.KNOWN_ISSUE[2], "SOURCE_SPLIT_MISSING_OR_UNKNOWN")
        self.assertEqual(M.Bounds(target_cases=15, target_rows=60).target_cases, 15)

    def test_rejects_tampered_source_hash_projection_issue_and_qa(self):
        bad = copy.deepcopy(self.bindings)
        bad["source_rows"][IDS[0]]["source_raw_sha256"] = "tampered"
        with self.assertRaises(ValueError):
            self.migrate(bindings=bad)
        self.assertFalse(self.child_path.exists())

        db = sqlite3.connect(self.parent_path)
        db.execute("UPDATE issues SET detail='wrong-id' WHERE kind='SOURCE_RAW_HASH_NOT_FOUND'")
        db.commit()
        db.close()
        with self.assertRaises(ValueError):
            self.migrate()
        self.assertFalse(self.child_path.exists())

        bad_review = copy.deepcopy(self.semantic)
        bad_review["rows"][0]["checks"].pop("units")
        with self.assertRaises(ValueError):
            self.migrate(semantic=bad_review)
        self.assertFalse(self.child_path.exists())

        bad = copy.deepcopy(self.bindings)
        bad["source_rows"][IDS[0]]["chats"][MODES[0]]["sample_id"] = "wrong-source:worked_solution"
        with self.assertRaises(ValueError):
            self.migrate(bindings=bad)
        self.assertFalse(self.child_path.exists())


if __name__ == "__main__":
    unittest.main()

