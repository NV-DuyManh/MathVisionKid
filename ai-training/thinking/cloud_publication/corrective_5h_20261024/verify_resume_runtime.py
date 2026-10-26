import pathlib,json,subprocess,os
root5=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024')
assert corrective_process.poll() is not None
verify_code='''import pathlib,json,importlib.util,sys,hashlib,torch
r=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024')
spec=importlib.util.spec_from_file_location('optimized_check',r/'corrective_worker_optimized_v2.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
transition=json.loads((r/'owner_optimization_transition_config.json').read_bytes())
candidate=json.loads((r/'training/latest.json').read_bytes())
g=r/'training'/candidate['generation']
manifest,metrics,cfg=m.validate_resume_files(g)
assert m.sha_file(g/'generation_manifest.json')==candidate['manifest_sha256']
resume=torch.load(g/'resume_state.pt',map_location='cpu',weights_only=False)
proof=m.optimizer_coherence(resume['optimizer'],metrics['step'])
assert resume['step']==metrics['step']==manifest['step']
assert resume['rows_done']==metrics['rows_done']==manifest['rows_done']==16*metrics['step']
assert resume['cursor']==manifest['cursor']
log=(r/'training/successful_ids.jsonl').read_bytes()[:resume['successful_ids_log_bytes']]
rows=[json.loads(l) for l in log.splitlines()]
assert len(rows)==metrics['rows_done'] and log.endswith(bytes([10]))
assert all(x['step']==i//16+1 for i,x in enumerate(rows))
if metrics.get('stop_reason')=='ERROR':
 error=json.loads((r/'training/error.json').read_bytes());trace=error.get('traceback','')
 assert error['error_type']=='KeyboardInterrupt' and '.backward()' in trace and 'scaler.step(optimizer)' not in trace
result={'coherent':True,'generation':candidate,'source_path':str(g),'optimizer':proof,'step':metrics['step'],'rows_done':metrics['rows_done'],'supervised_tokens':metrics['supervised_tokens'],'training_wall_seconds':metrics['training_wall_seconds'],'successful_log_prefix_bytes':len(log),'successful_log_prefix_sha256':hashlib.sha256(log).hexdigest(),'interruption_location':'pre-update backward','exact_rng_rewind_claimed':False,'all_source_files_rawhash_verified':True,'full_row_order_and_token_recheck_required_by_resume_worker':True}
(r/'resume_candidate_validation.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
'''
env=dict(os.environ);env['CUDA_VISIBLE_DEVICES']=''
result=subprocess.run([str(root5/'venv/bin/python'),'-c',verify_code],capture_output=True,text=True,timeout=55,env=env)
print(result.stdout)
if result.returncode:print(result.stderr[-3000:])
assert result.returncode==0,'Do not launch from an incoherent candidate'
