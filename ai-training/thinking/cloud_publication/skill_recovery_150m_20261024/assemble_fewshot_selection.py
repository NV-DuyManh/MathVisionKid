from pathlib import Path
import json,hashlib,base64
from base_review_notes import B
from fewshot_review_notes import F
import inference_contract as I
import final_evaluation_worker_v2 as FINAL
p=Path(__file__).parent;d=p/'fewshot_review'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def read(f):return json.loads(f.read_bytes())
def frozen(name,doc):
 f=p/name;raw=(json.dumps(doc,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
 if f.exists():assert f.read_bytes()==raw,'Do not replace reviewed decisions/selection'
 else:f.write_bytes(raw)
 return f
fixtures=[json.loads(x)for x in(p/'review_step_000100/new_validation_candidates.jsonl').read_text(encoding='utf8').splitlines()]
base=[json.loads(x)for x in(p/'review_step_000100/training__eval_step_000000__base_generations.jsonl').read_text(encoding='utf8').splitlines()]
candidate=[json.loads(x)for x in(d/'fewshot_dev__generations.jsonl').read_text(encoding='utf8').splitlines()]
assert len(fixtures)==len(base)==len(candidate)==len(B)==len(F)==30
proof=read(d/'fewshot_dev__complete.json');assert proof['complete']and proof['outputs_sha256']==sha(d/'fewshot_dev__generations.jsonl')
contract=read(d/'fewshot_dev__contract.json');assert hashlib.sha256(I.canonical(contract).encode()).hexdigest()==proof['contract_sha256']
policy=read(p/'fewshot_selection_policy.json');assert sha(p/'fewshot_selection_policy.json')==FINAL.FEWSHOT_POLICY_SHA
gate=read(p/'review_step_000100/root_gate.json');decisions=[]
for i,(f,b,c)in enumerate(zip(fixtures,base,candidate)):
 bp,bl,br=B[i];fp,fl,critical,fr=F[i]
 assert f['id']==b['fixture_id']==c['fixture_id']
 assert bp==gate['decisions'][i]['base_pass']and bl==gate['decisions'][i]['base_hint_leak']
 assert c['contract_sha256']==proof['contract_sha256']and c['seed']==b['seed']
 if fp:assert c['ended_eos']and not c['possibly_truncated']and not c['timed_out']
 decisions.append({'fixture_id':f['id'],'base_pass':bp,'fewshot_pass':fp,'base_hint_leak':bl,'fewshot_hint_leak':fl,'critical_new_error':critical,'base_reason':br,'fewshot_reason':fr})
review={'schema':'MathVisionKid.source_context_root_dev_review.v1','all_actual_fields_read':True,'human_review_claimed':False,'base_output_sha256':sha(p/'review_step_000100/training__eval_step_000000__base_generations.jsonl'),'fewshot_output_sha256':sha(d/'fewshot_dev__generations.jsonl'),'fixture_sha256':proof['fixture_sha256'],'contract_sha256':proof['contract_sha256'],'decisions':decisions}
review_path=frozen('root_fewshot_semantic_review.json',review)
eligibility={'hint_level_2':False,'hint_level_3':False};groups={}
for mode,allowed in policy['selection_groups'].items():
 rows=[(f,q)for f,q in zip(fixtures,decisions)if f['mode']in allowed]
 summary={'count':len(rows),'base_pass':sum(q['base_pass']for _,q in rows),'fewshot_pass':sum(q['fewshot_pass']for _,q in rows),'baseline_pass_regressions':sum(q['base_pass']and not q['fewshot_pass']for _,q in rows),'new_critical_errors':sum(q['critical_new_error']for _,q in rows),'new_hint_leaks':sum(q['fewshot_hint_leak']and not q['base_hint_leak']for _,q in rows),'base_answer_passes':sum(q['base_pass']for f,q in rows if f['mode']=='answer'),'fewshot_answer_passes':sum(q['fewshot_pass']for f,q in rows if f['mode']=='answer')}
 eligibility[mode]=summary['fewshot_pass']>summary['base_pass']and not summary['baseline_pass_regressions']and not summary['new_critical_errors']and not summary['new_hint_leaks']and summary['fewshot_answer_passes']>=summary['base_answer_passes']
 groups[mode]=summary
choices={m:('fewshot_contract'if eligibility[m]else'inference_contract')for m in ['worked_solution','hint_level_1','hint_level_2','hint_level_3']}
selection={'schema':'MathVisionKid.mode_context_selection.v1','base_kind':'untrained_base','dev_fixture_sha256':proof['fixture_sha256'],'baseline_output_sha256':review['base_output_sha256'],'fewshot_output_sha256':review['fewshot_output_sha256'],'fewshot_contract_sha256':proof['contract_sha256'],'bank_sha256':proof['example_bank_sha256'],'inference_module_sha256':{m:sha(p/(m+'.py'))for m in ['inference_contract','fewshot_contract']},'root_semantic_review_sha256':sha(review_path),'selection_policy_sha256':sha(p/'fewshot_selection_policy.json'),'eligible_by_model_mode':eligibility,'mode_selection':choices,'group_summaries':groups,'source_context_change_only':True,'production_approval':False,'selected_before_final_test':True}
selection_path=frozen('fewshot_selection.json',selection)
chosen=[q['fewshot_pass']if choices[I.MODE_MAP[f['mode']]]=='fewshot_contract'else q['base_pass']for f,q in zip(fixtures,decisions)]
print(json.dumps({'selection_sha256':sha(selection_path),'review_sha256':sha(review_path),'mode_selection':choices,'group_summaries':groups,'base_total':sum(q['base_pass']for q in decisions),'all_fewshot_total':sum(q['fewshot_pass']for q in decisions),'selected_total':sum(chosen),'fixture_count':30,'no_new_weights_selected':True},ensure_ascii=False))
