import pathlib,json,hashlib
pr=pathlib.Path('/content/mathvisionkid_recovery_20261026')
pv=json.loads((pr/'publication/publication_status.json').read_bytes())
print(json.dumps({'state':pv.get('state'),'last_error':pv.get('last_error'),'traceback':pv.get('traceback'),
 'artifacts':{k:{'id':v.get('id'),'sha256':v.get('sha256'),'bytes':v.get('bytes')} for k,v in pv.get('artifacts',{}).items()},
 'publication_files':[p.name for p in (pr/'publication').iterdir()]},ensure_ascii=False))
