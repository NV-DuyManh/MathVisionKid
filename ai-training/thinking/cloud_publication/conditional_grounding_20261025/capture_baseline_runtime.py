import pathlib,json,hashlib,base64,gzip
r=pathlib.Path('/content/mathvisionkid_conditional_grounding_20261025')
names=['new_validation_candidates.jsonl','training/evaluation_contract.json','training/run_config.json',
 'training/eval_step_000000/base_generations.jsonl','training/eval_step_000000/eval_bindings.json']
assert all((r/name).is_file() for name in names),'Baseline evaluation not complete'
files={name:(r/name).read_bytes() for name in names}
rows=[json.loads(line) for line in files['training/eval_step_000000/base_generations.jsonl'].splitlines()]
assert len(rows)==30
proof={'files':{n:base64.b64encode(data).decode() for n,data in files.items()},
 'hashes':{n:hashlib.sha256(data).hexdigest() for n,data in files.items()},
 'only_development_outputs_and_metadata':True,'raw_model_thinking_included':False}
print('CONDITIONAL_BASE_BUNDLE:'+base64.b64encode(gzip.compress(json.dumps(proof,ensure_ascii=False).encode())).decode())
