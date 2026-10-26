import json,sqlite3,hashlib
from datetime import datetime,timezone
_entry=next(e for e in recipe_all['chat_members'] if batch_module.member_key(e)=='a707937c3fa962493d5ec4765d31da22f03a44875bd0b840cb38f610da122641')
_cache_dir=ROOT/'full_audit_v3_worker_payload_cache'
_paths=[p for p in _cache_dir.rglob('*') if p.is_file() and p.stat().st_size==_entry['bytes']]
assert len(_paths)==1,[(p.name,p.stat().st_size) for p in _paths]
_chat_path=_paths[0]
_target_rows=[];_crosswalk=[]
with sqlite3.connect(V3_DB.as_uri()+'?mode=ro',uri=True,timeout=30) as _db:
 _db.execute('PRAGMA query_only=ON')
 with audit_v3.A.payload(_entry,_chat_path) as _stream:
  for _n,_text in enumerate(_stream,1):
   if _n<=511360:continue
   _row=json.loads(_text);_sid=batch_module.L.case_id(_row)
   _source=_db.execute('SELECT raw_sha,canonical_sha,projection,source_split FROM source_versions WHERE id=?',(_sid,)).fetchall()
   assert len(_source)==1
   _raw,_canonical,_projection,_split=_source[0]
   _errors=audit_v3.A.linkage_errors(_row,json.loads(_projection))
   _crosswalk.append({'line':_n,'sample_id':_row['sample_id'],'case_id':_sid,'mode':_row['mode'],'chat_raw_sha256':audit_v3.rawhash(_text),'chat_canonical_sha256':audit_v3.digest(_row),'chat_source_row_sha256':_row.get('source_row_sha256'),'chat_row_sha256':_row.get('row_sha256'),'current_source_raw_sha256':_raw,'current_source_canonical_sha256':_canonical,'source_split':_split,'projection_errors_ignoring_bad_hash':_errors,'verification':_row.get('verification'),'row_keys':list(_row)})
   _target_rows.append(_row)
_db.close()
assert len(_target_rows)==60
(resume_dir/'linkage60_actual_chat_rows.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in _target_rows),encoding='utf8')
linkage60_crosswalk={'schema':'MathVisionKid.exact_linkage60_diagnostic.v1','observed_utc':datetime.now(timezone.utc).isoformat(),'parent_entry':_entry,'source_index_identity':V3_ID,'rows':_crosswalk,'training_started':False,'data_mutated':False}
(resume_dir/'linkage60_crosswalk.json').write_text(json.dumps(linkage60_crosswalk,ensure_ascii=False,indent=2))
print(json.dumps(linkage60_crosswalk,ensure_ascii=False))
