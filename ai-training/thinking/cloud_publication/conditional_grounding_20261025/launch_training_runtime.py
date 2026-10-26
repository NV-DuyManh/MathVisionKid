import pathlib,json,hashlib,subprocess,os,time,socket
r=pathlib.Path('/content/mathvisionkid_conditional_grounding_20261025')
assert socket.gethostname()=='1611698ac255','Runtime changed before launch'
assert not globals().get('conditional_training_process') or conditional_training_process.poll() is not None
assert not (r/'training/run_config.json').exists(),'Refuse duplicate initialized run'
assert (r/'install_complete.json').is_file() and conditional_install_process.poll()==0
scope=json.loads((r/'owner_run_scope.json').read_bytes())
assert time.time()<scope['hard_deadline_unix']-3600
pins=json.loads((r/'preparation_code_provenance.json').read_bytes())['derived_files']
for name,wanted in pins.items():
 assert hashlib.sha256((r/name).read_bytes()).hexdigest()==wanted,name
publication=json.loads((r/'publication/publication_status.json').read_bytes())
assert publication['state']=='RUNNING' and publication['folder_name']=='MathVisionKid_CONDITIONAL_GROUNDING_20261025'
assert not publication['errors']
conditional_training_process=subprocess.Popen(
 [str(r/'venv/bin/python'),'-u',str(r/'recovery_worker_v3.py'),'--root',str(r)],
 stdout=(r/'training.log').open('ab',buffering=0),stderr=subprocess.STDOUT,
 env={**os.environ,'TOKENIZERS_PARALLELISM':'false','PYTHONPATH':str(r)})
proof={'training_worker_launched':True,'pid':conditional_training_process.pid,
 'model_backend':'native Transformers/PEFT/bitsandbytes',
 'optimizer_started_confirmed':False,'previous_adapter_loaded':False,
 'max_updates':500,'one_derived_pass_maximum':True,'gate_steps':[100,300,500],
 'hard_deadline_utc':scope['hard_deadline_utc'],'folder_id':publication['folder_id']}
(r/'launch_receipt.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof))
