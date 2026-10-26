import json,time
p=budget_root/'backward_preflight.json'
print(json.dumps({'observed_unix':time.time(),'process_poll':budget_backward_process.poll(),'result':json.loads(p.read_text()) if p.exists() else None,'log_tail':(budget_root/'backward_preflight.log').read_text()[-5000:]}))
