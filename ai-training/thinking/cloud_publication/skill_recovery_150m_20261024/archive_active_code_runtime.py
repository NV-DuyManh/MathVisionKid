import pathlib,json,hashlib,importlib.util,sys
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024');s=json.loads((r/'publication/publication_status.json').read_bytes())
assert s['state']=='RUNNING' and s['folder_id']=='1dZE2gMavdnJsK_-VLmdFBdAxBwY10HmA'
from googleapiclient.discovery import build
from google_auth_httplib2 import AuthorizedHttp
import httplib2
api=build('drive','v3',http=AuthorizedHttp(recovery_credentials,http=httplib2.Http(timeout=60)),cache_discovery=False)
try:
 spec=importlib.util.spec_from_file_location('skill_active_code_archive_lib',r/'frozen_integrity_store.py');lib=importlib.util.module_from_spec(spec);sys.modules[spec.name]=lib;spec.loader.exec_module(lib)
 store=skill_publisher.parent_verified_store_class(lib)(api,parent=skill_publisher.PARENT,folder_name=skill_publisher.FOLDER)
 found=store.find(skill_publisher.PARENT,skill_publisher.FOLDER);assert len(found)==1 and found[0]['id']==s['folder_id'];store.folder=s['folder_id']
 names=['recovery_worker_v3.py','owner_scope_binding_v2.json','scope_repair_cpu_validation.json','metadata_serialization_repair.json','training/pretrain_qa_approved.json']
 proofs={n:store.put(n.replace('/','__'),r/n,immutable=True) for n in names}
 assert all(x['fresh_raw_readback_verified'] for x in proofs.values())
 (r/'active_code_raw_verified.json').write_text(json.dumps(proofs,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'active_code_archived':True,'proofs':proofs,'training_worker_alive':skill_training_process.poll() is None},ensure_ascii=False))
finally:api.close()
