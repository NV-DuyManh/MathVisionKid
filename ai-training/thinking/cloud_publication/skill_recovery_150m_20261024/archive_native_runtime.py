import pathlib,json,threading,traceback,time,sys
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024')
assert not globals().get('skill_native_archive_thread') or not skill_native_archive_thread.is_alive()
def _archive_native_evidence():
 from googleapiclient.discovery import build
 from google_auth_httplib2 import AuthorizedHttp
 import httplib2
 api=build('drive','v3',http=AuthorizedHttp(recovery_credentials,http=httplib2.Http(timeout=60)),cache_discovery=False)
 status=r/'native_evidence_publication_status.json';proofs={}
 try:
  lib=sys.modules['skill_completion_archive_lib']
  store=skill_publisher.parent_verified_store_class(lib)(api,parent=skill_publisher.PARENT,folder_name=skill_publisher.FOLDER)
  found=store.find(skill_publisher.PARENT,skill_publisher.FOLDER);assert len(found)==1 and found[0]['id']=='1dZE2gMavdnJsK_-VLmdFBdAxBwY10HmA';store.folder=found[0]['id']
  names=['native_thinking_probe.py','test_native_thinking_probe.py','native_probe_scope.json','native_probe_selection_policy.json','native_locked15.jsonl','native_locked15_notes.json','native_locked15_root_review.json','native_locked15_train_screening.json','native_locked15_exact_checks.py','native_launch_pins.json','context_trial_final_review.json']
  for n in names:
   proofs[n]=store.put(n.replace('/','__'),r/n,immutable=True)
   status.write_text(json.dumps({'state':'ARCHIVING_SCOPE','completed':len(proofs)},indent=2)+'\n')
  while skill_native_dev_process.poll() is None:
   if time.time()>json.loads((r/'owner_run_scope.json').read_bytes())['hard_deadline_unix']-600:raise TimeoutError('Native dev did not finish within export reserve')
   time.sleep(10)
  for p in sorted((r/'native_probe/dev').glob('*')):
   if p.is_file() and p.suffix in('.json','.jsonl'):
    n=str(p.relative_to(r));proofs[n]=store.put(n.replace('/','__'),p,immutable=True)
    status.write_text(json.dumps({'state':'ARCHIVING_DEV','completed':len(proofs),'last':n},indent=2)+'\n')
  status.write_text(json.dumps({'state':'DEV_COMPLETE_RAW_VERIFIED','proofs':proofs,'all_raw_outputs_preserved_on_drive':True,'final_phase_not_yet_archived':True},indent=2)+'\n')
 except Exception as e:status.write_text(json.dumps({'state':'ERROR','error':repr(e),'traceback':traceback.format_exc(),'proofs':proofs},indent=2)+'\n')
 finally:api.close()
skill_native_archive_thread=threading.Thread(target=_archive_native_evidence,name='SkillNativeEvidenceArchive',daemon=True)
skill_native_archive_thread.start()
print(json.dumps({'native_evidence_archive_started':True,'optimizer_started':False}))
