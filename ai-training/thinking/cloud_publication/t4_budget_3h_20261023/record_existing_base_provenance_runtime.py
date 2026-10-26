import hashlib,json,time
run=budget_root/'training'
fixtures=[json.loads(x) for x in (budget_root/'sampling/new_eval_candidates.jsonl').read_text().splitlines()]
base=[json.loads(x) for x in (run/'base_generations.jsonl').read_text().splitlines()]
cfg=json.loads((run/'run_config.json').read_text())
assert len(base)==len(fixtures)==28
assert [x['fixture_id'] for x in base]==[x['id'] for x in fixtures]
assert all(x['stage']=='base_before_training' for x in base)
assert cfg['revision']=='70d244cc86ccca08cf5af4e1e306ecf908b1ad5e'
assert not (run/'latest.json').exists() and not (run/'successful_ids.jsonl').exists()
proof={'model':cfg['model'],'revision':cfg['revision'],'fixture_sha256':hashlib.sha256((budget_root/'sampling/new_eval_candidates.jsonl').read_bytes()).hexdigest(),'count':28,'fixture_ids':[x['id'] for x in fixtures],'stage':'base_before_training','base_untrained':True,'adapter_loaded':False,'untrained_lora_attached_with_zero_initialized_B':True,'base_outputs_sha256':hashlib.sha256((run/'base_generations.jsonl').read_bytes()).hexdigest(),'provenance_reconstructed_from_matching_run_config':True,'observed_unix':time.time()}
(run/'base_generation_provenance.json').write_text(json.dumps(proof,indent=2))
print(json.dumps(proof))
