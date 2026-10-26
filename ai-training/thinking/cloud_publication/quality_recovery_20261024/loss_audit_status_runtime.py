import pathlib,json,subprocess
from datetime import datetime,timezone
r=pathlib.Path('/content/mathvisionkid_quality_recovery_20261024');o=r/'target_alignment_audit'
v={'observed_utc':datetime.now(timezone.utc).isoformat(),'alive':audit_loss_process.poll() is None,'exit':audit_loss_process.poll()}
for n in ['dataset_shape.json','progress.json','forward_loss_audit.json','error.json','timeout.json']:
 if (o/n).exists():v[n]=json.loads((o/n).read_bytes())
if audit_loss_process.poll():v['log_tail']=(r/'target_loss_audit.log').read_text(errors='replace')[-2500:]
print(json.dumps(v,ensure_ascii=False))
