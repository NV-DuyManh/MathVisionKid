from pathlib import Path
import hashlib,base64
P=Path(__file__).parent
names=['build_quality_gate.py','paired_review_policy_pre_candidate.json','final_eval_worker.py']
payload={n:base64.b64encode((P/n).read_bytes()).decode() for n in names}
pins={n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in names}
code='''import threading
assert not globals().get('cpu_tools_publication_thread') or not cpu_tools_publication_thread.is_alive()
def cg_publish_cpu_tools(payload=PAYLOAD,pins=PINS):
 import pathlib,json,base64,hashlib,sys,traceback
 from googleapiclient.discovery import build
 from google_auth_httplib2 import AuthorizedHttp
 import httplib2
 root=pathlib.Path('/content/mathvisionkid_conditional_grounding_20261025')
 status=root/'cpu_tools_publication_status.json'
 def save(value):
  temp=status.with_suffix('.pending');temp.write_text(json.dumps(value,indent=2)+'\\n');temp.replace(status)
 api=None
 try:
  save({'state':'STAGING','training_code_modified':False})
  for name,encoded in payload.items():
   raw=base64.b64decode(encoded);assert hashlib.sha256(raw).hexdigest()==pins[name]
   dest=root/name
   if dest.exists():assert dest.read_bytes()==raw
   else:dest.write_bytes(raw)
  api=build('drive','v3',http=AuthorizedHttp(recovery_credentials,http=httplib2.Http(timeout=60)),cache_discovery=False)
  lib=sys.modules['qrec_integrity_store']
  store=conditional_publisher.parent_verified_store_class(lib)(api,parent=conditional_publisher.PARENT,folder_name=conditional_publisher.FOLDER)
  matches=store.find(conditional_publisher.PARENT,conditional_publisher.FOLDER)
  assert len(matches)==1 and matches[0]['id']=='1iP691P_pYTf-Pt_RdGpTZMnDtwjKR4ya'
  store.folder=matches[0]['id']
  proofs={n:store.put(n,root/n,immutable=True) for n in payload}
  assert all(p['fresh_raw_readback_verified'] for p in proofs.values())
  save({'state':'COMPLETE_RAW_VERIFIED','proofs':proofs,'no_gate_created':True,'no_evaluation_executed':True,'training_code_modified':False})
 except Exception as error:save({'state':'ERROR','error':repr(error),'traceback':traceback.format_exc()})
 finally:
  if api is not None:api.close()
cpu_tools_publication_thread=threading.Thread(target=cg_publish_cpu_tools,daemon=True,name='MathVisionKidCpuToolsPublication')
cpu_tools_publication_thread.start()
print({'cpu_tools_thread_started':True,'no_training_or_evaluation_started':True})
'''.replace('PAYLOAD',repr(payload)).replace('PINS',repr(pins))
compile(code,'cpu_tools_stage','exec')
(P/'publish_cpu_tools_runtime.py').write_text(code,encoding='utf8')
print(pins)
