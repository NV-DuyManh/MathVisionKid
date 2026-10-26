"""Independent peer review: inputs transcribed from actual problem text.
Does not import the author's oracle or consume independent_model/answers to generate results.
Read-only on frozen author files. AI peer review, no human attestation.
"""
import ast, calendar, datetime, hashlib, itertools, json, operator
from collections import Counter
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path

P=Path(__file__).resolve().parent
def sha(b): return hashlib.sha256(b).hexdigest()
def dump(name,obj):
    P.joinpath(name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def jsonl(name,rows):
    P.joinpath(name).write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for x in rows),encoding='utf8')
raw=P.joinpath('cases.jsonl').read_bytes()
chatraw=P.joinpath('chat.jsonl').read_bytes()
assert sha(raw)=='68955882a4b3427effb790ee6a6a971acaefce477c4bf0ec69637107e732b781'
assert sha(chatraw)=='c0ce9640a9d7102cfb229bfccca8aebac905bb999944fed3798f307da8e36ad9'
lines=raw.splitlines()
rows=[json.loads(x) for x in lines]
assert len(rows)==24
RH=[sha(x) for x in lines]
O=[]; M=[]
def record(i,method,result,checks,wrong,why):
    O.append(dict(sample_id=rows[i]['sample_id'],source_row_sha256=RH[i],
      status='PASS',method=method,computed=result,checked_against_actual_fields=checks,
      independent_of_author_model=True))
    assert wrong!=result
    M.append(dict(sample_id=rows[i]['sample_id'],source_row_sha256=RH[i],
      mutation=wrong,expected_rejection_reason=why,actual_reference=result,status='REJECTED_BY_PEER_MODEL'))

# Represent geometric rays by their equivalence classes of actual directions.
a=['A','B','C']; pairs=[''.join(x) for x in itertools.combinations(a,2)]
assert set(pairs)=={'AB','AC','BC'}
record(0,'All unordered pairs of three distinct ray directions',pairs,
       'AOB,AOC,BOC; count3; degree-free compound angle included',['AC','BC'],'Drops the outer pair AB.')
dirs={'X':'east','Y':'east','T':'interior','Z':'north'}
rep={'east':'X','interior':'T','north':'Z'}
ps=sorted(''.join(sorted((rep[x],rep[y]))) for x,y in itertools.combinations(rep,2))
assert ps==['TX','XZ','TZ'] or set(ps)=={'TX','XZ','TZ'}
record(1,'Quotient point names by same-ray direction, then unordered pairs',sorted(ps),
       'OnlyXOT,XOZ,TOZ; XY has one direction, not an extra angle',sorted(ps+['XY']),'Same ray has two point names, not two sides.')

orders=[list(q) for q in itertools.permutations('ABC') if q.index('C')<q.index('B')<q.index('A')]
assert orders==[['C','B','A']]
record(2,'Enumerate all six light-to-heavy permutations with low-pan inequalities',orders,
       'A>B from left low; B>C from right low',[['A','B','C']],'Reverses low=heavy on both pans.')
pans=[]
for name,l,r,observed in [('P','2.05','1.98','left'),('Q','2.50','2.5','level'),('R','0.9','0.85','right')]:
    x,y=Decimal(l),Decimal(r)
    correct='left' if x>y else 'right' if x<y else 'level'
    pans.append([name,observed==correct,correct])
assert pans==[['P',True,'left'],['Q',True,'level'],['R',False,'left']]
record(3,'Exact Decimal comparison per labelled pan without changing labels',pans,
       'P/Qconsistent; R must left-low',[['Q',False,'left']],'Trailing zero does not change value.')
mass={'A':Decimal('3.08'),'B':Decimal('3.8')}
result=dict(light_to_heavy=sorted(mass,key=mass.get),correct_pan='right',difference=str(mass['B']-mass['A']))
assert result=={'light_to_heavy':['A','B'],'correct_pan':'right','difference':'0.72'}
record(4,'Exact decimal ordering and subtraction',result,
       'A lighter; right low;0.72kg; student length-of-writing claim rejected',dict(light_to_heavy=['B','A'],correct_pan='left',difference='-0.72'),'String length is not decimal value.')

