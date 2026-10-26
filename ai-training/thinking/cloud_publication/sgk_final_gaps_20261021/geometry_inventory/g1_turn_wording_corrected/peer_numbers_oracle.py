"""Independent reviewer oracle. Enumerates physical moves and exact vertical slabs.
Does not import author oracle, generator, or authored expected answers as a solver.
"""
from fractions import Fraction as F
from itertools import combinations,permutations,product
from collections import Counter
import json,hashlib,ast,copy
from pathlib import Path
from decimal import Decimal,localcontext
HERE=Path(__file__).resolve().parent
def area(p):return abs(sum(F(x)*v-F(y)*u for (x,y),(u,v) in zip(p,p[1:]+p[:1])))/2
def edge_cross(a,b,c):return (F(b[0])-a[0])*(F(c[1])-a[1])-(F(b[1])-a[1])*(F(c[0])-a[0])
def vertical_interval(p,x):
 vals=[]
 for a,b in zip(p,p[1:]+p[:1]):
  if min(a[0],b[0])<x<max(a[0],b[0]):vals.append(F(a[1])+(x-a[0])*F(b[1]-a[1],b[0]-a[0]))
 return (min(vals),max(vals)) if vals else None
def partition_proof(target,pieces):
 polys=target+pieces;edges=[(a,b) for p in polys for a,b in zip(p,p[1:]+p[:1])];xs={F(x) for p in polys for x,y in p}
 # Every edge crossing is a slab boundary; endpoint ordering is fixed inside slabs.
 for (a,b),(c,d) in combinations(edges,2):
  r=(b[0]-a[0],b[1]-a[1]);s=(d[0]-c[0],d[1]-c[1]);det=r[0]*s[1]-r[1]*s[0]
  if not det:continue
  q=(c[0]-a[0],c[1]-a[1]);t=F(q[0]*s[1]-q[1]*s[0],det);u=F(q[0]*r[1]-q[1]*r[0],det)
  if 0<=t<=1 and 0<=u<=1:xs.add(a[0]+t*r[0])
 slices=0
 for l,r in zip(sorted(xs),sorted(xs)[1:]):
  x=(l+r)/2;ts=[a for p in target if (a:=vertical_interval(p,x))];ps=[a for p in pieces if (a:=vertical_interval(p,x))];ys=sorted({y for z in ts+ps for y in z})
  for lo,hi in zip(ys,ys[1:]):
   y=(lo+hi)/2;nt=sum(a<y<b for a,b in ts);np=sum(a<y<b for a,b in ps)
   assert nt<=1,'target overlaps itself';assert np==nt,('gap,overlap or outside',x,y,nt,np)
   slices+=1
 return {'areas':[str(area(p)) for p in pieces],'total':str(sum(area(p) for p in pieces)),'vertical_atomic_slices':slices}
def covered(a,b,drawn):
 if a==b:return False
 axis=0 if b[0]!=a[0] else 1;den=b[axis]-a[axis];segs=[];cuts={F(0),F(1)}
 for c,d in drawn:
  if edge_cross(a,b,c) or edge_cross(a,b,d):continue
  lo,hi=sorted((F(c[axis]-a[axis],den),F(d[axis]-a[axis],den)));lo=max(lo,F(0));hi=min(hi,F(1))
  if lo<hi:segs.append((lo,hi));cuts|={lo,hi}
 for lo,hi in zip(sorted(cuts),sorted(cuts)[1:]):
  mid=(lo+hi)/2
  if not any(u<=mid<=v for u,v in segs):return False
 return True
