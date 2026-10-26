import pathlib,json,time,subprocess
from datetime import datetime,timezone
root5=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024')
out={'observed_utc':datetime.now(timezone.utc).isoformat(),'root_exists':root5.exists()}
for name in ('training/run_config.json','training/progress.json','training/run_complete.json','training/error.json','training/resume_validation.json','training/physical_batch_tuning.json','owner_budget_revision_config.json','optimized_launch_manifest.json'):
 p=root5/name
 if p.is_file():out[name]=json.loads(p.read_bytes())
p=root5/'selected_view_tokenization_audit.json'
if p.is_file():
 audit=json.loads(p.read_bytes());out['audit']={k:audit.get(k) for k in ('state','counts','semantic_proof')}
p=root5/'drive_publication/publication_status.json'
if p.is_file():
 pub=json.loads(p.read_bytes());out['publication']={k:pub.get(k) for k in ('publisher_state','folder_id','last_checkpoint','latest_pointer_proof','last_error','last_tick_utc','complete_proof')}
 out['publication']['artifact_ids']={k:v['id'] for k,v in pub.get('artifacts',{}).items()}
for name in ('training_optimized_v2b.log',):
 p=root5/name
 if p.is_file():out[name+'_tail']=p.read_text(errors='replace')[-3000:]
out['worker_alive']=bool(globals().get('corrective_process') and corrective_process.poll() is None)
out['worker_exit']=corrective_process.poll() if globals().get('corrective_process') else None
for name in ('four_controls_publication_status.json','four_controls_queue_status.json'):
 p=root5/name
 if p.is_file():
  d=json.loads(p.read_bytes());out[name]={k:v for k,v in d.items() if k not in ('observation','controls')}
try:out['gpu']=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,memory.used,utilization.gpu','--format=csv,noheader'],text=True,timeout=8).strip()
except Exception as e:out['gpu_error']=str(e)
print(json.dumps(out,ensure_ascii=False))
