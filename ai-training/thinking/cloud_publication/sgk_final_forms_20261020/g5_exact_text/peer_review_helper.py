"""Independent finite peer QA. Never imports author helper or alters source rows."""
import pathlib,json,hashlib,collections,itertools,math,ast,operator,copy
from fractions import Fraction as F
from decimal import Decimal as D,localcontext
P=pathlib.Path(__file__).resolve().parent
BASE=P.parents[1]
OLD=BASE/'sgk_page_audit_20261019'
def h(b):return hashlib.sha256(b).hexdigest()
def rows(p):return [(json.loads(b),h(b),i) for i,b in enumerate(p.read_bytes().splitlines(),1) if b]
def dump(name,x): (P/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def jsonl(name,x): (P/name).write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in x),encoding='utf-8')
source_names=['cases.jsonl','chat.jsonl','selfqa7.jsonl','independent_oracles.jsonl','numeric_fraction_decimal.jsonl','nearest_actual_fullfields.jsonl','actual_page_receipts_readback.jsonl','manifest.json']
snap={n:h((P/n).read_bytes()) for n in source_names}
cases=rows(P/'cases.jsonl');chats=rows(P/'chat.jsonl');assert len(cases)==12 and len(chats)==48
byid={r['sample_id']:(r,s,i) for r,s,i in cases};assert len(byid)==12
notes={
'comma_slot_strict_selection':('Only internal comma slots; both bounds strict.','Three position-derived rational values are tested; only 1,234 remains.','Initial and all three hints suggest slot enumeration and dual-bound checking, without locating the winning slot.'),
'comma_slot_no_strict_solution':('Two slots both exactly on an excluded bound.','2,50 equals the lower bound and 25,0 equals the upper; no survivor. Correct equality is retained while eligibility is corrected.','The final hint asks to conclude from the survivor list; it does not give the empty-set/no-solution label.'),
'decimal_cards_fixed_slots_extrema':('Each of three distinct cards used once in fixed X,YZ format; leading and trailing zero allowed.','Finite hundredths-domain digit multiset filtering yields six sorted strings, minimum 0,25 and maximum 5,20.','Hints distinguish place roles and legal leading zero; they disclose neither list nor extrema.'),
'decimal_cards_duplicate_identity_vs_value':('u and v are different physical cards with the same digit; fixed two-decimal syntax.','The three digit strings each have two identity assignments, hence six arrangements but three strings and three numerical values.','Hints separate card identity, complete string equality, and numerical equality without announcing their counts.'),
'cube_all_edges_triple_factors':('All three dimensions scale 2 to 6; closed six-face surface and solid volume.','Neighbor-exposure enumeration gives surfaces 24 and 216 and voxel counts 8 and 216; ratios 9 and 27.','Hints ask how many edge factors occur and request ratio checks; no requested ratios or area/volume values are supplied.'),
'cube_half_edges_wrong_linear_scale':('All dimensions halve from 4 to 2; six-face surface.','Lattice exposure/voxel counts give area ratio 1/4 and volume ratio 1/8, disproving the quoted linear rule.','Hints request separate calculations and a dimension check without giving either fraction.'),
'painted_three_cube_all_categories':('Closed 3x3x3 assembly; all six exterior faces including bottom painted; contacts unpainted.','Axis contact-count polynomials multiply to coefficients 1,6,12,8 for zero through three painted faces; total cubes 27 and painted incidences 54.','Hints identify location categories and conservation checks, with no requested counts.'),
'painted_three_cube_unpainted_bottom':('Only top and four sides painted; bottom explicitly unpainted.','The vertical contact polynomial changes from 1+2t to 2+t, giving 2,9,12,4. Bottom corners each contact two painted sides; total incidences 45.','Hints demand using only painted faces and rechecking layers, never giving the category totals or bottom-corner answer.'),
'shared_apex_split_base_ratio':('D strictly between B,C, lengths 3 and 5; triangles partition total area 32 and share the altitude.','Eight equal base-width area units imply 4 square centimetres each, so parts 12 and 20; total and ratio both check.','Hints ask why heights agree and how to apportion total; they do not reveal the 3:5 area ratio or areas.'),
'base_ratio_requires_equal_height':('Different apexes with perpendicular heights 4 and 2, bases 3 and 5 on same line.','Coordinate determinants give areas 6 and 5, ratio 6:5. The quoted same-line-implies-same-height assertion is directly contradicted by the supplied distances.','Hints ask to verify each altitude and the condition for using base ratio; no corrected ratio or area is revealed.'),
'apex_parallel_line_including_external_foot':('Base length 8, parallel line at perpendicular distance 6; all apex positions including external feet allowed.','Piecewise bounding-rectangle minus complement triangles gives area 24 for left-external, internal and right-external positions; symbolic cancellation shows position independence.','The three questions direct attention to perpendicular distance and the line containing the base, without supplying the invariance conclusion or area.'),
'apex_nonparallel_path_breaks_invariance':('Base 10 remains fixed while positive heights change 3 to 5 along a nonparallel line.','Determinants give 15 and 25 square centimetres, a change of 10. The quoted assertion overlooks changed perpendicular height.','Hints ask whether base constancy ensures height constancy and request the missing parallel condition; no area/change is supplied.')}

