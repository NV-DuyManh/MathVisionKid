from pathlib import Path
P=Path(__file__).parent;old=P.parent/'conditional_grounding_20261025/prepare_cpu_tools_stage.py'
code=old.read_text(encoding='utf8').replace("names=['build_quality_gate.py','paired_review_policy_pre_candidate.json','final_eval_worker.py']", "names=['build_quality_gate_20261026.py','paired_review_policy_pre_candidate.json','baseline_semantic_review_frozen.json','baseline_content_comparison.json','final_eval_worker_20261026.py']")
code=code.replace('/content/mathvisionkid_conditional_grounding_20261025','/content/mathvisionkid_recovery_20261026').replace("'1iP691P_pYTf-Pt_RdGpTZMnDtwjKR4ya'","'10drqDBNTGy60JBIUqanc9fFHFopCUivq'")
exec(compile(code,str(P/'prepare_cpu_tools_stage.py'),'exec'),{'__file__':str(P/'prepare_cpu_tools_stage.py')})
