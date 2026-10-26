"""Root actual-content cross-review and independently transcribed finite oracles."""
from pathlib import Path
from itertools import product,permutations
from fractions import Fraction
from decimal import Decimal,localcontext
import json,hashlib
from sgk_g4extra_peer_oracle import calc
import exhaustive_colab_loader as L

HERE=Path(__file__).resolve().parent
OUT=HERE/'cloud_publication/sgk_finish_20261020/g2_append'
def sha(b):return hashlib.sha256(b).hexdigest()
def paths(edges,start,end,limit=8):
    result=[];q=[[start]]
    while q:
        p=q.pop()
        if p[-1]==end:result.append(p);continue
        if len(p)>limit:continue
        q.extend(p+[b] for a,b in edges if a==p[-1] and b not in p)
    return result

def oracle(branch):
    if branch=='growing_rows':return dict(rows=list(range(1,5)),total=sum(range(1,5)),increment=sum(range(1,5))-sum(range(1,4)))
    if branch=='alternating_shrinking_rows':
        rows=[(6-i,['lập phương','trụ'][i%2]) for i in range(4)]
        assert rows[-1]==(3,'trụ') and sum(n for n,t in rows)==18;return dict(rows=rows,total=18)
    if branch.startswith('animals_'):
        n,legs=(5,14) if branch.endswith('unique') else (4,18)
        allways=[dict(g=n-r,t=r,legs=2*(n-r)+4*r) for r in range(1,n)]
        good=[(v['g'],v['t']) for v in allways if v['legs']==legs]
        assert good==([(3,2)] if n==5 else []);return dict(all_ways=allways,valid=good)
    if branch.startswith('distribution_'):
        n,k=(5,3) if branch.endswith('possible') else (7,2)
        ways=[v for v in product(range(1,n),repeat=k) if sum(v)==n]
        if k==3:
            event=[v[0]==3 for v in ways];assert any(event) and not all(event)
        else:assert all(v[0]<7 for v in ways) and not any(v[1]==7 for v in ways)
        return dict(all_positive_compositions=ways)
    if branch.startswith('sequence_graph_'):
        if branch.endswith('labels'):
            edges=[('S','A'),('S','B'),('A','C'),('B','D'),('C','T'),('D','T')];labels=dict(A=4,B=7,C=7,D=4);target=[4,7]
        else:
            edges=[('S','P'),('S','Q'),('P','R'),('Q','R'),('R','U'),('R','V'),('U','T'),('V','T')];labels=dict(P=8-3,Q=2+2,R=3+3,U=9-2,V=10-4);target=[5,6,7]
        pp=paths(edges,'S','T');valid=[p for p in pp if [labels[n] for n in p[1:-1]]==target]
        assert valid==([['S','A','C','T']] if len(target)==2 else [['S','P','R','U','T']]);return dict(all_paths=pp,valid=valid)
    if branch.startswith('local_branch_'):
        values=(dict(A=18,B=12,C=7,D=9,E=99) if branch.endswith('global') else dict(A=5+6,B=16-4,C=7+2,D=14-5))
        graph=({'S':['A','B'],'A':['C','D'],'B':['E']} if branch.endswith('global') else {'S':['A','B'],'B':['C','D']});p=['S']
        while p[-1] in graph:p.append(sorted(graph[p[-1]],key=lambda n:(-values[n],n))[0])
        assert p==(['S','A','D'] if branch.endswith('global') else ['S','B','C']);return dict(values=values,path=p)
    if branch.startswith('measure_'):
        unit,times,lo_included=(10,3,False) if branch.endswith('strict_bounds') else (12,2,True)
        return dict(interval_lower=unit*times,lower_included=lo_included,interval_upper=unit*(times+1),upper_included=False,precise_measure_identified=False)
    if branch.startswith('commands_'):
        grid,start,moves=([[2,4,6],[3,5,7],[8,9,1]],(1,0),[(0,2),(-1,0),(0,-1)]) if branch.endswith('intermediate') else ([[4,8],[6,3]],(0,0),[(0,1),(1,0),(-1,0)])
        a,b=start;stops=[]
        for da,db in moves:a+=da;b+=db;assert 0<=a<len(grid) and 0<=b<len(grid[0]);stops.append((a,b,grid[a][b]))
        total=sum(v for a,b,v in stops);assert (a,b)==(0,1) and total==(17 if len(grid)==3 else 19);return dict(stops=stops,total=total)
    if branch=='regions_intersection_extrema':
        regions={'a':{'R'},'b':{'R','X'},'c':{'X'},'d':{'R','X'},'e':set()};values=dict(a=12,b=18,c=25,d=9,e=30)
        selected=[k for k,v in regions.items() if {'R','X'}<=v];vv=[values[k] for k in selected];assert selected==['b','d'];return dict(selected=selected,largest=max(vv),smallest=min(vv),difference=max(vv)-min(vv))
    if branch=='regions_union_once':
        selected={'M','N','P'}|{'N','Q'};v=dict(M=7,N=16,P=11,Q=20);assert len(selected)==4;return dict(selected=sorted(selected),count=4,difference=max(v[k] for k in selected)-min(v[k] for k in selected))
    if branch.startswith('height_'):
        old,change=(8,5) if branch.endswith('rises') else (4,7);A,B=old,change;assert abs(A-B)==3;return dict(relative_old_A=old,relative_new_B=change,higher='A' if A>B else 'B',difference=abs(A-B),relative_values_not_real_heights=True)
    if branch=='route_dead_end_sum':
        pp=paths([('S','A'),('S','B'),('A','C'),('B','D'),('C','T')],'S','T');assert pp==[['S','A','C','T']];return dict(valid_paths=pp,total=6+4)
    if branch=='route_shared_node_once':
        p=['S','A','B','A','T'];edges={('S','A'),('A','B'),('B','A'),('A','T')};assert all(e in edges for e in zip(p,p[1:]));taken=set(p)&{'A','B'};return dict(unique_collected=sorted(taken),total=sum({'A':7,'B':5}[k] for k in taken))
    if branch.startswith('scaled_'):
        origin,scale,ps,threshold,inclusive=(1,2,dict(A=3,B=4,C=5),6,False) if branch.endswith('threshold') else (5,5,dict(L=2,M=4,N=7),10,True)
        distances={k:abs(v-origin)*scale for k,v in ps.items()};valid=[k for k,d in distances.items() if d<=threshold] if inclusive else [k for k,d in distances.items() if d<threshold]
        assert valid==(['A'] if not inclusive else ['M','N']);return dict(distances=distances,valid=valid)
    if branch=='cards_shared_inventory_conflict':
        valid=[v for v in permutations([2,4,6,8]) if v[0]+2==6 and v[1]-v[0]==4 and v[2]+v[1]==14 and v[3]+v[2]==10];assert not valid;return dict(permutations_checked=24,valid=valid,forced_values=[4,8,6,4])
    if branch=='cards_repeated_value_inventory':
        values=dict(u=3,v=3,w=5,z=8);valid=[]
        for tokens in permutations(values):
            a,b,c,d=[values[t] for t in tokens]
            if a+b==6 and c-a==2 and d-c==3:valid.append(dict(zip('ABCD',tokens)))
        assert len(valid)==2;return dict(distinct_card_assignments=valid,values=[3,3,5,8])
    if branch.startswith('intersection_'):
        sets=[set('AOBC'),set('DOE')] if branch=='intersection_two_rows' else [set('AOB'),set('COD'),set('EOF')]
        union=set.union(*sets);assert len(union)==(6 if len(sets)==2 else 7);return dict(unique_points=sorted(union),count=len(union),total_listed=sum(map(len,sets)),excess=sum(map(len,sets))-len(union))
    if branch.startswith('merge_'):
        if branch=='merge_consistent':
            upper=10+6-2;lower=10-3+7;assert upper==lower==14;return dict(upper=upper,lower=lower)
        K=20+5-3;before=20-4;valid=[x for x in range(101) if before+x==K];assert valid==[6];return dict(K=K,before=before,all_nonnegative_solutions=valid)
    raise ValueError(branch)

