import pathlib,json,subprocess
from datetime import datetime as mon_datetime,timezone as mon_timezone
msroot=pathlib.Path('/content/mathvisionkid_conditional_grounding_20261025')
mon={'observed_utc':mon_datetime.now(mon_timezone.utc).isoformat(),'worker_exit':conditional_training_process.poll()}
for mname in ['training/progress.json','training/error.json','training/run_complete.json','publication/publication_status.json']:
 mp=msroot/mname
 if mp.exists():
  mv=json.loads(mp.read_bytes())
  mon[mname]={k:mv[k] for k in ['state','step','rows_done','supervised_tokens','last_loss','last_gradient_norm','stop_reason','complete','error','last_error'] if k in mv}
  if mname.endswith('publication_status.json'):mon[mname].update({'artifact_count':len(mv.get('artifacts',{})),'checkpoint_count':len(mv.get('checkpoints',{}))})
mon['eval_counts']={str(p.relative_to(msroot)):len(p.read_bytes().splitlines()) for p in sorted((msroot/'training').glob('eval_step_*/*generations*.jsonl'))}
mon['gpu']=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader'],text=True).strip()
print(json.dumps(mon,ensure_ascii=False))
