import pathlib,json,hashlib
from datetime import datetime,timezone
r=pathlib.Path('/content/mathvisionkid_verbal_recovery_20261024')
d={'observed_utc':datetime.now(timezone.utc).isoformat()}
for label,glob in [('training','verbal_process'),('final_evaluation','verbal_final_process')]:
 p=globals().get(glob);d[label]={'alive':p.poll() is None,'exit':p.poll(),'pid':p.pid} if p else {'observed':False}
for n in ['training/progress.json','training/error.json','training/best.json','final_eval/error.json','final_eval/final_eval_manifest.json','final_eval_publication_status.json','four_controls_publication_status.json']:
 if (r/n).exists():
  x=json.loads((r/n).read_bytes())
  if n.endswith('publication_status.json'):
   d[n]={k:x.get(k) for k in ['state','error','work','canonical_context_sha256','fixture_count','test_run_count']}
   d[n]['artifact_count']=len(x.get('artifacts',{}))
   if x.get('receipt'):d[n]['verified_writes']=x['receipt'].get('verified_writes')
  else:d[n]=x
p=r/'publication/publication_status.json'
if p.exists():
 s=json.loads(p.read_bytes());d['publisher']={k:s.get(k) for k in ['state','folder_id','error','final_artifacts']}
 d['publisher']['report']=s.get('artifacts',{}).get('training/final_semantic_assessment.json')
d['final_eval_counts']={p.name:len(p.read_bytes().splitlines()) for p in (r/'final_eval').glob('*generations*.jsonl')}
if (r/'final_evaluation.log').exists():d['final_log_tail']=(r/'final_evaluation.log').read_text(errors='replace')[-800:]
print(json.dumps(d,ensure_ascii=False))
