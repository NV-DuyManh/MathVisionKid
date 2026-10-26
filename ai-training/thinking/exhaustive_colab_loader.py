"""Data-only streaming, selection and Qwen3 audit. Never invokes training.

Manifest paths are resolved inside the supplied mounted Drive directory. Cloud
IDs identify immutable parts; the loader never downloads the whole corpus.
Resume means the next *unconsumed* JSONL line, bound to the manifest SHA256.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from contextlib import contextmanager
from dataclasses import asdict, dataclass
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import sqlite3
import unicodedata
from fractions import Fraction
from typing import Callable, Iterable, Iterator

MODES = ("worked_solution", "hint_level_1", "hint_level_2", "hint_level_3")
MODEL = "Qwen/Qwen3-1.7B"
REVISION = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".atomic")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


@dataclass(frozen=True)
class Cursor:
    manifest_sha256: str
    shard_index: int = 0
    next_line: int = 0


def manifest_entries(manifest):
    entries = manifest.get("shards", manifest.get("parts", []))
    # The global registry includes corpus ZIPs too: never read those as chats.
    return [entry for entry in entries if entry.get("kind", "chat_gzip") in
            ("chat_gzip", "chat", "gzip", "jsonl", "chat_jsonl", "selected_chat")]


def validate_chat(row):
    for key in ("sample_id", "case_group_id", "mode"):
        if not isinstance(row.get(key), str) or not row[key]:
            raise ValueError(f"missing {key}")
    if row["mode"] not in MODES:
        raise ValueError("unknown mode")
    messages = row.get("messages", [])
    if [message.get("role") for message in messages] != ["system", "user", "assistant"]:
        raise ValueError("expected exactly system,user,assistant")
    if any(not isinstance(message.get("content"), str) or not message["content"] for message in messages):
        raise ValueError("empty/non-string message")
    if row.get("split", "train") not in ("train", "validation", "test"):
        raise ValueError("unknown split")
    if "selected_view_origin_chat_sha256" in row:
        derived = {key: value for key, value in row.items() if key != "row_sha256"}
        if row.get("row_sha256") != digest_bytes(canonical_json(derived).encode()):
            raise ValueError("selected derived row hash mismatch")
    return row


class ManifestStream:
    """Bounded reader for plain or multi-member GZIP files on mounted Drive.

    A whole-file compressed SHA256 pass happens before rows are exposed. The
    gzip CRC/trailer is validated when fully iterated. A cursor can skip prior
    shards; no prior payload has to be rematerialized. GZIP resume replays the
    current compressed shard, retaining constant memory.
    """
    def __init__(self, manifest, drive_root, id_paths=None, verify_hash=True, split=None):
        self.manifest = manifest
        self.entries = manifest_entries(manifest)
        if split not in (None, "train", "validation", "test"):
            raise ValueError("unknown requested split")
        self.split = split
        if split is not None:
            self.entries = [entry for entry in self.entries if entry.get("split", split) == split]
        if not self.entries:
            raise ValueError("manifest has no chat shards")
        identity = manifest if split is None else {"manifest": manifest, "requested_split": split}
        self.manifest_sha256 = digest_bytes(canonical_json(identity).encode())
        self.root = Path(drive_root).resolve()
        self.id_paths = id_paths or {}
        self.verify_hash = verify_hash

    def for_split(self, split):
        """Explicit split selection; cursor identities cannot cross splits."""
        return ManifestStream(self.manifest, self.root, self.id_paths, self.verify_hash, split)

    def path_for(self, entry):
        name = self.id_paths.get(entry.get("file_id")) or entry.get("relative_path") or entry.get("file_name")
        if not name:
            raise ValueError("part requires file_name/relative_path or ID mapping")
        path = (self.root / name).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("manifest path escapes mounted root")
        return path

    def iter_with_cursors(self, cursor=None):
        cursor = Cursor(**cursor) if isinstance(cursor, dict) else cursor
        cursor = cursor or Cursor(self.manifest_sha256)
        if cursor.manifest_sha256 != self.manifest_sha256:
            raise ValueError("resume manifest changed")
        if cursor.shard_index < 0 or cursor.shard_index > len(self.entries) or cursor.next_line < 0:
            raise ValueError("invalid cursor")
        if cursor.shard_index == len(self.entries) and cursor.next_line:
            raise ValueError("invalid terminal cursor")
        for index in range(cursor.shard_index, len(self.entries)):
            entry = self.entries[index]
            path = self.path_for(entry)
            if "bytes" in entry and path.stat().st_size != entry["bytes"]:
                raise ValueError("part byte count mismatch")
            if self.verify_hash:
                if not entry.get("sha256") or file_hash(path) != entry["sha256"]:
                    raise ValueError("part SHA256 mismatch")
            opener = gzip.open if path.suffix == ".gz" else open
            start = cursor.next_line if index == cursor.shard_index else 0
            count = 0
            with opener(path, "rt", encoding="utf-8") as stream:
                for count, line in enumerate(stream, 1):
                    if count <= start:
                        continue
                    if not line.strip():
                        raise ValueError("blank JSONL row")
                    row = validate_chat(json.loads(line))
                    if self.split is not None and row.get("split", "train") != self.split:
                        continue
                    yield row, Cursor(self.manifest_sha256, index, count)
            expected = entry.get("chat_rows", entry.get("rows"))
            if expected is not None and expected != count:
                raise ValueError("part row count mismatch")
            if start > count:
                raise ValueError("cursor beyond shard end")
        # The last yielded cursor remains valid at EOF; iteration rechecks its
        # current shard then finishes. No unsafe implicit acknowledgement.

    def __iter__(self):
        for row, _ in self.iter_with_cursors():
            yield row


def case_id(row):
    return row.get("source_sample_id") or row["sample_id"].removesuffix(":" + row["mode"])


def question_key(row):
    content = row["messages"][1]["content"]
    try:
        payload = json.loads(content)
        content = str(payload.get("problem", payload.get("question", content)))
    except (ValueError, AttributeError):
        pass
    content = unicodedata.normalize("NFC", content)
    return digest_bytes(re.sub(r"\s+", " ", content).strip().casefold().encode())


def source_signatures(source):
    """Canonical metadata plus every arithmetic expression in observable steps."""
    def expression_group(expression):
        # Same bounded canonical form as the frozen v4 comparator, implemented
        # without importing any module that can open benchmark payloads.
        def walk(node):
            if isinstance(node, ast.Constant) and type(node.value) in (int, float):
                return ("n", str(Fraction(ast.get_source_segment(expression, node))))
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
                return ("neg", walk(node.operand))
            if not isinstance(node, ast.BinOp):
                raise ValueError("unsupported source expression")
            op = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.Mod: "%"}[type(node.op)]
            children = [walk(node.left), walk(node.right)]
            if op in ("+", "*"):
                flattened = []
                for child in children:
                    flattened.extend(child[1:]) if child[0] == op else flattened.append(child)
                return (op, *sorted(flattened, key=repr))
            return (op, *children)
        return digest_bytes(repr(walk(ast.parse(expression, mode="eval").body)).encode())
    result = set(source.get("canonical_signatures", []))
    expanded, values = [], []
    for step in source.get("worked_steps", source.get("steps", [])):
        expression = step.get("expression")
        if expression:
            def replace(match, preceding):
                index = int(match[1])
                if index >= len(preceding) or preceding[index] is None:
                    raise ValueError("unresolvable prior source step")
                return "(" + preceding[index] + ")"
            symbolic = re.sub(r"\{s(\d+)\}", lambda m: replace(m, expanded), expression)
            resolved = re.sub(r"\{s(\d+)\}", lambda m: replace(m, values), expression)
            result.update((expression_group(symbolic), expression_group(resolved)))
            expanded.append(symbolic)
        else:
            expanded.append(None)
        try:
            values.append(str(Fraction(str(step.get("result")))))
        except (ValueError, ZeroDivisionError):
            values.append(None)
    # Euclidean remainder metadata remains metadata, never a live calculator
    # operation. It must participate in the same exclusion rule as division.
    for expression in source.get("canonical_case", {}).get("operations", []):
        if isinstance(expression, str) and "{s" not in expression:
            result.add(expression_group(expression))
    return sorted(result)


def load_source_index(paths):
    result = {}
    for path in paths:
        opener = gzip.open if str(path).endswith(".gz") else open
        with opener(path, "rt", encoding="utf-8") as stream:
            for line in stream:
                source = json.loads(line)
                sid = source["sample_id"]
                if sid in result:
                    raise ValueError("duplicate source ID")
                result[sid] = {"canonical_signatures": source_signatures(source),
                               "case_kind": source.get("case_kind", source.get("curriculum_assignment", {}).get("case_kind",
                                                    source.get("coverage", {}).get("case_kind", source.get("kind", "unknown")))),
                               "topic": source.get("topic", "unknown"),
                               "grade": source.get("grade"),
                               "split": source.get("split", "train"),
                               "can_solve": source.get("can_solve", True),
                               "student_work_present": source.get("student_work") is not None,
                               "source_sha256": digest_bytes(canonical_json(source).encode())}
    return result


def selected_view(rows, source_index=None, protected=(), mandatory_ids=(), optional_cases_per_category=64):
    """Two-pass bounded deterministic case selection from a repeatable factory.

    Every accepted selected case keeps all four modes. Mandatory pedagogic
    cases are unlimited only by the explicit finite input; simple arithmetic
    is capped per category. Quarantine affects this view, never source corpus.
    The returned receipt enumerates each exclusion and exact case selection.
    """
    source_index = source_index or {}
    protected, mandatory_ids = set(protected), set(mandatory_ids)
    if optional_cases_per_category < 0:
        raise ValueError("negative selection cap")
    # Reserve new holdouts before considering any training row. This is
    # independent of input order and includes intermediate/check arithmetic.
    holdout_keys = {"group": set(), "question": set(), "canonical": set()}
    for row in rows():
        validate_chat(row)
        if row.get("split", "train") != "train":
            metadata = source_index.get(case_id(row), {})
            holdout_keys["group"].add(row["case_group_id"])
            holdout_keys["question"].add(question_key(row))
            holdout_keys["canonical"].update(metadata.get("canonical_signatures", row.get("canonical_signatures", [])))
    candidates, chosen, excluded = defaultdict(dict), set(), {}
    mandatory_categories = {}
    for row in rows():
        validate_chat(row)
        sid = case_id(row)
        metadata = source_index.get(sid, {})
        signatures = set(metadata.get("canonical_signatures", row.get("canonical_signatures", [])))
        if row.get("split", "train") == "train":
            if signatures & protected:
                excluded[sid] = {"reason": "PROTECTED_CANONICAL_OVERLAP", "signatures": sorted(signatures & protected)}
                continue
            reasons = []
            if row["case_group_id"] in holdout_keys["group"]:
                reasons.append("group")
            if question_key(row) in holdout_keys["question"]:
                reasons.append("question")
            if signatures & holdout_keys["canonical"]:
                reasons.append("canonical")
            if reasons:
                excluded[sid] = {"reason": "NEW_HOLDOUT_OVERLAP", "overlap_kinds": reasons,
                                 "signatures": sorted(signatures & holdout_keys["canonical"])}
                continue
        category = row.get("selection_category", metadata.get("topic", row.get("topic", "baseline_pedagogy")))
        if sid in mandatory_ids or row.get("split", "train") != "train":
            chosen.add(sid)
            mandatory_categories[sid] = category
        elif sid not in candidates[category]:
            candidates[category][sid] = digest_bytes(sid.encode())
            if len(candidates[category]) > optional_cases_per_category:
                worst = max(candidates[category], key=lambda x: (candidates[category][x], x))
                del candidates[category][worst]
    for values in candidates.values():
        chosen.update(values)
    categories = {sid: category for category, values in candidates.items() for sid in values}
    categories.update(mandatory_categories)
    chosen.difference_update(excluded)
    receipt = {"schema": "balanced_selection.v2", "selected_cases": len(chosen),
               "selected_case_ids": sorted(chosen), "excluded_cases": excluded,
               "by_category": dict(Counter(categories[sid] for sid in chosen)),
               "full_corpus_changed": False, "all_modes_preserved": True}
    def iterator():
        modes = defaultdict(set)
        for row in rows():
            if case_id(row) in chosen:
                if row["mode"] in modes[case_id(row)]:
                    raise ValueError("duplicate selected case mode")
                modes[case_id(row)].add(row["mode"])
                yield row
        for sid in chosen:
            if modes[sid] != set(MODES):
                raise ValueError(f"selected case lacks modes: {sid}")
    return iterator, receipt


def load_qwen_tokenizer(tokenizer_path=MODEL):
    from transformers import AutoTokenizer
    local = Path(tokenizer_path).exists()
    tokenizer = AutoTokenizer.from_pretrained(str(tokenizer_path), revision=None if local else REVISION,
                                            local_files_only=local, trust_remote_code=False)
    if tokenizer.convert_tokens_to_ids("<|im_end|>") != 151645:
        raise ValueError("unexpected Qwen3 assistant EOT")
    return tokenizer


def tokenize_assistant_only(row, tokenizer, max_sequence_tokens=40960):
    validate_chat(row)
    messages = row["messages"]
    prefix_text = tokenizer.apply_chat_template(messages[:2], tokenize=False, add_generation_prompt=True,
                                                enable_thinking=False)
    rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False,
                                            enable_thinking=False)
    full = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=False,
                                         enable_thinking=False)
    if hasattr(full, "keys"):
        full = full["input_ids"]
    if not rendered.startswith(prefix_text):
        raise ValueError("official chat template text prefix mismatch")
    # Byte-pair tokenization can merge the prompt's trailing newline with the
    # first completion character. Locate the boundary with fast-tokenizer
    # character offsets; independently encoding a prefix gives wrong masks.
    tokenized = tokenizer(rendered, add_special_tokens=False, return_offsets_mapping=True)
    if tokenized["input_ids"] != full:
        raise ValueError("official chat template token mismatch")
    boundary = next((i for i, (_, end) in enumerate(tokenized["offset_mapping"])
                     if end > len(prefix_text)), len(full))
    end = len(full)
    # Qwen appends a formatting newline after im_end: it is masked, not a
    # second loss-bearing completion terminator or silently truncated input.
    while end > boundary and full[end - 1] != 151645:
        end -= 1
    completion = full[boundary:end]
    if not completion or completion[-1] != 151645 or completion.count(151645) != 1:
        raise ValueError("assistant must contain exactly one EOT")
    if any(token in completion[:-1] for token in (151644, 151645)):
        raise ValueError("embedded role delimiter in assistant content")
    if len(full) > max_sequence_tokens:
        raise ValueError(f"sequence exceeds configured limit: {len(full)}")
    labels = [-100] * boundary + completion + [-100] * (len(full) - end)
    if len(labels) != len(full):
        raise AssertionError("mask length mismatch")
    return {"input_ids": full, "attention_mask": [1] * len(full), "labels": labels,
            "completion_tokens": len(completion), "prompt_tokens": boundary}


def tokenized_stream(stream, tokenizer, cursor=None, max_sequence_tokens=40960):
    """Yield one encoded row + acknowledgement cursor; never prefetch corpus."""
    if stream.split is None:
        raise ValueError("choose an explicit split with for_split before tokenized consumption")
    for row, next_cursor in stream.iter_with_cursors(cursor):
        yield {"sample_id": row["sample_id"], "case_group_id": row["case_group_id"],
               "split": row.get("split", "train"),
               **tokenize_assistant_only(row, tokenizer, max_sequence_tokens)}, next_cursor


def pad_batch(encoded_rows, pad_token_id=151643):
    """Right padding with zero attention and -100 loss, no truncation."""
    encoded_rows = list(encoded_rows)
    width = max((len(row["input_ids"]) for row in encoded_rows), default=0)
    result = {"input_ids": [], "attention_mask": [], "labels": []}
    for row in encoded_rows:
        padding = width - len(row["input_ids"])
        result["input_ids"].append(row["input_ids"] + [pad_token_id] * padding)
        result["attention_mask"].append(row["attention_mask"] + [0] * padding)
        result["labels"].append(row["labels"] + [-100] * padding)
    return result


class SplitAudit:
    """Disk-backed on Colab, in-memory for small bounded selected views."""
    def __init__(self, sqlite_path=":memory:"):
        self.db = sqlite3.connect(str(sqlite_path))
        self.db.executescript("CREATE TABLE samples(id TEXT PRIMARY KEY);"
                              "CREATE TABLE split_keys(kind TEXT,key TEXT,split TEXT,PRIMARY KEY(kind,key));"
                              "CREATE TABLE modes(case_id TEXT,mode TEXT,PRIMARY KEY(case_id,mode));")

    def add(self, row, signatures=()):
        split = row.get("split", "train")
        try:
            self.db.execute("INSERT INTO samples VALUES (?)", (row["sample_id"],))
            self.db.execute("INSERT INTO modes VALUES (?,?)", (case_id(row), row["mode"]))
        except sqlite3.IntegrityError as error:
            raise ValueError("duplicate sample_id or case mode") from error
        keys = [("group", row["case_group_id"]), ("question", question_key(row))]
        keys.extend(("canonical", key) for key in signatures)
        for kind, key in keys:
            prior = self.db.execute("SELECT split FROM split_keys WHERE kind=? AND key=?", (kind, key)).fetchone()
            if prior and prior[0] != split:
                raise ValueError(f"cross-split {kind} overlap")
            self.db.execute("INSERT OR IGNORE INTO split_keys VALUES (?,?,?)", (kind, key, split))

    def finish(self):
        incomplete = self.db.execute("SELECT COUNT(*) FROM (SELECT case_id FROM modes GROUP BY case_id HAVING COUNT(*) != 4)").fetchone()[0]
        if incomplete:
            raise ValueError("incomplete four-mode cases")
        return {"unique_samples": self.db.execute("SELECT COUNT(*) FROM samples").fetchone()[0],
                "unique_cases": self.db.execute("SELECT COUNT(DISTINCT case_id) FROM modes").fetchone()[0],
                "group_question_canonical_split_disjoint": True}

    def close(self):
        self.db.close()


def full_token_audit(rows, tokenizer, source_index=None, sqlite_path=":memory:", max_sequence_tokens=40960):
    source_index = source_index or {}
    audit = SplitAudit(sqlite_path)
    lengths, completions = Counter(), Counter()
    by_mode, by_split, by_grade, by_topic = Counter(), Counter(), Counter(), Counter()
    stream_hash = hashlib.sha256()
    try:
        for row in rows:
            metadata = source_index.get(case_id(row), {})
            signatures = metadata.get("canonical_signatures", row.get("canonical_signatures", []))
            audit.add(row, signatures)
            encoded = tokenize_assistant_only(row, tokenizer, max_sequence_tokens)
            lengths[len(encoded["input_ids"])] += 1
            completions[encoded["completion_tokens"]] += 1
            by_mode[row["mode"]] += 1
            by_split[row.get("split", "train")] += 1
            by_grade[str(row.get("grade", metadata.get("grade", "unknown")))] += 1
            by_topic[row.get("selection_category", metadata.get("topic", row.get("topic", "baseline")))] += 1
            stream_hash.update((canonical_json(row) + "\n").encode())
        result = audit.finish()
    finally:
        audit.close()
    result.update({"status": "PASSED", "model": MODEL, "revision": REVISION,
                   "enable_thinking": False, "full_selected_view_audited": True,
                   "all_archived_six_million_chat_audited": False, "model_training_started": False,
                   "max_sequence_tokens": max(lengths, default=0),
                   "configured_sequence_limit": max_sequence_tokens,
                   "max_completion_tokens": max(completions, default=0),
                   "sequence_length_histogram": dict(lengths), "completion_length_histogram": dict(completions),
                   "by_mode": dict(by_mode), "by_split": dict(by_split), "by_grade": dict(by_grade),
                   "by_topic": dict(by_topic), "selected_rows_sha256": stream_hash.hexdigest(),
                   "assistant_only_mask": True, "exact_one_assistant_eot": True,
                   "truncation": False, "legacy_numeric_overlap_disclosure_required": True,
                   "split_audit_scope": "selected release only, not archived old protected benchmarks"})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--drive-root", required=True)
    parser.add_argument("--tokenizer", default=MODEL)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--source-jsonl", action="append", default=[])
    args = parser.parse_args()
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    stream = ManifestStream(manifest, args.drive_root)
    receipt = full_token_audit(stream, load_qwen_tokenizer(args.tokenizer), load_source_index(args.source_jsonl))
    save_json(args.receipt, receipt)
    print(canonical_json({key: value for key, value in receipt.items() if not key.endswith("histogram")}))


if __name__ == "__main__":
    main()
