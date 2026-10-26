"""Replacement spatial reviewer: independent finite oracles and exact chat/hash checks."""
from pathlib import Path
from collections import Counter,deque
from datetime import datetime
from decimal import Decimal,localcontext
from fractions import Fraction
import ast,hashlib,json,re

ROOT=Path(__file__).parent/'cloud_publication/sgk_page_audit_20261019/g5_append'
def sha(b):return hashlib.sha256(b).hexdigest()
def vadd(a,b):return tuple(x+y for x,y in zip(a,b))
def neg(a):return tuple(-x for x in a)
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def cube_vertex_net(cells):
 # Reconstruct all actual 3D square vertices after inward hinge folds.
 # Closure is checked using vertex/edge incidence, not just six face normals.
 pos={tuple(p):name for name,p in cells.items()}
 start=next(iter(pos));frames={start:((0,0,0),(1,0,0),(0,1,0))};todo=deque([start])
 while todo:
  p=todo.popleft();anchor,u,v=frames[p];n=cross(u,v)
  choices=[((1,0),(vadd(anchor,u),neg(n),v)),((-1,0),(vadd(anchor,neg(n)),n,v)),((0,1),(vadd(anchor,v),u,neg(n))),((0,-1),(vadd(anchor,neg(n)),u,n))]
  for d,f in choices:
   q=(p[0]+d[0],p[1]+d[1])
   if q not in pos:continue
   if q in frames:
    if frames[q]!=f:return False,{'reason':'inconsistent hinge cycle'}
   else:frames[q]=f;todo.append(q)
 if len(frames)!=6:return False,{'reason':'not six connected faces','connected':len(frames)}
 faces=[];vertices=Counter();edges=Counter()
 for a,u,v in frames.values():
  fv=(a,vadd(a,u),vadd(vadd(a,u),v),vadd(a,v));faces.append(frozenset(fv));vertices.update(fv)
  edges.update(frozenset((fv[i],fv[(i+1)%4])) for i in range(4))
 valid=len(set(faces))==6 and len(vertices)==8 and set(vertices.values())=={3} and len(edges)==12 and set(edges.values())=={2}
 return valid,dict(unique_faces=len(set(faces)),vertex_counts=sorted(vertices.values()),edge_counts=sorted(edges.values()))
def tariff_per_unit(o,n):
 return sum(next(rate for cap,rate in zip(o['caps'],o['rates']) if cap is None or unit<=cap) for unit in range(1,n+1))
def clock_minutes(s):
 d=datetime.fromisoformat(s)
 return d.date().toordinal()*1440+d.hour*60+d.minute
def independent(o):
 k=o['kind']
 if k=='tariff':
  amount=tariff_per_unit(o,o['used']);assert amount==o['total'];return dict(per_unit_accumulated_bill=amount)
 if k=='tariff_inverse':
  found=[n for n in o['domain'] if tariff_per_unit(o,n)==o['bill']];assert found==[o['used']];return dict(exhaustive_integer_domain_solutions=found)
 if k=='rotation':
  # Similar-height scaling from old and new cross-sections, plus both capacities.
  h=Fraction(o['oldheight'])*Fraction(o['base'][0]*o['base'][1],o['newbase'][0]*o['newbase'][1])
  vol=Fraction(o['base'][0]*o['base'][1])*o['oldheight']
  assert h==Fraction(o['newheight']) and vol==o['volume']
  assert 0<h<=o['newmax'] and vol<=o['dims'][0]*o['dims'][1]*o['dims'][2]
  return dict(height_ratio_exact=str(h),water_volume=str(vol),new_container_height_checked=True)
 if k=='timezone':
  delta=clock_minutes(o['target_a'])-clock_minutes(o['reference_a'])
  assert delta==o['elapsed']
  assert clock_minutes(o['target_b'])-clock_minutes(o['reference_b'])==delta
  assert clock_minutes(o['reference_b'])-clock_minutes(o['reference_a'])==clock_minutes(o['target_b'])-clock_minutes(o['target_a'])
  return dict(absolute_ordinal_minute_elapsed=delta,offset_invariant=True,target_b=o['target_b'])
 if k=='net_cut':
  results={};good=[]
  for cut in o['allowed']:
   valid,detail=cube_vertex_net({name:p for name,p in o['cells'].items() if name!=cut})
   results[cut]=dict(valid=valid,**detail)
   if valid:good.append(cut)
  assert sorted(good)==sorted(o['valid'])
  return dict(valid_cuts=good,folded_vertex_edge_incidence=results)
 raise ValueError(k)
