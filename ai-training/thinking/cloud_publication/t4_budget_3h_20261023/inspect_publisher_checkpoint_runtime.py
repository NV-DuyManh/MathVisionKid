import sys,json,time
out={'observed_unix':time.time(),'publisher_alive':budget_publisher_thread.is_alive()}
frames=[]
for f in sys._current_frames().values():
 stack=[]
 while f:
  if f.f_code.co_name in ('_budget_publish_loop','package_checkpoint','put','download','publish_file','next_chunk'):
   stack.append({'function':f.f_code.co_name,'line':f.f_lineno,'name':f.f_locals.get('name'),'path':str(f.f_locals.get('path','')),'generation':str(f.f_locals.get('gen',''))})
  f=f.f_back
 if stack:frames.append(stack)
out['publisher_stack']=frames
out['generation_folders']=[p.name for p in (budget_root/'training').glob('generation_step_*')]
out['readback_files']=[{'name':p.name,'bytes':p.stat().st_size} for p in (budget_root/'drive_publication/runstore_work').glob('*') if p.name.startswith('readback_') or p.name.startswith('upload_snapshot_checkpoint')]
print(json.dumps(out,ensure_ascii=False))
