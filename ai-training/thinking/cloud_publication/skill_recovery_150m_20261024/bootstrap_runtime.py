import pathlib,json,hashlib,time,subprocess,base64,gzip,collections
from datetime import datetime,timezone
old=pathlib.Path('/content/mathvisionkid_verbal_recovery_20261024');r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024')
assert verbal_process.poll()==verbal_final_process.poll()==0
r.mkdir(exist_ok=False)
start=datetime(2026,10,24,12,37,46,tzinfo=timezone.utc).timestamp();deadline=start+9000
scope={'schema':'MathVisionKid.skill_recovery_150m_owner_scope.v1','authorization':'Owner explicitly requested improve model using existing data and selected2hours30minutes for this new run.','budget_start_utc':'2026-10-24T12:37:46Z','budget_start_unix':start,'hard_deadline_unix':deadline,'hard_deadline_utc':datetime.fromtimestamp(deadline,timezone.utc).isoformat(),'budget_max_wall_seconds':9000,'reserve_seconds':1800,'paid_resources':False,'source_and_old_checkpoints_preserved':True,'corpus_or_model_download_to_pc':False,'production_change':False,'new_human_attestation':False,'development_fixtures':'Existing dev30 only; previous final/locked fixtures excluded from tuning.','model':'Qwen/Qwen3-1.7B','revision':'70d244cc86ccca08cf5af4e1e306ecf908b1ad5e','notebook_id':'1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l'}
(r/'owner_run_scope.json').write_text(json.dumps(scope,ensure_ascii=False,indent=2)+'\n')
for name in ['venv','training_view.jsonl','sampling_manifest.json','frozen_training_primitives.py','tokenizer_helper.py','new_validation_candidates.jsonl','frozen_integrity_store.py','install_status.json','verbal_training_renderer_v3.py']:
 source=old/name
 if source.exists():(r/name).symlink_to(source,target_is_directory=source.is_dir())
source=old/'training_view.jsonl';h=hashlib.sha256(source.read_bytes()).hexdigest()
assert h=='14929ba64e5c94d812f1fc3804c771ca8e41fa92285aed3a925282c39b1e4331'
rows=[json.loads(x) for x in source.read_text().splitlines()]
groups=collections.Counter();schema=collections.Counter();modes=collections.Counter();beh=collections.Counter();examples=[]
for row in rows:
 p=json.loads(row['messages'][1]['content']);t=json.loads(row['messages'][-1]['content']);mode=row['mode'];grade=row['grade'];topic=row.get('topic','')
 category='guard' if t.get('can_solve') is False else ('student_feedback' if p.get('student_work') else 'standard')
 groups[(grade,str(topic),mode,category)]+=1;modes[mode]+=1;beh[category]+=1;schema[','.join(sorted(row))]+=1
 if len(examples)<2:examples.append({'sample_id':row['sample_id'],'keys':sorted(row),'topic':topic,'prompt_keys':sorted(p),'target_keys':sorted(t)})
inv={'source_rows':len(rows),'source_sha256':h,'row_schemas':dict(schema),'modes':dict(modes),'behavior_counts':dict(beh),'groups':[{'grade':g,'topic':t,'mode':m,'behavior':b,'count':n} for (g,t,m,b),n in sorted(groups.items(),key=lambda x:str(x[0]))],'bounded_schema_examples':examples,'observed_utc':datetime.now(timezone.utc).isoformat(),'source_modified':False}
(r/'source_inventory.json').write_text(json.dumps(inv,ensure_ascii=False,indent=2)+'\n')
print('NEW_SCOPE_INVENTORY_GZIP_BASE64:'+base64.b64encode(gzip.compress(json.dumps({'scope':scope,'inventory':inv}).encode())).decode())
print(json.dumps({'root':str(r),'source_rows':len(rows),'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.used,memory.total','--format=csv,noheader'],text=True).strip(),'old_workers_exited':True,'training_started':False}))
