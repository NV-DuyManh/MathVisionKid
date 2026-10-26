import pathlib,json,hashlib,base64,gzip
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024')
names=['fewshot_dev/contract.json','fewshot_dev/complete.json','fewshot_dev/runtime_progress.json','fewshot_code_publication_status.json']
raw={n:(r/n).read_bytes() for n in names if (r/n).exists()}
f=r/'fewshot_dev/generations.jsonl';partial=not f.exists()
if partial:f=r/'fewshot_dev/generations.partial.jsonl'
raw['fewshot_dev/generations.jsonl']=f.read_bytes() if f.exists() else b''
packet={'partial':partial,'files':{n:base64.b64encode(b).decode() for n,b in raw.items()},'hashes':{n:hashlib.sha256(b).hexdigest() for n,b in raw.items()}}
print('FEWSHOT_GZIP_BASE64:'+base64.b64encode(gzip.compress(json.dumps(packet).encode())).decode())
