import json,pathlib,subprocess,sys,importlib.metadata
from datetime import datetime,timezone
out={'observed_utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,'old_corrective_root_exists':pathlib.Path('/content/mathvisionkid_corrective_5h_20261024').exists(),'new_root_exists':pathlib.Path('/content/mathvisionkid_quality_recovery_20261024').exists(),'training_started':False}
try:out['gpu']=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,memory.used,utilization.gpu','--format=csv,noheader'],text=True,timeout=8).strip()
except Exception as e:out['gpu_error']=str(e)
out['versions']={}
for n in ['torch','transformers','peft','bitsandbytes','unsloth','trl']:
 try:out['versions'][n]=importlib.metadata.version(n)
 except importlib.metadata.PackageNotFoundError:out['versions'][n]=None
try:
 import google.auth
 probe_credentials,_=google.auth.default()
 out['adc_present']=True
except Exception as e:out['adc_present']=False;out['adc_error']=type(e).__name__
print(json.dumps(out))
