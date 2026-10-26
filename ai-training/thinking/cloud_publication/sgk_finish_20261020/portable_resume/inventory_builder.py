"""Rebuild finite metadata catalog from retained verified references, no network."""
import io
import json
from pathlib import Path
import sys
import zipfile
from collections import Counter

OUT = Path(__file__).resolve().parent
THINKING = OUT.parents[2]
sys.path.insert(0, str(THINKING))
import math_data_portable_resume as P

OLD = THINKING / "cloud_publication/sgk_page_audit_20261019"


def read(path):
    return json.loads(path.read_text("utf-8"))


def build():
    state = read(THINKING / "exhaustive_cloud_reference.json")
    registry = read(THINKING / "data/primary_math_teacher_20261016/drive_artifacts.json")
    artifacts, members, discoveries = {}, [], []
    def artifact(ref, family):
        fid = ref.get("file_id", ref.get("id"))
        item = {"file_id": fid, "sha256": ref["sha256"], "bytes": ref["bytes"],
                "file_name": ref.get("file_name", ref.get("name")), "family": family}
        if fid in artifacts and artifacts[fid] != item:
            raise ValueError("same artifact ID has conflicting content identity")
        artifacts[fid] = item
        return item
    def member(a, name, ref, role, rows=None, status="REFERENCE_PINNED_NOT_PROCESSED"):
        m = {**a, "member": name, "member_sha256": ref.get("sha256") if name else None,
             "member_bytes": ref.get("bytes") if name else None, "role": role,
             "rows": rows, "status": status}
        members.append(m)
        return m
    for ref in state["parts"]:
        a = artifact(ref, "original_corpus" if ref["kind"] == "corpus_zip" else "original_chat")
        if ref["kind"] == "chat_gzip":
            member(a, None, {}, "candidate_chat", ref["chat_rows"])
        else:
            discoveries.append({**a, "status": "PENDING_CENTRAL_DIRECTORY_AND_MANIFEST_DISCOVERY",
                "instruction": "Read hash-pinned archive central directory/manifest only. Never open frozen/sealed/pilot payloads. Assign exact source members to existing chats; no wildcard JSONL concatenation."})
    for shard in state["extension_shards"]:
        a = artifact({**shard["bundle"], "file_id": shard["file_id"], "file_name": shard["remote_name"]}, "numeric_extension")
        member(a, shard["source"]["name"], shard["source"], "candidate_source", shard["cases"])
        member(a, shard["view"]["name"], shard["view"], "candidate_chat", shard["chat_rows"])
        # The two data members are pinned by the current state. Extra manifest/
        # validation members remain metadata discovery, never implicit chats.
        discoveries.append({**a, "status": "PENDING_EXTRA_METADATA_MEMBER_CATALOG", "known_data_members": [shard["source"]["name"], shard["view"]["name"]]})
    balanced = artifact(state["balanced_release"]["bundle"], "balanced_plus_supplement_history")
    current = {"audit/boundary_cases.jsonl": ("candidate_source", 69),
               "audit/boundary_chat.jsonl": ("candidate_chat", 216),
               "audit/pedagogy_cases_v3.jsonl": ("candidate_source", 60),
               "audit/pedagogy_chat_v3.jsonl": ("candidate_chat", 240),
               "audit/holdout_arithmetic_cases_v2.jsonl": ("evaluation_only", 8),
               "audit/holdout_arithmetic_chat_v2.jsonl": ("evaluation_only", 32)}
    for path in sorted((OLD / "prior_balanced").rglob("*")):
        if not path.is_file():
            continue
        name = path.relative_to(OLD / "prior_balanced").as_posix()
        role, count = current.get(name, ("audit_history_or_metadata", None))
        item = member(balanced, name, {"sha256": P.file_hash(path), "bytes": path.stat().st_size}, role, count,
                      "LOCAL_RESTORED_REFERENCE_HASHED_NO_FULL_REMOTE_REPLAY_THIS_RUN")
        if name == "audit/pedagogy_chat_v3.jsonl":
            item["split_rows"] = {"train": 192, "validation": 24, "test": 24}
            item["future_training_filter"] = "split == train"
        elif name == "audit/boundary_chat.jsonl":
            item["note"] = "69 source cases retained; 54 cases/216 chat exported after protected filter. Do not synthesize missing60 rows."
    selected_manifest = read(OLD / "prior_balanced/balanced_release/MathVisionKid_BALANCED_TRAINING_MANIFEST.json")
    for ref in selected_manifest["shards"]:
        member(balanced, "balanced_release/" + ref["file_name"], ref, "diagnostic_duplicate_excluded", ref["chat_rows"])
    discoveries.append({**balanced, "status": "PENDING_COMPLETE_REMOTE_MEMBER_LIST", "instruction": "Local restored subset is catalogued; compare complete central directory and preserve selected diagnostic duplicates excluded from full-corpus union."})
    for run in state.get("sgk_gap_runs", []) + state.get("sgk_page_runs", []):
        a = artifact(run["bundle"], run["run_id"])
        if run["run_id"] == "sgk_page_audit_20261019":
            path = Path(read(OLD / "bundle_local.json")["path"])
            if path.stat().st_size != a["bytes"] or P.file_hash(path) != a["sha256"]:
                raise ValueError("latest110 retained archive mismatch")
            with zipfile.ZipFile(path) as z:
                manifest = json.loads(z.read("manifest.json"))
                names = z.namelist()
                if len(names) != len(set(names)) or set(names) != set(manifest["members"]) | {"manifest.json"}:
                    raise ValueError("latest archive list/manifest mismatch")
                member(a, "manifest.json", {"sha256": __import__('hashlib').sha256(z.read("manifest.json")).hexdigest(), "bytes": z.getinfo("manifest.json").file_size}, "metadata_only")
        else:
            manifest = read(OLD / "prior_append/manifest.json")
            member(a, "manifest.json", {"sha256": P.file_hash(OLD / "prior_append/manifest.json"), "bytes": (OLD / "prior_append/manifest.json").stat().st_size}, "metadata_only")
        for name, ref in manifest["members"].items():
            role = "candidate_chat" if name == run["chat_member"] else "candidate_source" if name == run["source_member"] else "audit_history_or_metadata"
            count = run["chat_rows"] if role == "candidate_chat" else run["cases"] if role == "candidate_source" else None
            member(a, name, ref, role, count)
    catalog = {"schema": "MathVisionKid.full_archive_member_catalog.v1", "artifacts": artifacts,
               "members": members, "pending_discoveries": discoveries, "training_started": False,
               "complete_remote_member_inventory": False,
               "counts": {"candidate_chat_rows": 6501044, "current_chat_rows_including_current_eval": 6501124,
                          "superseded_arithmetic_holdout_v1_audit_rows": 32, "all_rows_including_audit": 6501156},
               "frozen_policy": "Metadata/hash only. No sealed challenge or pilot payload reads. Frozen V3/V4, owner299 and old payloads are not modified or promoted to train."}
    P.save(OUT / "member_catalog.json", catalog)
    # Stable control IDs are locators; their historical hashes are anchors.
    # Root must refresh mutable hashes before publishing a new control revision.
    controls = read(OLD / "four_controls_remote_verified.json")
    control_refs = {name:{"file_id": fid, **{k:next(x for x in controls if x['id']==fid)[k] for k in ('sha256','bytes')}} for name,fid in state['control_ids'].items()}
    history = [{k:v for k,v in item.items() if k in ("email", "name", "profile_id")} for item in registry.get("account_identity_history", [])]
    history.append({k:v for k,v in registry["account_identity"].items() if k in ("email", "name", "profile_id")})
    checkpoint = P.new_checkpoint(artifacts, history)
    checkpoint["control_pointers"] = {name:{"file_id":ref['file_id'], "hash_policy":"FRESH_RAW_MONOTONIC_REVISION_NOT_FROZEN_CONTENT"} for name,ref in control_refs.items()}
    checkpoint["pinned_input_state_sha256"] = control_refs['state']['sha256']
    checkpoint["pinned_input_state_note"] = "Historical input snapshot only. Mutable state content changes after publication; never require its old hash or embed a self hash."
    checkpoint["identity_history_semantics"] = "Historical publication identities, not a claim of current Drive ownership. Chosen runtime profile must be freshly verified; Codex account/chat/agent IDs are not authority."
    checkpoint["catalog_sha256"] = P.digest(catalog)
    checkpoint["expected_counts"] = catalog["counts"]
    for index, entry in enumerate(members):
        if entry["role"] not in ("candidate_source", "candidate_chat"):
            continue
        spec = P.task_spec("CPU_DATA_ONLY_MEMBER_AUDIT", [{"sha256": entry["sha256"], "member": entry["member"], "member_sha256": entry["member_sha256"]}], {"role":entry["role"], "tokenizer_revision": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e", "auditor_schema":"archive_audit.v2"})
        key = P.add_task(checkpoint, spec)
        checkpoint["tasks"][key]["catalog_entry"] = index
    for discovery in discoveries:
        P.add_task(checkpoint, P.task_spec("DISCOVER_HASH_PINNED_METADATA_MEMBERS", [{"sha256": discovery["sha256"]}], {"family": discovery["family"]}, "metadata_only"))
    P.add_task(checkpoint, P.task_spec("FINAL_GLOBAL_SPLIT_RECONCILIATION", [{"sha256":P.digest(catalog)}], {"frozen_comparison":"known-protected hash index only; no sealed/pilot payload", "require_complete_source_signatures":True}, "metadata_only"))
    checkpoint_path = OUT / "portable_checkpoint.json"
    if checkpoint_path.exists():
        previous = read(checkpoint_path)
        if any(artifacts.get(key) != value for key,value in previous['artifacts'].items()):
            raise ValueError('immutable artifact removed/changed; review required before replacing checkpoint')
        for key,item in previous['tasks'].items():
            if P.digest(item['spec']) != key:
                raise ValueError('previous task integrity mismatch')
            if key not in checkpoint['tasks']:
                # Discovery can append valid tasks with another fixed catalog.
                # Rebuilding the base catalog must never discard that work.
                checkpoint['tasks'][key] = item
                if key in previous['completed']:
                    result = previous['completed'][key]
                    if item.get('result_sha256') != P.digest(result):
                        raise ValueError('previous result integrity mismatch')
                    checkpoint['completed'][key] = result
                continue
            if item['spec'] != checkpoint['tasks'][key]['spec']:
                raise ValueError('previous task content mismatch')
            current_entry = checkpoint['tasks'][key].get('catalog_entry')
            checkpoint['tasks'][key] = item
            if current_entry is not None:
                checkpoint['tasks'][key]['catalog_entry'] = current_entry
            if key in previous['completed']:
                result = previous['completed'][key]
                if item.get('result_sha256') != P.digest(result):
                    raise ValueError('previous result integrity mismatch')
                checkpoint['completed'][key] = result
        changed = set(checkpoint['tasks']) != set(previous['tasks']) or checkpoint['catalog_sha256'] != previous.get('catalog_sha256')
        checkpoint['revision'] = previous['revision'] + int(changed)
        for key in ('discovered_catalog_sha256','catalog_lineage_note'):
            if key in previous:
                checkpoint[key] = previous[key]
    P.save(checkpoint_path, checkpoint)
    P.save(OUT / "inventory_receipt.json", {"artifacts":len(artifacts), "members_catalogued":len(members),
        "member_roles": dict(Counter(x["role"] for x in members)), "finite_tasks":len(checkpoint["tasks"]),
        "remote_discoveries_pending":sum(x['spec']['action']=='DISCOVER_HASH_PINNED_METADATA_MEMBERS' and x['status']!='COMPLETE' for x in checkpoint['tasks'].values()),
        "base_catalog_metadata_requests":len(discoveries), "latest110_included":True,
        "completed_tasks":len(checkpoint['completed']), "remaining_tasks":len(checkpoint['tasks'])-len(checkpoint['completed']),
        "candidate_rows_reconciled": sum(x['rows'] for x in members if x['role']=='candidate_chat')-48,
        "full_archive_token_split_audit_complete":False, "no_new_drive_files_or_folder_created":True, "training_started":False})
    return catalog, checkpoint


if __name__ == "__main__":
    catalog, checkpoint = build()
    print(json.dumps(read(OUT / "inventory_receipt.json")))
