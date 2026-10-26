import pathlib,json,sys,threading,traceback,time
root5=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024')
frames=sys._current_frames()
out={'observed_unix':time.time(),'control_threads':[],'work_files':[]}
for t in threading.enumerate():
 if 'FourControl' in t.name:
  frame=frames.get(t.ident)
  out['control_threads'].append({'name':t.name,'alive':t.is_alive(),'stack':[{'file':s.filename,'line':s.lineno,'function':s.name} for s in traceback.extract_stack(frame)[-18:]] if frame else []})
p=root5/'four_controls_publication_status.json'
if p.exists():
 state=json.loads(p.read_bytes());out['state']=state.get('state');work=pathlib.Path(state['work'])
 for f in work.rglob('*'):
  if f.is_file():out['work_files'].append({'relative':str(f.relative_to(work)),'bytes':f.stat().st_size,'mtime_unix':f.stat().st_mtime})
print(json.dumps(out))
