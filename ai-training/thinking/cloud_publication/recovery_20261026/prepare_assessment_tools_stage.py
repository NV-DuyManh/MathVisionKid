from pathlib import Path
P=Path(__file__).parent;OLD=P.parent/'conditional_grounding_20261025'
code=(OLD/'prepare_cpu_tools_stage.py').read_text(encoding='utf8')
code=code.replace("names=['build_quality_gate.py','paired_review_policy_pre_candidate.json','final_eval_worker.py']", "names=['build_final_assessment_20261026.py','independent_preoptimizer_review.json','screening_repair_receipt.json']")
code=code.replace('/content/mathvisionkid_conditional_grounding_20261025','/content/mathvisionkid_recovery_20261026').replace("'1iP691P_pYTf-Pt_RdGpTZMnDtwjKR4ya'","'10drqDBNTGy60JBIUqanc9fFHFopCUivq'")
code=code.replace("cpu_tools_publication_status.json","assessment_tools_publication_status.json").replace("cpu_tools_publication_thread","assessment_tools_publication_thread").replace("publish_cpu_tools_runtime.py","publish_assessment_tools_runtime.py")
exec(compile(code,str(P/'prepare_assessment_tools_stage.py'),'exec'),{'__file__':str(P/'prepare_assessment_tools_stage.py')})
