from pathlib import Path
import base64,json,hashlib
p=Path(__file__).parent
names=['verbal_training_renderer_v3.py','test_verbal_training_renderer_v3.py']
payload={n:base64.b64encode((p/n).read_bytes()).decode() for n in names}
code='''import pathlib,json,base64,hashlib,sys,collections,time
r=pathlib.Path('/content/mathvisionkid_quality_recovery_20261024')
assert audit_loss_process.poll()==0
assert json.loads((r/'target_alignment_audit/forward_loss_audit.json').read_bytes())['all_next_token_parity_pass'] is True
for n,v in PAYLOAD.items():
 b=base64.b64decode(v);f=r/n
 if f.exists():assert f.read_bytes()==b
 else:f.write_bytes(b)
if str(r) not in sys.path:sys.path.insert(0,str(r))
import verbal_training_renderer_v3 as V
raw=(r/'training_view.jsonl').read_bytes();assert hashlib.sha256(raw).hexdigest()=='14929ba64e5c94d812f1fc3804c771ca8e41fa92285aed3a925282c39b1e4331'
rows=[json.loads(x) for x in raw.splitlines()];shapes=collections.Counter();errors=[];samples=[];leaves=0;chars=[0,0]
for i,row in enumerate(rows):
 p=json.loads(row['messages'][1]['content']);shapes[','.join(sorted(p))]+=1
 try:
  transformed,proof=V.render(row);leaves+=len(proof['fields']);chars[0]+=len(row['messages'][-1]['content']);chars[1]+=len(transformed['messages'][-1]['content'])
  if (row['mode']=='worked_solution' and row['grade'] in range(1,6) and not any(s['grade']==row['grade'] and s['mode']==row['mode'] for s in samples)) or (row['mode']!='worked_solution' and row['grade']==3 and not any(s['mode']==row['mode'] for s in samples)) or (p.get('student_work') and not any(s.get('student_work_present') for s in samples)):
   samples.append({'sample_id':row['sample_id'],'grade':row['grade'],'mode':row['mode'],'source_original_raw_row_sha256':hashlib.sha256(raw.splitlines()[i]).hexdigest(),'student_work_present':bool(p.get('student_work')),'actual_prompt':transformed['messages'][1]['content'],'actual_target':transformed['messages'][2]['content'],'proof':proof})
 except Exception as e:
  if len(errors)<10:errors.append({'sample_id':row['sample_id'],'error':repr(e),'actual_prompt_object':p,'actual_target':json.loads(row['messages'][-1]['content'])})
out={'rows_scanned':len(rows),'prompt_shapes':dict(shapes),'errors':errors,'all_semantic_field_instances_preserved':leaves,'assistant_character_counts':{'source_json':chars[0],'verbal':chars[1]},'samples':samples,'source_modified':False,'train_started':False,'human_attestation_added':False,'renderer_sha256':hashlib.sha256((r/'verbal_training_renderer_v3.py').read_bytes()).hexdigest()}
(r/'target_alignment_audit/verbal_projection_preflight_v3.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\\n')
print(json.dumps(out,ensure_ascii=False))
'''.replace('PAYLOAD',repr(payload))
(p/'verbal_preflight_v3_runtime.py').write_text(code,encoding='utf8');print(json.dumps({'code_bytes':len(code.encode())}))
