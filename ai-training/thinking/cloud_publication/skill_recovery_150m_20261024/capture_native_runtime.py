import pathlib,json,hashlib,base64,gzip
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024');names=['native_probe_scope.json','native_probe_selection_policy.json','native_locked15_train_screening.json']
for phase in ['dev','final']:
 for p in(r/'native_probe'/phase).glob('*'):
  if p.suffix in('.json','.jsonl')and'_raw'not in p.name:names.append(str(p.relative_to(r)))
raw={n:(r/n).read_bytes()for n in names if(r/n).exists()}
assert all(len(b)<1_000_000 for b in raw.values()),'Only bounded metadata and final answers, no raw thinking'
print('NATIVE_GZIP_BASE64:'+base64.b64encode(gzip.compress(json.dumps({'files':{n:base64.b64encode(b).decode()for n,b in raw.items()},'hashes':{n:hashlib.sha256(b).hexdigest()for n,b in raw.items()}}).encode())).decode())
