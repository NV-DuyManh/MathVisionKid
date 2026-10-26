import json,pathlib,subprocess
out={'preflight_poll':budget_preflight_process.poll(),'log_tail':(budget_root/'gpu_preflight.log').read_text()[-5000:]}
if (budget_root/'gpu_preflight.json').exists():out['preflight']=json.loads((budget_root/'gpu_preflight.json').read_text())
out['gpu']=subprocess.run(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader'],capture_output=True,text=True).stdout
print(json.dumps(out))
