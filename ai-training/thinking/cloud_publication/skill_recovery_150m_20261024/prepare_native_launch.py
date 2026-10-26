from pathlib import Path
import json,hashlib,base64
p=Path(__file__).parent
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
policy={'schema':'MathVisionKid.native_probe_selection_policy.v1','frozen_before_probe_outputs':True,'dev_indices':[0,1,5,6,7,10,12,13,16,18,19,22,24,25,29],'whole_subset_selection_only':True,'minimum_full_task_gain':1,'maximum_baseline_pass_regressions':0,'maximum_new_critical_errors':0,'answer_pass_count_must_not_decrease':True,'all_rows_must_end_with_nonempty_final_and_eos':True,'seed':'Same perfixture as original I comparator','candidate':'Untrained pinned Qwen3 native thinking, no examples/adapter, T0.6 topP0.95 topK20 minP0 maxnew1536','prior_final20_excluded_from_training_and_selection':True,'final15_once_only_after_dev_gate':True,'no_reselect_from_final15':True,'budget_deadline_utc':'2026-10-24T15:07:46Z','paid_resources':False,'new_human_certification':False}
def freeze(n,v):
 f=p/n;b=(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
 if f.exists():assert f.read_bytes()==b
 else:f.write_bytes(b)
freeze('native_probe_selection_policy.json',policy)
scope={'schema':'MathVisionKid.native_probe_scope.v1','dev_fixture_sha256':'75eab78085830aa5bf0cf856eb6f70d2630e2407c8143409816dec94d849aaed','selection_policy_sha256':sha(p/'native_probe_selection_policy.json'),'native_locked15_sha256':sha(p/'native_locked15.jsonl'),'owner_budget_unchanged':True,'native_dev_subset_count':15,'native_final_count':15,'source_and_old_results_preserved':True}
freeze('native_probe_scope.json',scope)
qa={'schema':'MathVisionKid.native_locked15_root_preflight.v1','fixture_sha256':scope['native_locked15_sha256'],'actual15_questions_references_rubrics_read':True,'exact_fraction_decimal_check_script_sha256':sha(p/'native_locked15_exact_checks.py'),'exact_checks_passed':13,'semantic_qa':{'task_and_data_meaning':True,'grade_appropriateness':True,'math_and_oracle':True,'units':True,'pedagogy_and_fully_requested_task':True,'grounded_student_work_or_missing_guard':True,'no_hint_answer_leak_in_applicable_tasks':True},'not_training_data':True,'human_review_claimed':False,'original_draft_preserved':True,'screen_full6_5m_claimed':False}
freeze('native_locked15_root_review.json',qa)
names=['native_thinking_probe.py','test_native_thinking_probe.py','native_locked15.jsonl','native_locked15_notes.json','native_locked15_exact_checks.py','native_locked15_root_review.json','native_probe_scope.json','native_probe_selection_policy.json','context_trial_final_review.json']
payload={n:base64.b64encode((p/n).read_bytes()).decode()for n in names};pins={n:sha(p/n)for n in names}
code="""import pathlib,json,hashlib,base64,subprocess,os,time,sys
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024');payload=PAYLOAD;pins=PINS
assert skill_training_process.poll()==skill_fewshot_process.poll()==skill_final_process.poll()==0
assert not globals().get('skill_native_dev_process') or skill_native_dev_process.poll() is not None
assert not(r/'native_probe/dev').exists(),'Preserve prior native probe attempt'
for n,v in payload.items():
 b=base64.b64decode(v);assert hashlib.sha256(b).hexdigest()==pins[n]
 if(r/n).exists():assert(r/n).read_bytes()==b
 else:(r/n).write_bytes(b)
sys.path.insert(0,str(r));import recovery_policy_v2 as policy
f=[json.loads(x)for x in(r/'native_locked15.jsonl').read_text().splitlines()]
rows=[json.loads(x)for x in(r/'training_view.jsonl').read_text().splitlines()]
screen=policy.screen_fixtures(f,rows);assert not screen['collisions'],screen
prior=[]
for n in['new_validation_candidates.jsonl','locked_test_candidates.jsonl']:prior+=[json.loads(x)for x in(r/n).read_text().splitlines()]
keys={policy.prompt_key(x['userproblem'],True)for x in prior};assert not any(policy.prompt_key(x['userproblem'],True)in keys for x in f)
(r/'native_locked15_train_screening.json').write_text(json.dumps({'actual16k_screen':screen,'prior_dev_and_context_final_numbermasked_collisions':0,'full6_5m_independence':'UNPROVEN','fixture_sha256':pins['native_locked15.jsonl']},indent=2)+'\\n')
assert time.time()<json.loads((r/'owner_run_scope.json').read_bytes())['hard_deadline_unix']-2100
skill_native_dev_process=subprocess.Popen([str(r/'venv/bin/python'),'-u',str(r/'native_thinking_probe.py'),'--root',str(r),'--phase','dev'],stdout=(r/'native_probe_dev.log').open('ab',buffering=0),stderr=subprocess.STDOUT,env={**os.environ,'TOKENIZERS_PARALLELISM':'false','PYTHONPATH':str(r)})
(r/'native_launch_pins.json').write_text(json.dumps({'files':pins,'pid':skill_native_dev_process.pid,'started_unix':time.time(),'dev_only':True},indent=2)+'\\n')
print(json.dumps({'native_probe_dev_launched':True,'pid':skill_native_dev_process.pid,'new_weight_training':False,'old_train_and_evaluations_exited':True,'new15_sealed_sha256':pins['native_locked15.jsonl'],'actual16k_screen':screen,'owner_deadline_unchanged':True}))
""".replace('PAYLOAD',repr(payload)).replace('PINS',repr(pins))
compile(code,'native_launch','exec');(p/'launch_native_runtime.py').write_text(code,encoding='utf8');print(json.dumps({'policy_sha256':scope['selection_policy_sha256'],'scope_sha256':sha(p/'native_probe_scope.json'),'worker_sha256':pins['native_thinking_probe.py'],'script_bytes':len(code)}))
