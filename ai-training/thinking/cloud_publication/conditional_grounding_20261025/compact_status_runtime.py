import pathlib,json,datetime,subprocess
r=pathlib.Path('/content/mathvisionkid_conditional_grounding_20261025')
o={'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'worker_exit':conditional_training_process.poll(),'worker_pid':conditional_training_process.pid}
for name in ['training/progress.json','training/error.json','training/native_first_microbatch_audit.json','training/run_complete.json']:
 p=r/name
 if p.is_file():o[name]=json.loads(p.read_bytes())
o['eval']={}
for p in sorted((r/'training').glob('eval_step_*/*generations*.jsonl')):
 rows=[json.loads(line) for line in p.read_bytes().splitlines()]
 o['eval'][str(p.relative_to(r))]={'rows':len(rows),'last_id':rows[-1]['fixture_id'] if rows else None,'all_eos':all(x['ended_eos'] for x in rows)}
p=r/'publication/publication_status.json'
if p.exists():
 value=json.loads(p.read_bytes());o['publication']={k:value.get(k) for k in ['state','folder_id','errors','last_error'] if k in value}
 o['publication']['artifacts']=len(value.get('artifacts',{}));o['publication']['checkpoints']=value.get('checkpoints',{})
for name in ['four_controls_publication_status.json']:
 p=r/name
 if p.exists():
  value=json.loads(p.read_bytes());o[name]={k:value.get(k) for k in ['state','error','work','canonical_context_sha256'] if k in value}
o['gpu']=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader'],text=True).strip()
print(json.dumps(o,ensure_ascii=False))
