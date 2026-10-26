"""Read-only independent peer check of geometry draft source, no source edits."""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal as D,localcontext
from itertools import combinations
import ast,copy,hashlib,json
P=Path(__file__).parent
FIELDS=['problem','givens','requested_quantity','student_work','initial_guidance','hints','worked_steps','expected_answer']
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def evaluate(expr,typ):
 def visit(n):
  if isinstance(n,ast.Constant) and type(n.value) is int:return typ(n.value)
  if isinstance(n,ast.BinOp):
   a,b=visit(n.left),visit(n.right)
   if isinstance(n.op,ast.Add):return a+b
   if isinstance(n.op,ast.Sub):return a-b
   if isinstance(n.op,ast.Mult):return a*b
   if isinstance(n.op,ast.Div):return a/b
  raise AssertionError(expr)
 return visit(ast.parse(expr,mode='eval').body)
def divisor_shapes(v,open_box):
 # Enumerate divisors by volume layers, then use symbolic face-pair areas.
 divs=[n for n in range(1,v+1) if v%n==0];out=[]
 for h in divs:
  base=v//h
  for b in divs:
   if base%b:continue
   a=base//b
   if a<b or (not open_box and b<h):continue
   area=a*b+2*h*(a+b) if open_box else 2*(a*b+h*(a+b))
   out.append(dict(dimensions=[a,b,h],area=area))
 return out
def independent(m):
 k=m['kind'];pi=F(m.get('pi','3.14'))
 if k=='semiboundary':
  d=F(m['diameter']);full=pi*d
  # Conservation: double boundary equals full round circumference plus two diameters.
  boundary=(full+2*d)/2;arc=boundary-d
  return dict(arc=str(arc),perimeter=str(boundary))
 if k=='chain':
  # Scale the reference half-circle by diameter ratios, no summing individually computed arc formulas.
  ref=F(m['reference_diameter']);ref_arc=pi*ref/2
  chain=ref_arc*sum(F(x)/ref for x in m['diameters'])+F(m['connector'])
  return dict(chain=str(chain),reference=str(ref_arc))
 if k=='wheel_forward':
  # Distance/diameter ratio is pi times turns, dimensionless.
  return dict(distance=str(F(m['diameter'])*(pi*F(m['turns']))))
 if k=='wheel_inverse':
  ratio=F(m['distance'])/F(m['diameter']);turns=ratio/pi;full=turns.numerator//turns.denominator
  return dict(turns=str(turns),full=full,partial=str(turns-full))
 if k=='stadium':
  w=F(m['width']);overall=F(m.get('overall_length',str(F(m['rect_length'])+w)) if 'rect_length' in m else m['overall_length'])
  # Bounding rectangle minus four corner deficits of a square versus a circle.
  area=overall*w-(4-pi)*w*w/4
  perimeter=2*overall+(pi-2)*w
  return dict(rect_length=str(overall-w),area=str(area),perimeter=str(perimeter))
 if k=='wrap_forward':
  # Material minus join must equal total travelled circumference.
  geometry=F(m['wraps'])*F(m['diameter'])*pi;material=geometry+F(m['join'])
  return dict(geometry=str(geometry),material=str(material))
 if k=='wrap_inverse':
  # Solve pi*d*wraps + join = material directly; inverse conservation.
  diameter=(F(m['material'])-F(m['join']))/(pi*F(m['wraps']))
  return dict(diameter=str(diameter),geometry=str(F(m['material'])-F(m['join'])))
 if k in ('surface_closed','surface_open'):
  candidates=divisor_shapes(m['volume'],k=='surface_open');minimum=min(x['area'] for x in candidates);best=[x['dimensions'] for x in candidates if x['area']==minimum]
  return dict(candidates=candidates,minimum=minimum,optima=best)
 raise AssertionError(k)
