import pathlib,json
p=pathlib.Path('/content/mathvisionkid_recovery_20261026/training/eval_step_000100/adapter_generations.partial.jsonl')
if not p.exists():p=p.with_name('adapter_generations.jsonl')
rows=[json.loads(line) for line in p.read_bytes().splitlines()]
print(json.dumps({'rows':len(rows),'generation_metadata':[{k:r[k] for k in ['fixture_id','generated_tokens','ended_eos','possibly_truncated','timed_out','generation_seconds']} for r in rows]}))
