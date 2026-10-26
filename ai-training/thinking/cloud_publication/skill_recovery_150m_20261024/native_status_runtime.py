import pathlib,json,time
from datetime import datetime,timezone
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024')
v={'observed_utc':datetime.now(timezone.utc).isoformat(),'seconds_remaining':json.loads((r/'owner_run_scope.json').read_bytes())['hard_deadline_unix']-time.time()}
for phase in ['dev','final']:
 proc=globals().get('skill_native_'+phase+'_process');v[phase+'_process']={'alive':proc.poll() is None,'exit':proc.poll()}if proc else None
 folder=r/'native_probe'/phase
 for n in ['runtime_progress.json','complete.json','error.json']:
  if(folder/n).exists():v[f'{phase}/{n}']=json.loads((folder/n).read_bytes())
 v[phase+'_rows']={p.name:len(p.read_bytes().splitlines())for p in folder.glob('*_final*.jsonl')}
 if proc and proc.poll() not in (None,0):v[phase+'_log_tail']=(r/('native_probe_'+phase+'.log')).read_text(errors='replace')[-2000:]
for n in ['publication/publication_status.json','completion_evidence_publication_status.json']:
 if(r/n).exists():
  s=json.loads((r/n).read_bytes());v[n]={'state':s.get('state'),'error':s.get('error'),'completed':s.get('completed'),'proofs':len(s.get('proofs',{})),'artifact_count':len(s.get('artifacts',{}))}
print(json.dumps(v,ensure_ascii=False))
