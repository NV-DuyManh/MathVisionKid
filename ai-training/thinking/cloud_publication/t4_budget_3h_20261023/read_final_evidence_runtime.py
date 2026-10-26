import pathlib, json, base64, hashlib, importlib.util
from datetime import datetime, timezone
root=pathlib.Path('/content/mathvisionkid_t4_budget_3h_20261023')
train=root/'training'
assert (train/'run_complete.json').is_file(), 'Training not complete; read status instead'
assert (train/'final_runtime_evidence.json').is_file(), 'CPU collector not yet finished'
e=json.loads((train/'final_runtime_evidence.json').read_bytes())
spec=importlib.util.spec_from_file_location('actual_coverage',train/'actual_coverage.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
coverage=mod.summarize_actual_coverage(e['sampling_manifest'],e['raw_file_records']['successful_ids']['records'])
(train/'actual_optimizer_coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
out={'observed_utc':datetime.now(timezone.utc).isoformat(),
     'normalized_run':e['normalized_run_complete_candidate'],
     'runtime_settings':e.get('training_runtime_settings'),
     'actual_coverage':coverage,
     'checkpoint_timing_records':e['checkpoint_timing_records'],
     'completeness':e['completeness'],
     'raw_file_proofs':{k:{a:b for a,b in v.items() if a!='records'} for k,v in e['raw_file_records'].items()},
     'collector_evidence_sha256':hashlib.sha256((train/'final_runtime_evidence.json').read_bytes()).hexdigest(),
     'raw_outputs':{}}
for name in ('base_generations.jsonl','adapter_generations.jsonl','run_complete.json'):
    raw=(train/name).read_bytes()
    out['raw_outputs'][name]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'base64':base64.b64encode(raw).decode('ascii')}
for key,name in [('publication','drive_publication/publication_status.json'),('benchmark_binding','benchmark_id_binding.json'),('gpu_memory_observations','gpu_total_memory_observations.json'),('runtime_versions','runtime_versions.json')]:
    p=root/name
    out[key]=json.loads(p.read_bytes()) if p.is_file() else None
print(json.dumps(out,ensure_ascii=False))
