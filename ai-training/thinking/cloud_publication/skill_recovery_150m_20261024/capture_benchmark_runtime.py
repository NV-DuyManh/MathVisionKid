import pathlib,json,base64,gzip,hashlib
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024');p=r/'benchmark'
names=['contract.json','complete.json','final_generations.jsonl','error.json']
raw={n:(p/n).read_bytes() for n in names if (p/n).exists()}
print('CALIBRATION_BUNDLE_GZIP_BASE64:'+base64.b64encode(gzip.compress(json.dumps({'files':{n:base64.b64encode(b).decode() for n,b in raw.items()},'hashes':{n:hashlib.sha256(b).hexdigest() for n,b in raw.items()}}).encode())).decode())
