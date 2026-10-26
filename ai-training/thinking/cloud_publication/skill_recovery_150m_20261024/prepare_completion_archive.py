from pathlib import Path
import json,base64,hashlib
p=Path(__file__).parent
assets={'selected_inference_runtime.py':p/'selected_inference_runtime.py','test_selected_inference_runtime.py':p/'test_selected_inference_runtime.py','base_review_notes.py':p/'base_review_notes.py','candidate_review_notes.py':p/'candidate_review_notes.py','fewshot_review_notes.py':p/'fewshot_review_notes.py'}
for group in ['g1_g2','g3_g4','g5']:assets[f'root_review_dev100_{group}.json']=p/f'review_step_000100/semantic_{group}.json'
payload={n:base64.b64encode(f.read_bytes()).decode()for n,f in assets.items()}
pins={n:hashlib.sha256(f.read_bytes()).hexdigest()for n,f in assets.items()}
code="""import pathlib,json,hashlib,base64,threading,traceback,importlib.util,sys,time
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024');payload=PAYLOAD;pins=PINS
assert not globals().get('skill_completion_archive_thread') or not skill_completion_archive_thread.is_alive()
for n,v in payload.items():
 b=base64.b64decode(v);assert hashlib.sha256(b).hexdigest()==pins[n]
 if(r/n).exists():assert(r/n).read_bytes()==b
 else:(r/n).write_bytes(b)
def _archive_skill_completion():
 from googleapiclient.discovery import build
 from google_auth_httplib2 import AuthorizedHttp
 import httplib2
 api=build('drive','v3',http=AuthorizedHttp(recovery_credentials,http=httplib2.Http(timeout=60)),cache_discovery=False)
 status=r/'completion_evidence_publication_status.json';proofs={}
 try:
  spec=importlib.util.spec_from_file_location('skill_completion_archive_lib',r/'frozen_integrity_store.py');lib=importlib.util.module_from_spec(spec);sys.modules[spec.name]=lib;spec.loader.exec_module(lib)
  store=skill_publisher.parent_verified_store_class(lib)(api,parent=skill_publisher.PARENT,folder_name=skill_publisher.FOLDER)
  found=store.find(skill_publisher.PARENT,skill_publisher.FOLDER);assert len(found)==1and found[0]['id']=='1dZE2gMavdnJsK_-VLmdFBdAxBwY10HmA';store.folder=found[0]['id']
  names=list(payload)+['final_evaluation_worker_v2.py','test_final_evaluation_worker_v2.py','fewshot_selection.json','root_fewshot_semantic_review.json','fewshot_selection_policy.json','final_launch_pins.json']
  names+=[str(p.relative_to(r))for p in(r/'fewshot_dev').iterdir()if p.is_file()and p.name in ['contract.json','generations.jsonl','complete.json']]
  for n in names:
   proofs[n]=store.put(n.replace('/','__'),r/n,immutable=True)
   status.write_text(json.dumps({'state':'ARCHIVING_BOUND_DEV_AND_CODE','completed':len(proofs),'count':len(names)},indent=2)+'\\n')
  while not(r/'final_eval/complete.json').exists():
   if skill_final_process.poll()not in(None,0):raise RuntimeError('Final evaluator failed; retain published partial metadata')
   if time.time()>json.loads((r/'owner_run_scope.json').read_bytes())['hard_deadline_unix']-600:raise TimeoutError('Final completion not available before publication reserve')
   time.sleep(10)
  names=[str(p.relative_to(r))for p in(r/'final_eval').rglob('*')if p.is_file()and p.suffix in('.json','.jsonl')and'.partial.'not in p.name]
  for n in sorted(names):
   proofs[n]=store.put(n.replace('/','__'),r/n,immutable=True)
   status.write_text(json.dumps({'state':'ARCHIVING_FINAL','completed':len(proofs),'last':n},indent=2)+'\\n')
  assert all(x['fresh_raw_readback_verified']for x in proofs.values())
  status.write_text(json.dumps({'state':'COMPLETE_RAW_VERIFIED','proofs':proofs,'final_evidence_does_not_change_selection':True},indent=2)+'\\n')
 except Exception as e:status.write_text(json.dumps({'state':'ERROR','error':repr(e),'traceback':traceback.format_exc(),'completed_proofs':proofs},indent=2)+'\\n')
 finally:api.close()
skill_completion_archive_thread=threading.Thread(target=_archive_skill_completion,name='SkillCompletionEvidenceArchive',daemon=True)
skill_completion_archive_thread.start()
print(json.dumps({'completion_archive_started':True,'final_evaluator_active':skill_final_process.poll()is None,'source_and_weights_changed':False}))
""".replace('PAYLOAD',repr(payload)).replace('PINS',repr(pins))
compile(code,'completion_archive','exec');(p/'archive_completion_runtime.py').write_text(code,encoding='utf8')
print(json.dumps({'assets':pins,'script_bytes':len(code)}))
