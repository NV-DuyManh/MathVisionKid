import pathlib,json,subprocess,os,time
root5=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024')
assert corrective_process.poll() is not None
verified=json.loads((root5/'resume_candidate_validation.json').read_bytes())
assert verified['coherent'] is True
pub=json.loads((root5/'drive_publication/publication_status.json').read_bytes())
cp=pub.get('last_checkpoint',{})
assert cp.get('step')==verified['step'] and cp.get('fresh_raw_readback_verified') is True,'Wait for matching raw-verified Drive checkpoint'
old=root5/'training';preserved=root5/'training_v1_preserved'
assert old.is_dir() and not preserved.exists(),'Do not duplicate transition'
assert json.loads((old/'latest.json').read_bytes())==verified['generation']
old.rename(preserved)
generation=preserved/verified['generation']['generation']
cmd=[str(root5/'venv/bin/python'),'-u',str(root5/'corrective_worker_optimized_v2.py'),'--train-view',str(root5/'training_view.jsonl'),'--view-manifest',str(root5/'sampling_manifest.json'),'--eval-fixtures',str(root5/'eval_fixtures.jsonl'),'--tokenizer-helper',str(root5/'exhaustive_colab_loader.py'),'--out',str(root5/'training'),'--eval-timeout-seconds','600','--resume-generation',str(generation),'--resume-successful-ids',str(preserved/'successful_ids.jsonl'),'--resume-base-dir',str(preserved),'--owner-budget-revision',str(root5/'owner_budget_revision_config.json'),'--pair-loss-helper',str(root5/'pair_weighted_batching_v2.py'),'--resume-source-error',str(preserved/'error.json')]
env=dict(os.environ);env['TOKENIZERS_PARALLELISM']='false'
log=(root5/'training_optimized_v2.log').open('ab')
corrective_process=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
record={'state':'RESUMED_PROCESS_INITIALIZING','worker_pid':corrective_process.pid,'launched_unix':time.time(),'source_generation':verified['generation'],'source_checkpoint_raw_verified':cp,'command':cmd,'hard_deadline_utc':'2026-10-24T05:28:23Z','train_stop_utc':'2026-10-24T05:13:23Z','benchmark_optimizer_updates':0,'old_directory_preserved':str(preserved),'existing_publisher_folder_preserved':True,'current_optimizer_resumed':False}
(root5/'optimized_launch_manifest.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record))
