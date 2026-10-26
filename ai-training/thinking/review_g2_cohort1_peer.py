"""Bounded independent six-case review and append-only wording derivation.

No Drive, runtime, acceptance, training, evaluation payload or global state writes.
"""
from pathlib import Path
from collections import Counter
from itertools import product
from math import factorial
from fractions import Fraction
from decimal import Decimal
import ast, copy, hashlib, json, operator
from exhaustive_primary_math import chat_records
import exhaustive_colab_loader as L

HERE = Path(__file__).resolve().parent
P = HERE/'cloud_publication/g2_finite_forms_20261021/numerals_cohort1'
OUT = P/'polished'

def sha(b): return hashlib.sha256(b).hexdigest()
def canon(x): return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
def write_json(p, x): p.write_text(json.dumps(x, ensure_ascii=False, indent=2)+'\n', encoding='utf8', newline='\n')
def write_lines(p, rows): p.write_text(''.join(canon(x)+'\n' for x in rows), encoding='utf8', newline='\n')

# Independent transcription from each actual problem, not copied from its oracle.
MODELS = [
    ({0:1, 2:1, 7:1}, 2, None, [20,27,70,72], 4),
    ({0:1, 1:1, 4:1, 8:1}, 2, None, [10,14,18,40,41,48,80,81,84], 9),
    ({0:2, 5:1}, 2, None, [50], 2),
    ({0:1, 2:2}, 3, None, [202,220], 4),
    ({0:1, 3:1, 6:1}, 3, 306, [360,603,630], 3),
    ({1:1, 2:1, 4:1}, 3, 500, [], 0),
]
NOTES = [
    'Unrestricted two-digit list must retain 27 as well as even values; 0 may occur only in units. 72-20=52.',
    'Four-card stock is optional selection, not compulsory zero. Nine values in three tens groups; 84-10=74. Feedback is tied to the supplied mandatory-zero statement.',
    'Two separate zero resources give C-A and C-B, one numeral value50, two physical placements. Same minimum/maximum50; difference0 is not an empty result.',
    'All three physical cards must be used. A-C-B/B-C-A produce202; A-B-C/B-A-C produce220. Four placements, two values, difference18; supplied deletion of B is invalid.',
    'Stock permits306,360,603,630 before comparison; strict >306 removes equality306. Retained360,603,630 have minimum360/maximum630/difference270.',
    'Six stock numbers124,142,214,241,412,421 are all <500. The largest stock number is not feasible. No feasible minimum/maximum; feasible count0 is valid, unlike substituting numeral0 for an extremum.',
]
CRITERIA = [
    'problem_givens_request_consistency',
    'mathematical_oracle_complete_finite_inventory',
    'steps_reasons_units_checks',
    'initial_and_three_hints_no_filled_answer',
    'student_feedback_only_supplied_quote',
    'grade2_original_substantive_branch',
    'provenance_hash_preservation',
]

def oracle(model):
    stock, length, bound, expected, physical_expected = model
    values = []
    multiplicities = {}
    # Third method: cartesian product of digit VALUES plus inventory capacities.
    # Count labeled physical realizations by independent falling-factorial weights.
    before_bound = []
    for word in product(sorted(stock), repeat=length):
        if word[0] == 0: continue
        used = Counter(word)
        if any(used[d] > stock.get(d, 0) for d in used): continue
        number = sum(d*10**(length-i-1) for i,d in enumerate(word))
        before_bound.append(number)
        if bound is not None and number <= bound: continue
        values.append(number)
        multiplicities[number] = 1
        for d, count in used.items():
            multiplicities[number] *= factorial(stock[d]) // factorial(stock[d]-count)
    assert values == expected
    assert sum(multiplicities.values()) == physical_expected
    return dict(method='Digit-value cartesian words filtered by independently transcribed stock capacities; physical assignments counted by falling-factorial weights, not physical-card permutations or scanning integer ranges.',
                stock=stock, length=length, strict_lower_bound=bound,
                stock_values_before_bound=before_bound, values=values,
                physical_realizations_per_value=multiplicities,
                physical_assignments=sum(multiplicities.values()),
                minimum=min(values) if values else None, maximum=max(values) if values else None,
                difference=max(values)-min(values) if values else None,
                status='PASS')

