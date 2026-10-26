"""Restore only pinned inputs in Colab and install an isolated training env."""
import pathlib,json,hashlib,gzip,subprocess,sys,time
from datetime import datetime,timezone

r=pathlib.Path('/content/mathvisionkid_conditional_grounding_20261025')
assert not r.exists(), 'New root exists: inspect state rather than duplicate work'
assert 'recovery_credentials' in globals() and 'recovery_drive' in globals()
r.mkdir()
start=datetime(2026,10,25,2,47,40,tzinfo=timezone.utc).timestamp()
scope={'schema':'MathVisionKid.conditional_grounding_owner_scope.v1',
 'authorization':'Owner requested reconnect Hoai and continue free-T4 training to improve accuracy. Reuse most recent 2h30 maximum budget as stated before launch.',
 'budget_start_unix':start,'budget_max_wall_seconds':9000,
 'hard_deadline_unix':start+9000,'hard_deadline_utc':datetime.fromtimestamp(start+9000,timezone.utc).isoformat(),
 'reserve_seconds':1800,'paid_resources':False,'previous_adapters_loaded':False,
 'source_and_old_checkpoints_preserved':True,'new_human_attestation':False,
 'production_change':False,'corpus_or_model_download_to_pc':False,
 'model':'Qwen/Qwen3-1.7B','revision':'70d244cc86ccca08cf5af4e1e306ecf908b1ad5e',
 'notebook_id':'1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l'}
(r/'owner_run_scope.json').write_text(json.dumps(scope,indent=2)+'\n')
refs={
 'training_view.jsonl.gz':('1Twd75htZfKKSKvjJ4j4imAu_sca7UJ1c',3893404,'319dfddf43e1ad63878e52b1e5f34a5d276a1e557257ea7b4c33dcfe790200e9'),
 'sampling_manifest.json':('1kqDGkAEHuhgRtCQqejjfVfvGHzvEeGlr',5010290,'444db8845af0c12bb528795b7e441b996571960dd58ab6898eb9394c77031545'),
 'exhaustive_colab_loader.py':('1FFq86rhR0bBCSDK3WMKXQvDOPTbCBAUz',24727,'9b1287f495e30b85085c6d8c23b2fc273e38fefbf1e730d19b0d95a9d8950a3c'),
 'frozen_training_primitives.py':('1xf8CMVbtsSC4mZuMxJ0twzDnR20J0pvG',76258,'d5f4f0bc2df2b9ff8b2999d607f7ab0b773a76e2ececd4cf48bada99ffcc787c'),
 'frozen_integrity_store.py':('1ZwjnSGMXJ-aAsAMXhNsp0BuAceOxo9Kd',27124,'5f8d69f542e63bd7cc17f9a62551710c74e931d7d2c69974b0e13aaac326fb8e')}
proofs={}
for name,(fid,size,digest) in refs.items():
 meta=recovery_drive.files().get(fileId=fid,fields='id,name,size,trashed',supportsAllDrives=True).execute()
 assert meta['id']==fid and not meta.get('trashed') and int(meta['size'])==size
 raw=recovery_drive.files().get_media(fileId=fid).execute()
 assert len(raw)==size and hashlib.sha256(raw).hexdigest()==digest, name
 (r/name).write_bytes(raw)
 proofs[name]={'id':fid,'bytes':size,'sha256':digest,'fresh_raw_readback_verified':True}
raw=gzip.decompress((r/'training_view.jsonl.gz').read_bytes())
assert len(raw)<100000000 and hashlib.sha256(raw).hexdigest()=='14929ba64e5c94d812f1fc3804c771ca8e41fa92285aed3a925282c39b1e4331'
(r/'training_view.jsonl').write_bytes(raw)
(r/'input_readback.json').write_text(json.dumps({'files':proofs,'raw_view_bytes':len(raw),'corpus_or_weights_on_PC':False},indent=2)+'\n')
subprocess.run([sys.executable,'-m','venv','--system-site-packages',str(r/'venv')],check=True,timeout=90)
requirements=['unsloth==2026.10.7','unsloth_zoo==2026.10.7','transformers==5.16.1','peft==0.21.2','bitsandbytes==0.50.2','accelerate==1.15.0']
(r/'requirements-pinned.txt').write_text('\n'.join(requirements)+'\n')
install_command=[str(r/'venv/bin/python'),'-m','pip','install','--disable-pip-version-check','--report',str(r/'install_report.json'),*requirements]
conditional_install_process=subprocess.Popen(install_command,stdout=(r/'install.log').open('ab',buffering=0),stderr=subprocess.STDOUT)
(r/'install_launch.json').write_text(json.dumps({'pid':conditional_install_process.pid,'command':install_command,'started_utc':datetime.now(timezone.utc).isoformat(),'training_started':False},indent=2)+'\n')
print(json.dumps({'state':'SOURCE_RAW_VERIFIED_INSTALLING','root':str(r),'input_proofs':proofs,'install_pid':conditional_install_process.pid,'scope':scope,'training_started':False}))
