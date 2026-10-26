from pathlib import Path
import subprocess,sys,json
p=Path(__file__).parent;old=p.parent/'quality_recovery_20261024'
for n in ['prepare_four_controls_runtime.py','four_controls_transaction.py','prepare_control_stage.py','test_four_controls_runtime.py']:
 s=(old/n).read_text(encoding='utf8').replace('quality_recovery_20261024','verbal_recovery_20261024').replace('latest_quality_recovery_branch','latest_verbal_recovery_branch').replace('quality_recovery_control_publications','verbal_recovery_control_publications').replace('MathVisionKidQualityRecoveryFourControls','MathVisionKidVerbalRecoveryFourControls')
 compile(s,n,'exec');(p/n).write_text(s,encoding='utf8')
r=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(p),'-p','test_four_controls_runtime.py'],capture_output=True,text=True);print(r.stderr);assert r.returncode==0
