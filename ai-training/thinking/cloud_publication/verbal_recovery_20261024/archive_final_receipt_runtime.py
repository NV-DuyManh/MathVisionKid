import pathlib,json,hashlib,importlib.util,sys
from datetime import datetime,timezone
r=pathlib.Path('/content/mathvisionkid_verbal_recovery_20261024')
assert verbal_process.poll()==verbal_final_process.poll()==0
assert not recovery_controls_thread.is_alive()
controls=json.loads((r/'four_controls_publication_status.json').read_bytes())
assert controls['state']=='COMPLETE_RAW_VERIFIED'
receipt=json.loads((r/'four_controls_verified_manifest.json').read_bytes())
assert controls['receipt']==receipt
ids={'progress':'1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX','chat':'1tkSQoAlxXXRUg2AwYfvqsFKVEmM_LmR6','context':'13gdIPQTFKcekoQQtgo0TXc7RgeadzIN9','state':'1TLoQIbrRVmgsg-2uiUujCfM3HrK62Yme'}
assert [x['kind'] for x in receipt['verified_writes']]==['progress','chat','context','state']
assert all(x['id']==ids[x['kind']] and x['fresh_raw_readback_verified'] and x['sha256']==receipt['prepared_hashes'][x['kind']] for x in receipt['verified_writes'])
pub=json.loads((r/'publication/publication_status.json').read_bytes())
fe=json.loads((r/'final_eval_publication_status.json').read_bytes())
assert pub['state']==fe['state']=='COMPLETE_RAW_VERIFIED'
assert all(x['fresh_raw_readback_verified'] for x in fe['artifacts'].values())
rh=hashlib.sha256((r/'training/final_semantic_assessment.json').read_bytes()).hexdigest()
assert rh=='445586a3e8ed7fc82563b4408108d59ddf7e6b8263eda34dca9083e3ca4a3f54'
assert pub['artifacts']['training/final_semantic_assessment.json']['sha256']==rh
payload={'schema':'MathVisionKid.verbal_recovery_final_archive_receipt.v1','four_controls':receipt,'report_proof':pub['artifacts']['training/final_semantic_assessment.json'],'run_publication_finalized':pub['publication_finalized'],'final_evaluation_raw_verified_files':fe['artifacts'],'actual_training_updates':50,'actual_unique_chat_exposures':800,'supervised_tokens':169406,'selected_kind':'untrained_base','new_adapter_promoted':False,'source_data_or_labels_modified':False}
b=(json.dumps(payload,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode();p=r/'publication/final_controls_raw_verified_receipt.json'
if p.exists():assert p.read_bytes()==b
else:p.write_bytes(b)
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
assert hashlib.sha256((r/'publisher_runtime.py').read_bytes()).hexdigest()=='44df9db30c245fc701e4ff04651562c3d34f8324d0851a925ed413d148e064e0'
mod=load(r/'publisher_runtime.py','verbal_archive_publisher')
assert hashlib.sha256((r/'frozen_integrity_store.py').read_bytes()).hexdigest()==mod.STORE_SHA
lib=load(r/'frozen_integrity_store.py','verbal_archive_store')
from googleapiclient.discovery import build
from google_auth_httplib2 import AuthorizedHttp
import httplib2
api=build('drive','v3',http=AuthorizedHttp(recovery_credentials,http=httplib2.Http(timeout=60)),cache_discovery=False)
try:
 store=mod.parent_verified_store_class(lib)(api,parent=mod.PARENT,folder_name=mod.FOLDER)
 found=store.find(mod.PARENT,mod.FOLDER)
 assert len(found)==1 and found[0]['id']=='18kRud04F04OF34HcI2l9okHYUmzFVY4M'
 store.folder=found[0]['id'];meta=store.metadata(store.folder)
 assert mod.PARENT in meta.get('parents',[]) and meta['mimeType']=='application/vnd.google-apps.folder'
 proof=store.put('final_controls_raw_verified_receipt.json',p,immutable=True)
 assert proof['fresh_raw_readback_verified'] and proof['sha256']==hashlib.sha256(b).hexdigest()
 out={'verified_utc':datetime.now(timezone.utc).isoformat(),'archive_receipt_proof':proof,'all_four_controls_raw_verified':True,'training_alive':False,'final_evaluation_alive':False}
 (r/'final_archive_receipt_proof.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(out,ensure_ascii=False))
finally:api.close()
