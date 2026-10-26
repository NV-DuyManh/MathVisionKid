from pathlib import Path
import base64,hashlib,json,subprocess,sys
P=Path(__file__).parent;OLD=P.parent/'skill_recovery_150m_20261024'
result=subprocess.run([sys.executable,'-X','utf8','-m','unittest','discover','-s',str(P),'-p','test_*.py'],capture_output=True,text=True)
if result.returncode:raise RuntimeError(result.stdout+result.stderr)
(P/'cpu_validation.json').write_text(json.dumps({'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'model_or_gpu_called':False},indent=2)+'\n',encoding='utf8')
names=['recovery_worker_v3.py','recovery_policy_v2.py','recovery_worker.py','recovery_worker_v2.py','recovery_policy.py',
 'inference_contract.py','publisher_runtime.py','conditional_behavior_renderer.py','behavior_renderer.py',
 'verbal_training_renderer_v3.py','native_backend.py','exact_math_audit.py','development_root_review.json',
 'development_author_notes.json','preparation_code_provenance.json','cpu_validation.json',
 'test_recovery_policy.py','test_recovery_worker.py','test_conditional_behavior_renderer.py','test_behavior_renderer.py']
sources={n:P/n for n in names}
sources['new_validation_candidates.jsonl']=P/'development_candidates.jsonl'
sources['new_validation_candidate_notes.json']=P/'development_author_notes.json'
sources['prior_used_development.jsonl']=P.parent/'quality_recovery_20261024/new_validation_candidates.jsonl'
for name in ['source_semantic_review_g1_g3.json','source_semantic_review_g4_g5.json']:
 sources[name]=OLD/name
sources['projection_preflight_previous.json']=OLD/'projection_preflight.json'
sources['source_behavior_samples_previous.json']=OLD/'source_behavior_samples.json'
payload={name:base64.b64encode(path.read_bytes()).decode() for name,path in sources.items()}
pins={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in sources.items()}
template='''import pathlib,json,hashlib,base64,sys,importlib.util,subprocess,time,socket
r=pathlib.Path('/content/mathvisionkid_conditional_grounding_20261025')
assert socket.gethostname()=='1611698ac255','Runtime changed; inspect before staging'
assert r.exists() and (r/'input_readback.json').exists()
assert conditional_install_process.poll()==0,'Missing dependency installer not complete'
assert not (r/'training/run_config.json').exists(),'Initialized run must not be duplicated'
assert not globals().get('conditional_training_process') or conditional_training_process.poll() is not None
payload=PAYLOAD;pins=PINS
for name,encoded in payload.items():
 raw=base64.b64decode(encoded);assert hashlib.sha256(raw).hexdigest()==pins[name]
 path=r/name
 if path.exists():assert path.read_bytes()==raw,'Different staged file; preserve and inspect: '+name
 else:path.write_bytes(raw)
sys.path.insert(0,str(r))
import recovery_policy_v2 as policy
import conditional_behavior_renderer as renderer
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
scope=json.loads((r/'owner_run_scope.json').read_bytes())
assert time.time()<scope['hard_deadline_unix']-3600,'Insufficient time for new run'
binding={'original_scope_sha256':sha(r/'owner_run_scope.json'),'dev_sha256':pins['new_validation_candidates.jsonl'],
 'locked_test_sha256':'0526ec69b5b1730376835c2961d32c79c187f6d1d0fe3057f2d98358b71674f7',
 'repair_reason':'Fresh reviewed development30; unused native15 reserved final-only and not loaded by training worker. Owner budget unchanged.'}
(r/'owner_scope_binding_v2.json').write_text(json.dumps(binding,sort_keys=True,indent=2)+'\\n')
source=(r/'training_view.jsonl').read_bytes();assert hashlib.sha256(source).hexdigest()=='14929ba64e5c94d812f1fc3804c771ca8e41fa92285aed3a925282c39b1e4331'
rows=[json.loads(line) for line in source.splitlines()]
dev=[json.loads(line) for line in (r/'new_validation_candidates.jsonl').read_bytes().splitlines()]
assert len(dev)==30
screen=policy.screen_fixtures(dev,rows)
prior=[json.loads(line) for line in (r/'prior_used_development.jsonl').read_bytes().splitlines()]
prior_rows=[{'messages':[{}, {'content':json.dumps({'problem':f['userproblem']})}]} for f in prior]
screen['against_prior_used_development']=policy.screen_fixtures(dev,prior_rows)
assert not screen['collisions'] and not screen['against_prior_used_development']['collisions'],'Development collision; preserve original and adjudicate before model outputs'
(r/'dev_train_screening.json').write_text(json.dumps(screen,sort_keys=True,indent=2)+'\\n')
plan=policy.prepare_plan(rows,hashlib.sha256(source).hexdigest())
assert plan['mode_counts']['worked_solution']==4000 and len(plan['schedule'])==len(set(plan['schedule']))
(r/'derived_sampling_plan.json').write_text(json.dumps(plan,ensure_ascii=False,sort_keys=True,indent=2)+'\\n')
raw_by_id={json.loads(line)['sample_id']:(json.loads(line),hashlib.sha256(line).hexdigest()) for line in source.splitlines()}
samples=json.loads((r/'projection_preflight_previous.json').read_bytes())['samples']+json.loads((r/'source_behavior_samples_previous.json').read_bytes())['samples']
for sample in samples:
 row,rawhash=raw_by_id[sample['sample_id']]
 assert rawhash==sample['source_original_raw_row_sha256']
 projected,proof=renderer.render(row)
 assert projected['messages'][-1]['content']==sample['actual_target'],'Actual source target projection differs from previously read sample'
oldreviews={n:sha(r/n) for n in ['source_semantic_review_g1_g3.json','source_semantic_review_g4_g5.json']}
qa={'root_actual_source_samples_reviewed':True,'human_review_claimed':False,'source_plan_sha256':sha(r/'derived_sampling_plan.json'),
 'renderer_sha256':sha(r/'conditional_behavior_renderer.py'),'source_review_files_sha256':oldreviews,
 'sample_count':24,'all24_original_raw_source_hashes_reverified_in_current_cloud':True,'all24_targets_equal_previously_read_content':True,
 'review_scope':'Reused24fullsource semantic reviews, exact raw-source rebind and unchanged target check. Conditional instruction suffix independently reviewed; no new human attestation or fullcorpus semantic proof.'}
(r/'source_qa_binding.json').write_text(json.dumps(qa,sort_keys=True,indent=2)+'\\n')
(r/'training').mkdir(exist_ok=True)
(r/'training/pretrain_qa_approved.json').write_text(json.dumps(qa,sort_keys=True,indent=2)+'\\n')
meta=subprocess.check_output([str(r/'venv/bin/python'),'-c',"import importlib.metadata as m,json,sys;print(json.dumps({'python':sys.version,'versions':{k:m.version(k) for k in ['torch','transformers','peft','accelerate','bitsandbytes']}}))"],text=True)
(r/'install_complete.json').write_text(json.dumps({'state':'NATIVE_ENVIRONMENT_READY_NOT_MODEL_TESTED','metadata':json.loads(meta),'only_missing_bnb_installed':True},indent=2)+'\\n')
spec=importlib.util.spec_from_file_location('conditional_publisher_runtime',r/'publisher_runtime.py')
conditional_publisher=importlib.util.module_from_spec(spec);sys.modules[spec.name]=conditional_publisher;spec.loader.exec_module(conditional_publisher)
publication=conditional_publisher.start(recovery_credentials,r)
print(json.dumps({'staged':True,'dev_sha256':pins['new_validation_candidates.jsonl'],'dev_screen':screen,
 'source_plan_sha256':qa['source_plan_sha256'],'derived_rows':len(plan['schedule']),'all4000worked_retained':True,
 'publisher':publication,'environment':json.loads(meta),'training_started':False}))
'''
code=template.replace('PAYLOAD',repr(payload)).replace('PINS',repr(pins))
compile(code,'stage_new_run','exec')
(P/'stage_runtime.py').write_bytes(code.encode())
(P/'staged_code_pins.json').write_text(json.dumps(pins,indent=2)+'\n')
print(json.dumps({'stage_bytes':len(code.encode()),'files':len(pins),'tests':result.stderr.strip()}))
