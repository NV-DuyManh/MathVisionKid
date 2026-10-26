import pathlib,json,hashlib,base64,gzip,sys
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024');sys.path.insert(0,str(r))
import behavior_renderer as B,recovery_policy_v2 as P
raw=(r/'training_view.jsonl').read_bytes().splitlines();rows=[json.loads(x) for x in raw];byid={x['sample_id']:(x,b) for x,b in zip(rows,raw)}
plan=json.loads((r/'derived_sampling_plan.json').read_bytes());samples=[];seen=set()
for sid in plan['schedule']:
 row,b=byid[sid];behavior=P._behavior(row);key=(row['grade'],behavior,row['mode'])
 if behavior not in ['guard','student_feedback'] or row['mode']!='worked_solution' or key in seen:continue
 seen.add(key);neutral,proof=B.render(row);samples.append({'sample_id':sid,'grade':row['grade'],'mode':row['mode'],'behavior':behavior,'source_original_raw_row_sha256':hashlib.sha256(b).hexdigest(),'actual_prompt':neutral['messages'][1]['content'],'actual_target':neutral['messages'][-1]['content']})
 if len(samples)==10:break
blob=(json.dumps({'samples':samples,'source_plan_sha256':hashlib.sha256((r/'derived_sampling_plan.json').read_bytes()).hexdigest(),'source_modified':False},ensure_ascii=False,indent=2)+'\n').encode();(r/'source_behavior_samples.json').write_bytes(blob)
print('BEHAVIOR_QA_GZIP_BASE64:'+base64.b64encode(gzip.compress(blob)).decode())
