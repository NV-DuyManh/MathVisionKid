import json,pathlib,time,threading
from datetime import datetime,timezone
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024')
v={'observed_utc':datetime.now(timezone.utc).isoformat(),'seconds_remaining':json.loads((r/'owner_run_scope.json').read_bytes())['hard_deadline_unix']-time.time(),'all_experiment_workers_exited':all(p.poll()==0for p in [skill_training_process,skill_fewshot_process,skill_final_process,skill_native_dev_process])}
for n in ['final_release_publication.json','native_evidence_publication_status.json','completion_evidence_publication_status.json','publication/publication_status.json','four_controls_publication_status.json']:
 if(r/n).exists():
  s=json.loads((r/n).read_bytes());v[n]={k:s.get(k)for k in['state','error','completed','bundle','canonical_context_sha256','publication_finalized','final_semantic_assessment_proof']};v[n]['proof_count']=len(s.get('proofs',{}))
v['publication_threads']=[{'name':t.name,'alive':t.is_alive()}for t in threading.enumerate()if t.name.startswith(('MathVisionKid','Skill'))]
print(json.dumps(v,ensure_ascii=False))
