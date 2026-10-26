#!/usr/bin/env python3
"""Read-only, bounded metadata reconciliation helper; intentionally not run here.

Reads only V3 source_versions(id,raw_sha,canonical_sha,signatures,source_split)
and samples(case_id,mode,split), plus two SHA-256-verified signature indexes.
It never reads projection, prompts, answers, archive payloads, or evaluation text.
"""
from __future__ import annotations
import argparse, hashlib, json, sqlite3
from collections import Counter
from pathlib import Path

PROTECTED_SHA256 = "56a5691c1b3b566e373559b9c883d5eacdff353473cca66868f2988ab3e368b8"
HOLDOUT_SHA256 = "a5c15420a9606f27bdcfadd00f44b5eea0b23a2b528458e73a4a1c48d6304263"
# These are the paths implied by exhaustive_cloud_resume.py's META and RUN.
# Supply exact fresh index files from the verified runtime; local files are absent.
PROTECTED_PATH = Path("thinking/cloud_publication/resume_20261018/metadata/thinking/data/exhaustive_math_v1/protected_numeric_signatures.json")
HOLDOUT_PATH = Path("thinking/cloud_publication/resume_20261018/holdout_signatures.json")
MAX_UNLINKED = 5000
EXPECTED_UNLINKED = 4308  # current observed gap: 4307 train_candidate + 1 regression_only

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def load_signatures(path: Path, expected: str) -> set[str]:
    actual = sha256(path)
    if actual != expected:
        raise ValueError(f"index hash mismatch for {path}: {actual}")
    obj = json.loads(path.read_text("utf-8"))
    values = obj.get("signatures")
    if not isinstance(values, list) or any(not isinstance(x, str) for x in values):
        raise ValueError(f"unexpected signature index schema: {path}")
    return set(values)

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("database", type=Path, help="freshly verified V3 checkpoint copy")
    ap.add_argument("output", type=Path, help="new bounded JSON report path")
    ap.add_argument("--protected-index", type=Path, default=PROTECTED_PATH)
    ap.add_argument("--holdout-index", type=Path, default=HOLDOUT_PATH)
    ap.add_argument("--expected-unlinked", type=int, default=EXPECTED_UNLINKED)
    args = ap.parse_args()
    protected = load_signatures(args.protected_index, PROTECTED_SHA256)
    holdout = load_signatures(args.holdout_index, HOLDOUT_SHA256)
    db = sqlite3.connect(f"file:{args.database.resolve().as_posix()}?mode=ro", uri=True)
    db.execute("PRAGMA query_only=ON")
    try:
        identity = db.execute("SELECT identity FROM config").fetchone()
        if identity != ("f0332df91020ace0fc48d88491fe97364d08826458d08c71ba4ec60524e25863",):
            raise ValueError("unexpected exact V3 recipe identity")
        if db.execute("SELECT count(*) FROM members WHERE complete=1 AND next_line=expected_rows").fetchone()[0] != 251:
            raise ValueError("all 251 exact member cursors must be complete before anti-join")
        if db.execute("SELECT count(*) FROM samples").fetchone()[0] != 6502392:
            raise ValueError("full unique chat scan is required before anti-join")
        cols = {r[1] for r in db.execute("PRAGMA table_info(source_versions)")}
        required = {"id", "raw_sha", "canonical_sha", "signatures", "source_split"}
        if not required <= cols:
            raise ValueError(f"V3 source_versions missing required metadata columns: {sorted(required-cols)}")
        duplicates = db.execute("SELECT COUNT(*) FROM (SELECT id FROM source_versions GROUP BY id HAVING COUNT(*)<>1)").fetchone()[0]
        if duplicates:
            raise ValueError(f"source IDs with multiple versions require separate adjudication: {duplicates}")
        # No source member is recorded on source_versions: family attribution is impossible here.
        rows = db.execute("""
            SELECT v.id,v.raw_sha,v.canonical_sha,v.source_split,v.signatures,
                   COALESCE(c.linked_cases,0),COALESCE(c.chat_rows,0)
            FROM source_versions v
            LEFT JOIN (
              SELECT case_id,COUNT(DISTINCT case_id) AS linked_cases,COUNT(*) AS chat_rows
              FROM samples GROUP BY case_id
            ) c ON c.case_id=v.id
            WHERE COALESCE(c.linked_cases,0)=0
            ORDER BY v.id,v.raw_sha
            LIMIT 5001
        """).fetchall()
        if len(rows) > MAX_UNLINKED or len(rows) != args.expected_unlinked:
            raise ValueError(f"unlinked source count {len(rows)} outside expected bounded total {args.expected_unlinked} (cap {MAX_UNLINKED})")
        counts = Counter(); items = []
        for sid, raw_sha, canonical_sha, split, signatures_json, linked_cases, chat_rows in rows:
            sigs = set(json.loads(signatures_json or "[]"))
            if split == "regression_only":
                reason = "regression_only"
            elif sigs & protected:
                reason = "protected_numeric"
            elif sigs & holdout:
                reason = "selected_holdout"
            else:
                reason = "UNRESOLVED_QUARANTINE"
            counts[reason] += 1
            items.append({"id":sid,"raw_sha":raw_sha,"canonical_sha":canonical_sha,"source_split":split,
                          "signatures":sorted(sigs),"linked_case_count":linked_cases,"linked_chat_rows":chat_rows,
                          "classification":reason})
        report = {"schema":"source_chat_antijoin_classification.v1","read_only":True,
                  "payload_or_question_content_read":False,"source_member_provenance_available":False,
                  "source_member_provenance_limitation":"V3 source_versions has no member/family column; this report cannot assign zero-chat source IDs to recipe families.",
                  "index_pins":{"protected":{"path":str(args.protected_index),"sha256":PROTECTED_SHA256},
                                "selected_holdout":{"path":str(args.holdout_index),"sha256":HOLDOUT_SHA256}},
                  "counts":{"unlinked_source_versions":len(rows),"classifications":dict(sorted(counts.items()))},
                  "unlinked":items,
                  "policy":"Only explicit regression/protected/holdout matches get those classifications. Every residual stays quarantined; no candidate is promoted or added to train."}
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    finally:
        db.close()

if __name__ == "__main__":
    main()
