from pathlib import Path
import base64,hashlib,json
p=Path(__file__).parent
names=['recovery_policy.py','recovery_worker.py','publisher_runtime.py','owner_run_scope.json','frozen_code_references.json',
 'new_validation_candidates.jsonl','new_validation_candidate_notes.json','locked_test_candidates.jsonl','locked_test_notes.json',
 'source_semantic_review_g1_g3.json','source_semantic_review_g4_g5.json','cpu_validation.json',
 'test_recovery_policy.py','test_recovery_worker.py','test_recovery_publisher.py']
payload={n:base64.b64encode((p/n).read_bytes()).decode() for n in names}
hashes={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in names}
code='''import pathlib,json,base64,hashlib,sys,importlib.util
r=pathlib.Path('/content/mathvisionkid_quality_recovery_20261024')
assert r.exists() and not (r/'training/run_config.json').exists(),'Inspect existing initialized run; do not duplicate'
payload=PAYLOAD
expected=HASHES
for n,v in payload.items():
 b=base64.b64decode(v);assert hashlib.sha256(b).hexdigest()==expected[n]
 f=r/n
 if f.exists():assert f.read_bytes()==b,'Different source already staged: '+n
 else:f.write_bytes(b)
refs=json.loads((r/'frozen_code_references.json').read_bytes())
for original,local in [('corrective_worker_optimized_v2b.py','frozen_training_primitives.py'),('start_publisher_runtime.py','frozen_integrity_store.py')]:
 ref=refs[original];f=r/local
 b=f.read_bytes() if f.exists() else recovery_drive.files().get_media(fileId=ref['id']).execute()
 assert len(b)==ref['bytes'] and hashlib.sha256(b).hexdigest()==ref['sha256']
 if not f.exists():f.write_bytes(b)
if str(r) not in sys.path:sys.path.insert(0,str(r))
import recovery_policy as rp
spec=importlib.util.spec_from_file_location('qrec_preflight_worker',r/'recovery_worker.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
source=(r/'training_view.jsonl').read_bytes();assert hashlib.sha256(source).hexdigest()=='14929ba64e5c94d812f1fc3804c771ca8e41fa92285aed3a925282c39b1e4331'
rows=[json.loads(x) for x in source.splitlines()];dev=[json.loads(x) for x in (r/'new_validation_candidates.jsonl').read_text().splitlines()]
locked=[json.loads(x) for x in (r/'locked_test_candidates.jsonl').read_text().splitlines()]
scope=json.loads((r/'owner_run_scope.json').read_bytes())
assert hashlib.sha256((r/'new_validation_candidates.jsonl').read_bytes()).hexdigest()==scope['dev_sha256']
assert hashlib.sha256((r/'locked_test_candidates.jsonl').read_bytes()).hexdigest()==scope['locked_test_sha256']
ds=rp.screen_fixtures(dev,rows);ts=rp.screen_fixtures(locked,rows)
devrows=[{'messages':[{}, {'content':json.dumps({'problem':x['userproblem']})}]} for x in dev]
td=rp.screen_fixtures(locked,devrows)
assert not ds['collisions'] and not ts['collisions'] and not td['collisions'],'Frozen candidate collision; do not change training data to force pass'
m.atomic(r/'dev_train_screening.json',ds);m.atomic(r/'locked_train_screening.json',{'against_train':ts,'against_dev':td,'root_has_not_reviewed_test_content':True,'test_never_used_for_model_selection':True})
plan=rp.prepare_plan(rows,hashlib.sha256(source).hexdigest());m.atomic(r/'derived_sampling_plan.json',plan)
assert sum(x['mode']=='worked_solution' for x in rows)==plan['mode_counts']['worked_solution']==4000
m.atomic(r/'staged_code_hashes.json',expected)
spec=importlib.util.spec_from_file_location('qrec_publisher',r/'publisher_runtime.py');qrec_publisher=importlib.util.module_from_spec(spec);sys.modules[spec.name]=qrec_publisher;spec.loader.exec_module(qrec_publisher)
print(json.dumps({'preflight':'PASS_SOURCE_HASH_PLAN_SPLIT_SCREEN_ONLY','derived_view_rows':plan['view_rows'],'mode_counts':plan['mode_counts'],'source_plan_sha256':hashlib.sha256((r/'derived_sampling_plan.json').read_bytes()).hexdigest(),'dev_screen':ds,'locked_screen_counts_only':{'train_collisions':len(ts['collisions']),'dev_collisions':len(td['collisions'])},'source_labels_changed':False,'training_started':False}))
print(json.dumps(qrec_publisher.start(recovery_credentials)))
'''.replace('PAYLOAD',repr(payload)).replace('HASHES',repr(hashes))
(p/'stage_and_prepare_runtime.py').write_text(code,encoding='utf8')
print(json.dumps({'stage_bytes':len(code.encode()),'hashes':hashes},indent=2))
