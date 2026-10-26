import json,time,subprocess,pathlib
out={'observed_unix':time.time(),'remaining_seconds':budget_status['deadline_unix']-time.time()}
sp=budget_root/'sampling/launcher_status.json'
if sp.exists():out['sampler']=json.loads(sp.read_text())
out['gpu']=subprocess.run(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader'],capture_output=True,text=True).stdout
out['global_modules']=[k for k,v in list(globals().items()) if isinstance(v,torch.nn.Module)]
out['allocated_parent']=torch.cuda.memory_allocated()
if 'budget_process' in globals():out['worker_poll']=budget_process.poll()
for name in ['training/progress.json','training/base_generations.jsonl','training/run_complete.json','training/run_config.json']:
    p=budget_root/name
    if p.exists():out[name]=json.loads(p.read_text()) if p.suffix=='.json' else {'bytes':p.stat().st_size,'rows':len(p.read_text().splitlines())}
for name in ['training.log','gpu_preflight.log']:
    p=budget_root/name
    if p.exists():out[name+'_tail']=p.read_text()[-2500:]
print(json.dumps(out,ensure_ascii=False))
