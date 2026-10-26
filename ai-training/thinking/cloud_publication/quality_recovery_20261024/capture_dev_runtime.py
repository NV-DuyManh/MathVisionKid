import pathlib,json,hashlib,base64,gzip
r=pathlib.Path('/content/mathvisionkid_quality_recovery_20261024')
step=int(globals().get('recovery_capture_step',50))
adapter=f'training/eval_step_{step:06d}/adapter_generations.jsonl'
partial=not (r/adapter).exists()
adapter_bytes=(r/(adapter.replace('.jsonl','.partial.jsonl') if partial else adapter)).read_bytes()
names=['new_validation_candidates.jsonl','training/evaluation_contract.json','training/run_config.json','training/eval_step_000000/base_generations.jsonl','training/best.json']
binding=f'training/eval_step_{step:06d}/eval_bindings.json'
if (r/binding).exists():names.append(binding)
raw={n:(r/n).read_bytes() for n in names};raw[adapter]=adapter_bytes
files={n:base64.b64encode(b).decode() for n,b in raw.items()};hashes={n:hashlib.sha256(b).hexdigest() for n,b in raw.items()}
print('EVAL_BUNDLE_GZIP_BASE64:'+base64.b64encode(gzip.compress(json.dumps({'step':step,'partial_adapter':partial,'files':files,'hashes':hashes}).encode())).decode())
