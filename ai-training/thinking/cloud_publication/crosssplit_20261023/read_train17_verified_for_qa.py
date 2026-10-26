import json,hashlib
assert len(_out)==len(_train_pins)==17
_crosssplit_train_rows={r['sample_id']:r for r in _out}
assert set(_crosssplit_train_rows)==set(_train_pins)
_hints={};_rows=[]
for r in _crosssplit_train_rows.values():
 assert audit_v3.digest(r)==_train_pins[r['sample_id']]['canonical_sha256']
 h=r['hints'];key=audit_v3.digest(h);_hints[key]=h
 item={k:r.get(k) for k in ['sample_id','grade','problem','givens','requested_quantity','student_work','initial_guidance','worked_steps','expected_answer','curriculum_assignment']}
 item['actual_hints_hash']=key;_rows.append(item)
print(json.dumps({'actual_distinct_hints':_hints,'actual_train_source_rows':_rows},ensure_ascii=False))
