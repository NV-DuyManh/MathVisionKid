import json,sys,ast,re
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
from fractions import Fraction
from decimal import Decimal
sys.path.insert(0,str(Path(__file__).resolve().parent))
from primary_math_data_pipeline import *
AUTHOR_AGENT='root'
R=DEFAULT_ROOT; E=HERE/'evidence/primary_math_teacher_20261016'
B=json.loads((R/'curriculum_blueprint.json').read_text('utf-8')); N={x['node_id']:x for x in B['nodes']}
T=read_rows(R/'authored_batches/g5_fraction_operations_0071.jsonl')[0]
def make(node_id, batch, specs, supports):
 n=N[node_id]; dest=R/('authored_batches/'+batch+'.jsonl');assert not dest.exists(),dest
 occupied={(x['curriculum_assignment']['node_id'],x['curriculum_assignment'].get('case_slot')) for f in (R/'authored_batches').glob('*.jsonl') for x in read_rows(f) if x['curriculum_assignment']['case_kind']=='core'}
 rows=[]
 for i,z in enumerate(specs):
  kind=z.get('kind','core');slot=z.get('slot','core_'+str(i+1).zfill(2)) if kind=='core' else None
  if kind=='core':assert (node_id,slot) not in occupied
  a={'node_id':node_id,'curriculum_scope':n['curriculum_scope'],'case_kind':kind}
  if kind=='core':a.update({k:next(c for c in n['authoring_plan']['core_cases'] if c['case_slot']==slot)[k] for k in ['case_slot','context_variant','method_variant']})
  sid='primary_20261018_'+batch+'_'+z['id'];p=deepcopy(T['provenance']);p.update({'authoring_agent':AUTHOR_AGENT,'source_evidence':n['source_evidence'],'student_work_origin':'EXPLICITLY_SYNTHETIC' if z.get('student') else None,'modality_evidence':'ORIGINAL_TEXT_OR_EXPLICIT_HYPOTHETICAL_DESCRIPTION_NO_REAL_ACTIVITY_CLAIM'})
  if n['required_modality']!='text':p['visual_asset_status']='PENDING_ACTUAL_IMAGE_OR_PHYSICAL_EVIDENCE'
  st=[]
  for j,(title,reason,result,explanation,expression,unit) in enumerate(z.get('steps',[])):st.append({'step_id':'s'+str(j),'title':title,'reason':reason,'result':str(result),'explanation':explanation,'expression':expression,'unit':unit})
  hs=z.get('hints',supports)
  sw={'text':z['student'],'observations':[{'excerpt':z['student'],'claim_scope':'Explicit synthetic written evidence only; no hidden reasoning or unseen image inferred.'}]} if z.get('student') else None
  row={'sample_id':sid,'case_group_id':sid,'split':'train','grade':n['grade'],'topic':z['id'],'problem':z['q'],'givens':[{'id':'g'+str(j),'text':t,'value':v,'unit':u,'role':'explicit_given_'+str(j)} for j,(t,v,u) in enumerate(z['g'])],'requested_quantity':z['request'],'student_work':sw,'initial_guidance':z.get('initial',[hs[0][0]]),'hints':[{'level':j+1,'hint':h,'question':q} for j,(h,q) in enumerate(hs)],'worked_steps':st,'expected_answer':[{'quantity':q,'result':str(v),'unit':u} for q,v,u in z.get('answers',[])],'can_solve':kind!='guard','canonical_case':{'family':z.get('family',z['id']),'operations':z.get('ops',[]),'numeric_values':[v for t,v,u in z['g'] if v is not None]},'curriculum_assignment':a,'provenance':p,'quality_flags':deepcopy(T['quality_flags'])|{'historical_topic_only_not_complete_2006_curriculum':node_id.startswith('old_')}}
  assert inspect_case(row)['passed'],(sid,inspect_case(row));assert mapping_error(row,N) is None
  rows.append(row)
 write_rows(dest,rows)
 exact_rows=[]
 for row in rows:
  ins=inspect_case(row)
  for step,expr in zip(row['worked_steps'],ins['expanded_expressions']):
   if not expr:continue
   f=exact(expr);assert f==Fraction(step['result'])
   def decimal_eval(t):
    if isinstance(t,ast.Constant):return Decimal(str(t.value))
    a=decimal_eval(t.left);b=decimal_eval(t.right)
    if isinstance(t.op,ast.Add):return a+b
    if isinstance(t.op,ast.Sub):return a-b
    if isinstance(t.op,ast.Mult):return a*b
    if isinstance(t.op,ast.Div):return a/b
    if isinstance(t.op,ast.Mod):return a%b
    raise ValueError('unsupported')
   d=decimal_eval(ast.parse(expr,mode='eval').body);assert abs(d-Decimal(f.numerator)/Decimal(f.denominator))<Decimal('1e-24')
   tree=ast.parse(expr,mode='eval').body;inverse=None
   if isinstance(tree,ast.BinOp):
    a=exact(ast.unparse(tree.left));bb=exact(ast.unparse(tree.right))
    if isinstance(tree.op,ast.Add):inverse=f-bb==a
    elif isinstance(tree.op,ast.Sub):inverse=f+bb==a
    elif isinstance(tree.op,ast.Mult):inverse=(bb==0 and f==0) or (bb!=0 and f/bb==a)
    elif isinstance(tree.op,ast.Div):inverse=f*bb==a
    elif isinstance(tree.op,ast.Mod):inverse=a//bb*bb+f==a and 0<=f<bb
    assert inverse is not False
   exact_rows.append({'sample_id':row['sample_id'],'step_id':step['step_id'],'expression':expr,'fraction':str(f),'decimal':str(d),'inverse_identity':inverse})
 write_json(E/(batch+'_pre_review.json'),{'batch':batch,'utc':datetime.now(timezone.utc).isoformat(),'rows':[{'sample_id':x['sample_id'],'row_sha256':row_sha(x),'parser':inspect_case(x)} for x in rows],'exact_fraction_decimal_and_separate_inverse_oracles':exact_rows,'actual_semantic_content_read':False,'arithmetic_is_not_semantic_proof':True,'human_verified':False,'teacher_certified':False,'training_started':False})
 hint_dictionary={sha(json.dumps(x['hints'],ensure_ascii=False,sort_keys=True).encode()):x['hints'] for x in rows}
 print('ACTUAL_SHARED_HINT_DICTIONARY',json.dumps(hint_dictionary,ensure_ascii=False))
 for x in rows:print(json.dumps([x['sample_id'],x['problem'],[(g['text'],g['value'],g['unit']) for g in x['givens']],x['requested_quantity'],x['student_work'],x['initial_guidance'],{'hints_ref':sha(json.dumps(x['hints'],ensure_ascii=False,sort_keys=True).encode())},[(t['title'],t['reason'],t['result'],t['explanation'],t['expression'],t['unit']) for t in x['worked_steps']],x['expected_answer'],x['can_solve'],x['curriculum_assignment']],ensure_ascii=False))
 return rows

