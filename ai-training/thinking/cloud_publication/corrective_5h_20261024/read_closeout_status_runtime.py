import json,pathlib
from datetime import datetime,timezone
if globals().get('corrective_controls_thread') and corrective_controls_thread.is_alive():corrective_controls_thread.join(timeout=35)
p=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024/four_controls_publication_status.json')
d=json.loads(p.read_bytes())
print(json.dumps({'observed_utc':datetime.now(timezone.utc).isoformat(),'controls':{k:v for k,v in d.items() if k not in ('observation','controls')},'control_thread_alive':corrective_controls_thread.is_alive(),'worker_exit':corrective_process.poll()},ensure_ascii=False))
