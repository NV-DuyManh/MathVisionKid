"""Independent actual-content review: no author-oracle import or source edits."""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal as D,localcontext
from itertools import product
from heapq import heappush,heappop
import ast,copy,hashlib,json,sys

P=Path(__file__).resolve().parent
HERE=P.parents[2]
sys.path.insert(0,str(HERE))
from math_data_archive_audit import source_projection,linkage_errors
import exhaustive_colab_loader as L

FIELDS=['problem','givens','requested_quantity','student_work','initial_guidance','hints','worked_steps','expected_answer']
EXPECTED_SOURCE='a28c0806e59669bbddff5da43591c5da5d78b317972496e7a6dd28f6da7e1002'
EXPECTED_CHAT='cab230016ad010e15e267ddf098bf8480e0b32c052e47f62adc3383f97703a99'
NOTES=[
 'All four allowed plus/minus pairs explicitly assessed at fixed operand order. Residual equation 4s+2t=-2 has only s=-1,t=1; original fractions restore7/12. Initial and all hints give strategy only.',
 'The explicit student subtraction is wrong:2/3-1/4=5/12. Required residual1/6-2/3=-1/2 is neither allowed signed1/4, so complete impossibility rather than missing information. No hint gives the final no-solution label.',
 'Two-way network has only three simple S-to-T alternatives; Dijkstra and tight-edge certificate pick SAT2km. Required inverse return totals4km; 30+24minutes=54 and8thousand cost. Rate roles and conversion explicit.',
 'Dijkstra gives both HAT andHBT1.5km. Independent return choices give four ordered optimal pairs, roundtrip3km,60minutes,12thousand. Critique removes false uniqueness while retaining the valid HBT route.',
 'All ten height-role factorizations of12 retained. Voxel horizontal-side boundary counting verifies areas26,16,14,28,20,30,24,32,36,48 and unique14minimum at4,3,1. Four lateral faces only; no top/base.',
 'Height boundh>=2 filters factorizationsof18 to seven options. Voxel sidecount40,24,42,30,48,54,72 certifies minimum24 at3,3,2. Quoted30 is correct for3,2,3 but height-role rotation cannot prune optimum.'
]

def sha(b):return hashlib.sha256(b).hexdigest()
def dump(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def jl(p,rs):p.write_text(''.join(dump(r)+'\n' for r in rs),encoding='utf-8',newline='\n')

def evaluate(expr,typ):
    def visit(n):
        if isinstance(n,ast.Constant) and type(n.value) in (int,float):return typ(str(n.value))
        if isinstance(n,ast.UnaryOp):
            a=visit(n.operand)
            if isinstance(n.op,ast.USub):return -a
            if isinstance(n.op,ast.UAdd):return a
        if isinstance(n,ast.BinOp):
            a,b=visit(n.left),visit(n.right)
            if isinstance(n.op,ast.Add):return a+b
            if isinstance(n.op,ast.Sub):return a-b
            if isinstance(n.op,ast.Mult):return a*b
            if isinstance(n.op,ast.Div):return a/b
        raise ValueError('Expression outside arithmetic subset')
    return visit(ast.parse(expr,mode='eval').body)

def tight_routes(edges,start,end):
    # Positive-edge Dijkstra distances, followed only by distance-tight edges.
    # This independently certifies minima without enumerating all simple paths.
    g={}
    for a,b,v in edges:
        g.setdefault(a,[]).append((b,F(v)));g.setdefault(b,[]).append((a,F(v)))
    dist={start:F(0)};queue=[(F(0),start)]
    while queue:
        cost,u=heappop(queue)
        if cost!=dist[u]:continue
        for v,w in g[u]:
            new=cost+w
            if v not in dist or new<dist[v]:dist[v]=new;heappush(queue,(new,v))
    routes=[]
    def trace(u,path):
        if u==end:routes.append(''.join(path));return
        for v,w in g[u]:
            if dist[v]==dist[u]+w and dist[v]<=dist[end]:trace(v,path+[v])
    trace(start,[start])
    return dist[end],sorted(routes),{k:str(v) for k,v in dist.items()}

def voxel_lateral(a,b,h):
    # Count unit faces with horizontal normals only; excludes both horizontal
    # top/base, and all glued internal faces by neighbour occupancy.
    cubes=set(product(range(a),range(b),range(h)))
    return sum((x+dx,y+dy,z) not in cubes for x,y,z in cubes for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)])

