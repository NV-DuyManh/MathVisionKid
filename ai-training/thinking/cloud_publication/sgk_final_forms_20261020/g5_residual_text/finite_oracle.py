"""Separate finite enumeration from actual fixed constraints; no author import."""
from fractions import Fraction
from itertools import product


def graph_paths(edges,start,end):
    graph={}
    for a,b,value in edges:
        graph.setdefault(a,[]).append((b,Fraction(value)));graph.setdefault(b,[]).append((a,Fraction(value)))
    found=[]
    def visit(path,total):
        if path[-1]==end:found.append((''.join(path),total));return
        for nxt,length in graph[path[-1]]:
            if nxt not in path:visit(path+[nxt],total+length)
    visit([start],Fraction(0));return sorted(found)


def lateral(volume,minheight):
    return [(a,b,h,2*h*(a+b)) for h in range(minheight,volume+1) for a in range(volume,0,-1) for b in range(a,0,-1) if a*b*h==volume]


def check(row):
    name=row['topic'];answer=[x['result'] for x in row['expected_answer']]
    if name=='fraction_plus_minus_complete':
        nums=[Fraction(3,4),Fraction(1,3),Fraction(1,6)];target=Fraction(7,12)
        values={''.join(signs):str(nums[0]+(1 if signs[0]=='+' else -1)*nums[1]+(1 if signs[1]=='+' else -1)*nums[2]) for signs in product('+-',repeat=2)}
        valid=[s for s,v in values.items() if Fraction(v)==target]
        assert valid==['-+'] and answer[0]=='(−,+)';return dict(all_values=values,valid=valid)
    if name=='fraction_no_legal_sign_error':
        values={'+':Fraction(2,3)+Fraction(1,4),'-':Fraction(2,3)-Fraction(1,4)}
        assert all(v!=Fraction(1,6) for v in values.values()) and answer[1]=='5/12'
        return dict(all_values={k:str(v) for k,v in values.items()},valid_signs=[],mathematical_impossibility_not_missing_input=True)
    if name=='shortest_graph_roundtrip_cost':
        paths=graph_paths([('S','A','0.8'),('A','T','1.2'),('S','B','0.5'),('B','T','2'),('S','T','2.4')],'S','T')
        best=min(v for p,v in paths);winners=[p for p,v in paths if v==best]
        minutes=(best/4+best/5)*60;cost=best*2*2
        assert winners==['SAT'] and best==2 and minutes==54 and cost==8
        assert answer[1:]==['2','4','54','8'];return dict(paths=[(p,str(v)) for p,v in paths],minimum=str(best),winners=winners,minutes=str(minutes),cost=str(cost))
    if name=='tied_routes_independent_return_error':
        paths=graph_paths([('H','A','0.9'),('A','T','0.6'),('H','B','0.4'),('B','T','1.1'),('H','T','1.8')],'H','T')
        pairs=[(a,b,va+vb) for a,va in paths for b,vb in paths];minimum=min(v for a,b,v in pairs);winning=[(a,b) for a,b,v in pairs if v==minimum]
        assert len(pairs)==9 and len(winning)==4 and minimum==3 and answer[2:]==['3','60','12']
        return dict(all_paths=[(p,str(v)) for p,v in paths],all_roundtrip_pairs=[(a,b,str(v)) for a,b,v in pairs],winners=winning,minutes=str(minimum/3*60),cost=str(minimum*4))
    volume,minheight=(12,1) if name=='lateral_only_volume12_all_heights' else (18,2)
    options=lateral(volume,minheight);best=min(s for a,b,h,s in options);winners=[(a,b,h) for a,b,h,s in options if s==best]
    assert (best,winners)==((14,[(4,3,1)]) if volume==12 else (24,[(3,3,2)]))
    assert answer[1]==str(best)
    return dict(volume=volume,min_height=minheight,options=options,best=best,winners=winners,faces_scope='FOUR_LATERAL_ONLY')
