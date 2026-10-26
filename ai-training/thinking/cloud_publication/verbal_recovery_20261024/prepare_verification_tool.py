from pathlib import Path
p=Path(__file__).parent;old=p.parent/'quality_recovery_20261024'/'verify_final_closeout.py'
code=old.read_text(encoding='utf8').replace("==162336","==169406").replace("COMPLETE_REGRESSION_REJECTED_NO_NEW_ADAPTER_PROMOTED","COMPLETE_REPRESENTATION_TRIAL_NOT_ELIGIBLE_BASE_RETAINED")
code=code.replace("'no_active_training_expected':True", "'no_active_training_expected':True,'representation_trial':True")
target=p/'verify_final_closeout.py';assert not target.exists();target.write_text(code,encoding='utf8')
print('Prepared additive final integrity verifier; no network/model I/O.')
