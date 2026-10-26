"""CPU staging builder for the low-dose branch; never launches training."""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, shutil, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT_FILES = (
    "owner_run_scope.json", "owner_scope_binding_v2.json",
    "training_view.jsonl", "sampling_manifest.json",
    "new_validation_candidates.jsonl", "derived_sampling_plan.json",
    "pretrain_qa_approved.json", "exhaustive_colab_loader.py",
    "frozen_training_primitives.py", "conditional_behavior_renderer.py",
    "inference_contract.py", "behavior_renderer.py",
    "verbal_training_renderer_v3.py",
)
CODE_FILES = (
    "recovery_worker_lowdose_20261026.py", "native_backend_20261026.py",
    "recovery_policy_20261026.py",
)

def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha(path: pathlib.Path) -> str:
    return sha_bytes(path.read_bytes())

def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")

def atomic_json(path: pathlib.Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode() + b"\n"
    with path.open("xb") as f:
        f.write(data); f.flush(); os.fsync(f.fileno())

def copy_exact(src: pathlib.Path, dst: pathlib.Path) -> str:
    data = src.read_bytes()
    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("xb") as f:
        f.write(data); f.flush(); os.fsync(f.fileno())
    if dst.read_bytes() != data:
        raise IOError(f"copy mismatch: {src}")
    return sha_bytes(data)

def bind_cache(source: pathlib.Path, target: pathlib.Path, review_files: list[pathlib.Path],
               scope: dict, contract: dict, model_proof: dict) -> dict:
    evaldir = source / "training" / "eval_step_000000"
    output_src = evaldir / "base_generations.jsonl"
    prov_src = evaldir / "base_generation_provenance.json"
    contract_src = source / "training" / "evaluation_contract.json"
    plan_src = source / "derived_sampling_plan.json"
    dev_src = source / "new_validation_candidates.jsonl"
    view_src = source / "training_view.jsonl"
    infer_src = source / "inference_contract.py"
    renderer_src = source / "conditional_behavior_renderer.py"
    fixtures = [json.loads(x) for x in dev_src.read_text(encoding="utf-8").splitlines() if x.strip()]
    if len(fixtures) != 30: raise ValueError("expected exactly 30 frozen development fixtures")
    output = output_src.read_bytes(); provenance_bytes = prov_src.read_bytes()
    provenance = json.loads(provenance_bytes)
    contract_bytes = contract_src.read_bytes()
    if json.loads(contract_bytes) != contract: raise ValueError("contract bytes differ from supplied contract")
    contract_sha = sha_bytes(contract_bytes); dev_sha = sha(dev_src)
    if contract.get("fixture_sha256") != dev_sha or dev_sha != scope["dev_sha256"]:
        raise ValueError("dev fixtures/contract/scope SHA mismatch")
    proof_sha = sha_bytes(canonical(model_proof))
    if provenance.get("model") != "Qwen/Qwen3-1.7B" or provenance.get("revision") != "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e":
        raise ValueError("base provenance is not for the pinned model/revision")
    if provenance.get("stage") != "base_before_training" or provenance.get("outputs_sha256") != sha_bytes(output):
        raise ValueError("base output provenance mismatch")
    ids = [f["id"] for f in fixtures]
    prompt_hashes = contract.get("prompt_token_sha256")
    if not isinstance(prompt_hashes, dict) or set(prompt_hashes) != set(ids):
        raise ValueError("contract prompt-token map differs from fixtures")
    seeds = {i:(20261024 + int(sha_bytes(i.encode())[:8],16)) % (2**31) for i in ids}
    rows = [json.loads(x) for x in output.decode("utf-8").splitlines() if x.strip()]
    if len(rows) != len(fixtures): raise ValueError("base outputs incomplete")
    for row, fixture in zip(rows, fixtures):
        if (row.get("fixture_id") != fixture["id"] or row.get("grade") != fixture["grade"]
            or row.get("mode") != fixture["mode"] or row.get("stage") != "base_before_training"
            or row.get("contract_sha256") != contract_sha
            or row.get("prompt_token_sha256") != prompt_hashes[fixture["id"]]
            or row.get("seed") != seeds[fixture["id"]]
            or row.get("max_new_tokens") != contract["decoding"]["max_new_tokens"]
            or row.get("timed_out") is not False or row.get("possibly_truncated") is not False
            or row.get("ended_eos") is not True):
            raise ValueError("base row is incomplete or identity-mismatched: " + fixture["id"])
    if not review_files: raise ValueError("at least one frozen review is required")
    reviews = {}
    for file in review_files:
        name = file.name
        if name in reviews: raise ValueError("duplicate frozen review basename")
        reviews[name] = sha(file)
    target.mkdir(parents=True, exist_ok=False)
    copy_exact(output_src, target / "base_generations.jsonl")
    copy_exact(prov_src, target / "base_generation_provenance.json")
    for f in review_files: copy_exact(f, target / "frozen_reviews" / f.name)
    binding = {
        "schema":"MathVisionKid.immutable_dev_base_cache.v1",
        "source_run_id":str(provenance.get("source_run_id") or "recovery_20261026_base"),
        "model":"Qwen/Qwen3-1.7B",
        "revision":"70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
        "model_artifact_proof":model_proof, "model_artifact_proof_sha256":proof_sha,
        "source_view_sha256":sha(view_src), "source_plan_sha256":sha(plan_src),
        "dev_sha256":dev_sha, "contract_sha256":contract_sha,
        "inference_contract_sha256":sha(infer_src), "renderer_sha256":sha(renderer_src),
        "fixture_ids":ids, "prompt_token_sha256":prompt_hashes, "seed_by_fixture":seeds,
        "base_output_sha256":sha_bytes(output), "base_output_bytes":len(output),
        "base_provenance_sha256":sha_bytes(provenance_bytes), "frozen_review_files":reviews,
    }
    atomic_json(target / "baseline_cache_binding.json", binding)
    return binding

def build(source: pathlib.Path, code: pathlib.Path, bundle: pathlib.Path,
          target: pathlib.Path, reviews: list[pathlib.Path]) -> dict:
    source=source.resolve(); code=code.resolve(); bundle=bundle.resolve()
    if target.exists(): raise FileExistsError("target exists; staging never overwrites")
    scope=json.loads((source/"owner_run_scope.json").read_bytes())
    scope_binding=json.loads((source/"owner_scope_binding_v2.json").read_bytes())
    if sha(source/"owner_run_scope.json") != scope_binding.get("original_scope_sha256"):
        raise ValueError("owner scope immutable binding failed")
    if scope_binding.get("dev_sha256") != scope.get("dev_sha256"):
        raise ValueError("scope binding dev SHA mismatch")
    if int(scope["hard_deadline_unix"]) <= 0 or int(scope.get("reserve_seconds",0)) != 600:
        raise ValueError("owner deadline/reserve is missing or changed")
    cfg=json.loads((source/"training"/"run_config.json").read_bytes())
    if cfg.get("model") != "Qwen/Qwen3-1.7B" or cfg.get("revision") != "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e":
        raise ValueError("source run config model/revision mismatch")
    contract_path=source/"training"/"evaluation_contract.json"
    contract=json.loads(contract_path.read_bytes())
    dev_sha=sha(source/"new_validation_candidates.jsonl")
    if dev_sha != scope["dev_sha256"] or contract.get("fixture_sha256") != dev_sha:
        raise ValueError("development fixture binding mismatch")
    screening=source/"dev_train_screening.json"
    if not screening.is_file(): raise FileNotFoundError("immutable dev_train_screening.json missing")
    screen_bytes=screening.read_bytes()
    if json.loads(screen_bytes).get("collisions") != []:
        raise ValueError("source screening reports train/dev overlap")
    model_proof=json.loads((source/"training"/"model_artifact_binding.json").read_bytes())
    cache_target=target/"baseline_cache"
    # Validate the complete cache before creating the target directory.
    cache_tmp=target.with_name(target.name+".cache_stage")
    if cache_tmp.exists(): raise FileExistsError("temporary target exists")
    binding=bind_cache(source,cache_tmp,reviews,scope,contract,model_proof)
    try:
        target.mkdir(parents=True,exist_ok=False)
        for name in ROOT_FILES:
            src=source/name
            if not src.is_file(): raise FileNotFoundError(src)
            if name in ("training_view.jsonl","sampling_manifest.json"):
                (target/name).symlink_to(src)
            else: copy_exact(src,target/name)
        for name in CODE_FILES:
            copy_exact(code/name,target/name)
        for name in ("recovery_worker_lowdose_20261026.py","preflight_checks_lowdose.py"):
            copy_exact(bundle/name,target/name)
        copy_exact(screening,target/"dev_train_screening.json")
        if (target/"dev_train_screening.json").read_bytes() != screen_bytes:
            raise IOError("dev screening bytes changed during staging")
        shutil.move(str(cache_tmp),str(cache_target))
        atomic_json(target/"baseline_cache_stage_receipt.json",{
            "schema":"MathVisionKid.lowdose_stage_receipt.v1",
            "source_run_config_sha256":sha(source/"training"/"run_config.json"),
            "source_model_artifact_proof_sha256":sha_bytes(canonical(model_proof)),
            "source_dev_train_screening_sha256":sha_bytes(screen_bytes),
            "cache_binding_sha256":sha(cache_target/"baseline_cache_binding.json"),
            "worker_sha256":sha(target/"recovery_worker_lowdose_20261026.py"),
            "backend_sha256":sha(target/"native_backend_20261026.py"),
            "policy_sha256":sha(target/"recovery_policy_20261026.py"),
            "corpus_and_manifest":"symlinked byte-identically to active recovery_20261026 root",
            "dev_validation":"reused preexisting 30-item development set; no independence claim",
            "launch_command":f"python -u {target}/recovery_worker_lowdose_20261026.py --root {target} --baseline-cache {cache_target}",
        })
    except Exception:
        # Keep partial artifacts visible for audit; never erase evidence automatically.
        raise
    return json.loads((target/"baseline_cache_stage_receipt.json").read_bytes())

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-root",type=pathlib.Path,required=True)
    ap.add_argument("--code-root",type=pathlib.Path,required=True)
    ap.add_argument("--bundle-dir",type=pathlib.Path,default=HERE)
    ap.add_argument("--target-root",type=pathlib.Path,required=True)
    ap.add_argument("--review",type=pathlib.Path,action="append",default=[])
    a=ap.parse_args()
    print(json.dumps(build(a.source_root,a.code_root,a.bundle_dir,a.target_root,a.review),indent=2))
if __name__=="__main__": main()

