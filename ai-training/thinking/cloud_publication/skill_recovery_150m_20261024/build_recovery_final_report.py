from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,base64
import recovery_policy_v2 as P
p=Path(__file__).parent
def read(q):return json.loads(q.read_bytes())
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
meta=p/'metadata_before_final_report';pub=read(meta/'publication__publication_status.json');native=read(p/'native_probe_gate.json')
assert not native['candidate_eligible'],'This final report path assumes native candidate not eligible; review implementation if selection differs.'
complete=read(meta/'training__run_complete.json');sft=read(p/'review_step_000100/root_gate.json');sft_summary=P.summarize_decisions(sft['decisions'])
context=read(p/'context_trial_final_review.json');context_dev=read(p/'fewshot_selection.json')
assert sft['decision']=='STOP'and not sft_summary['candidate_eligible']
assert pub['folder_id']=='1dZE2gMavdnJsK_-VLmdFBdAxBwY10HmA'and len(pub['checkpoints'])==2
archive=read(meta/'completion_evidence_publication_status.json');native_archive=read(meta/'native_evidence_publication_status.json')
assert archive['state']=='COMPLETE_RAW_VERIFIED'and native_archive['state']=='DEV_COMPLETE_RAW_VERIFIED'
assert all(x['fresh_raw_readback_verified']for x in archive['proofs'].values())
assert all(x['fresh_raw_readback_verified']for x in native_archive['proofs'].values())
report={
 'schema':'MathVisionKid.skill_recovery_150m_final_semantic_assessment.v1',
 'observed_utc':datetime.now(timezone.utc).isoformat(),'status':'TRIALS_COMPLETE_NO_ELIGIBLE_ADAPTER_OR_GENERAL_REASONING_UPGRADE',
 'selected_weight_artifact':'untrained_pinned_base','adapter_promoted':False,'production_approved':False,
 'owner_scope':read(p/'owner_run_scope.json'),
 'training':complete,
 'sft_development':{'full_task_summary':sft_summary,'decisions':sft['decisions'],'gate_sha256':sha(p/'review_step_000100/root_gate.json'),'all_actual_fields_read':True,'human_review_claimed':False,'candidate_rejected_despite_answer_gain':True},
 'source_context_trial':{'dev_selection':context_dev,'dev_baseline_full_task':15,'dev_all_fewshot_full_task':19,'dev_mode_selected_full_task':17,'dev_count':30,'one_time_new20':context,'selected_context_is_not_a_weight_training_gain':True,'production_approved':False,'no_change_to_old_final_selection_from_this_result':True},
 'native_thinking_probe':{'gate':native,'dev_complete':read(p/'native_review/native_probe__dev__complete.json'),'protocol':read(p/'native_review/native_probe__dev__contract.json'),'raw_reasoning_downloaded_to_pc':False,'raw_reasoning_used_as_training_data':False,'new15_final_performed':False,'new15_final_skipped_reason':'Candidate failed frozen development eligibility; no additional heldout inference or training.','new15_sealed_sha256':sha(p/'native_locked15.jsonl'),'new15_screen':read(p/'native_review/native_locked15_train_screening.json'),'does_not_reselect_original_context_trial':True},
 'diagnosis_observed':[
  'SFT repaired three requested-answer tasks but introduced wrong calendar and subtraction guidance; exact result alone is insufficient.',
  'Mode-specific source demonstrations suppressed hint answer leaks on final20but did not improve full-task score and introduced new or unhelpful guidance.',
  'Native thinking changes inference behavior and cost on unchanged base weights; a correct product may still use quantities from the wrong real-world grouping.',
  'These experiments do not establish a unique causal reason for the remaining model errors.'
 ],
 'raw_drive_evidence':{'run_folder_id':pub['folder_id'],'checkpoint_proofs':pub['checkpoints'],'diagnostic_adapter_proofs':pub.get('final_artifacts',{}),'code_and_context_final_proofs':archive['proofs'],'native_dev_code_scope_and_raw_proofs':native_archive['proofs']},
 'source_preservation':{'full_corpus_train_chats':6502344,'source_view_chats':16000,'source_view_cases':4000,'derived_training_view_rows':6879,'actually_trained_unique_chats':1600,'actually_supervised_tokens':178939,'successful_optimizer_updates':100,'optimizer_seconds':complete['training_seconds'],'derived_view_fraction':1600/6879,'full6502344_epoch_completed':False,'data_deleted_or_source_labels_changed':False,'new_human_attestation_created':False,'all_older_models_checkpoints_and_sources_preserved':True,'corpus_or_model_downloaded_to_pc':False},
 'verification':{'source_semantic_sample_review':24,'sft_cpu_tests_passed':33,'four_controls_cpu_tests_passed':11,'fewshot_contract_tests_passed':7,'source_example_bank_tests_passed':5,'final_evaluator_tests_passed':7,'selected_inference_helper_tests_passed':9,'native_probe_tests_passed':9,'new15_exact_checks_passed':13,'parser_or_hash_pass_is_not_semantic_proof':True},
 'limitations':[
  'Small reused development sets and20new final tasks; exact/number-masked screening of actual16kview only, not proven independent of the full6.5M corpus.',
  'Full-task grading requires sound explanation, requested checks, grounded feedback/guards and useful nonleaking hints; numerical-only answer accuracy is a different metric.',
  'Semantic reviews are model-assisted root judgments with actual-output reasons and hash bindings, not newly verified human or independent external certification.',
  'The frozen F helper nested completion proof carries locked_test_accessed=false even when its labeled selected-final stage used locked fixtures. The authoritative final evaluator complete.json records the actual once-only locked use; original helper bytes/proofs are preserved, not rewritten.',
  'No proof of100percent correctness, whole-curriculum coverage, image/physical observation readiness, legal2026certification, or product acceptance.',
  'The candidate adapters are retained for diagnosis; keeping the base does not claim the base is a finished reliable tutor.'
 ],
 'next_concrete_work':[
  'Use exact independent arithmetic verification and explicit grounding checks before accepting or serving a generated solution; keep them separate from loss and answer matching.',
  'Curate diverse skill and behavior demonstrations with clear quantities, units and checks before another long SFT run; do not increase epochs merely because a trial regressed.',
  'Resume only from an explicitly chosen saved experiment and new authorized budget; no training worker is left running by this completed phase.'
 ],
 'paid_resources':False,'app_or_production_modified':False,'skills_applied':['google-drive:google-drive']}
