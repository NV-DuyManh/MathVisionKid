"""Resumable CPU DATA-ONLY audit over explicit hash-pinned archive members.

One mounted/read-only payload at a time; no network, training or model weights.
SQLite, cursors and split evidence must travel with portable checkpoints. Source
members must be indexed before matching chats. Missing canonical metadata is
reported as incomplete, never silently called full split independence.
"""
from contextlib import contextmanager, ExitStack
import argparse
import gzip
import io
import json
from pathlib import Path
import sqlite3
import zipfile
import hashlib

import exhaustive_colab_loader as L
from math_data_portable_resume import canonical, digest, file_hash, save


def source_projection(row):
    """Small field fingerprints; keep no second copy of all source payloads."""
    fields = {key: digest(row[key]) for key in ("problem", "grade", "givens", "requested_quantity", "student_work") if key in row}
    student = row.get("student_work")
    fields["student_work_present"] = bool(student)
    if isinstance(student, dict) and "text" in student:
        fields["student_work_text"] = digest(student["text"])
    targets = {"worked_solution": digest({"can_solve": row["can_solve"],
                "initial_guidance": row["initial_guidance"], "steps": row["worked_steps"],
                "answer": row["expected_answer"]})}
    for hint in row["hints"]:
        targets["hint_level_" + str(hint["level"])] = digest({"hint":hint["hint"], "question":hint["question"]})
    return {"fields":fields, "targets":targets, "case_group_id":row["case_group_id"]}


def linkage_errors(row, projection):
    errors = []
    if row["case_group_id"] != projection["case_group_id"]:
        errors.append("case_group_id")
    if row["sample_id"] != L.case_id(row) + ":" + row["mode"]:
        errors.append("source_sample_id")
    try:
        prompt = json.loads(row["messages"][1]["content"])
        target = json.loads(row["messages"][2]["content"])
    except (ValueError, TypeError):
        return errors + ["structured_prompt_or_target"]
    if not isinstance(prompt, dict) or not isinstance(target, dict):
        return errors + ["structured_prompt_or_target"]
    fields = projection["fields"]
    for field in ("problem", "grade"):
        if digest(prompt.get(field)) != fields.get(field):
            errors.append("prompt." + field)
    if prompt.get("mode") != row["mode"]:
        errors.append("prompt.mode")
    for field in ("givens", "requested_quantity"):
        if field in prompt and digest(prompt[field]) != fields.get(field):
            errors.append("prompt." + field)
    if fields["student_work_present"]:
        if digest(prompt.get("student_work")) not in (fields.get("student_work"), fields.get("student_work_text")):
            errors.append("prompt.student_work")
    elif prompt.get("student_work"):
        errors.append("prompt.student_work")
    if digest(target) != projection["targets"].get(row["mode"]):
        errors.append("assistant.target")
    return errors


@contextmanager
def payload(entry, path):
    """Verify compressed file and exact member bytes before exposing content."""
    path = Path(path)
    if path.stat().st_size != entry["bytes"] or file_hash(path) != entry["sha256"]:
        raise ValueError("payload byte/hash mismatch")
    member = entry.get("member")
    if entry.get("role") not in ("candidate_chat", "candidate_source"):
        raise ValueError("only explicit candidate members may be read")
    if any(word in (member or path.name).casefold() for word in ("sealed", "pilot", "concept_challenge")):
        raise ValueError("protected payload refused")
    with ExitStack() as stack:
        if member:
            archive = stack.enter_context(zipfile.ZipFile(path))
            if archive.namelist().count(member) != 1:
                raise ValueError("ambiguous/missing archive member")
            ref = entry.get("member_sha256")
            if not ref:
                raise ValueError("exact member hash required; discover manifest first")
            import hashlib
            h = hashlib.sha256()
            with archive.open(member) as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    h.update(chunk)
            if h.hexdigest() != ref:
                raise ValueError("archive member hash mismatch")
            binary = stack.enter_context(archive.open(member))
        else:
            binary = stack.enter_context(path.open("rb"))
        if (member or path.name).endswith(".gz"):
            binary = stack.enter_context(gzip.GzipFile(fileobj=binary))
        yield stack.enter_context(io.TextIOWrapper(binary, encoding="utf-8"))


