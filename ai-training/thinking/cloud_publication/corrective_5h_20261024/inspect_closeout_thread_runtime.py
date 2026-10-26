import json,pathlib,sys,traceback,time
r=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024')
s=json.loads((r/'four_controls_publication_status.json').read_bytes())
w=pathlib.Path(s['work'])
print(json.dumps({'state':s['state'],'files':[{'name':str(p.relative_to(w)),'bytes':p.stat().st_size,'modified_unix':p.stat().st_mtime} for p in w.rglob('*') if p.is_file()],'now':time.time()},ensure_ascii=False))
f=sys._current_frames().get(corrective_controls_thread.ident)
if f:print(''.join(traceback.format_stack(f)[-15:]))
