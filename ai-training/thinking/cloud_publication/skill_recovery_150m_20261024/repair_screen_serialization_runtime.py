import pathlib,json,hashlib,importlib.util,sys,time
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024');s=json.loads((r/'publication/publication_status.json').read_bytes())
assert s['state']=='ERROR' and not skill_publisher.publisher_thread.is_alive()
q=r/'dev_train_screening.json';current=q.read_bytes();value=json.loads(current)
assert set(value)=={'fixtures','training_rows_screened','collisions','scope'} and value['fixtures']==30 and value['training_rows_screened']==16000 and not value['collisions']
original=(json.dumps({k:value[k] for k in ['fixtures','training_rows_screened','collisions','scope']},ensure_ascii=False,indent=2)+'\n').encode()
pin=s['artifacts']['dev_train_screening.json'];assert hashlib.sha256(original).hexdigest()==pin['sha256'] and len(original)==pin['bytes']
from googleapiclient.discovery import build
from google_auth_httplib2 import AuthorizedHttp
import httplib2
api=build('drive','v3',http=AuthorizedHttp(recovery_credentials,http=httplib2.Http(timeout=60)),cache_discovery=False)
try:
 spec=importlib.util.spec_from_file_location('skill_serialization_repair_store',r/'frozen_integrity_store.py');lib=importlib.util.module_from_spec(spec);sys.modules[spec.name]=lib;spec.loader.exec_module(lib)
 store=skill_publisher.parent_verified_store_class(lib)(api,parent=skill_publisher.PARENT,folder_name=skill_publisher.FOLDER);store.folder=s['folder_id']
 fresh=store.raw_proof(pin['id'],pin['sha256'],pin['bytes'])
 assert fresh['fresh_raw_readback_verified']
 h=r/'error_history/screen_serialization_only';h.mkdir(exist_ok=False,parents=True)
 (h/'sorted_worker_screen.json').write_bytes(current);(h/'publisher_error.json').write_bytes((r/'publication/publication_status.json').read_bytes())
 assert json.loads(original)==json.loads(current)
 q.write_bytes(original)
 report={'repair':'Restore exact original immutable metadata serialization after semantic-equivalent sort_keys rewrite.','file':'dev_train_screening.json','current_semantics_equal_original':True,'source_data_model_and_training_worker_unchanged':True,'original_published_sha256':pin['sha256'],'retained_sorted_version_sha256':hashlib.sha256(current).hexdigest(),'fresh_original_drive_readback':fresh,'repaired_unix':time.time()}
 (r/'metadata_serialization_repair.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'metadata_serialization_restored':True,'original_drive_sha_verified':True,'source_or_weights_changed':False,'training_worker_alive':skill_training_process.poll() is None}))
finally:api.close()
print(json.dumps(skill_publisher.start(recovery_credentials,r)))
