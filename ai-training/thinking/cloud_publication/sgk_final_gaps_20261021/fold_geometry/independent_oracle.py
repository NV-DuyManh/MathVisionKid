"""Independent exact geometry/state oracles, never parses child worked steps."""
from fractions import Fraction as F
from itertools import combinations
from copy import deepcopy

def cross(a,b,c):return (F(b[0])-F(a[0]))*(F(c[1])-F(a[1]))-(F(b[1])-F(a[1]))*(F(c[0])-F(a[0]))
def signed(p):return sum(F(a[0])*F(b[1])-F(a[1])*F(b[0])for a,b in zip(p,p[1:]+p[:1]))/2
def area(p):return abs(signed(p))
def clip(poly,clipper):
 out=[tuple(map(F,p))for p in poly];cp=list(clipper)
 if signed(cp)<0:cp.reverse()
 for a,b in zip(cp,cp[1:]+cp[:1]):
  old=out;out=[]
  if not old:break
  for s,e in zip(old,old[1:]+old[:1]):
   ds,de=cross(a,b,s),cross(a,b,e)
   if ds>=0:out.append(s)
   if (ds<0<de)or(de<0<ds):
    u=ds/(ds-de);out.append((s[0]+u*(e[0]-s[0]),s[1]+u*(e[1]-s[1])))
 return out
def parallel(a,b,c,d):return (b[0]-a[0])*(d[1]-c[1])==(b[1]-a[1])*(d[0]-c[0])
def tangram(m):
 ps=m['pieces'];A=[area(p)for p in ps];s=F(m['square_side'])
 assert len(ps)==7 and sum(A)==s*s
 assert all(0<=F(x)<=s and 0<=F(y)<=s for p in ps for x,y in p)
 intersections=[area(clip(a,b))for a,b in combinations(ps,2)];assert not any(intersections)
 return A,intersections

