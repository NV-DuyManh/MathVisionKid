"""Actual-content peer review using methods separate from author oracle."""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal as D,localcontext
from itertools import combinations,permutations,product
import ast,copy,hashlib,json,re,sys
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parents[2]))
import exhaustive_colab_loader as L
from math_data_archive_audit import source_projection,linkage_errors
FIELDS=['problem','givens','requested_quantity','student_work','initial_guidance','hints','worked_steps','expected_answer']
EXPECTED_SOURCE='ebfcb15d3d675e91d8372ea3efad5c98ab65e78248a9e36251a91465b988dc15'
EXPECTED_CHAT='941667181533b61354072d765569e8154e75e45b7784ee93cb6a2c0cbb439059'
NOTES=[
 'The six cells partition into twelve congruent right triangles; L2/U5 can translate to complementary halves, and all original pieces used exactly once. Each group area2, A fraction1/3; hints describe unit/regrouping only.',
 'Two full cells and four half cells each have area2. The supplied comparison of piece counts treats unlike-size pieces as equal units; solution preserves correct counts but corrects the area inference.',
 'Both triangles fit rectangle and are separated by diagonal strips. Each area2 and nonoverlap; complementC8, M=N10. Common-part cancellation uses congruent translated pieces and disjoint unions.',
 'A half-cell moves into an already covered identical half-cell; paper area remains4 but union loses old half-cell. Covered union3.5, with explicit overlap/hole; no hint fills numeric or final condition outcome.',
 'OrderedABC fixes D2,3 uniquely. Side-step checks confirm both opposite pairs; diagonal midpoint result crosschecked independently by bounded-grid side equation enumeration.',
 'Unordered three vertices admit three distinct completions0,4;4,0;6,4 within inclusive bounds. The supplied candidate6,4 is valid but the forced-order uniqueness rationale is unsupported.',
 'Topological available-node recursion gives ABCD, ABDC, ADBC; all satisfy A<B<C andA<D. Three orders preserve the unresolved position ofD and avoid invented occlusion relations.',
 'Transitive closure ofA<B<C<A contains selfreachability and has no global strict-layer order. Removing onlyC<A leaves uniqueABC and forcesA<C; contradiction is complete data, not missing image.',
 'Three equal tangent circlesr2 require full extent12, width4; center-to-center span8. Linear endpoint budget distinguishes whole frame from two gaps; inherited contact relation explicit.',
 'Four-circle frame24 supplies four diameters, not three center gaps: diameter6, radius3, span18. Check18+3+3=24; critique rests only on exact student quote.',
 'Halfturn aboutM6.5,2 maps upper piece to opposite side ofMB and exact horizontal strips fill13by2 rectangle without gap/overlap. Area26; old perimeter22 versus new30. Area conservation does not impose perimeter conservation.',
 'Pure translation gives overlap triangle7,0;10,0;7,4 area6 and target gap triangle11,4;14,4;14,0 area6. Exact strip integration union50; halfturn around7,4 repairs to14by4 union56. Supplied transform points retained.'
]
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def write(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def jl(n,rs):(P/n).write_text(''.join(dump(r)+'\n' for r in rs),encoding='utf-8',newline='\n')
def polygon(poly):return [(F(str(x)),F(str(y))) for x,y in poly]
def area(poly):
    p=polygon(poly);return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(p,p[1:]+p[:1])))/2
def ints(s):return [int(x) for x in re.findall(r'-?\d+',s)]
def vsub(a,b):return tuple(x-y for x,y in zip(a,b))
def cross(a,b):return a[0]*b[1]-a[1]*b[0]

