import pathlib, json, subprocess, hashlib
from datetime import datetime, timezone
root=pathlib.Path('/content/mathvisionkid_t4_budget_3h_20261023')
code="import importlib.metadata as m,json,sys;print(json.dumps({'python':sys.version,'packages':{n:m.version(n) for n in ['torch','transformers','unsloth','unsloth_zoo','peft','bitsandbytes','accelerate','triton','xformers']}}))"
out=json.loads(subprocess.check_output([str(root/'venv/bin/python'),'-c',code],text=True))
out['nvidia_smi']=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,driver_version,compute_cap','--format=csv,noheader'],text=True).strip()
out['observed_utc']=datetime.now(timezone.utc).isoformat()
out['evidence_scope']='Installed package metadata and nvidia-smi query only; no model or optimizer mutation'
p=root/'runtime_versions.json'
p.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'record':out,'raw_sha256':hashlib.sha256(p.read_bytes()).hexdigest()},ensure_ascii=False))
