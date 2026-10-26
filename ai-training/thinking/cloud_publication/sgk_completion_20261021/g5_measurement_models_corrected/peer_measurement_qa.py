"""Independent content peer checks; never edit author cases/chats/QA."""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal,localcontext
from itertools import combinations,product
from collections import Counter
import ast,operator,json,hashlib,re,copy

P=Path(__file__).resolve().parent
FIELDS=['problem','givens','requested_quantity','student_work','worked_steps','expected_answer','initial_guidance','hints']
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def rows(n):return [(json.loads(b),sha(b)) for b in (P/n).read_bytes().splitlines() if b.strip()]
def write(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def jl(n,x):(P/n).write_text(''.join(dump(r)+'\n' for r in x),encoding='utf-8',newline='\n')
def numbers(t):return [F(v.replace(',','.')) for v in re.findall(r'-?\d+(?:,\d+|\.\d+)?',t)]
def calc(expr,typ):
 def walk(n):
  if isinstance(n,ast.Constant):return typ(ast.get_source_segment(expr,n))
  if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.USub):return -walk(n.operand)
  if isinstance(n,ast.BinOp):return {ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv}[type(n.op)](walk(n.left),walk(n.right))
  raise ValueError(expr)
 return walk(ast.parse(expr,mode='eval').body)
def signarea(p):return sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(p,p[1:]+p[:1]))/2
def polygon(p):
 p=[tuple(F(v) for v in x) for x in p]
 return list(reversed(p)) if signarea(p)<0 else p
def area(p):return abs(signarea(p)) if len(p)>2 else F(0)
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def clip(subject,bound):
 out=polygon(subject);bound=polygon(bound)
 for a,b in zip(bound,bound[1:]+bound[:1]):
  inp=out;out=[]
  if not inp:break
  s=inp[-1]
  for e in inp:
   ds=cross(a,b,s);de=cross(a,b,e)
   if de>=0:
    if ds<0:
     t=ds/(ds-de);out.append((s[0]+t*(e[0]-s[0]),s[1]+t*(e[1]-s[1])))
    out.append(e)
   elif ds>=0:
    t=ds/(ds-de);out.append((s[0]+t*(e[0]-s[0]),s[1]+t*(e[1]-s[1])))
   s=e
 return out

def tiling_subsets(m):
 w,h=m['width'],m['height'];a,b=m['tile'];shapes=[(a,b)]
 if m['allow_rotate']:shapes.append((b,a))
 placements=[]
 for tw,th in shapes:
  for x,y in product(range(w-tw+1),range(h-th+1)):
   mask=sum(1<<(j*w+i) for i,j in product(range(x,x+tw),range(y,y+th)))
   placements.append((x,y,tw,th,mask))
 count=F(w*h,a*b);assert count.denominator==1
 target=(1<<(w*h))-1;solutions=[];combinations_checked=0
 for chosen in combinations(placements,int(count)):
  combinations_checked+=1;cover=0;valid=True
  for v in chosen:
   if cover&v[4]:valid=False;break
   cover|=v[4]
  if valid and cover==target and (not m['require_mixed'] or len({v[2:4] for v in chosen})==2):solutions.append([list(v[:4]) for v in chosen])
 return solutions,combinations_checked,placements

