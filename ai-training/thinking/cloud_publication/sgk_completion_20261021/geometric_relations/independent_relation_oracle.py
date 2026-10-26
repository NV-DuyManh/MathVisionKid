"""Exact independent finite/polygon oracle; no imports from the author helper."""
from fractions import Fraction as F
from itertools import product,permutations,combinations
import re

def P(poly):return [tuple(F(str(v)) for v in p) for p in poly]
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def area(poly):
 p=P(poly)
 return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(p,p[1:]+p[:1])))/2 if len(p)>2 else F(0)
def intersect(subject,clip):
 out=P(subject);clip=P(clip)
 assert sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(clip,clip[1:]+clip[:1]))>0
 for a,b in zip(clip,clip[1:]+clip[:1]):
  inp=out;out=[]
  if not inp:break
  start=inp[-1]
  for end in inp:
   ds=cross(a,b,start);de=cross(a,b,end)
   if de>=0:
    if ds<0:
     t=ds/(ds-de);out.append((start[0]+t*(end[0]-start[0]),start[1]+t*(end[1]-start[1])))
    out.append(end)
   elif ds>=0:
    t=ds/(ds-de);out.append((start[0]+t*(end[0]-start[0]),start[1]+t*(end[1]-start[1])))
   start=end
 return out
def halfturn(poly,center):
 x,y=map(lambda v:F(str(v)),center)
 return [(2*x-a,2*y-b) for a,b in P(poly)]
def orderings(labels,edges):return [list(p) for p in permutations(labels) if all(p.index(a)<p.index(b) for a,b in edges)]
def ints(text):return [int(x) for x in re.findall(r'-?\d+',text)]

