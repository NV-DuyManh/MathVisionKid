from pathlib import Path
P=Path(__file__).parent;OLD=P.parent/'conditional_grounding_20261025'
for src,dest in [('capture_baseline_runtime.py','capture_baseline_runtime.py'),('decode_baseline_capture.py','decode_baseline_capture.py')]:
 code=(OLD/src).read_text(encoding='utf8').replace('/content/mathvisionkid_conditional_grounding_20261025','/content/mathvisionkid_recovery_20261026')
 (P/dest).write_bytes(code.encode())
code=(OLD/'capture_evaluation_runtime.py').read_text(encoding='utf8')
code=code.replace('/content/mathvisionkid_conditional_grounding_20261025','/content/mathvisionkid_recovery_20261026')
code=code.replace("'active_code_raw_verified.json',\n 'active_memory_code_raw_verified.json','training/actual_memory_resume_binding.json',\n 'training/native_resumed_microbatch_audit.json','memory_resume_migration.json'", "'active_staged_code_pins.json','root_reviewed_training_plan.json','independent_preoptimizer_review.json','training/pretrain_qa_approved.json'")
(P/'capture_evaluation_runtime.py').write_bytes(code.encode())
(P/'decode_evaluation_capture.py').write_bytes((OLD/'decode_evaluation_capture.py').read_bytes())
print('Prepared bounded output/metadata capture scripts; no corpus or model included')
