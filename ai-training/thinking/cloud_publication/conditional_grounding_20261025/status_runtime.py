import pathlib,json,subprocess,datetime
r=pathlib.Path('/content/mathvisionkid_conditional_grounding_20261025')
report={'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'root_exists':r.is_dir()}
for key in ('conditional_install_process','conditional_training_process'):
 p=globals().get(key)
 report[key]={'pid':p.pid,'exit':p.poll()} if isinstance(p,subprocess.Popen) else None
for name in ('owner_run_scope.json','install_complete.json','training/progress.json','training/latest.json','training/best.json','training/run_complete.json','training/error.json','publication/publication_status.json'):
 p=r/name
 if p.is_file():
  if name=='publication/publication_status.json':
   value=json.loads(p.read_bytes());artifacts=value.get('artifacts',{})
   report[name]={k:value.get(k) for k in ('state','folder_id','folder_name','errors','last_error','publication_finalized') if k in value}
   report[name]['artifact_count']=len(artifacts)
   report[name]['checkpoints']=value.get('checkpoints',{})
   report[name]['active_code_proofs']={k:artifacts[k] for k in ('recovery_worker_v3.py','recovery_policy_v2.py','inference_contract.py','native_backend.py') if k in artifacts}
  elif p.stat().st_size<100000:report[name]=json.loads(p.read_bytes())
for name in ('install.log','training.log'):
 p=r/name
 if p.is_file():
  with p.open('rb') as stream:stream.seek(max(0,p.stat().st_size-4000));report[name+'_tail']=stream.read().decode('utf8',errors='replace')
report['gpu']=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.used,memory.total,utilization.gpu','--format=csv,noheader'],text=True).strip()
report['evaluation_output_progress']={}
for folder in ('eval_step_000000','eval_step_000100','eval_step_000300'):
 for name in ('base_generations.jsonl','base_generations.partial.jsonl','adapter_generations.jsonl','adapter_generations.partial.jsonl'):
  path=r/'training'/folder/name
  if path.is_file():
   records=[json.loads(line) for line in path.read_bytes().splitlines()]
   report['evaluation_output_progress'][folder+'/'+name]={'rows':len(records),'all_ended_eos':all(row['ended_eos'] for row in records),'last_fixture_id':records[-1]['fixture_id'] if records else None}
for name in ('four_controls_publication_status.json','training/native_first_microbatch_audit.json','training/model_artifact_binding.json'):
 path=r/name
 if path.is_file() and path.stat().st_size<20000:report[name]=json.loads(path.read_bytes())
print(json.dumps(report,ensure_ascii=False))