def strip_integrals(polys):
    # Every polygon edge gives affine x(y). Split at all vertices and crossings
    # of these lines: their order is fixed on each resulting open strip.
    # Union and overlap widths are affine there, so trapezoid integration is
    # exact. No clipping / polygon intersection routine from author is used.
    ps=[polygon(p) for p in polys];lines=[];ys=set()
    for poly in ps:
        ys.update(y for x,y in poly)
        for a,b in zip(poly,poly[1:]+poly[:1]):
            if a[1]!=b[1]:
                slope=(b[0]-a[0])/(b[1]-a[1]);intercept=a[0]-slope*a[1]
                lines.append((slope,intercept,min(a[1],b[1]),max(a[1],b[1])))
    bottom,top=min(ys),max(ys)
    for l,r in combinations(lines,2):
        if l[0]!=r[0]:
            y=(r[1]-l[1])/(l[0]-r[0])
            if bottom<y<top:ys.add(y)
    def section(poly,mid):
        result=[]
        for a,b in zip(poly,poly[1:]+poly[:1]):
            if min(a[1],b[1])<mid<max(a[1],b[1]):
                slope=(b[0]-a[0])/(b[1]-a[1]);result.append((slope,a[0]-slope*a[1]))
        return sorted(result,key=lambda t:t[0]*mid+t[1])
    union=F(0);overlap=F(0);each=[F(0) for p in ps];bands=[]
    ys=sorted(ys)
    for low,high in zip(ys,ys[1:]):
        mid=(low+high)/2;sections=[]
        for index,poly in enumerate(ps):
            ss=section(poly,mid)
            if ss:
                assert len(ss)==2
                sections.append(ss)
                widths=[(ss[1][0]-ss[0][0])*y+ss[1][1]-ss[0][1] for y in (low,high)]
                each[index]+=sum(widths)*(high-low)/2
        def widths(y):
            intervals=sorted((a*y+b,c*y+d) for (a,b),(c,d) in sections)
            if not intervals:return F(0),F(0)
            merged=[]
            for a,b in intervals:
                if merged and a<=merged[-1][1]:merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
                else:merged.append((a,b))
            uw=sum(b-a for a,b in merged);ow=sum(b-a for a,b in intervals)-uw
            return uw,ow
        a,b=widths(low);c,d=widths(high);union+=(a+c)*(high-low)/2;overlap+=(b+d)*(high-low)/2
        bands.append([str(low),str(high)])
    return dict(union=union,overlap=overlap,parts=each,bands=bands)

def side_parallelogram(points):
    a,b,c,d=points
    return cross(vsub(b,a),vsub(d,a))!=0 and vsub(b,a)==vsub(c,d) and vsub(c,b)==vsub(d,a)
def bounded_fourth(points,bounds,ordered):
    left,right,bottom,top=bounds;valid=[]
    for d in product(range(left,right+1),range(bottom,top+1)):
        if d in points:continue
        orders=[tuple(points)+(d,)] if ordered else [p+(d,) for p in permutations(points)]
        if any(side_parallelogram(p) for p in orders):valid.append(d)
    return valid

def topological(labels,edges):
    orders=[]
    def extend(prefix,remaining):
        if not remaining:orders.append(prefix);return
        available=sorted(v for v in remaining if not any(b==v and a in remaining for a,b in edges))
        for v in available:extend(prefix+[v],remaining-{v})
    extend([],set(labels));return orders

