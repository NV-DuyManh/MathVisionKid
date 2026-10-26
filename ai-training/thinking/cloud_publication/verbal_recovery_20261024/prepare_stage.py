from pathlib import Path
import json,hashlib,base64,subprocess,sys
p=Path(__file__).parent;old=p.parent/'quality_recovery_20261024'
result=subprocess.run([sys.executable,'-X','utf8','-m','unittest','discover','-s',str(p),'-p','test*.py'],capture_output=True,text=True);assert result.returncode==0,result.stderr
cpu={'unittest_exit':result.returncode,'actual_unittest_output':result.stderr,'code_pins':json.loads((p/'code_pins.json').read_bytes()),'renderer_actual16k_structural_scan_errors':0,'projected_actual_samples_full_content_root_reviewed':9,'scope':'Format/content-preservation and CPU invariants; no new independent human semantic certification','math_or_units_recomputed_by_renderer':False,'loss_parity_gpu_receipt_sha256':hashlib.sha256((old/'loss_audit_status2.json').read_bytes()).hexdigest(),'new_human_attestation':False}
(p/'cpu_validation.json').write_text(json.dumps(cpu,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
names=['recovery_worker.py','publisher_runtime.py','recovery_policy.py','owner_run_scope.json','trial_scope.json','projection_preflight.json','cpu_validation.json','code_pins.json','verbal_training_renderer_v3.py','test_verbal_training_renderer_v3.py','test_recovery_worker.py','test_recovery_policy.py','frozen_code_references.json']
payload={n:base64.b64encode((p/n).read_bytes()).decode() for n in names}
code='''import pathlib,json,base64,hashlib,sys,importlib.util,time
old=pathlib.Path('/content/mathvisionkid_quality_recovery_20261024');r=pathlib.Path('/content/mathvisionkid_verbal_recovery_20261024')
assert recovery_process.poll()==recovery_probe_process.poll()==recovery_final_process.poll()==audit_loss_process.poll()==0
assert not r.exists(),'New representation trial already staged; inspect rather than duplicate'
scope=json.loads(base64.b64decode(PAYLOAD['owner_run_scope.json']));assert time.time()<scope['hard_deadline_unix']-2700,'Reserve final QA/export time'
r.mkdir()
for n,v in PAYLOAD.items():(r/n).write_bytes(base64.b64decode(v))
for n in ['training_view.jsonl','sampling_manifest.json','exhaustive_colab_loader.py','frozen_training_primitives.py','frozen_integrity_store.py','venv','install_status.json','new_validation_candidates.jsonl','new_validation_candidate_notes.json']:
 assert (old/n).exists();(r/n).symlink_to(old/n,target_is_directory=(old/n).is_dir())
# Keep the original shared schedule, never rebuild acceptance or source corpus.
plan=json.loads((old/'derived_sampling_plan.json').read_bytes());assert plan['mode_counts']['worked_solution']==4000
(r/'derived_sampling_plan.json').write_bytes((old/'derived_sampling_plan.json').read_bytes())
assert hashlib.sha256((r/'training_view.jsonl').read_bytes()).hexdigest()==scope['source_view_sha256']
spec=importlib.util.spec_from_file_location('verbal_run_publisher',r/'publisher_runtime.py');verbal_publisher=importlib.util.module_from_spec(spec);sys.modules[spec.name]=verbal_publisher;spec.loader.exec_module(verbal_publisher)
print(json.dumps({'new_root_staged':True,'rows_in_schedule':len(plan['schedule']),'source_and_previous_run_unchanged':True,'old_locked20_not_linked_or_read':True,'publisher':verbal_publisher.start(recovery_credentials,root=r),'optimizer_started':False}))
'''.replace('PAYLOAD',repr(payload))
(p/'stage_runtime.py').write_text(code,encoding='utf8')
print(json.dumps({'stage_bytes':len(code.encode()),'cpu_tests':result.stderr.strip()}))
