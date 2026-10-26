"""Build only a schema adapter code table for the already pinned primary782 export.
Does not curate/export/rewrite source or chat data, and does not read sealed tests.
"""
from pathlib import Path
import hashlib,json
from collections import Counter
import primary_math_data_pipeline as B
import math_data_archive_audit as A
from math_data_portable_resume import canonical,digest
HERE=Path(__file__).resolve().parent
BASE=HERE/'data/primary_math_teacher_20261016'
PINS={
'exports/accepted_teacher_cases.jsonl':'917f541097c4cd7f8fc6ee2f4a23a6187f64a002df111f2eb984044897314911',
'exports/accepted_teacher_cases_polished.jsonl':'99aefab7a58177e3b3222f7bf269c02e991fafeaf2fed79e83b5b5b39ebc5a02',
'exports/teacher_chat_train_polished.jsonl':'e33915cf24b8dcd39500c3bb4a5fd939b948f3c345cb851862aa35f6778f8ded',
'exports/polished_export_manifest.jsonl':'a3189d7e6ab9c7960678813437dd25be50522ea40562f3f79df1efff6a69f6d1',
'curation_manifest.jsonl':'b79e6cee4a7945b345b29c3a47b54cafa60e717c36d4575dd9cd50ea0bd41963',
'owner_human_signoffs.jsonl':'9475d9fabc1668e04a3e4ce3f5708a8f28e65ebf8c87337c212463017f3a7f1a',
'owner_human_attestations.json':'e0d59a9a5ee6e428bfe2c2bcc3cee9fa7b8b52f507140ca09491a39f269cf4ea'}
def h(b):return hashlib.sha256(b).hexdigest()
def main():
 for name,expected in PINS.items():assert h((BASE/name).read_bytes())==expected,name
 raw=(BASE/'exports/accepted_teacher_cases_polished.jsonl').read_bytes()
 rs=[json.loads(x)for x in raw.splitlines()]
 parents={r['sample_id']:r for r in map(json.loads,(BASE/'exports/accepted_teacher_cases.jsonl').read_bytes().splitlines())}
 manifest={r['sample_id']:r for r in map(json.loads,(BASE/'exports/polished_export_manifest.jsonl').read_bytes().splitlines())}
 signoffs=B.load_owner_signoffs(BASE)
 chats=[json.loads(x)for x in (BASE/'exports/teacher_chat_train_polished.jsonl').read_bytes().splitlines()]
 by_chat={x['sample_id']:x for x in chats};assert len(rs)==782 and len(chats)==3128
 table={};counts=Counter()
 for row,line in zip(rs,raw.splitlines()):
  sid=row['sample_id'];m=manifest[sid];canonical_hash=digest(row);alias=row['verification']['source_row_sha256']
  assert canonical_hash==m['exported_row_sha256']
  derived=m['derived_source_row_sha256'];assert alias==(derived or m['original_source_row_sha256'])
  if row['human_verified']:
   sig=signoffs[sid];assert sig['source_row_sha256']==alias
   assert sig['exported_row_sha256']==canonical_hash and sig['attestation_id']==row['verification']['attestation_id']
   counts['existing_exact_owner_attested_exports']+=1
  elif derived:
   assert not row['teacher_certified'] and not row['owner_human_reviewed']
   counts['derived_polish_not_human_attested']+=1
  inspected=B.inspect_case(row);assert inspected['passed'],(sid,inspected['errors'])
  signatures=sorted(B.answer_signatures(row,inspected))
  parent=parents[m['parent_sample_id']];assert digest(parent)==m['parent_exported_row_sha256']
  # Frozen finalizer deliberately preserves the original parent's grouping.
  group=B.chat_records(parent)[0]['case_group_id'];assert group==m['case_group_id']
  actual=B.chat_records(row);assert len(actual)==4
  for c in actual:
   c['case_group_id']=group
   stored=by_chat[c['sample_id']]
   assert all(stored.get(k)==v for k,v in c.items()),c['sample_id']
   extra=set(stored)-set(c)
   assert extra<=({'parent_sample_id','original_source_row_sha256'}if derived else set())
   if derived:
    assert stored['parent_sample_id']==m['parent_sample_id']
    assert stored['original_source_row_sha256']==m['original_source_row_sha256']
  adapted=dict(row,can_solve=row.get('can_solve',bool(row['expected_answer'])),case_group_id=group)
  projection=A.source_projection(adapted)
  table[h(line)]={'sample_id':sid,'exported_canonical_sha256':canonical_hash,
                 'original_or_derived_source_sha256':alias,'chat_group_id':group,
                 'can_solve':adapted['can_solve'],'source_verification_digest':digest(row['verification']),
                 'projection_sha256':digest(projection),'canonical_signatures':signatures,
                 'hash_chain_kind':'DERIVED_POLISH_SOURCE'if derived else'ORIGINAL_AI_SOURCE',
                 'existing_owner_attested':bool(row['human_verified'])}
  counts['source_rows']+=1;counts['chat_rows_verified']+=4
  counts['missing_can_solve_explicitly_adapted']+= 'can_solve'not in row
 provenance={'schema':'MathVisionKid.primary782_exact_schema_adapter.v3','input_files_sha256':PINS,
  'builder_code_sha256':h((HERE/'primary_math_data_pipeline.py').read_bytes()),
  'finalizer_code_sha256':h((HERE/'finalize_primary_math_finite.py').read_bytes()),
  'parent_source_projection_code_sha256':h((HERE/'math_data_archive_audit.py').read_bytes()),
  'source_hash_overlay_previous_scope':'Existing1130source/3596chat overlay is unchanged and does not bind this primary782 member.',
  'known_source_member_sha256':PINS['exports/accepted_teacher_cases_polished.jsonl'],
  'counts':dict(counts),'no_raw_data_rewritten':True,'no_human_attestation_added':True,
  'binding_table_sha256':digest(table)}
 text='"""Generated exact-row schema bindings for frozen primary782 export; no problem text copied."""\n'
 text+='import json\nPROVENANCE = json.loads('+repr(canonical(provenance))+')\n'
 text+='BINDINGS = json.loads('+repr(canonical(table))+')\n'
 dest=HERE/'math_data_primary782_bindings_v3.py';dest.write_text(text,encoding='utf-8')
 proof=dict(provenance,generated_helper_sha256=h(dest.read_bytes()),generated_helper_bytes=dest.stat().st_size,raw_source_sha256_after=h((BASE/'exports/accepted_teacher_cases_polished.jsonl').read_bytes()),raw_chat_sha256_after=h((BASE/'exports/teacher_chat_train_polished.jsonl').read_bytes()))
 (HERE/'math_data_primary782_adapter_v3_validation.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(proof,ensure_ascii=False))
if __name__=='__main__':main()

