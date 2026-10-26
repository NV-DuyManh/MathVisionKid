import json,pathlib,collections
r=pathlib.Path('/content/mathvisionkid_quality_recovery_20261024');shapes={k:collections.Counter() for k in ['step','answer','given','student_work','observation']}
for line in (r/'training_view.jsonl').read_text().splitlines():
 x=json.loads(line);p=json.loads(x['messages'][1]['content']);t=json.loads(x['messages'][2]['content'])
 for label,objects in [('step',t.get('steps',[])),('answer',t.get('answer',[])),('given',p.get('givens',[]))]:
  for o in objects:shapes[label][','.join(sorted(o))]+=1
 w=p.get('student_work')
 if w is not None:
  shapes['student_work'][','.join(sorted(w)) if isinstance(w,dict) else type(w).__name__]+=1
  if isinstance(w,dict):
   for o in w.get('observations',[]):shapes['observation'][','.join(sorted(o))]+=1
out={k:dict(v) for k,v in shapes.items()};(r/'target_alignment_audit/full_field_shape_inventory.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps(out,ensure_ascii=False))