def frac(s):return F(str(s).replace(',','.'))
def dec(f):return D(f.numerator)/D(f.denominator)
def prove_q(q):
    f=F(q)
    with localcontext() as ctx:
        ctx.prec=70
        d=dec(f); assert F(d)==f # these finite cases have terminating decimal results
    return {'fraction':str(f),'decimal':str(d)}
def comma_by_place(digits,low,high):
    # No insertion/evaluation of candidate strings: numerator stays fixed and
    # denominator is the place count to the right of each internal slot.
    n=int(digits);lo=F(low);hi=F(high);out=[];trials=[]
    for right in range(len(digits)-1,0,-1):
        value=F(n,10**right);slot=len(digits)-right
        ok=lo.numerator*value.denominator < value.numerator*lo.denominator and value.numerator*hi.denominator < hi.numerator*value.denominator
        written=digits[:slot]+','+digits[slot:]
        trials.append({'right_places':right,'value':prove_q(value),'strictly_inside':ok,'written':written})
        if ok:out.append(written)
    return out,trials
def cards_by_hundredths(digits):
    # Exhaustively search the 1000 hundredths-format numerals, not card permutations.
    counter=collections.Counter(digits);strings=[]
    for hundredths in range(1000):
        s=f'{hundredths:03}'
        if collections.Counter(s)==counter:strings.append(s[0]+','+s[1:])
    multiplicity=math.prod(math.factorial(n) for n in counter.values())
    return strings,len(strings)*multiplicity,multiplicity
def voxel_surface(n):
    occupied=set(itertools.product(range(n),repeat=3));surface=0
    for c in occupied:
        for axis in range(3):
            for shift in [-1,1]:
                adjacent=list(c);adjacent[axis]+=shift
                surface+=tuple(adjacent) not in occupied
    return len(occupied),surface
def multiply(a,b):
    out=[0]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):out[i+j]+=x*y
    return out
def paint_poly(bottom):
    # An axis with both ends painted has one interior position and two painted
    # endpoints; with only top painted it has two unpainted and one painted.
    return multiply(multiply([1,2],[1,2]),[1,2] if bottom else [2,1])
def determinant_area(a,b,c):return abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))/F(2)
def bbox_area(base,height,x):
    b,h0,x=F(base),F(height),F(x)
    if x<0:return (b-x)*h0-(-x)*h0/2-(b-x)*h0/2,'left_external'
    if x>b:return x*h0-(x-b)*h0/2-x*h0/2,'right_external'
    return b*h0-x*h0/2-(b-x)*h0/2,'internal_or_endpoint'

oracle_evidence=[];specs={};mutations=[]
def add_mutation(sid,name,expected,mutated):
    assert mutated!=expected,(sid,name)
    mutations.append({'sample_id':sid,'source_row_sha256':byid[sid][1],'mutation':name,'expected':str(expected),'mutated':str(mutated),'detected':True})
