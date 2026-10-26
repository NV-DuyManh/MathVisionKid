import pathlib,json,threading
from datetime import datetime,timezone
r=pathlib.Path('/content/mathvisionkid_quality_recovery_20261024')
out={'observed_utc':datetime.now(timezone.utc).isoformat(),'train_alive':recovery_process.poll() is None,'probe_alive':recovery_probe_process.poll() is None,'final_eval_alive':recovery_final_process.poll() is None,'control_thread_alive':bool(globals().get('recovery_controls_thread') and recovery_controls_thread.is_alive())}
for n in ['publication/publication_status.json','final_eval_publication_status.json','four_controls_publication_status.json']:
 d=json.loads((r/n).read_bytes());out[n]={k:d.get(k) for k in ['state','error','work','canonical_context_sha256','run_metadata_sha256','publication_finalized']}
 if n.startswith('publication/'):
  out[n]['report_proof']=d.get('artifacts',{}).get('training/final_semantic_assessment.json');out[n]['completion_proof']=d.get('artifacts',{}).get('training_complete_publication_proof.json')
 if n.startswith('four_controls'):
  out[n]['verified_writes']=d.get('receipt',{}).get('verified_writes')
print(json.dumps(out,ensure_ascii=False))
