import sys,json,time
stages=[]
for frame in sys._current_frames().values():
 while frame:
  if frame.f_code.co_name=='scan_and_sample':
   loc=frame.f_locals;stages.append({'line':frame.f_lineno,'member_index':loc.get('mi'),'counts':dict(loc.get('counts',{})),'selected_cases':len(loc.get('chosen',[])),'materialized_rows':len(loc.get('found_row_hashes',[])),'strata_labels':len(loc.get('labels',[]))})
  frame=frame.f_back
print(json.dumps({'observed_unix':time.time(),'stages':stages,'overlay':globals().get('selected_row_readback_overlay'),'sampler_alive':sampling_worker_thread.is_alive(),'gpu_orchestration':json.loads((budget_root/'orchestration_status.json').read_text())}))
