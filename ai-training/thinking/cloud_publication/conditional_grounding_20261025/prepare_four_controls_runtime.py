"""Prepare additive quality-recovery metadata controls. Import has no API effects.

The caller supplies fresh verified parent refs, canonical context bytes, explicit
metadata/code evidence and an actual observation captured by the controller.
This module neither discovers corpus/model files nor invents process/checkpoint
claims. Call the separate adapted transaction helper to publish prepared bytes.
"""
from __future__ import annotations
import hashlib, json, zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

KINDS = ("progress", "chat", "context", "state")
IDS = {"progress":"1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX", "chat":"1tkSQoAlxXXRUg2AwYfvqsFKVEmM_LmR6", "context":"13gdIPQTFKcekoQQtgo0TXc7RgeadzIN9", "state":"1TLoQIbrRVmgsg-2uiUujCfM3HrK62Yme"}
EXT = {"progress":".zip", "chat":".json", "context":".md", "state":".json"}
MAX_FILE = 2 * 1024 * 1024
MAX_ADDITIONS = 8 * 1024 * 1024
MAX_CONTROL = 32 * 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)+"\n").encode("utf-8")


def strict_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate metadata key: " + key)
        value[key] = item
    return value


def read_json_bytes(data):
    return json.loads(data.decode("utf-8"), object_pairs_hook=strict_object,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError("nonfinite metadata")))


def pin(path, file_id):
    data = path.read_bytes()
    if len(data) > MAX_CONTROL:
        raise ValueError("control exceeds bounded transaction limit")
    return {"id":file_id, "bytes":len(data), "sha256":digest(data), "path":str(path)}


def capture_branch_metadata(root, *, worker_observation):
    """Read metadata only; caller must supply a fresh real process observation.

    worker_observation must contain observed_utc and worker_alive (bool), obtained
    by the caller from its actual child process/thread, not a default value.
    Publisher checkpoint proofs remain verbatim observations, not new attestations.
    """
    if not isinstance(worker_observation, dict) or type(worker_observation.get("worker_alive")) is not bool or not worker_observation.get("observed_utc"):
        raise ValueError("explicit timestamped actual worker observation required")
    root = Path(root)
    result = {"observed_utc":worker_observation["observed_utc"], "worker_alive":worker_observation["worker_alive"],
              "worker_observation":worker_observation, "metadata_files":{}}
    # No recursive scan, generation directory, corpus, model or successful-ID log.
    for name in ("owner_run_scope.json", "owner_scope_binding_v2.json", "active_code_raw_verified.json", "metadata_serialization_repair.json", "training/run_config.json", "training/progress.json",
                 "training/native_first_microbatch_audit.json", "training/latest.json", "training/best.json", "training/run_complete.json", "training/error.json",
                 "training/final_semantic_assessment.json", "final_semantic_assessment.json",
                 "publication/publication_status.json", "publication/json/latest_checkpoint.json",
                 "publication/json/selected_best_checkpoint.json", "publication/json/training_complete_publication_proof.json"):
        path = root / name
        if path.is_file():
            before = path.stat()
            if before.st_size > MAX_FILE:
                raise ValueError("metadata file too large: " + name)
            data = path.read_bytes()
            after = path.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns) or len(data) != before.st_size:
                raise RuntimeError("metadata changed during capture; retry: " + name)
            result["metadata_files"][name] = {"bytes":len(data), "sha256":digest(data), "snapshot":read_json_bytes(data)}
    progress = result["metadata_files"].get("training/progress.json", {}).get("snapshot", {})
    if type(progress.get("training_started")) is bool:
        result["training_started"] = progress["training_started"]
    return result


