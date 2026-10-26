import pathlib,json,hashlib,base64,gzip,time
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024')
names=['training/run_complete.json','training/progress.json','training/best.json','publication/publication_status.json','active_code_raw_verified.json','fewshot_code_publication_status.json','completion_evidence_publication_status.json','native_evidence_publication_status.json','four_controls_publication_status.json','four_controls_verified_manifest.json','owner_scope_binding_v2.json','drive_write_coordination.json','native_probe_gate.json','native_probe/dev/complete.json','native_probe/final/complete.json','final_release_publication.json']
raw={n:(r/n).read_bytes()for n in names if(r/n).exists()}
assert all(len(b)<2_000_000 for b in raw.values())
print('METADATA_GZIP_BASE64:'+base64.b64encode(gzip.compress(json.dumps({'observed_unix':time.time(),'files':{n:base64.b64encode(b).decode()for n,b in raw.items()},'hashes':{n:hashlib.sha256(b).hexdigest()for n,b in raw.items()}}).encode())).decode())
