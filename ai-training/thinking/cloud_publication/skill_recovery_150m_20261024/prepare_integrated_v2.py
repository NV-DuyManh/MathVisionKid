from pathlib import Path
import json,hashlib,subprocess,sys
p=Path(__file__).parent;old=p.parent/'verbal_recovery_20261024'
policy=(p/'recovery_policy.py').read_text(encoding='utf8')
a="eligible=safe and (answer_gain>=1 or (perfect and candidate['answers']==base['answers'] and hint_gain>=1))"
b="eligible=safe and candidate['answers']>=base['answers'] and candidate['total']>base['total']"
assert policy.count(a)==1;policy=policy.replace(a,b)
policy=policy.replace("'candidate_eligible':eligible", "'candidate_eligible':eligible,'eligibility_rule':'No baseline-pass regression/new critical/new hint leak, retain all base answers, and at least one full-task gain in any requested tutor mode'")
(p/'recovery_policy_v2.py').write_text(policy,encoding='utf8')
worker=(p/'recovery_worker.py').read_text(encoding='utf8').replace('from recovery_policy import','from recovery_policy_v2 import').replace("with_name('recovery_policy.py')", "with_name('recovery_policy_v2.py')")
# Retain frozen original staged drafts. Integrated version waits for root's data QA.
anchor=" model=FastLanguageModel.get_peft_model(model,r=8,lora_alpha=8"
assert worker.count(anchor)==1
approval=""" approval_path=out/'pretrain_qa_approved.json'
 atomic(out/'progress.json',{'state':'WAITING_SOURCE_QA_BEFORE_OPTIMIZER','training_started':False,'step':0})
 while not approval_path.exists() and time.time()<cutoff and not STOP:time.sleep(2)
 if not approval_path.exists():raise TimeoutError('Source QA approval not provided before train cutoff')
 approval=json.loads(approval_path.read_bytes())
 if not approval.get('root_actual_source_samples_reviewed') or approval.get('human_review_claimed') is not False or approval['source_plan_sha256']!=cfg['source_plan_sha256'] or approval['renderer_sha256']!=cfg['renderer_sha256']:raise ValueError('Source QA must bind actual plan and projected renderer')
"""
worker=worker.replace(anchor,approval+'\n'+anchor)
q=p/'recovery_worker_v2.py';q.write_text(worker,encoding='utf8');compile(worker,str(q),'exec')
tests=(old/'test_recovery_policy.py').read_text(encoding='utf8').replace('from recovery_policy import','from recovery_policy_v2 import')
start=tests.index(' def test_sources_keep_all_worked_and_cap_hints(');end=tests.index(' def test_leakage_screen_numeric_variant(',start)
tests=tests[:start]+tests[end:]
# Original tests enforced primary-answer-only improvement; new owner goal explicitly includes useful hints/feedback.
start=tests.index(' def test_hint_only_gain_ineligible_below_answer_ceiling(');end=tests.index(' def test_perfect_answer_ceiling_allows_useful_hint_gain(',start)
tests=tests[:start]+""" def test_safe_hint_gain_eligible_without_math_regression(self):
  records=reviews();records[15]['adapter_pass']=True;summary=summarize_decisions(records)
  self.assertTrue(summary['candidate_eligible']);self.assertEqual(summary['strict_answer_gain'],0)
  self.assertEqual(validate_gate(gate(records,100,'CONTINUE_IMPROVED'),100,bindings(records)),'CONTINUE_IMPROVED')

"""+tests[end:]
(p/'test_recovery_policy.py').write_text(tests,encoding='utf8')
tests=(old/'test_recovery_worker.py').read_text(encoding='utf8').replace('import recovery_worker as','import recovery_worker_v2 as')
(p/'test_recovery_worker.py').write_text(tests,encoding='utf8')
result=subprocess.run([sys.executable,'-X','utf8','-m','unittest','test_balanced_plan_v2','test_behavior_renderer','test_recovery_policy','test_recovery_worker'],cwd=p,text=True,capture_output=True)
receipt={'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'code_sha256':{n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in ['recovery_worker_v2.py','recovery_policy_v2.py','behavior_renderer.py','inference_contract.py']},'eligibility_rule_changed_before_new_candidate_outputs':True,'source_targets_unchanged':True,'scope':'CPU invariants; source semantic review still separate'}
(p/'cpu_validation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(receipt,ensure_ascii=False));assert result.returncode==0