def prepare_controls(parent_refs, canonical_context_bytes, actual_observation, evidence_paths, output_dir, *, run_metadata=None):
    """Stage four next_* controls; never writes supplied parents/canonical file.

    parent_refs: {kind:{id,bytes,sha256,path,fresh_raw_readback_verified:true}}
    evidence_paths: explicit {archive_relative_name:local_runtime_metadata_path}.
    actual_observation: output of capture_branch_metadata or supplied equivalent.
    output_dir: fresh runtime staging directory; reusing it is rejected.
    """
    if set(parent_refs) != set(KINDS) or len({x["id"] for x in parent_refs.values()}) != 4:
        raise ValueError("exactly four distinct existing controls required")
    parents = {}
    for kind in KINDS:
        ref = parent_refs[kind]
        if ref.get("id") != IDS[kind] or ref.get("fresh_raw_readback_verified") is not True:
            raise ValueError("control ID/fresh-parent proof mismatch: " + kind)
        path = Path(ref["path"]).resolve(strict=True)
        if path.stat().st_size > MAX_CONTROL:
            raise ValueError("parent control too large")
        data = path.read_bytes()
        if (len(data), digest(data)) != (ref["bytes"], ref["sha256"]):
            raise ValueError("parent control raw pin mismatch: " + kind)
        parents[kind] = data
    if not isinstance(canonical_context_bytes, bytes) or not canonical_context_bytes.startswith(parents["context"]):
        raise ValueError("supplied canonical context must preserve the exact fresh parent prefix")
    canonical_context_bytes.decode("utf-8")
    if len(canonical_context_bytes) > MAX_FILE:
        raise ValueError("canonical context too large")
    if not isinstance(actual_observation, dict) or type(actual_observation.get("worker_alive")) is not bool or not actual_observation.get("observed_utc"):
        raise ValueError("actual observation needs explicit observed_utc and worker_alive")
    observation_bytes = json_bytes(actual_observation)
    if len(observation_bytes) > MAX_FILE:
        raise ValueError("branch observation too large; supply metadata only")
    observation_sha = digest(observation_bytes)
    if run_metadata is None:
        run_metadata = {}
    if not isinstance(run_metadata, dict) or len(json_bytes(run_metadata)) > MAX_FILE:
        raise ValueError("run metadata must be a bounded explicit JSON object")
    run_metadata_sha = digest(json_bytes(run_metadata))
    publication_sha = digest(json_bytes({"observation_sha256":observation_sha,
                         "run_metadata_sha256":run_metadata_sha,"context_sha256":digest(canonical_context_bytes)}))
    prefix = "conditional_grounding_20261025/publications/" + publication_sha[:20] + "/"
    additions = {prefix+"actual_branch_observation.json":observation_bytes,
                 prefix+"canonical_context.md":canonical_context_bytes}
    evidence_index = []
    for relative, value in sorted(evidence_paths.items()):
        rel = PurePosixPath(relative)
        path = Path(value).resolve(strict=True)
        if not relative or rel.is_absolute() or ".." in rel.parts or "\\" in relative or path.suffix.lower() not in {".py", ".json", ".md", ".txt"}:
            raise ValueError("evidence must be explicitly named bounded code/metadata: " + relative)
        if path.stat().st_size > MAX_FILE:
            raise ValueError("evidence too large: " + relative)
        data = path.read_bytes()
        data.decode("utf-8")
        if path.suffix.lower() == ".json":
            read_json_bytes(data)
        name = prefix + "evidence/" + rel.as_posix()
        if name in additions:
            raise ValueError("duplicate addition path")
        additions[name] = data
        evidence_index.append({"path":rel.as_posix(),"bytes":len(data),"sha256":digest(data)})
    branch = {"branch":"conditional_grounding_20261025", "actual_observation":actual_observation,
              "run_metadata":run_metadata,"run_metadata_sha256":run_metadata_sha,
              "actual_observation_sha256":observation_sha, "canonical_context_sha256":digest(canonical_context_bytes),
              "metadata_only":True, "source_and_full_corpus_preserved":True, "new_case_count":0,"new_chat_count":0,
              "production_approval":False,"semantic_quality_certified":False,"whole_corpus_training_claimed":False,
              "evidence_files":evidence_index,"prepared_utc":datetime.now(timezone.utc).isoformat()}
    branch["worker_alive"] = actual_observation["worker_alive"]
    if "training_started" in actual_observation:
        if type(actual_observation["training_started"]) is not bool:
            raise ValueError("supplied training_started must be an observed boolean")
        branch["training_started"] = actual_observation["training_started"]
    additions[prefix+"branch_manifest.json"] = json_bytes(branch)
    if sum(map(len, additions.values())) > MAX_ADDITIONS:
        raise ValueError("metadata additions exceed bounded size")
    out = Path(output_dir).resolve()
    if out.exists():
        raise FileExistsError("use a fresh staging directory")
    out.mkdir(parents=True)
    # Retain pinned parents inside the staging directory for the transaction guard.
    retained_refs = {}
    for kind in KINDS:
        path = out / ("parent_" + kind + EXT[kind])
        path.write_bytes(parents[kind])
        retained_refs[kind] = {**pin(path, IDS[kind]),"fresh_raw_readback_verified":True}
    progress = out / "next_progress.zip"
    with zipfile.ZipFile(retained_refs["progress"]["path"]) as old, zipfile.ZipFile(progress,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as new:
        names = old.namelist()
        if len(names) != len(set(names)):
            raise ValueError("parent progress has duplicate members")
        for info in old.infolist():
            new.writestr(info, old.read(info.filename))
        for name, data in additions.items():
            if name in names:
                raise ValueError("publication member already exists; use a newer actual observation")
            new.writestr(name, data)
    with zipfile.ZipFile(retained_refs["progress"]["path"]) as old, zipfile.ZipFile(progress) as new:
        if not set(old.namelist()).issubset(new.namelist()) or any(old.read(n) != new.read(n) for n in old.namelist()):
            raise AssertionError("prior progress ZIP member changed")
    for kind in ("chat", "state"):
        doc = read_json_bytes(parents[kind])
        history = doc.setdefault("conditional_grounding_control_publications", [])
        if not isinstance(history, list):
            raise ValueError("existing quality-recovery branch history is not a list")
        previous = doc.get("latest_conditional_grounding_branch")
        if previous is not None and (not history or history[-1] != previous):
            history.append(previous)
        doc["latest_conditional_grounding_branch"] = branch
        (out / ("next_"+kind+EXT[kind])).write_bytes(json_bytes(doc))
    (out/"next_context.md").write_bytes(canonical_context_bytes)
    prepared = {kind:pin(out/("next_"+kind+EXT[kind]),IDS[kind]) for kind in KINDS}
    result = {"parents":retained_refs,"controls":prepared,"state_must_be_written_last":True,
              "old_progress_members_preserved_byte_for_byte":True,"new_case_count":0,"new_chat_count":0,
              "actual_observation_sha256":observation_sha,"run_metadata_sha256":run_metadata_sha,"drive_calls_made":False}
    (out/"prepared_control_updates.json").write_bytes(json_bytes(result))
    return result