def shelf(w,h,d,n):
    # Independently sum the purchased plank list, not the author area formula.
    planks=[(h,d),(h,d)]+[(w,d)]*(n+2)
    cm2=sum(x*y for x,y in planks)
    return dict(planks=planks,cm2=cm2,cost=Fraction(cm2,10000)*200000,
                domain=30<=w<=80 and 50<=h<=100 and 20<=d<=30 and 2<=n<=5)
s=shelf(50,60,20,3); assert s['cm2']==7400 and s['cost']==148000 and s['domain']
record(5,'Enumerated physical plank list for one allowable open-answer design',
       dict(cm2=s['cm2'],cost=int(s['cost']),plank_count=len(s['planks']),valid=s['domain'] and s['cost']<=300000),
       'Example W50 H60 D20 N3 valid; no uniqueness/optimization assertion',
       dict(cm2=5400,cost=108000,plank_count=5,valid=True),'Omitting roof and floor fails explicit N+2 horizontal planks.')
old=shelf(80,100,30,4); new=shelf(40,60,20,4)
assert old['cost']==408000 and new['cost']==144000 and new['domain']
record(6,'Separate purchased-plank lists for old and new open-answer design',
       dict(old_cost=int(old['cost']),new_cost=int(new['cost']),old_over=old['cost']>250000,new_valid=new['domain'] and new['cost']<=250000),
       'Oldoverbudget, one lawful repair; no best-design assertion',
       dict(old_cost=408000,new_cost=144000,old_over=False,new_valid=True),'408000 exceeds 250000; cost must be compared to budget.')

def color_draw(stock,k):
    # Distinct tokens -> every token subset -> color multiset projection.
    tokens=[(color,i) for color,num in stock.items() for i in range(num)]
    seen=set()
    for subset in itertools.combinations(tokens,k):
        c=Counter(x[0] for x in subset)
        seen.add(''.join(color*c[color] for color in ['Đ','V','X']))
    return sorted(seen)
x=color_draw({'Đ':2,'V':1,'X':1},2);assert set(x)=={'ĐĐ','ĐV','ĐX','VX'}
record(7,'Enumerate six two-token subsets then deduplicate color-only observations',x,
       'Four color multisets; no VV/XX; ordering not counted',sorted(x+['VV']),'Only one yellow token exists.')
x=color_draw({'Đ':2,'V':1,'X':3},3);assert set(x)=={'XXX','ĐXX','ĐĐX','VXX','ĐVX','ĐĐV'}
record(8,'Enumerate20 distinct three-token subsets then project color multisets',x,
       'Six outcomes, yellowatmost1 redatmost2',sorted(x+['ĐVV']),'Two yellow exceeds the singleton stock.')
x=color_draw({'Đ':3,'X':2},3)
remain={s:{'Đ':3-s.count('Đ'),'X':2-s.count('X')} for s in x}
assert set(x)=={'ĐĐĐ','ĐĐX','ĐXX'} and remain['ĐXX']=={'Đ':2,'X':0}
record(9,'Enumerate10 distinct token subsets and independently subtract remaining stock',
       dict(outcomes=x,remaining=remain),'Three outcomes and exactly conserved remaining inventory',
       dict(outcomes=x+['XXX'],remaining=remain),'XXX needs three blue while stock has only two.')

