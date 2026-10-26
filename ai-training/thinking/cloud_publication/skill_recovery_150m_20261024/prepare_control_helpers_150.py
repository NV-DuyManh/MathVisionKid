from pathlib import Path
p=Path(__file__).parent;old=p.parent/'verbal_recovery_20261024'
for name in ['prepare_four_controls_runtime.py','four_controls_transaction.py','prepare_control_stage.py','test_four_controls_runtime.py']:
 text=(old/name).read_text(encoding='utf8').replace('mathvisionkid_verbal_recovery_20261024','mathvisionkid_skill_recovery_150m_20261024').replace('verbal_recovery_20261024','skill_recovery_150m_20261024').replace('latest_verbal_recovery_branch','latest_skill_recovery_branch').replace('verbal_recovery_control_publications','skill_recovery_control_publications').replace('MathVisionKidVerbalRecoveryFourControls','MathVisionKidSkillRecoveryFourControls')
 if name=='prepare_four_controls_runtime.py':
  text=text.replace('"owner_run_scope.json", "training/run_config.json"','"owner_run_scope.json", "owner_scope_binding_v2.json", "active_code_raw_verified.json", "metadata_serialization_repair.json", "training/run_config.json"')
 q=p/name;assert not q.exists();q.write_text(text,encoding='utf8')
print('Prepared same-ID additive controls for new owner150minute scope; no network calls.')
