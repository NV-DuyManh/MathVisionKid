import pathlib,json,time
from datetime import datetime,timezone
root5=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024')
out={'observed_utc':datetime.now(timezone.utc).isoformat()}
p=root5/'four_controls_publication_status.json'
if p.exists():
 s=json.loads(p.read_bytes());out['controls']={k:v for k,v in s.items() if k not in ('observation','controls')}
for n in ['base_generations.partial.jsonl','base_generations.jsonl','adapter_generations.partial.jsonl','adapter_generations.jsonl']:
 p=root5/'training'/n
 if p.exists():
  rows=[json.loads(l) for l in p.read_text().splitlines() if l.strip()]
  out[n]={'rows':len(rows),'generated_tokens':sum(r['generated_tokens'] for r in rows),'ended_eos_count':sum(r.get('ended_eos',False) for r in rows),'mtime_unix':p.stat().st_mtime}
p=root5/'training/progress.json'
if p.exists():
 d=json.loads(p.read_bytes());out['progress']={k:v for k,v in d.items() if k!='config'}
out['worker_alive']=bool(globals().get('corrective_process') and corrective_process.poll() is None)
print(json.dumps(out,ensure_ascii=False))
