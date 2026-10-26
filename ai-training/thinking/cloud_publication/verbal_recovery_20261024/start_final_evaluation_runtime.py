import pathlib,json,subprocess,threading,time,hashlib,importlib.util,sys,traceback
r=pathlib.Path('/content/mathvisionkid_verbal_recovery_20261024')
assert verbal_process.poll()==0,'Training worker must have completed and released GPU'
assert json.loads((r/'training/run_complete.json').read_bytes())['complete'] is True
assert not (r/'final_eval').exists(),'Final test can run only once'
assert not globals().get('verbal_final_process') or verbal_final_process.poll() is not None
assert hashlib.sha256((r/'final_evaluation_worker.py').read_bytes()).hexdigest()=='3d075d7a4f32c1f1b528fbdfafaa4f19fab9afea6578167b2733ee14cec03605'
flog=(r/'final_evaluation.log').open('ab',buffering=0)
verbal_final_process=subprocess.Popen([str(r/'venv/bin/python'),'-u',str(r/'final_evaluation_worker.py'),'--root',str(r)],stdout=flog,stderr=subprocess.STDOUT)
def publish_final_evaluation():
 status=r/'final_eval_publication_status.json'
 def save(x):
  t=status.with_suffix('.pending');t.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');t.replace(status)
 api=None
 try:
  save({'state':'WAITING_EVALUATION','pid':verbal_final_process.pid})
  code=verbal_final_process.wait(timeout=950)
  assert code==0,'Final evaluation failed; inspect original error without rerunning locked test'
  manifest=json.loads((r/'final_eval/final_eval_manifest.json').read_bytes());assert manifest['complete'] is True
  for n,proof in manifest['files'].items():
   p=r/'final_eval'/n;assert p.name==n and hashlib.sha256(p.read_bytes()).hexdigest()==proof['sha256'] and p.stat().st_size==proof['bytes'],n
  from googleapiclient.discovery import build
  from google_auth_httplib2 import AuthorizedHttp
  import httplib2
  api=build('drive','v3',http=AuthorizedHttp(recovery_credentials,http=httplib2.Http(timeout=60)),cache_discovery=False)
  assert hashlib.sha256((r/'publisher_runtime.py').read_bytes()).hexdigest()=='44df9db30c245fc701e4ff04651562c3d34f8324d0851a925ed413d148e064e0'
  spec=importlib.util.spec_from_file_location('qrec_final_publication_code',r/'publisher_runtime.py');pub=importlib.util.module_from_spec(spec);sys.modules[spec.name]=pub;spec.loader.exec_module(pub)
  assert hashlib.sha256((r/'frozen_integrity_store.py').read_bytes()).hexdigest()==pub.STORE_SHA
  spec=importlib.util.spec_from_file_location('qrec_final_frozen_store',r/'frozen_integrity_store.py');lib=importlib.util.module_from_spec(spec);sys.modules[spec.name]=lib;spec.loader.exec_module(lib)
  store=pub.parent_verified_store_class(lib)(api,parent=pub.PARENT,folder_name=pub.FOLDER)
  found=store.find(pub.PARENT,pub.FOLDER)
  assert len(found)==1 and found[0]['id']=='18kRud04F04OF34HcI2l9okHYUmzFVY4M','Existing exact run folder is required'
  store.folder=found[0]['id'];meta=store.metadata(store.folder)
  assert pub.PARENT in meta.get('parents',[]) and meta['mimeType']=='application/vnd.google-apps.folder'
  artifacts={};save({'state':'PUBLISHING','artifacts':artifacts})
  files=[r/'final_evaluation_worker.py',r/'test_final_evaluation_worker.py']+[p for p in sorted((r/'final_eval').iterdir()) if p.is_file() and not p.name.endswith('.partial.jsonl') and not p.name.endswith('.pending')]
  for p in files:
   name=str(p.relative_to(r)).replace('/','__');artifacts[name]=store.put(name,p,immutable=True);save({'state':'PUBLISHING','artifacts':artifacts})
  save({'state':'COMPLETE_RAW_VERIFIED','artifacts':artifacts,'fixture_count':20,'test_run_count':1,'selected_before_test':True,'human_review_claimed':False})
 except BaseException as e:save({'state':'ERROR','error':repr(e),'traceback':traceback.format_exc()})
 finally:
  if api is not None:api.close()
verbal_final_publisher=threading.Thread(target=publish_final_evaluation,name='MathVisionKidVerbalFinalEvalPublisher',daemon=True);verbal_final_publisher.start()
print(json.dumps({'final_evaluation_started':True,'pid':verbal_final_process.pid,'training_started':False,'locked_test_once':True,'publication_thread_started':True}))
