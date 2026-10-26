import pathlib,json,subprocess
from datetime import datetime,timezone
r=pathlib.Path('/content/mathvisionkid_verbal_recovery_20261024');o=r/'training'
d={'observed_utc':datetime.now(timezone.utc).isoformat(),'worker_alive':bool(globals().get('verbal_process') and verbal_process.poll() is None),'exit':verbal_process.poll() if globals().get('verbal_process') else None}
for n in ['progress.json','error.json','best.json','run_complete.json']:
 if (o/n).exists():d[n]=json.loads((o/n).read_bytes())
p=r/'publication/publication_status.json'
if p.exists():
 s=json.loads(p.read_bytes());d['publication']={k:s.get(k) for k in ['state','folder_id','error','final_artifacts']};d['publication']['artifact_count']=len(s.get('artifacts',{}));d['publication']['checkpoints']=s.get('checkpoints',{})
d['eval_progress']={str(p.relative_to(r)):len(p.read_bytes().splitlines()) for p in o.glob('eval_step_*/*.partial.jsonl')}
if (r/'training.log').exists():d['log_tail']=(r/'training.log').read_text(errors='replace')[-1800:]
try:d['gpu']=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader'],text=True,timeout=6).strip()
except Exception as e:d['gpu_error']=repr(e)
print(json.dumps(d,ensure_ascii=False))