def numeric_checks(row):
    checks=[]
    for s in row['worked_steps']:
        expr=s.get('expression')
        if not expr: continue
        def calc(n, ctor):
            if isinstance(n,ast.Constant) and type(n.value) is int: return ctor(str(n.value))
            if isinstance(n,ast.BinOp) and type(n.op) in (ast.Add,ast.Sub):
                return {ast.Add:operator.add,ast.Sub:operator.sub}[type(n.op)](calc(n.left,ctor),calc(n.right,ctor))
            raise ValueError('Unexpected expression in bounded review')
        tree=ast.parse(expr,mode='eval').body
        f=calc(tree,Fraction); d=calc(tree,Decimal)
        assert f==Fraction(s['result']) and d==Decimal(s['result'])
        checks.append(dict(step_id=s['step_id'],expression=expr,Fraction=str(f),Decimal=str(d),expected=s['result'],status='PASS'))
    return checks

def check_answers(row, computed, index):
    a={x['quantity']:x['result'] for x in row['expected_answer']}
    list_key = 'Mọi số trước lọc' if index==5 else ('Mọi số được nhận' if index==4 else ('Mọi giá trị' if index in (2,3) else 'Mọi số'))
    expected_list = computed['stock_values_before_bound'] if index==5 else computed['values']
    assert a[list_key] == ';'.join(map(str,expected_list))
    if index==5:
        assert a['Mọi số được nhận']=='không có'
        assert a['Số nhỏ nhất sau lọc']==a['Số lớn nhất sau lọc']=='không tồn tại'
        assert a['Số giá trị được nhận']=='0'
    else:
        assert a['Số nhỏ nhất']==str(computed['minimum'])
        assert a['Số lớn nhất']==str(computed['maximum'])
        assert a['Hiệu']==str(computed['difference'])
        assert a['Số giá trị']==str(len(computed['values']))
    if index in (2,3): assert a['Số cách đặt']==str(computed['physical_assignments'])

def check_chats(rows, chats):
    byid={r['sample_id']:r for r in rows}
    seen=set()
    for chat in chats:
        r=byid[chat['source_sample_id']]
        assert chat['source_row_sha256']==sha(canon(r).encode('utf8'))
        assert chat['sample_id']==r['sample_id']+':'+chat['mode']
        assert (r['sample_id'],chat['mode']) not in seen
        seen.add((r['sample_id'],chat['mode']))
        assert chat['case_group_id']==r['case_group_id'] and chat['split']=='train'
        user=json.loads(chat['messages'][1]['content'])
        assistant=json.loads(chat['messages'][2]['content'])
        assert user==dict(grade=2,problem=r['problem'],mode=chat['mode'],**({'student_work':r['student_work']['text']} if r['student_work'] else {}))
        if chat['mode']=='worked_solution':
            assert assistant==dict(can_solve=True,initial_guidance=r['initial_guidance'],steps=r['worked_steps'],answer=r['expected_answer'])
        else:
            hint=r['hints'][int(chat['mode'][-1])-1]
            assert assistant==dict(hint=hint['hint'],question=hint['question'])
        assert not chat['human_verified'] and not chat['teacher_certified']
        assert chat['acceptance_status']=='DRAFT_AWAITING_ROOT_CONTENT_CROSS_REVIEW'
    assert len(seen)==24

