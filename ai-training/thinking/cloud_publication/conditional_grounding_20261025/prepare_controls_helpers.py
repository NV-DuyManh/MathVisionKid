from pathlib import Path
P=Path(__file__).parent;OLD=P.parent/'skill_recovery_150m_20261024'
for name in ['prepare_four_controls_runtime.py','four_controls_transaction.py','prepare_control_stage.py','test_four_controls_runtime.py']:
 text=(OLD/name).read_text(encoding='utf8')
 for old,new in [('mathvisionkid_skill_recovery_150m_20261024','mathvisionkid_conditional_grounding_20261025'),
                 ('skill_recovery_150m_20261024','conditional_grounding_20261025'),
                 ('latest_skill_recovery_branch','latest_conditional_grounding_branch'),
                 ('skill_recovery_control_publications','conditional_grounding_control_publications'),
                 ('MathVisionKidSkillRecoveryFourControls','MathVisionKidConditionalGroundingFourControls')]:
  text=text.replace(old,new)
 if name=='prepare_four_controls_runtime.py':
  text=text.replace('"training/latest.json", "training/best.json"','"training/native_first_microbatch_audit.json", "training/latest.json", "training/best.json"')
 compile(text,name,'exec')
 (P/name).write_bytes(text.encode())
print('Prepared additive same-ID controls; no Drive calls and no model effects.')
