import pathlib,json,hashlib,base64
r=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024')
names=['training/final_metrics.json','training/run_complete.json','training/base_generations.jsonl','training/adapter_generations.jsonl','eval_fixtures.jsonl','four_controls_publication_status.json','four_controls_verified_manifest.json']
out={}
for n in names:
 p=r/n
 if p.exists():
  b=p.read_bytes();assert len(b)<1000000
  out[n]={'sha256':hashlib.sha256(b).hexdigest(),'base64':base64.b64encode(b).decode()}
proofs=list(r.rglob('complete_publication_proof.json'))
for p in proofs:
 b=p.read_bytes();assert len(b)<1000000
 out[str(p.relative_to(r))]={'sha256':hashlib.sha256(b).hexdigest(),'base64':base64.b64encode(b).decode()}
print(json.dumps(out))
