import pathlib,json
from datetime import datetime as cs_datetime,timezone as cs_timezone
csroot=pathlib.Path('/content/mathvisionkid_recovery_20261026')
cs={'observed_utc':cs_datetime.now(cs_timezone.utc).isoformat(),'worker_exit':conditional_training_process.poll()}
for name in ['training/progress.json','training/error.json','training/native_first_microbatch_audit.json','training/run_complete.json']:
 p=csroot/name
 if p.is_file():
  v=json.loads(p.read_bytes());cs[name]={k:v[k] for k in ['state','step','rows_done','supervised_tokens','last_loss','last_gradient_norm','training_seconds','complete','stop_reason','error','selected_token_row_CE_matches_per_row_reference','absolute_difference'] if k in v}
pub=json.loads((csroot/'publication/publication_status.json').read_bytes())
cs['publication']={'state':pub['state'],'artifact_count':len(pub.get('artifacts',{})),'checkpoints':len(pub.get('checkpoints',{}))}
if pub.get('checkpoints'):cs['latest_checkpoint']=list(pub['checkpoints'].values())[-1]
cs['eval_counts']={str(p.relative_to(csroot)):len(p.read_bytes().splitlines()) for p in sorted((csroot/'training').glob('eval_step_*/*generations*.jsonl'))}
cp=csroot/'four_controls_publication_status.json'
if cp.exists():cs['four_controls_state']=json.loads(cp.read_bytes())['state']
print(json.dumps(cs,ensure_ascii=False))