def review(batch,notes):
 rows=read_rows(R/('authored_batches/'+batch+'.jsonl'));assert len(rows)==len(notes)
 p=R/('reviews/'+batch+'_owner_preauthorized_self_QA.jsonl');assert not p.exists()
 method='Current named author agent actually read every printed problem/givens/request/student evidence/initial/all steps/reasons/explanations/answers and full actual shared hint dictionary with per-row hash bindings; exact Fraction and Decimal plus separate inverse identities, semantic given-role/unit/grade/operation/hint checks per row. Same-author QA under standing authorization, not human or independent review; historical scope and physical limitations retained.'
 out=[]
 for x,note in zip(rows,notes):
  assert inspect_case(x)['passed']
  out.append({'sample_id':x['sample_id'],'row_sha256':row_sha(x),'reviewer':AUTHOR_AGENT+'_author_self_QA_under_owner_standing_authorization','reviewer_runtime':'Codex Desktop current author session','review_method':method,'notes':note,'acceptance_route':'ACCEPTED_OWNER_PREAUTHORIZED','owner_acceptance_policy':'thinking/data/primary_math_teacher_20261016/owner_acceptance_policy.json','owner_approved_for_data_preparation':True,'human_verified':False,'teacher_certified':False,'owner_human_reviewed':False,'independent_external_reviewer':False,'new_human_review_claim':False,'production_approved':False,'training_started':False,**{k:True for k in REVIEW_FIELDS}})
 write_rows(p,out);ep=E/(batch+'_pre_review.json');ev=json.loads(ep.read_text('utf-8'));ev.update({'actual_semantic_content_read':True,'official_review_sha256':sha(p.read_bytes()),'review_method':method});write_json(ep,ev)
 print(json.dumps({'batch':batch,'reviewed':len(out),'source_sha256':sha((R/('authored_batches/'+batch+'.jsonl')).read_bytes()),'review_sha256':sha(p.read_bytes())}))


