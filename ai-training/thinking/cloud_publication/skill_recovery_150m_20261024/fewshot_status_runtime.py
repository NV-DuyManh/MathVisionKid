import pathlib,json,time
from datetime import datetime,timezone
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024')
o={'observed_utc':datetime.now(timezone.utc).isoformat(),'worker_alive':skill_fewshot_process.poll() is None,'worker_exit':skill_fewshot_process.poll(),'training_worker_exit':skill_training_process.poll(),'seconds_remaining':json.loads((r/'owner_run_scope.json').read_bytes())['hard_deadline_unix']-time.time()}
for n in ['fewshot_dev/runtime_progress.json','fewshot_dev/complete.json','fewshot_dev/error.json','fewshot_code_publication_status.json']:
 if (r/n).exists():
  v=json.loads((r/n).read_bytes());o[n]={k:v.get(k) for k in ['state','completed','count','error']} if n.endswith('publication_status.json') else v
o['output_rows']={p.name:len(p.read_bytes().splitlines()) for p in (r/'fewshot_dev').glob('*generations*.jsonl')}
if (r/'fewshot_dev/error.json').exists():o['log_tail']=(r/'fewshot_dev.log').read_text(errors='replace')[-3000:]
print(json.dumps(o,ensure_ascii=False))
