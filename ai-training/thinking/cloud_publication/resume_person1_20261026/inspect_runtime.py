import pathlib,json,socket,os,subprocess
from datetime import datetime as inspect_datetime,timezone as inspect_timezone
ir=pathlib.Path('/content/mathvisionkid_conditional_grounding_20261025')
obs={'observed_utc':inspect_datetime.now(inspect_timezone.utc).isoformat(),'hostname':socket.gethostname(),'kernel_pid':os.getpid(),'prior_run_root_exists':ir.is_dir(),
 'prior_worker_global_present':'conditional_training_process' in globals()}
if 'conditional_training_process' in globals():obs['prior_worker']={'pid':conditional_training_process.pid,'exit':conditional_training_process.poll()}
for name in ['training/progress.json','training/run_complete.json','training/error.json','training/best.json','publication/publication_status.json']:
 p=ir/name
 if p.is_file():
  v=json.loads(p.read_bytes());obs[name]={k:v[k] for k in ['state','step','rows_done','supervised_tokens','kind','complete','stop_reason','error','folder_id','publication_finalized'] if k in v}
try:obs['gpu']=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,memory.used,utilization.gpu','--format=csv,noheader'],text=True).strip()
except Exception as e:obs['gpu_error']=type(e).__name__
obs['packages']={}
from importlib.metadata import version,PackageNotFoundError
for name in ['torch','transformers','peft','accelerate','bitsandbytes']:
 try:obs['packages'][name]=version(name)
 except PackageNotFoundError:obs['packages'][name]=None
print(json.dumps(obs,ensure_ascii=False))
