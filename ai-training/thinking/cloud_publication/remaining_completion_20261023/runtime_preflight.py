import json, subprocess, threading
from datetime import datetime, timezone
_probe={'observed_utc':datetime.now(timezone.utc).isoformat(),'probe_only':True,
 'training_launched_by_probe':False,'threads':[t.name for t in threading.enumerate()],
 'publication':globals().get('cloud_closeout_publication_state'),
 'numeric':globals().get('numeric_resume2_state'),
 'has_authenticated_drive_service':'service' in globals() or 'drive_service' in globals(),
 'has_root':'ROOT' in globals()}
try:
    _gpu=subprocess.run(['nvidia-smi','--query-gpu=name,memory.total','--format=csv,noheader'],capture_output=True,text=True,timeout=8)
    _probe['gpu_inventory']=_gpu.stdout.strip();_probe['gpu_probe_returncode']=_gpu.returncode
except (FileNotFoundError,subprocess.TimeoutExpired) as _error:
    _probe['gpu_inventory']='NO_GPU_RUNTIME';_probe['gpu_probe_error']=type(_error).__name__
print(json.dumps(_probe,ensure_ascii=False))
