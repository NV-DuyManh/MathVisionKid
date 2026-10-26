import subprocess,json,pathlib,time,statistics
from datetime import datetime,timezone
root5=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024')
cmd=['nvidia-smi','--query-gpu=utilization.gpu,memory.used,power.draw','--format=csv,noheader,nounits','-l','1']
start=time.time()
try:raw=subprocess.run(cmd,timeout=15,capture_output=True,text=True).stdout
except subprocess.TimeoutExpired as e:raw=e.stdout.decode() if isinstance(e.stdout,bytes) else e.stdout
samples=[]
for line in (raw or '').splitlines():
 try:samples.append([float(x.strip()) for x in line.split(',')])
 except ValueError:pass
progress=json.loads((root5/'training/progress.json').read_bytes())
result={'observed_utc':datetime.now(timezone.utc).isoformat(),'read_only':True,'training_configuration_changed':False,'sample_window_seconds':time.time()-start,'sample_count':len(samples),'gpu_busy_percent_min_mean_max':[min(x[0] for x in samples),statistics.mean(x[0] for x in samples),max(x[0] for x in samples)] if samples else None,'used_MiB_min_max':[min(x[1] for x in samples),max(x[1] for x in samples)] if samples else None,'power_watts_mean':statistics.mean(x[2] for x in samples) if samples else None,'step':progress.get('step'),'rows_done':progress.get('rows_done'),'training_wall_seconds':progress.get('training_wall_seconds')}
(root5/'gpu_readonly_sample.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
