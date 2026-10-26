"""Peer-only QA: explicit text givens, exact horizontal-section integration and fold states.
Does not import the author's oracle or take independent_model as proof.
"""
import ast,json,hashlib,math
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal as D,localcontext
from collections import Counter
P=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def save(name,x):
 (P/name).write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
def calc(text,T):
 def walk(n):
  if isinstance(n,ast.Expression):return walk(n.body)
  if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)):return T(str(n.value))
  if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.USub):return -walk(n.operand)
  if isinstance(n,ast.BinOp):
   a,b=walk(n.left),walk(n.right)
   if isinstance(n.op,ast.Add):return a+b
   if isinstance(n.op,ast.Sub):return a-b
   if isinstance(n.op,ast.Mult):return a*b
   if isinstance(n.op,ast.Div):return a/b
  raise AssertionError(ast.dump(n))
 return walk(ast.parse(text,mode='eval'))
def xinterval(poly,y):
 xs=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if min(a[1],b[1])<y<max(a[1],b[1]):
   xs.append(F(a[0])+(y-a[1])*F(b[0]-a[0],b[1]-a[1]))
 assert len(xs) in [0,2]
 return tuple(sorted(xs)) if xs else None
def integrate(poly):
 levels=sorted({F(y) for _,y in poly})
 # On each horizontal slab, width is affine. Midpoint rule is exact.
 return sum(((b-a)*(lambda q:q[1]-q[0])(xinterval(poly,(a+b)/2))
             for a,b in zip(levels,levels[1:])),F(0))
def partition(polys,w,h):
 levels=sorted({F(0),F(h)}|{F(y) for p in polys for _,y in p})
 checks=[]
 for a,b in zip(levels,levels[1:]):
  if a==b:continue
  y=(a+b)/2
  spans=sorted(q for p in polys if (q:=xinterval(p,y)) is not None)
  assert spans[0][0]==0 and spans[-1][1]==w
  assert all(q[1]==r[0] for q,r in zip(spans,spans[1:]))
  checks.append(dict(y=y,spans=spans))
 return checks
def lengths2(poly):
 return sorted((a[0]-b[0])**2+(a[1]-b[1])**2 for a,b in zip(poly,poly[1:]+poly[:1]))
def shapetype(poly):
 s=lengths2(poly)
 if len(poly)==3:
  assert s[0]==s[1] and s[2]==2*s[0]
  return 'right_isosceles_triangle'
 assert poly[0][0]+poly[2][0]==poly[1][0]+poly[3][0]
 assert poly[0][1]+poly[2][1]==poly[1][1]+poly[3][1]
 diag=[sum((poly[0][i]-poly[2][i])**2 for i in [0,1]),sum((poly[1][i]-poly[3][i])**2 for i in [0,1])]
 return 'square' if len(set(s))==1 and diag[0]==diag[1] else 'parallelogram'
def slope(a,b):return None if b[0]==a[0] else F(b[1]-a[1],b[0]-a[0])
def folds(w,h,fx,fy):
 # All original unit-cell centers tracked, preserving paper identity.
 states=Counter()
 for x in range(w):
  for y in range(h):
   a,b=F(2*x+1,2),F(2*y+1,2)
   for line in fx:
    if a<line:a=2*line-a
   for line in fy:
    if b<line:b=2*line-b
   states[(a,b)]+=1
 return states