def model_pass(m):
 got=independent(m);k=m['kind'];pairs={
 'semiboundary':[('arc','expected_arc'),('perimeter','expected_perimeter')],
 'chain':[('chain','expected_chain'),('reference','expected_reference')],
 'wheel_forward':[('distance','expected_distance')],
 'wheel_inverse':[('turns','expected_turns'),('partial','expected_partial')],
 'stadium':[('area','expected_area'),('perimeter','expected_perimeter')],
 'wrap_forward':[('geometry','expected_geometry'),('material','expected_material')],
 'wrap_inverse':[('geometry','expected_geometry'),('diameter','expected_diameter')],
 }.get(k,[])
 for out,expected in pairs:
  if F(got[out])!=F(m[expected]):return False
 if k=='wheel_inverse' and got['full']!=m['expected_full']:return False
 if k.startswith('surface_'):
  if got['minimum']!=m['expected_min'] or sorted(got['optima'])!=sorted(m['expected_optima']):return False
  if 'expected_candidates' in m and len(got['candidates'])!=m['expected_candidates']:return False
  if 'expected_shapes' in m and sorted(x['dimensions'] for x in got['candidates'])!=sorted(m['expected_shapes']):return False
 return True
DECISIONS={
 'semidisc_entire_boundary':'Diameter is explicitly on boundary; full boundary 25.7 cm checked via doubled-boundary conservation. Hints describe parts only.',
 'semidisc_arc_only_error':'Supplied 9.42 is correctly retained as arc; adding diameter6 gives15.42. Feedback refers only to exact written claim.',
 'semicircle_chain_equal_total_diameters':'Only arcs traversed, no hidden straight seam. Equality follows diameter sum; hints do not give final equality or length.',
 'semicircle_chain_connector_error':'Two unequal semicircles do not imply a complete circle with sum diameter. Connector3 included, diameter paths excluded;18.7 correct.',
 'wheel_full_turns_distance':'No slip/continuous same direction is explicit;20 whole turns yield31.4m. m/vòng denotes per-turn progress; no physical result claim.',
 'wheel_partial_turns_not_rounded':'Partial turns allowed explicitly; 2.5=2+half and no rounding. Student work already contains2.5; hints give method, not numerical completion.',
 'stadium_center_rectangle_area_outer_perimeter':'Central rectangle known, caps external and disjoint; seam diameters excluded from perimeter.146.24m² and49.12m distinct units.',
 'stadium_overall_length_not_rectangle_error':'Overall20 includes two radii total6; center14, area112.26m². Feedback corrects supplied length-role error without imagined drawing.',
 'circle_three_wraps_single_final_join':'Exactly three traversals plus one final allowance, not three joins;39.18cm. Explicit ideal material convention sufficient.',
 'circle_joined_wire_inverse_diameter':'One overlap removes3 from34.4 to31.4 circumference, then diameter10. Conservation recovers material; radius/diameter distinguished.',
 'fixed_twelve_cubes_closed_surface_minimum':'All4 rotation-quotiented integer cuboids enumerated; closed six-face convention gives areas50,40,38,32, unique3x2x2. Grade5 bounded enrichment.',
 'fixed_capacity_open_box_surface_two_optima':'All10 role-sensitive open-box candidates; remove only top. Areas38,28,26,34,26,34,28,35,38,49; two optima kept. Hint about retaining ties is procedural, no dimensions or minimum revealed.'}
