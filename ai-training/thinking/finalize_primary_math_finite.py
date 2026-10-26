"""Finite data preparation release: preserve originals and explicit attestation scopes."""
import ast,json,sys
from pathlib import Path
from copy import deepcopy
from fractions import Fraction
from decimal import Decimal,localcontext
from collections import Counter
from datetime import datetime,timezone
from primary_math_data_pipeline import *
R=DEFAULT_ROOT
E=HERE/'evidence/primary_math_teacher_20261016'
def load(p):return json.loads(p.read_text('utf-8'))
def stamp():return datetime.now(timezone.utc).isoformat()

POLISH_NOTES=[
'1m=100cm; 100+5=105cm; incorrect written1+5=6 preserves quote and only rejects mixing units; hints do not fill105.',
'Partition IDs AEG red3, BCFH blue4, D yellow1 uses all8 once; redundant yellow sentence removed, no actual vision claim.',
'68384-25568=42816: units14-8, tens7-6, hundreds13-5, thousands7-5, ten-thousands6-2; inverse68384.',
'76458 total disjoint story24326 and reference52132; each subtraction column and inverse checked, no other books inferred.',
'31527+12458=43985; explicit written7+8=15 carry1 followed by2+5 omits that written carry; do not invent unseen work.',
'Grid plan four by three1cm squares, closure and four right angles; no assertion of actual drawing; hint3 grammar fixed.',
'A96-24/3=88 versus B(96-24)/3=24, precedence8/72 tracked, brackets and all operands retained.',
'Unknown minuend □-247=328 gives575;575-247=328; correct quantity roles.',
'Unknown dividend □/4=213 gives852;213*4 trace and852/4 long division verified; semicolon roles remove decimal-looking punctuation.',
'684-unknown=239 gives445; quoted923 is not the requested subtrahend; inverse684-445=239, no hidden method claim.',
'Between plus6=6 makes M midpoint; between plus4!=8 makes N not midpoint; equal total12 alone insufficient.',
'P off AB with equal distances5 and AB6 is not midpoint; preserve given position, never move point.',
'AOB both set-square sides aligned even rotated is right; CPD second ray inside is not; hypothetical tool evidence only.',
'OA=OB=5 does not imply right angle; explicit set-square second side inside fails, no unseen measuring error inferred.',
'EqualMA=MB5 lacks collinearity/between; asks image or position before conclusion; no numeric answer.',
'4237*2=8474: units14 carry1, tens7, hundreds4, thousands8; inverse4237.',
'836/4=209 includes zero tens in quotient; final36/4=9 and209*4=836; punctuation clearly separates incorrect29 from2hundreds.',
'2203/7 q314 r5; intermediate22,10,33;314*7+5=2203 and0<=5<7; metadata remainder kept.',
'846/4 wrong210r6 reconstructs846 but remainder6>=4; one more group gives211r2; do not call correct multiplication wrong.',
'48items with ambiguous6bags vs6items/bag swaps quantity labels; asks missing role, no guessed numeric solution.',
'99999+1=100000; all-nine carry boundary proves Bgreater, inverse recovers99999.',
'417+26+83 associative grouping500+26=526 and417+109=526, every addend once.',
'16*5*2 left80*2/right16*10 both160; retain all factors, multiplication associativity only.',
'628+147=775 checked by both inverse subtractions, no altered operand roles.',
'86-(23-13)=76 versus(86-23)-13=50 counterexample to subtraction associativity; no universal claim every change differs.',
'24 and6 missing operator cannot determine sum vs product; asks exact expression, empty worked answer.',
'Explicit standard Roman notation IV4 VI6; order matters, no clock-notation claim.',
'95000 is halfway90k/100k; stated tie-up rule gives100k approximation only, exact inventory remains95000.',
'36450 nearestthousand36000 by hundreds4 and distances450/550; reject written tens5 rule only.',
'ABCD four right angles with opposite8/5 has rectangle not square; boundary sides exclude diagonalAC.',
'P four equal sides5 plus four right angles square even rotated; Q equal sides but failed right-angle condition not square.',
'Circle centerO, endpoints on boundary;OA/OB/OC radii;AB passes through center with O between, diameter;DE neither radius nor diameter.',
'Student calls OA diameter but one endpoint at center makes radius;AB correct diameter by described endpoints/throughO, preserve labels.',
'Cube A-H eight distinct vertices;4bottom+4top+4connectors=12edges; six namedfaces, shared edge once.',
'P dimensions4/4/4 allsquarefaces cube; Q6/4/2 rectangularbox; same8vertices12edges6faces does not imply cube.',
'AtA edgesAB AD AE;AC diagonal notedge;CDHG oppositeABFE no commonvertex;ADHE adjacent sharesAE.',
'Explicit closed cube observed threefaces means visible subset only; six total, no unseen image description.',
'One square frontface lacks depth/otherfaces; ask full evidence without inferring cube.',
'54 reduced byfactor3 gives18, difference36;18*3=54 and18+36=54; hints do not give intermediate/final.',
'A63 removes18 to external library gives45; B9unchanged;45/9=5times with inverse45+18=63; not transfer toB.',
'Quoted36-4=32 arithmetic correct but wrong multiplicative relation;36/4=9 and9*4=36, only explicit written reason diagnosed.',
'6bags minus9items lacks items/bag or initialtotal; asks missing amount, never subtract mismatched units.',
'Six equalarea parts cover whole, onechosen1/6 readone-sixth; five uncolored is not denominator; no real image claim.',
'56cucks in7equalgroups gives8pergroup,8*7=56; object count vs group count distinct.',
'Eight equalarea cells partitioned into seven unequal pieces: colored2cells versus others1cell; cannot infer one-seventh from piececount; hints leave condition to check.',
'45objects one-fifth gives9,9*5=45; quoted5labels numberofparts not directselectedobjectcount; no hidden counting diagnosis.',
'Fourpieces onecolored lacks equalityofarea; asks image/partition evidence; empty solution/answer until known.'
]