def polygons(pts,edges,shape):
 drawn=[(pts[e[0]],pts[e[1]]) for e in edges];out=set()
 for names in combinations(sorted(pts),4):
  for rest in permutations(names[1:]):
   ns=(names[0],)+rest;p=[pts[n] for n in ns];turn=[edge_cross(p[i],p[(i+1)%4],p[(i+2)%4]) for i in range(4)]
   if not all(t>0 for t in turn):continue
   if not all(covered(p[i],p[(i+1)%4],drawn) for i in range(4)):continue
   # Equal diagonal midpoints characterize a parallelogram independently of author angle sort.
   if any(p[0][j]+p[2][j]!=p[1][j]+p[3][j] for j in [0,1]):continue
   v=[(p[(i+1)%4][0]-p[i][0],p[(i+1)%4][1]-p[i][1]) for i in range(4)]
   if shape=='square':
    if len({x*x+y*y for x,y in v})!=1 or v[0][0]*v[1][0]+v[0][1]*v[1][1]:continue
   if shape=='rhombus' and len({x*x+x*y+y*y for x,y in v})!=1:continue
   out.add(''.join(names))
 return sorted(out)
def triangles(m,edges):
 p=m['points'];drawn=[(p[e[0]],p[e[1]]) for e in edges]
 return [''.join(ns) for ns in combinations(sorted(p),3) if edge_cross(*(p[n] for n in ns)) and all(covered(p[a],p[b],drawn) for a,b in combinations(ns,2))]
CODES=['abcdef','bc','abdeg','abcdg','bcfg','acdfg','acdefg','abc','abcdefg','abcdfg']
DECODE={frozenset(s):str(i) for i,s in enumerate(CODES)}
def physical_moves(m,budget=None):
 n=len(m['initial']);old={(i,s) for i,c in enumerate(m['initial']) if c!='_' for s in CODES[int(c)]};empty={(i,s) for i in range(n) for s in 'abcdefg'}-old;budget=m['budget'] if budget is None else budget;outs={}
 for removed in combinations(sorted(old),budget):
  for added in combinations(sorted(empty),budget):
   new=(old-set(removed))|set(added);ds=[]
   for i in range(n):
    seg=frozenset(s for j,s in new if j==i)
    if not seg and m.get('empty'):ds.append('_')
    elif seg in DECODE:ds.append(DECODE[seg])
    else:break
   if len(ds)!=n:continue
   occ=[i for i,c in enumerate(ds) if c!='_']
   if not occ:continue
   if m.get('equation'):
    if int(ds[0])+int(ds[1])!=int(ds[2]):continue
    val=None
   else:
    if occ!=list(range(min(occ),max(occ)+1)):continue
    if len(occ)>1 and ds[occ[0]]=='0':continue
    val=int(''.join(ds[i] for i in occ))
   outs[''.join(ds)]={'value':val,'removed':removed,'added':added}
 return {'layouts':sorted(outs),'minimum':min((a['value'] for a in outs.values() if a['value'] is not None),default=None),'physical_configurations':len(outs)}
def placements(poly,w,h):
 out=set()
 for turn in range(4):
  q=[tuple(p) for p in poly]
  for _ in range(turn):q=[(y,-x) for x,y in q]
  lx=min(x for x,y in q);ly=min(y for x,y in q);q=[(x-lx,y-ly) for x,y in q];dx=max(x for x,y in q);dy=max(y for x,y in q)
  for tx in range(w-dx+1):
   for ty in range(h-dy+1):out.add(tuple((x+tx,y+ty) for x,y in q))
 return list(out)
