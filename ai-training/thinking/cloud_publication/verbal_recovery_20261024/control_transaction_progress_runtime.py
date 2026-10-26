import pathlib,json,threading,sys
from datetime import datetime,timezone
r=pathlib.Path('/content/mathvisionkid_verbal_recovery_20261024')
s=json.loads((r/'four_controls_publication_status.json').read_bytes());work=pathlib.Path(s['work'])
assert work.resolve().is_relative_to((r/'four_controls_publication').resolve())
d={'observed_utc':datetime.now(timezone.utc).isoformat(),'state':s['state'],'thread_alive':recovery_controls_thread.is_alive(),'retained_files':{}}
for folder in [work,work/'parents',work/'prepared']:
 if folder.exists():
  for p in folder.iterdir():
   if p.is_file():d['retained_files'][str(p.relative_to(work))]={'bytes':p.stat().st_size,'modified_unix':p.stat().st_mtime}
p=work/'four_controls_raw_verified.json'
if p.exists():
 try:d['verified_writes']=json.loads(p.read_bytes())['verified_writes']
 except json.JSONDecodeError:d['receipt_update_in_progress']=True
if recovery_controls_thread.is_alive():
 frame=sys._current_frames().get(recovery_controls_thread.ident);stack=[]
 while frame is not None:
  stack.append({'file':pathlib.Path(frame.f_code.co_filename).name,'function':frame.f_code.co_name,'line':frame.f_lineno});frame=frame.f_back
 d['stack_without_locals']=stack
print(json.dumps(d,ensure_ascii=False))
