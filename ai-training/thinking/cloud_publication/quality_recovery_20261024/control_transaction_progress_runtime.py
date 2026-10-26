import pathlib,json,time
r=pathlib.Path('/content/mathvisionkid_quality_recovery_20261024')
d=json.loads((r/'four_controls_publication_status.json').read_bytes());w=pathlib.Path(d['work'])
out={'state':d['state'],'observed_unix':time.time(),'control_thread_alive':recovery_controls_thread.is_alive(),'bounded_local_metadata_files':[]}
for p in sorted(w.glob('*')):
 if p.is_file():out['bounded_local_metadata_files'].append({'name':p.name,'bytes':p.stat().st_size,'mtime':p.stat().st_mtime})
 for f in sorted(p.glob('*')) if p.is_dir() else []:
  if f.is_file():out['bounded_local_metadata_files'].append({'name':str(f.relative_to(w)),'bytes':f.stat().st_size,'mtime':f.stat().st_mtime})
p=w/'four_controls_raw_verified.json'
if p.exists():out['transaction_receipt']=json.loads(p.read_bytes())
print(json.dumps(out,ensure_ascii=False))
