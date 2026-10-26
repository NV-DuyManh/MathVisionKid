"""Separate finite models from explicit authored givens; no author import."""
from collections import Counter
from fractions import Fraction as F
from itertools import combinations,permutations

def edge(a,b):return ''.join(sorted((a,b)))
def triangles(points,edges):
    edges=set(edges);out=[]
    for a,b,c in combinations(points,3):
        x,y=points[a];u,v=points[b];s,t=points[c]
        if (u-x)*(t-y)==(s-x)*(v-y):continue
        if {edge(a,b),edge(a,c),edge(b,c)}<=edges:out.append(a+b+c)
    return sorted(out)

def square_regions(m):
    w,h=m['width'],m['height'];edges=set()
    key=lambda a,b:tuple(sorted((tuple(a),tuple(b))))
    for y in range(h+1):
        for x in range(w):edges.add(key((x,y),(x+1,y)))
    for x in range(w+1):
        for y in range(h):edges.add(key((x,y),(x,y+1)))
    edges-={key(a,b) for a,b in m['removed']};found=[]
    for k in range(1,min(w,h)+1):
        for x in range(w-k+1):
            for y in range(h-k+1):
                border={key((xx,y),(xx+1,y)) for xx in range(x,x+k)}|{key((xx,y+k),(xx+1,y+k)) for xx in range(x,x+k)}|{key((x,yy),(x,yy+1)) for yy in range(y,y+k)}|{key((x+k,yy),(x+k,yy+1)) for yy in range(y,y+k)}
                if border<=edges:found.append(dict(left=x,bottom=y,size=k))
    return found

def collect(m):
    positions={'An':1,'Bình':1};owners={'An':[],'Bình':[]};remaining=dict(m['tokens']);trace=[];winner=None
    for index,(player,steps,named) in enumerate(m['moves'],1):
        assert winner is None and player==('An' if index%2 else 'Bình')
        positions[player]=(positions[player]-1+steps)%m['board']+1
        eligible=[k for k,t in remaining.items() if t['position']==positions[player]]
        if named is not None:
            assert named in eligible;token=named
        elif eligible:
            assert len(eligible)==1;token=eligible[0]
        else:token=None
        if token:owners[player].append(token);del remaining[token]
        scores={p:sum(m['tokens'][t]['value'] for t in ts) for p,ts in owners.items()}
        metric=len(owners[player]) if m['metric']=='tokens' else scores[player]
        if metric>=m['threshold']:winner=player
        trace.append(dict(turn=index,player=player,position=positions[player],received=token,owners={p:list(ts) for p,ts in owners.items()},scores=scores,winner=winner))
    assert winner is not None
    return dict(trace=trace,owners=owners,winner=winner,turn=len(trace),remaining=remaining,scores=trace[-1]['scores'])

def game(m):
    w,h=m['width'],m['height'];names={(x,y):chr(65+y*(w+1)+x) for y in range(h+1) for x in range(w+1)}
    e=lambda a,b:edge(names[a],names[b])
    all_edges={e((x,y),(x+1,y)) for y in range(h+1) for x in range(w)}|{e((x,y),(x,y+1)) for x in range(w+1) for y in range(h)}
    targets={}
    for dx in range(1,w+1):
        for dy in range(1,h+1):
            if m['rhombi_only'] and dx!=dy:continue
            for x in range(w-dx+1):
                for y in range(h-dy+1):
                    border={e((xx,y),(xx+1,y)) for xx in range(x,x+dx)}|{e((xx,y+dy),(xx+1,y+dy)) for xx in range(x,x+dx)}|{e((x,yy),(x,yy+1)) for yy in range(y,y+dy)}|{e((x+dx,yy),(x+dx,yy+1)) for yy in range(y,y+dy)}
                    label=names[x,y]+names[x+dx,y]+names[x+dx,y+dy]+names[x,y+dy];targets[label]=border
    remaining=set(all_edges);trace=[];terminal=False;winner=None
    for index,(player,removed) in enumerate(m['moves'],1):
        assert not terminal and player==('An' if index%2 else 'Bình')
        before={k:s for k,s in targets.items() if s<=remaining}
        assert removed in remaining and any(removed in s for s in before.values())
        remaining.remove(removed);after=sorted(k for k,s in targets.items() if s<=remaining)
        if not after:terminal=True;winner=player
        trace.append(dict(turn=index,player=player,removed=removed,legal=True,remaining_targets=after,terminal=terminal))
    return dict(initial_targets=sorted(targets),trace=trace,winner=winner,terminal=terminal)

