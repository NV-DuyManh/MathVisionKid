import pathlib,json,hashlib,subprocess,os,time,socket
rr=pathlib.Path('/content/mathvisionkid_recovery_20261026')
assert socket.gethostname()=='fb7636900c84','Inspect replacement runtime before launch'
assert not globals().get('conditional_training_process') or conditional_training_process.poll() is not None
assert not (rr/'training/run_config.json').exists(),'Do not duplicate initialized run'
assert (rr/'install_complete.json').exists() and conditional_install_process.poll()==0
rpins=json.loads((rr/'active_staged_code_pins.json').read_bytes())
for rn,rhash in rpins.items():assert hashlib.sha256((rr/rn).read_bytes()).hexdigest()==rhash,rn
assert rpins['recovery_worker_20261026.py']=='b618f2d961dd0d342f006a8b07abe39268962fc0bdcab43622c425ee2bf67d4f'
scope=json.loads((rr/'owner_run_scope.json').read_bytes())
assert scope['reserve_seconds']==600 and scope['hard_deadline_utc']=='2026-10-26T11:14:18Z'
assert time.time()<scope['hard_deadline_unix']-scope['reserve_seconds']
preflight=json.loads((rr/'preflight_complete.json').read_bytes());assert preflight['returncode']==0
assert (rr/'training/pretrain_source_qa_prepared.json').exists()
assert not (rr/'training/pretrain_qa_approved.json').exists(),'Hold optimizer until code raw readback and reviewed source approval'
pub=json.loads((rr/'publication/publication_status.json').read_bytes())
assert pub['state']=='RUNNING' and not pub['errors']
conditional_training_process=subprocess.Popen([str(rr/'venv/bin/python'),'-u',str(rr/'recovery_worker_20261026.py'),'--root',str(rr)],
 stdout=(rr/'training.log').open('ab',buffering=0),stderr=subprocess.STDOUT,
 env={**os.environ,'TOKENIZERS_PARALLELISM':'false','PYTHONPATH':str(rr),'PYTORCH_ALLOC_CONF':'expandable_segments:True'})
receipt={'worker_launched':True,'pid':conditional_training_process.pid,'phase':'BASE_LOADING_THEN_BASE_DEVELOPMENT_EVALUATION',
 'optimizer_updates_confirmed':False,'new_run_folder_id':pub['folder_id'],'hard_deadline_utc':scope['hard_deadline_utc'],
 'train_cutoff_utc':scope['train_cutoff_utc'],'previous_adapter_loaded':False,'whole_corpus_training_claimed':False}
(rr/'launch_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
