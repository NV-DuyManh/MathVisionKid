import pathlib,json
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024');s=json.loads((r/'publication/publication_status.json').read_bytes())
print(json.dumps({'state':s['state'],'last_error':s.get('last_error'),'traceback':s.get('traceback'),'artifacts':{k:{'id':v['id'],'sha256':v['sha256'],'name':v['name'],'bytes':v['bytes']} for k,v in s.get('artifacts',{}).items()},'latest_snapshots':[{'name':p.name,'bytes':p.stat().st_size,'mtime':p.stat().st_mtime} for p in sorted((r/'publication/snapshots').glob('*'),key=lambda p:p.stat().st_mtime)[-6:]]},ensure_ascii=False))
