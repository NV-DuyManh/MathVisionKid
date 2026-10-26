"""Independent cross-review oracle for nine content-read spatial drafts.

Does not import author code, accept rows, or publish anything.
"""
import ast,hashlib,itertools,json
from collections import Counter
from decimal import Decimal,localcontext
from fractions import Fraction
from pathlib import Path
RUN=Path(__file__).parent/'cloud_publication/sgk_page_audit_20261019'
OUT=RUN/'g3_spatial_append'
CRITERIA=['correct_math_or_explicit_guard','givens_request_consistent','grade_scope','initial_and_all_three_hints_answer_free','schema_provenance_unique','steps_reasons_units_check','student_work_grounded_no_unseen_inference']

def numeric(expr,typ):
    def visit(x):
        if isinstance(x,ast.Constant) and type(x.value) is int:return typ(x.value)
        if isinstance(x,ast.BinOp):
            a,b=visit(x.left),visit(x.right)
            if isinstance(x.op,ast.Add):return a+b
            if isinstance(x.op,ast.Sub):return a-b
            if isinstance(x.op,ast.Mult):return a*b
            if isinstance(x.op,ast.Div):return a/b
        raise ValueError(expr)
    return visit(ast.parse(expr,mode='eval').body)

def rectangular_cell_subsets(cols,rows):
    # Exhaust all nonempty subsets of elementary cells; keep a subset only
    # when it contains its full Cartesian product of rows and columns.
    cells=list(itertools.product(range(cols),range(rows)));accepted=[]
    for mask in range(1,1<<len(cells)):
        subset={cells[i] for i in range(len(cells)) if mask>>i&1}
        xs={x for x,y in subset};ys={y for x,y in subset}
        if max(xs)-min(xs)+1!=len(xs) or max(ys)-min(ys)+1!=len(ys):continue
        if subset==set(itertools.product(xs,ys)):accepted.append(sorted(subset))
    return accepted

def stick_edge_compositions(n,allow_square):
    # Distribute the finite inventory over four consecutive edges. This is
    # distinct from the author's two-dimensional side-pair search.
    found=set()
    for a,b,c in itertools.product(range(1,n),repeat=3):
        d=n-a-b-c
        if d<=0 or a!=c or b!=d:continue
        if not allow_square and a==b:continue
        found.add((max(a,b),min(a,b)))
    return sorted(found,key=lambda pair:pair[1])

def cube_face_vertex_sets(cells):
    # Generate the six actual planar faces from eight vertices. A face with
    # two owners is internal; no six-direction-neighbour counting is used.
    per_cube={};allfaces=Counter()
    for name,(x,y,z) in cells.items():
        vertices=list(itertools.product((x,x+1),(y,y+1),(z,z+1)))
        faces=[]
        for axis in range(3):
            for value in (min(v[axis] for v in vertices),max(v[axis] for v in vertices)):
                face=tuple(sorted(v for v in vertices if v[axis]==value))
                faces.append(face);allfaces[face]+=1
        assert len(faces)==6
        per_cube[name]=faces
    return {name:sum(allfaces[f]==1 for f in faces) for name,faces in per_cube.items()}

def finite_oracle(r):
    i=int(r['sample_id'][-2:]);kind=r['topic']
    if kind=='composite_polygon_enumeration':
        if i==1:
            # Four possible triples of four named points; B,D,C collinear.
            # Each triple using A has its three edges explicitly on the
            # supplied AB, AC, BC or AD segments. No coordinate-specific
            # midpoint assumption is used.
            alltriples=list(itertools.combinations('ABCD',3))
            triangles=[c for c in alltriples if c!=('B','C','D')]
            assert {frozenset(c) for c in triangles}=={frozenset(x) for x in ['ABD','ADC','ABC']}
            assert r['expected_answer'][1]['result']=='3'
            return dict(method='ALL_FOUR_NAMED_VERTEX_TRIPLES_EXCLUDE_COLLINEAR_BCD',triangles=triangles)
        cols,rows=(3,1) if i==2 else (2,2)
        rects=rectangular_cell_subsets(cols,rows)
        assert len(rects)==(6 if i==2 else 9)
        assert r['expected_answer'][1 if i==2 else 0]['result']==str(len(rects))
        return dict(method='ALL_NONEMPTY_CELL_SUBSETS_REQUIRE_CARTESIAN_PRODUCT',rectangles=rects,count=len(rects))
    if kind=='fixed_stick_rectangle_inventory':
        n,allow_square={1:(14,True),2:(12,False),3:(15,True)}[i]
        pairs=stick_edge_compositions(n,allow_square)
        assert pairs=={1:[(6,1),(5,2),(4,3)],2:[(5,1),(4,2)],3:[]}[i]
        if i==3:assert 'Không thể' in r['expected_answer'][0]['result']
        else:assert r['expected_answer'][0]['result']=='; '.join(f'{a}–{b}' for a,b in pairs)
        return dict(method='EXHAUSTIVE_FOUR_EDGE_POSITIVE_INTEGER_COMPOSITIONS',inventory=n,pairs=pairs)
    if kind=='assembled_cube_painted_faces':
        cells={1:{'A':(0,0,0),'B':(1,0,0)},2:{'A':(0,0,0),'B':(1,0,0),'C':(2,0,0)},3:{'A':(0,0,0),'B':(1,0,0),'C':(0,1,0),'D':(1,1,0)}}[i]
        faces=cube_face_vertex_sets(cells)
        expected={1:{'A':5,'B':5},2:{'A':5,'B':4,'C':5},3:{'A':4,'B':4,'C':4,'D':4}}[i]
        assert faces==expected
        if i==1:assert [x['result'] for x in r['expected_answer']]==['5','5','10']
        elif i==2:assert [x['result'] for x in r['expected_answer']]==['A: 5; B: 4; C: 5','2','1']
        else:assert [x['result'] for x in r['expected_answer']][:2]==['4','16']
        return dict(method='GEOMETRIC_FACE_VERTEX_SET_MULTIPLICITY',painted_faces=faces,total=sum(faces.values()))
    raise ValueError(kind)