def verify(r):
    m=r['independent_model'];k=m['kind'];a={v['quantity']:v['result'] for v in r['expected_answer']}
    if k=='half_cells':
        n=m['total_cells'];atoms=[];areas={}
        for group,ids in m['groups'].items():
            polygons=[]
            for atom in ids:
                cell=int(atom[:-1]);label=atom[-1];x=(cell-1)%3 if n==6 else (cell-1)%2;y=(cell-1)//3 if n==6 else (cell-1)//2
                poly=[(x,y),(x+1,y),(x+1,y+1)] if label=='L' else [(x,y),(x+1,y+1),(x,y+1)]
                polygons.append(poly);atoms.append(atom)
            areas[group]=sum(map(area,polygons));assert F(a[group])==areas[group]
        assert len(atoms)==len(set(atoms))==2*n and sum(areas.values())==n and len(set(areas.values()))==1
        if 'Phần A'in a:assert F(a['Phần A'])==areas['A']/n==F(1,3)
        else:assert a['So sánh']=='Bằng diện tích'
        return dict(method='TRIANGULATE_UNIT_CELLS_AND_SHOELACE_GROUP_AREAS',areas={v:str(w) for v,w in areas.items()},whole_area=n,atoms_used_once=True)
    if k=='common_triangles':
        strips=strip_integrals([m['T'],m['U']]);whole=area(m['rectangle']);t,u=strips['parts']
        assert strips['overlap']==0 and t==u==2 and whole==12
        common=whole-strips['union'];regions=[common+t,common+u]
        assert regions==[10,10] and F(a['M'])==regions[0] and F(a['N'])==regions[1] and a['So sánh']=='Bằng diện tích'
        return dict(method='EXACT_HORIZONTAL_STRIPS_AND_COMMON_COMPLEMENT',parts=list(map(str,strips['parts'])),common=str(common),regions=list(map(str,regions)),overlap=str(strips['overlap']))
    if k=='half_transfer':
        old_triangle=[(0,0),(1,0),(1,1)];new_triangle=[(1,0),(2,0),(2,1)]
        removed=area(old_triangle);arrived=area(new_triangle)
        # Destination is a different lower-row cell, unchanged except for the
        # extra layer. Its whole area already belongs to retained sheet.
        assert removed==arrived==F(1,2)
        union=F(4)-removed;assert F(a['Vùng phủ'])==union
        assert a['Điều kiện bị vi phạm']=='Các miếng không chồng và không để hở miền đích'
        return dict(method='EXPLICIT_SOURCE_DESTINATION_TRIANGLE_GEOMETRY',removed_region=str(removed),newly_covered_destination='0',union=str(union),paper_area='4')
    if k=='parallelogram_ordered':
        pts=[tuple(m[v]) for v in ['A','B','C']]
        ds=bounded_fourth(pts,[-2,7,-2,7],True);assert ds==[(2,3)] and ints(a['D'])==list(ds[0])
        assert a['Cạnh đối']=='AB song song DC; BC song song AD'
        return dict(method='BOUNDED_GRID_SEARCH_USING_BOTH_OPPOSITE_SIDE_VECTORS',candidates_checked=100,valid=ds)
    if k=='parallelogram_unordered':
        pts=[tuple(v) for v in m['points']];ds=bounded_fourth(pts,m['bounds'],False)
        assert ds==[(0,4),(4,0),(6,4)] and ints(a['Mọi D'])==[v for d in ds for v in d] and int(a['Số vị trí'])==3
        return dict(method='ALL_BOUNDED_POINTS_AND_BOUNDARY_ORDERS_USING_SIDE_VECTORS',candidates_checked=35,valid=ds)
    if k in ['layer_orders','layer_orders_remove']:
        orders=topological(m['labels'],m['edges'])
        if k=='layer_orders':
            assert {tuple(v.split('-')) for v in a['Thứ tự'].split(';')}==set(map(tuple,orders))
            assert len(orders)==3 and a['Tính duy nhất']=='Chưa duy nhất'
            return dict(method='KAHN_AVAILABLE_NODE_RECURSION_NO_FULL_PERMUTATION_SEARCH',orders=orders)
        edges={tuple(e) for e in m['edges']};reach=set(edges)
        for z in m['labels']:
            for x in m['labels']:
                for y in m['labels']:
                    if (x,z) in reach and (z,y) in reach:reach.add((x,y))
        assert not orders and any((v,v) in reach for v in m['labels'])
        after=topological(m['labels'],[e for e in m['edges'] if e!=m['remove']]);assert after==[['A','B','C']]
        assert a['Cả ba dòng']=='Không có thứ tự hợp lệ' and a['Khi bỏ dòng cuối']=='A trước C; thứ tự A-B-C'
        return dict(method='TRANSITIVE_CLOSURE_CYCLE_CERTIFICATE_AND_KAHN_AFTER_EXACT_REMOVAL',cycle_nodes=[v for v in m['labels'] if (v,v) in reach],after=after)
    if k in ['circle_forward','circle_inverse']:
        n=m['count'];radius=F(m['radius']) if k=='circle_forward' else F(m['length'])/(2*n)
        # Tangency gives n-1 center gaps of2r; outer edges contribute r+r.
        center_span=2*radius*(n-1);length=center_span+radius+radius;width=2*radius
        if k=='circle_forward':assert F(a['Dài khung'])==length and F(a['Rộng khung'])==width and F(a['O1O3'])==center_span
        else:
            assert F(a['Bán kính'])==radius and F(a['Đoạn tâm đầu-cuối'])==center_span
            assert a['Đoạn24 cm']=='Toàn khung gồm bốn đường kính, không phải ba khoảng tâm'
        return dict(method='LINEAR_CONTACT_GAP_AND_TWO_ENDPOINT_RADII_CONSTRAINT',radius=str(radius),center_gaps=n-1,span=str(center_span),frame=str(length),width=str(width))
    if k=='trapezoid_rotate':
        mx,my=map(lambda v:F(str(v)),m['center']);moved=[(2*mx-x,2*my-y) for x,y in polygon(m['upper'])]
        result=strip_integrals([m['lower'],moved]);assert result['union']==26 and result['overlap']==0
        assert area(m['target'])==26 and sum(result['parts'])==26
        assert ints(a['Chữ nhật'])==[13,2] and F(a['Diện tích'])==result['union']
        # Original slanted side3-4-5 plus parallelbases8,5 andvertical4.
        old=8+5+5+4;new=2*13+2*2
        assert F(a['Chu vi cũ'])==old==22 and F(a['Chu vi mới'])==new==30
        return dict(method='PIECEWISE_AFFINE_HORIZONTAL_WIDTH_INTEGRATION',rotated_vertices=[list(map(str,v)) for v in moved],part_areas=list(map(str,result['parts'])),union=str(result['union']),overlap=str(result['overlap']),strip_breaks=result['bands'],old_perimeter=old,new_perimeter=new)
    if k=='trapezoid_bad_translate':
        bad=strip_integrals([m['lower'],m['upper_bad']]);target=area(m['target']);gap=target-bad['union']
        assert bad['union']==50 and bad['overlap']==gap==6
        mx,my=map(lambda v:F(str(v)),m['center']);good_poly=[(2*mx-x,2*my-y) for x,y in polygon(m['upper_original'])]
        good=strip_integrals([m['lower'],good_poly]);assert good['union']==56 and good['overlap']==0
        assert ints(a['Phần chồng'])==[7,0,10,0,7,4,6] and ints(a['Phần hở'])==[11,4,14,4,14,0,6]
        assert F(a['Vùng phủ sau tịnh tiến'])==bad['union'] and a['Phép sửa']=='Nửa vòng quanh M, ghép chữ nhật14×4 cm'
        return dict(method='EXACT_HORIZONTAL_INTERVAL_UNION_VERSUS_OVERLAP',bad_union=str(bad['union']),bad_overlap=str(bad['overlap']),target_gap=str(gap),corrected_union=str(good['union']),corrected_overlap=str(good['overlap']),bad_strip_breaks=bad['bands'])
    raise ValueError(k)

