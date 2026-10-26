import pathlib,json,subprocess,time
from datetime import datetime,timezone
r=pathlib.Path('/content/mathvisionkid_quality_recovery_20261024')
out={'observed_utc':datetime.now(timezone.utc).isoformat(),'root_exists':r.exists(),'worker_alive':bool(globals().get('recovery_process') and recovery_process.poll() is None),'worker_exit':recovery_process.poll() if globals().get('recovery_process') else None}
for n in ['owner_run_scope.json','install_status.json','training/progress.json','training/error.json','training/best.json','training/run_complete.json']:
 p=r/n
 if p.exists():out[n]=json.loads(p.read_bytes())
p=r/'publication/publication_status.json'
if p.exists():
 d=json.loads(p.read_bytes());out['publication']={k:d.get(k) for k in ['state','folder_id','error','final_artifacts']};out['publication']['artifact_count']=len(d.get('artifacts',{}));out['publication']['checkpoints']=d.get('checkpoints',{});out['publication']['recent_errors']=d.get('errors',[])[-2:]
p=r/'training.log'
if p.exists():out['log_tail']=p.read_text(errors='replace')[-3500:]
out['evaluation_progress']={str(p.relative_to(r)):len(p.read_bytes().splitlines()) for p in (r/'training').glob('eval_step_*/*.partial.jsonl')}
for label,var in [('step1_probe','recovery_probe_process'),('locked_final_eval','recovery_final_process')]:
 proc=globals().get(var)
 if proc:out[label]={'alive':proc.poll() is None,'exit':proc.poll(),'pid':proc.pid}
for n in ['training/eval_step_000001/probe_error.json','training/eval_step_000001/probe_complete.json','final_eval/error.json','final_eval/final_eval_manifest.json','final_eval_publication_status.json']:
 p=r/n
 if p.exists():
  d=json.loads(p.read_bytes());out[n]={k:v for k,v in d.items() if k not in ['files','input_hashes','packages','selected_best','artifacts']}
p=r/'four_controls_publication_status.json'
if p.exists():
 d=json.loads(p.read_bytes());out['four_controls']={k:d.get(k) for k in ['state','error','work','canonical_context_sha256','run_metadata_sha256']}
try:out['gpu']=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,memory.used,utilization.gpu','--format=csv,noheader'],text=True,timeout=8).strip()
except Exception as e:out['gpu_error']=str(e)
print(json.dumps(out,ensure_ascii=False))
