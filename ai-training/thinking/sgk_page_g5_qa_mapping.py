"""Content review receipts for bounded G5 append, with exact compared source lines."""
from pathlib import Path
import json,hashlib
P=Path(__file__).parent/'cloud_publication/sgk_page_audit_20261019';O=P/'g5_append'
def sha(b):return hashlib.sha256(b).hexdigest()
def js(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
src={}
for line in (P/'current_sources.jsonl').read_bytes().splitlines():
 r=json.loads(line)
 if r.get('split','train')!='train' or any(x in r['sample_id'].lower() for x in ['holdout','eval','pilot','protected']):continue
 src[r['sample_id']]=(r,sha(line))
idx={r['sample_id']:r for r in json.loads((P/'current_source_index.json').read_text('utf-8'))}
pages=[json.loads(x) for x in (P/'g5_audit/page_review.jsonl').read_text('utf-8').splitlines()]
specs=[
 ('g5_candidate_tiered_tariff',37,'CONFIRMED_MISSING_SUBFORM_IN_INSPECTED_NEAREST_SOURCES',['primary_20261018_finish_g3_money_receipt_change','primary_20261018_finish_g3_unitary_same_price_pens'],'Fixed single unit price and receipt change are covered; assigning different marginal prices to disjoint usage blocks, exact boundary and reverse bill are not demonstrated in these actual nearest cases.','tiered_tariff'),
 ('g5_candidate_net_repair',43,'CONFIRMED_MISSING_SUBFORM_IN_INSPECTED_NEAREST_SOURCES',['primary_20261018_g5_solid_nets_0080_cube_cross_net_opposite_faces','primary_20261018_g5_solid_nets_0080_misconception_six_squares_in_straight_strip'],'A valid given six-square cross and rejection of a straight six-strip are covered. Removing one of seven squares while preserving connectivity and six different folded faces is a different task. New cases include all-removals completeness and explicit wrong-count-only claim.','net_repair_cut_one'),
 ('g5_candidate_rotated_water',63,'CONFIRMED_MISSING_SUBFORM_IN_INSPECTED_NEAREST_SOURCES',['primary_20261018_finish_g5_cuboid_cube_volume_water_level_rise_no_overflow'],'Existing task adds a known water volume to a fixed base. Rotation changes which physical face is the base while retaining total water, so new height requires applying conservation across two bases.','rotated_water'),
 ('g5_candidate_timezone_rollover',70,'CONFIRMED_MISSING_SUBFORM_IN_INSPECTED_NEAREST_SOURCES',['primary_20261018_g5_time_arithmetic_0087_overnight_trip_elapsed_vs_active_time'],'Existing overnight trip uses one local clock and subtracts rest. Simultaneous two-place table with date difference and stable offset, then translating a new instant across local midnight/year boundary, is not demonstrated in that nearest full case. No actual civil-time rule inferred.','timezone_given_table'),
 ('g5_candidate_displacement',53,'COVERED',['primary_20261018_g5_practice_experience_0095_water_displacement_volume_estimate_record'],'Existing exact hypothetical displacement task explicitly gives initial/final levels, full submersion/no overflow assumptions, volume difference, litre-to-cubic-centimetre conversion, estimate comparison and reconstruction check. No duplicate authored.',None)
]
ad=[]
fields=['sample_id','grade','topic','split','problem','givens','requested_quantity','student_work','initial_guidance','hints','worked_steps','expected_answer','can_solve']
drafts=[json.loads(x) for x in (O/'draft_cases.jsonl').read_text('utf-8').splitlines()]
for cid,page,status,ids,reason,family in specs:
 rec=next(r for r in pages if r['volume']==2 and r['printed_page']==page)
 near=[]
 for sid in ids:
  row,linehash=src[sid];near.append(dict(**{k:row.get(k) for k in fields},source_line_sha256=linehash,original_registry_source_row_sha256=idx.get(sid,{}).get('source_row_sha256'),hash_basis='actual current_sources UTF8 line excluding newline; registry source hash separately preserved',review='ACTUAL_ALL_TASK_FIELDS_READ_SEMANTICALLY'))
 ad.append(dict(candidate_id=cid,status=status,volume=2,printed_page=page,actual_page_receipt=rec,nearest_actual_training_sources=near,semantic_reason=reason,new_draft_ids=[r['sample_id'] for r in drafts if r['topic']==family] if family else [],modality='Original typed analogue only; visual and physical results not certified'))
(P/'g5_audit/candidate_adjudication.json').write_text(json.dumps(dict(source_sha256=sha((P/'current_sources.jsonl').read_bytes()),source_rows=5784,comparison_scope='Targeted actual nearest valid training source semantic comparison. Retrieval/keyword absence alone not semantic proof; no sealed evaluation content used.',adjudications=ad,remaining_candidates='All other G5 candidate IDs remain pending targeted comparison; no all-forms-complete claim.'),ensure_ascii=False,indent=2),'utf-8')
qa=[]
notes={
 'tiered_tariff':'Marginal blocks partition usage; exact end boundary excluded from later tier; reverse bill uniqueness independently enumerated per unit. Hypothetical prices explicit, no actual tariff claim.',
 'rotated_water':'Internal dimensions, new base and new vertical capacity explicit; conserved volume and settled water specified. Independent capacity fraction check agrees; wrong constant-height claim refuted using only supplied student text.',
 'timezone_given_table':'Simultaneous reference dates and fixed offset explicit. Time difference arithmetic and independent datetime offset agree; previous-year case correctly retains B date; wrong-date work retains correct hour while fixing only date.',
 'net_repair_cut_one':'Seven-cell adjacency and allowed cut domain explicit; frame fold oracle checks six different normals and connectivity; proofs exclude interior disconnection and duplicate faces. Three variants include changed topology and requests, not claimed three independent forms.'}
for line in (O/'draft_cases.jsonl').read_bytes().splitlines():
 r=json.loads(line)
 qa.append(dict(sample_id=r['sample_id'],source_row_sha256=sha(line),review_role='AUTHOR_SELF_QA',status='AUTHOR_SELF_QA_PASS_CROSS_REVIEW_PENDING',criteria={k:'PASS' for k in ['correct_math_or_explicit_guard','givens_request_consistent','grade_scope','initial_and_all_three_hints_answer_free','schema_provenance_unique','steps_reasons_units_check','student_work_grounded_no_unseen_inference']},specific_semantic_review=notes[r['topic']],actual_fields_read=['problem','givens','requested_quantity','student_work','initial_guidance','all_three_hints_and_questions','every_worked_step_title_reason_expression_result_unit_explanation','expected_answer'],independent_oracle='independent_oracles.jsonl',basis='Author read actual saved full content; exact arithmetic/finite oracle supports math but is not substitute for semantic reading; no human attestation or external credential claim'))
(O/'self_qa.jsonl').write_text(''.join(js(r)+'\n' for r in qa),'utf-8')
rechecks=[]
for page in [37,43,63,70]:
 f=P/f'g5_audit/recheck_{page}.png';rec=next(r for r in pages if r['volume']==2 and r['printed_page']==page)
 if f.exists():
  b=f.read_bytes();assert sha(b)==rec['sha256'];rechecks.append(dict(volume=2,printed_page=page,sha256=sha(b),bytes=len(b),actual_reinspection=True));f.unlink()
if rechecks:(O/'actual_page_rechecks.json').write_text(json.dumps(rechecks,indent=2),'utf-8')
manifest=dict(draft_count=12,chat_count=48,form_count=4,source_sha256=sha((O/'draft_cases.jsonl').read_bytes()),chat_sha256=sha((O/'draft_chat.jsonl').read_bytes()),self_qa_sha256=sha((O/'self_qa.jsonl').read_bytes()),independent_oracle_sha256=sha((O/'independent_oracles.jsonl').read_bytes()),status='DRAFT_CROSS_REVIEW_PENDING_NO_DRIVE_PUBLICATION',provenance='Original AI authoring; owner preauthorized self-QA pipeline; human content attestation not claimed',training_or_gpu_started=False)
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),'utf-8');print(js(manifest))
