import pathlib,json,subprocess,sys
from datetime import datetime,timezone
r=pathlib.Path('/content/mathvisionkid_quality_recovery_20261024');r.mkdir(exist_ok=True)
assert not (r/'training/run_config.json').exists(),'Inspect existing run, do not duplicate'
if not (r/'venv/bin/python').exists():subprocess.run([sys.executable,'-m','venv','--system-site-packages',str(r/'venv')],check=True,timeout=45)
if not globals().get('recovery_install_process') or recovery_install_process.poll() is not None:
 assert not (r/'install_complete.json').exists(),'Already installed; do not repeat'
 cmd=[str(r/'venv/bin/python'),'-m','pip','install','unsloth==2026.10.7','unsloth_zoo==2026.10.7','transformers==5.16.1','peft==0.21.2','bitsandbytes==0.50.2','accelerate==1.15.0']
 recovery_install_process=subprocess.Popen(cmd,stdout=(r/'install.log').open('ab'),stderr=subprocess.STDOUT)
 (r/'install_launch.json').write_text(json.dumps({'pid':recovery_install_process.pid,'command':cmd,'launched_utc':datetime.now(timezone.utc).isoformat(),'training_started':False},indent=2))
print(json.dumps({'installer_pid':recovery_install_process.pid,'installer_exit':recovery_install_process.poll(),'training_started':False}))
