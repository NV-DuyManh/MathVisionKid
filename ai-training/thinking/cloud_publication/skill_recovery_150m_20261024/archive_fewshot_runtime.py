import pathlib,json,hashlib,importlib.util,sys,threading,traceback
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024')
assert not globals().get('skill_context_archive_thread') or not skill_context_archive_thread.is_alive()
def _archive_skill_context():
 from googleapiclient.discovery import build
 from google_auth_httplib2 import AuthorizedHttp
 import httplib2
 api=build('drive','v3',http=AuthorizedHttp(recovery_credentials,http=httplib2.Http(timeout=60)),cache_discovery=False)
 status=r/'fewshot_code_publication_status.json'
 try:
  spec=importlib.util.spec_from_file_location('skill_context_archive_lib',r/'frozen_integrity_store.py');lib=importlib.util.module_from_spec(spec);sys.modules[spec.name]=lib;spec.loader.exec_module(lib)
  store=skill_publisher.parent_verified_store_class(lib)(api,parent=skill_publisher.PARENT,folder_name=skill_publisher.FOLDER)
  found=store.find(skill_publisher.PARENT,skill_publisher.FOLDER);assert len(found)==1 and found[0]['id']=='1dZE2gMavdnJsK_-VLmdFBdAxBwY10HmA';store.folder=found[0]['id']
  names=list(json.loads((r/'fewshot_launch_pins.json').read_bytes())['files'])+['fewshot_launch_pins.json']
  proofs={}
  for n in names:
   proofs[n]=store.put(n.replace('/','__'),r/n,immutable=True)
   status.write_text(json.dumps({'state':'ARCHIVING','completed':len(proofs),'count':len(names)},indent=2)+'\n')
  assert all(x['fresh_raw_readback_verified'] for x in proofs.values())
  status.write_text(json.dumps({'state':'COMPLETE_RAW_VERIFIED','proofs':proofs},indent=2)+'\n')
 except Exception as e:status.write_text(json.dumps({'state':'ERROR','error':repr(e),'traceback':traceback.format_exc()},indent=2)+'\n')
 finally:api.close()
skill_context_archive_thread=threading.Thread(target=_archive_skill_context,name='SkillContextArchive',daemon=True)
skill_context_archive_thread.start()
print(json.dumps({'context_archive_thread_started':True,'train_process_changed':False}))