def adjudicate_numeric_overlaps(tag):
 policy=R/'numeric_overlap_exception_policy.json';assert json.loads(policy.read_text('utf-8'))['owner_authorized'] is True
 old=read_rows(R/'numeric_overlap_exceptions.jsonl') if (R/'numeric_overlap_exceptions.jsonl').exists() else []
 existing={x['sample_id']:x for x in old};protected,questions,_=protections()
 reviews={x['sample_id']:x for f in (R/'reviews').glob('*.jsonl') for x in read_rows(f)}
 cases=[]
 import teacher_math_data_v4 as v4
 for w in read_rows(R/'pending_cases.jsonl'):
  row=w['row'];ins=inspect_case(row)
  if w['decision']['status']!='PROTECTED_DEVELOPMENT_CASE_COLLISION':continue
  if normalized(row['problem']) in questions:continue
  assert ins['passed'] and review_case(row,reviews)=='ACCEPTED_AUTHOR_QA'
  assert row['provenance']['authoring_label']=='AI_GENERATED'
  matches=[expr for expr in ins['expanded_expressions'] if expr and v4.digest(v4.canonical_expression(expr)) in protected]
  cases.append({'sample_id':row['sample_id'],'source_row_sha256':row_sha(row),'question_exact_collision':False,'own_matching_expressions':matches,'current_review_row_sha256':reviews[row['sample_id']]['row_sha256'],'same_author_QA_notes':reviews[row['sample_id']]['notes'],'numeric_test_independence_claimed':False,'authorization':'Explicit direct owner reply authorizes per-hash exceptions after QA; not evidence of human content review.','semantic_non_equivalence_to_unread_protected_content_proven':False})
 if not cases:return
 ep=E/(tag+'_numeric_overlap_adjudication.json');assert not ep.exists();write_json(ep,{'utc':datetime.now(timezone.utc).isoformat(),'policy_sha256':sha(policy.read_bytes()),'cases':cases,'sealed_concept_challenge_read':False,'protected_questions_disclosed':False,'frozen_sources_modified':False,'source_answers_modified':False,'acceptance_basis':'OWNER_AUTHORIZED_NUMERIC_OVERLAP_EXCEPTION_AFTER_SELF_QA','limitations':'Exact numeric overlap remains. Do not claim these numeric tests independently evaluate the overlapping calculations. No claim of semantic non-equivalence to unread protected content.'})
 for c in cases:
  assert c['sample_id'] not in existing
  old.append({'sample_id':c['sample_id'],'source_row_sha256':c['source_row_sha256'],'policy_sha256':sha(policy.read_bytes()),'evidence_path':str(ep.relative_to(HERE.parent)),'evidence_sha256':sha(ep.read_bytes()),'numeric_test_independence_claimed':False,'new_human_review_claim':False})
 write_rows(R/'numeric_overlap_exceptions.jsonl',old);print('HASH_BOUND_NUMERIC_EXCEPTIONS',len(cases))


def C(id,q,g,request,steps,answers,student=None,kind='core',ops=None,hints=None):
 z={'id':id,'q':q,'g':g,'request':request,'steps':steps,'answers':answers,'kind':kind}
 if student:z['student']=student
 if ops is not None:z['ops']=ops
 if hints is not None:z['hints']=hints
 return z

def S(title,why,result,check,expr=None,unit=''):
 return (title,why,str(result),check,expr,unit)

def H(a,b,c):
 return [(a,'Em nhận ra dữ kiện và quan hệ cần dùng như thế nào?'),(b,'Em thực hiện theo quan hệ đó với đúng đơn vị ra sao?'),(c,'Em kiểm kết quả và đối chiếu điều được hỏi thế nào?')]
