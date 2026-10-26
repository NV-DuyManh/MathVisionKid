import pathlib,json,subprocess,os,time
root5=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024')
audit=json.loads((root5/'selected_view_tokenization_audit.json').read_bytes())
assert audit['state']=='PASS_STRUCTURAL_TOKENIZATION_ONLY'
pub=json.loads((root5/'drive_publication/publication_status.json').read_bytes())
assert pub['publisher_state']=='RUNNING' and pub.get('folder_id')
assert not globals().get('corrective_process') or corrective_process.poll() is not None
assert not (root5/'training/run_config.json').exists(),'Already initialized; do not duplicate'
cmd=[str(root5/'venv/bin/python'),'-u',str(root5/'corrective_worker.py'),'--train-view',str(root5/'training_view.jsonl'),'--view-manifest',str(root5/'sampling_manifest.json'),'--eval-fixtures',str(root5/'eval_fixtures.jsonl'),'--tokenizer-helper',str(root5/'exhaustive_colab_loader.py'),'--out',str(root5/'training'),'--eval-timeout-seconds','900']
env=dict(os.environ);env['TOKENIZERS_PARALLELISM']='false'
log=(root5/'training.log').open('ab')
corrective_process=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
launch={'worker_pid':corrective_process.pid,'launched_unix':time.time(),'command':cmd,'requested_training_wall_seconds':18000,'optimizer_pilot':False,'training_started':False,'folder_id':pub['folder_id']}
(root5/'launch_status.json').write_text(json.dumps(launch,indent=2))
print(json.dumps(launch))
