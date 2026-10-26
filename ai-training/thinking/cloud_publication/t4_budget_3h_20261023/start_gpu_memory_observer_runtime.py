import threading,subprocess,json,time,pathlib
if not (globals().get('budget_memory_observer') and budget_memory_observer.is_alive()):
 def _observe_budget_gpu_memory():
    p=budget_root/'gpu_total_memory_observations.json';peak=0;samples=0;first=time.time()
    while time.time()<budget_status['deadline_unix']+30:
      try:
       raw=subprocess.run(['nvidia-smi','--query-gpu=name,memory.used,memory.total,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=8).stdout.strip()
       parts=[x.strip() for x in raw.split(',')];used=int(parts[1]);total=int(parts[2]);util=int(parts[3]);samples+=1;peak=max(peak,used)
       out={'schema':'MathVisionKid.T4_total_memory_observation.v1','gpu':parts[0],'first_observed_unix':first,'latest_observed_unix':time.time(),'current_used_mib':used,'peak_total_used_mib':peak,'total_mib':total,'gpu_utilization_percent':util,'samples':samples,'sampling_interval_seconds':5,'gpu_allocated_by_observer':False,'scope':'all processes on this T4, sampled peak may miss shorter transient peaks'}
       tmp=p.with_suffix('.pending');tmp.write_text(json.dumps(out,indent=2));tmp.replace(p)
      except Exception as ex:
       (budget_root/'gpu_observer_error.txt').write_text(str(ex))
      time.sleep(5)
 budget_memory_observer=threading.Thread(target=_observe_budget_gpu_memory,daemon=True,name='BudgetGpuReadOnlyMemoryObserver');budget_memory_observer.start()
print(json.dumps({'state':'READ_ONLY_GPU_MEMORY_SAMPLING_STARTED','gpu_allocation':False}))