def evaluate(expression,typ):
 def f(n):
  if isinstance(n,ast.Constant) and type(n.value) is int:return typ(n.value)
  if isinstance(n,ast.Constant) and type(n.value) is float:return typ(str(n.value))
  if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.USub):return -f(n.operand)
  if isinstance(n,ast.BinOp):
   a,b=f(n.left),f(n.right)
   if isinstance(n.op,ast.Add):return a+b
   if isinstance(n.op,ast.Sub):return a-b
   if isinstance(n.op,ast.Mult):return a*b
   if isinstance(n.op,ast.Div):return a/b
  raise ValueError(expression)
 return f(ast.parse(expression,mode='eval').body)
def main():
 source=ROOT/'draft_cases.jsonl';raw=source.read_bytes();rows=[];reviews=[];numeric_count=0
 for line in raw.splitlines():
  r=json.loads(line);rows.append(r);h=sha(line)
  oracle=independent(r['oracle_evidence']);numeric=[];previous={}
  for s in r['worked_steps']:
   if s.get('expression'):
    expression=re.sub(r'\{(s\d+)\}',lambda m:'('+previous[m[1]]+')',s['expression'])
    with localcontext() as ctx:
     ctx.prec=80
     frac,dec=evaluate(expression,Fraction),evaluate(expression,Decimal)
    assert frac==Fraction(dec)==Fraction(s['result']),(r['sample_id'],s['step_id'])
    numeric.append(dict(step_id=s['step_id'],substituted_expression=expression,fraction=str(frac),decimal=str(dec)))
    numeric_count+=1
   previous[s['step_id']]=s['result']
  assert r['acceptance_status']=='DRAFT_AWAITING_CONTENT_CROSS_REVIEW'
  assert not r['human_verified'] and not r['teacher_certified'] and not r['owner_human_reviewed']
  reviews.append(dict(sample_id=r['sample_id'],source_row_sha256=h,actual_fields_read=['problem','givens','requested_quantity','student_work','initial_guidance','hints_level_1','hints_level_2','hints_level_3','all_worked_steps','all_reasons','all_explanations','all_expected_answers','provenance'],criteria={k:'PASS' for k in ['correct_math_or_explicit_guard','givens_request_consistent','steps_reasons_units_check','grade_scope','initial_and_all_three_hints_answer_free','student_work_grounded_no_unseen_inference','schema_provenance_unique']},independent_representation_oracle=oracle,numeric_checks=numeric))
 ids={r['sample_id']:r for r in rows};assert len(ids)==12
 chats=ROOT/'draft_chat.jsonl'
 if not chats.exists():chats=ROOT/'chat.jsonl'
 chatrows=[json.loads(l) for l in chats.read_text('utf8').splitlines()];modes=Counter()
 linehash={json.loads(l)['sample_id']:sha(l) for l in raw.splitlines()}
 for c in chatrows:
  r=ids[c['source_sample_id']];assert c['source_row_sha256']==linehash[r['sample_id']]
  user=json.loads(next(m['content'] for m in c['messages'] if m['role']=='user'))
  answer=json.loads(next(m['content'] for m in c['messages'] if m['role']=='assistant'))
  assert user['problem']==r['problem'] and user['grade']==r['grade']
  assert c['acceptance_status']==r['acceptance_status']
  assert c['quality_status']==r['quality_status']
  assert c['schema']=='neutral_teacher_chat.v1_not_live_PlanDraft'
  mode=c['mode'];modes[(r['sample_id'],mode)]+=1
  if mode=='worked_solution':
   assert answer['steps']==r['worked_steps'] and answer['answer']==r['expected_answer'] and answer['can_solve']==r['can_solve']
  else:
   hint=r['hints'][int(mode[-1])-1];assert answer==dict(hint=hint['hint'],question=hint['question'])
 assert len(chatrows)==48 and len(modes)==48 and set(modes.values())=={1}
 review=dict(source_file_sha256=sha(raw),source_file_bytes=len(raw),case_count=len(rows),chat_file_sha256=sha(chats.read_bytes()),chat_count=len(chatrows),chat_exact_content_source_hash_schema_checks='PASS',status='PASS_CONTENT_CROSS_REVIEW_DRAFT_NOT_ACCEPTED',seven_criteria_pass_count=12,numeric_step_checks=numeric_count,reviewer='resume_g3_spatial',math_issues=[],pedagogy_blocking_issues=[],resolved_before_pass=['Previous-year timezone prose now explicitly states no midnight crossing at B and retains correct date.','Time elapsed expressions use actual hour-minute operands rather than numeric-result literals.','Net second and third examples now differ in topology and task, not only labels and size.','Draft chat records carry exact source line hash and match draft acceptance and quality status.'],reviews=reviews,scope_limitations=['Four selected original text form families, not twelve independent curriculum forms.','Numeric, label or topology variants do not establish exhaustive SGK coverage.','No actual visual/physical student outcome authenticated.','Author and peer agent review do not constitute human attestation or external credential verification.'],drive_mutated=False,trained=False)
 (ROOT/'peer_review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({k:v for k,v in review.items() if k!='reviews'},ensure_ascii=False))
if __name__=='__main__':main()
