"""Account-neutral DATA-ONLY work ledger. No network, credentials or training.

Exported JSON is the portable handoff; conversation IDs and connector link IDs
are deliberately absent from task identity. Use one coordinator with optimistic
revision checking when saving it to an EXISTING Drive control ID. A local lock
cannot arbitrate concurrent writers in separate machines/Drive sync replicas.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import time
import uuid

SCHEMA = "MathVisionKid.portable_data_resume.v1"


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".atomic")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def safe_metadata(value):
    """Portable state must never transport connector authority or credentials."""
    forbidden = {"link_id", "access_token", "refresh_token", "api_key", "credentials", "authorization"}
    if isinstance(value, dict):
        for key, child in value.items():
            if key.casefold() in forbidden:
                raise ValueError("runtime authority/secret cannot enter portable state: " + key)
            safe_metadata(child)
    elif isinstance(value, list):
        for child in value:
            safe_metadata(child)


def task_spec(action, inputs, parameters=None, scope="candidate_data"):
    if scope not in ("candidate_data", "metadata_only", "semantic_mapping"):
        raise ValueError("frozen/evaluation/pilot payload work is excluded")
    for entry in inputs:
        if not re.fullmatch(r"[a-f0-9]{64}", entry.get("sha256", "")):
            raise ValueError("content hash required for each task input")
        if entry.get("role") in ("sealed", "pilot", "frozen_evaluation"):
            raise ValueError("frozen source separation")
    def no_runtime_identity(value):
        forbidden = {"profile_id", "selected_profile", "observed_profile", "selected_runtime_profile",
                     "runtime_binding", "codex_account", "thread_id", "agent_id", "worker_id", "email"}
        if isinstance(value, dict):
            for name, child in value.items():
                if name.casefold() in forbidden:
                    raise ValueError("runtime identity cannot determine task content hash: " + name)
                no_runtime_identity(child)
        elif isinstance(value, list):
            for child in value:
                no_runtime_identity(child)
    # Artifact locators remain in the outer catalog. A changed mount path,
    # connector link, filename, or duplicate locator must not fork the work key.
    locators = {"file_id", "id", "file_name", "url", "relative_path", "path"}
    identities = [{k:deepcopy(v) for k,v in entry.items() if k not in locators} for entry in inputs]
    spec = {"action": action, "inputs": sorted(identities, key=canonical),
            "parameters": parameters or {}, "scope": scope, "training_started": False}
    no_runtime_identity(spec)
    safe_metadata(spec)
    return spec


def new_checkpoint(artifacts, data_owner_history=()):
    value = {"schema": SCHEMA, "revision": 0, "artifacts": deepcopy(artifacts),
             "data_owner_history": list(data_owner_history), "tasks": {},
             "completed": {}, "training_started": False,
             "coordination": "ONE_COORDINATOR_EXISTING_CONTROL_ID_COMPARE_REVISION_BEFORE_UPDATE"}
    safe_metadata(value)
    return value


def add_task(checkpoint, spec):
    safe_metadata(spec)
    key = digest(spec)
    prior = checkpoint["tasks"].setdefault(key, {"spec": deepcopy(spec), "status": "PENDING",
                                                "attempt": 0, "lease": None, "progress": {}})
    if prior["spec"] != spec:
        raise ValueError("task hash collision")
    return key


def rebind(checkpoint, selected_profile, observed_profile, observations, requested="read"):
    """Return ephemeral runtime binding, without altering owner history/IDs.

    Each observation must be fresh evidence from the selected connector, with
    exact artifact ID/hash. Read access is never promoted to update rights.
    Link IDs can be supplied by the caller to its connector, never persisted here.
    """
    if requested not in ("read", "update") or selected_profile != observed_profile:
        raise ValueError("selected connector profile mismatch")
    for name, expected in checkpoint["artifacts"].items():
        actual = observations.get(name, {})
        if not actual.get("fresh_raw_verified") or any(actual.get(k) != expected.get(k)
                for k in ("file_id", "sha256", "bytes")):
            raise ValueError("exact-ID/hash revalidation required: " + name)
        if requested == "update" and actual.get("can_update") is not True:
            raise ValueError("update rights unproven: " + name)
    return {"selected_runtime_profile": selected_profile, "access": requested,
            "verified_artifact_ids": [x["file_id"] for x in checkpoint["artifacts"].values()],
            "data_owner_history_changed": False, "create_duplicates_allowed": False}


def claim(checkpoint, key, worker, now=None, ttl=1800):
    now = time.time() if now is None else now
    if ttl <= 0:
        raise ValueError("positive lease TTL required")
    item = checkpoint["tasks"][key]
    if item["status"] == "COMPLETE":
        return None
    lease = item["lease"]
    if lease and lease["expires"] > now:
        raise ValueError("task already leased")
    item["attempt"] += 1
    token = uuid.uuid4().hex
    item.update(status="LEASED", lease={"token": token, "worker": worker,
                "expires": now + ttl, "attempt": item["attempt"]})
    checkpoint["revision"] += 1
    return token


def acknowledge(checkpoint, key, token, progress=None, result=None, now=None):
    now = time.time() if now is None else now
    item = checkpoint["tasks"][key]
    lease = item["lease"]
    if not lease or lease["token"] != token or lease["expires"] <= now:
        raise ValueError("stale lease")
    safe_metadata(progress or {})
    if progress is not None:
        item["progress"] = deepcopy(progress)
    if result is not None:
        safe_metadata(result)
        prior = checkpoint["completed"].get(key)
        if prior and prior != result:
            raise ValueError("conflicting result")
        checkpoint["completed"][key] = deepcopy(result)
        item.update(status="COMPLETE", lease=None, result_sha256=digest(result))
    checkpoint["revision"] += 1


def merge_results(checkpoint, exported, expected_revision):
    """Idempotent import of results, never stale leases or status overlays."""
    if checkpoint["revision"] != expected_revision:
        raise ValueError("coordinator revision changed; reload before merge")
    if checkpoint["artifacts"] != exported["artifacts"]:
        raise ValueError("artifact identity/hash changed")
    safe_metadata(exported)
    pending = []
    for key, result in exported["completed"].items():
        if key not in exported["tasks"] or digest(exported["tasks"][key]["spec"]) != key:
            raise ValueError("invalid exported task identity")
        item = checkpoint["tasks"].get(key)
        if not item or item["spec"] != exported["tasks"][key]["spec"]:
            raise ValueError("unrecognized task")
        if exported["tasks"][key].get("result_sha256") != digest(result):
            raise ValueError("result integrity mismatch")
        if key in checkpoint["completed"] and checkpoint["completed"][key] != result:
            raise ValueError("conflicting result requires review")
        pending.append((key, result))
    changed = False
    for key, result in pending:
        if key not in checkpoint["completed"]:
            checkpoint["completed"][key] = deepcopy(result)
            checkpoint["tasks"][key].update(status="COMPLETE", lease=None, result_sha256=digest(result))
            changed = True
    if changed:
        checkpoint["revision"] += 1
    return changed


class Ledger:
    """Serialized local transactions; export is the cross-account checkpoint."""
    def __init__(self, path):
        self.db = sqlite3.connect(path, timeout=30)
        self.db.execute("CREATE TABLE IF NOT EXISTS ledger(id INTEGER PRIMARY KEY CHECK(id=1), document TEXT)")

    def initialize(self, checkpoint):
        safe_metadata(checkpoint)
        with self.db:
            self.db.execute("INSERT INTO ledger VALUES(1,?)", (canonical(checkpoint),))

    def mutate(self, function, *args, **kwargs):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute("SELECT document FROM ledger WHERE id=1").fetchone()
            if not row:
                raise ValueError("initialize ledger first")
            checkpoint = json.loads(row[0])
            result = function(checkpoint, *args, **kwargs)
            self.db.execute("UPDATE ledger SET document=? WHERE id=1", (canonical(checkpoint),))
            self.db.commit()
            return result
        except Exception:
            self.db.rollback()
            raise

    def export(self):
        return json.loads(self.db.execute("SELECT document FROM ledger WHERE id=1").fetchone()[0])

    def close(self):
        self.db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--export", required=True)
    args = parser.parse_args()
    ledger = Ledger(args.ledger)
    try:
        if not ledger.db.execute("SELECT 1 FROM ledger").fetchone():
            ledger.initialize(json.loads(Path(args.checkpoint).read_text("utf-8")))
        save(args.export, ledger.export())
    finally:
        ledger.close()


if __name__ == "__main__":
    main()
