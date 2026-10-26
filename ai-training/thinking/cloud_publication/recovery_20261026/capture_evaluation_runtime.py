import pathlib,json,hashlib,base64,gzip
r=pathlib.Path('/content/mathvisionkid_recovery_20261026')
step=100
candidate=f'training/eval_step_{step:06d}/adapter_generations.jsonl'
names=['new_validation_candidates.jsonl','training/evaluation_contract.json','training/run_config.json',
 'training/eval_step_000000/base_generations.jsonl','training/eval_step_000000/eval_bindings.json',
 'training/native_first_microbatch_audit.json','training/model_artifact_binding.json',
 'derived_sampling_plan.json','training/best.json',candidate,
 f'training/eval_step_{step:06d}/eval_bindings.json','active_staged_code_pins.json','root_reviewed_training_plan.json','independent_preoptimizer_review.json','training/pretrain_qa_approved.json']
assert all((r/name).is_file() for name in names),'Do not grade incomplete paired evaluation'
assert len((r/candidate).read_bytes().splitlines())==30,'Read all candidate rows only after complete generation'
files={}
for name in names:
 data=(r/name).read_bytes()
 assert len(data)<3*1024*1024,'Only explicitly bounded metadata; no modelweights/corpus'
 # The sampling plan contains provenance IDs only; do not download all IDs to
 # PC when a hash and aggregate distribution suffice.
 if name=='derived_sampling_plan.json':
  plan=json.loads(data)
  summary={key:value for key,value in plan.items() if key not in ('schedule','selected_rows')}
  summary['original_plan_raw_sha256']=hashlib.sha256(data).hexdigest()
  files['source_plan_summary.json']=(json.dumps(summary,ensure_ascii=False,indent=2)+'\n').encode()
 else:files[name]=data
progress=json.loads((r/'training/progress.json').read_bytes())
generation=r/'training'/json.loads((r/'training/latest.json').read_bytes())['generation']
for name in ('generation_manifest.json','metrics.json'):
 files['generation/'+name]=(generation/name).read_bytes()
proof={'step':step,'files':{n:base64.b64encode(data).decode() for n,data in files.items()},
 'hashes':{n:hashlib.sha256(data).hexdigest() for n,data in files.items()},'worker_progress':progress,
 'only_development_outputs_and_metadata':True,'raw_model_thinking_included':False}
print('CONDITIONAL_EVAL_BUNDLE:'+base64.b64encode(gzip.compress(json.dumps(proof,ensure_ascii=False).encode())).decode())
