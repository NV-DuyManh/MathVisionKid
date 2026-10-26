from pathlib import Path
import base64,hashlib
P=Path(__file__).parent;review=(P/'independent_preoptimizer_review.json').read_bytes()
oldreview=P.parent/'conditional_grounding_20261025/root_paired_decisions_step_000100.json'
code='''import pathlib,json,base64,hashlib,sys
root=pathlib.Path('/content/mathvisionkid_recovery_20261026')
publication=json.loads((root/'publication/publication_status.json').read_bytes())
assert publication['state']=='RUNNING' and conditional_training_process.poll() is None
pins=json.loads((root/'active_staged_code_pins.json').read_bytes())
required=['recovery_worker_20261026.py','native_backend_20261026.py','recovery_policy_20261026.py','conditional_behavior_renderer.py','inference_contract.py','derived_sampling_plan.json','source_qa_binding.json','owner_run_scope.json']
for name in required:
 raw=(root/name).read_bytes();proof=publication['artifacts'][name]
 assert proof['fresh_raw_readback_verified'] and proof['sha256']==hashlib.sha256(raw).hexdigest(),name
 if name in pins:assert pins[name]==proof['sha256']
assert json.loads((root/'screening_publication_repair.json').read_bytes())['training_data_targets_config_or_evaluation_changed'] is False
peer=base64.b64decode(PEER64);assert hashlib.sha256(peer).hexdigest()==PEERSHA
(root/'independent_preoptimizer_review.json').write_bytes(peer)
qa=json.loads((root/'training/pretrain_source_qa_prepared.json').read_bytes())
assert qa['root_actual_source_samples_reviewed'] is True and qa['human_review_claimed'] is False
assert qa['sample_count']==24 and qa['all24_original_raw_source_hashes_reverified_in_current_cloud'] is True
assert qa['all24_targets_equal_previously_read_content'] is True
assert qa['source_plan_sha256']==hashlib.sha256((root/'derived_sampling_plan.json').read_bytes()).hexdigest()
assert qa['renderer_sha256']==hashlib.sha256((root/'conditional_behavior_renderer.py').read_bytes()).hexdigest()
# Fresh raw readback of the prior run's standalone semantic closure; no checkpoint is loaded.
remote=recovery_drive.files().get_media(fileId='1gz9LMFrDvWnbHp5ycOuyQm223i5SGptL').execute()
assert len(remote)==OLDBYTES and hashlib.sha256(remote).hexdigest()==OLDSHA
(root/'prior_run_review_raw_verified.json').write_text(json.dumps({'id':'1gz9LMFrDvWnbHp5ycOuyQm223i5SGptL','sha256':OLDSHA,'bytes':OLDBYTES,'fresh_raw_readback_verified':True,'prior_adapter_loaded':False},indent=2)+'\\n')
approval={**qa,'independent_code_review_sha256':PEERSHA,'core_code_raw_verified_before_optimizer':True,
 'root_final_code_review_complete':True,'root_approval_scope':'Reuse exact24reviewedsource target bindings, tested row objective and pinned configuration. This is automated root/peer QA, no human attestation or performance guarantee.'}
dest=root/'training/pretrain_qa_approved.json';assert not dest.exists()
tmp=dest.with_suffix('.pending');tmp.write_text(json.dumps(approval,sort_keys=True,indent=2)+'\\n');tmp.replace(dest)
print(json.dumps({'optimizer_approval_written':True,'peer_review_sha256':PEERSHA,'previous_review_raw_verified':True,'human_review_claimed':False,'optimizer_update_observed':False}))
'''.replace('PEER64',repr(base64.b64encode(review).decode())).replace('PEERSHA',repr(hashlib.sha256(review).hexdigest())).replace('OLDBYTES',repr(oldreview.stat().st_size)).replace('OLDSHA',repr(hashlib.sha256(oldreview.read_bytes()).hexdigest()))
compile(code,'approve26','exec');(P/'approve_optimizer_runtime.py').write_bytes(code.encode())
print('Prepared source/hash-bound optimizer approval; no update claimed')
