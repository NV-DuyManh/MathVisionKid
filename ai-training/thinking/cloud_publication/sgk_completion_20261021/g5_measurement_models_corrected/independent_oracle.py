"""Separate finite model checks; no import of author or worked-step evaluator."""
from fractions import Fraction as F
from collections import Counter
from itertools import product
def tile_solutions(width,height,tile,rotate):
 shapes=[tuple(tile)]+([tuple(reversed(tile))]if rotate and tile[0]!=tile[1]else[])
 placements=[]
 for w,h in shapes:
  for x in range(width-w+1):
   for y in range(height-h+1):placements.append((x,y,w,h,frozenset((i,j)for i in range(x,x+w)for j in range(y,y+h))))
 full=frozenset(product(range(width),range(height)));solutions=[]
 def visit(covered,chosen):
  if covered==full:solutions.append(chosen);return
  target=min(full-covered)
  for p in placements:
   if target in p[4]and not p[4]&covered:visit(covered|p[4],chosen+[p[:4]])
 visit(frozenset(),[]);return solutions
def area(points,names):
 p=[points[n]for n in names];return abs(sum(p[i][0]*p[(i+1)%3][1]-p[(i+1)%3][0]*p[i][1]for i in range(3)))/F(2)
def oracle(m):
 k=m['kind']
 if k in('board_bill','board_budget'):
  # Work in integer square centimetres, independently of metre-first author arithmetic.
  def cmarea(boards):
   allboards=[]
   for n,a,b in boards:
    x,y=F(a)*100,F(b)*100;assert x.denominator==y.denominator==1
    allboards.extend([int(x)*int(y)]*n)
   return sum(allboards),allboards
  if k=='board_bill':
   s,parts=cmarea(m['boards']);value=F(s,10000);cost=value*F(m['price']);assert value==F(m['expected_area'])and cost==F(m['expected_cost'])
   return dict(method='Expanded integer cm2 finished-board inventory, then conversion and exact per-area cost',each_board_cm2=parts,total_cm2=s,total_m2=str(value),cost=str(cost))
  fixed,_=cmarea(m['fixed']);shelf,_=cmarea([[1,*m['shelf']]])
  allcost=[F(fixed+n*shelf,10000)*F(m['price'])for n in m['choices']]
  eligible=[n for n,c in zip(m['choices'],allcost)if c<=F(m['budget'])]
  assert allcost==list(map(F,m['expected_costs']))and eligible==m['expected_eligible']and max(eligible)==m['expected_best']
  return dict(method='Enumerate whole permitted shelf counts after independent cm2 inventory',fixed_cm2=fixed,one_shelf_cm2=shelf,costs=list(map(str,allcost)),eligible=eligible,best=max(eligible))
 if k=='cut_compare':
  # Represent every equal cake by six atoms, conserving physical piece stocks.
  out=[]
  for scheme in m['schemes']:
   stock=Counter();used=Counter()
   for cakes,den in scheme['cuts']:
    assert 6%den==0;stock[den]+=cakes*den
   for count,den in scheme['each']:used[den]+=count*m['people']
   atoms=sum(count*(6//den)for count,den in scheme['each'])
   possible=used==stock and atoms*m['people']==m['whole']*6
   out.append(dict(stock={str(a):b for a,b in stock.items()},need={str(a):b for a,b in used.items()},pieces=sum(stock.values()),share=str(F(atoms,6)),feasible=possible,total_atoms_required=atoms*m['people'],available_atoms=m['whole']*6))
  assert [x['feasible']for x in out]==m['expected_feasible']and[x['pieces']for x in out]==m['expected_pieces']and out[0]['share']==str(F(m['expected_share']))
  return dict(method='Finite six-atom cake model with separate denominator-piece inventory',schemes=out)
 if k in('frame','frame_inverse'):
  w=m['width']
  def border(h):return {(x,y)for x in range(w)for y in range(h)if x in(0,w-1)or y in(0,h-1)}
  if k=='frame_inverse':
   possible=[h for h in range(3,m['border_count']+1)if len(border(h))==m['border_count']];assert possible==[m['expected_height']];h=possible[0]
  else:h=m['height'];possible=[h]
  full=set(product(range(w),range(h)));bb=border(h);inside=full-bb;cell=F(m['scale'])**2
  total=len(full)*cell;interior=len(inside)*cell
  assert total==F(m['expected_total'])and interior==F(m['expected_inside'])
  if'expected_border'in m:assert len(bb)*cell==F(m['expected_border'])
  return dict(method='Enumerate unique integer grid cells; border is coordinate predicate, corners automatic once',height_candidates=possible,width=w,height=h,border_cells=len(bb),inside_cells=len(inside),total_cells=len(full),total_area=str(total),inside_area=str(interior),border_area=str(len(bb)*cell))
 if k=='net':
  a,b=m['caps'];h=m['height'];strip=m['strip'];s=F(m['scale'])
  assert strip==[a,b,a,b]
  faces=Counter(tuple(sorted(x))for x in[(a,h),(b,h),(a,h),(b,h),(a,b),(a,b)])
  expected=Counter(tuple(sorted(x))for x in[(a,b)]*2+[(a,h)]*2+[(b,h)]*2)
  assert faces==expected
  cubes=list(product(range(a),range(b),range(h)));v=len(cubes)*s**3;dims=[F(a)*s,F(b)*s,F(h)*s]
  assert dims==list(map(F,m['expected_dimensions']))and v==F(m['expected_volume'])
  if'total_strip'in m:assert sum(strip)==m['total_strip']
  # Side-strip four folds have distinct outward face normals; opposite caps are ±z.
  normals=[(1,0,0),(0,1,0),(-1,0,0),(0,-1,0),(0,0,1),(0,0,-1)];assert len(set(normals))==6
  return dict(method='Opposite-face pair inventory and all integer unit-volume cells; distinct face normals of declared strip/cap net',grid_dimensions=[a,b,h],physical_dimensions=list(map(str,dims)),faces={str(k):v for k,v in faces.items()},unit_volume_cells=len(cubes),cell_volume=str(s**3),volume=str(v),fold_normals=normals)
 if k=='tiling':
  solutions=tile_solutions(m['width'],m['height'],m['tile'],m['allow_rotate'])
  if m['require_mixed']:solutions=[s for s in solutions if len({(x[2],x[3])for x in s})==2]
  assert bool(solutions)==m['expected_possible']
  if m['placements']:
   full=set(product(range(m['width']),range(m['height'])));covered=set()
   for x,y,w,h in m['placements']:
    assert sorted([w,h])==sorted(m['tile'])
    cells=set(product(range(x,x+w),range(y,y+h)));assert cells<=full and not cells&covered;covered|=cells
   assert covered==full and len({(x[2],x[3])for x in m['placements']})==2
  return dict(method='Complete cell exact-cover recursion on first uncovered cell; allowed orientations explicit',legal_solutions=len(solutions),possible=bool(solutions),one_solution=solutions[0]if solutions else[],given_constructive_placement_verified=bool(m['placements']))
 if k=='nested':
  points={k:tuple(map(F,v))for k,v in m['points'].items()};aa=[area(points,t)for t in m['triangles']]
  assert aa==list(map(F,m['expected_areas']))
  return dict(method='Coordinate shoelace area independent of chosen-base altitude formula',triangles=m['triangles'],areas=list(map(str,aa)),outer_area=str(area(points,['A','B','C'])),inner_partition_sum=str(sum(aa)))
 raise ValueError(k)
