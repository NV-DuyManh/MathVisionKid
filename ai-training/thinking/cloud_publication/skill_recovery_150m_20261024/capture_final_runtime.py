import pathlib,json,hashlib,base64,gzip
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024');f=r/'final_eval'
assert (f/'complete.json').exists() and skill_final_process.poll()==0,'Final test not complete'
m=json.loads((f/'complete.json').read_bytes())
for n,info in m['files'].items():
 b=(f/n).read_bytes();assert len(b)==info['bytes']and hashlib.sha256(b).hexdigest()==info['sha256']
names=['locked_test_candidates.jsonl','locked_test_binding.json','training/run_complete.json','training/best.json','fewshot_selection.json','root_fewshot_semantic_review.json']
names += [str(p.relative_to(r))for p in f.rglob('*')if p.is_file()and p.suffix in('.json','.jsonl')and'.partial.'not in p.name]
raw={n:(r/n).read_bytes()for n in names};assert all(len(b)<1_000_000for b in raw.values())
packet={'files':{n:base64.b64encode(b).decode()for n,b in raw.items()},'hashes':{n:hashlib.sha256(b).hexdigest()for n,b in raw.items()}}
print('FINAL_GZIP_BASE64:'+base64.b64encode(gzip.compress(json.dumps(packet).encode())).decode())
