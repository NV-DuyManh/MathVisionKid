"""Hierarchical deterministic one-pass balanced view; source rows stay intact."""
import hashlib
import json
from collections import Counter, defaultdict, deque

MODES = {"worked_solution", "hint_level_1", "hint_level_2", "hint_level_3"}


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _behavior(row):
    try:
        prompt = json.loads(row["messages"][1]["content"])
        target = json.loads(row["messages"][-1]["content"])
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid prompt/target JSON") from exc
    if not isinstance(prompt, dict) or not isinstance(target, dict):
        raise ValueError("prompt and target must be JSON objects")
    if prompt.get("mode") != row["mode"]:
        raise ValueError("prompt mode differs from row mode")
    if row["mode"] == "worked_solution" and target.get("can_solve") is False:
        return "guard"
    if prompt.get("student_work") is not None:
        return "student_feedback"
    return "standard"


def prepare_plan(raw_rows, source_sha, seed=20261024):
    """Deduplicate within grade/topic/mode/behavior, then hierarchically weave.

    One visit per extant topic/provenance group occurs before a second visit.
    Visits are round-robined by grade, then by behavior+mode within grade, then
    by topic/provenance within that bucket. Empty topics use identity only as
    provenance partition; this does not infer conceptual skill.
    """
    if not isinstance(raw_rows, list):
        raise ValueError("raw_rows must be a list")
    if not isinstance(source_sha, str) or len(source_sha) != 64 or any(c not in "0123456789abcdefABCDEF" for c in source_sha):
        raise ValueError("source_sha must be a 64-character SHA256 hex string")
    ids, buckets = set(), defaultdict(list)
    for i, row in enumerate(raw_rows):
        if not isinstance(row, dict) or row.get("split") != "train":
            raise ValueError("nontrain or invalid input row")
        sid, mode = row.get("sample_id"), row.get("mode")
        if not isinstance(sid, str) or not sid or sid in ids:
            raise ValueError("missing or duplicate sample_id")
        ids.add(sid)
        if not isinstance(mode, str) or mode not in MODES:
            raise ValueError("invalid mode")
        if type(row.get("grade")) is not int or row["grade"] not in range(1, 6):
            raise ValueError("invalid grade")
        if not isinstance(row.get("messages"), list) or len(row["messages"]) < 3:
            raise ValueError("invalid messages")
        behavior = _behavior(row)
        topic = row.get("topic")
        topic_key = ("topic", str(topic)) if topic else (
            "unlabeled_case", str(row.get("case_group_id") or row.get("source_sample_id") or sid))
        try:
            target = json.loads(row["messages"][-1]["content"])
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid assistant target JSON") from exc
        if not isinstance(target, dict):
            raise ValueError("assistant target must be a JSON object")
        target_hash = _sha(_canonical(target).encode("utf-8"))
        group = (row["grade"], topic_key, mode, behavior)
        buckets[(group, target_hash)].append(i)

    def rank(i):
        return _sha((str(seed) + "|" + raw_rows[i]["sample_id"]).encode("utf-8"))

    groups, provenance = defaultdict(list), {}
    for (group, _target_hash), members in buckets.items():
        rep = min(members, key=rank)
        groups[group].append(rep)
        provenance[raw_rows[rep]["sample_id"]] = sorted(raw_rows[i]["sample_id"] for i in members)

    # Within each grade, rotate behavior+mode buckets and their topic queues.
    # Then rotate grades, so abundant grade-1 groups cannot delay grade 5.
    per_grade = {}
    member_queues = {group: deque(sorted(members, key=rank)) for group, members in groups.items()}
    original_group_counts = {group: len(members) for group, members in groups.items()}
    for grade in range(1, 6):
        mode_buckets = defaultdict(list)
        for group in groups:
            if group[0] == grade:
                mode_buckets[(group[3], group[2])].append(group)
        bucket_order = sorted(mode_buckets)
        topic_queues = {
            key: deque(sorted(mode_buckets[key], key=lambda g: (g[1], g[0])))
            for key in bucket_order
        }
        group_sequence = []
        while any(topic_queues.values()):
            for key in bucket_order:
                if topic_queues[key]:
                    group_sequence.append(topic_queues[key].popleft())
        per_grade[grade] = group_sequence
    grade_cursor = {grade: 0 for grade in range(1, 6)}

    schedule = []
    while any(member_queues.values()):
        for grade in range(1, 6):
            sequence = per_grade[grade]
            if not sequence:
                continue
            # One group visit per grade per round. Advance cyclically over the
            # prewoven behavior+mode/topic sequence, skipping exhausted groups.
            for offset in range(len(sequence)):
                pos = (grade_cursor[grade] + offset) % len(sequence)
                group = sequence[pos]
                if member_queues[group]:
                    schedule.append((group, member_queues[group].popleft()))
                    grade_cursor[grade] = (pos + 1) % len(sequence)
                    break

    selected = []
    for _, i in schedule:
        row = raw_rows[i]
        selected.append({
            "sample_id": row["sample_id"],
            "selected_index": i,
            "canonical_embedded_row_sha256": _sha(_canonical(row).encode("utf-8")),
            "assistant_target_sha256": _sha(row["messages"][-1]["content"].encode("utf-8")),
            "behavior": _behavior(row),
        })
    return {
        "schema": "MathVisionKid.balanced_training_plan.v2",
        "source_raw_sha256": source_sha.lower(),
        "seed": seed,
        "source_rows": len(raw_rows),
        "view_rows": len(schedule),
        "deduplicated_rows_in_view": len(raw_rows) - len(schedule),
        "source_rows_modified_or_deleted": 0,
        "sampling": "one pass; outer grade round robin; inner behavior+mode then topic/provenance round robin",
        "topic_fallback": "blank topics partition by case_group_id, then source_sample_id, then sample_id; provenance only",
        "duplicate_rule": "one canonical assistant-target representative per grade/topic-or-fallback/mode/behavior; source IDs retained in representative_provenance",
        "behavior_counts": dict(Counter(x["behavior"] for x in selected)),
        "group_counts": {"|".join(map(str, g)): original_group_counts[g] for g in sorted(groups)},
        "schedule": [raw_rows[i]["sample_id"] for _, i in schedule],
        "selected_rows": selected,
        "representative_provenance": provenance,
        "hash_note": "source_raw_sha256 binds original raw JSONL externally; canonical_embedded_row_sha256 hashes canonical parsed JSON, not original raw JSONL line bytes",
    }
