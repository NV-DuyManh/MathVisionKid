from pathlib import Path
import base64,gzip,hashlib,json
p=Path(__file__).parent
sources={name:p/name for name in ['prepare_four_controls_runtime.py','test_corrective_worker.py']}
sources['test_start_publisher_runtime_optimized_v2.py']=p/'test_start_publisher_runtime.py'
sources['four_controls_transaction_v2.py']=p/'four_controls_transaction.py'
sources['test_four_controls_runtime_v2.py']=p/'test_four_controls_runtime.py'
for name in ['corrective_worker_optimized_v2.py','corrective_worker_optimized_v2b.py','pair_weighted_batching_v2.py','owner_budget_revision_config.json','revised_publisher_contract_v2.py','optimized_v2_cpu_validation.json','optimized_v2b_cpu_validation.json','status_runtime.py']:
 sources[name]=p/name
old=Path('thinking/cloud_publication/t4_budget_3h_20261023/resume_20261024')
for name in ['completed_branch_assessment.json','adapter_semantic_review.json','base_vs_adapter_comparison.json','tokenization_code_audit.json','training_target_code_audit.json']:
 sources['prior3h_'+name]=old/name
for name in ['final_semantic_assessment.json','review_g1_g2.json','review_g3_g4.json','review_g5.json']:
 sources['final_'+name]=p/'final_evidence'/name
payload={n:base64.b64encode(s.read_bytes()).decode() for n,s in sources.items()}
ctx=Path('MATH_TRAINING_CONTEXT.md').read_bytes()
ctx64=base64.b64encode(gzip.compress(ctx,mtime=0)).decode()
code='''import pathlib,json,base64,gzip,hashlib,importlib.util,sys,threading,time,traceback
from datetime import datetime,timezone
root5=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024')
payload=PAYLOAD
for n,v in payload.items():
 b=base64.b64decode(v);path=root5/n
 if path.exists():assert path.read_bytes()==b,'Existing source differs: '+n
 else:path.write_bytes(b)
canonical_context_bytes=gzip.decompress(base64.b64decode(CTX64))
assert hashlib.sha256(canonical_context_bytes).hexdigest()==CTXSHA
(root5/'canonical_context_staged.md').write_bytes(canonical_context_bytes)
def load_control(name):
 spec=importlib.util.spec_from_file_location(name,root5/(name+'.py'))
 mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
prepare5=load_control('prepare_four_controls_runtime');transaction5=load_control('four_controls_transaction_v2')
assert not globals().get('corrective_controls_thread') or not corrective_controls_thread.is_alive()
def _publish5_controls():
 state_path=root5/'four_controls_publication_status.json'
 def state(value):
  tmp=state_path.with_suffix('.pending');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2));tmp.replace(state_path)
 work=root5/'four_controls_publication'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
 try:
  state({'state':'READING_PARENTS','work':str(work)})
  parents=transaction5.download_current_parents_with_credentials(repair_credentials,prepare5.IDS,work/'parents',min_request_interval=1.25)
  worker_observation={'observed_utc':datetime.now(timezone.utc).isoformat(),'worker_alive':bool(globals().get('corrective_process') and corrective_process.poll() is None),'worker_exit':corrective_process.poll() if globals().get('corrective_process') else None,'pid':corrective_process.pid if globals().get('corrective_process') else None}
  actual=prepare5.capture_branch_metadata(root5,worker_observation=worker_observation)
  evidence_names=list(payload)+['corrective_worker.py','start_publisher_runtime.py','audit_view_runtime.py','exhaustive_colab_loader.py','owner_run_scope.json','cpu_validation.json','selected_view_tokenization_audit.json','staged_code_hashes.json']
  evidence={n:root5/n for n in evidence_names}
  prepared=prepare5.prepare_controls(parents,canonical_context_bytes,actual,evidence,work/'prepared')
  state({'state':'PREPARED','work':str(work),'observation':actual,'controls':prepared['controls']})
  receipt=transaction5.publish_with_credentials(repair_credentials,prepared['parents'],prepared['controls'],work,receipt_path=work/'four_controls_raw_verified.json',min_request_interval=1.25)
  assert [x['kind'] for x in receipt['verified_writes']]==['progress','chat','context','state']
  assert all(x['fresh_raw_readback_verified'] for x in receipt['verified_writes'])
  (root5/'four_controls_verified_manifest.json').write_text(json.dumps(receipt,indent=2))
  state({'state':'COMPLETE_RAW_VERIFIED','work':str(work),'receipt':receipt,'canonical_context_sha256':CTXSHA})
 except Exception as e:state({'state':'ERROR','work':str(work),'error':repr(e),'traceback':traceback.format_exc()})
corrective_controls_thread=threading.Thread(target=_publish5_controls,name='MathVisionKidCorrective5hFourControlPublisher',daemon=True)
corrective_controls_thread.start()
print(json.dumps({'controls_thread_started':True,'canonical_context_sha256':CTXSHA,'data_or_weights_changed':False}))
'''.replace('PAYLOAD',repr(payload)).replace('CTX64',repr(ctx64)).replace('CTXSHA',repr(hashlib.sha256(ctx).hexdigest()))
(p/'stage_controls_runtime.py').write_text(code,encoding='utf-8')