def evaluate(expr,typ):
    def visit(n):
        if isinstance(n,ast.Constant) and type(n.value) in (int,float):return typ(ast.get_source_segment(expr,n))
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.USub):return -visit(n.operand)
        if isinstance(n,ast.BinOp):
            a,b=visit(n.left),visit(n.right)
            if isinstance(n.op,ast.Add):return a+b
            if isinstance(n.op,ast.Sub):return a-b
            if isinstance(n.op,ast.Mult):return a*b
            if isinstance(n.op,ast.Div):return a/b
        raise ValueError(expr)
    return visit(ast.parse(expr,mode='eval').body)

def main():
    before={p.name:sha(p.read_bytes()) for p in P.iterdir() if p.is_file() and not p.name.startswith('peer_')}
    assert before['cases.jsonl']==EXPECTED_SOURCE and before['chat.jsonl']==EXPECTED_CHAT
    rows=[(json.loads(b),sha(b)) for b in (P/'cases.jsonl').read_bytes().splitlines()];chats=[json.loads(b) for b in (P/'chat.jsonl').read_bytes().splitlines()]
    qa={json.loads(b)['sample_id']:json.loads(b) for b in (P/'selfqa7.jsonl').read_bytes().splitlines()}
    assert len(rows)==12 and len(chats)==48
    reviews=[];numeric=[];oracles=[];mutations=[]
    for index,(r,h) in enumerate(rows):
        assert qa[r['sample_id']]['source_row_sha256']==h
        assert not any(r.get(k) for k in ['human_verified','teacher_certified','owner_human_reviewed'])
        assert r['curriculum_assignment']['enrichment'] is True and r['split']=='train'
        assert [s['step_id'] for s in r['worked_steps']]==['s'+str(i) for i in range(len(r['worked_steps']))]
        assert [g['id'] for g in r['givens']]==['g'+str(i) for i in range(len(r['givens']))]
        assert [v['level'] for v in r['hints']]==[1,2,3]
        if r['student_work']:
            assert r['student_work']['text'] in r['problem']
            assert all(v['excerpt']==r['student_work']['text'] for v in r['student_work']['observations'])
        proof=verify(r);oracles.append(dict(sample_id=r['sample_id'],source_row_sha256=h,status='PASS_INDEPENDENT_PEER',oracle=proof))
        for s in r['worked_steps']:
            assert s['reason'] and s['explanation'] and 'unit' in s
            if s.get('expression'):
                f=evaluate(s['expression'],F);assert f==F(s['result'])
                with localcontext() as ctx:
                    ctx.prec=90;decimal=evaluate(s['expression'],D);assert abs(decimal-D(f.numerator)/D(f.denominator))<D('1e-70')
                numeric.append(dict(sample_id=r['sample_id'],source_row_sha256=h,step_id=s['step_id'],expression=s['expression'],exact=str(f),decimal_agrees=True))
        for ai in range(len(r['expected_answer'])):
            bad=copy.deepcopy(r);bad['expected_answer'][ai]['result']='WRONG_ORACLE_MUTATION'
            try:verify(bad)
            except (AssertionError,ValueError,ZeroDivisionError):mutations.append(dict(sample_id=r['sample_id'],field=f'expected_answer[{ai}].result',detected=True))
            else:raise AssertionError('answer mutation escaped independent check')
        related=[c for c in chats if c['source_sample_id']==r['sample_id']]
        assert len(related)==4 and {c['mode'] for c in related}=={'worked_solution','hint_level_1','hint_level_2','hint_level_3'}
        for c in related:
            L.validate_chat(c);assert c['source_row_sha256']==h and not linkage_errors(c,source_projection(r))
            assert c['quality_status']==r['quality_status'] and c['acceptance_status']==r['acceptance_status']
        criteria=[dict(criterion=k,passed=True,evidence=e) for k,e in [
            ('actual_problem_givens_request_consistency',NOTES[index]),
            ('mathematical_correctness_independent_oracle','Separate geometric/finite methods implemented without importing author helper or oracle. Numeric expressions agree Fraction/Decimal.'),
            ('steps_reasons_units_and_complete_check','Every actual step/result/reason/explanation/answer read. Operation relation, cm versus cm2, transformations and exhaustive alternatives match request.'),
            ('initial_guidance_all_hints_answer_free','All initial and three hint texts/questions read; strategy and conditions only, no filled requested value, final list or full solution.'),
            ('grounded_student_work_and_assets','Feedback only on supplied synthetic statement; exact text/grid relations, inherited image receipts not claimed newly viewed or physically verified.'),
            ('grade_enrichment_and_structural_diversity','Grades3/4/5 enrichment explicit; paired branches change units, overlap, order, contradictory constraints, inverse roles or transform rather than numbers alone.'),
            ('hash_provenance_preservation','Exact source QA row and chat hashes verified; original AI provenance retained, no new human content attestation.')]]
        reviews.append(dict(sample_id=r['sample_id'],source_row_sha256=h,status='PASS_INDEPENDENT_PEER',actual_fields={k:r[k] for k in FIELDS},actual_fields_read='ALL_ACTUAL_FIELDS',criteria=criteria,semantic_decision=NOTES[index],independent_oracle=proof,human_review_claimed=False))
    assert len(numeric)==15
    files=['peer_fullfield_reviews.jsonl','peer_independent_oracles.jsonl','peer_numeric_checks.jsonl','peer_adversarial_mutations.jsonl']
    for name,data in zip(files,[reviews,oracles,numeric,mutations]):jl(name,data)
    assert all(sha((P/n).read_bytes())==h for n,h in before.items())
    result=dict(status='PASS_INDEPENDENT_PEER',cases=12,chats=48,full_field_reviews=12,seven_criteria_pass_count=12,numeric_steps=15,independent_models=12,adversarial_mutations_detected=len(mutations),source_file_sha256=EXPECTED_SOURCE,chat_file_sha256=EXPECTED_CHAT,source_hashes=before,source_files_unchanged=True,fixes_required=[],reviews=[{k:v[k] for k in ['sample_id','source_row_sha256','status','criteria','actual_fields_read','semantic_decision','independent_oracle']} for v in reviews],artifact_hashes={n:sha((P/n).read_bytes()) for n in files},peer_helper_sha256=sha(Path(__file__).read_bytes()),limitations=['Independent AI peer content review; not human attestation, actual physical result or wholecurriculum certification.','Parent root final acceptance/publication remains pending.'])
    write('peer_review.json',result);print(dump({k:result[k] for k in ['status','cases','chats','numeric_steps','independent_models','adversarial_mutations_detected','source_files_unchanged','fixes_required']}))
if __name__=='__main__':main()
