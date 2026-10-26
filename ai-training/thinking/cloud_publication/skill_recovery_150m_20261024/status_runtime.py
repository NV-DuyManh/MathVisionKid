import pathlib,json,time,subprocess
from datetime import datetime,timezone
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024');d={'observed_utc':datetime.now(timezone.utc).isoformat(),'remaining_budget_seconds':json.loads((r/'owner_run_scope.json').read_bytes())['hard_deadline_unix']-time.time()}
for name in ['skill_benchmark_process','skill_training_process','skill_final_process']:
 p=globals().get(name);d[name]={'alive':p.poll() is None,'exit':p.poll(),'pid':p.pid} if p else None
for n in ['benchmark/progress.json','benchmark/error.json','benchmark/complete.json','training/progress.json','training/best.json','training/error.json','training/run_complete.json','final_eval/progress.json','final_eval/error.json','four_controls_publication_status.json']:
 if (r/n).exists():d[n]=json.loads((r/n).read_bytes())
p=r/'publication/publication_status.json'
if p.exists():
 s=json.loads(p.read_bytes());d['publication']={k:s.get(k) for k in ['state','folder_id','error','last_error','final_artifacts']};d['publication']['artifact_count']=len(s.get('artifacts',{}));d['publication']['checkpoints']=s.get('checkpoints',{})
for name in ['benchmark.log','training.log','final_evaluation.log']:
 if (r/name).exists():d[name]=(r/name).read_text(errors='replace')[-900:]
try:d['gpu']=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.used,utilization.gpu','--format=csv,noheader'],text=True,timeout=5).strip()
except Exception as e:d['gpu_error']=repr(e)
print(json.dumps(d,ensure_ascii=False))