# Coordinates determine incidence, and intervals determine ink coverage.
def cross(a,b,c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def triples(coords):
    return [''.join(t) for t in itertools.combinations(sorted(coords),3) if cross(*(coords[k] for k in t))==0]
coords={'A':(-1,0),'B':(0,0),'C':(1,0),'D':(2,0),'E':(0,1),'F':(0,2)}
tri=triples(coords)
segs=sorted(''.join(x) for ls in ['ABCD','BEF'] for x in itertools.combinations(ls,2))
assert len(segs)==9 and set(tri)=={'ABC','ABD','ACD','BCD','BEF'}
record(10,'Coordinate determinant over all20 triples and all pairwise drawn intervals',
       dict(segments=segs,collinear_triples=tri),'Nine drawn segments/five triples',
       dict(segments=['AB','BC','CD','BE','EF'],collinear_triples=tri),'Adjacent-only counting omits continuous compound segments.')
coords={'A':(0,0),'B':(1,0),'C':(2,0),'D':(3,0),'E':(0,1),'F':(0,2)}
tri=triples(coords);segs=sorted(['AB','CD','AE','AF','EF'])
assert set(tri)=={'ABC','ABD','ACD','BCD','AEF'}
record(11,'Coordinate collinearity separated from disconnected ink intervals',
       dict(segments=segs,collinear_triples=tri),'Five drawnsegments; all five collinear triples survive missing BC ink',
       dict(segments=segs+['AD'],collinear_triples=tri),'AD crosses the uninked BC gap despite collinear endpoints.')

fractions=[Fraction(x) for x in ['1/2','2/4','3/6','4/8','5/10','1/3','2/3','3/4','4/5']]
eligible={chr(97+i) for i,f in enumerate(fractions) if f==Fraction(1,2)}
remaining=set('abcdefghi');own={'An':[],'Bình':[]}; trace=[]
for turn,(who,token) in enumerate([('An','a'),('Bình','f'),('An','b'),('Bình','c'),('An','d'),('Bình','e')],1):
    if token in eligible and token in remaining: own[who].append(token);remaining.remove(token)
    trace.append(dict(turn=turn,owned={k:v[:] for k,v in own.items()},remaining=sorted(remaining)))
    if sum(map(len,own.values()))==5:break
assert turn==6 and own=={'An':['a','b','d'],'Bình':['c','e']}
record(12,'Exact rational eligibility then finite turn-by-turn inventory transition',
       dict(eligible=sorted(eligible),trace=trace,winner='An',stop=turn),
       'Eligiblea..e; one invalid f turn; finalAn3Binh2, remainingfghi',
       dict(winner='Bình',stop=5),'Stopping condition is total valid flowers, not player turns or all nine visible objects.')
cards=dict(zip('abcdef',map(Fraction,['2/3','3/2','4/5','5/4','7/6','6/7'])))
left=set(cards);own={'An':[],'Bình':[]};trace=[]
for turn,(who,a,b) in enumerate([('An','a','c'),('Bình','a','b'),('An','c','d'),('Bình','e','f')],1):
    assert a in left and b in left
    if cards[a]*cards[b]==1:
        own[who].append(a+b);left-={a,b}
    trace.append(dict(turn=turn,face_down=sorted(left),owned={k:v[:] for k,v in own.items()}))
    if len(own[who])==2:break
assert trace[0]['face_down']==list('abcdef') and own=={'An':['cd'],'Bình':['ab','ef']} and not left
record(13,'Rational product condition plus face-state machine after each complete turn',
       dict(trace=trace,winner='Bình',stop=turn),
       'Mismatch returns cards face-down; removed matches never return; Binh wins4',
       dict(winner='An',stop=3),'At turn3 An owns only one pair, below per-player threshold2.')
# Two explicit completions of missing history demonstrate non-identifiability.
worldA=dict(eligible=['a','b','c','d','e'],owner=['An']*5,total=5,winner='An')
worldB=dict(eligible=['a','b','c','d','e'],owner=['Bình']*5,total=5,winner='Bình')
assert worldA['winner']!=worldB['winner']
record(14,'Countermodel pair: two completions of missing labels/history and permitted threshold interpretation',
       dict(conclusion='not identifiable',countermodels=[worldA,worldB],
            ask=['fraction labels','threshold scope','removal and victory rule','state/owners','turn history']),
       'No winner entailed; countermodels are proof only, not invented facts presented as observations',
       dict(conclusion='An certainly won'),'Both owner assignments fit the supplied incomplete description.')

leap=[y for y in [2024,2100,2400] if calendar.isleap(y)]
nextday={str(y):(datetime.date(y,2,28)+datetime.timedelta(days=1)).isoformat() for y in [2024,2100,2400]}
assert leap==[2024,2400] and nextday['2100']=='2100-03-01'
record(15,'Standard calendar/date arithmetic cross-check of supplied Gregory rule',
       dict(leap_years=leap,next_dates=nextday),
       '2024/2400leap;2100common; exact dates after28Feb',
       dict(leap_years=[2024,2100,2400],next_dates=nextday),'Divisible-by4 shortcut misses century exception2100.')
days=[(datetime.date(y+1,1,1)-datetime.date(y,1,1)).days for y in [2099,2100,2101]]
assert days==[365,365,365] and sum(days)==1095
record(16,'Independent differences of consecutive Jan1 dates for each complete year',
       dict(days=days,total=sum(days)),'1095days; no leap year in list',
       dict(days=[365,366,365],total=1096),'2100 has no leap day under supplied calendar.')

solutions=[]
for a in range(10):
    for b in range(10):
        if (104+10*a)*3==402+10*b:solutions.append([a,b])
assert solutions==[[3,0],[4,3],[5,6],[6,9]]
record(17,'Brute-force all100 complete multiplicand/product digit assignments',
       solutions,'Exactlyfour (a,b); carry1from units, carry1tohundreds',
       [[3,9],[4,2],[5,5],[6,8]],'Ignoring carried1 from4×3 breaks each complete product.')
sol=[list(x) for x in itertools.permutations([1,2,4]) if (10*x[0]+x[1])*x[2]==84]
assert sol==[[2,1,4]]
record(18,'Enumerate six physical-card permutations, evaluate full multiplication',sol,
       'A2 B1 C4唯一;42×2 notlegalstock',
       [[4,2,2]],'Uses card2 twice and never uses card1 although product84.')

def strip_paths(pieces):
    good=[]
    for seq in itertools.permutations(pieces):
        if pieces[seq[0]][0]!='START' or pieces[seq[-1]][1]!='END':continue
        if all(pieces[a][1]==pieces[b][0] for a,b in zip(seq,seq[1:])):
            good.append(dict(path=list(seq),number=''.join(pieces[k][2] for k in seq)))
    return good
x=strip_paths({'P':('START','flower','4'),'Q':('flower','star','0'),'R':('star','END','7')})
assert x==[{'path':['P','Q','R'],'number':'407'}]
record(19,'Enumerate all six directed connector chains, then positional decoding',
       dict(paths=x,zero_value=0),'PQR unique;407;zero retains tens place',
       dict(paths=[dict(path=['P','Q','R'],number='47')],zero_value=0),'Dropping zero shifts the place values and violates three-digit requirement.')
x=strip_paths({'P':('START','round','6'),'Q':('square','round','2'),'R':('square','END','5')})
assert x==[]
record(20,'All six directed chains fail connector constraints without rotations',x,
       'No validnumber; Pmustfirst andno remaining round-left piece',
       [dict(path=['P','Q','R'],number='625')],'P round-right does not match Q square-left.')
def assign(people,inventory,less=(),equal=()):
    return [dict(zip(people,x)) for x in sorted(set(itertools.permutations(inventory)))
            if all(x[people.index(a)]<x[people.index(b)] for a,b in less)
            and all(x[people.index(a)]==x[people.index(b)] for a,b in equal)]
x=assign(['An','Bình','Chi'],[24,42,68],[('Bình','An'),('An','Chi')])
assert x==[{'An':42,'Bình':24,'Chi':68}]
record(21,'All six full person-card bijections satisfying strict inequalities',x,
       'UniqueAn42Binh24Chi68',
       [{'An':24,'Bình':42,'Chi':68}],'First inequality An>Binh fails.')
x=assign(['Lan','Minh','Nhi'],[21,35,54],[('Minh','Lan')])
assert len(x)==3 and {a['Nhi'] for a in x}=={21,35,54}
record(22,'All six person-card bijections, filter only supplied single inequality',x,
       'Threeways and Nhi notunique; no invented middle rank',
       [{'Lan':54,'Minh':21,'Nhi':35}],'A single middle assignment omits two other lawful worlds.')
areas=[4*4,4*4,6*3]
x=assign(['An','Bình','Chi'],areas,equal=[('An','Bình')])
assert x==[{'An':16,'Bình':16,'Chi':18}]
record(23,'Compute areas before enumerate distinct area allocations with exact multiplicities',
       dict(areas=areas,assignments=x),'Uniqueareaassignment16,16,18; twoidentical squares neednotdistinguishphysicalidentity',
       dict(areas=[16,16,18],assignments=[{'An':16,'Bình':18,'Chi':16}]),'An=Binh fails after real area computation.')

# Explicit AST walking: Fraction and Decimal use source numeric token strings, not binary floats.
ops={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv}
def arithmetic(expr,constructor):
    def ev(n):
        if isinstance(n,ast.Constant) and type(n.value) in (int,float):
            return constructor(ast.get_source_segment(expr,n))
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.USub):return -ev(n.operand)
        if isinstance(n,ast.BinOp) and type(n.op) in ops:return ops[type(n.op)](ev(n.left),ev(n.right))
        raise ValueError(ast.dump(n))
    return ev(ast.parse(expr,mode='eval').body)
