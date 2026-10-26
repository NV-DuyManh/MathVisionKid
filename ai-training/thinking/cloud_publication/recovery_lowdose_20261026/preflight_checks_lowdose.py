"""CPU-only proof tests for immutable baseline cache acceptance/rejection."""
import importlib.util,json,hashlib,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"recovery_20261026"))
path=HERE/"recovery_worker_lowdose_20261026.py"
spec=importlib.util.spec_from_file_location("lowdose_worker",path)
W=importlib.util.module_from_spec(spec);spec.loader.exec_module(W)
source=path.read_text(encoding="utf-8")
assert "'learning_rate':5e-6" in source and "'max_successful_updates':100" in source
assert "'gate_steps':[100]" in source and "'lora_r':16" in source
assert "'branch':'recovery_lowdose_20261026'" in source
assert "lr=5e-6*min(1.,(state['step']+1)/10)" in source
assert "row_mean_assistant_loss(forward.logits,batch['labels'])" in source
assert "checkpoint_resume_supported':False" in source

def sha_bytes(b):return hashlib.sha256(b).hexdigest()
fixtures=[{"id":f"d{i:02d}","grade":i%5+1,"mode":["answer","hint_no_answer","student_error","missing_or_contradictory_info"][i%4],"userproblem":f"Synthetic training-dev item {i}"} for i in range(30)]
dev_sha="a"*64;source_view="b"*64;plan_sha="c"*64;contract_sha="d"*64;inference_sha="e"*64;renderer_sha="f"*64
proof={"requested_model":W.MODEL,"requested_revision":W.REV,"snapshot_directory_revision":W.REV,"metadata_sha256":{"config.json":"e"*64},"weight_shards":["model-00001-of-00001.safetensors"]}
proof_sha=sha_bytes(W.canonical(proof).encode())
prompt_hashes={f["id"]:sha_bytes(f["id"].encode()) for f in fixtures}
contract={"fixture_sha256":dev_sha,"prompt_token_sha256":prompt_hashes,"decoding":{"max_new_tokens":1024}}
seeds={f["id"]:(20261024+int(W.digest(f["id"].encode())[:8],16))%(2**31) for f in fixtures}
with tempfile.TemporaryDirectory() as tmp:
 cache=Path(tmp);(cache/"frozen_reviews").mkdir()
 review=b"synthetic frozen review evidence only\n";(cache/"frozen_reviews"/"review.json").write_bytes(review)
 rows=[]
 for f in fixtures:
  rows.append({"fixture_id":f["id"],"grade":f["grade"],"mode":f["mode"],"stage":"base_before_training","contract_sha256":contract_sha,"prompt_token_sha256":prompt_hashes[f["id"]],"seed":seeds[f["id"]],"max_new_tokens":1024,"timed_out":False,"possibly_truncated":False,"ended_eos":True})
 output=b"".join((json.dumps(r,ensure_ascii=False,sort_keys=True)+"\n").encode() for r in rows)
 (cache/"base_generations.jsonl").write_bytes(output)
 provenance={"model":W.MODEL,"revision":W.REV,"contract_sha256":contract_sha,"fixture_sha256":dev_sha,"stage":"base_before_training","outputs_sha256":sha_bytes(output)}
 provenance_bytes=(json.dumps(provenance,sort_keys=True)+"\n").encode();(cache/"base_generation_provenance.json").write_bytes(provenance_bytes)
 binding={"schema":"MathVisionKid.immutable_dev_base_cache.v1","source_run_id":"synthetic-run","model":W.MODEL,"revision":W.REV,"model_artifact_proof":proof,"model_artifact_proof_sha256":proof_sha,"source_view_sha256":source_view,"source_plan_sha256":plan_sha,"dev_sha256":dev_sha,"contract_sha256":contract_sha,"inference_contract_sha256":inference_sha,"renderer_sha256":renderer_sha,"fixture_ids":[f["id"] for f in fixtures],"prompt_token_sha256":prompt_hashes,"seed_by_fixture":seeds,"base_output_sha256":sha_bytes(output),"base_output_bytes":len(output),"base_provenance_sha256":sha_bytes(provenance_bytes),"frozen_review_files":{"review.json":sha_bytes(review)}}
 binding_path=cache/"baseline_cache_binding.json";binding_path.write_text(json.dumps(binding,sort_keys=True),encoding="utf-8")
 accepted=W.verify_baseline_cache(cache,fixtures,contract,contract_sha,dev_sha,plan_sha,proof,source_view,inference_sha,renderer_sha)
 assert accepted["outputs_reused_without_rewriting"] and accepted["complete_base_rows"]==30
 (cache/"base_generations.jsonl").write_bytes(output+b" ")
 try:W.verify_baseline_cache(cache,fixtures,contract,contract_sha,dev_sha,plan_sha,proof,source_view,inference_sha,renderer_sha)
 except ValueError:pass
 else:raise AssertionError("changed base output was accepted")
 (cache/"base_generations.jsonl").write_bytes(output)
 wrong={**proof,"metadata_sha256":{"config.json":"f"*64}}
 try:W.verify_baseline_cache(cache,fixtures,contract,contract_sha,dev_sha,plan_sha,wrong,source_view,inference_sha,renderer_sha)
 except ValueError:pass
 else:raise AssertionError("different pinned model artifact was accepted")
 (cache/"frozen_reviews"/"review.json").write_bytes(b"changed")
 try:W.verify_baseline_cache(cache,fixtures,contract,contract_sha,dev_sha,plan_sha,proof,source_view,inference_sha,renderer_sha)
 except ValueError:pass
 else:raise AssertionError("changed frozen review was accepted")
print("PASS: 30-row cache proof accepted; output, artifact, and frozen-review mismatches rejected")

