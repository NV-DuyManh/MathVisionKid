from pathlib import Path
import json,hashlib
from prepare_control_stage import build_stage
p=Path(__file__).parent;meta=p/'metadata_final_verified'
def read(q):return json.loads(q.read_bytes())
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
publication=read(meta/'publication__publication_status.json');release=read(meta/'final_release_publication.json')
assert publication['state']=='COMPLETE_RAW_VERIFIED'and publication['publication_finalized']
assert publication['final_semantic_assessment_proof']['sha256']==sha(p/'final_semantic_assessment.json')
assert release['state']=='COMPLETE_RAW_VERIFIED'and release['bundle']['fresh_raw_readback_verified']
run_metadata={'schema':'MathVisionKid.skill_recovery_final_control_metadata.v1','phase':'COMPLETED_NO_ELIGIBLE_MODEL_UPGRADE','all_experiment_workers_exited':True,'source_and_corpus_preserved':True,'new_data_cases':0,'new_train_chats':0,'actually_trained_existing_chats':1600,'successful_optimizer_updates':100,'supervised_tokens':178939,'whole6502344_epoch_completed':False,'adapter_promoted':False,'production_approved':False,'sft_dev_base_fulltask':15,'sft_dev_candidate_fulltask':17,'dev_fixture_count':30,'context_final20_base':11,'context_final20_selected':11,'native_dev_base':8,'native_dev_candidate':10,'native_dev_fixture_count':15,'native_new15_test_not_run_due_failed_dev_gate':True,'selected_weight_kind':'untrained_pinned_base','report':publication['final_semantic_assessment_proof'],'audit_bundle':release['bundle'],'raw_readback_publication_finalized':True,'fresh_worker_observation_receipt_sha256':sha(p/'release_status2.json'),'skills_applied':['google-drive:google-drive']}
(p/'final_run_metadata.json').write_text(json.dumps(run_metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
names=['final_semantic_assessment.json','context_trial_final_review.json','native_probe_gate.json','native_dev_review_notes.py','fewshot_selection.json','fewshot_selection_policy.json','native_probe_scope.json','native_probe_selection_policy.json','native_locked15_root_review.json','behavior_renderer.py','recovery_worker_v3.py','recovery_policy_v2.py','inference_contract.py','fewshot_contract.py','selected_inference_runtime.py','native_thinking_probe.py']
evidence={'final_control_evidence/'+n:p/n for n in names}
for n in ['final_release_publication.json','completion_evidence_publication_status.json','native_evidence_publication_status.json']:
 evidence['final_control_evidence/'+n]=meta/n
result=build_stage((p.parents[2]/'MATH_TRAINING_CONTEXT.md').read_bytes(),run_metadata,evidence,p/'publish_final_controls_runtime.py',runtime_root='/content/mathvisionkid_skill_recovery_150m_20261024',credentials_global='recovery_credentials',process_global='skill_training_process',min_request_interval=1.25)
(p/'final_control_stage_pins.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in result.items()if k!='source_hashes'},ensure_ascii=False))
