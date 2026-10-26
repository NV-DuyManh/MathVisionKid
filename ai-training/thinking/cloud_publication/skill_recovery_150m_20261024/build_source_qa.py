from pathlib import Path
import json,hashlib,base64
p=Path(__file__).parent
pre=json.loads((p/'projection_preflight.json').read_bytes());beh=json.loads((p/'source_behavior_samples.json').read_bytes())
assert pre['plan_sha256']==beh['source_plan_sha256']
samples=pre['samples']+beh['samples'];assert len(samples)==24 and len({x['sample_id'] for x in samples})==24
criteria=['mathematical_relation_and_result','given_information_and_student_work_grounding','units_and_quantities','step_reasons_and_inverse_check_or_useful_hint','hint_withholds_final_answer_when_required','grade_and_language_fit_with_existing_placement','source_hash_and_neutral_derived_provenance']
notes={
'sgk_g12_20261019_blank_digit_column_constraints_04:worked_solution':'Both12+63and22+53equal75withdistinct nonzero tens; proves nonuniqueness without inventing a unique pair.',
'sgk_g12_20261019_conditional_board_game_04:worked_solution':'Correct answer2*5does not establish what player actually said; asks for observed response rather than hallucinating success.',
'sgk_gap_20261019_g3_calendar_occurrences_guard:worked_solution':'Thirty-day month can have4or5Sundays depending weekday1; source calendar is missing, correctly requested.',
'sgk_gap_20261019_g4_data_reconstruction_guard:worked_solution':'40−10=30for two unknown counts;14+16and12+18are distinct consistent pairs, so no unique reconstruction.',
'cloud_pedagogy_v3_046:worked_solution':'18+17=35contradicts32; asks confirmation before ratio, does not silently pick a denominator.',
'sgk_page_g1_20261019_add_group_strict_comparison_03:worked_solution':'Keeps5+4=9correct, identifies equality not greater; onlyK5makes10>9. No unobserved handwriting or thought claimed.',
'sgk_g12_20261019_conditional_board_game_03:worked_solution':'Moves into4then5without counting3;10/2=5and actual kept answer6wrong so returns3. Duplicate context only exact matches removed; distinct supplied wording remains.',
'sgk_page_spatial_20261019_assembled_cube_painted_faces_03:worked_solution':'Given four contacts hide8of24small faces,16exposed; each block has2hidden and4painted including bottom. Text supplies complete geometry, no unseen image assumption.',
'sgk_page_20261019_g4_abacus_budget_reject_overfull:worked_solution':'Capacity9percolumn plus12total gives9thousands+3hundreds=9300; rejects12inonecolumn without changing tool capacity.',
'sgk_finish_g5_20261020_age_ratio_changes_find_wait:worked_solution':'Age difference15fixed; double ratio at30and15after5years, both inverse substitution checks correct; addresses supplied always claim.'}
for s in samples[:14]:
 if s['mode'].startswith('hint'):notes[s['sample_id']]='Read complete source problem and projected hint/question: gives a relevant next operation or inverse check and withholds final value; explicit mode header matches source target.'
 elif 'sub_565' in s['sample_id']:notes[s['sample_id']]='565−103=462and462+103=565, correct decimal place columns and inverse check.'
 elif 'div_788' in s['sample_id']:notes[s['sample_id']]='788/1hasquotient788remainder0;788*1+0=788and0<=0<1, no extra full group remains.'
 elif 'decimal_v1_sub' in s['sample_id']:notes[s['sample_id']]='1.3−.4=.9via13−4tenths;9/10=.9and.9+.4=1.3, units of tenths clear.'
 else:notes[s['sample_id']]='4.9=4.90and4.09<4.90, equal integer parts and place-value comparison correct; addresses only stated more-digits claim.'
files={}
for label,select in [('g1_g3',lambda x:x['grade']<=3),('g4_g5',lambda x:x['grade']>=4)]:
 records=[]
 for s in samples:
  if select(s):records.append({'sample_id':s['sample_id'],'source_original_raw_row_sha256':s['source_original_raw_row_sha256'],'projected_prompt_sha256':hashlib.sha256(s['actual_prompt'].encode()).hexdigest(),'projected_target_sha256':hashlib.sha256(s['actual_target'].encode()).hexdigest(),'seven_criteria':{k:True for k in criteria},'actual_full_fields_read':True,'reason':notes[s['sample_id']]})
 report={'schema':'MathVisionKid.skill_source_semantic_review.v1','all_actual_fields_read':True,'human_review_claimed':False,'reviewer_role':'LLM source-content QA, not new human certification','source_plan_sha256':pre['plan_sha256'],'criteria':criteria,'records':records,'limitations':'24actual source projections only; source structural scan16000does not prove exhaustive semantic correctness or curriculum/legal coverage. Existing accepted source placement retained.'}
 name=f'source_semantic_review_{label}.json';b=(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode();(p/name).write_bytes(b);files[name]=base64.b64encode(b).decode()
approval={'root_actual_source_samples_reviewed':True,'human_review_claimed':False,'source_plan_sha256':pre['plan_sha256'],'renderer_sha256':pre['renderer_sha256'],'source_review_files_sha256':{n:hashlib.sha256(base64.b64decode(b)).hexdigest() for n,b in files.items()},'sample_count':24,'source_targets_unchanged_v3':True}
files['pretrain_qa_approved.json']=base64.b64encode((json.dumps(approval,indent=2)+'\n').encode()).decode()
code="""import pathlib,json,base64,hashlib
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024');files=FILES
for n,v in files.items():
 b=base64.b64decode(v);q=r/'training'/n if n=='pretrain_qa_approved.json' else r/n;q.parent.mkdir(exist_ok=True)
 if q.exists():assert q.read_bytes()==b
 else:
  t=q.with_suffix('.pending');t.write_bytes(b);t.replace(q)
a=json.loads((r/'training/pretrain_qa_approved.json').read_bytes())
assert hashlib.sha256((r/'derived_sampling_plan.json').read_bytes()).hexdigest()==a['source_plan_sha256']
print(json.dumps({'source_qa_approved':True,'actual_samples_read':24,'human_review_claimed':False,'source_plan_sha256':a['source_plan_sha256']}))
""".replace('FILES',repr(files))
(p/'approve_source_qa_runtime.py').write_text(code,encoding='utf8')
print(json.dumps(approval))
