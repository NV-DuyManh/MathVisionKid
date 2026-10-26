import pathlib,json,base64,gzip,hashlib
r=pathlib.Path('/content/mathvisionkid_verbal_recovery_20261024');f=r/'final_eval'
assert (f/'selection_before_test.json').exists(),'Selection must precede locked content access'
names=['locked_test_candidates.jsonl','training/run_complete.json','training/best.json','final_eval/selection_before_test.json','final_eval/evaluation_contract.json','training/generation_step_000001_rows_00000016/metrics.json','training/generation_step_000050_rows_00000800/metrics.json']
for n in ['final_eval/base_generations.jsonl','final_eval/adapter_generations.jsonl','final_eval/selected_output_reference.json','final_eval/final_eval_manifest.json','final_eval/error.json']:
 if (r/n).exists():names.append(n)
partial=not (f/'base_generations.jsonl').exists()
raw={n:(r/n).read_bytes() for n in names}
if partial:raw['final_eval/base_generations.jsonl']=(f/'base_generations.partial.jsonl').read_bytes()
bundle={'partial':partial,'files':{n:base64.b64encode(b).decode() for n,b in raw.items()},'hashes':{n:hashlib.sha256(b).hexdigest() for n,b in raw.items()}}
print('FINAL_BUNDLE_GZIP_BASE64:'+base64.b64encode(gzip.compress(json.dumps(bundle).encode())).decode())
