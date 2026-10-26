import pathlib,subprocess,sys,json,datetime
r=pathlib.Path('/content/mathvisionkid_conditional_grounding_20261025')
assert (r/'input_readback.json').is_file()
assert not (r/'install_launch.json').exists() and not (r/'training/run_config.json').exists()
subprocess.run([sys.executable,'-m','venv','--without-pip','--system-site-packages',str(r/'venv')],check=True,timeout=90)
requirements=['unsloth==2026.10.7','unsloth_zoo==2026.10.7','transformers==5.16.1','peft==0.21.2','bitsandbytes==0.50.2','accelerate==1.15.0']
(r/'requirements-pinned.txt').write_text('\n'.join(requirements)+'\n')
cmd=[str(r/'venv/bin/python'),'-m','pip','install','--disable-pip-version-check','--report',str(r/'install_report.json'),*requirements]
conditional_install_process=subprocess.Popen(cmd,stdout=(r/'install.log').open('ab',buffering=0),stderr=subprocess.STDOUT)
proof={'pid':conditional_install_process.pid,'command':cmd,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'repair_reason':'Fresh Colab base lacks ensurepip. Isolated venv uses inherited pip; base environment not reinstalled.',
 'training_started':False}
(r/'install_launch.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof))
