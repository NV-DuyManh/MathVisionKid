"""Deterministic, lossless-source balanced one-pass view of training rows."""
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
    if prompt.get("mode") != row["mode"]:
        raise ValueError("prompt mode differs from row mode")
    if row["mode"] == "worked_solution" and target.get("can_solve") is False:
        return "guard"
    if prompt.get("student_work") is not None:
        return "student_feedback"
    return "standard"


def prepare_plan(raw_rows, source_sha, seed=20261024):
    """Return a deterministic group-round-robin schedule and dedup audit map.

    Blank/missing topic rows are keyed by their case/source identity so blank
    topics are not falsely treated as one conceptual skill. Source rows are
    never mutated; identical assistant targets collapse only in this view.
    """
    if not isinstance(raw_rows, list):
        raise ValueError("raw_rows must be a list")
    if not isinstance(source_sha, str) or len(source_sha) != 64:
        raise ValueError("source_sha must be a SHA256 hex string")
    ids, buckets = set(), defaultdict(list)
    for i, row in enumerate(raw_rows):
        if not isinstance(row, dict) or row.get("split") != "train":
            raise ValueError("nontrain or invalid input row")
        sid, mode = row.get("sample_id"), row.get("mode")
        if not isinstance(sid, str) or not sid or sid in ids:
            raise ValueError("missing or duplicate sample_id")
        ids.add(sid)
        if mode not in MODES:
            raise ValueError("invalid mode")
        if type(row.get("grade")) is not int or row["grade"] not in range(1, 6):
            raise ValueError("invalid grade")
        if not isinstance(row.get("messages"), list) or len(row["messages"]) < 3:
            raise ValueError("invalid messages")
        behavior = _behavior(row)
        topic = row.get("topic")
        if topic:
            topic_key = ("topic", str(topic))
        else:
            # This is a provenance partition, not a claim about skill identity.
            fallback = row.get("case_group_id") or row.get("source_sample_id") or sid
            topic_key = ("unlabeled_case", str(fallback))
        try:
            target = json.loads(row["messages"][-1]["content"])
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid assistant target JSON") from exc
        target_hash = _sha(_canonical(target).encode("utf-8"))
        group = (row["grade"], topic_key, mode, behavior)
        buckets[(group, target_hash)].append(i)

    def rank(i):
        return _sha((str(seed) + "|" + raw_rows[i]["sample_id"]).encode("utf-8"))

    groups = defaultdict(list)
    representatives, provenance = [], {}
    for (group, target_hash), members in buckets.items():
        rep = min(members, key=rank)
        representatives.append(rep)
        provenance[raw_rows[rep]["sample_id"]] = sorted(raw_rows[i]["sample_id"] for i in members)
        groups[group].append(rep)
    # Deterministic ordering within each group; one item from every extant group
    # per round prevents large arithmetic groups dominating early updates.
    queues = {}
    for group, members in groups.items():
        queues[group] = deque(sorted(members, key=rank))
    group_order = sorted(queues, key=lambda g: (g[0], g[1], g[2], g[3]))
    schedule = []
    while any(queues.values()):
        for group in group_order:
            if queues[group]:
                schedule.append(queues[group].popleft())

    row_audit = []
    for i in schedule:
        row = raw_rows[i]
        row_audit.append({
            "sample_id": row["sample_id"],
            "selected_index": i,
            "canonical_embedded_row_sha256": _sha(_canonical(row).encode("utf-8")),
            "assistant_target_sha256": _sha(row["messages"][-1]["content"].encode("utf-8")),
            "behavior": _behavior(row),
        })
    return {
        "schema": "MathVisionKid.balanced_training_plan.v1",
        "source_raw_sha256": source_sha,
        "seed": seed,
        "source_rows": len(raw_rows),
        "view_rows": len(schedule),
        "deduplicated_rows_in_view": len(raw_rows) - len(schedule),
        "source_rows_modified_or_deleted": 0,
        "sampling": "one pass, deterministic round robin across grade/topic/mode/behavior groups",
        "topic_fallback": "blank topics partition by case_group_id, then source_sample_id, then sample_id; provenance only",
        "duplicate_rule": "one target representative per grade/topic-or-fallback/mode/behavior; all original IDs retained in representative_provenance",
        "behavior_counts": dict(Counter(x["behavior"] for x in row_audit)),
        "group_counts": {"|".join(map(str, group)): len(members) for group, members in sorted(groups.items())},
        "schedule": [raw_rows[i]["sample_id"] for i in schedule],
        "selected_rows": row_audit,
        "representative_provenance": provenance,
        "hash_note": "source_raw_sha256 binds the original raw JSONL externally; canonical_embedded_row_sha256 hashes parsed canonical JSON and is not the original raw line hash",
    }