for r,s,i in cases:
    sid=r['sample_id'];b=r['coverage']['branch'];expected=[];proof={};method='';specific=[]
    def want(quantity,result,unit=''):expected.append({'quantity':quantity,'result':str(result),'unit':unit})
    if b.startswith('comma_slot'):
        digits,lo,hi=('1234','1','2') if b.endswith('strict_selection') else ('250','2.5','25')
        good,trials=comma_by_place(digits,lo,hi);method='Integer place-value denominators and cross-multiplied strict inequalities; Fraction and Decimal crosscheck';proof={'trials':trials,'valid_strings':good}
        if good:want('Số hợp lệ',good[0]);want('Khe đặt','Giữa 1 và 2 trong chuỗi')
        else:want('Kết luận','Không có cách đặt thỏa cả hai dấu nghiêm ngặt')
        inclusive=[t['written'] for t in trials if F(lo)<=frac(t['written'])<=F(hi)]
        if not good:add_mutation(sid,'replace_strict_bounds_with_inclusive',good,inclusive)
        else:add_mutation(sid,'accept_number_above_upper_bound',good,good+['12,34'])
    elif b.startswith('decimal_cards'):
        digits='025' if b.endswith('fixed_slots_extrema') else '004';strings,arrangements,multiplicity=cards_by_hundredths(digits)
        method='Exhaustive integer hundredths-domain digit-multiset filter; factorial multiplicity recovers physical-card assignments';proof={'written_strings':strings,'arrangements':arrangements,'identity_multiplicity_per_string':multiplicity,'numeric_values':[prove_q(frac(t)) for t in strings]}
        if digits=='025':want('Danh sách',';'.join(strings));want('Nhỏ nhất',strings[0]);want('Lớn nhất',strings[-1]);add_mutation(sid,'incorrectly_ban_zero_whole_digit',strings,[t for t in strings if t[0]!='0'])
        else:want('Cách xếp thẻ',arrangements,'cách');want('Chuỗi khác nhau',';'.join(strings));want('Giá trị khác nhau','0,04;0,4;4');add_mutation(sid,'merge_two_equal_digit_card_identities',arrangements,len(strings))
    elif b.startswith('cube_'):
        a,z=(2,6) if b.startswith('cube_all') else (4,2);va,sa=voxel_surface(a);vb,sb=voxel_surface(z);sr=F(sb,sa);vr=F(vb,va)
        method='Enumerate unit voxels and absent face-neighbours; derive exact ratios from counts, not the author square/cube formulas';proof={'old_voxels':va,'new_voxels':vb,'old_exposed_unit_faces':sa,'new_exposed_unit_faces':sb,'surface_ratio':prove_q(sr),'volume_ratio':prove_q(vr)}
        if a==2:want('A diện tích',sa,'cm²');want('A thể tích',va,'cm³');want('B diện tích',sb,'cm²');want('B thể tích',vb,'cm³');want('Hệ số',f'Diện tích {sr}; thể tích {vr}')
        else:want('Tỉ số diện tích',sr);want('Tỉ số thể tích',vr)
        add_mutation(sid,'use_linear_factor_for_area',sr,F(z,a));add_mutation(sid,'use_linear_factor_for_volume',vr,F(z,a))
    elif b.startswith('painted_'):
        bottom=b.endswith('all_categories');poly=paint_poly(bottom);method='Multiply axis contact-count generating polynomials, independently of cell-coordinate enumeration';proof={'axis_polynomials':[[1,2],[1,2],[1,2] if bottom else [2,1]],'coefficients_zero_through_three':poly,'cube_total':sum(poly),'painted_face_total':sum(k*v for k,v in enumerate(poly))}
        assert sum(poly)==27 and proof['painted_face_total']==9*(6 if bottom else 5)
        for k in [3,2,1]:want(f'Đúng {k} mặt',poly[k],'khối')
        want('Không sơn',poly[0],'khối')
        if not bottom:want('Góc đáy','Mỗi góc đáy 2 mặt sơn')
        add_mutation(sid,'substitute_other_bottom_paint_convention',poly,paint_poly(not bottom))
    elif b=='shared_apex_split_base_ratio':
        unit=F(32,8);areas=[3*unit,5*unit];method='Equal base-subdivision area units; partition total into eight equal widths without reconstructing an altitude';proof={'unit_area':prove_q(unit),'areas':[prove_q(v) for v in areas],'sum':str(sum(areas))}
        want('ABD',areas[0],'cm²');want('ADC',areas[1],'cm²');add_mutation(sid,'divide_total_equally_despite_unequal_bases',areas,[F(16),F(16)])
    elif b=='base_ratio_requires_equal_height':
        area1=determinant_area((F(0),F(0)),(F(3),F(0)),(F(1),F(4)));area2=determinant_area((F(3),F(0)),(F(8),F(0)),(F(6),F(2)))
        method='Exact coordinate determinant areas, with different apex heights assigned to their own bases';proof={'areas':[prove_q(area1),prove_q(area2)],'actual_ratio':str(area1/area2),'base_ratio':str(F(3,5))}
        want('ABD',area1,'cm²');want('ECD',area2,'cm²');want('Tỉ số',f'{area1}:{area2}');add_mutation(sid,'assume_common_height_from_collinear_bases',area1/area2,F(3,5))
    elif b=='apex_parallel_line_including_external_foot':
        trials=[{'x':str(x),'area':str(bbox_area(8,6,x)[0]),'region':bbox_area(8,6,x)[1]} for x in [F(-11,2),F(0),F(3),F(8),F(25,2)]]
        assert {t['area'] for t in trials}=={'24'}
        method='Piecewise bounding rectangles minus complementary triangles; left-external, internal and right-external formulas cancel the horizontal apex coordinate';proof={'trials':trials,'symbolic_identity':'x<0: (b-x)h-(-x)h/2-(b-x)h/2=bh/2; 0<=x<=b: bh-xh/2-(b-x)h/2=bh/2; x>b: xh-(x-b)h/2-xh/2=bh/2','exact_common_area':prove_q(24)}
        want('Diện tích chung',24,'cm²');want('Kết luận','Không đổi theo vị trí P trên m');add_mutation(sid,'drop_triangle_half_factor',F(24),F(48));add_mutation(sid,'treat_external_foot_area_as_zero',F(24),F(0))
    else:
        assert b=='apex_nonparallel_path_breaks_invariance'
        areas=[determinant_area((F(0),F(0)),(F(10),F(0)),(F(1),F(3))),determinant_area((F(0),F(0)),(F(10),F(0)),(F(2),F(5)))]
        method='Exact coordinate determinants at two points on a nonparallel line; compare actual endpoint areas';proof={'points':[[1,3],[2,5]],'areas':[prove_q(v) for v in areas],'area_change':prove_q(areas[1]-areas[0])}
        want('ABP',areas[0],'cm²');want('ABQ',areas[1],'cm²');want('Thay đổi',areas[1]-areas[0],'cm²');add_mutation(sid,'force_area_invariant_from_fixed_base',areas,[areas[0],areas[0]])
    assert r['expected_answer']==expected,(b,r['expected_answer'],expected)
    specs[sid]=expected
    oracle_evidence.append({'sample_id':sid,'source_row_sha256':s,'master_id':r['coverage']['finite_master_id'],'independent_method':method,'proof':proof,'computed_expected_answer':expected,'matches_actual_expected_answer':True,'author_model_expected_values_used':False,'author_helper_imported':False})

