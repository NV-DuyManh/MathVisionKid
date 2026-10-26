import pathlib,json,gzip,base64,hashlib
r=pathlib.Path('/content/mathvisionkid_verbal_recovery_20261024')
names=['training/run_complete.json','training/best.json','training/eval_step_000001/probe_complete.json','publication/publication_status.json','four_controls_publication_status.json','four_controls_verified_manifest.json','final_eval_publication_status.json','final_eval/final_eval_manifest.json']
raw={n:(r/n).read_bytes() for n in names if (r/n).exists()}
print('META_BUNDLE_GZIP_BASE64:'+base64.b64encode(gzip.compress(json.dumps({'files':{n:base64.b64encode(b).decode() for n,b in raw.items()},'hashes':{n:hashlib.sha256(b).hexdigest() for n,b in raw.items()}}).encode())).decode())
