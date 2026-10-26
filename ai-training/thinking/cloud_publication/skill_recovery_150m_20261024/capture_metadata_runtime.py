import pathlib,json,hashlib,base64,gzip
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024')
names=['owner_scope_binding_v2.json','training/run_complete.json','training/run_config.json','training/input_audit.json','training/best.json','training/progress.json','publication/publication_status.json','four_controls_verified_manifest.json','four_controls_publication_status.json','active_code_raw_verified.json']
names += [str(p.relative_to(r)) for p in (r/'final_eval').glob('*.json')] if (r/'final_eval').exists() else []
names += [str(p.relative_to(r)) for p in (r/'fewshot_dev').glob('*.json')] if (r/'fewshot_dev').exists() else []
raw={n:(r/n).read_bytes() for n in names if (r/n).exists()}
assert all(len(b)<2_000_000 for b in raw.values()),'Only bounded metadata may leave cloud'
bundle={'files':{n:base64.b64encode(b).decode() for n,b in raw.items()},'hashes':{n:hashlib.sha256(b).hexdigest() for n,b in raw.items()}}
print('METADATA_GZIP_BASE64:'+base64.b64encode(gzip.compress(json.dumps(bundle).encode())).decode())
