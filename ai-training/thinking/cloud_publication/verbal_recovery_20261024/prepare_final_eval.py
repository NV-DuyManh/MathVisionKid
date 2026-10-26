from pathlib import Path
import json,hashlib,base64
p=Path(__file__).parent;old=p.parent/'quality_recovery_20261024'
notes=json.loads((p/'locked_test_notes.json').read_bytes());locked=notes['fixture_sha256']
code=(old/'final_evaluation_worker.py').read_text(encoding='utf8')
assert hashlib.sha256(code.encode()).hexdigest()=='5d8d7e89e0a31615db2820c99f4074038ea827b0303c94a3685c9517f2380b3e'
code=code.replace("LOCKED_SHA256 = '41413ac3e61e7180cee53d06ccec6186256f1cfdf845557a6a598822f6ca22d0'",'LOCKED_SHA256 = '+repr(locked)).replace('MathVisionKid.quality_recovery_locked_final_eval.v1','MathVisionKid.verbal_recovery_locked_final_eval.v1')
code=code.replace("scope.get('locked_test_sha256') != LOCKED_SHA256","read(root / 'locked_test_binding.json').get('fixture_sha256') != LOCKED_SHA256")
code=code.replace("'recovery_policy.py', 'frozen_training_primitives.py'):","'recovery_policy.py', 'frozen_training_primitives.py','verbal_training_renderer_v3.py','locked_test_binding.json'):")
line="        H = load(root / 'frozen_training_primitives.py', 'final_eval_frozen_primitives')"
assert code.count(line)==1
code=code.replace(line,line+"""
        if sha(root / 'verbal_training_renderer_v3.py') != '6b15233ae253eed7825864413edbdf3f8553ad955ef248e045c05f64e4473057':
            raise ValueError('Renderer changed before final test')
        V=load(root / 'verbal_training_renderer_v3.py','verbal_final_renderer')
        def verbal_fixture_messages(fixture):
            return [{'role':'system','content':H.SYSTEM},{'role':'user','content':V.prompt({'grade':fixture['grade'],'problem':fixture['userproblem'],'mode':H.MODE_MAP[fixture['mode']]})}]
        H.fixture_messages=verbal_fixture_messages""")
compile(code,'verbal_final_eval_worker.py','exec');(p/'final_evaluation_worker.py').write_text(code,encoding='utf8')
binding={**notes,'hard_deadline_unix':json.loads((p/'owner_run_scope.json').read_bytes())['hard_deadline_unix'],'frozen_before_reading_candidate_outputs':True,'inherited_owner_scope_locked_sha_is_previous_consumed_test_provenance_only':True}
(p/'locked_test_binding.json').write_text(json.dumps(binding,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
names=['locked_test_candidates.jsonl','locked_test_notes.json','locked_test_binding.json','final_evaluation_worker.py','forward_loss_audit.json']
payload={n:base64.b64encode((p/n).read_bytes()).decode() for n in names}
runtime='''import pathlib,json,base64,hashlib,sys
r=pathlib.Path('/content/mathvisionkid_verbal_recovery_20261024')
for n,v in PAYLOAD.items():
 b=base64.b64decode(v);f=r/n
 if f.exists():assert f.read_bytes()==b,'Do not overwrite frozen candidate/test/evalcode'
 else:f.write_bytes(b)
binding=json.loads((r/'locked_test_binding.json').read_bytes())
assert hashlib.sha256((r/'locked_test_candidates.jsonl').read_bytes()).hexdigest()==binding['fixture_sha256']
if str(r) not in sys.path:sys.path.insert(0,str(r))
import recovery_policy as policy
fixtures=[json.loads(x) for x in (r/'locked_test_candidates.jsonl').read_text().splitlines()]
rows=[json.loads(x) for x in (r/'training_view.jsonl').read_text().splitlines()]
screen=policy.screen_fixtures(fixtures,rows)
dev=[json.loads(x) for x in (r/'new_validation_candidates.jsonl').read_text().splitlines()]
devrows=[{'messages':[{}, {'content':json.dumps({'problem':x['userproblem']})}]} for x in dev]
devscreen=policy.screen_fixtures(fixtures,devrows)
assert not screen['collisions'] and not devscreen['collisions'],'Test collision; do not tune training to force pass'
out={'fixture_sha256':binding['fixture_sha256'],'train_screen':screen,'dev_screen':devscreen,'frozen_before_candidate_outputs_review':True,'old_locked20_not_loaded':True,'test_inference_executed':False}
(r/'locked_preflight.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\\n')
print(json.dumps(out,ensure_ascii=False))
'''.replace('PAYLOAD',repr(payload))
(p/'stage_locked_runtime.py').write_text(runtime,encoding='utf8')
print(json.dumps({'worker_sha256':hashlib.sha256(code.encode()).hexdigest(),'locked_sha256':locked,'stage_bytes':len(runtime.encode())}))
