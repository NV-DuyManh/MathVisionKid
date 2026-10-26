from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import json,hashlib,base64
import recovery_policy as P
p=Path(__file__).parent
def read(x):return json.loads(x.read_bytes())
def sha(x):return hashlib.sha256(x.read_bytes()).hexdigest()
dev=[]
for step in [1,50]:
 d=p/f'review_step_{step:06d}';gate=read(d/'root_gate.json');summary=P.summarize_decisions(gate['decisions'])
 for label in ['g1_g2','g3_g4','g5']:
  review=read(d/f'semantic_{label}.json');assert review['input_pair_sha256']==sha(d/f'paired_{label}.json') and review['human_review_claimed'] is False
 dev.append({'checkpoint_step':step,'review_gate_sha256':sha(d/'root_gate.json'),'bindings':{k:gate[k] for k in P.GATE_HASH_FIELDS},'summary':summary,'decisions':gate['decisions']})
assert dev[0]['summary']['base']==dev[0]['summary']['candidate']==dev[1]['summary']['base']
assert not any(x['summary']['candidate_eligible'] for x in dev)
final=p/'final_review';decisions=[]
for grade in range(1,6):
 d=read(final/f'semantic_g{grade}.json');assert d['all_actual_fields_read'] and not d['human_review_claimed'] and d['input_pair_sha256']==sha(final/f'paired_g{grade}.json')
 decisions+=d['decisions']
assert len(decisions)==len({x['fixture_id'] for x in decisions})==20
manifest=read(final/'final_eval__final_eval_manifest.json');complete=read(final/'training__run_complete.json')
assert manifest['complete'] is True and manifest['selected_kind']=='untrained_base' and manifest['test_run_count']==1 and manifest['selection_changed'] is False
counts={'total':{'pass':sum(x['selected_pass'] for x in decisions),'count':20},'by_mode':{},'by_grade':{},'hint_leaks':sum(x['selected_hint_leak'] for x in decisions)}
for mode in sorted({x['mode'] for x in decisions}):
 subset=[x for x in decisions if x['mode']==mode];counts['by_mode'][mode]={'pass':sum(x['selected_pass'] for x in subset),'count':len(subset)}
for grade in range(1,6):
 subset=[x for x in decisions if x['grade']==grade];counts['by_grade'][str(grade)]={'pass':sum(x['selected_pass'] for x in subset),'count':len(subset)}
pub=read(p/'metadata_before_report/publication__publication_status.json')
report={'schema':'MathVisionKid.quality_recovery_final_semantic_assessment.v1','observed_utc':datetime.now(timezone.utc).isoformat(),
 'status':'REGRESSION_AT_STEP50_DO_NOT_PROMOTE_ADAPTER','selected_kind':'untrained_base','new_adapter_improvement_demonstrated':False,'production_approved':False,
 'training':complete,'proposal_comparison':read(p/'run_metadata.json')['proposal_comparison'],
 'development_validation':{'count':30,'criteria':'Full requested task: correct result, no contradictory substantive reasoning, completed EOS; hint useful and nonleaking; guard/student feedback grounded in supplied information. Numerical-only accuracy is a different metric. Minor optional rubric details handled consistently with frozen first-review reasons.','checkpoints':dev,'base_judgments_frozen':True},
 'locked_final_test':{'manifest_sha256':sha(final/'final_eval__final_eval_manifest.json'),'output_sha256':manifest['files']['base_generations.jsonl']['sha256'],'fixture_sha256':manifest['locked_test_sha256'],'test_run_count':1,'selected_before_test':True,'selected_reuses_exact_base_outputs':True,'rejected_step50_adapter_not_run_on_locked_test':True,'counts':counts,'all_actual_outputs_read':True,'decisions':decisions,'all20_completed_eos_no_timeout_or_truncation':True,'not_used_to_retrain_or_reselect':True},
 'artifact_raw_readback':{'run_folder_id':pub['folder_id'],'checkpoint_proofs':pub['checkpoints'],'diagnostic_adapter':pub['final_artifacts']['last_adapter_diagnostic.zip']},
 'source_preservation':{'full_corpus_train_chats':6502344,'source_view_rows':16000,'source_view_cases':4000,'derived_sampling_rows':6625,'all4000_worked_solutions_retained_in_sampling_plan':True,'actual_trained_unique_chats':800,'actual_trained_fraction_of_derived_view':800/6625,'source_data_or_labels_modified_or_deleted':False,'new_human_signoff_or_credential':False,'previous_checkpoints_preserved':True,'corpus_or_model_downloaded_to_pc':False},
 'limitations':['Small authored dev30 and locked20; screened only against actual16k text, not proven independent of full6.5M corpus.','Semantic assessment by LLM with recorded full-output reasons, not new human or independent external certification.','Greedy nonthinking matched evaluation protocol; no demonstrated global best decoding or thinking quality.','No improvement on selected base; preserving base does not mean production-ready math tutor.','No image/physical observation completion or whole-curriculum/legal certification.','Observed echo/repetition and response-style drift by50updates, while CP1 tiesbase. Cause not isolated; not proof source mathematics is wrong or one hyperparameter caused it.'],
 'recommended_next_work':['Before another long run, audit actual training target/schema alignment and preservation of solution behavior on a larger locked skill-balanced set.','Use bounded comparative pilots with base included and actual-output review; do not increase epochs to fix observed regressions.','For dependable arithmetic in product, separately validate exact computation and grounded explanations; no live app changes made here.'],
 'paid_resources':False,'skills_applied':['google-drive','computer-use']}
target=p/'final_semantic_assessment.json';b=(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode();target.write_bytes(b)
code='''import pathlib,json,base64,hashlib
r=pathlib.Path('/content/mathvisionkid_quality_recovery_20261024');b=base64.b64decode(DATA);report=json.loads(b)
assert recovery_process.poll()==0 and recovery_probe_process.poll()==0 and recovery_final_process.poll()==0
assert hashlib.sha256((r/'final_eval/final_eval_manifest.json').read_bytes()).hexdigest()==report['locked_final_test']['manifest_sha256']
assert json.loads((r/'training/best.json').read_bytes())['kind']=='untrained_base'
assert report['training']==json.loads((r/'training/run_complete.json').read_bytes())
p=r/'training/final_semantic_assessment.json'
if p.exists():assert p.read_bytes()==b
else:
 t=p.with_suffix('.pending');t.write_bytes(b);t.replace(p)
print(json.dumps({'final_report_staged':True,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'selected_kind':report['selected_kind'],'train_steps':report['training']['metrics']['step'],'locked_test_counts':report['locked_final_test']['counts']}))
'''.replace('DATA',repr(base64.b64encode(b).decode()))
(p/'stage_final_report_runtime.py').write_text(code,encoding='utf8')
print(json.dumps({'report_sha256':sha(target),'report_bytes':len(b),'locked_counts':counts,'dev_base':dev[1]['summary']['base']['total'],'dev_step50':dev[1]['summary']['candidate']['total']}))
