import pathlib,json,hashlib,time
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024')
assert skill_training_process.poll()==skill_fewshot_process.poll()==skill_final_process.poll()==skill_native_dev_process.poll()==0
release=json.loads((r/'final_release_publication.json').read_bytes());assert release['state']=='COMPLETE_RAW_VERIFIED' and release['bundle']['fresh_raw_readback_verified']
p=r/'training/final_semantic_assessment.json';h=hashlib.sha256(p.read_bytes()).hexdigest();assert h=='0d7e5e2fe032aeb3e03384892634f8c6b627594e8812ef3edccc3c7b5ce4c855'
pub=json.loads((r/'publication/publication_status.json').read_bytes());proof=pub['artifacts']['training/final_semantic_assessment.json'];assert proof['sha256']==h and proof['fresh_raw_readback_verified']
request={'finalize_requested':True,'final_semantic_assessment_sha256':h,'request_unix':time.time(),'release_bundle_id':release['bundle']['id'],'release_bundle_sha256':release['bundle']['sha256'],'all_gpu_workers_exited':True}
marker=r/'publication/finalize_requested.json'
if marker.exists():assert json.loads(marker.read_bytes())['final_semantic_assessment_sha256']==h
else:marker.write_text(json.dumps(request,indent=2)+'\n')
print(json.dumps({'finalization_requested':True,'report_drive_proof':proof,'bundle_drive_proof':release['bundle'],'no_new_training':True}))
