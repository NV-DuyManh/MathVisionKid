from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,base64
import recovery_policy as P
p=Path(__file__).parent
def read(q):return json.loads(q.read_bytes())
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
d=p/'review_step_000050';gate=read(d/'root_gate.json');summary=P.summarize_decisions(gate['decisions'])
for label in ['g1_g2','g3_g4','g5']:
 review=read(d/f'semantic_{label}.json')
 assert review['input_pair_sha256']==sha(d/f'paired_{label}.json') and review['all_actual_fields_read'] and not review['human_review_claimed']
assert not summary['candidate_eligible'] and gate['decision']=='STOP'
final=p/'final_review';decisions=[]
for grade in range(1,6):
 review=read(final/f'semantic_g{grade}.json')
 assert review['all_actual_fields_read'] and not review['human_review_claimed'] and review['input_pair_sha256']==sha(final/f'paired_g{grade}.json')
 decisions+=review['decisions']
assert len(decisions)==len({x['fixture_id'] for x in decisions})==20
manifest=read(final/'final_eval__final_eval_manifest.json');complete=read(final/'training__run_complete.json')
assert manifest['complete'] and manifest['selected_kind']=='untrained_base' and manifest['test_run_count']==1 and not manifest['selection_changed']
outputs=[json.loads(x) for x in (final/'final_eval__base_generations.jsonl').read_text(encoding='utf8').splitlines()]
assert len(outputs)==20
counts={'total':{'pass':sum(x['selected_pass'] for x in decisions),'count':20},'by_mode':{},'by_grade':{},'hint_leaks':sum(x['selected_hint_leak'] for x in decisions)}
for label,key in [('by_mode','mode'),('by_grade','grade')]:
 for value in sorted({x[key] for x in decisions}):
  sub=[x for x in decisions if x[key]==value];counts[label][str(value)]={'pass':sum(x['selected_pass'] for x in sub),'count':len(sub)}
