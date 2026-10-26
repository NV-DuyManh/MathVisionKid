import pathlib,json,hashlib,zipfile,time,threading,traceback,sys
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024')
assert skill_training_process.poll()==skill_fewshot_process.poll()==skill_final_process.poll()==skill_native_dev_process.poll()==0
assert(r/'training/final_semantic_assessment.json').is_file()
assert not globals().get('skill_release_archive_thread')or not skill_release_archive_thread.is_alive()
def _package_and_archive():
 from googleapiclient.discovery import build
 from google_auth_httplib2 import AuthorizedHttp
 import httplib2
 api=build('drive','v3',http=AuthorizedHttp(recovery_credentials,http=httplib2.Http(timeout=60)),cache_discovery=False)
 status=r/'final_release_publication.json';proofs={}
 try:
  lib=sys.modules['skill_completion_archive_lib']
  store=skill_publisher.parent_verified_store_class(lib)(api,parent=skill_publisher.PARENT,folder_name=skill_publisher.FOLDER)
  found=store.find(skill_publisher.PARENT,skill_publisher.FOLDER);assert len(found)==1 and found[0]['id']=='1dZE2gMavdnJsK_-VLmdFBdAxBwY10HmA';store.folder=found[0]['id']
  names=['native_probe_gate.json','context_trial_final_review.json','drive_write_coordination.json','training/final_semantic_assessment.json']
  names +=[str(p.relative_to(r))for p in(r/'native_probe/dev').iterdir()if p.is_file()and p.suffix in('.json','.jsonl')]
  for n in names:
   proofs[n]=store.put(n.replace('/','__'),r/n,immutable=(n!='training/final_semantic_assessment.json'))
   status.write_text(json.dumps({'state':'ARCHIVING_FINAL_METADATA','completed':len(proofs)},indent=2)+'\n')
  static=['owner_run_scope.json','owner_scope_binding_v2.json','behavior_renderer.py','verbal_training_renderer_v3.py','balanced_plan_v2.py','recovery_worker_v3.py','recovery_policy_v2.py','inference_contract.py','fewshot_contract.py','source_example_bank.json','projection_preflight.json','source_behavior_samples.json','fewshot_selection_policy.json','fewshot_selection.json','root_fewshot_semantic_review.json','context_trial_final_review.json','selected_inference_runtime.py','native_thinking_probe.py','native_probe_selection_policy.json','native_probe_scope.json','native_probe_gate.json','native_locked15.jsonl','native_locked15_notes.json','native_locked15_root_review.json','native_locked15_train_screening.json','native_locked15_exact_checks.py','new_validation_candidates.jsonl','locked_test_candidates.jsonl','locked_test_binding.json','source_semantic_review_g1_g3.json','source_semantic_review_g4_g5.json','source_example_bank_root_review.json','root_review_dev100_g1_g2.json','root_review_dev100_g3_g4.json','root_review_dev100_g5.json','calibration_review.json']
  static +=[str(p.relative_to(r))for p in(r/'training').glob('*.json')if p.name not in['error.json','successful_ids.jsonl']]
  static +=[str(p.relative_to(r))for folder in['benchmark','fewshot_dev','final_eval','native_probe/dev']for p in(r/folder).rglob('*')if p.is_file()and p.suffix in('.json','.jsonl')and'_raw'not in p.name and'.partial.'not in p.name]
  static +=[str(p.relative_to(r))for p in(r/'training').glob('eval_step_*/*.json')]
  static +=[str(p.relative_to(r))for p in(r/'training').glob('eval_step_*/*generations.jsonl')]
  files={}
  for n in sorted(set(static)):
   p=r/n;assert p.is_file(),n
   b=p.read_bytes();assert len(b)<2_000_000,'Only bounded code/evaluation metadata, no corpus/model'
   files[n]=b
  manifest={'schema':'MathVisionKid.skill_recovery_audit_package.v1','status':'EXPERIMENTS_COMPLETE_NO_PRODUCTION_APPROVED_UPGRADE','base_model':'Qwen/Qwen3-1.7B','revision':'70d244cc86ccca08cf5af4e1e306ecf908b1ad5e','contains_model_weights':False,'contains_original_corpus':False,'training_chat_count':1600,'supervised_tokens':178939,'adapter_is_diagnostic_only':True,'experimental_context_helper_not_production_approved':True,'new_native15_not_inferred_due_failed_dev_gate':True,'files':{n:{'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}for n,b in files.items()},'checkpoint_and_adapter_drive_proofs':json.loads((r/'training/final_semantic_assessment.json').read_bytes())['raw_drive_evidence']['checkpoint_proofs'],'final_report_sha256':hashlib.sha256((r/'training/final_semantic_assessment.json').read_bytes()).hexdigest()}
  manifest_bytes=(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
  package_dir=r/'release';package_dir.mkdir(exist_ok=True);target=package_dir/'quality_recovery_audit_bundle.zip'
  assert not target.exists(),'Do not duplicate packaged bytes'
  with zipfile.ZipFile(target,'x',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
   for n,b in{'PACKAGE_MANIFEST.json':manifest_bytes,**files}.items():
    info=zipfile.ZipInfo(n,date_time=(2026,10,24,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b)
  with zipfile.ZipFile(target)as z:
   assert z.testzip() is None
   actual=json.loads(z.read('PACKAGE_MANIFEST.json'))
   for n,meta in actual['files'].items():
    b=z.read(n);assert len(b)==meta['bytes']and hashlib.sha256(b).hexdigest()==meta['sha256']
  h=hashlib.sha256(target.read_bytes()).hexdigest();proof=store.put('quality_recovery_audit_bundle_'+h[:16]+'.zip',target,immutable=True)
  assert proof['fresh_raw_readback_verified']
  status.write_text(json.dumps({'state':'COMPLETE_RAW_VERIFIED','bundle':proof,'manifest_sha256':hashlib.sha256(manifest_bytes).hexdigest(),'metadata_proofs':proofs,'all_gpu_workers_exited':True,'production_approved':False},indent=2)+'\n')
 except Exception as e:status.write_text(json.dumps({'state':'ERROR','error':repr(e),'traceback':traceback.format_exc(),'metadata_proofs':proofs},indent=2)+'\n')
 finally:api.close()
skill_release_archive_thread=threading.Thread(target=_package_and_archive,name='SkillFinalAuditPackageArchive',daemon=True)
skill_release_archive_thread.start()
print(json.dumps({'final_audit_package_thread_started':True,'corpus_or_model_downloaded_to_pc':False,'new_training_started':False}))
