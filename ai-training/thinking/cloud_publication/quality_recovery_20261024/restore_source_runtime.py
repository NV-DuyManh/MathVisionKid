import pathlib,json,hashlib,gzip,subprocess,sys,os,time
from datetime import datetime,timezone
import google.auth
from googleapiclient.discovery import build
r=pathlib.Path('/content/mathvisionkid_quality_recovery_20261024')
r.mkdir(exist_ok=True)
assert not (r/'training/run_config.json').exists(),'Run already initialized; inspect existing state before any new launch'
recovery_credentials,_=google.auth.default()
recovery_drive=build('drive','v3',credentials=recovery_credentials,cache_discovery=False)
refs={
 'training_view.jsonl.gz':('1Twd75htZfKKSKvjJ4j4imAu_sca7UJ1c',3893404,'319dfddf43e1ad63878e52b1e5f34a5d276a1e557257ea7b4c33dcfe790200e9'),
 'sampling_manifest.json':('1kqDGkAEHuhgRtCQqejjfVfvGHzvEeGlr',5010290,'444db8845af0c12bb528795b7e441b996571960dd58ab6898eb9394c77031545'),
 'exhaustive_colab_loader.py':('1FFq86rhR0bBCSDK3WMKXQvDOPTbCBAUz',None,'9b1287f495e30b85085c6d8c23b2fc273e38fefbf1e730d19b0d95a9d8950a3c')}
verified={}
for name,(fid,size,sha) in refs.items():
 p=r/name
 if p.exists():b=p.read_bytes()
 else:
  meta=recovery_drive.files().get(fileId=fid,fields='id,name,size,trashed',supportsAllDrives=True).execute()
  assert meta['id']==fid and not meta.get('trashed') and int(meta['size'])<8000000
  b=recovery_drive.files().get_media(fileId=fid).execute()
 assert (size is None or len(b)==size) and hashlib.sha256(b).hexdigest()==sha,(name,'raw hash mismatch')
 if not p.exists():p.write_bytes(b)
 verified[name]={'id':fid,'bytes':len(b),'sha256':sha,'fresh_raw_readback_verified':True}
raw=gzip.decompress((r/'training_view.jsonl.gz').read_bytes())
assert len(raw)<100000000 and hashlib.sha256(raw).hexdigest()=='14929ba64e5c94d812f1fc3804c771ca8e41fa92285aed3a925282c39b1e4331'
p=r/'training_view.jsonl'
if p.exists():assert p.read_bytes()==raw
else:p.write_bytes(raw)
(r/'input_readback.json').write_text(json.dumps({'observed_utc':datetime.now(timezone.utc).isoformat(),'refs':verified,'raw_view_bytes':len(raw),'corpus_or_weights_on_PC':False},indent=2))
print(json.dumps({'state':'SOURCE_RAW_VERIFIED','input_refs':verified,'raw_view_bytes':len(raw),'training_started':False}))