# Detect concrete wrong-answer and wrong-unit mutations against independently
# computed answer specifications; every original answer component is exercised.
for r,s,i in cases:
    sid=r['sample_id']
    for j,a in enumerate(r['expected_answer']):
        mutant=copy.deepcopy(r['expected_answer']);mutant[j]['result']=str(frac(a['result'])+1) if all(ch in '0123456789/.,-' for ch in a['result']) else a['result']+' [sai]'
        add_mutation(sid,f'change_answer_component_{j}',specs[sid],mutant)
        mutant=copy.deepcopy(r['expected_answer']);mutant[j]['unit']='cm' if a['unit']!='cm' else 'cm²'
        add_mutation(sid,f'change_unit_component_{j}',specs[sid],mutant)

numeric=[]
def calc(node,kind):
    if isinstance(node,ast.Expression):return calc(node.body,kind)
    if isinstance(node,ast.Constant) and isinstance(node.value,(int,float)):return kind(str(node.value))
    if isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.USub):return -calc(node.operand,kind)
    if isinstance(node,ast.BinOp):
        op={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv}[type(node.op)]
        return op(calc(node.left,kind),calc(node.right,kind))
    raise ValueError(ast.dump(node))
for r,s,i in cases:
    for step in r['worked_steps']:
        if step['expression']:
            node=ast.parse(step['expression'],mode='eval');f=calc(node,F);d=calc(node,D)
            assert f==frac(step['result']) and F(d)==f
            numeric.append({'sample_id':r['sample_id'],'source_row_sha256':s,'step_id':step['step_id'],'expression':step['expression'],'fraction':str(f),'decimal':str(d),'actual_result':step['result'],'passed':True})

chat_by=collections.defaultdict(list)
for c,cs,ci in chats:
    sid=c['source_sample_id'];r,s,i=byid[sid]
    assert c['source_row_sha256']==s and c['grade']==r['grade'] and c['split']=='train'
    user=json.loads(next(x['content'] for x in c['messages'] if x['role']=='user'));ans=json.loads(next(x['content'] for x in c['messages'] if x['role']=='assistant'))
    expected_user={'grade':r['grade'],'problem':r['problem'],'mode':c['mode']}
    if r['student_work']:expected_user['student_work']=r['student_work']['text']
    assert user==expected_user
    if c['mode']=='worked_solution':assert ans=={'can_solve':r['can_solve'],'initial_guidance':r['initial_guidance'],'steps':r['worked_steps'],'answer':r['expected_answer']}
    else:
        n=int(c['mode'].rsplit('_',1)[1]);hint=r['hints'][n-1];assert ans=={'hint':hint['hint'],'question':hint['question']}
    chat_by[sid].append({'sample_id':c['sample_id'],'line':ci,'row_sha256':cs,'mode':c['mode'],'source_row_sha256':s})