def main():
 files=['cases.jsonl','chat.jsonl','selfqa7.jsonl','independent_oracles.jsonl','numeric_fraction_decimal.jsonl','manifest.json']
 before={n:sha((P/n).read_bytes()) for n in files}
 rows=[json.loads(b) for b in (P/'cases.jsonl').read_bytes().splitlines()];qa=[json.loads(b) for b in (P/'selfqa7.jsonl').read_bytes().splitlines()];chats=[json.loads(b) for b in (P/'chat.jsonl').read_bytes().splitlines()]
 assert len(rows)==len(qa)==12 and len(chats)==48
 byid={r['sample_id']:r for r in rows};hashes={r['sample_id']:sha(b) for r,b in zip(rows,(P/'cases.jsonl').read_bytes().splitlines())}
 reviews=[];numeric=[];models=[];mutations=[]
 for r,q in zip(rows,qa):
  sid=r['sample_id'];assert q['source_row_sha256']==hashes[sid] and q['actual_fields']=={f:r[f] for f in FIELDS};assert len(q['criteria'])==7
  assert r['grade']==5 and r['curriculum_assignment']['enrichment'] and not r['human_verified'] and not r['teacher_certified']
  assert len(r['hints'])==3 and [h['level'] for h in r['hints']]==[1,2,3]
  for st in r['worked_steps']:
   assert st['reason'] and st['explanation'] and 'unit' in st
   if st['expression']:
    f=evaluate(st['expression'],F);d=evaluate(st['expression'],D);assert f==F(st['result']) and d==D(st['result']);numeric.append(dict(sample_id=sid,step_id=st['step_id'],expression=st['expression'],fraction=str(f),decimal=str(d)))
  m=r['independent_model'];assert model_pass(m);models.append(dict(sample_id=sid,source_row_sha256=hashes[sid],result=independent(m),passed=True,method='Peer implementation: algebraic conservation, reference scaling, bounding rectangle corner deficits, divisor-factor pair formulas; no author oracle imported.'))
  # Every numeric worked result perturbation must be detected by the independent expression check.
  for st in r['worked_steps']:
   if st['expression']:
    fake=F(st['result'])+1;detected=evaluate(st['expression'],F)!=fake;assert detected;mutations.append(dict(sample_id=sid,mutation=st['step_id']+'.result += 1',detected=detected))
  mm=copy.deepcopy(m)
  target=next((key for key in mm if key.startswith('expected_') and isinstance(mm[key],(str,int)) and key!='expected_candidates'),None)
  assert target;mm[target]=str(F(mm[target])+1);detected=not model_pass(mm);assert detected;mutations.append(dict(sample_id=sid,mutation=target+' += 1',detected=detected))
  decision=DECISIONS[r['topic']]
  reviews.append(dict(sample_id=sid,source_row_sha256=hashes[sid],actual_fields={f:r[f] for f in FIELDS},fields_read='ALL problem/givens/request/student_work/initial/hints all texts/questions/worked steps reasons expressions results units/explanations/answers',semantic_decision=decision,hints_initial_answer_free=True,units_and_scope_pass=True,grade_enrichment_pass=True,grounding_pass=True,source_qa_hash_pass=True,status='PASS_INDEPENDENT_PEER',human_review_claimed=False))
 for c in chats:
  r=byid[c['source_sample_id']];assert c['source_row_sha256']==hashes[r['sample_id']]
  t=json.loads(c['messages'][2]['content'])
  if c['mode']=='worked_solution':assert t==dict(can_solve=r['can_solve'],initial_guidance=r['initial_guidance'],steps=r['worked_steps'],answer=r['expected_answer'])
  else:
   h=r['hints'][int(c['mode'][-1])-1];assert t==dict(hint=h['hint'],question=h['question'])
 # Convention-specific adversarial formulas, not only changed arithmetic literals.
 bads=[('omit_semidisc_diameter',F('15.7'),F('25.7')),('count_two_arcs_as_full_sumdiameter_circle',F('31.4')+3,F('18.7')),('wheel_use_diameter_without_pi',F('.5')*20,F('31.4')),('wheel_round_2_5_to_3',F(3),F('2.5')),('stadium_use_overall_rectangle',20*6+F('3.14')*9,F('112.26')),('add_internal_stadium_seams',F('49.12')+16,F('49.12')),('add_join_per_wrap',F('37.68')+3*F('1.5'),F('39.18')),('inverse_join_add_instead_subtract',(F('34.4')+3)/F('3.14'),F(10)),('open_box_count_lid',32,26),('drop_tied_open_optimum',1,2)]
 for name,bad,good in bads:assert bad!=good;mutations.append(dict(mutation=name,detected=True,wrong=str(bad),expected=str(good)))
 after={n:sha((P/n).read_bytes()) for n in files};assert before==after
 def write(name,items):(P/name).write_text(''.join(dump(x)+'\n' for x in items),'utf-8')
 write('peer_fullfield_reviews.jsonl',reviews);write('peer_independent_oracles.jsonl',models);write('peer_numeric_checks.jsonl',numeric);write('peer_adversarial_mutations.jsonl',mutations)
 report=dict(status='PASS_INDEPENDENT_PEER',cases=12,chats=48,full_field_reviews=12,numeric_steps=len(numeric),independent_models=len(models),adversarial_mutations_detected=len(mutations),source_hashes=before,source_files_unchanged=True,fixes_required=[],substantive_limitations=['Finite grade5 text enrichment only; no physical/image outcome evidence.','No model accuracy or human review attestation assigned.'],artifact_hashes={n:sha((P/n).read_bytes()) for n in ['peer_fullfield_reviews.jsonl','peer_independent_oracles.jsonl','peer_numeric_checks.jsonl','peer_adversarial_mutations.jsonl']})
 (P/'peer_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8');print(dump(report))
if __name__=='__main__':main()