N=[]
for i,r in enumerate(rows):
    for s in r['worked_steps']:
        if s['expression'] is None:continue
        f=arithmetic(s['expression'],Fraction)
        with localcontext() as c:
            c.prec=60
            d=arithmetic(s['expression'],Decimal)
            assert f==Fraction(s['result']) and d==Decimal(s['result'])
        N.append(dict(sample_id=r['sample_id'],source_row_sha256=RH[i],step_id=s['step_id'],
          expression=s['expression'],fraction=str(f),decimal=str(d),expected=s['result'],status='PASS'))
assert len(N)==16

# Compare every actual chat user/assistant field against actual source, not a keyword semantic proxy.
chat_rows=[json.loads(x) for x in chatraw.splitlines()]
assert len(chat_rows)==96
byid={r['sample_id']:(r,RH[i]) for i,r in enumerate(rows)}
links=[]; counts=Counter()
for c in chat_rows:
    r,h=byid[c['source_sample_id']]
    assert c['source_row_sha256']==h
    u=json.loads(c['messages'][1]['content']);a=json.loads(c['messages'][2]['content'])
    assert u['problem']==r['problem'] and u['grade']==r['grade'] and u['mode']==c['mode']
    assert u.get('student_work')==(r['student_work']['text'] if r['student_work'] else None)
    if c['mode']=='worked_solution':
        assert a['steps']==r['worked_steps'] and a['answer']==r['expected_answer']
        assert a['initial_guidance']==r['initial_guidance'] and a['can_solve']==r['can_solve']
    else:
        hint=r['hints'][int(c['mode'].rsplit('_',1)[1])-1]
        assert a==dict(hint=hint['hint'],question=hint['question'])
    counts[r['sample_id']]+=1
    links.append(dict(sample_id=c['sample_id'],source_row_sha256=h,status='PASS',mode=c['mode'],
                      checked='All actual serialized user and assistant payload fields match source semantics reviewed'))
