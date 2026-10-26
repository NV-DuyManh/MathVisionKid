"""Independent exhaustive finite geometric/or physical-slot oracle; no tutor text matching."""
from fractions import Fraction as F
from itertools import combinations,permutations,product
from math import atan2
import json

def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def area(p):return abs(sum(F(p[i][0])*p[(i+1)%len(p)][1]-F(p[(i+1)%len(p)][0])*p[i][1] for i in range(len(p)))/2)
def clip(poly,edgea,edgeb):
    out=[]
    if not poly:return []
    for a,b in zip(poly,poly[1:]+poly[:1]):
        x,y=cross(edgea,edgeb,a),cross(edgea,edgeb,b)
        if x>=0:out.append(a)
        if (x<0<y) or (y<0<x):
            t=F(x,x-y);out.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])))
    return out
def intersection(p,q):
    for a,b in zip(q,q[1:]+q[:1]):p=clip(p,a,b)
    return p
def ccw(p):
    p=[tuple(map(F,a)) for a in p]
    if sum(p[i][0]*p[(i+1)%len(p)][1]-p[(i+1)%len(p)][0]*p[i][1] for i in range(len(p)))<0:p.reverse()
    return p
def partition(target,pieces):
    # targets here convex except the house, decomposed explicitly to its convex square+roof.
    targets=[ccw(p) for p in target];pieces=[ccw(p) for p in pieces]
    for p in pieces:assert sum(area(intersection(p,t)) for t in targets)==area(p),'outside target'
    for a,b in combinations(pieces,2):assert area(intersection(a,b))==0,'interior overlap'
    assert sum(map(area,pieces))==sum(map(area,targets)),'gap'
    return [str(area(p)) for p in pieces]
def covered(a,b,edges):
    if a==b:return False
    d=(b[0]-a[0],b[1]-a[1]);idx=0 if d[0] else 1;intervals=[]
    for p,q in edges:
        if cross(a,b,p) or cross(a,b,q):continue
        x,y=sorted((F(p[idx]-a[idx],d[idx]),F(q[idx]-a[idx],d[idx])))
        x=max(F(0),x);y=min(F(1),y)
        if x<=y:intervals.append((x,y))
    end=F(0)
    for x,y in sorted(intervals):
        if x>end:return False
        end=max(end,y)
    return end==1
def polygons(points,edge_names,shape):
    edges=[(points[e[0]],points[e[1]]) for e in edge_names]
    out=[]
    for names in combinations(sorted(points),4):
        ctr=[sum(points[n][i] for n in names)/4 for i in range(2)]
        ns=sorted(names,key=lambda n:atan2(points[n][1]-ctr[1],points[n][0]-ctr[0]))
        vs=[points[n] for n in ns]
        if any(cross(vs[i],vs[(i+1)%4],vs[(i+2)%4])<=0 for i in range(4)):continue
        if not all(covered(vs[i],vs[(i+1)%4],edges) for i in range(4)):continue
        if vs[0][0]+vs[2][0]!=vs[1][0]+vs[3][0] or vs[0][1]+vs[2][1]!=vs[1][1]+vs[3][1]:continue
        ds=[(vs[(i+1)%4][0]-vs[i][0],vs[(i+1)%4][1]-vs[i][1]) for i in range(4)]
        metric=lambda u:u[0]*u[0]+u[1]*u[1]+(u[0]*u[1] if shape=='rhombus_axial' else 0)
        if shape in ('square','rhombus_axial') and len({metric(u) for u in ds})!=1:continue
        if shape=='square' and ds[0][0]*ds[1][0]+ds[0][1]*ds[1][1]!=0:continue
        out.append(''.join(sorted(names)))
    return sorted(out)
def triangles(points,edge_names):
    edges=[(points[e[0]],points[e[1]]) for e in edge_names]
    return [''.join(ns) for ns in combinations(sorted(points),3) if cross(*(points[n] for n in ns)) and all(covered(points[a],points[b],edges) for a,b in combinations(ns,2))]
SEG=[set(s) for s in ('abcdef','bc','abdeg','abcdg','bcfg','acdfg','acdefg','abc','abcdefg','abcdfg')]
def seven_moves(initial,budget,empty=False,equation=False):
    old={(i,s) for i,d in enumerate(initial) if d!='_' for s in SEG[int(d)]};out=[]
    alphabet=list(range(10))+(['_'] if empty else [])
    for ds in product(alphabet,repeat=len(initial)):
        occupied=[i for i,d in enumerate(ds) if d!='_']
        if not occupied:continue
        if not equation:
            if occupied!=list(range(min(occupied),max(occupied)+1)):continue
            if len(occupied)>1 and ds[occupied[0]]==0:continue
        new={(i,s) for i,d in enumerate(ds) if d!='_' for s in SEG[d]}
        rem,add=old-new,new-old
        if len(rem)!=budget or len(add)!=budget:continue
        if equation and ds[0]+ds[1]!=ds[2]:continue
        out.append(dict(layout=''.join(map(str,ds)),value=int(''.join(str(ds[i]) for i in occupied)) if not equation else None,removed=sorted(rem),added=sorted(add)))
    return out
