from pathlib import Path
import json,hashlib
p=Path(__file__).parent;old=p.parent/'verbal_recovery_20261024'
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
base=(old/'recovery_policy.py').read_text(encoding='utf8');plan=(p/'balanced_plan_v2.py').read_text(encoding='utf8')
policy=base+'\n\n# Explicit v2 derived schedule supersedes original prepare_plan; original gate rules stay unchanged.\n'+plan
q=p/'recovery_policy.py'
if q.exists():assert q.read_text(encoding='utf8')==policy,'Do not replace different policy bytes'
else:q.write_text(policy,encoding='utf8')
worker=(old/'recovery_worker.py').read_text(encoding='utf8')
def replace(a,b,n=1):
 global worker
 assert worker.count(a)==n,(a,worker.count(a));worker=worker.replace(a,b)
replace("import verbal_training_renderer_v3 as V","import behavior_renderer as V\n import inference_contract as I")
replace("if sha(root/'verbal_training_renderer_v3.py')!='6b15233ae253eed7825864413edbdf3f8553ad955ef248e045c05f64e4473057':raise ValueError('verbal renderer changed')",f"if sha(root/'behavior_renderer.py')!={sha(p/'behavior_renderer.py')!r}:raise ValueError('behavior renderer changed')\n if sha(root/'inference_contract.py')!={sha(p/'inference_contract.py')!r}:raise ValueError('inference contract changed')")
replace(' H.fixture_messages=verbal_fixture_messages',' H.fixture_messages=verbal_fixture_messages\n H.generate_fixtures=I.generate_fixtures')
replace("'learning_rate':1e-5,'warmup_updates':10,'lora_r':16,'lora_alpha':16", "'learning_rate':3e-6,'warmup_updates':20,'lora_r':8,'lora_alpha':8,'target_modules':['q_proj','k_proj','v_proj','o_proj']")
replace("'gate_steps':[50],'max_successful_updates':50", "'gate_steps':[100,300],'max_successful_updates':300")
replace("'peak_lr':1e-5", "'peak_lr':3e-6")
replace("'warmup_updates':10,'peak_lr':3e-6", "'warmup_updates':20,'peak_lr':3e-6")
replace("model,r=16,lora_alpha=16", "model,r=8,lora_alpha=8")
replace("target_modules=H.TARGET_MODULES", "target_modules=['q_proj','k_proj','v_proj','o_proj']")
replace("lr=1e-5*min(1.,(state['step']+1)/10)", "lr=3e-6*min(1.,(state['step']+1)/20)")
replace("sha(root/'verbal_training_renderer_v3.py')", "sha(root/'behavior_renderer.py')",2)
replace("contract,csha=H.eval_contract(fixtures,tok)", "contract,csha=I.eval_contract(fixtures,tok,dev_sha)")
replace("if state['step']==1 or state['step'] in cfg['gate_steps'] or final:", "if state['step']==1 or state['step']%100==0 or final:")
worker=worker.replace("'validation_scope':'Reused development30 for representation iteration; prior locked20 is not read or reused; no new independent-test claim'", "'validation_scope':'Reused dev30 matched official nonthinking sampling, behavior-aligned prompts and balanced skill schedule; prior locked/final20 excluded; new final20 sealed before this branch outputs'")
# Clear old unrelated wording while retaining exact tested source math target rendering.
worker=worker.replace('source content reformatted through hash-pinned verbal renderer','source targets unchangedV3; mode-aware deduplicated prompt, grade/behavior/topic balanced one-pass schedule')
compile(worker,'skill_recovery_worker','exec')
q=p/'recovery_worker.py';assert not q.exists();q.write_text(worker,encoding='utf8')
refs={'source_worker_sha256':sha(old/'recovery_worker.py'),'source_policy_sha256':sha(old/'recovery_policy.py'),'balanced_plan_v2_sha256':sha(p/'balanced_plan_v2.py'),'target_renderer_sha256':sha(old/'verbal_training_renderer_v3.py'),'changes':['mode header/system and exact duplicate student work omission in bothtrain/eval','hierarchical grade/behavior/mode/topic schedule','official seeded nonthinking sampling replacing greedy','attention-only LoRAr8alpha8 replacing all-projectionr16','LR3e-6warmup20','gates100and300,cap300onepass'],'hypothesis_not_causal_proof':True,'source_corpus_or_math_labels_changed':False,'new_human_attestation':False}
(p/'frozen_code_references.json').write_text(json.dumps(refs,indent=2)+'\n',encoding='utf8')
print(json.dumps({'worker_sha256':sha(q),'policy_sha256':sha(p/'recovery_policy.py'),'renderer_sha256':sha(p/'behavior_renderer.py'),'inference_sha256':sha(p/'inference_contract.py')}))