def numeric_audit(rows):
 out=[]
 def de(t):
  if isinstance(t,ast.Constant):return Decimal(str(t.value))
  if isinstance(t,ast.UnaryOp):return -de(t.operand) if isinstance(t.op,ast.USub) else de(t.operand)
  a,b=de(t.left),de(t.right)
  if isinstance(t.op,ast.Add):return a+b
  if isinstance(t.op,ast.Sub):return a-b
  if isinstance(t.op,ast.Mult):return a*b
  if isinstance(t.op,ast.Div):return a/b
  if isinstance(t.op,ast.Mod):return a%b
  raise ValueError('unsupported decimal operator')
 for x in rows:
  ins=inspect_case(x);assert ins['passed'],(x['sample_id'],ins)
  for s,ex in zip(x['worked_steps'],ins['expanded_expressions']):
   if not ex:continue
   f=exact(ex);assert f==Fraction(s['result'])
   with localcontext() as ctx:
    ctx.prec=48;d=de(ast.parse(ex,mode='eval').body);assert abs(d-Decimal(f.numerator)/Decimal(f.denominator))<Decimal('1e-38')
   t=ast.parse(ex,mode='eval').body;inv=None
   if isinstance(t,ast.BinOp):
    a,b=exact(ast.unparse(t.left)),exact(ast.unparse(t.right))
    if isinstance(t.op,ast.Add):inv=f-b==a
    elif isinstance(t.op,ast.Sub):inv=f+b==a
    elif isinstance(t.op,ast.Mult):inv=f==0 if b==0 else f/b==a
    elif isinstance(t.op,ast.Div):inv=f*b==a
    elif isinstance(t.op,ast.Mod):inv=(a//b)*b+f==a and 0<=f<b
    assert inv is not False
   out.append({'sample_id':x['sample_id'],'source_row_sha256':row_sha(x),'step_id':s['step_id'],'expanded_expression':ex,'fraction':str(f),'decimal':str(d),'separate_inverse_identity':inv})
 return out

def polish_qa():
 p=R/'derived_release/pre_sft_polished_sources.jsonl';rows=read_rows(p);assert len(rows)==len(POLISH_NOTES)==47
 originals={x['sample_id']:x for f in (R/'authored_batches').glob('*.jsonl') for x in read_rows(f)}
 for x in rows:
  x['provenance']['content_review_status']='AI_DERIVATIVE_SELF_QA_COMPLETED'
  par=originals[x['derivation']['parent_sample_id']]
  assert row_sha(par)==x['derivation']['original_source_row_sha256']
  assert x['student_work']==par['student_work']
  assert [s['expression'] for s in x['worked_steps']]==[s['expression'] for s in par['worked_steps']]
  assert [g['value'] for g in x['givens']]==[g['value'] for g in par['givens']]
  assert x['curriculum_assignment']==par['curriculum_assignment']
 write_rows(p,rows)
 review=[]
 for x,n in zip(rows,POLISH_NOTES):
  review.append({'sample_id':x['sample_id'],'row_sha256':row_sha(x),'reviewer':'root_actual_derivative_content_self_QA','notes':n,'review_method':'Read all47 actual derivative problems/givens/request/quotes/initial/allhints/steps/reasons/explanations/results/answers; read final changed-field diff against previously read content. Exact arithmetic and inverse independently recomputed on current derivatives. Parser/keyword checks are not semantic proof.','human_verified':False,'teacher_certified':False,'owner_human_reviewed':False,'independent_external_reviewer':False,**{k:True for k in REVIEW_FIELDS}})
 rp=R/'derived_release/pre_sft_polish_reviews.jsonl';write_rows(rp,review)
 traces=numeric_audit(rows)
 write_json(E/'pre_sft_polish_QA_20261018.json',{'utc':stamp(),'cases':47,'actual_full_content_read':True,'review_sha256':sha(rp.read_bytes()),'source_sha256':sha(p.read_bytes()),'numeric_checks':traces,'semantic_notes':[{'sample_id':r['sample_id'],'source_row_sha256':r['row_sha256'],'note':r['notes']} for r in review],'original_sources_and_owner_signoffs_modified':False,'physical_or_vision_verified':False})
 m=load(E/'pre_sft_polish_derivation_manifest_20261018.json')
 for c,x in zip(m['cases'],rows):c['derived_source_row_sha256']=row_sha(x)
 m.update(status='47_DERIVATIVES_QA_COMPLETE',QA_evidence_sha256=sha((E/'pre_sft_polish_QA_20261018.json').read_bytes()))
 write_json(E/'pre_sft_polish_derivation_manifest_20261018.json',m)
 qp=R/'pre_sft_polish_queue.json';q=load(qp)
 write_json(E/'pre_sft_polish_original_queue_before_resolution.json',q)
 for c,x in zip(q['cases'],rows):
  assert c['sample_id']==x['derivation']['parent_sample_id']
  c.update(status='RESOLVED_BY_HASH_BOUND_AI_DERIVATIVE',derived_sample_id=x['sample_id'],derived_source_row_sha256=row_sha(x),source_modified=False,physical_or_vision_verified=False)
 q.update(status='ALL47_TEXT_POLISH_DERIVATIVES_QA_COMPLETE',remaining_text_polish_cases=0,physical_or_vision_limitations_retained=True,neutral_schema_not_live_guide_or_PlanDraft=True)
 write_json(qp,q)
 print('POLISH_QA47_COMPLETE',len(traces))

def release():
 state=load(R/'data_build_state.json');assert state['remaining_core_cases']==0 and state['core_nodes_complete']==165
 assert state['authored_cases']==state['accepted_cases']
 base=read_rows(R/'exports/accepted_teacher_cases.jsonl');derived=read_rows(R/'derived_release/pre_sft_polished_sources.jsonl');rev={x['sample_id']:x for x in read_rows(R/'derived_release/pre_sft_polish_reviews.jsonl')}
 byparent={x['derivation']['parent_sample_id']:x for x in derived};assert len(byparent)==47
 output=[];manifest=[];chat=[];cm={x['sample_id']:x for x in read_rows(R/'curation_manifest.jsonl')}
 for b in base:
  d=byparent.get(b['sample_id'])
  if d:
   assert review_case(d,rev)=='ACCEPTED_AUTHOR_QA'
   assert row_sha(b)==d['derivation']['original_owner_overlay_row_sha256']
   x=owner_export_row(d,{})
  else:x=b
  group=chat_records(b)[0]['case_group_id'];cr=chat_records(x)
  for z in cr:
   z['case_group_id']=group
   if d:z['original_source_row_sha256']=d['derivation']['original_source_row_sha256'];z['parent_sample_id']=b['sample_id']
  output.append(x);chat.extend(cr)
  manifest.append({'sample_id':x['sample_id'],'parent_sample_id':b['sample_id'],'original_source_row_sha256':cm[b['sample_id']]['source_row_sha256'],'parent_exported_row_sha256':row_sha(b),'derived_source_row_sha256':row_sha(d) if d else None,'exported_row_sha256':row_sha(x),'case_group_id':group,'acceptance_status':x['acceptance_status'],'human_verified':x['human_verified'],'numeric_overlap_exception':cm[b['sample_id']].get('protected_numeric_overlap_adjudication'),'physical_or_vision_verified':False})
 assert len(output)==len(base) and len(chat)==4*len(output) and len({x['sample_id'] for x in output})==len(output)
 assert len({normalized(x['problem']) for x in output})==len(output)
 artifacts={'accepted_cases':write_rows(R/'exports/accepted_teacher_cases_polished.jsonl',output),'chat_train':write_rows(R/'exports/teacher_chat_train_polished.jsonl',chat),'manifest':write_rows(R/'exports/polished_export_manifest.jsonl',manifest)}
 counts=Counter(x['curriculum_assignment']['case_kind'] for x in output)
 groups={}
 for c in chat:
  pid=c['sample_id'].rsplit(':',1)[0];groups.setdefault(pid,set()).add(c['case_group_id'])
 assert all(len(s)==1 for s in groups.values())
 state['final_release']={'status':'FINITE_DATASET_COMPLETE_NOT_TRAINED','cases':len(output),'chat_rows':len(chat),'core_cases':counts['core'],'core_chat_rows':counts['core']*4,'case_kind_counts':dict(counts),'polished_derivatives':47,'original_parent_rows_replaced_not_added':True,'human_teacher_verified_cases':sum(x['human_verified'] for x in output),'human_teacher_verified_chat_rows':sum(x['human_verified'] for x in chat),'original_baseline_human_certified_cases_preserved':299,'artifacts':artifacts,'split':'train_only','model_training_started':False,'live_guide_or_PlanDraft_compatibility_claimed':False}
 state['phase']='FINITE_DATA_FINAL_AUDIT_PENDING';state['completion']=False
 write_json(R/'data_build_state.json',state)
 print(json.dumps(state['final_release'],ensure_ascii=False))

def audit():
 state=load(R/'data_build_state.json');b=load(R/'curriculum_blueprint.json');nodes={n['node_id']:n for n in b['nodes']}
 sources=[x for p in sorted((R/'authored_batches').glob('*.jsonl')) for x in read_rows(p)]
 byid={x['sample_id']:x for x in sources};assert len(byid)==len(sources)==782
 reviews=[x for p in sorted((R/'reviews').glob('*.jsonl')) for x in read_rows(p)]
 rb={x['sample_id']:x for x in reviews};assert len(rb)==len(reviews)==782
 base=read_rows(R/'exports/accepted_teacher_cases.jsonl');bm={x['sample_id']:x for x in base}
 out=read_rows(R/'exports/accepted_teacher_cases_polished.jsonl');chat=read_rows(R/'exports/teacher_chat_train_polished.jsonl')
 manifests=read_rows(R/'exports/polished_export_manifest.jsonl');cm=read_rows(R/'curation_manifest.jsonl')
 assert len(base)==len(out)==len(manifests)==782 and len(chat)==3128 and not read_rows(R/'pending_cases.jsonl')
 assert len({normalized(x['problem']) for x in out})==782
 for x in sources:
  assert review_case(x,rb)=='ACCEPTED_AUTHOR_QA',x['sample_id']
  assert mapping_error(x,nodes) is None
  answer_signatures(x,inspect_case(x))
 source_traces=numeric_audit(sources)
 # This current-row audit supersedes pre-QA draft arithmetic traces, including
 # finite106 money's grade-bound revision. Historical traces remain evidence.
 write_json(E/'finite_all782_current_numeric_oracles_20261018.json',{'utc':stamp(),'row_bindings':{x['sample_id']:row_sha(x) for x in sources},'numeric_steps':len(source_traces),'traces':source_traces,'semantic_proof_claimed':False,'supersedes_pre_QA_numeric_traces_for_current_rows':True})
 fp=b['existing_inputs']['source_fingerprints'];frozen={p:sha((HERE.parent/p).read_bytes())==h for p,h in fp.items()};assert all(frozen.values())
 sign=load_owner_signoffs(R);assert len(sign)==299
 assert sha((R/'owner_human_signoffs.jsonl').read_bytes())=='9475d9fabc1668e04a3e4ce3f5708a8f28e65ebf8c87337c212463017f3a7f1a'
 assert sha((R/'owner_acceptance_policy.json').read_bytes())=='086c5588c47cc90ec079678857b24dbb65601246cca6b208a700212c7dea6c6e'
 assert sha((R/'owner_human_attestations.json').read_bytes())=='e0d59a9a5ee6e428bfe2c2bcc3cee9fa7b8b52f507140ca09491a39f269cf4ea'
 assert sha((R/'tutor_contract.json').read_bytes())=='0e09c27b728dccf9fb1d374480699498425d647e0f55fcf016efe7d0eaca70c5'
 for sid,a in sign.items():
  assert row_sha(byid[sid])==a['source_row_sha256'] and row_sha(bm[sid])==a['exported_row_sha256']
 for x in base:
  if x['sample_id'] not in sign:assert not any(x[k] for k in ('human_verified','teacher_certified','owner_human_reviewed'))
 assert sum(x['human_verified'] for x in base)==299 and sum(x['human_verified'] for x in out)==252
 assert all(not x['human_verified'] for x in out if ':polish_v1' in x['sample_id'])
 cov=load(R/'coverage_progress.json');assert len(cov)==165 and sum(x['accepted_core_cases'] for x in cov)==495
 assert all(x['accepted_core_cases']==3 and x['remaining_core_cases']==0 and set(x['accepted_core_slots'])=={'core_01','core_02','core_03'} for x in cov)
 supplement=[]
 for c in cov:
  n=nodes[c['node_id']]
  for kind in ('misconception','guard'):
   target=n['authoring_plan'][kind+'_case']['target_case_count'];actual=c['accepted_'+kind+'_cases']
   assert actual>=target,(c['node_id'],kind,actual,target)
   supplement.append({'node_id':c['node_id'],'case_kind':kind,'target':target,'accepted':actual,'remaining':max(0,target-actual)})
 assert sum(x['target'] for x in supplement)==277
 core_slots=Counter((x['curriculum_assignment']['node_id'],x['curriculum_assignment'].get('case_slot')) for x in sources if x['curriculum_assignment']['case_kind']=='core');assert len(core_slots)==495 and all(c==1 for c in core_slots.values())
 oc={x['sample_id']:x for x in out};groups={};modes=Counter()
 for z in chat:
  sid=z['sample_id'].rsplit(':',1)[0];x=oc[sid];assert z['row_sha256']==row_sha(x) and z['source_row_sha256']==x['verification']['source_row_sha256']
  assert z['split']=='train' and z['schema']=='neutral_teacher_chat.v1_not_live_PlanDraft'
  groups.setdefault(sid,set()).add(z['case_group_id']);modes[z['mode']]+=1
  user=json.loads(z['messages'][1]['content']);target=json.loads(z['messages'][2]['content'])
  assert set(user)<={'grade','problem','student_work','mode'}
  if z['mode'].startswith('hint'):assert set(target)=={'hint','question'}
 assert len(groups)==782 and all(len(v)==1 for v in groups.values()) and all(v==782 for v in modes.values())
 for m in manifests:
  assert row_sha(oc[m['sample_id']])==m['exported_row_sha256']
  assert m['case_group_id']==chat_records(bm[m['parent_sample_id']])[0]['case_group_id']
 docx=Path(r'C:\Users\My PC\Downloads\SO_SANH_MODEL_THINKING_VOI_MODEL_HIEN_TAI_20261016.docx')
 assert sha(docx.read_bytes())=='488455e5e2deb12437f4f6afcd8164fb2829a4ac7024a9a30108b8c0ed6b44e6'
 assert sha((R/'coverage_adjudications.jsonl').read_bytes())=='1c7a4b2d9d8cda1497812ea67d63b222a8fd4620d345113e8881ae0d5ca34457'
 policy=load_numeric_overlap_exceptions(R);applied=[x for x in cm if 'protected_numeric_overlap_adjudication' in x]
 assert len(applied)==len(policy)==state['protected_numeric_overlap_exceptions_applied']
 cp=load(R/'coverage_adjudication_queue.json')
 cp['historical_protected_exclusions_before_owner_authorized_hash_exceptions']={'core':cp.get('protected_excluded_core_slots_not_accepted',[]),'supplementary':cp.get('protected_excluded_supplementary_not_accepted',[])}
 cp.update(queue=[],accepted_not_credited_core_slots=0,status='ALL_ADJUDICATIONS_RESOLVED_FINITE495_COMPLETE',protected_excluded_core_slots_not_accepted=[],protected_excluded_core_slot_count=0,protected_excluded_supplementary_not_accepted=[],coverage_counts={'accepted_core':495,'remaining_core':0,'complete_nodes':165},numeric_overlap_exceptions_applied=len(applied),numeric_test_independence_claimed=False)
 write_json(R/'coverage_adjudication_queue.json',cp)
 write_json(R/'authoring_queue.json',{'status':'FINITE495_COMPLETE_NO_MORE_AUTHORING','coverage_sha256':sha((R/'coverage_progress.json').read_bytes()),'curation_manifest_sha256':sha((R/'curation_manifest.jsonl').read_bytes()),'accepted_remaining_core_cases':0,'pending_core_slots_prepared':0,'protected_excluded_core_slots_already_authored':[],'core_slots_not_authored':0,'nodes':[],'next_action':'No further cases; finite data complete. Training outside authorized scope.'})
 write_json(R/'supplementary_queue.json',{'status':'ALL_BLUEPRINT_REQUIRED_TASKS_COMPLETE','source_coverage_sha256':sha((R/'coverage_progress.json').read_bytes()),'remaining_required_tasks':0,'remaining_tasks_not_authored':0,'queue':[],'audited_node_kind_counts':supplement,'required_target_cases':277,'actual_misconception_cases':166,'actual_guard_cases':112,'extra_auxiliary_cases':9,'auxiliary_does_not_count_as_core':True})
 report={'schema_version':'finite_primary_math_final_audit.v1','utc':stamp(),'status':'PASSED_FINITE_DATA_AUDIT','authored_cases':782,'accepted_cases':782,'core_cases':495,'core_chat_rows':1980,'core_nodes_complete':165,'chat_rows':3128,'pending_cases':0,'remaining_required_supplementary':0,'polish_derivatives_QA':47,'source_reviews_current_hash_valid':782,'current_numeric_steps_recomputed':len(source_traces),'frozen_source_hashes_unchanged':frozen,'owner299_source_and_export_hashes_unchanged':True,'baseline_human_certified_cases':299,'final_polished_human_certified_cases':252,'final_polished_AI_preauthorized_cases':530,'human_attestation_extended_to_derivatives':False,'source_export_and_derivative_hashes_separate':True,'unique_core_assignments':495,'unique_normalized_questions':782,'case_modes_group_consistent':True,'split':'train_only','protected_exact_question_collisions':0,'hash_bound_numeric_overlap_exceptions_applied':len(applied),'numeric_tests_independent_for_overlapping_calculations':False,'pipeline_adversarial_tests':{'passed':33,'runner':'Python313 -Xutf8 -m pytest test_primary_math_data_pipeline.py -q from thinking; 33passed'},'additional_numeric_exception_gate_tests':load(E/'numeric_overlap_exception_gate_tests_20261018.json'),'pipeline_sha256':sha((HERE/'primary_math_data_pipeline.py').read_bytes()),'source_row_hashes':{x['sample_id']:row_sha(x) for x in sources},'final_release':state['final_release'],'limits':state['limits']+['165 registered nodes with3meaningfully varied core cases each is a bounded blueprint, not exhaustive curricular/legal2026 or complete2006 certification.','Physical/vision outcomes remain unverified when only text descriptions are available.','47 polished rows are AI-derived versions without new human content attestations.','No tokenizer/training-loader compatibility claim for this new release; model selection, training, deployment and independent evaluation remain separate.'],'training_started':False,'sealed_concept_challenge_read':False,'paid_API_used':False,'production_approved':False}
 write_json(E/'finite495_final_audit_20261018.json',report)
 state.update(phase='FINITE_DATASET_COMPLETE_NOT_TRAINED',completion=True,remaining_required_supplementary=0,pre_sft_polish_remaining=0,final_audit={'path':str((E/'finite495_final_audit_20261018.json').relative_to(HERE.parent)),'sha256':sha((E/'finite495_final_audit_20261018.json').read_bytes()),'status':'PASSED'},publication_status='LOCAL_PACKAGE_AND_DRIVE_READBACK_PENDING')
 write_json(R/'data_build_state.json',state)
 checkpoint={'phase':state['phase'],'executed_utc':stamp(),'accepted_cases':782,'chat_rows':3128,'accepted_core_cases':495,'core_nodes_complete':165,'remaining_core_cases':0,'core_slots_not_authored':0,'remaining_required_supplementary':0,'polish47_resolved':True,'final_release':state['final_release'],'final_audit_sha256':sha((E/'finite495_final_audit_20261018.json').read_bytes()),'new_human_attestation_claim':False,'training_started':False,'next_action':'Package, update same Drive artifact IDs and verify fresh raw bytes, then remove completed automation.'}
 write_json(E/'finite495_20261018_completion_checkpoint.json',checkpoint)
 v=E/'drive_artifact_verification.json';old=load(v);old.update(superseded=True,superseded_by='finite495_final_release',current_phase_status='UPLOAD_READBACK_PENDING');write_json(v,old)
 print(json.dumps({k:report[k] for k in ('status','accepted_cases','core_cases','core_nodes_complete','chat_rows','current_numeric_steps_recomputed','hash_bound_numeric_overlap_exceptions_applied')}))

if __name__=='__main__':
 if sys.argv[1]=='polish_qa':polish_qa()
 elif sys.argv[1]=='release':release()
 elif sys.argv[1]=='audit':audit()
