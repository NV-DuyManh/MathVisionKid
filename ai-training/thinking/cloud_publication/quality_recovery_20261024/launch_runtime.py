import pathlib,json,hashlib,subprocess,os,time
r=pathlib.Path('/content/mathvisionkid_quality_recovery_20261024')
scope=json.loads((r/'owner_run_scope.json').read_bytes())
assert time.time()<scope['hard_deadline_unix']-1800,'No authorized training window'
assert not globals().get('recovery_process') or recovery_process.poll() is not None,'Worker already active'
assert not (r/'training/run_config.json').exists(),'Existing initialized run; inspect instead of duplicate'
assert json.loads((r/'install_status.json').read_bytes())['state']=='INSTALLED_NOT_TRAINING'
ps=json.loads((r/'publication/publication_status.json').read_bytes())
assert ps['state']=='RUNNING',ps.get('error')
for n in ['owner_run_scope.json','recovery_policy.py','recovery_worker.py','publisher_runtime.py']:
 proof=ps['artifacts'][n]
 assert proof['fresh_raw_readback_verified'] and hashlib.sha256((r/n).read_bytes()).hexdigest()==proof['sha256'],n
assert not json.loads((r/'dev_train_screening.json').read_bytes())['collisions']
plan=json.loads((r/'derived_sampling_plan.json').read_bytes())
assert plan['mode_counts']['worked_solution']==4000 and len(set(plan['schedule']))==plan['view_rows']
log=(r/'training.log').open('ab',buffering=0)
env={**os.environ,'TOKENIZERS_PARALLELISM':'false','PYTHONUNBUFFERED':'1'}
recovery_process=subprocess.Popen([str(r/'venv/bin/python'),'-u',str(r/'recovery_worker.py'),'--root',str(r)],stdout=log,stderr=subprocess.STDOUT,env=env)
receipt={'worker_pid':recovery_process.pid,'launched_unix':time.time(),'source_plan_sha256':hashlib.sha256((r/'derived_sampling_plan.json').read_bytes()).hexdigest(),'hard_deadline_unix':scope['hard_deadline_unix'],'training_started_confirmed':False,'next':'Fresh base load, validation baseline, then first optimizer step','previous_checkpoint_loaded':False}
(r/'launch_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
