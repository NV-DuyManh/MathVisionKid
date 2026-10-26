import json,hashlib,time
p=budget_root/'sampling/run/training_view_manifest.json';doc=json.loads(p.read_text())
out={k:v for k,v in doc.items() if k!='selected_cases_manifest'}
out['manifest_file_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
out['observed_unix']=time.time()
out['selected_row_readback_overlay']=globals().get('selected_row_readback_overlay')
print(json.dumps(out,ensure_ascii=False))