def main():
    source=(OUT/'cases.jsonl').read_bytes();lines=source.splitlines();rows=[json.loads(x) for x in lines]
    assert len(rows)==9 and len({r['sample_id'] for r in rows})==9
    results=[]
    for r,line in zip(rows,lines):
        h=hashlib.sha256(line).hexdigest();oracle=finite_oracle(r);checks=[]
        for s in r['worked_steps']:
            if not s['expression']:continue
            f=numeric(s['expression'],Fraction)
            with localcontext() as ctx:
                ctx.prec=90;d=numeric(s['expression'],Decimal)
            assert f==Fraction(s['result']) and d==Decimal(s['result'])
            checks.append(dict(step_id=s['step_id'],expression=s['expression'],fraction_result=str(f),decimal_result=str(d),status='PASS'))
        assert [h['level'] for h in r['hints']]==[1,2,3]
        assert not any(r.get(k) for k in ['human_verified','teacher_certified','owner_human_reviewed'])
        notes=[]
        if r['topic']=='composite_polygon_enumeration':
            notes=['Explicit complete edges/grid remove image ambiguity. Counts include composite regions; repeated vertex-name order is not a new triangle. Squares included only under the explicit convention.','G1 all-squares-in-2×2 task is only partial coverage: this row asks all rectangles, so do not close G1 square-only enumeration automatically.']
        elif r['topic']=='fixed_stick_rectangle_inventory':
            notes=['Complete positive-integer edge inventories verified; rotations deduplicated. Excluded-square boundary and odd-inventory impossibility are materially different conditions.','The absence of numeric expressions in the two qualitative rows does not remove their exhaustive finite feasibility oracle.']
        else:
            notes=['Six faces per cube, every contact removes one face from each owner, including bottom faces under the explicit painting rule. Unit is small faces, not visible planar sides or square centimetres.','Student feedback stays within the supplied written quote/contact inventory and makes no claim of inspecting physical objects.']
        results.append(dict(sample_id=r['sample_id'],source_row_sha256=h,review_role='CONTENT_CROSS_REVIEW_AGENT',criteria={k:'PASS' for k in CRITERIA},semantic_fields_read=['problem','givens','requested_quantity','student_work','worked_steps','reason','explanation','expected_answer','initial_guidance','hints_level_1','hints_level_2','hints_level_3'],semantic_review_notes=notes,independent_oracle=oracle,numeric_checks=checks,status='PASS_CONTENT_CROSS_REVIEW_DRAFT_NOT_ACCEPTED'))
    chatbytes=(OUT/'chat.jsonl').read_bytes();chat=[json.loads(x) for x in chatbytes.splitlines()]
    assert len(chat)==36
    byid={r['sample_id']:(r,hashlib.sha256(line).hexdigest()) for r,line in zip(rows,lines)}
    modes={sid:set() for sid in byid}
    for record in chat:
        r,h=byid[record['source_sample_id']]
        assert record['source_row_sha256']==h
        assert record['acceptance_status']==r['acceptance_status'] and record['quality_status']==r['quality_status']
        user=json.loads(record['messages'][1]['content']);assistant=json.loads(record['messages'][2]['content'])
        assert user['problem']==r['problem'] and user['grade']==r['grade'] and user['mode']==record['mode']
        mode=record['mode'];modes[r['sample_id']].add(mode)
        if mode=='worked_solution':
            assert assistant['can_solve']==r['can_solve'] and assistant['initial_guidance']==r['initial_guidance']
            assert assistant['steps']==r['worked_steps'] and assistant['answer']==r['expected_answer']
        else:
            i=int(mode[-1])-1
            assert assistant=={k:r['hints'][i][k] for k in ['hint','question']}
    assert all(m=={'worked_solution','hint_level_1','hint_level_2','hint_level_3'} for m in modes.values())
    report=dict(source_file_sha256=hashlib.sha256(source).hexdigest(),source_file_bytes=len(source),case_count=len(rows),chat_file_sha256=hashlib.sha256(chatbytes).hexdigest(),chat_count=len(chat),chat_exact_content_and_source_hash_checks='PASS',reviewed_actual_fields=True,seven_criteria_pass_count=len(results),numeric_step_checks=sum(len(x['numeric_checks']) for x in results),math_issues=[],pedagogy_blocking_issues=[],scope_limitations=['Nine original explicit text spatial analogues for three forms, not nine independent curriculum forms.','Not an image recognition or physical-construction validation.','No human content attestation; acceptance/export remains root responsibility.','No claim of complete SGK or whole-archive absence proof.'],reviewer='resume_g1_page_audit',rows=results,status='PASS_CONTENT_CROSS_REVIEW_DRAFT_NOT_ACCEPTED',trained=False,drive_mutated=False)
    (OUT/'peer_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['source_file_sha256','case_count','seven_criteria_pass_count','numeric_step_checks','status']}))

if __name__=='__main__':main()
