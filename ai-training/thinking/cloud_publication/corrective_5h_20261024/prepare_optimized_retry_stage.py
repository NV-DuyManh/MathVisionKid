from pathlib import Path
import base64,hashlib
p=Path(__file__).parent
name='corrective_worker_optimized_v2b.py'
raw=(p/name).read_bytes();sha=hashlib.sha256(raw).hexdigest()
assert sha=='d5f4f0bc2df2b9ff8b2999d607f7ab0b773a76e2ececd4cf48bada99ffcc787c'
code='''import pathlib,base64,hashlib,json,subprocess,os,time
root5=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024')
name=NAME
b=base64.b64decode(PAYLOAD);assert hashlib.sha256(b).hexdigest()==SHA
p=root5/name
if p.exists():assert p.read_bytes()==b
else:p.write_bytes(b)
assert corrective_process.poll() is not None
failed=root5/'training';history=root5/'training_optimized_v2_attempt1_preserved'
error=json.loads((failed/'error.json').read_bytes())
assert error['step']==0 and error['rows_done']==0 and error['error']=='optimizer state1 shape does not match parameter index 0'
assert not history.exists()
failed.rename(history)
preserved=root5/'training_v1_preserved'
verified=json.loads((root5/'resume_candidate_validation.json').read_bytes())
assert verified['coherent'] and verified['step']==270
generation=preserved/verified['generation']['generation']
pub=json.loads((root5/'drive_publication/publication_status.json').read_bytes());cp=pub['last_checkpoint']
assert cp['step']==270 and cp['fresh_raw_readback_verified']
cmd=[str(root5/'venv/bin/python'),'-u',str(p),'--train-view',str(root5/'training_view.jsonl'),'--view-manifest',str(root5/'sampling_manifest.json'),'--eval-fixtures',str(root5/'eval_fixtures.jsonl'),'--tokenizer-helper',str(root5/'exhaustive_colab_loader.py'),'--out',str(root5/'training'),'--eval-timeout-seconds','600','--resume-generation',str(generation),'--resume-successful-ids',str(preserved/'successful_ids.jsonl'),'--resume-base-dir',str(preserved),'--owner-budget-revision',str(root5/'owner_budget_revision_config.json'),'--pair-loss-helper',str(root5/'pair_weighted_batching_v2.py'),'--resume-source-error',str(preserved/'error.json')]
env=dict(os.environ);env['TOKENIZERS_PARALLELISM']='false'
log=(root5/'training_optimized_v2b.log').open('ab')
corrective_process=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
record={'state':'RETRY_CONFIRMED_BNB_SERIALIZATION_GUARD_FIX','worker_pid':corrective_process.pid,'worker_sha256':SHA,'launched_unix':time.time(),'source_generation':verified['generation'],'source_checkpoint_raw_verified':cp,'command':cmd,'hard_deadline_utc':'2026-10-24T05:28:23Z','train_stop_utc':'2026-10-24T05:13:23Z','benchmark_optimizer_updates':0,'prior_attempt_updates':0,'prior_attempt_history':str(history),'new_training_started':False}
(root5/'optimized_retry_manifest.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record))
'''.replace('NAME',repr(name)).replace('PAYLOAD',repr(base64.b64encode(raw).decode())).replace('SHA',repr(sha))
(p/'retry_optimized_v2b_runtime.py').write_text(code,encoding='utf-8')
