import pathlib,json,time,hashlib,subprocess,os
r=pathlib.Path('/content/mathvisionkid_verbal_recovery_20261024')
assert not (r/'training/run_config.json').exists(),'Never duplicate initialized trial'
assert not globals().get('verbal_process') or verbal_process.poll() is not None
ps=json.loads((r/'publication/publication_status.json').read_bytes());assert ps['state']=='RUNNING'
for n in ['owner_run_scope.json','recovery_worker.py','publisher_runtime.py','recovery_policy.py']:
 proof=ps['artifacts'][n];assert proof['fresh_raw_readback_verified'] and hashlib.sha256((r/n).read_bytes()).hexdigest()==proof['sha256']
assert time.time()<json.loads((r/'owner_run_scope.json').read_bytes())['hard_deadline_unix']-2700
verbal_process=subprocess.Popen([str(r/'venv/bin/python'),'-u',str(r/'recovery_worker.py'),'--root',str(r)],stdout=(r/'training.log').open('ab',buffering=0),stderr=subprocess.STDOUT,env={**os.environ,'TOKENIZERS_PARALLELISM':'false','PYTHONUNBUFFERED':'1'})
print(json.dumps({'worker_launched':True,'pid':verbal_process.pid,'max_updates':50,'optimizer_started_confirmed':False,'locked20_not_used':True,'factors_changed':['prompt formatting','target formatting']}))