def oracle(m):
 k=m['kind'];proof={}
 if k=='disk':
  result=F(m['pi'])*F(m['radius'])**2;assert result==F(m['area'])and m['finite_exact']is False
  proof=dict(area=str(result),finite_exact=False,reason='Finite positive-radius arcs remain curved under rigid sector rearrangement; bounding rectangle is not identical to curved union.')
 elif k=='disk_estimate':
  a=F(m['pi'])*F(m['radius'])**2;b=F(m['rectangle'][0])*F(m['rectangle'][1]);assert (a,b,a-b)==tuple(F(m[x])for x in ['area','rect','gap'])
  proof=dict(area=str(a),rectangle=str(b),difference=str(a-b),finite_exact=False)
 elif k=='fold_equal':
  n=m['parts'];assert n in[2,4,8]and 0<m['selected']<n
  # Unit interval is repeatedly mapped to half its support; endpoints expanded on unfolding.
  levels=n.bit_length()-1;points={F(0),F(1)}
  for _ in range(levels):points|={F(i,2**(_+1))for i in range(2**(_+1)+1)}
  assert sorted(points)==[F(i,n)for i in range(n+1)]
  proof=dict(parts=n,creases=n-1,selected_fraction=str(F(m['selected'],n)))
  if m['total']is not None:proof['length']=str(F(m['total'])*m['selected']/n)
 elif k=='perpendicular_fold':
  # Reflect the ray direction (1,0) to (-1,0) while fixing its origin.
  assert m['point_fixed']and m['line_coincides'];normal=(F(1),F(0));v=(F(1),F(0));ref=(v[0]-2*normal[0],v[1]-2*normal[1]);assert ref==(-1,0)and F(m['angle'])==90
  proof=dict(ray_reflected=list(map(int,ref)),crease_direction=[0,1],dot_product=0,angle=90)
 elif k=='fold_cells':
  w,h=m['w'],m['h'];seed=(w,h)if len(m['folds'])==1 else(w//2+1,h//2+1)
  removed={seed,(w+1-seed[0],seed[1])}
  if len(m['folds'])==2:removed|={(x,h+1-y)for x,y in list(removed)}
  assert removed=={tuple(x)for x in m['removed']}and w*h-len(removed)==m['expected']
  # Components by edge adjacency distinguish one central hole versus separate notches.
  left=set(removed);groups=[]
  while left:
   component={left.pop()};front=list(component)
   while front:
    x,y=front.pop()
    for p in[(x+1,y),(x-1,y),(x,y+1),(x,y-1)]:
     if p in left:left.remove(p);component.add(p);front.append(p)
   groups.append(sorted(component))
  proof=dict(removed=sorted(removed),remaining=w*h-len(removed),components=groups)
 elif k in['tangram','tangram_groups']:
  aa,inter=tangram(m)
  if k=='tangram':assert aa==list(map(F,m['areas']));proof=dict(areas=list(map(str,aa)),pair_intersection_areas=list(map(str,inter)),sum=str(sum(aa)),fractions=[str(a/F(m['square_side'])**2)for a in aa])
  else:
   x=sum(aa[i]for i in m['x']);y=sum(aa[i]for i in m['y']);c=1-x/F(m['square_side'])**2
   assert (x,y,c)==tuple(F(m[z])for z in ['x_area','y_area','complement']);proof=dict(x_area=str(x),y_area=str(y),complement=str(c),pair_intersections_zero=True)
 elif k=='circle_chain':
  cm=[F(m['radii'][0].split()[0])*10,F(m['radii'][1].split()[0])/10,F(m['radii'][2].split()[0])*100];assert cm==list(map(F,m['cm']))
  # Explicit collinear endpoint witnesses, centers O=0,A=r1,B=r1±r2.
  witnesses=sorted([abs(cm[0]-cm[1]),cm[0]+cm[1]]);assert witnesses==list(map(F,m['ob_examples']))
  proof=dict(openings=list(map(str,cm)),ob_witnesses=list(map(str,witnesses)),unique=False)
 elif k=='circle_same':
  a=F(m['first_m'])*100;b=F(m['second_mm'])/10;c=F(m['diameter_cm'])/2;assert a==b==c==F(m['opening']);proof=dict(openings=list(map(str,[a,b,c])))
 elif k=='grid_angle':
  x,y=m['v2'];assert y>0 and abs(x)==abs(y)
  # A diagonal makes equal horizontal and vertical projections, so acute complement is45.
  a=45 if x>0 else 135;assert a==m['angle'];proof=dict(equal_projections=True,side='right'if x>0 else'left',angle=a)
 elif k=='fold_uniform':
  w,h=F(m['w']),F(m['h']);folds=m['folds'];layers=2**folds;foot=w*h/layers;assert foot==F(m['footprint'])and layers==m['layers']and w*h==F(m['original']);proof=dict(width=str(w/2),height=str(h/2),footprint=str(foot),layers=layers,original=str(w*h))
 elif k=='fold_nonuniform':
  # Integer unit cells each carry an original paper label; reflection tracks multiplicity.
  counts={}
  for x in range(m['w']):
   for y in range(m['h']):
    xx=2*m['first_flap']-1-x if x<m['first_flap']else x;yy=m['h']-1-y if y<m['h']//2 else y
    counts[xx,yy]=counts.get((xx,yy),0)+1
  assert len(counts)==m['footprint']and sum(counts.values())==m['total']
  assert set(counts.values())=={v for _,v in m['bands']};proof=dict(footprint=len(counts),layer_area={str(v):list(counts.values()).count(v)for v in sorted(set(counts.values()))},original=sum(counts.values()))
 elif k=='trapezoid':
  A,B,C=m['A'],m['B'],m['C'];valid=[];details={}
  for label,D in m['candidates'].items():
   p=[A,B,C,D];turns=[cross(p[i],p[(i+1)%4],p[(i+2)%4])for i in range(4)];convex=all(t>0 for t in turns)or all(t<0 for t in turns)
   base=parallel(A,B,C,D);other=parallel(B,C,D,A)
   details[label]=dict(convex=convex,base_parallel=base,other_parallel=other)
   if convex and base and not other:valid.append(label)
  assert valid==m['valid'];proof=dict(valid=valid,details=details)
 elif k=='rect_cut':
  a=m['w']*m['h'];nw,nh=m['new'];assert a==nw*nh==m['area']and nw==nh
  assert m['pieces']==[[nw,m['h']],[nw,m['h']]]and sum(y for _,y in m['pieces'])==nh
  per=[2*(m['w']+m['h']),2*(nw+nh)];assert per==m['perimeters'];proof=dict(area=a,perimeters=per,placements=[[0,0,nw,m['h']],[0,m['h'],nw,m['h']]])
 elif k=='par_cut':
  A,B,C,D,E,FF=[m[z]for z in['A','B','C','D','E','F']];shift=m['shift'];p=[A,E,D];q=[[x+shift[0],y+shift[1]]for x,y in p];assert q==[B,FF,C]
  remaining=[E,B,C,D];added=q;assert area(clip(remaining,added))==0
  a=area([A,B,C,D]);rect=area([E,FF,C,D]);assert a==rect==m['area']and area(remaining)+area(added)==rect
  proof=dict(original_area=str(a),transferred_area=str(area(p)),intersection='0',reassembled_area=str(rect))
 elif k=='square_diagonal':
  s=F(m['side']);assert m['triangles']==4 and m['joint']=='hypotenuse'and m['ratio']==[2,1]and s*s==m['area']
  # Pairs of unit right triangles tile two unit squares after scaling by half-diagonal.
  a=[[(0,0),(1,0),(1,1)],[(0,0),(1,1),(0,1)]];assert area(clip(*a))==0 and sum(map(area,a))==1
  proof=dict(small_triangle_area=str(s*s/4),pair_area=str(s*s/2),final_area=str(s*s),ratio=[2,1],normalized_pair_partition=True)
 elif k=='wheel':
  # Count distance in millimetres to avoid copying the cm-to-m worked route.
  mm=F(m['diameter_cm'])*10*F(m['pi'])*F(m['turns']);distance=mm/1000;assert distance==F(m['distance_m']);proof=dict(distance_mm=str(mm),distance_m=str(distance))
 elif k=='wheel_inverse':
  # Convert path km to dm; circumference in dm then divide.
  path=F(m['distance_km'])*10000;circ=2*F(m['pi'])*F(m['radius_dm']);turns=path/circ;assert turns==F(m['turns']);proof=dict(path_dm=str(path),circumference_dm=str(circ),turns=str(turns))
 else:raise AssertionError(k)
 return proof

def adversarial(m):
 """Mutate a declared condition/result so the exact oracle must reject it."""
 k=m['kind'];x=deepcopy(m)
 field={'disk':'finite_exact','disk_estimate':'gap','fold_equal':'parts','perpendicular_fold':'angle','fold_cells':'expected','tangram':'areas','tangram_groups':'x_area','circle_chain':'cm','circle_same':'opening','grid_angle':'angle','fold_uniform':'layers','fold_nonuniform':'total','trapezoid':'valid','rect_cut':'area','par_cut':'area','square_diagonal':'joint','wheel':'distance_m','wheel_inverse':'turns'}[k]
 old=x[field]
 if isinstance(old,bool):x[field]=not old
 elif isinstance(old,list):x[field]=list(reversed(old))if k not in['tangram','trapezoid']else(old+['bogus'])
 elif isinstance(old,int):x[field]=old+1
 elif field=='joint':x[field]='leg'
 else:x[field]=str(F(old)+1)
 try:oracle(x)
 except (AssertionError,ValueError,TypeError):return dict(field=field,original=old,mutation=x[field],rejected=True)
 raise AssertionError('Mutation survived '+k)