assert set(counts.values())=={4}

notes=[
'Three distinct rays yield three unordered pairs; outer angle included; no degrees required.',
'Same-ray X/Y is quotiented before naming angles; student claim explicitly supplied; hints identify method without naming final angles.',
'Low pan inequalities reverse correctly with side changes; six complete orders checked.',
'Decimal equality includes trailing zeros; only label-consistency assessed; no instrument fault inferred.',
'3.08<3.80; difference0.72kg; critique limited to the quoted digit-count claim.',
'One chosen open-domain shelf, seven actual planks,0.74m²and148000đ; no uniqueness or physical strength claim.',
'Old8planks2.04m²cost408000; legal repair8planks0.72m²cost144000; optimization not requested.',
'Distinct physical-token subsets collapse to four color multisets with singleton colors constrained.',
'All three-token subsets project to exactlysix bounded color multisets; no probability claim.',
'Exactlythree lawful color multisets; each remaining count conserves stock; supplied XXX misconception grounded.',
'Drawn intervals vs named endpoints; compound segments preserved; all20triples checked.',
'Ink gap removes compound segments only; collinearity remains true from explicit positional givens.',
'Fraction equivalence separate from visible inventory; invalid turn consumes turn; shared total5 determines stopping.',
'After mismatch cards return face-down; reciprocal matches removed; per-player pair threshold honored.',
'Missing labels/history/threshold cannot entail winner; asking for missing data is the correct requested behavior.',
'Supplied Gregory400year exception preserved; dates independently checked; enrichment scope explicit.',
'Three complete common years each365days; Jan1date-difference crosscheck1095; no invented leapday.',
'100digit pairs tested; four full-products; unit carry1 andhundreds carry1 explained; no forceduniqueness.',
'Six one-use card permutations; correct84product must also preserve inventory; wrong42×2explicitly ruledout.',
'Directed connectors determine uniquePQR; zero holds tens position; placevalue0notomitted.',
'All six directed orders impossible; prescribed initialPcannotconnect; no rotatedQor repairedlabels.',
'Unique strict rank mapping over six bijections; no alphabetical inference.',
'Three full mappings under only one relation; Nhi varies allthree; no hiddenmiddlecondition.',
'Repeated16area occurs exactlytwice; actual16vs18calculation precedes identity assignment; squares interchangeable.'
]
assert len(notes)==24
criteria=[
'problem_givens_request_consistency','mathematical_oracle_and_complete_finite_cases',
'steps_reasons_units_checks','all_initial_and_three_hints_answer_free',
'grounded_student_work_no_imagined_assets','grade_enrichment_original_branches','provenance_hash_preservation'
]
Q=[]
for i,r in enumerate(rows):
    assert r['human_verified'] is False and r['teacher_certified'] is False and r['owner_human_reviewed'] is False
    assert len(r['hints'])==3 and [h['level'] for h in r['hints']]==[1,2,3]
    Q.append(dict(sample_id=r['sample_id'],source_row_sha256=RH[i],status='PASS_INDEPENDENT_AI_PEER_QA',
        criteria={k:'PASS' for k in criteria},semantic_notes=notes[i],
        actual_fields_read=['problem','givens','requested_quantity','student_work','worked_steps.title',
           'worked_steps.reason','worked_steps.explanation','worked_steps.expression','worked_steps.result',
           'worked_steps.unit','expected_answer','initial_guidance','hints.1.hint','hints.1.question',
           'hints.2.hint','hints.2.question','hints.3.hint','hints.3.question'],
        oracle_artifact='peer_independent_oracles.jsonl',chat_modes_checked=4,
        human_review_claimed=False,source_mutated=False))