target=p/'final_semantic_assessment.json';raw=(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
if target.exists():assert target.read_bytes()==raw
else:target.write_bytes(raw)
code="""import pathlib,json,base64,hashlib
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024');b=base64.b64decode(DATA);doc=json.loads(b)
assert skill_training_process.poll()==skill_fewshot_process.poll()==skill_final_process.poll()==skill_native_dev_process.poll()==0
assert not globals().get('skill_native_final_process'),'Native final must remain unrun after failed dev gate'
assert doc['training']==json.loads((r/'training/run_complete.json').read_bytes())
assert json.loads((r/'training/best.json').read_bytes())['kind']=='untrained_base'
assert not doc['native_thinking_probe']['gate']['candidate_eligible']
p=r/'training/final_semantic_assessment.json'
if p.exists():assert p.read_bytes()==b
else:p.write_bytes(b)
print(json.dumps({'final_report_staged':True,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'production_approved':False,'all_gpu_workers_exited':True}))
""".replace('DATA',repr(base64.b64encode(raw).decode()))
(p/'stage_final_report_runtime.py').write_text(code,encoding='utf8')
print(json.dumps({'report_sha256':sha(target),'report_bytes':len(raw),'training_chat_count':1600,'sft_dev':{'base':sft_summary['base']['total'],'candidate':sft_summary['candidate']['total']},'context_final20':{'base':context['base']['passed'],'selected':context['selected']['passed']},'native_dev':native['summary']}))
