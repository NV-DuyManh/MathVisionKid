"""Bounded SQLite-only differential check for V3 report indexes.

Uses the frozen V3 constructor/schema/report method and synthetic rows only.
No payloads, tokenizer, corpus, runtime, or remote database are accessed.
"""
from __future__ import annotations

import importlib.util
import json
import sqlite3
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
THINKING = ROOT / "thinking"
import sys
sys.path.insert(0, str(THINKING))
import math_data_full_audit_v3 as v3

INDEX_SQL = [
    "CREATE INDEX mvk_report_source_label_id_hash ON source_versions(source_split,id,raw_sha)",
    "CREATE INDEX mvk_report_sample_link_split_case_hash ON samples(linkage,split,case_id,source_raw_sha)",
    "CREATE INDEX mvk_report_sample_hash_origin ON samples(raw_hash_origin)",
]
PLAN_SQL = {
    "candidate_source_train_chat_links": "SELECT count(*) FROM samples s JOIN source_versions v ON s.case_id=v.id AND s.source_raw_sha=v.raw_sha WHERE s.linkage=1 AND v.source_split='train_candidate' AND s.split='train'",
    "source_labelcounts": "SELECT coalesce(source_split,'<missing>'),count(*) FROM source_versions GROUP BY source_split",
    "hash_origin": "SELECT raw_hash_origin,count(*) FROM samples GROUP BY raw_hash_origin",
}

def entry(role: str, serial: int, rows: int) -> dict:
    return {"sha256": f"{serial:064x}", "bytes": rows * 100, "member": None,
            "role": role, "rows": rows}

def main() -> dict:
    source_entries = [entry("candidate_source", i + 1, 1) for i in range(16)]
    chat_entries = [entry("candidate_chat", i + 100, 4) for i in range(16)]
    recipe = {"source_members": source_entries, "chat_members": chat_entries}
    with tempfile.TemporaryDirectory(prefix="mvk-v3-index-check-") as td:
        db_path = Path(td) / "audit.sqlite"
        audit = v3.FullArchiveAudit(db_path, recipe, tokenizer=object())
        db = audit.db
        for i, source in enumerate(source_entries):
            case_id = f"case-{i:02d}"
            raw_sha = f"{i + 1:064x}"
            label = "train_candidate" if i < 8 else ("validation" if i < 12 else "test")
            db.execute("INSERT INTO source_versions VALUES (?,?,?,?,?,?,?,?,?)",
                       (case_id, raw_sha, f"{i + 101:064x}", "{}", "[]", label,
                        None, None, None))
            db.execute("INSERT INTO members VALUES (?,?,1,1,1)",
                       (v3.member_key(source), "candidate_source"))
        # Preserve a representative recorded source issue through the index-only change.
        db.execute("INSERT INTO issues VALUES (?,?,?,?)",
                   (v3.member_key(source_entries[0]), 1,
                    "SOURCE_SPLIT_MISSING_OR_UNKNOWN", "synthetic-preserved-issue"))
        modes = ("cot", "hint", "direct", "answer")
        for i, chat in enumerate(chat_entries):
            case_id = f"case-{i:02d}"
            source_i = i
            raw_sha = f"{source_i + 1:064x}"
            for mode in modes:
                sample_id = f"{case_id}:{mode}"
                origin = "READ_TIME_DERIVED_BY_FULL_PROMPT_TARGET_LINKAGE" if i % 2 else "ORIGINAL_RAW_HASH_VERIFIED"
                split = "train" if i < 8 else ("validation" if i < 12 else "test")
                db.execute("INSERT INTO samples VALUES (?,?,?,?,?,?,?,?,?,?)",
                           (sample_id, f"{i + 200:064x}", case_id, mode, split, raw_sha,
                            1, origin, 1250 + i, 300 + i))
                db.execute("INSERT INTO occurrences VALUES (?,?,?,?,?)",
                           (v3.member_key(chat), modes.index(mode) + 1, sample_id,
                            f"{i + 500:064x}", "CURRENT_CANDIDATE"))
            db.execute("INSERT INTO members VALUES (?,?,4,1,4)",
                       (v3.member_key(chat), "candidate_chat"))
        db.commit()

        before_report = audit.report()
        before_counts = {name: db.execute(sql).fetchone()[0] for name, sql in {
            "source_versions": "SELECT count(*) FROM source_versions",
            "samples": "SELECT count(*) FROM samples",
            "occurrences": "SELECT count(*) FROM occurrences",
            "members": "SELECT count(*) FROM members",
            "issues": "SELECT count(*) FROM issues",
        }.items()}
        plans_before = {name: db.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
                        for name, sql in PLAN_SQL.items()}

        for statement in INDEX_SQL:
            db.execute(statement)
            db.commit()
        after_report = audit.report()
        after_counts = {name: db.execute(sql).fetchone()[0] for name, sql in {
            "source_versions": "SELECT count(*) FROM source_versions",
            "samples": "SELECT count(*) FROM samples",
            "occurrences": "SELECT count(*) FROM occurrences",
            "members": "SELECT count(*) FROM members",
            "issues": "SELECT count(*) FROM issues",
        }.items()}
        plans_after = {name: db.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
                       for name, sql in PLAN_SQL.items()}

        expected_created = [s.split()[2] for s in INDEX_SQL]
        actual_created = [row[0] for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'mvk_report_%' ORDER BY name")]
        result = {
            "scope": "synthetic SQLite only; frozen V3 schema and report method; no corpus/tokenizer/runtime access",
            "assertions": {
                "report_exactly_equal": before_report == after_report,
                "table_counts_exactly_equal": before_counts == after_counts,
                "exact_three_indexes_created": sorted(expected_created) == actual_created,
                "only_nonunique_indexes": all(not row[0] for row in db.execute(
                    "SELECT sql LIKE '%UNIQUE%' FROM sqlite_master WHERE type='index' AND name LIKE 'mvk_report_%'")),
                "all_fixture_members_complete": before_report["members_complete"] == before_report["members_expected"] == 32,
                "fixture_report_invariants": before_report["candidate_source_train_chat_links"] == 32
                    and before_report["unique_chat_rows_processed"] == 64
                    and before_report["physical_chat_occurrences_processed"] == 64
                    and before_report["incomplete_four_mode_cases"] == 0
                    and before_report["issues"] == {"SOURCE_SPLIT_MISSING_OR_UNKNOWN": 1}
                    and before_report["full_archive_token_linkage_split_audit_complete"] is False,
                "no_data_mutations": before_counts == after_counts,
            },
            "table_counts": before_counts,
            "report": before_report,
            "query_plans_before": plans_before,
            "query_plans_after": plans_after,
        }
        result["pass"] = all(result["assertions"].values())
        audit.close()
        return result

if __name__ == "__main__":
    output = main()
    (HERE / "sqlite_report_index_synthetic_evidence.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