def solve(m):
 k=m['kind']
 if k=='boundary':
  target=set(map(tuple,m['whole']))-set(map(tuple,m['fixed']));out=[]
  for name,cells in m['options'].items():
   for t in m['turns']:
    turned={(x,y) if t==0 else (2-y,x) if t==1 else (2-x,2-y) if t==2 else (y,2-x) for x,y in cells}
    if turned==target:out.append(name+':'+str(90*t))
  return {'valid':sorted(out)}
 if k=='squares':return {'shapes':polygons(m['points'],m['edges'],'square')}
 if k=='partition':return partition_proof(m['target'],m['pieces'])
 if k=='pair_assembly':
  w,h=m['target_size'];target=[[(0,0),(w,0),(w,h),(0,h)]];valid=[];counts={}
  for a,b in combinations(sorted(m['pieces']),2):
   n=0
   for p in placements(m['pieces'][a],w,h):
    for q in placements(m['pieces'][b],w,h):
     try:partition_proof(target,[list(p),list(q)]);n+=1
     except AssertionError:pass
   if n:valid.append(a+b)
   counts[a+b]=n
  return {'valid_pairs':valid,'placement_counts':counts}
 if k=='triangle_remove':return {'before':triangles(m,m['edges']),'after':triangles(m,[e for e in m['edges'] if e not in m['remove']])}
 if k=='rhombus_move':
  plans=[]
  for rem in combinations(sorted(m['edges']),m['budget']):
   for add in combinations(m['new_slots'],m['budget']):
    new=(set(m['edges'])-set(rem))|set(add);got=polygons(m['points'],new,'rhombus')
    if len(got)==m['goal']:plans.append({'removed':list(rem),'added':list(add),'rhombi':got})
  return {'plans':plans}
 if k=='unit_cells':
  units={a:{'LD','RU'} for a in m['full']}
  for item in m['halves']:
   a,b=item.split(':');assert b not in units.setdefault(a,set());units[a].add(b)
  return {'units':str(F(sum(map(len,units.values())),2))}
 if k=='quads':return {'parallelograms':polygons(m['points'],m['edges'],'any'),'rhombi':polygons(m['points'],m['edges'],'rhombus')}
 if k=='seven_build':return {'digits':[i for i,c in enumerate(CODES) if len(set(c))==m['count']]}
 if k=='seven':return physical_moves(m)
 if k=='faces':
  selected={i:f for i,f in enumerate(m['faces']) if f['direction'] in set(m['asked_directions']) and f['visible'] is True}
  return {'labels':[f['label'] for f in selected.values()],'sum':sum(f['dots'] for f in selected.values())}
 raise ValueError(k)
def calc(e,typ):
 def go(n):
  if isinstance(n,ast.Constant):return typ(ast.get_source_segment(e,n))
  a,b=go(n.left),go(n.right)
  if isinstance(n.op,ast.Add):return a+b
  if isinstance(n.op,ast.Sub):return a-b
  if isinstance(n.op,ast.Mult):return a*b
  if isinstance(n.op,ast.Div):return a/b
  raise ValueError(e)
 return go(ast.parse(e,mode='eval').body)
def audit(source=None):
 source=Path(source) if source else HERE/'cases.jsonl';proofs=[];nums=[]
 for raw in source.read_bytes().splitlines():
  r=json.loads(raw);h=hashlib.sha256(raw).hexdigest();got=solve(r['independent_model'])
  for key,value in r['independent_expected'].items():assert got[key]==value,(r['sample_id'],key,got[key],value)
  proofs.append({'sample_id':r['sample_id'],'source_row_sha256':h,'result':got,'status':'PASS_REVIEWER_DIFFERENT_METHOD'})
  if r['independent_model']['kind']=='seven' and r['independent_model'].get('empty'):
   one=physical_moves(r['independent_model'],1);assert not one['layouts'];proofs[-1]['one_move_no_valid_layout']=True
  for s in r['worked_steps']:
   if s.get('expression'):
    f=calc(s['expression'],F);assert f==F(s['result'])
    with localcontext() as c:c.prec=80;d=calc(s['expression'],Decimal);assert abs(d-Decimal(f.numerator)/Decimal(f.denominator))<Decimal('1e-60')
    nums.append({'sample_id':r['sample_id'],'source_row_sha256':h,'expression':s['expression'],'exact':str(f),'decimal_agrees':True})
 for name,items in [('peer_numbers_oracles.jsonl',proofs),('peer_numbers_numeric.jsonl',nums)]:
  (HERE/name).write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for r in items),'utf-8',newline='\n')
 print(json.dumps({'rows':len(proofs),'numeric':len(nums),'source':hashlib.sha256(source.read_bytes()).hexdigest()}))
if __name__=='__main__':
 import sys
 audit(sys.argv[1] if len(sys.argv)>1 else None)