def verify(r):
 m=r['independent_model'];k=m['kind'];a={x['quantity']:x['result'] for x in r['expected_answer']}
 if k in ['board_bill','board_budget']:
  # Count 5cm-by-5cm material cells, with price per cell. Unlike the author's
  # expanded cm2 board products, this is an exact repeated-cell inventory.
  def raster(boards):
   count=0;details=[]
   for n,x,y in boards:
    columns=F(x)/F('0.05');rows=F(y)/F('0.05');assert columns.denominator==rows.denominator==1
    cells=[(i,j) for i,j in product(range(int(columns)),range(int(rows)))];count+=n*len(cells);details.append([n,len(cells)])
   return count,details
  unit=F('0.05')**2;price=F(m['price'])*unit
  if k=='board_bill':
   cells,details=raster(m['boards']);ar=cells*unit;cost=cells*price
   assert ar==F(m['expected_area'])==F(a['Diện tích']) and cost==F(m['expected_cost'])==F(a['Tiền'])
   return dict(method='Count equal 5cm material cells then price each cell',cells=cells,per_board_type=details,cell_area_m2=str(unit),cell_price_thousand=str(price),area=str(ar),cost=str(cost))
  fixed,details=raster(m['fixed']);single,_=raster([[1,*m['shelf']]])
  costs=[(fixed+n*single)*price for n in m['choices']];valid=[n for n,c in zip(m['choices'],costs) if c<=F(m['budget'])];best=max(valid);cost=costs[m['choices'].index(best)];left=F(m['budget'])-cost
  assert costs==list(map(F,m['expected_costs'])) and valid==m['expected_eligible'] and best==m['expected_best']
  assert [int(n) for n in re.findall(r'\d+',a['Đủ tiền'])]==valid and int(a['Tối đa'])==best and F(a['Tiền'])==cost and F(a['Còn'])==left
  return dict(method='Finite shelf enumeration using repeated material cells and cell-level price',fixed_cells=fixed,one_shelf_cells=single,costs=list(map(str,costs)),eligible=valid,best=best,remaining=str(left))
 if k=='cut_compare':
  schemes=[]
  for scheme in m['schemes']:
   # Materialize identified pieces and allocate their exact sizes to each
   # recipient, rather than representing cakes by the author's six-atom grid.
   available={};allpieces=[]
   for batch,(cakes,den) in enumerate(scheme['cuts']):
    for cake in range(cakes):
     for piece in range(den):
      token=f'b{batch}_cake{cake}_piece{piece}';available[token]=F(1,den);allpieces.append(token)
   original=dict(available);alloc=[];missing=[]
   for who in range(m['people']):
    got=[]
    for count,den in scheme['each']:
     for _ in range(count):
      eligible=next((key for key,value in available.items() if value==F(1,den)),None)
      if eligible is None:missing.append([who,str(F(1,den))])
      else:got.append(eligible);del available[eligible]
    alloc.append(got)
   share=sum(F(count,den) for count,den in scheme['each']);total=share*m['people'];feasible=not missing and not available and total==m['whole']
   assert sum(original.values())==m['whole']
   schemes.append(dict(pieces=len(original),share=str(share),total_requested=str(total),feasible=feasible,identified_allocations=alloc,missing_piece_requests=missing,unallocated_pieces=list(available)))
  assert [x['pieces'] for x in schemes]==m['expected_pieces'] and [x['feasible'] for x in schemes]==m['expected_feasible'] and F(schemes[0]['share'])==F(m['expected_share'])
  if 'Cách A'in a:
   assert int(a['Cách A'])==schemes[0]['pieces'] and int(a['Cách B'])==schemes[1]['pieces'] and F(a['Mỗi bạn ở cả hai cách'])==F(schemes[0]['share']) and a['So']=='Cả hai khả thi và cùng lượng mỗi bạn'
  else:
   assert a['Cách đạt']=='X' and schemes[0]['feasible'] and not schemes[1]['feasible'] and F(a['Mỗi bạn theo X'])==F(schemes[0]['share']) and a['Y']=='Không đủ miếng nửa và vượt tổng bánh'
  return dict(method='Identified physical-piece allocation by exact rational size; no recutting or replacement',schemes=schemes)
 if k in ['frame','frame_inverse']:
  w=m['width'];s=F(m['scale'])
  if k=='frame_inverse':
   h=F(m['border_count']-2*w+4,2);assert h.denominator==1 and h>=3;h=int(h);assert h==m['expected_height']==int(a['Số hàng'])
  else:h=m['height']
  boundary=2*w+2*h-4;inside=(w-2)*(h-2);full=w*h
  assert boundary+inside==full
  total=full*s*s;white=inside*s*s;paint=boundary*s*s
  assert total==F(m['expected_total'])==F(a['Toàn']) and white==F(m['expected_inside'])==F(a['Trắng'])
  assert numbers(a['Kích thước'])==[w*s,h*s]
  if 'Tô'in a:assert paint==F(m['expected_border'])==F(a['Tô'])
  return dict(method='Perimeter-row strip accounting with four corner corrections and algebraic inverse; not cell-set enumeration',width=w,height=h,border_cells=boundary,inside_cells=inside,total_area=str(total),inside_area=str(white),border_area=str(paint))
 if k=='net':
  u,v=m['caps'];h=m['height'];s=F(m['scale']);strip=m['strip']
  # Reconstruct an oriented closed base loop and extrude by the common side
  # height. This is independent of the author's voxel and face-normal inventory.
  assert strip==[u,v,u,v]
  edges=[(strip[0],0),(0,strip[1]),(-strip[2],0),(0,-strip[3])];x=y=0;loop=[(F(0),F(0))]
  for dx,dy in edges:x+=dx;y+=dy;loop.append((F(x),F(y)))
  assert loop[-1]==loop[0];base_area=area(loop[:-1])*s*s;volume=base_area*h*s;dims=[u*s,v*s,h*s]
  assert dims==list(map(F,m['expected_dimensions'])) and volume==F(m['expected_volume'])==F(a['Thể tích']) and numbers(a['Kích thước'])==dims
  if 'Bề ngang'in a:assert list(map(int,a['Bề ngang'].split(',')))==strip and sum(strip)==m['total_strip']
  return dict(method='Close oriented base-edge loop, cap area by polygon and exact extrusion height',base_loop=[list(map(str,p)) for p in loop],base_area=str(base_area),height=str(h*s),dimensions=list(map(str,dims)),volume=str(volume))
 if k=='tiling':
  solutions,trials,placements=tiling_subsets(m);possible=bool(solutions);assert possible==m['expected_possible']
  if m['placements']:
   given={tuple(p) for p in m['placements']};assert any(set(map(tuple,v))==given for v in solutions)
  if possible:assert int(a['Số miếng'])==len(solutions[0]) and a['Bố trí']=='Dải rộng 2: hai miếng 2 × 3; dải rộng 3: ba miếng 3 × 2'
  else:assert a['Khả thi']=='Không có phép lát theo luật cấm xoay' and a['Lý do']=='Mỗi hàng cần phủ 5 ô nhưng là tổng các đoạn rộng 2 ô'
  return dict(method='Enumerate every unordered subset of the required number of legal placements; bitmask exact cover, not first-hole recursion',legal_placements=len(placements),subsets_checked=trials,solutions=len(solutions),possible=possible,one_solution=solutions[0] if solutions else [])
 if k=='nested':
  points={n:tuple(map(F,p)) for n,p in m['points'].items()}
  if r['topic']=='nested_triangles_distinct_apex_heights':roles=[(['B','C'],'A'),(['B','E'],'A'),(['B','E'],'D')]
  else:roles=[(['A','D'],'E'),(['D','B'],'E'),(['C','E'],'A')]
  aa=[];heights=[]
  for names,apex in roles:
   p,q=[points[n] for n in names];z=points[apex]
   if p[0]==q[0]:base=abs(p[1]-q[1]);height=abs(z[0]-p[0])
   else:assert p[1]==q[1];base=abs(p[0]-q[0]);height=abs(z[1]-p[1])
   aa.append(base*height/2);heights.append(height)
  assert aa==list(map(F,m['expected_areas']))
  outer=polygon([points[n] for n in ['A','B','C']]);triangles=[polygon([points[n] for n in t]) for t in m['triangles']]
  assert all(area(clip(t,outer))==ar for t,ar in zip(triangles,aa))
  if r['topic']=='nested_triangles_distinct_apex_heights':
   assert numbers(a['Chiều cao theo ba đáy'])==heights
   assert [F(a['Diện tích '+n]) for n in ['ABC','ABE','DBE']]==aa and F(a['ABC ngoài DBE'])==aa[0]-aa[-1]
  else:
   assert numbers(a['Chiều cao theo AD, DB, CE'])==heights and [F(a[n]) for n in ['ADE','DBE','ACE']]==aa and F(a['Tổng'])==sum(aa)==area(outer)
   assert all(area(clip(t,u))==0 for t,u in combinations(triangles,2))
   assert 'DEchiaABE' in r['worked_steps'][2]['explanation'].replace(' ','') and 'ADchiaABE' not in r['worked_steps'][2]['explanation'].replace(' ','')
  return dict(method='Match each actual selected base to perpendicular coordinate distance from its own apex; verify containment and disjoint partition separately',base_apex_roles=roles,heights=list(map(str,heights)),areas=list(map(str,aa)),outer_area=str(area(outer)))
 raise ValueError(k)