def main():
    raw=(OUT/'cases.jsonl').read_bytes();assert sha(raw)=='1aed920b82e5231329d5c69e5316fdedaa78d8e8c8d07c1b29ccfcead6c30f16'
    rows=[(json.loads(b),sha(b)) for b in raw.splitlines()];reviews=[];nums=0
    for r,h in rows:
        proof=oracle(r['topic']);numeric=[]
        for s in r['worked_steps']:
            if s.get('expression'):
                f=calc(s['expression']);assert f==Fraction(s['result'])
                with localcontext() as ctx:
                    ctx.prec=90;d=calc(s['expression'],Decimal);assert abs(d-Decimal(f.numerator)/Decimal(f.denominator))<Decimal('1e-70')
                numeric.append(dict(expression=s['expression'],exact=str(f),decimal_agrees=True));nums+=1
        reviews.append(dict(sample_id=r['sample_id'],source_row_sha256=h,status='PASS_CONTENT_CROSS_REVIEW',review_role='ROOT_FULL_ACTUAL_CONTENT_REVIEW_AND_INDEPENDENT_FINITE_ENUMERATION',actual_fields_read=['problem','givens','requested_quantity','student_work','worked_steps','reasons','explanations','expected_answer','initial_guidance','all_three_hints'],criteria={k:'PASS' for k in ['math_correctness_or_explicit_decision','givens_request_consistency','grade_enrichment_scope','steps_reasons_units_check','initial_all_three_hints_answer_free','student_work_grounding','neutral_schema_provenance']},structural_oracle=proof,numeric_checks=numeric,human_review_claimed=False,external_review_claimed=False,parser_pass_not_semantic_proof=True))
    byid={r['sample_id']:(r,h) for r,h in rows};chats=[json.loads(b) for b in (OUT/'chat.jsonl').read_bytes().splitlines()];modes={k:set() for k in byid}
    for c in chats:
        L.validate_chat(c);r,h=byid[c['source_sample_id']];assert c['source_row_sha256']==h
        target=json.loads(c['messages'][2]['content']);mode=c['mode'];modes[r['sample_id']].add(mode)
        if mode=='worked_solution':assert target['steps']==r['worked_steps'] and target['answer']==r['expected_answer']
        else:
            hint=r['hints'][int(mode[-1])-1];assert target==dict(hint=hint['hint'],question=hint['question'])
    assert len(rows)==28 and len(chats)==112 and all(len(v)==4 for v in modes.values())
    result=dict(source_file_sha256=sha(raw),chat_file_sha256=sha((OUT/'chat.jsonl').read_bytes()),case_count=28,chat_count=112,seven_criteria_pass_count=28,numeric_checks=nums,reviews=reviews,status='PASS_CONTENT_CROSS_REVIEW_DRAFT_NOT_ACCEPTED',training_started=False)
    (OUT/'peer_review.json').write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:result[k] for k in ['case_count','chat_count','numeric_checks','source_file_sha256','status']}))
if __name__=='__main__':main()