def sub(a,b):return (F(a[0])-F(b[0]),F(a[1])-F(b[1]))
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def dot(a,b):return a[0]*b[0]+a[1]*b[1]
def relations(segments):
    parallel=[];perpendicular=[]
    for i,j in combinations(range(len(segments)),2):
        a,b=segments[i];c,d=segments[j];u=sub(b,a);v=sub(d,c)
        assert u!=(0,0) and v!=(0,0)
        det=cross(u,v)
        if det==0:
            if cross(sub(c,a),u)!=0:parallel.append([i,j])
        elif dot(u,v)==0:
            t=cross(sub(c,a),v)/det;s=cross(sub(c,a),u)/det
            if 0<=t<=1 and 0<=s<=1:perpendicular.append([i,j])
    return dict(parallel_pairs=parallel,meeting_perpendicular_pairs=perpendicular)

def check(row):
    m=row['independent_model'];kind=m['kind'];a=row['expected_answer'];topic=row['topic']
    if kind=='boundary':
        # Physical bijections, independent of the author's count-table prose.
        permitted={k for k,labels in m['regions'].items() if any(list(p)==labels for p in permutations(m['dice']))}
        expected=';'.join(sorted(permitted));assert a[0]['result']==expected
        return dict(kind=kind,all_region_count=len(m['regions']),valid=sorted(permitted),die_occurrences=sorted(m['dice']),all_boundary_constraints=True)
    if kind=='shared_plan':
        p=m['points'];metric=m['vertical_scale_squared']
        lengths={e:(p[e[1]][0]-p[e[0]][0])**2+metric*(p[e[1]][1]-p[e[0]][1])**2 for e in m['edges']}
        assert set(lengths.values())=={4};ts=triangles(p,m['edges']);assert ts==['ABC','ABD']
        assert a[0]['result']=='AB;AC;BC;AD;BD' and a[1]['result']==str(len(set(m['edges'])))=='5'
        return dict(kind=kind,distinct_edges=sorted(set(m['edges'])),squared_lengths=lengths,triangles=ts,que_count=len(set(m['edges'])))
    if kind=='shared_repair':
        choices={option:triangles(m['points'],m['edges']+[option]) for option in m['add_options']}
        winners=[k for k,v in choices.items() if {'ABC','ABD'}<=set(v)]
        assert winners==['AB'] and choices['AE']==[]
        assert a[0]['result']==';'.join(winners) and a[1]['result']=='2'
        return dict(kind=kind,all_additions=choices,valid=winners)
    if kind=='squares':
        regions=square_regions(m);names={(0,1):'A',(1,1):'B',(0,0):'C',(1,0):'D'}
        listed=sorted(names[(v['left'],v['bottom'])] for v in regions if v['size']==1)+['toàn bảng' for v in regions if v['size']==2]
        assert a[0]['result']==';'.join(listed) and a[1]['result']==str(len(regions))
        return dict(kind=kind,regions=regions,learner_labels=listed,count=len(regions),square_only=True)
    if kind=='collection':
        out=collect(m)
        ownertext=';'.join(p+':'+','.join(v) for p,v in out['owners'].items())
        assert a[0]['result']==ownertext
        if m['metric']=='score':
            assert a[1]['result']==str(out['scores']['An']) and a[2]['result']==str(out['scores']['Bình'])
            assert a[3]['result']==out['winner']+'; dừng lượt'+str(out['turn'])
        else:assert a[1]['result']==out['winner']+'; dừng lượt'+str(out['turn'])
        assert not out['remaining']
        return dict(kind=kind,**out)
    if kind=='edge_game':
        out=game(m)
        if m['rhombi_only']:
            assert out['initial_targets']==['ABED','BCFE'] and out['terminal'] and out['winner']=='An'
            assert a[0]['result']=='Không còn hình thoi mục tiêu' and a[1]['result']=='An thắng lượt1; Bình không chơi tiếp'
        else:
            assert len(out['initial_targets'])==9 and out['terminal'] and out['winner']=='Bình'
            for r,v in zip(a[:3],out['trace'][:3]):assert set(r['result'].split(';'))==set(v['remaining_targets'])
            assert a[3]['result']=='Không còn mục tiêu' and a[4]['result']=='Bốn lượt hợp lệ; Bình thắng lượt4'
        return dict(kind=kind,**out)
    if kind=='glyph':
        per={k:relations(v) for k,v in m['glyphs'].items()};valid=sorted(k for k,v in per.items() if v['parallel_pairs'] and v['meeting_perpendicular_pairs'])
        assert a[0]['result']==';'.join(valid)
        return dict(kind=kind,relations=per,valid=valid,finite_segment_intersections_required=True)
    raise AssertionError(kind)
