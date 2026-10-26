import pathlib,json,time
from datetime import datetime as status_datetime,timezone as status_timezone
sr=pathlib.Path('/content/mathvisionkid_recovery_20261026')
o={'observed_utc':status_datetime.now(status_timezone.utc).isoformat(),'worker_exit':conditional_training_process.poll(),'pid':conditional_training_process.pid}
for name in ['training/progress.json','training/error.json','training/native_first_microbatch_audit.json','training/run_complete.json']:
 p=sr/name
 if p.is_file():o[name]=json.loads(p.read_bytes())
p=sr/'publication/publication_status.json'
if p.exists():
 v=json.loads(p.read_bytes());o['publication']={k:v.get(k) for k in ['state','folder_id','last_error'] if k in v}
 o['publication'].update(artifacts=len(v.get('artifacts',{})),checkpoints=len(v.get('checkpoints',{})))
 required=['recovery_worker_20261026.py','native_backend_20261026.py','recovery_policy_20261026.py','conditional_behavior_renderer.py','inference_contract.py','derived_sampling_plan.json','source_qa_binding.json','owner_run_scope.json']
 o['core_code_raw_verified']={n:bool(v.get('artifacts',{}).get(n,{}).get('fresh_raw_readback_verified')) for n in required}
o['eval_counts']={str(p.relative_to(sr)):len(p.read_bytes().splitlines()) for p in sorted((sr/'training').glob('eval_step_*/*generations*.jsonl'))}
if (sr/'training.log').exists():o['log_tail']=(sr/'training.log').read_text(errors='replace')[-1000:]
o['optimizer_approved']=(sr/'training/pretrain_qa_approved.json').exists()
print(json.dumps(o,ensure_ascii=False))