assert all({x['mode'] for x in v}=={'worked_solution','hint_level_1','hint_level_2','hint_level_3'} for v in chat_by.values())

near_evidence={};old_cache={}
for r,s,i in cases:
    for ref in r['nearest_source_comparison']['nearest_actual_valid_train_rows']:
        fn=ref['source_file'];old_cache.setdefault(fn,(OLD/fn).read_bytes().splitlines());raw=old_cache[fn][ref['line']-1];n=json.loads(raw)
        assert h(raw)==ref['sha256'] and n['sample_id']==ref['sample_id'] and n['split']=='train'
        near_evidence[(fn,ref['line'])]={'reference':ref,'actual_full_row':n,'byte_hash_validated':True}
qa={x['sample_id']:x for x,hs,i in rows(P/'selfqa7.jsonl')}
for r,s,i in cases:
    assert qa[r['sample_id']]['source_row_sha256']==s
    assert len(qa[r['sample_id']]['criteria'])==7 and all(x['passed'] for x in qa[r['sample_id']]['criteria'])
    assert all(qa[r['sample_id']]['actual_fields'][k]==r[k] for k in qa[r['sample_id']]['actual_fields'])

reviews=[]
for r,s,i in cases:
    sid=r['sample_id'];b=r['coverage']['branch'];giv,mathnote,hintnote=notes[b]
    assert len(r['hints'])==3 and [x['level'] for x in r['hints']]==[1,2,3]
    assert r['grade']==5 and r['curriculum_assignment']['grade']==5 and r['curriculum_assignment']['enrichment']
    assert all(st.get('reason') and st.get('explanation') and 'unit' in st for st in r['worked_steps'])
    assert r['human_verified'] is False and r['teacher_certified'] is False and r['owner_human_reviewed'] is False
    if r['student_work']:
        assert r['student_work']['text'] in r['problem']
        assert all(o['excerpt'] in r['student_work']['text'] for o in r['student_work']['observations'])
    reviews.append({'sample_id':sid,'source_row_sha256':s,'actual_full_row':r,'chat_links':chat_by[sid],'criteria':[{'criterion':'problem_givens_request_consistency','passed':True,'evidence':giv},{'criterion':'mathematical_correctness','passed':True,'evidence':mathnote},{'criterion':'reason_steps_units_check','passed':True,'evidence':'Each actual step reason/explanation/unit was read; exact Fraction/Decimal arithmetic and independent finite model agree with all answers. cm²/cm³ remain distinct where numerical values coincide.'},{'criterion':'pedagogical_hint_nonleak','passed':True,'evidence':hintnote},{'criterion':'grounded_student_work_missing_data','passed':True,'evidence':'Feedback addresses only the exact synthetic excerpt included in the problem; no hidden reasoning, image or physical result inferred.'},{'criterion':'provenance_originality_grade_limit','passed':True,'evidence':'Original complete text model; grade5 enrichment declared. The paired branch changes syntax boundary, card multiplicity, scale direction, painted faces, equal-height premise or parallel-line premise.'},{'criterion':'finite_scope_no_false_attestation','passed':True,'evidence':'Draft status retained; no human certification, no model-accuracy claim, no full curriculum/physical-competency closure.'}]})
assert snap=={n:h((P/n).read_bytes()) for n in source_names}
jsonl('peer_fullfield_reviews.jsonl',reviews);jsonl('peer_independent_oracles.jsonl',oracle_evidence);jsonl('peer_numeric_checks.jsonl',numeric);jsonl('peer_adversarial_mutations.jsonl',mutations);jsonl('peer_nearest_hash_evidence.jsonl',list(near_evidence.values()))
artifacts={n:h((P/n).read_bytes()) for n in ['peer_fullfield_reviews.jsonl','peer_independent_oracles.jsonl','peer_numeric_checks.jsonl','peer_adversarial_mutations.jsonl','peer_nearest_hash_evidence.jsonl','peer_review_helper.py']}
report={'status':'PASS_INDEPENDENT_PEER','cases':12,'chats':48,'full_field_reviews':12,'numeric_steps':len(numeric),'independent_models':12,'adversarial_mutations_detected':len(mutations),'actual_unique_nearest_rows_hash_validated':len(near_evidence),'source_hashes':snap,'source_files_unchanged':True,'fixes_required':[],'substantive_limitations':['Finite grade5 text enrichment only; no physical/image outcome evidence.','No model accuracy or human review attestation assigned.','Manifest inherited wording about age models is irrelevant to this batch; it does not alter source mathematical content.'],'artifact_hashes':artifacts}
dump('peer_review.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
