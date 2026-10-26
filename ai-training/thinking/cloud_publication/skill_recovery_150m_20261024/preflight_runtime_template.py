import pathlib,json,hashlib,importlib.util,sys,collections,base64,gzip
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024');payload=__PAYLOAD__;pins=__PINS__
assert skill_benchmark_process.poll()==0
assert not (r/'training/run_config.json').exists()
for n,value in payload.items():
 b=base64.b64decode(value);assert hashlib.sha256(b).hexdigest()==pins[n];q=r/n
 if q.exists():assert q.read_bytes()==b,'Never change staged code '+n
 else:q.write_bytes(b)
def load(n):
 spec=importlib.util.spec_from_file_location('skill_'+n,r/(n+'.py'));mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod);return mod
sys.path.insert(0,str(r));P=load('recovery_policy');B=load('behavior_renderer')
raw=(r/'training_view.jsonl').read_bytes();source_sha=hashlib.sha256(raw).hexdigest();rows=[json.loads(x) for x in raw.splitlines()]
assert source_sha=='14929ba64e5c94d812f1fc3804c771ca8e41fa92285aed3a925282c39b1e4331' and len(rows)==16000
plan=P.prepare_plan(rows,source_sha);(r/'derived_sampling_plan.json').write_text(json.dumps(plan,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
dev=[json.loads(x) for x in (r/'new_validation_candidates.jsonl').read_text().splitlines()]
locked=[json.loads(x) for x in (r/'locked_test_candidates.jsonl').read_text().splitlines()]
for label,fixtures in [('dev',dev),('locked',locked)]:
 screen=P.screen_fixtures(fixtures,rows);assert not screen['collisions'],label+'actual16k collision'
 (r/(label+'_train_screening.json')).write_text(json.dumps(screen,ensure_ascii=False,indent=2)+'\n')
devkeys={P.prompt_key(x['userproblem'],m) for x in dev for m in (False,True)}
assert not [x['id'] for x in locked if any(P.prompt_key(x['userproblem'],m) in devkeys for m in (False,True))]
systems=collections.Counter(hashlib.sha256(x['messages'][0]['content'].encode()).hexdigest() for x in rows)
byid={x['sample_id']:x for x in rows};sample=[];seen=set();target_mismatch=[];dedup_count=0
for row in rows:
 neutral,proof=B.render(row)
 original_target=B.V3.target(json.loads(row['messages'][-1]['content']),row['mode'])[0]
 assert neutral['messages'][-1]['content']==original_target and proof['target_unchanged_from_v3']
 assert not any(x in neutral for x in ['human_verified','teacher_certified','owner_human_reviewed','source_role','acceptance_status'])
 prompt=json.loads(row['messages'][1]['content']);work=prompt.get('student_work');wt=work.get('text','') if isinstance(work,dict) else (work or '')
 if wt and wt in prompt['problem']:dedup_count+=1
 key=(row['grade'],row['mode'],P._behavior(row))
 if key not in seen and (len(sample)<14):
  seen.add(key);sample.append({'sample_id':row['sample_id'],'grade':row['grade'],'mode':row['mode'],'behavior':key[2],'source_original_raw_row_sha256':hashlib.sha256(next(b for b in raw.splitlines() if json.loads(b)['sample_id']==row['sample_id'])).hexdigest(),'actual_prompt':neutral['messages'][1]['content'],'actual_target':neutral['messages'][-1]['content']})
def distribution(items):
 return {'grade':dict(collections.Counter(str(x['grade']) for x in items)),'mode':dict(collections.Counter(x['mode'] for x in items)),'behavior':dict(collections.Counter(P._behavior(x) for x in items))}
summary={'source_rows':16000,'view_rows':plan['view_rows'],'source_sha256':source_sha,'plan_sha256':hashlib.sha256((r/'derived_sampling_plan.json').read_bytes()).hexdigest(),'original_source_system_sha_counts':dict(systems),'new_train_eval_system_sha256':hashlib.sha256(B.SYSTEM.encode()).hexdigest(),'source_targets_exactly_unchanged_v3':True,'old_source_labels_not_carried_to_changed_bytes':True,'source_duplicate_student_work_rows_detected':dedup_count,'prefix1600':distribution([byid[x] for x in plan['schedule'][:1600]]),'whole_derived':distribution([byid[x] for x in plan['schedule']]),'samples':sample,'renderer_sha256':pins['behavior_renderer.py'],'scope':'Structural source preservation and small actual content sample; not exhaustive semantic proof or human certification.'}
assert hashlib.sha256((r/'training_view.jsonl').read_bytes()).hexdigest()==source_sha
(r/'projection_preflight.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
binding={'fixture_sha256':hashlib.sha256((r/'locked_test_candidates.jsonl').read_bytes()).hexdigest(),'count':20,'frozen_before_new_candidate_outputs':True,'not_used_for_training':True,'no_prior_locked_fixture_access':True,'source_screening_scope':'Actual16k exact+numbermasked only; full6.5M independence unproven'}
(r/'locked_test_binding.json').write_text(json.dumps(binding,indent=2)+'\n')
print('SKILL_PREFLIGHT_GZIP_BASE64:'+base64.b64encode(gzip.compress(json.dumps({'summary':summary,'locked_binding':binding}).encode())).decode())
print(json.dumps({'preflight_complete':True,'prefix1600':summary['prefix1600'],'source_targets_changed':False,'model_loaded':False,'training_started':False}))
