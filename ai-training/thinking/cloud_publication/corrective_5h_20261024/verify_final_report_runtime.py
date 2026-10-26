import json,hashlib,pathlib
from datetime import datetime,timezone
fid='1hw2I662iP35WZxtoYsVJs1e80xoRBqnh'
b=repair_drive.files().get_media(fileId=fid).execute()
assert len(b)==147446 and hashlib.sha256(b).hexdigest()=='3eb96dbdf3709c5379b7bb3f83b40f0a126a11307d9c86b2171a89d93ea4db7e'
data=json.loads(b)
assert data['summary']['base']['strict_task_pass']==14 and data['summary']['adapter']['strict_task_pass']==7
r=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024')
(r/'final_semantic_assessment.json').write_bytes(b)
proof={'id':fid,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'fresh_raw_readback_verified':True,'raw_verified_utc':datetime.now(timezone.utc).isoformat()}
(r/'final_semantic_assessment_readback.json').write_text(json.dumps(proof,indent=2))
print(json.dumps(proof))