NOTES=[
'Six finished boards counted once each; raster5cm material cells reproduce1.26m2 and226.8thousand. No two-face paint or stock-sheet packing assertion.',
'Finite permitted n2/3/4 evaluated after mandatory0.88m2.236/266/296thousand means n2/3eligible,n3maximum,cash4; inclusive budget properly retained.',
'Identified half/third/sixth piece inventories allocate exactly to6recipients without recutting;12versus30pieces still5/6cake perperson.',
'Xallocates3thirds+6sixths exactly; Yrequests3halves fromstock2 and5/2cake from2. Correctly distinguishes equal-looking prescription from available inventory.',
'Counts along edges are cells, notendpointmarks;9by7 yields4.5by3.5metres,63total35inner28bordercells, correct m2 scaling.',
'Border count includescorners once.2w+2h-4=24 withw9 givesh5; whole11.25 andwhite5.25 differ fromborder6m2. Quote arithmetic correct for wrong requested region.',
'Four-side strip closes a6by3 grid base and commonheight4; physical3by1.5by2cm gives9cm3. Opposite caps attached above/below firstside are consistent, no actual fold claimed.',
'Cap6by4 constrains missing widths4/4; strip20 measures baseperimeter, not edge. Dimensions1.2/0.8/0.6dm and0.576dm3 correct; quoted1.92correct arithmetic wrong edge role.',
'Exhaustive unordered five-placement subsets verify two vertical plus three rotated rectangles exact-cover5by6 with both orientations; equality of area used only as prerequisite.',
'Withrotationforbidden every horizontalrowcover is sum of width2 intervals, impossible forwidth5. Complete placement-subset enumeration agrees; no unstatedpermission introduced.',
'Selected basesBC/BE/BE pair withapexA/A/D givingheights6/6/3 andareas24/12/6; inner6removed fromouter24leaves18, noextraABEsubtraction.',
'Latest repaired source usesDE, notAD, todivideABE. VerticalbasesAD/DB usehorizontalEB4, evenwhenfootBoutsideAD; CEusesAB6.6+6+12partition24; DE5isoblique, notheight.'
]