def verify(row):
 m=row['independent_model'];k=m['kind'];answers={a['quantity']:a['result'] for a in row['expected_answer']}
 if k=='half_cells':
  groups={name:set(v) for name,v in m['groups'].items()};allids=set().union(*groups.values())
  assert sum(map(len,groups.values()))==len(allids)==m['total_cells']*2
  assert allids=={str(i)+h for i in range(1,m['total_cells']+1) for h in ['L','U']}
  areas={name:F(len(v),2) for name,v in groups.items()}
  assert all(areas[n]==F(v) for n,v in m['expected_areas'].items())
  for name,a in areas.items():assert F(answers[name])==a
  if 'expected_selected_fraction'in m:
   frac=areas['A']/m['total_cells'];assert frac==F(m['expected_selected_fraction'])==F(answers['Phần A'])
  if 'So sánh'in answers:assert answers['So sánh']=='Bằng diện tích' and len(set(areas.values()))==1
  return dict(method='Exact atom partition and unit-area cardinality; no equality assumption on raw piece counts',group_area={n:str(a) for n,a in areas.items()},atoms_partition_whole=True)
 if k=='common_triangles':
  ar=area(m['rectangle']);t=area(m['T']);u=area(m['U']);overlap=area(intersect(m['T'],m['U']))
  assert overlap==0 and t==u==F(m['expected_triangle_area'])
  assert area(intersect(m['T'],m['rectangle']))==t and area(intersect(m['U'],m['rectangle']))==u
  common=ar-t-u;regions=[common+t,common+u]
  assert common==F(m['expected_C']) and regions[0]==regions[1]==F(m['expected_regions'])
  assert F(answers['M'])==regions[0] and F(answers['N'])==regions[1] and answers['So sánh']=='Bằng diện tích'
  return dict(method='Exact rational polygon intersection and shoelace areas',rectangle=str(ar),triangle_T=str(t),triangle_U=str(u),overlap=str(overlap),common=str(common),regions=list(map(str,regions)))
 if k=='half_transfer':
  cells=set(m['initial']);assert m['remove']in cells and m['landing']in cells and m['landing']!=m['remove']
  retained=cells-{m['remove']};counts={i:1 for i in retained};counts[m['landing']]+=1
  union=F(len(counts),2);paper=F(sum(counts.values()),2)
  assert union==F(m['expected_union_area']) and paper==F(m['expected_paper_area'])
  assert F(answers['Vùng phủ'])==union and answers['Điều kiện bị vi phạm']=='Các miếng không chồng và không để hở miền đích'
  return dict(method='Exact atomic occupied-set union versus layer multiplicity',covered_atoms=sorted(counts),double_covered_atoms=[c for c,n in counts.items() if n==2],union_area=str(union),layer_area_sum=str(paper))
 if k=='parallelogram_ordered':
  a,b,c=[tuple(m[n]) for n in ['A','B','C']];d=(a[0]+c[0]-b[0],a[1]+c[1]-b[1])
  assert cross(a,b,c)!=0 and list(d)==m['expected_D'] and ints(answers['D'])==list(d)
  assert answers['Cạnh đối']=='AB song song DC; BC song song AD'
  return dict(method='Diagonals share midpoint: A+C=B+D, independent of learner side-step construction',D=list(d),diagonal_double_midpoint=[a[i]+c[i] for i in range(2)],nonzero_area=True)
 if k=='parallelogram_unordered':
  pts=[tuple(p) for p in m['points']];lo,hi,bot,top=m['bounds'];ds=[]
  assert cross(*pts)!=0
  for d in product(range(lo,hi+1),range(bot,top+1)):
   if d in pts:continue
   # Pair each of the three original points with candidate D as diagonals.
   if any(tuple(d[i]+p[i] for i in range(2))==tuple(sum(q[i] for q in pts if q!=p) for i in range(2)) for p in pts):ds.append(list(d))
  assert ds==m['expected_Ds'] and ints(answers['Mọi D'])==[v for p in ds for v in p] and int(answers['Số vị trí'])==len(ds)
  return dict(method='Enumerate all35 bounded lattice candidate points; equal diagonal midpoints for allthree pairings',lattice_candidates=(hi-lo+1)*(top-bot+1),valid_D=ds)
 if k in ['layer_orders','layer_orders_remove']:
  os=orderings(m['labels'],m['edges']);assert os==m['expected_orders']
  if k=='layer_orders':
   given={tuple(v.split('-')) for v in answers['Thứ tự'].split(';')};assert given==set(map(tuple,os)) and answers['Tính duy nhất']=='Chưa duy nhất' and len(os)>1
   return dict(method='Exhaust all24 total permutations against pairwise global-layer inequalities',orders=os)
  remaining=[v for v in m['edges'] if v!=m['remove']];after=orderings(m['labels'],remaining)
  assert after==m['expected_after'] and answers['Cả ba dòng']=='Không có thứ tự hợp lệ' and answers['Khi bỏ dòng cuối']=='A trước C; thứ tự A-B-C'
  return dict(method='Exhaust all6 permutations before and after one specified-edge removal',orders=os,after_removing_requested_edge=after)
 if k in ['circle_forward','circle_inverse']:
  n=m['count'];r=F(m['radius']) if k=='circle_forward' else F(m['length'])/(2*n)
  centers=[r+2*r*i for i in range(n)];left=centers[0]-r;right=centers[-1]+r;length=right-left;span=centers[-1]-centers[0];width=2*r
  assert left==0 and all(centers[i+1]-centers[i]==2*r for i in range(n-1))
  if k=='circle_forward':
   assert length==F(m['expected_length'])==F(answers['Dài khung']) and width==F(m['expected_width'])==F(answers['Rộng khung']) and span==F(m['expected_center_span'])==F(answers['O1O3'])
  else:
   assert r==F(m['expected_radius'])==F(answers['Bán kính']) and span==F(m['expected_center_span'])==F(answers['Đoạn tâm đầu-cuối'])
  return dict(method='Reconstruct successive tangent intervals and bounding extrema from centers',radius=str(r),centers=list(map(str,centers)),full_length=str(length),width=str(width),center_span=str(span))
 if k=='trapezoid_rotate':
  lower,upper,target=map(P,[m['lower'],m['upper'],m['target']]);moved=halfturn(upper,m['center']);overlap=area(intersect(lower,moved));total=area(lower)+area(moved)-overlap;targetarea=area(target)
  assert overlap==F(m['expected_overlap'])==0 and total==targetarea==F(m['expected_area'])
  assert area(intersect(lower,target))==area(lower) and area(intersect(moved,target))==area(moved)
  assert ints(answers['Chữ nhật'])==[int(v) for v in m['expected_dimensions']] and F(answers['Diện tích'])==total
  oldperimeter=F(8+5+5+4);newperimeter=F(2*(13+2));assert list(map(str,[oldperimeter,newperimeter]))==m['expected_perimeters']
  assert F(answers['Chu vi cũ'])==oldperimeter and F(answers['Chu vi mới'])==newperimeter
  return dict(method='Exact transformed polygons, clipped intersection and target-containment plus shoelace conservation',source_piece_areas=[str(area(lower)),str(area(upper))],rotated_vertices=[list(map(str,p)) for p in moved],overlap=str(overlap),union=str(total),target=str(targetarea),gap='0',old_perimeter=str(oldperimeter),new_perimeter=str(newperimeter))
 if k=='trapezoid_bad_translate':
  lower,bad,upper,target=map(P,[m['lower'],m['upper_bad'],m['upper_original'],m['target']]);overlap=area(intersect(lower,bad));badunion=area(lower)+area(bad)-overlap;gap=area(target)-badunion
  good=halfturn(upper,m['center']);goodoverlap=area(intersect(lower,good));goodunion=area(lower)+area(good)-goodoverlap
  assert overlap==F(m['expected_overlap']) and gap==F(m['expected_gap']) and badunion==F(m['expected_bad_union']) and goodunion==F(m['expected_good_union']) and goodoverlap==0
  assert ints(answers['Phần chồng'])==[7,0,10,0,7,4,6] and ints(answers['Phần hở'])==[11,4,14,4,14,0,6]
  assert F(answers['Vùng phủ sau tịnh tiến'])==badunion and answers['Phép sửa']=='Nửa vòng quanh M, ghép chữ nhật14×4 cm'
  return dict(method='Exact convex polygon clipping and union areas for two different rigid motions',bad_intersection_vertices=[list(map(str,p)) for p in intersect(lower,bad)],bad_overlap=str(overlap),bad_union=str(badunion),target_gap=str(gap),good_overlap=str(goodoverlap),good_union=str(goodunion),good_rotated_vertices=[list(map(str,p)) for p in good])
 raise ValueError(k)