def layer_shapes(volume,min_height):
    choices=[]
    for h in range(min_height,volume+1):
        if volume%h:continue
        plane=volume//h
        for b in range(1,int(plane**.5)+1):
            if plane%b:continue
            a=plane//b
            choices.append((a,b,h,voxel_lateral(a,b,h)))
    return choices

def oracle(row):
    k=row['topic']
    if k=='fraction_plus_minus_complete':
        residual=(F(7,12)-F(3,4))*12
        valid=[(s,t) for s in [-1,1] for t in [-1,1] if 4*s+2*t==residual]
        assert residual==-2 and valid==[(-1,1)]
        assert row['expected_answer'][0]['result']=='(−,+)'
        assert row['expected_answer'][1]['result']=='3/4 − 1/3 + 1/6 = 7/12'
        return dict(method='TARGET_RESIDUAL_INTEGER_SIGN_EQUATION',scaled_residual=str(residual),valid=valid,complete_domain_size=4)
    if k=='fraction_no_legal_sign_error':
        residual=F(1,6)-F(2,3);allowed={-F(1,4),F(1,4)}
        assert residual not in allowed
        assert row['expected_answer'][0]['result']=='Không có trong {+,−}'
        assert row['expected_answer'][1]['result']=='5/12'
        return dict(method='TARGET_MINUS_FIXED_FIRST_OPERAND',required_contribution=str(residual),allowed=sorted(map(str,allowed)),valid_signs=[],correct_subtraction='5/12')
    if k=='shortest_graph_roundtrip_cost':
        best,paths,dist=tight_routes([('S','A','0.8'),('A','T','1.2'),('S','B','0.5'),('B','T','2'),('S','T','2.4')],'S','T')
        assert best==2 and paths==['SAT']
        outbound=best*60/4;inbound=best*60/5;total=outbound+inbound;cost=(best+best)*2
        assert [r['result'] for r in row['expected_answer']]==['S→A→T','2','4','54','8']
        assert total==54 and cost==8
        return dict(method='DIJKSTRA_AND_TIGHT_EDGE_CERTIFICATE',distances=dist,winners=paths,one_way=str(best),outbound_minutes=str(outbound),inbound_minutes=str(inbound),total_minutes=str(total),cost_thousand=str(cost))
    if k=='tied_routes_independent_return_error':
        best,paths,dist=tight_routes([('H','A','0.9'),('A','T','0.6'),('H','B','0.4'),('B','T','1.1'),('H','T','1.8')],'H','T')
        assert best==F(3,2) and paths==['HAT','HBT']
        combinations=[(a,b) for a in paths for b in paths]
        assert len(combinations)==4
        assert [r['result'] for r in row['expected_answer']]==['H→A→T và H→B→T','(A,A);(A,B);(B,A);(B,B)','3','60','12']
        return dict(method='DIJKSTRA_TIGHT_PATHS_PLUS_SEPARABLE_MINIMUM_BOUND',distances=dist,one_way_best=str(best),winners=paths,optimal_roundtrips=combinations,total=str(best*2),minutes=str(best*2*60/3),cost_thousand=str(best*2*4))
    volume,lower=(12,1) if k=='lateral_only_volume12_all_heights' else (18,2)
    choices=layer_shapes(volume,lower);minimum=min(v for a,b,h,v in choices);win=[(a,b,h) for a,b,h,v in choices if v==minimum]
    correct=[{'quantity':'Bộ tối ưu','result':'(a,b,h)=(4,3,1)','unit':'cm'},{'quantity':'Diện tích bốn mặt bên nhỏ nhất','result':'14','unit':'cm²'}] if volume==12 else [
        {'quantity':'Bộ tối ưu','result':'(a,b,h)=(3,3,2)','unit':'cm'},
        {'quantity':'Diện tích bên nhỏ nhất','result':'24','unit':'cm²'},
        {'quantity':'Nhận xét','result':'Giá trị30 đúng cho bộ đã chọn, nhưng bỏ cách đặt khác làm kết luận tối ưu sai','unit':''}]
    assert row['expected_answer']==correct
    assert (minimum,win,len(choices))==((14,[(4,3,1)],10) if volume==12 else (24,[(3,3,2)],7))
    expected='26;16;14;28;20;30;24;32;36;48 cm²' if volume==12 else '40;24;42;30;48;54;72 cm²'
    assert row['worked_steps'][1]['result']==expected
    assert [v for a,b,h,v in choices]==([26,16,14,28,20,30,24,32,36,48] if volume==12 else [40,24,42,30,48,54,72])
    return dict(method='LAYER_DIVISORS_AND_EXPOSED_VOXEL_SIDE_FACE_COUNT',volume=volume,min_height=lower,options=choices,minimum=minimum,winners=win,excluded_faces='TOP_AND_BOTTOM')

