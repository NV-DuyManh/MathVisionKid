from pathlib import Path
import base64,hashlib,json
p=Path(__file__).parent
names=['corrective_worker_optimized_v2.py','pair_weighted_batching_v2.py','test_optimized_v2.py','owner_budget_revision_config.json']
payload={n:base64.b64encode((p/n).read_bytes()).decode() for n in names}
hashes={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in names}
assert hashes['corrective_worker_optimized_v2.py']=='07f30dedd6b330218283ec7771e72c84d5ae008cf3c27885a1a8de8c0b169761'
code='''import pathlib,base64,json,hashlib,signal,time
root5=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024')
payload=PAYLOAD
hashes=HASHES
for n,v in payload.items():
 b=base64.b64decode(v);assert hashlib.sha256(b).hexdigest()==hashes[n]
 p=root5/n
 if p.exists():assert p.read_bytes()==b,'Do not overwrite prior code bytes: '+n
 else:p.write_bytes(b)
assert corrective_process.poll() is None,'Old worker already exited; inspect before transition'
assert not (root5/'owner_optimization_transition_config.json').exists(),'Do not duplicate stop request'
before=json.loads((root5/'training/latest.json').read_bytes())
assert before['step']>1,'Wait for first regular production checkpoint before interrupting'
record={'owner_authorized_optimization':True,'state':'REQUESTING_OLD_WORKER_STOP','requested_unix':time.time(),'old_pid':corrective_process.pid,'last_regular_checkpoint':before,'code_hashes':hashes,'preserve_all_data':True,'exact_optimizer_boundary_claimed':False,'resume_candidate_requires_coherence_checks':True}
(root5/'owner_optimization_transition_config.json').write_text(json.dumps(record,indent=2))
corrective_process.send_signal(signal.SIGINT)
try:exitcode=corrective_process.wait(timeout=50)
except Exception as e:exitcode=None;record['wait_error']=repr(e)
record.update(old_exit=exitcode,state='OLD_WORKER_EXITED_CHECKPOINT_CANDIDATE' if exitcode is not None else 'WAITING_OLD_WORKER_EXIT')
p=root5/'training/error.json'
if p.exists():record['old_error']=json.loads(p.read_bytes())
p=root5/'training/latest.json'
if p.exists():record['latest_after_stop']=json.loads(p.read_bytes())
(root5/'owner_optimization_transition_config.json').write_text(json.dumps(record,indent=2))
print(json.dumps({k:v for k,v in record.items() if k!='old_error'}))
if 'old_error' in record:print(json.dumps({'old_error_type':record['old_error'].get('error_type'),'traceback':record['old_error'].get('traceback','')[-2400:]}))
'''.replace('PAYLOAD',repr(payload)).replace('HASHES',repr(hashes))
(p/'stage_and_pause_optimized_runtime.py').write_text(code,encoding='utf-8')
