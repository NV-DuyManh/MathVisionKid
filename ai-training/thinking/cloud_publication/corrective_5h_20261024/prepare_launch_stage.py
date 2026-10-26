from pathlib import Path
import base64,hashlib,json

p=Path(__file__).parent
sources={name:p/name for name in ['corrective_worker.py','start_publisher_runtime.py','cpu_validation.json','owner_run_scope.json']}
payload={n:base64.b64encode(s.read_bytes()).decode() for n,s in sources.items()}
hashes={n:hashlib.sha256(s.read_bytes()).hexdigest() for n,s in sources.items()}
code='''import pathlib,base64,json,hashlib,subprocess,os,importlib.util,sys,time
root5=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024')
payload=PAYLOAD
expected=HASHES
audit=json.loads((root5/'selected_view_tokenization_audit.json').read_bytes())
assert audit['state']=='PASS_STRUCTURAL_TOKENIZATION_ONLY'
assert audit['counts']['rows_tokenized']==16000
assert audit['counts']['exact_one_final_supervised_eot']==16000
assert not globals().get('corrective_process') or corrective_process.poll() is not None
assert not (root5/'training/run_config.json').exists(),'Fresh run already initialized; do not duplicate'
for n,v in payload.items():
 b=base64.b64decode(v);assert hashlib.sha256(b).hexdigest()==expected[n]
 path=root5/n
 if path.exists():assert path.read_bytes()==b,'Existing source differs: '+n
 else:path.write_bytes(b)
old=json.loads((root5/'staged_code_hashes.json').read_bytes())
old.update(expected)
(root5/'staged_code_hashes.json').write_text(json.dumps(old,indent=2))
manifest=json.loads((root5/'sampling_manifest.json').read_bytes())
print(json.dumps({'staged_hashes':expected,'manifest_protected_hash':manifest.get('protected_eval_hash_file_sha256'),'manifest_protected_count':manifest.get('protected_eval_hash_count')}))
spec=importlib.util.spec_from_file_location('corrective5h_publisher',root5/'start_publisher_runtime.py')
corrective5h_publisher=importlib.util.module_from_spec(spec);sys.modules[spec.name]=corrective5h_publisher;spec.loader.exec_module(corrective5h_publisher)
print(json.dumps(corrective5h_publisher.start_publisher(credentials=repair_credentials)))
'''.replace('PAYLOAD',repr(payload)).replace('HASHES',repr(hashes))
(p/'stage_launch_runtime.py').write_text(code,encoding='utf-8')

launch='''import pathlib,json,subprocess,os,time
root5=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024')
audit=json.loads((root5/'selected_view_tokenization_audit.json').read_bytes())
assert audit['state']=='PASS_STRUCTURAL_TOKENIZATION_ONLY'
pub=json.loads((root5/'drive_publication/publication_status.json').read_bytes())
assert pub['publisher_state']=='RUNNING' and pub.get('folder_id')
assert not globals().get('corrective_process') or corrective_process.poll() is not None
assert not (root5/'training/run_config.json').exists(),'Already initialized; do not duplicate'
cmd=[str(root5/'venv/bin/python'),'-u',str(root5/'corrective_worker.py'),'--train-view',str(root5/'training_view.jsonl'),'--view-manifest',str(root5/'sampling_manifest.json'),'--eval-fixtures',str(root5/'eval_fixtures.jsonl'),'--tokenizer-helper',str(root5/'exhaustive_colab_loader.py'),'--out',str(root5/'training'),'--eval-timeout-seconds','900']
env=dict(os.environ);env['TOKENIZERS_PARALLELISM']='false'
log=(root5/'training.log').open('ab')
corrective_process=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
launch={'worker_pid':corrective_process.pid,'launched_unix':time.time(),'command':cmd,'requested_training_wall_seconds':18000,'optimizer_pilot':False,'training_started':False,'folder_id':pub['folder_id']}
(root5/'launch_status.json').write_text(json.dumps(launch,indent=2))
print(json.dumps(launch))
'''
(p/'launch_worker_runtime.py').write_text(launch,encoding='utf-8')