def rot(cells,k,size=3):
    s=set(map(tuple,cells))
    for _ in range(k):s={(size-1-y,x) for x,y in s}
    return s
def placements(poly,w,h):
    # Exhaust all quarter-turn + integer-translation placements within fixed rectangular target.
    res=set()
    for k in range(4):
        q=[tuple(p) for p in poly]
        for _ in range(k):q=[(-y,x) for x,y in q]
        for tx in range(-8,9):
            for ty in range(-8,9):
                r=tuple(sorted((x+tx,y+ty) for x,y in q))
                if all(0<=x<=w and 0<=y<=h for x,y in r):res.add(r)
    return [ccw(sorted(p,key=lambda a:atan2(a[1]-sum(t[1] for t in p)/len(p),a[0]-sum(t[0] for t in p)/len(p)))) for p in res]
def solve(m):
    k=m['kind']
    if k=='boundary':
        whole=set(map(tuple,m['whole']));fixed=set(map(tuple,m['fixed']));valid=[]
        for name,cs in m['options'].items():
            for turn in m['turns']:
                s=rot(cs,turn)
                if not s&fixed and s|fixed==whole:valid.append(name+':'+str(turn*90))
        return dict(valid=sorted(valid))
    if k=='squares':return dict(shapes=polygons(m['points'],m['edges'],'square'))
    if k=='pair_assembly':
        options={}
        for a,b in combinations(sorted(m['pieces']),2):
            valid=0
            for p in placements(m['pieces'][a],*m['target_size']):
                for q in placements(m['pieces'][b],*m['target_size']):
                    if not area(intersection(p,q)) and area(p)+area(q)==m['target_size'][0]*m['target_size'][1]:valid+=1
            options[a+b]=valid
        return dict(valid_pairs=sorted(a for a,n in options.items() if n),placement_counts=options)
    if k=='partition':
        areas=partition(m['target'],m['pieces'])
        return dict(areas=areas,total=str(sum(map(F,areas))))
    if k=='triangle_remove':
        before=triangles(m['points'],m['edges']);after=triangles(m['points'],[e for e in m['edges'] if e not in m['remove']])
        return dict(before=before,after=after)
    if k=='rhombus_move':
        successes=[];old=set(m['edges'])
        for rem in combinations(sorted(old),m['budget']):
            for add in combinations(m['new_slots'],m['budget']):
                final=(old-set(rem))|set(add);sh=polygons(m['points'],final,'rhombus_axial')
                if len(sh)==m['goal']:successes.append(dict(removed=list(rem),added=list(add),rhombi=sh))
        return dict(plans=successes)
    if k=='unit_cells':
        assert len(set(m['full']))==len(m['full'])
        assert not set(m['full'])&{s.split(':')[0] for s in m['halves']}
        assert len(set(m['halves']))==len(m['halves'])
        # Each declared half is one explicit diagonal half of a distinct unit cell; both halves may occur.
        n=F(len(m['full']))+F(len(m['halves']),2);return dict(units=str(n))
    if k=='quads':return dict(parallelograms=polygons(m['points'],m['edges'],'parallelogram'),rhombi=polygons(m['points'],m['edges'],'rhombus_axial'))
    if k=='seven_build':return dict(digits=[i for i,s in enumerate(SEG) if len(s)==m['count']])
    if k=='seven':
        out=seven_moves(m['initial'],m['budget'],m.get('empty',False),m.get('equation',False))
        return dict(layouts=sorted(x['layout'] for x in out),minimum=min((x['value'] for x in out if x['value'] is not None),default=None),moves=out)
    if k=='faces':
        selected=[f for f in m['faces'] if f['visible'] and f['direction'] in m['asked_directions']]
        return dict(labels=[f['label'] for f in selected],sum=sum(f['dots'] for f in selected))
    raise ValueError(k)
def check(row):
    result=solve(row['independent_model']);expected=row['independent_expected']
    for k,v in expected.items():assert result[k]==v,(row['sample_id'],k,result[k],v)
    return result