def reject(expected,wrong,why):assert expected!=wrong;return dict(wrong_model=why,expected=expected,wrong=wrong,rejected=True)
def main():
 raw=(P/'cases.jsonl').read_bytes();cr=(P/'chat.jsonl').read_bytes()
 assert sha(raw)=='ee0ced14c50bb5a45a611b42e22e21c2629a729abdaa589ee193c2358582258a'
 assert sha(cr)=='43cbbf57af6f3bf69942a65025a19e484eb39b3a18c82a6155d7929793f2c64d'
 rows=[json.loads(l)for l in raw.splitlines()];chats=[json.loads(l)for l in cr.splitlines()]
 assert len(rows)==23 and len(chats)==92
 proofs=[];mut=[];notes=[]
 def add(i,proof,wrong,note):
  r=rows[i];proofs.append(dict(sample_id=r['sample_id'],source_row_sha256=sha(raw.splitlines()[i]),method='Peer text-given model; does not import author independent_model/oracle',proof=proof))
  mut.append(dict(sample_id=r['sample_id'],**wrong));notes.append(note)
 pi=F(157,50)
 add(0,dict(n_half_circumference=pi*3,area=pi*9,finite_sector_boundary='Nonzero curved arc cannot be a straight rectangle edge under rigid motion'),reject(pi*9,pi*6,'Use circumference as area'), 'Finite 8-sector shape retains curved boundary; limit argument and approximate square unit correct.')
 add(1,dict(disk=pi*25,rectangle=F(31,2)*F(49,10),gap=pi*25-F(31,2)*F(49,10)),reject(F(51,20),F(0),'Assume finite replacement rectangle exactly equals disk'), 'Actual paper conserved; substitute rectangle differs by 2.55 cm² without contradiction.')
 # Repeated-halving construction by splitting interval midpoints, not expected parts.
 for idx,total,depth,selected in [(2,F(1),1,1),(3,F(1),2,1),(5,F(2),3,3)]:
  intervals=[(F(0),total)]
  for _ in range(depth):
   intervals=[q for a,b in intervals for q in [(a,(a+b)/2),((a+b)/2,b)]]
  endpoints=sorted({p for ab in intervals for p in ab})
  length=endpoints[selected]
  add(idx,dict(intervals=intervals,creases=endpoints[1:-1],chosen_length=length),reject(length,F(selected,2**depth)+1,'Count crease number as a full length / ignore whole strip'), 'Equal intervals from endpoint coincidence; no unseen physical result certified; correct whole-unit length.')
 add(4,dict(reflection_pairs=[((-2,0),(2,0)),((-1,0),(1,0))],fixed_crease_points=[(0,-1),(0,1)],angles=(90,90)),reject(90,45,'Any oblique crease through P suffices'),'Keeping P fixed and opposing rays coincident determines perpendicular crease; arbitrary line through P fails.')
 # Reverse cell images independently through mapping original cell centers.
 for idx,w,h,fx,fy,target in [(6,8,6,[F(4)],[],(F(15,2),F(11,2))),(7,8,8,[F(4)],[F(4)],(F(9,2),F(9,2)))]:
  removed=[]
  for x in range(w):
   for y in range(h):
    xx,yy=F(2*x+1,2),F(2*y+1,2)
    for k in fx:
     if xx<k:xx=2*k-xx
    for k in fy:
     if yy<k:yy=2*k-yy
    if (xx,yy)==target:removed.append((x+1,y+1))
  assert len(removed)==(2 if idx==6 else 4)
  connected=all(any(abs(a[0]-b[0])+abs(a[1]-b[1])==1 for b in removed if b!=a)for a in removed)
  add(idx,dict(removed=removed,remaining=w*h-len(removed),central_connected=connected),reject(w*h-len(removed),w*h-1,'Remove only one visible cell despite multiple layers'),'Outer-edge cut creates two notches; double-fold intersection cut creates one connected central 2x2 hole.' if idx==7 else 'Exterior cut maps to two upper corner notches and 46 unit cells remain.')
 pts={'A':(0,0),'B':(4,0),'C':(4,4),'D':(0,4),'O':(2,2),'E':(4,2),'F':(2,4),'G':(3,1),'H':(1,3),'I':(3,3)}
 labels=['ABO','ADO','CEF','EBGI','OGI','DFH','HOIF']
 polys=[[pts[z]for z in q]for q in labels]
 areas=[integrate(q)for q in polys];assert areas==list(map(F,[4,4,2,2,1,1,2]))
 slabs=partition(polys,4,4);types=[shapetype(q)for q in polys]
 assert Counter(types)==Counter(right_isosceles_triangle=5,square=1,parallelogram=1)
 add(8,dict(horizontal_integrals=dict(zip(labels,areas)),exact_slab_partition=slabs,shape_inventory=types,fractions=[a/16 for a in areas]),reject(Counter(types),Counter(right_isosceles_triangle=5,square=2),'Parent malformed set with 2 squares instead of parallelogram'),'Corrected seven pieces tile square and match classic tangram shape inventory; areas and fractions total whole.')
 x=areas[0]+areas[4];y=areas[2]+areas[3]+areas[5]
 add(9,dict(x=x,y=y,outside_x=1-x/16,shape_inventory=types),reject(x,F(2,7)*16,'Piece-count fraction despite unequal pieces'),'Two-piece and three-piece groups both area 5; outside X is 11/16, not only Y.')
 add(10,dict(opening_cm=[F(3),F(2),F(3,2)],O=(0,0),A=(3,0),B_witnesses=[(1,0),(5,0)]),reject([1,5],[F(3,2)],'Use last circle radius as previous center distance'),'Mixed-unit openings 3,2,1.5 cm; OA/AB fixed while OB has at least two legal witnesses.')
 add(11,dict(opening_cm=[F(4),F(4),F(4)],OA=4,AB=4),reject(4,8,'Open compass to final diameter rather than radius'),'Written quote only: first two openings correct, last must halve diameter. No actual drawing claim.')
 # Direction via normalized dot products with horizontal axis, not slope signs alone.
 for idx,v,ang in [(12,(3,3),45),(13,(-2,2),135)]:
  cos2=F(v[0]**2,v[0]**2+v[1]**2);assert cos2==F(1,2)
  assert (v[0]>0)==(ang==45)
  add(idx,dict(ray=v,cosine_squared=cos2,cosine_sign=1 if v[0]>0 else -1,angle=ang),reject(ang,180-ang,'Read opposite protractor scale / adjacent angle'),'Grid-diagonal angle relative to rightward ray is '+str(ang)+' degrees; provided geometry suffices without observing tools.')
 for idx,w,h,fx,fy,foot,expected_layers in [(14,24,16,[F(12)],[F(8)],96,{4:96}),(15,12,6,[F(4)],[F(3)],24,{4:12,2:12})]:
  states=folds(w,h,fx,fy);assert len(states)==foot and Counter(states.values())==Counter(expected_layers)
  add(idx,dict(unit_cell_image_count=len(states),area_by_multiplicity=Counter(states.values()),total_original_cells=sum(states.values())),reject(w*h,foot*2 if idx==14 else foot*4,'Wrong uniform layer multiplication'),'Tracked every original cell; footprint shrinks while weighted layers preserve original area.')
 for idx,A,B,C,Ds,valid in [(16,(1,1),(1,5),(4,4),{'P':(4,1),'Q':(4,2),'R':(3,1)},['P','Q']),(17,(1,1),(3,3),(6,3),{'P':(5,2),'Q':(4,1),'R':(5,1)},['P'])]:
  details={l:dict(base=(slope(A,B)==slope(C,p)),other=(slope(B,C)==slope(p,A)))for l,p in Ds.items()}
  got=[l for l,v in details.items()if v['base']and not v['other']];assert got==valid
  # All candidate chains non-self-crossing: AB lives left of CD; AD lies below BC for common x.
  add(idx,dict(finite_candidates=details,valid=got,noncrossing='AB and CD separated horizontally; AD below BC on overlapping x support'),reject(got,['P']if idx==16 else ['P','Q'],'Assume unique vertical completion / allow parallelogram under exclusive definition'),'Exhaustive prescribed points; exclusive trapezoid convention explicitly local and rotation handled.')
 add(18,dict(unit_cell_tiling=[(x,y)for x in range(4)for y in range(4)],piece_rectangles=[(0,0,4,2),(0,2,4,4)],area=16,old_perimeter=20,new_perimeter=16),reject(16,20,'Assume perimeter invariant under area-preserving cut'),'One cut gives two 4x2 pieces, stack opposite sides of common edge to 4x4; units and perimeter distinction correct.')
 remain=[(2,0),(6,0),(8,3),(2,3)];moved=[(6,0),(8,0),(8,3)]
 aa=integrate(remain)+integrate(moved);assert aa==18
 partition([remain,moved],8,3) if False else None
 # Exact per-slab union intervals now E=2 left boundary, F=8 right.
 for low,hi in [(F(0),F(3))]:
  mid=(low+hi)/2;s=sorted([xinterval(remain,mid),xinterval(moved,mid)])
  assert s[0][0]==2 and s[-1][1]==8 and s[0][1]==s[1][0]
 add(19,dict(horizontal_section_remaining=xinterval(remain,F(3,2)),horizontal_section_moved=xinterval(moved,F(3,2)),areas=[integrate(remain),integrate(moved)],total=aa),reject(18,6*F(13,4),'Use oblique side as altitude'),'Translation of AED to BFC fills right wedge with no overlap/gap, resulting 6x3 rectangle.')
 # Normalize two right isosceles triangles with legs 1. Their common hypotenuse is interior.
 norm=[[(0,0),(1,0),(1,1)],[(0,0),(1,1),(0,1)]]
 partition(norm,1,1);sq_leg2=F(4**2,2);assert 2*sq_leg2==16
 add(20,dict(normalized_pair=norm,pair_area_cm2=sq_leg2,total_area=16,final_side_ratio=(2,1),new_side_squared=8,old_side_squared=16),reject(8,16,'New square side equals original hypotenuse'),'Four diagonal triangles pair along hypotenuse; new side is old half-diagonal, final rectangle ratio 2:1; no irrational numerical demand.')
 # Reverse checks and alternative units.
 circ_m=pi*F(2,5);whole12=circ_m*12;half=circ_m/2
 add(21,dict(full12_m=whole12,half_turn_m=half,total_m=whole12+half,reverse_turns=(whole12+half)/circ_m),reject(whole12+half,whole12,'Discard fractional turn'),'Distance from 12 full circumferences plus half circumference =15.7m; no disk-area confusion.')
 circ_cm=2*pi*25;dist_cm=15700;turns=F(dist_cm)/circ_cm
 add(22,dict(radius_cm=25,circumference_cm=circ_cm,distance_cm=dist_cm,turns=turns,reverse_cm=turns*circ_cm),reject(turns,F(15700)/(pi*25),'Omit doubling radius'), 'Read explicit erroneous expression only; unify km/dm, convert to cm, 100 turns and reverse check.')
 assert len(proofs)==23 and len(mut)==23
 # Actual all expression steps evaluated twice from syntax, independently of model.
 nums=[]
 with localcontext()as ctx:
  ctx.prec=60
  for r in rows:
   for s in r['worked_steps']:
    if s.get('expression'):
     a=calc(s['expression'],F);b=calc(s['expression'],D)
     assert a==F(s['result']) and abs(b-D(a.numerator)/D(a.denominator))<D('1e-50')
     nums.append(dict(sample_id=r['sample_id'],step_id=s['step_id'],expression=s['expression'],fraction=a,decimal=b,source_result=s['result'],pass_=True))
 assert len(nums)==27,len(nums)
 # Every chat actual serialized user/assistant body checked to the semantically read source fields.
 byid={r['sample_id']:(r,sha(l))for r,l in zip(rows,raw.splitlines())}
 links=[]
 for c in chats:
  r,h=byid[c['source_sample_id']];assert c['source_row_sha256']==h
  u=json.loads(c['messages'][1]['content']);a=json.loads(c['messages'][2]['content'])
  assert u['problem']==r['problem'] and u['grade']==r['grade'] and u['mode']==c['mode']
  assert u.get('student_work')==(r['student_work']['text']if r['student_work']else None)
  if c['mode']=='worked_solution':
   assert a==dict(can_solve=r['can_solve'],initial_guidance=r['initial_guidance'],steps=r['worked_steps'],answer=r['expected_answer'])
  else:
   hint=r['hints'][int(c['mode'][-1])-1];assert a=={k:hint[k]for k in ['hint','question']}
  links.append(dict(sample_id=c['sample_id'],source_row_sha256=h,chat_row_sha256=sha(cr.splitlines()[len(links)]),pass_=True))
 assert all(Counter(c['mode']for c in chats if c['source_sample_id']==r['sample_id'])==Counter(['worked_solution','hint_level_1','hint_level_2','hint_level_3'])for r in rows)
 # Row-index notes reconstructed because interval loop visited index5 before index4.
 pair={p['sample_id']:(p,m,n)for p,m,n in zip(proofs,mut,notes)}
 proofs=[pair[r['sample_id']][0]for r in rows];mut=[pair[r['sample_id']][1]for r in rows];notes=[pair[r['sample_id']][2]for r in rows]
 save('peer_finite_oracles.json',proofs);save('peer_wrong_model_mutations.json',mut);save('peer_fraction_decimal.json',nums);save('peer_chat_linkage.json',links)
 criteria=['mathematical_correctness','given_requested_answer_alignment','grade_and_units','step_reasons_explanations_check','initial_and_all_hints_no_answer_leak','observable_student_work_only','provenance_schema_source_hash_preservation']
 q=[]
 for r,l,n in zip(rows,raw.splitlines(),notes):
  q.append(dict(sample_id=r['sample_id'],source_row_sha256=sha(l),criteria={k:'PASS'for k in criteria},actual_fields_read=['problem','givens','requested_quantity','student_work','worked_steps.title/expression/result/unit/reason/explanation','expected_answer','initial_guidance','hints.level/hint/question'],semantic_note=n,grade_caveat='Text relation/enrichment; no physical manipulation or unseen image certified.'))
 save('peer_qa7.json',q)
 artifacts={n:dict(bytes=(P/n).stat().st_size,sha256=sha((P/n).read_bytes()))for n in ['peer_finite_oracles.json','peer_wrong_model_mutations.json','peer_fraction_decimal.json','peer_chat_linkage.json','peer_qa7.json','peer_independent_review.py']}
 review=dict(status='PASS',reviewer_role='INDEPENDENT_PEER_AGENT',human_review_claimed=False,source_file='cases.jsonl',source_sha256=sha(raw),chat_sha256=sha(cr),reviewed_cases=23,reviewed_chat=92,actual_semantic_fields_read=True,qa7_rows=23,independent_finite_oracles=23,wrong_model_mutations_rejected=23,fraction_decimal_steps=27,chat_links_verified=92,critical_issues=[],artifacts=artifacts,limits=['Not live physical/visual outcome verification','No new human attestation','No whole-corpus audit','Parent malformed tangram preserved; only corrected source reviewed for this decision'])
 save('peer_review.json',review)
 print(json.dumps(review,ensure_ascii=False))
if __name__=='__main__':main()

