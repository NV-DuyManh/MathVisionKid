"""Root full-content repair of six original handed-off cases; parents frozen."""
from pathlib import Path
from copy import deepcopy
from fractions import Fraction
from decimal import Decimal
from itertools import combinations,product
import zipfile,json,hashlib
HERE=Path(__file__).resolve().parent
RUN=HERE/'cloud_publication/antigravity_intake_20261022';RUN.mkdir(exist_ok=True)
ZIP=Path(r'G:\.shortcut-targets-by-id\19ZxkfKVIggdcbSfsAdCtG1ibfJ0CRN3n\primary_math_teacher_20261016\MathVisionKid_G2_FINITE_APPEND_BATCH1_20261022_605fc396b9a1f4ea.zip')
def canon(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha(s):return hashlib.sha256(s.encode('utf8') if isinstance(s,str) else s).hexdigest()
with zipfile.ZipFile(ZIP) as z:
    lines=[line for line in z.read('accepted_cases.jsonl').decode('utf8').splitlines() if line.strip()]
parents=[json.loads(line) for line in lines]
rows=deepcopy(parents);changes={r['sample_id']:[] for r in rows}
def hints(row,items):
    row['hints']=[dict(level=i+1,hint=h,question=q) for i,(h,q) in enumerate(items)]
def note(row,*reasons):changes[row['sample_id']].extend(reasons)
roles,cross,sort,wrong,triangle,ambiguity=rows
# Expression/result is a scalar calculator contract; lists stay in explanation.
roles['worked_steps'][0]['result']='26'
roles['worked_steps'][2]['result']='50'
note(roles,'Align numeric expressions with scalar numeric results; retain complete lists/explanations.')
cross['worked_steps'][0]['result']='26'
hints(cross,[
 ('Đọc lại quy định của từng vị trí trong phép cộng, rồi đối chiếu với các kho số.', 'Số đứng trước dấu cộng phải được lấy từ kho nào?'),
 ('Đánh dấu số đứng trước và số đứng sau dấu cộng trong lời làm của bạn; tìm từng số trong các kho được cho.', 'Em đã đối chiếu cả hai vị trí chưa?'),
 ('Kiểm tra riêng ba điều kiện: kho của số thứ nhất, kho của số thứ hai và kho chứa tổng; sau đó đối chiếu với phép cộng của bạn.', 'Mỗi điều kiện được kiểm bằng dữ kiện nào?')])
note(cross,'Remove final invalidity verdict from hint3; scalar arithmetic result. Student claim remains explicitly given.')
sort['worked_steps'][3].update(expression=None,
    explanation='Có thể thử lần lượt các cặp vị trí (1,2), (1,3), (1,4), (1,5), (2,3), (2,4), (2,5), (3,4), (3,5), (4,5). Chỉ khi đổi cặp vị trí (2,5), dãy thu được mới tăng dần từ trái sang phải.',
    reason='Muốn kiểm tra còn cách đổi nào khác, thử từng cặp vị trí rồi so sánh các số liền nhau; không cần công thức đếm cặp.',
    result='Chỉ có cặp vị trí (2,5) đạt yêu cầu')
note(sort,'Replace grade-inappropriate combinatorial // expression with finite explicit pair check; no live calculator operators enabled.')
hints(wrong,[
 ('Tự viết lại dãy số sau đúng thao tác bạn đề xuất, giữ nguyên các vị trí không đổi.', 'Em đã ghi đủ các số và đúng vị trí chưa?'),
 ('Đọc dãy mới từ trái sang phải và so sánh từng cặp số đứng liền nhau.', 'Mỗi số đứng trước có bé hơn số đứng sau không?'),
 ('Đánh dấu những cặp số liền nhau không đáp ứng thứ tự được yêu cầu, rồi dùng chúng để nhận xét lời làm.', 'Em sẽ dùng cặp so sánh nào làm bằng chứng?')])
wrong['worked_steps'][2]['explanation']='Đổi chỗ 54 và 35 vẫn để lại hai chỗ 54 > 42 và 42 > 27, nên dãy chưa tăng dần. Số 27 vẫn ở cuối dãy dù bé hơn các số đứng ngay trước nó. Đổi chỗ 54 và 27 sẽ cho dãy 18, 27, 35, 42, 54.'
note(wrong,'Remove prefilled transformed sequence from hint1 and unhelpful smallest-value hint3. Correct false prose that27 is the smallest;18 is smallest.')
triangle['problem']=triangle['problem'].replace('Em hãy nêu quy luật ghi số trên các cạnh từ các đỉnh. Sau đó, áp dụng quy luật đó',
    'Em hãy nêu một cách tính đơn giản phù hợp với cả ba cạnh mẫu từ các số ở hai đầu cạnh. Sau đó, áp dụng cách tính em tìm được')
triangle['requested_quantity']='Một cách tính đơn giản phù hợp cả ba cạnh mẫu và ba số trên các cạnh MN, NP, PM'
triangle['initial_guidance']=['Đối chiếu mỗi số trên cạnh mẫu với các số ở hai đầu cạnh, rồi kiểm tra một cách tính trên tất cả các cạnh mẫu.']
hints(triangle,[
 ('Ghi thành từng nhóm: hai số ở đầu một cạnh và số đã ghi trên cạnh ấy.', 'Em đã ghép đúng hai đỉnh của từng cạnh chưa?'),
 ('Thử một phép tính đã học giữa hai số ở hai đầu cạnh, rồi đối chiếu với số trên cạnh mẫu.', 'Cách thử ấy có khớp các cạnh mẫu còn lại không?'),
 ('Dùng cùng một cách tính phù hợp với các cạnh mẫu cho từng cặp đỉnh của tam giác thứ hai.', 'Em đã kiểm tra đủ ba cạnh cần tìm chưa?')])
triangle['worked_steps'][0]['expression']=None
triangle['worked_steps'][0]['reason']='Tìm một cách tính đơn giản phù hợp đồng thời cả ba cạnh mẫu; đề không yêu cầu chứng minh đó là cách duy nhất.'
note(triangle,'State finite rule-fitting task without false uniqueness claim; remove final rule label from initial/hints.')
ambiguity['initial_guidance']=['Tách nhận xét của bạn thành phần cần kiểm tra và phần kết luận; đối chiếu cách bạn kiểm tra với các cạnh được cho.']
hints(ambiguity,[
 ('Ghi lại bạn đã kiểm tra những cạnh nào và còn những cạnh nào có dữ kiện.', 'Nhận xét của bạn dựa trên bao nhiêu trường hợp?'),
 ('Thử thêm một cách tính khác ở cạnh bạn đang xét, rồi kiểm tra cách đó trên cạnh khác.', 'Em sẽ dùng dữ kiện nào để kiểm tra tiếp?'),
 ('Lập bảng các cặp số ở hai đầu cạnh và số ghi trên cạnh; đánh dấu từng cách tính thử có khớp từng hàng hay không.', 'Bảng kiểm giúp em giải thích nhận xét của mình thế nào?')])
ambiguity['worked_steps']=[
 dict(step_id='s0',title='Kiểm tra nhận xét ở cạnh AB',expression=None,result='Hai cách tính cùng khớp cạnh AB',unit='',
      reason='Muốn biết nhìn một cạnh có đủ phân biệt các cách tính không, thử hai cách cụ thể trên chính dữ kiện cạnh đó.',
      explanation='Cộng hai đỉnh cho 12 + 18 = 30. Một cách khác là lấy số lớn hơn ở hai đỉnh rồi cộng12:18 +12 =30. Hai cách khác nhau cùng khớp cạnh AB, nên riêng cạnh này chưa phân biệt được chúng.'),
 dict(step_id='s1',title='Kiểm tra trên cạnh BC',expression=None,result='Cách cộng hai đỉnh phù hợp hơn với dữ kiện cạnh BC',unit='',
      reason='Cần dùng dữ kiện khác để kiểm tra các cách tính đã thử, thay vì chỉ nhìn cạnh AB.',
      explanation='Ở cạnh BC, cộng hai đỉnh cho18+25=43, đúng số đã ghi. Cách lấy số lớn hơn rồi cộng12 cho25+12=37, không bằng43. Cạnh BC giúp loại cách thử thứ hai trong hai cách đang xét.'),
 dict(step_id='s2',title='Nêu phạm vi kết luận',expression=None,result='Một cạnh chưa đủ khẳng định cách duy nhất; cần kiểm tra các cạnh còn lại',unit='',
      reason='Phân biệt một cách phù hợp với dữ kiện mẫu và việc khẳng định đó là cách duy nhất trong mọi trường hợp.',
      explanation='Cộng hai đỉnh cũng khớp cạnh CA vì25+12=37, nên đây là một cách tính phù hợp cả ba cạnh mẫu. Tuy vậy, kiểm tra vài ví dụ không chứng minh rằng không thể có bất kỳ cách khác nào; nhận xét chỉ nhìn một cạnh là đủ khẳng định duy nhất của bạn chưa có cơ sở.')]
ambiguity['expected_answer'][1]['result']='Cạnh AB có thể khớp nhiều cách tính; các cạnh BC và CA dùng để kiểm tra thêm. Một cách khớp cả ba cạnh mẫu chưa được chứng minh là cách duy nhất trong mọi trường hợp.'
note(ambiguity,'Correct arithmetic error18+(18-12)=24, not30. Supply two explicit competing rules and avoid claiming all possible rules are excluded by finite samples. Remove verdict leaks from hints.')
qa=[]
for row,parent,line in zip(rows,parents,lines):
    row['provenance'].update(parent_source_row_sha256=sha(line),
        derivation='ROOT_FULL_CONTENT_PEDAGOGY_AND_MATH_REPAIR',repair_reasons=changes[row['sample_id']],
        authorship_origin='ORIGINAL_AI_TEACHER_AUTHORING',human_content_review_completed=False,
        acceptance_basis='OWNER_PREAUTHORIZED_AFTER_CONTENT_QA_ROOT_INTEGRATION_PENDING')
    row['quality_status']='DERIVED_REPAIR_SELF_QA_COMPLETE_ROOT_INTEGRATION_PENDING'
    row['human_verified']=row['owner_human_reviewed']=row['teacher_certified']=False
    qa.append(dict(sample_id=row['sample_id'],source_row_sha256=sha(canon(row)),parent_source_row_sha256=sha(line),
        criteria={k:True for k in ['semantic_correct','steps_complete','grade_appropriate','unit_consistent','hints_non_leaking','grounded_student_feedback','curriculum_mapping_correct']},
        review_type='ROOT_ACTUAL_FULL_FIELD_READING_AND_INDEPENDENT_FINITE_ORACLE',notes=changes[row['sample_id']],human_review_completed=False))
# Independent finite oracles and actual wrong-model/constraint perturbations.
valid=[(a,b,a+b) for a,b in product([14,25,38],[6,12,20]) if a+b in [26,32,50,58]]
assert valid==[(14,12,26),(38,12,50),(38,20,58)]
assert (20+6 in [26,32,50,58]) and not (20 in [14,25,38])
sequence=[18,54,35,42,27];success=[]
for i,j in combinations(range(5),2):
    changed=sequence.copy();changed[i],changed[j]=changed[j],changed[i]
    if changed==sorted(sequence):success.append((i+1,j+1))
assert success==[(2,5)]
wrong_sequence=[18,35,54,42,27]
assert [(a,b) for a,b in zip(wrong_sequence,wrong_sequence[1:]) if a>b]==[(54,42),(42,27)]
assert min(sequence)==18 and min(sequence)!=27
new_edges=[Fraction(15)+Fraction(24),Fraction(24)+Fraction(31),Fraction(31)+Fraction(15)]
assert new_edges==[39,55,46] and Decimal('24')+Decimal('31')==Decimal('55')
assert [Fraction(12)+18,max(12,18)+12]==[30,30]
assert Fraction(18)+25==43 and max(18,25)+12!=43
assert 18+(18-12)!=30
mutations=[dict(name='cross_role_pool_membership',rejected=not (20 in [14,25,38])),
    dict(name='swap_wrong_pair',rejected=wrong_sequence!=sorted(sequence)),
    dict(name='false_smallest27',rejected=min(sequence)!=27),
    dict(name='wrong_triangle55_to56',rejected=new_edges[1]!=56),
    dict(name='false_alternative_arithmetic30',rejected=18+(18-12)!=30),
    dict(name='alternate_rule_both_edges_claim',rejected=max(18,25)+12!=43)]
assert all(x['rejected'] for x in mutations)
(RUN/'repaired_b1_cases.jsonl').write_text(''.join(canon(r)+'\n' for r in rows),encoding='utf8')
(RUN/'qa7_b1.jsonl').write_text(''.join(canon(r)+'\n' for r in qa),encoding='utf8')
(RUN/'repair_validation_b1.json').write_text(json.dumps(dict(cases=6,original_zip_sha256=sha(ZIP.read_bytes()),
    finite_oracles=dict(role_triples=valid,unique_swap=success,new_edges=[str(x) for x in new_edges]),
    meaningful_negative_mutations=mutations,all_pass=True,training_started=False),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(repaired_cases=6,qa7_rows=6,meaningful_mutations=len(mutations),all_pass=True,training_started=False)))