class AuditStore:
    def __init__(self, path, catalog, tokenizer=None, sequence_limit=40960):
        self.db = sqlite3.connect(path)
        self.tokenizer = tokenizer
        self.limit = sequence_limit
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS config(identity TEXT PRIMARY KEY, document TEXT);
        CREATE TABLE IF NOT EXISTS cursors(member TEXT PRIMARY KEY, next_line INTEGER, complete INTEGER);
        CREATE TABLE IF NOT EXISTS sources(id TEXT PRIMARY KEY, hash TEXT, raw_hash TEXT, signatures TEXT, projection TEXT);
        CREATE TABLE IF NOT EXISTS samples(id TEXT PRIMARY KEY, member TEXT, line INTEGER, hash TEXT,
          case_id TEXT, mode TEXT, split TEXT, sequence_tokens INTEGER, completion_tokens INTEGER,
          canonical_known INTEGER, linkage_verified INTEGER, source_hash_verified INTEGER, UNIQUE(case_id,mode));
        CREATE TABLE IF NOT EXISTS split_keys(kind TEXT,key TEXT,split TEXT,PRIMARY KEY(kind,key));
        CREATE TABLE IF NOT EXISTS issues(member TEXT,line INTEGER,kind TEXT,detail TEXT,
          PRIMARY KEY(member,line,kind,detail));
        """)
        identity = {"catalog_sha256": digest(catalog), "tokenizer_revision": L.REVISION if tokenizer else None,
                    "sequence_limit": sequence_limit, "schema": "archive_audit.v2"}
        config = self.db.execute("SELECT document FROM config").fetchone()
        if config and config[0] != canonical(identity):
            self.db.close()
            raise ValueError("audit inputs/config changed; use another DB")
        self.db.execute("INSERT OR IGNORE INTO config VALUES (?,?)", (digest(identity), canonical(identity)))
        self.db.commit()

    def issue(self, key, line, kind, detail):
        self.db.execute("INSERT OR IGNORE INTO issues VALUES (?,?,?,?)", (key, line, kind, str(detail)))

    def consume(self, entry, path, max_rows=None, commit_every=128):
        if max_rows is not None and max_rows <= 0 or commit_every <= 0:
            raise ValueError("positive row/commit bounds required")
        key = digest({k:entry.get(k) for k in ("sha256", "member", "member_sha256", "role")})
        cursor = self.db.execute("SELECT next_line,complete FROM cursors WHERE member=?", (key,)).fetchone()
        if cursor and cursor[1]:
            return {"already_complete": True, "rows": cursor[0]}
        start = cursor[0] if cursor else 0
        processed, last = 0, 0
        try:
            with payload(entry, path) as stream:
                for last, text in enumerate(stream, 1):
                    if last <= start:
                        continue
                    if not text.strip():
                        raise ValueError("blank JSONL row")
                    row = json.loads(text)
                    if entry["role"] == "candidate_source":
                        signatures = L.source_signatures(row)
                        previous = self.db.execute("SELECT hash FROM sources WHERE id=?", (row["sample_id"],)).fetchone()
                        if previous and previous[0] != digest(row):
                            raise ValueError("conflicting source identity")
                        raw_hash = hashlib.sha256(text.removesuffix("\n").removesuffix("\r").encode()).hexdigest()
                        self.db.execute("INSERT OR IGNORE INTO sources VALUES (?,?,?,?,?)",
                                        (row["sample_id"], digest(row), raw_hash, canonical(signatures), canonical(source_projection(row))))
                    else:
                        L.validate_chat(row)
                        sid = L.case_id(row)
                        source = self.db.execute("SELECT signatures,raw_hash,projection,hash FROM sources WHERE id=?", (sid,)).fetchone()
                        source_hash_verified = bool(source and row.get("source_row_sha256") == source[1])
                        if source and row.get("source_row_sha256") and not source_hash_verified:
                            self.issue(key, last, "SOURCE_HASH_MISMATCH", sid)
                        errors = linkage_errors(row, json.loads(source[2])) if source else []
                        for error in errors:
                            self.issue(key, last, "SOURCE_CHAT_LINKAGE_MISMATCH", error)
                        known = source is not None or "canonical_signatures" in row
                        signatures = json.loads(source[0]) if source else row.get("canonical_signatures", [])
                        encoded = L.tokenize_assistant_only(row, self.tokenizer, self.limit) if self.tokenizer else None
                        try:
                            self.db.execute("INSERT INTO samples VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                                (row["sample_id"], key, last, digest(row), sid, row["mode"], row.get("split", "train"),
                                 len(encoded["input_ids"]) if encoded else None,
                                 encoded["completion_tokens"] if encoded else None, int(known), int(bool(source) and not errors),
                                 int(source_hash_verified)))
                        except sqlite3.IntegrityError:
                            self.issue(key, last, "DUPLICATE_SAMPLE_OR_MODE", row["sample_id"])
                        split = row.get("split", "train")
                        keys = [("group", row["case_group_id"]), ("question", L.question_key(row))]
                        keys.extend(("canonical", signature) for signature in signatures)
                        for kind, value in keys:
                            prior = self.db.execute("SELECT split FROM split_keys WHERE kind=? AND key=?", (kind, value)).fetchone()
                            if prior and prior[0] != split:
                                self.issue(key, last, "CROSS_SPLIT_" + kind.upper(), value)
                            self.db.execute("INSERT OR IGNORE INTO split_keys VALUES (?,?,?)", (kind, value, split))
                    self.db.execute("INSERT OR REPLACE INTO cursors VALUES (?,?,0)", (key, last))
                    processed += 1
                    if processed % commit_every == 0:
                        self.db.commit()
                    if max_rows is not None and processed >= max_rows:
                        self.db.commit()
                        return {"already_complete": False, "rows": last, "bounded_pause": True}
            if start > last:
                raise ValueError("cursor beyond end")
            if entry.get("rows") is not None and entry["rows"] != last:
                raise ValueError("member row count mismatch")
            self.db.execute("INSERT OR REPLACE INTO cursors VALUES (?,?,1)", (key, last))
            self.db.commit()
            return {"already_complete": False, "rows": last, "complete": True}
        except Exception:
            self.db.rollback()
            raise

    def report(self):
        samples, maxtokens, maxcompletion, missing, untokenized, unlinked, unhashed = self.db.execute(
            "SELECT count(*),max(sequence_tokens),max(completion_tokens),"
            "coalesce(sum(canonical_known=0),0),coalesce(sum(sequence_tokens IS NULL),0),"
            "coalesce(sum(linkage_verified=0),0),coalesce(sum(source_hash_verified=0),0) FROM samples").fetchone()
        incomplete = self.db.execute("SELECT count(*) FROM (SELECT case_id FROM samples GROUP BY case_id HAVING count(*)!=4)").fetchone()[0]
        return {"schema": "MathVisionKid.archive_audit_progress.v1", "rows_processed": samples,
                "members_complete": self.db.execute("SELECT count(*) FROM cursors WHERE complete=1").fetchone()[0],
                "max_sequence_tokens": maxtokens, "max_completion_tokens": maxcompletion,
                "missing_source_signatures_rows": missing, "untokenized_rows": untokenized,
                "source_linkage_unverified_rows": unlinked, "source_raw_row_hash_unverified_rows": unhashed,
                "incomplete_four_mode_cases": incomplete,
                "issues": dict(self.db.execute("SELECT kind,count(*) FROM issues GROUP BY kind")),
                "full_archive_token_split_audit_complete": False,
                "scope_note": "Progress only. Full catalog coverage and frozen metadata comparison are separate final gates.",
                "training_started": False, "gpu_used": False}

    def close(self):
        self.db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--entry", type=int, required=True)
    parser.add_argument("--payload", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--tokenizer", help="Pinned local tokenizer directory; no weights/network")
    parser.add_argument("--max-rows", type=int)
    args = parser.parse_args()
    if args.max_rows is not None and args.max_rows <= 0:
        parser.error("max-rows must be positive")
    tokenizer = None
    if args.tokenizer:
        directory = Path(args.tokenizer)
        if not directory.is_dir() or directory.name != L.REVISION:
            parser.error("local tokenizer directory must be the pinned revision snapshot")
        tokenizer = L.load_qwen_tokenizer(directory)
    catalog = json.loads(Path(args.catalog).read_text("utf-8"))
    store = AuditStore(args.database, catalog, tokenizer)
    try:
        progress = store.consume(catalog["members"][args.entry], args.payload, args.max_rows)
        save(args.receipt, {"consume": progress, "audit": store.report()})
    finally:
        store.close()


if __name__ == "__main__":
    main()
