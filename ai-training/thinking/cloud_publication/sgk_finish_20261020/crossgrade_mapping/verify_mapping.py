import json,pathlib,hashlib,re,collections
B=pathlib.Path(__file__).resolve().parent
R=B.parent.parent/'sgk_page_audit_20261019'
H=lambda b:hashlib.sha256(b).hexdigest()
J=lambda p:json.loads(p.read_text('utf-8-sig'))
m=J(B/'mapping.json');q=J(B/'resume_queue.json');v=J(B/'validation.json')
cs={x['candidate_id']:x for x in m['candidates']}
masters={x['master_id']:x for x in q['masters']}
linecache={f:(R/f).read_bytes().splitlines() for f in ['current_sources.jsonl','release/accepted_cases.jsonl']}
errors=[]
check=lambda yes,desc:errors.append(desc) if not yes else None
for z in cs.values():
 check(z['decision']['master_id'] in masters,'missing master '+z['candidate_id'])
 for ref in z['nearest_refs']:
  raw=linecache[ref['source_file']][ref['line']-1]
  check(H(raw)==ref['sha256'],'raw hash '+ref['sample_id'])
  row=json.loads(raw)
  check(row['sample_id']==ref['sample_id'],'ID '+ref['sample_id'])
  check(row.get('split','train')=='train','split '+ref['sample_id'])
  check(not re.search('holdout|eval|pilot|protected',ref['sample_id'],re.I),'excluded ID '+ref['sample_id'])
original_counts={}
for dr,key in [('g1v1_audit','new_gap_candidate_ids'),('g1v2_audit','new_gap_candidate_ids'),('g3_audit','gap_ids'),('g4_audit','gap_candidates'),('g5_audit','gap_ids')]:
 expected=[]
 for n,l in enumerate((R/dr/'page_review.jsonl').read_text('utf-8-sig').splitlines(),1):
  row=json.loads(l)
  for c in row.get(key,[]):expected.append(f'{dr}:{n}:{c}')
 actual=[o['occurrence_id'] for o in m['occurrences'] if o['occurrence_id'].startswith(dr+':')]
 check(collections.Counter(expected)==collections.Counter(actual),'lost or duplicated original occurrences '+dr)
 original_counts[dr]={'expected':len(expected),'mapped':len(actual)}
for fn,key in [('g1v1_audit/gaps.json',None),('g1v2_audit/candidate_adjudication.json','candidates'),('g3_audit/candidate_adjudication.json','adjudications'),('g4_audit/remaining_candidate_adjudication.json','candidates'),('g5_audit/candidate_adjudication.json','adjudications')]:
 d=J(R/fn);arr=d if key is None else d[key]
 for a in arr:
  c=a.get('candidate_id',a.get('gap_id'))
  check(c in cs,'lost original adjudication '+c)
for z in m['published110_mapping']:
 raw=linecache['release/accepted_cases.jsonl'][z['line']-1]
 check(H(raw)==z['source_row_sha256'],'published hash '+z['sample_id'])
 check(bool(z['matched_candidate_ids']),'unmapped accepted source '+z['sample_id'])
for rowline in (B/'nearest_fullfields.jsonl').read_text('utf-8').splitlines():
 z=json.loads(rowline);raw=linecache[z['source_file']][z['line']-1];row=json.loads(raw)
 check(H(raw)==z['sha256'],'fullfield raw hash '+z['sample_id'])
 check(z['source_row']==row,'fullfield source payload '+z['sample_id'])
 check(all(z['semantic_field_values'][k]==row.get(k) for k in ['problem','givens','requested_quantity','student_work','worked_steps','expected_answer','initial_guidance','hints','can_solve']),'semantic fields '+z['sample_id'])
for p,h in v['source_file_sha256'].items():check(H((R/p).read_bytes())==h,'changed input '+p)
check(len(m['published110_mapping'])==110,'published count')
check(len(set(z['family'] for z in m['published110_mapping']))==40,'family count')
check(all(z['category']!='PENDING_ACTUAL_COMPARISON' for z in q['masters']),'unresolved source comparison')
report={'pass':not errors,'errors':errors,'original_page_candidate_occurrence_conservation':original_counts,'additional_adjudication_and_spatial_receipt_occurrences':len(m['occurrences'])-sum(z['expected'] for z in original_counts.values()),'unique_candidate_labels':len(cs),'total_occurrences':len(m['occurrences']),'masters':len(masters),'published_rows':110,'published_families':40,'fullfield_row_count':sum(1 for _ in (B/'nearest_fullfields.jsonl').open(encoding='utf-8')),'raw_source_id_hash_split_validation':True,'all_supported_semantic_fields_equal_exact_current_source_rows':True,'source_files_same_hash_as_mapping_build':True,'no_eval_pilot_protected_payload_output':True,'limitations':'Semantic adjudication is manual bounded comparison of actual closest fields, not an algorithmic proof of exhaustive absence. Exact raw/source validations do not certify student outcomes or original visual/physical assets.'}
(B/'independent_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
hashes=J(B/'artifact_hashes.json')
for p in ['independent_validation.json','verify_mapping.py']:hashes[p]=H((B/p).read_bytes())
(B/'artifact_hashes.json').write_text(json.dumps(hashes,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
if errors:raise SystemExit(1)