def main():
    parent_hashes={p.name:sha(p.read_bytes()) for p in P.iterdir() if p.is_file() and p.name!='peer_review.json'}
    source_lines=(P/'cases.jsonl').read_bytes().splitlines()
    parents=[json.loads(b) for b in source_lines]
    chats=[json.loads(b) for b in (P/'chat.jsonl').read_bytes().splitlines()]
    assert len(parents)==6 and len(chats)==24
    assert all(canon(r).encode('utf8')==b for r,b in zip(parents,source_lines))
    check_chats(parents,chats)
    computations=[oracle(m) for m in MODELS]
    for i,r in enumerate(parents): check_answers(r,computations[i],i)
    nearest=[json.loads(b) for b in (P/'nearest_actual_fullfields.jsonl').read_bytes().splitlines()]
    assert len(nearest)==5
    plan=json.loads((P/'planning_task_snapshot.json').read_text('utf8'))
    assert {r['coverage']['planning_task_id'] for r in parents}=={t['task_id'] for t in plan['tasks']}
    original_reviews=[]
    for i,(r,b) in enumerate(zip(parents,source_lines)):
        criteria={k:'PASS' for k in CRITERIA}
        criteria['grade2_original_substantive_branch']='MATHEMATICAL_BRANCH_PASS_WORDING_POLISH_REQUIRED'
        if i in (1,3,5): criteria['student_feedback_only_supplied_quote']='OBSERVABLE_SCOPE_PASS_REMOVE_INTERNAL_META_COMMENT'
        original_reviews.append(dict(sample_id=r['sample_id'],source_row_sha256=sha(b),criteria=criteria,
            actual_fields_read=['problem','givens','requested_quantity','student_work','worked_steps.title','worked_steps.reason','worked_steps.explanation','worked_steps.expression','worked_steps.result','worked_steps.unit','expected_answer','initial_guidance','all_three_hints_and_questions'],
            semantic_note=NOTES[i],independent_computation=computations[i],numeric_checks=numeric_checks(r),
            status='MATH_PASS_DERIVED_GRADE2_WORDING_POLISH_BEFORE_ROOT_ACCEPTANCE',human_review_claimed=False))
    # All original source/evidence files remain untouched. The new files below
    # are a separate derived candidate, with the exact parent row hash recorded.
    derived=copy.deepcopy(parents)
    deltas=[]
    def setv(i,path,after,why):
        current=derived[i]
        for key in path[:-1]: current=current[key]
        before=current[path[-1]]
        if before==after: return
        current[path[-1]]=after
        deltas.append(dict(sample_id=derived[i]['sample_id'],path=list(path),before=before,after=after,reason=why))
    def settext(i,path,after): setv(i,path,after,'Grade2 plain language or direct mathematical feedback; no numerical/answer change.')
    for i,r in enumerate(derived):
        # Only learner-facing text/requests are simplified. Never rewrite page
        # receipts, inherited historical comparisons or other source evidence.
        for key in ('requested_quantity',):
            v=r[key].replace('hai cực trị','số nhỏ nhất và số lớn nhất').replace('cực trị','số nhỏ nhất và số lớn nhất')
            settext(i,(key,),v)
        for j,s in enumerate(r['worked_steps']):
            for key in ('title','reason','explanation'):
                v=s[key].replace('nhánh','nhóm')
                settext(i,('worked_steps',j,key),v)
        for j,h in enumerate(r['hints']):
            settext(i,('hints',j,'hint'),h['hint'].replace('nhánh','nhóm'))
    settext(0,('hints',2,'hint'),'Gộp các nhóm, sắp theo thứ tự tăng và dùng phép cộng để kiểm lại hiệu.')
    settext(0,('requested_quantity',),'Danh sách đủ số hai chữ số, số nhỏ nhất, số lớn nhất và hiệu')
    settext(1,('requested_quantity',),'Sửa danh sách bỏ sót, tìm số nhỏ nhất, số lớn nhất và hiệu')
    settext(1,('worked_steps',0,'explanation'),'10,40,80 là những số đúng cách dùng thẻ. Đề không bắt buộc dùng thẻ 0, nên danh sách này còn bỏ sót.')
    settext(2,('requested_quantity',),'Các số khác nhau, cách đặt thẻ theo thứ tự chục–đơn vị, số nhỏ nhất, số lớn nhất và hiệu')
    settext(2,('givens',1,'text'),'Phân biệt số đọc được và tên các thẻ đã dùng; chữ số hàng chục khác 0.')
    settext(2,('worked_steps',1,'title'),'Ghi tên thẻ rồi đọc số')
    settext(2,('worked_steps',3,'title'),'Tìm số nhỏ nhất, số lớn nhất và hiệu')
    settext(2,('hints',2,'hint'),'Gộp các cách đọc cùng một số, rồi tìm số nhỏ nhất và số lớn nhất.')
    settext(3,('problem',),'Có ba thẻ riêng A ghi 2, B ghi 2, C ghi 0. Trong mỗi lần, phải dùng đủ cả ba thẻ đúng một lần để lập số có ba chữ số; hàng trăm khác 0. Trả thẻ về giữa các lần. Khi liệt kê số thì gộp các cách đọc cùng giá trị, còn khi đếm cách đặt thẻ thì phân biệt A và B. Bạn viết: “A và B cùng ghi 2 nên bỏ B, chỉ còn số 20.” Hãy kiểm câu viết; liệt kê mọi giá trị và cách đặt thẻ theo thứ tự trăm–chục–đơn vị, nêu số nhỏ nhất, số lớn nhất và hiệu.')
    settext(3,('worked_steps',0,'explanation'),'Số 20 chỉ có hai chữ số và thiếu một thẻ, nên không đúng yêu cầu dùng đủ ba thẻ.')
    settext(3,('requested_quantity',),'Các số và cách đặt đủ ba thẻ, số nhỏ nhất, số lớn nhất và hiệu')
    settext(3,('worked_steps',2,'title'),'Liệt kê cách đặt thẻ và đọc các số')
    settext(4,('requested_quantity',),'Danh sách các số đạt yêu cầu, số nhỏ nhất, số lớn nhất và hiệu')
    settext(4,('givens',1,'text'),'Số được nhận phải lớn hơn 306; không nhận bằng 306, không thay mốc hoặc bỏ thẻ.')
    settext(4,('worked_steps',2,'title'),'Tìm số nhỏ nhất và lớn nhất trong danh sách đạt yêu cầu')
    settext(4,('worked_steps',2,'reason'),'Tìm số nhỏ nhất và số lớn nhất sau khi đã bỏ các số không đạt điều kiện.')
    settext(4,('worked_steps',3,'reason'),'Dùng đúng số lớn nhất và số nhỏ nhất đã tìm để trừ.')
    settext(4,('hints',2,'hint'),'Chỉ tìm số nhỏ nhất và số lớn nhất trong các số đã qua mọi điều kiện; dùng phép cộng để kiểm hiệu.')
    settext(5,('problem',),'Ba thẻ riêng ghi 1,2,4. Mỗi lần dùng đủ ba thẻ đúng một lần để lập số ba chữ số. Chỉ nhận số lớn hơn 500. Bạn viết: “Em chọn 421 vì lớn nhất rồi.” Hãy liệt kê mọi số có thể lập từ các thẻ trước khi kiểm mốc, rồi xác định có số nào được nhận không. Nếu có thì nêu số nhỏ nhất, lớn nhất trong các số được nhận; nếu không có thì nói rõ không có số nhỏ nhất và số lớn nhất đạt yêu cầu, không điền 0 thay cho hai số ấy. Không thay mốc 500 hoặc thêm thẻ.')
    settext(5,('requested_quantity',),'Các số lập được, có số nào đạt yêu cầu không, số nhỏ nhất và số lớn nhất nếu có')
    settext(5,('givens',1,'text'),'Số được nhận phải lớn hơn 500; không đổi các thẻ hoặc mốc để có số đạt yêu cầu.')
    settext(5,('worked_steps',0,'title'),'Liệt kê theo hàng trăm')
    settext(5,('worked_steps',0,'reason'),'Có ba lựa chọn hàng trăm; mỗi nhóm đổi chỗ hai thẻ còn lại.')
    settext(5,('worked_steps',1,'title'),'Tìm số lớn nhất từ các thẻ')
    settext(5,('worked_steps',2,'explanation'),'Mọi số lập được đều không vượt 421, nên đều nhỏ hơn 500. Vì vậy, 421 trong câu bạn viết không đạt điều kiện lớn hơn 500.')
    settext(5,('worked_steps',3,'title'),'Trả lời rõ khi không có số hợp lệ')
    settext(5,('worked_steps',3,'reason'),'Không có số nào đạt yêu cầu, nên không có số nhỏ nhất hay lớn nhất để chọn.')
    settext(5,('worked_steps',3,'result'),'Không có số nhỏ nhất hay lớn nhất đạt yêu cầu')
    settext(5,('worked_steps',3,'explanation'),'Không điền 0 vào câu trả lời số nhỏ nhất hay lớn nhất: 0 không được lập từ các thẻ và cũng không lớn hơn 500. Giữ nguyên đề và kết luận không có số nào đạt yêu cầu.')
    settext(5,('worked_steps',4,'explanation'),'2+2+2=6 cách đặt; các thẻ khác nhau nên cũng là sáu giá trị. Đã xét đủ sáu số; không còn số nào khác từ ba thẻ để đạt yêu cầu.')
    settext(5,('hints',2,'hint'),'Nếu chưa tìm được số hợp lệ, hãy kiểm tra đã xét hết các cách dùng thẻ chưa. Giữ nguyên các thẻ và điều kiện của đề.')
    for i,r in enumerate(derived):
        assert r['expected_answer']==parents[i]['expected_answer']
        assert r['independent_model']==parents[i]['independent_model']
        assert r['canonical_signatures']==L.source_signatures(r)
        r['provenance']['wording_derivation']=dict(parent_file='numerals_cohort1/cases.jsonl',parent_source_row_sha256=sha(source_lines[i]),
            method='Independent peer plain-language/observable-feedback polish only; all expected_answer bytes/expressions and original inventories preserved.',human_content_review_completed=False)
        r['quality_status']='PEER_POLISHED_DRAFT_PENDING_ROOT_REVIEW'
        check_answers(r,computations[i],i)
        assert not r['human_verified'] and not r['teacher_certified'] and not r['owner_human_reviewed']
    derived_chats=[]
    for r in derived:
        for c in chat_records(r):
            c['source_row_sha256']=sha(canon(r).encode('utf8'))
            c['quality_status']=r['quality_status']
            c['acceptance_status']=r['acceptance_status']
            derived_chats.append(c)
    check_chats(derived,derived_chats)
    OUT.mkdir(exist_ok=True)
    write_lines(OUT/'cases.jsonl',derived)
    write_lines(OUT/'chat.jsonl',derived_chats)
    write_lines(OUT/'wording_deltas.jsonl',deltas)
    qa=[]
    for i,r in enumerate(derived):
        rh=sha(canon(r).encode('utf8'))
        qa.append(dict(sample_id=r['sample_id'],source_row_sha256=rh,parent_source_row_sha256=sha(source_lines[i]),
            criteria={k:'PASS' for k in CRITERIA},semantic_note=NOTES[i],independent_computation=computations[i],numeric_checks=numeric_checks(r),
            actual_fields_read=original_reviews[i]['actual_fields_read'],
            hints_semantic_review='All initial guidance and all18hints/questions read. They describe grouping/place-value/card-use/bound checks without filling numeric results or the final feasibility label. No full worked solution in hints.',
            student_work_review='Only the three explicitly quoted synthetic statements are corrected. No hidden thought, image or learner action is asserted.',
            status='PASS_INDEPENDENT_PEER_DERIVED_DRAFT_ROOT_REVIEW_REQUIRED',human_review_claimed=False))
    write_lines(OUT/'peer_qa7.jsonl',qa)
    # True negative constraints, not tests that merely mirror a serialization.
    mutation_checks=[
        dict(case=0,wrong_rule='Even-only filter',witness=27,rejected=True),
        dict(case=0,wrong_rule='Repeat absent second2card',witness=22,rejected=True),
        dict(case=1,wrong_rule='Require0in every selected pair',witness=14,rejected=True),
        dict(case=1,wrong_rule='Use all4cards in2slots',impossible_slot_count=True,rejected=True),
        dict(case=2,wrong_rule='Count two physical arrangements as two values',numeric_values=1,physical_assignments=2,rejected=True),
        dict(case=2,wrong_rule='Admit05',leading_zero_invalid=True,rejected=True),
        dict(case=3,wrong_rule='Delete repeated-value Bcard',witness=20,invalid_length=2,rejected=True),
        dict(case=3,wrong_rule='Count four placements as four values',numeric_values=2,physical_assignments=4,rejected=True),
        dict(case=4,wrong_rule='Change strict> into >=',equality=306,in_before_bound=True,in_retained=False,rejected=True),
        dict(case=4,wrong_rule='Reuse6card to meet bound',witness=660,rejected=True),
        dict(case=5,wrong_rule='Choose unrestricted maximum421',witness=421,below_required_bound=500,rejected=True),
        dict(case=5,wrong_rule='Return0as feasible minimum',witness=0,rejected=True),
    ]
    assert 27 in computations[0]['values'] and 22 not in computations[0]['values']
    assert 14 in computations[1]['values'] and len(MODELS[1][0])>MODELS[1][1]
    assert len(computations[2]['values'])==1 and computations[2]['physical_assignments']==2
    assert 5 not in computations[2]['values'] and 20 not in computations[3]['values']
    assert len(computations[3]['values'])==2 and computations[3]['physical_assignments']==4
    assert 306 in computations[4]['stock_values_before_bound'] and 306 not in computations[4]['values']
    assert 660 not in computations[4]['values'] and 421<500 and not computations[5]['values']
    write_json(OUT/'independent_mutation_checks.json',mutation_checks)
    assert all(sha((P/name).read_bytes())==h for name,h in parent_hashes.items())
    receipt=dict(schema='MathVisionKid.G2Cohort1.IndependentPeerReview.v1',
        status='MATH_PASS_PARENT_PRESERVED_DERIVED_WORDING_READY_FOR_ROOT_REVIEW',
        source_cases_sha256=parent_hashes['cases.jsonl'],source_chat_sha256=parent_hashes['chat.jsonl'],
        original_case_reviews=original_reviews,
        derived_cases_sha256=sha((OUT/'cases.jsonl').read_bytes()),derived_chat_sha256=sha((OUT/'chat.jsonl').read_bytes()),
        derived_cases=6,derived_chat_rows=24,independent_oracles=6,numeric_Fraction_Decimal_steps=sum(len(x['numeric_checks']) for x in qa),
        mutation_checks=12,wording_deltas=len(deltas),expected_answers_unchanged=True,
        actual_nearest_source_count=5,
        nearest_semantic_assessment='Earlier parity-only distinct-card exemplar omits unrestricted values. New branches add optional-card selection with explicit erroneous extra condition, repeated resources versus values and physical placements, using all3slots, strict bound equality, and a bound with no feasible numeral. These are constraint/representation changes, not mere digit substitutions. Comparison is bounded to supplied five actual nearest references, not full-archive absence proof.',
        source_locator_scope='Inherited publisher-page receipts only. Peer did not newly view publisher images; no physical performance or image-reading coverage certified.',
        criteria7=CRITERIA,parents_unchanged=parent_hashes,root_acceptance_required=True,
        data_accepted=False,global_state_mutated=False,drive_mutated=False,training_started=False,human_review_claimed=False)
    write_json(P/'peer_review.json',receipt)
    files=[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json']
    write_json(OUT/'manifest.json',dict(schema='MathVisionKid.G2Cohort1.PeerPolishedDraft.v1',status='DRAFT_ROOT_REVIEW_REQUIRED',cases=6,chat_rows=24,files=files,parent_cases_sha256=parent_hashes['cases.jsonl'],peer_review_sha256=sha((P/'peer_review.json').read_bytes()),script_sha256=sha(Path(__file__).read_bytes()),expected_answers_unchanged=True,human_review_claimed=False,accepted=False))
    print(json.dumps(dict(status=receipt['status'],cases=6,chat=24,numeric=receipt['numeric_Fraction_Decimal_steps'],mutations=12,wording_deltas=len(deltas),peer_review_sha256=sha((P/'peer_review.json').read_bytes()),derived_cases_sha256=receipt['derived_cases_sha256'],derived_chat_sha256=receipt['derived_chat_sha256']),ensure_ascii=False))

if __name__=='__main__': main()