def main():
 names=['cases.jsonl','chat.jsonl','selfqa7.jsonl','manifest.json','independent_oracle.py','independent_oracles.jsonl','numeric_fraction_decimal.jsonl','author_polish_delta.jsonl']
 before={n:sha((P/n).read_bytes()) for n in names};rr=rows('cases.jsonl');assert len(rr)==12
 # Refuse the known stale source until the author has made the content repair.
 assert 'DEchiaABE' in rr[-1][0]['worked_steps'][2]['explanation'].replace(' ','')
 qa={r['sample_id']:r for r,h in rows('selfqa7.jsonl')};full=[];oracles=[];numeric=[];mutations=[]
 for (r,h),note in zip(rr,NOTES):
  assert r['grade']==5 and r['split']=='train' and r['acceptance_status'].startswith('DRAFT')
  assert qa[r['sample_id']]['source_row_sha256']==h and len(qa[r['sample_id']]['criteria'])==7 and all(x['passed'] for x in qa[r['sample_id']]['criteria'])
  assert all(r[k]==v for k,v in qa[r['sample_id']]['actual_fields'].items())
  result=verify(r);oracles.append(dict(sample_id=r['sample_id'],source_row_sha256=h,status='PASS_INDEPENDENT_PEER',oracle=result))
  prev={}
  for st in r['worked_steps']:
   assert st['reason'] and st['explanation'] and 'unit'in st
   if st.get('expression'):
    expr=re.sub(r'\{(s\d+)\}',lambda z:'('+str(F(prev[z[1]]))+')',st['expression']);f=calc(expr,F)
    with localcontext() as ctx:
     ctx.prec=90;d=calc(expr,Decimal);assert abs(d-Decimal(f.numerator)/Decimal(f.denominator))<Decimal('1e-70')
    assert f==F(st['result']);numeric.append(dict(sample_id=r['sample_id'],source_row_sha256=h,step_id=st['step_id'],expression=expr,fraction=str(f),decimal_agrees=True))
   prev[st['step_id']]=st['result']
  if r['student_work']:assert r['student_work']['text'] in r['problem'] and all(o['excerpt'] in r['student_work']['text'] for o in r['student_work']['observations'])
  assert [v['id'] for v in r['givens']]==['g0','g1'] and [v['step_id'] for v in r['worked_steps']]==['s'+str(i) for i in range(len(r['worked_steps']))]
  assert [v['level'] for v in r['hints']]==[1,2,3] and r['initial_guidance']
  bad=copy.deepcopy(r)
  try:bad['expected_answer'][0]['result']=str(F(bad['expected_answer'][0]['result'])+1)
  except ValueError:bad['expected_answer'][0]['result']='INCORRECT_MUTATED_ANSWER'
  try:verify(bad)
  except (AssertionError,ValueError,KeyError):mutations.append(dict(sample_id=r['sample_id'],source_row_sha256=h,kind='Wrong actual expected answer',detected=True))
  else:raise AssertionError('Expected-answer mutation accepted')
  bad=copy.deepcopy(r);m=bad['independent_model'];k=m['kind']
  if k in ['board_bill','board_budget']:m['price']=str(F(m['price'])+1)
  elif k=='cut_compare':m['schemes'][0]['cuts'][0][0]+=1
  elif k in ['frame','frame_inverse','net']:m['scale']=str(F(m['scale'])+F(1,10))
  elif k=='tiling':m['allow_rotate']=not m['allow_rotate']
  elif k=='nested':m['points']['E'][0]+=1
  try:verify(bad)
  except (AssertionError,ValueError,KeyError):mutations.append(dict(sample_id=r['sample_id'],source_row_sha256=h,kind='Alter exact quantity or legal convention while retaining original answer',detected=True))
  else:raise AssertionError('Given/convention mutation accepted')
  criteria=[dict(criterion=k,passed=True,evidence=e) for k,e in [('actual_problem_givens_request',note),('mathematics_and_independent_oracle','Separate raster/piece-ID/closedformula/base-loop/subset-exactcover/perpendicular-projection oracle; no author helper imports.'),('worked_steps_reason_units_check','Read every actual step/reason/explanation/answer and unit, including arithmetic in supplied quotes.'),('initial_and_three_hints_no_answer_leak','Read every hint/question and initial; strategy only, no filled requested result or final label.'),('student_work_and_asset_grounding','Exact synthetic quotes only; explicit model not unseen-image or physical success.'),('grade_and_structural_diversity','Grade5 original text enrichment; pairs change inventory/constraint/inverse/unit/motion roles rather than constants only.'),('source_hash_provenance_limits','Exact raw row/sourceQA/chat hashes, draft status and original AI provenance retained, no human-review claim.')]]
  full.append(dict(sample_id=r['sample_id'],source_row_sha256=h,status='PASS_INDEPENDENT_PEER',criteria=criteria,actual_fields={k:r[k] for k in FIELDS},semantic_decision=note,fields_read='ALL actual problem/givens/request/student_work/steps/reasons/explanations/results/units/answers/initial/all hints and questions',human_review_claimed=False))
 byid={r['sample_id']:(r,h) for r,h in rr};modes={sid:[] for sid in byid};links=0
 for c,ch in rows('chat.jsonl'):
  r,h=byid[c['source_sample_id']];assert c['source_row_sha256']==h and c['acceptance_status']==r['acceptance_status'] and c['quality_status']==r['quality_status']
  prompt=json.loads(c['messages'][1]['content']);wanted=dict(grade=r['grade'],problem=r['problem'],mode=c['mode'])
  if r['student_work']:wanted['student_work']=r['student_work']['text']
  assert prompt==wanted;target=json.loads(c['messages'][2]['content'])
  if c['mode']=='worked_solution':assert target==dict(can_solve=r['can_solve'],initial_guidance=r['initial_guidance'],steps=r['worked_steps'],answer=r['expected_answer'])
  else:
   hi=r['hints'][int(c['mode'][-1])-1];assert target==dict(hint=hi['hint'],question=hi['question'])
  modes[r['sample_id']].append(c['mode']);links+=1
 assert links==48 and all(Counter(v)==Counter({'worked_solution':1,'hint_level_1':1,'hint_level_2':1,'hint_level_3':1}) for v in modes.values())
 jl('peer_fullfield_reviews.jsonl',full);jl('peer_independent_oracles.jsonl',oracles);jl('peer_numeric_checks.jsonl',numeric);jl('peer_adversarial_mutations.jsonl',mutations)
 assert all(sha((P/n).read_bytes())==h for n,h in before.items())
 summary=dict(status='PASS_INDEPENDENT_PEER',cases=12,chats=48,source_file_sha256=before['cases.jsonl'],chat_file_sha256=before['chat.jsonl'],seven_criteria_pass_count=12,reviews=full,source_hashes=before,full_field_reviews=12,numeric_steps=len(numeric),independent_models=12,adversarial_mutations_detected=len(mutations),source_files_unchanged=True,fixes_required=[],artifact_hashes={n:sha((P/n).read_bytes()) for n in ['peer_fullfield_reviews.jsonl','peer_independent_oracles.jsonl','peer_numeric_checks.jsonl','peer_adversarial_mutations.jsonl']},peer_helper_sha256=sha(Path(__file__).read_bytes()),training_started=False,drive_mutated=False,substantive_limitations=['Explicit original text/grid reasoning only; no actual image/physical competency certified.','Only exact latest repaired draft bytes reviewed; root acceptance still required.','No external independent human review or accuracy guarantee.'])
 write('peer_review.json',summary);print(dump({k:v for k,v in summary.items() if k not in ['reviews','source_hashes']}))
if __name__=='__main__':main()