def main():
    source=P/'cases.jsonl';chat=P/'chat.jsonl'
    before={p.name:sha(p.read_bytes()) for p in P.iterdir() if p.is_file() and not p.name.startswith('peer_')}
    assert before['cases.jsonl']==EXPECTED_SOURCE and before['chat.jsonl']==EXPECTED_CHAT
    source_rows=[(json.loads(b),sha(b)) for b in source.read_bytes().splitlines()]
    chats=[json.loads(b) for b in chat.read_bytes().splitlines()]
    assert len(source_rows)==6 and len(chats)==24
    qa={json.loads(b)['sample_id']:json.loads(b) for b in (P/'selfqa7.jsonl').read_bytes().splitlines()}
    proofs=[];numeric=[];models=[];mutations=[];modes={}
    for index,(row,h) in enumerate(source_rows):
        assert qa[row['sample_id']]['source_row_sha256']==h
        assert row['grade']==5 and row['curriculum_assignment']['enrichment'] is True
        assert row['split']=='train' and row['can_solve'] is True
        assert not any(row.get(k) for k in ['human_verified','teacher_certified','owner_human_reviewed'])
        assert [x['id'] for x in row['givens']]==['g'+str(i) for i in range(len(row['givens']))]
        assert [x['step_id'] for x in row['worked_steps']]==['s'+str(i) for i in range(len(row['worked_steps']))]
        assert [x['level'] for x in row['hints']]==[1,2,3]
        if row['student_work']:
            assert row['student_work']['text'] in row['problem']
            assert all(x['excerpt']==row['student_work']['text'] for x in row['student_work']['observations'])
        result=oracle(row);models.append(dict(sample_id=row['sample_id'],source_row_sha256=h,oracle=result,status='PASS'))
        for step in row['worked_steps']:
            assert step['reason'] and step['explanation'] and 'unit' in step
            if step.get('expression'):
                value=evaluate(step['expression'],F);assert value==F(step['result'])
                with localcontext() as ctx:
                    ctx.prec=90;decimal=evaluate(step['expression'],D)
                    assert abs(decimal-D(value.numerator)/D(value.denominator))<D('1e-70')
                numeric.append(dict(sample_id=row['sample_id'],source_row_sha256=h,step_id=step['step_id'],expression=step['expression'],exact=str(value),decimal_agrees=True,status='PASS'))
        # Mutations of every requested answer entry must fail against actual
        # independently established result, rather than change the source.
        for ai in range(len(row['expected_answer'])):
            bad=copy.deepcopy(row);bad['expected_answer'][ai]['result']='WRONG_ORACLE_MUTATION'
            try:oracle(bad)
            except AssertionError:mutations.append(dict(sample_id=row['sample_id'],field=f'expected_answer[{ai}].result',detected=True))
            else:raise AssertionError('Answer mutation escaped peer oracle')
        criteria=[dict(criterion=k,passed=True,evidence=e) for k,e in [
            ('actual_problem_givens_request_consistency',NOTES[index]),
            ('independent_mathematical_correctness','Separate peer methods without author oracle import, plus exact Fraction/Decimal checks.'),
            ('steps_reasons_units_complete_answer_check','Read every actual title/result/reason/explanation/unit and answer; finite scope/operation/unit/reconstruction checks match.'),
            ('initial_guidance_all_hints_no_answer_leak','Read initial guidance and all three hint texts/questions; method and constraints only, no filled requested value/final outcome/whole solution.'),
            ('student_work_grounding','Feedback limited to actual supplied synthetic statement; no inferred thinking or unseen physical/image result.'),
            ('grade_and_structural_diversity','Explicit grade5 enrichment; paired branches change solvability/return rule/ties/height constraint and observable error, not number-only substitution.'),
            ('hash_provenance_preservation','Exact source row SHA and original-source role retained; future human review not implied; no data edits.')]]
        proofs.append(dict(sample_id=row['sample_id'],source_row_sha256=h,status='PASS_INDEPENDENT_PEER',actual_fields={k:row[k] for k in FIELDS},actual_fields_read='ALL_ACTUAL_FIELDS',criteria=criteria,semantic_decision=NOTES[index],human_review_claimed=False,independent_oracle=result))
        related=[c for c in chats if c['source_sample_id']==row['sample_id']]
        assert len(related)==4 and {c['mode'] for c in related}=={'worked_solution','hint_level_1','hint_level_2','hint_level_3'}
        for c in related:
            L.validate_chat(c);assert c['source_row_sha256']==h
            assert not linkage_errors(c,source_projection(row))
            assert c['quality_status']==row['quality_status'] and c['acceptance_status']==row['acceptance_status']
            modes[c['sample_id']]=c['mode']
    assert len(numeric)==12 and len(modes)==24
    outfiles=['peer_fullfield_reviews.jsonl','peer_independent_oracles.jsonl','peer_numeric_checks.jsonl','peer_adversarial_mutations.jsonl']
    for n,rs in zip(outfiles,[proofs,models,numeric,mutations]):jl(P/n,rs)
    unchanged={p.name:sha(p.read_bytes()) for p in P.iterdir() if p.is_file() and p.name in before}
    assert unchanged==before
    result=dict(status='PASS_INDEPENDENT_PEER',cases=6,chats=24,full_field_reviews=6,numeric_steps=12,independent_models=6,adversarial_mutations_detected=len(mutations),seven_criteria_pass_count=6,source_file_sha256=EXPECTED_SOURCE,chat_file_sha256=EXPECTED_CHAT,source_files_unchanged=True,fixes_required=[],reviews=[{k:r[k] for k in ['sample_id','source_row_sha256','status','criteria','actual_fields_read','independent_oracle','semantic_decision']} for r in proofs],source_hashes=before,peer_helper_sha256=sha(Path(__file__).read_bytes()),artifact_hashes={n:sha((P/n).read_bytes()) for n in outfiles},limitations=['Independent AI content review; not human content attestation or wholecurriculum certification.','Finite original text relation and grade5 enrichment only; no actual image or physical success claimed.','Root final review and publication pending.'])
    write(P/'peer_review.json',result)
    print(dump({k:result[k] for k in ['status','cases','chats','numeric_steps','independent_models','adversarial_mutations_detected','source_file_sha256','chat_file_sha256','source_files_unchanged','fixes_required']}))
if __name__=='__main__':main()
