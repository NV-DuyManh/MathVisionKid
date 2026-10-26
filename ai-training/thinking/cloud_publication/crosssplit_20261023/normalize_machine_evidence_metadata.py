import json,hashlib,sqlite3
from datetime import datetime,timezone
_dir=ROOT/'crosssplit_20261023/pinned_metadata'
_original=(_dir/'train17_numeric_overlap_machine_evidence.json').read_bytes()
_ev=json.loads(_original);_cross=json.loads((_dir/'signature_crosswalk.json').read_bytes())
_train={x['case_id']:x for x in _cross['matches'] if x['source_split']=='train_candidate' and x['linked_samples']}
_eval={x['case_id']:x for x in _cross['matches'] if x['source_split'] in ('validation','test')}
assert _ev['all_fraction_decimal_oracles_passed'] is True and len(_ev['train_rows'])==17
with sqlite3.connect(V3_DB.as_uri()+'?mode=ro',uri=True,timeout=30) as _db:
 for _row in _ev['train_rows']:
  _pin=_train[_row['case_id']]
  _source=_db.execute('SELECT canonical_sha,source_split FROM source_versions WHERE id=? AND raw_sha=?',(_row['case_id'],_row['source_raw_sha256'])).fetchone()
  assert _source==(_pin['canonical_sha256'],'train_candidate')
  _row['source_split']=_source[1]
 for _row in _ev['current_eval_sources']:
  _pin=_eval[_row['case_id']]
  _source=_db.execute('SELECT canonical_sha,source_split,signatures FROM source_versions WHERE id=? AND raw_sha=?',(_row['case_id'],_row['source_raw_sha256'])).fetchone()
  assert _source and _source[0]==_pin['canonical_sha256'] and _source[1]==_pin['source_split']
  assert _row['signatures']==json.loads(_source[2])
  assert set(_pin['overlapping_signatures']).issubset(_row['signatures'])
  _row['signatures']=_pin['overlapping_signatures']
_ev['metadata_binding_derivation']={'parent_machine_sha256':hashlib.sha256(_original).hexdigest(),'observed_utc':datetime.now(timezone.utc).isoformat(),'changes':['Added source_split reverified from exact indexed source hashes','Restricted current_eval_sources signatures to the already verified crosswalk overlap subset'],'original_machine_evidence_preserved':True,'oracle_not_rerun':True,'source_chat_payload_bytes_changed':0,'training_started':False}
_result=(json.dumps(_ev,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
_dest=_dir/'train17_numeric_overlap_machine_evidence_v2.json'
assert not _dest.exists()
_dest.write_bytes(_result)
print(json.dumps({'machine_evidence_rows':17,'chat_bindings':68,'all_fraction_decimal_oracles_passed':True,'original_machine_sha256':hashlib.sha256(_original).hexdigest(),'derived_bytes':len(_result),'derived_sha256':hashlib.sha256(_result).hexdigest(),'training_started':False}))