pub=read(p/'metadata_before_report/publication__publication_status.json')
audit=read(p/'forward_loss_audit.json');assert audit['complete'] and len(audit['results'])==6
test_rows=[json.loads(x) for x in (final/'locked_test_candidates.jsonl').read_text(encoding='utf8').splitlines()]
owner=[f for f in test_rows if '10034' in f['userproblem']];assert len(owner)==1
owner_id=owner[0]['id'];owner_review=next(x for x in decisions if x['fixture_id']==owner_id)
report={
 'schema':'MathVisionKid.verbal_recovery_final_semantic_assessment.v1','observed_utc':datetime.now(timezone.utc).isoformat(),
 'status':'REPRESENTATION_TRIAL_NOT_ELIGIBLE_DO_NOT_PROMOTE_ADAPTER','selected_kind':'untrained_base','new_adapter_improvement_demonstrated':False,'production_approved':False,
 'trial_scope':read(p/'trial_scope.json'),'training':complete,
 'loss_alignment_audit':{'evidence_sha256':sha(p/'forward_loss_audit.json'),'measurements':6,'max_abs_next_token_loss_error':max(x['absolute_error_next_token'] for x in audit['results']),'all_finite_and_next_token_parity':all(x['finite'] and x['causal_loss_parity_pass'] for x in audit['results']),'scope':'Three real training microbatches on fresh base and existing prior step50; forward only, no optimizer, no heldout access. Does not prove whole stack correct or establish causal root cause.'},
 'representation_change':{'renderer_sha256':sha(p/'verbal_training_renderer_v3.py'),'preflight':read(p/'projection_preflight.json'),'changed':['natural-language prompt rendering','natural-language assistant target rendering'],'unchanged_source_math_and_sampling':True,'new_human_labels_applied_to_derived_bytes':False,'causal_improvement_from_representation_proven':False,'contract_metadata_caveat':'Frozen primitive eval_contract retains an old human-readable user_serialization=json.dumps label. Actual fixture_messages was overridden with the pinned verbal renderer in both dev and final workers; actual prompt token hashes are checked before each generation. Preserve original contract bytes for audit, do not describe that old label as actual serialization.'},
 'development_validation':{'count':30,'contract_sha256':gate['contract_sha256'],'gate_sha256':sha(d/'root_gate.json'),'summary':summary,'decisions':gate['decisions'],'criteria':'Full requested task, including correct complete result, no substantive contradictory explanation, explicit required checks, useful nonleaking hints, grounded guards and student feedback. NonEOS/truncated/timeouts cannot pass. Numerical-only answer accuracy is distinct.','not_directly_comparable_to_previous_json_prompt_trial':True,'previous_locked20_not_reused':True},
 'locked_final_test':{'manifest_sha256':sha(final/'final_eval__final_eval_manifest.json'),'fixture_sha256':manifest['locked_test_sha256'],'output_sha256':manifest['files']['base_generations.jsonl']['sha256'],'test_run_count':1,'selected_before_test':True,'selected_reuses_exact_base_outputs':True,'rejected_adapter_not_tested':True,'counts':counts,'all_actual_outputs_read':True,'decisions':decisions,'completed_eos_count':sum(bool(x['ended_eos'] and not x['possibly_truncated'] and not x['timed_out']) for x in outputs),'not_used_to_retrain_or_reselect':True,'owner_requested_division':{'fixture_id':owner_id,'explicitly_known_probe_not_unseen_generalization':True,'review':owner_review}},
 'artifact_raw_readback':{'run_folder_id':pub['folder_id'],'checkpoint_proofs':pub['checkpoints'],'diagnostic_adapter':pub['final_artifacts']['last_adapter_diagnostic.zip']},
 'source_preservation':{'full_corpus_train_chats':6502344,'source_view_rows':16000,'source_view_cases':4000,'derived_sampling_rows':6625,'all4000worked_in_sampling_plan':True,'actual_unique_trained_chats':800,'actual_fraction_of_derived_view':800/6625,'source_data_or_labels_changed_or_deleted':False,'new_human_attestation':False,'previous_checkpoints_preserved':True,'corpus_or_model_downloaded_to_pc':False},
 'limitations':['Thirty reused development tasks and twenty newly authored final tasks are small; only actual16k exact/number-masked collision screening, not proven independent of full6.5M corpus.','The explicit owner10034/33 probe is known before this test and is not evidence of unseen generalization.','Semantic judgments by LLM with full actual-output reasons and row/hash binding, no new human or external certification.','Matched greedy nonthinking evaluation, not evidence of best thinking mode or global model quality.','No production approval, no image/physical observation completion or whole-curriculum/legal certification.','Representational trial changes prompts as well as targets. Compare adapter with fresh base under this contract; cross-trial raw scores alone do not isolate a cause.','A small numerical-answer gain cannot override newly leaking hints, lost checks or completion failures. Keeping the base is not a claim of a reliable finished tutor.'],
 'next_work':['Do not spend another full long run on this rejected configuration. First diagnose response length/repetition, training distribution and prompt-template behavior with broader skill-balanced development evidence.','Keep exact arithmetic checking and grounded explanation validation separate; no app or calculator changes made here.'],
 'paid_resources':False,'skills_applied':['google-drive']}
target=p/'final_semantic_assessment.json';b=(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
assert not target.exists(),'Final report is immutable; do not overwrite'
target.write_bytes(b)
code='''import pathlib,json,base64,hashlib
r=pathlib.Path('/content/mathvisionkid_verbal_recovery_20261024');b=base64.b64decode(DATA);report=json.loads(b)
assert verbal_process.poll()==verbal_final_process.poll()==0
assert hashlib.sha256((r/'final_eval/final_eval_manifest.json').read_bytes()).hexdigest()==report['locked_final_test']['manifest_sha256']
assert json.loads((r/'training/best.json').read_bytes())['kind']=='untrained_base'
assert report['training']==json.loads((r/'training/run_complete.json').read_bytes())
p=r/'training/final_semantic_assessment.json'
if p.exists():assert p.read_bytes()==b
else:
 t=p.with_suffix('.pending');t.write_bytes(b);t.replace(p)
print(json.dumps({'final_report_staged':True,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'selected_kind':report['selected_kind'],'locked_test_counts':report['locked_final_test']['counts']}))
'''.replace('DATA',repr(base64.b64encode(b).decode()))
(p/'stage_final_report_runtime.py').write_text(code,encoding='utf8')
print(json.dumps({'report_sha256':sha(target),'report_bytes':len(b),'locked_counts':counts,'dev_base':summary['base'],'dev_adapter':summary['candidate']}))
