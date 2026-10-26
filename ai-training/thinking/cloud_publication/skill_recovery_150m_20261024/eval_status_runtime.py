import pathlib,json,time
from datetime import datetime,timezone
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024');s={'observed_utc':datetime.now(timezone.utc).isoformat(),'worker_alive':skill_training_process.poll() is None,'exit':skill_training_process.poll(),'remaining_seconds':json.loads((r/'owner_run_scope.json').read_bytes())['hard_deadline_unix']-time.time()}
for n in ['training/progress.json','training/error.json','training/best.json','four_controls_publication_status.json']:
 if (r/n).exists():
  v=json.loads((r/n).read_bytes());s[n]={k:v.get(k) for k in ['state','error','canonical_context_sha256']} if n.startswith('four_') else v
s['eval_rows']={str(p.relative_to(r)):len(p.read_bytes().splitlines()) for p in (r/'training').glob('eval_step_*/*generations*.jsonl')}
p=r/'publication/publication_status.json'
if p.exists():
 v=json.loads(p.read_bytes());s['publication']={'state':v['state'],'folder_id':v['folder_id'],'checkpoint_count':len(v.get('checkpoints',{})),'checkpoints':v.get('checkpoints',{})}
print(json.dumps(s,ensure_ascii=False))
