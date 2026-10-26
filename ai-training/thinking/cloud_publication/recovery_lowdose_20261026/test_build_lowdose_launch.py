"""Synthetic CPU integration check; does not access corpus/model/evaluation fixtures."""
import hashlib, importlib.util, json, tempfile, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
PUB=HERE.parent/"recovery_20261026"
spec=importlib.util.spec_from_file_location("stage_builder",HERE/"build_lowdose_launch.py")
B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
sys.path.insert(0,str(HERE.parent/"recovery_20261026"))
spec=importlib.util.spec_from_file_location("lowdose_worker",HERE/"recovery_worker_lowdose_20261026.py")
W=importlib.util.module_from_spec(spec);spec.loader.exec_module(W)
def wr(p,b): p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def wj(p,v): wr(p,(json.dumps(v,sort_keys=True,ensure_ascii=False)+"\n").encode())
with tempfile.TemporaryDirectory() as td:
 t=Path(td);src=t/"active";target=t/"new";bundle=HERE;code=PUB
 fixtures=[{"id":f"fake{i:02d}","grade":i%5+1,"mode":["answer","hint_no_answer","student_error","missing_or_contradictory_info"][i%4],"userproblem":f"synthetic {i}"} for i in range(30)]
 dev=b"".join((json.dumps(x,ensure_ascii=False)+"\n").encode() for x in fixtures);wr(src/"new_validation_candidates.jsonl",dev);devsha=hashlib.sha256(dev).hexdigest()
 scope={"hard_deadline_unix":2_000_000_000,"reserve_seconds":600,"dev_sha256":devsha,"locked_test_sha256":"a"*64}
 wj(src/"owner_run_scope.json",scope);wj(src/"owner_scope_binding_v2.json",{"original_scope_sha256":B.sha(src/"owner_run_scope.json"),"dev_sha256":devsha,"locked_test_sha256":"a"*64,"repair_reason":"synthetic"})
 for n,b in {"training_view.jsonl":b"{}\n","sampling_manifest.json":b"{}\n","derived_sampling_plan.json":b"{}\n","exhaustive_colab_loader.py":b"x=1\n","frozen_training_primitives.py":b"x=1\n","conditional_behavior_renderer.py":b"x=1\n","inference_contract.py":b"x=1\n","behavior_renderer.py":b"x=1\n","verbal_training_renderer_v3.py":b"x=1\n","dev_train_screening.json":b'{"collisions": [], "against_prior_used_development": {"sha256":"x"}}\n'}.items():wr(src/n,b)
 (src/"training").mkdir()
 model="Qwen/Qwen3-1.7B";rev="70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
 cfg={"model":model,"revision":rev,"branch":"source26"};wj(src/"training"/"run_config.json",cfg)
 proof={"requested_model":model,"requested_revision":rev,"snapshot_directory_revision":rev,"metadata_sha256":{"config.json":"b"*64},"weight_shards":["model-00001-of-00001.safetensors"]}
 wj(src/"training"/"model_artifact_binding.json",proof);wj(src/"training"/"pretrain_qa_approved.json",{"approved":True})
 contract={"fixture_sha256":devsha,"prompt_token_sha256":{x["id"]:hashlib.sha256(x["id"].encode()).hexdigest() for x in fixtures},"decoding":{"max_new_tokens":1024}}
 wj(src/"training"/"evaluation_contract.json",contract)
 csha=hashlib.sha256(B.canonical(contract)).hexdigest()
 seeds={x["id"]:(20261024+int(W.digest(x["id"].encode())[:8],16))%(2**31) for x in fixtures}
 rows=[{"fixture_id":x["id"],"grade":x["grade"],"mode":x["mode"],"stage":"base_before_training","contract_sha256":csha,"prompt_token_sha256":contract["prompt_token_sha256"][x["id"]],"seed":seeds[x["id"]],"max_new_tokens":1024,"timed_out":False,"possibly_truncated":False,"ended_eos":True} for x in fixtures]
 out=b"".join((json.dumps(x,sort_keys=True)+"\n").encode() for x in rows)
 wr(src/"training"/"eval_step_000000"/"base_generations.jsonl",out)
 wj(src/"training"/"eval_step_000000"/"base_generation_provenance.json",{"model":model,"revision":rev,"contract_sha256":csha,"fixture_sha256":devsha,"stage":"base_before_training","outputs_sha256":hashlib.sha256(out).hexdigest()})
 review=t/"frozen.json";wr(review,b"synthetic review bytes\n")
 rec=B.build(src,code,bundle,target,[review])
 assert (target/"prior_dev_train_screening_preserved.json").read_bytes()==(src/"dev_train_screening.json").read_bytes()
 assert not (target/"dev_train_screening.json").exists()
 assert (target/"training_view.jsonl").is_symlink() and (target/"sampling_manifest.json").is_symlink()
 cache=target/"baseline_cache"
 got=W.verify_baseline_cache(cache,fixtures,contract,csha,devsha,B.sha(src/"derived_sampling_plan.json"),proof,B.sha(src/"training_view.jsonl"),B.sha(src/"inference_contract.py"),B.sha(src/"conditional_behavior_renderer.py"))
 assert got["complete_base_rows"]==30 and got["outputs_reused_without_rewriting"]
 (cache/"base_generations.jsonl").write_bytes(out+b" ")
 try: W.verify_baseline_cache(cache,fixtures,contract,csha,devsha,B.sha(src/"derived_sampling_plan.json"),proof,B.sha(src/"training_view.jsonl"),B.sha(src/"inference_contract.py"),B.sha(src/"conditional_behavior_renderer.py"))
 except ValueError: pass
 else: raise AssertionError("tampered cache was accepted")
 print("PASS: staged cache exact-match acceptance; tamper rejection; screening bytes preserved; corpus symlinks intact")