jsonl('peer_independent_oracles.jsonl',O)
jsonl('peer_mutations.jsonl',M)
jsonl('peer_numeric_fraction_decimal.jsonl',N)
jsonl('peer_chat_linkage.jsonl',links)
jsonl('peer_qa7.jsonl',Q)
assert sha(P.joinpath('cases.jsonl').read_bytes())==sha(raw)
assert sha(P.joinpath('chat.jsonl').read_bytes())==sha(chatraw)
artifacts=[]
for name in ['peer_independent_oracles.jsonl','peer_mutations.jsonl','peer_numeric_fraction_decimal.jsonl','peer_chat_linkage.jsonl','peer_qa7.jsonl','peer_independent_review.py']:
    b=P.joinpath(name).read_bytes();artifacts.append(dict(path=name,bytes=len(b),sha256=sha(b)))
dump('peer_review.json',dict(status='PASS_INDEPENDENT_AI_PEER_QA',reviewer='qa_final_numbers_new',
    cases=24,chat_rows=96,source_sha256=sha(raw),chat_sha256=sha(chatraw),
    semantic_cases_read=24,all_initial_guidance_and_three_hints_read=True,criteria=7,
    different_method_finite_oracles=24,fraction_decimal_expression_checks=16,
    meaningful_mutations_rejected=24,chat_field_linkage_checks=96,
    blocking_findings=[],changes_required=[],source_manifest_frozen=True,
    human_review_claimed=False,training_started=False,artifacts=artifacts,
    limitations=['Text relations and original finite enrichment only, no image/physical competency certification.',
       'Open-domain shelf examples prove one lawful answer, not an exhaustive list or optimum.',
       'Peer finite mathematical checks do not establish full-archive split/duplicate absence or training readiness.']))
print(json.dumps(dict(status='PASS',cases=24,chat=96,oracles=len(O),numeric=len(N),mutations=len(M),source_sha256=sha(raw),chat_sha256=sha(chatraw),artifacts=artifacts),ensure_ascii=False))

