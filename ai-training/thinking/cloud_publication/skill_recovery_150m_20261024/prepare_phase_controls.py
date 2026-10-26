from pathlib import Path
import json,hashlib
from prepare_control_stage import build_stage
p=Path(__file__).parent;ctx=p.parents[2]/'MATH_TRAINING_CONTEXT.md'
names=['owner_run_scope.json','source_inventory.json','projection_preflight.json','locked_test_binding.json','locked_test_notes.json','curate_locked_before_training.py','behavior_renderer.py','test_behavior_renderer.py','balanced_plan_v2.py','test_balanced_plan_v2.py','inference_contract.py','calibration_review.json','audit_behavior_contract.json','recovery_worker_v3.py','recovery_policy_v2.py','source_semantic_review_g1_g3.json','source_semantic_review_g4_g5.json','scope_repair_cpu_validation.json','cpu_validation.json','prepare_scope_repair.py','screen_serialization_repair_receipt.json','source_qa_approved_receipt.json','active_code_archived_receipt.json']
evidence={'phase_preflight/'+n:str((p/n).resolve()) for n in names}
meta={'branch':'skill_recovery_150m_20261024','phase':'PREFLIGHT_AND_MATCHED_BASELINE_ACTIVE','owner_budget_seconds':9000,'deadline_utc':'2026-10-24T15:07:46Z','source_rows':16000,'derived_view_rows':6879,'source_and_old_labels_preserved':True,'new_human_attestation':False,'production_approval':False,'calibration_nonthinking_fulltask':3,'calibration_thinking_fulltask':2,'calibration_count':4,'new_training_optimizer_started_in_this_metadata':False,'source_QA_actual_samples':24,'worker_code_sha256':'a855d1c2c7bb38f1d046ce49bf1ed539037985269b469aaf1c8ab42a8fef5df2','next':'Observe actual baseline then optimizer progress; read full paired outputs at100/300, choose best includingbase and run newlocked20onceafterselection.'}
(p/'phase_run_metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
result=build_stage(ctx.read_bytes(),meta,evidence,p/'publish_phase_controls_runtime.py',process_global='skill_training_process')
print(json.dumps({k:v for k,v in result.items() if k!='source_hashes'},ensure_ascii=False))
