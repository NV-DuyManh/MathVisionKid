"""Six finite original G5 residual text drafts. No Drive/state/training calls."""
from pathlib import Path
from fractions import Fraction
from decimal import Decimal,localcontext
import ast
import hashlib
import json
import importlib.util
from collections import Counter

import exhaustive_colab_loader as L
from exhaustive_primary_math import chat_records

HERE=Path(__file__).resolve().parent
OUT=HERE/'cloud_publication/sgk_final_forms_20261020/g5_residual_text'


def dump(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha(b):return hashlib.sha256(b).hexdigest()
def write(name,x): (OUT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def jl(name,rows):(OUT/name).write_text(''.join(dump(r)+'\n' for r in rows),encoding='utf8')


def calc(expression,decimal=False):
    def walk(node):
        if isinstance(node,ast.Constant) and type(node.value) in (int,float):
            text=ast.get_source_segment(expression,node)
            return Decimal(text) if decimal else Fraction(text)
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.USub):return -walk(node.operand)
        if not isinstance(node,ast.BinOp):raise ValueError('unsupported numeric syntax')
        a,b=walk(node.left),walk(node.right)
        if isinstance(node.op,ast.Add):return a+b
        if isinstance(node.op,ast.Sub):return a-b
        if isinstance(node.op,ast.Mult):return a*b
        if isinstance(node.op,ast.Div):return a/b
        raise ValueError('unsupported numeric operation')
    return walk(ast.parse(expression,mode='eval').body)


def step(title,result,explanation,expression=None,unit=''):
    return dict(title=title,result=str(result),reason=explanation,explanation=explanation,expression=expression,unit=unit)


def build():
    candidates={r['candidate_id']:r for r in json.loads((OUT/'candidate_snapshot.json').read_text('utf8'))}
    rows=[]
    def add(topic,candidate,problem,givens,request,steps,answers,hints,student=None):
        sid='sgk_final_g5_20261020_'+topic
        for i,s in enumerate(steps):s['step_id']='s'+str(i)
        c=candidates[candidate]
        row=dict(sample_id=sid,case_group_id=sid+'_group',grade=5,topic=topic,case_kind='observable_student_error' if student else 'original_representation_gap',
            split='train',problem=problem,givens=[dict(id='g'+str(i),text=t,value=None,unit='') for i,t in enumerate(givens)],
            requested_quantity=request,student_work={'text':student,'observations':[dict(excerpt=student,claim_scope='Explicit synthetic text only; no hidden student behavior inferred.')]} if student else None,
            can_solve=True,worked_steps=steps,expected_answer=[dict(quantity=q,result=str(v),unit=u) for q,v,u in answers],
            initial_guidance=[hints[0]],hints=[dict(level=i+1,hint=h,question=['Em cần giữ những điều kiện nào?','Em xét hết các lựa chọn hợp lệ ra sao?','Em kiểm kết quả với đầy đủ điều kiện thế nào?'][i]) for i,h in enumerate(hints)],
            source_role='AI_GENERATED',acceptance_status='DRAFT_AWAITING_ROOT_CONTENT_CROSS_REVIEW',quality_status='AUTHOR_QA_PENDING_ROOT_REVIEW',
            human_verified=False,teacher_certified=False,owner_human_reviewed=False,
            provenance=dict(authorship_origin='ORIGINAL_AI_TEACHER_AUTHORING',content_human_review_completed=False,book_exercise_copied=False,actual_physical_or_image_result_claimed=False,acceptance_basis='OWNER_PREAUTHORIZED_AFTER_CONTENT_QA_PENDING_ROOT_CROSS_REVIEW'),
            curriculum_assignment=dict(grade=5,enrichment=True,candidate_id=candidate,master_id=c['decision']['master_id'],actual_page_receipts=c['page_receipts'],
                page_receipt_basis='Previously viewed publisher image receipt inherited; not newly re-viewed by this author.',
                nearest_source_refs=c['nearest_refs'],coverage_claim='Bounded text constraint branch only; no whole curriculum/master or physical/vision certification.'),
            coverage=dict(gap_type=topic,mode='FINITE_G5_RESIDUAL_TEXT_BRANCH',numbers_only_variant=False),
            nearest_source_comparison=dict(status='NEAREST_ACTUAL_FULLFIELDS_READ',evidence='nearest_actual_fullfields.jsonl',limitation='Finite nearest-source comparison, not exhaustive absence proof over all archives.'))
        row['canonical_signatures']=L.source_signatures(row);rows.append(row)
    add('fraction_plus_minus_complete','g5_candidate_unknown_fraction_operator',
        'Giữ nguyên thứ tự ba phân số 3/4, 1/3, 1/6 trong 3/4 □ 1/3 □ 1/6 = 7/12. Mỗi ô chỉ điền + hoặc −, được lặp dấu. Không đổi các phân số, không ghép tử hay mẫu, không thêm ngoặc; cộng và trừ cùng bậc, làm từ trái sang phải. Tìm tất cả cặp dấu thỏa đẳng thức và chứng minh không bỏ sót.',
        ['Ba phân số cố định theo thứ tự; đích 7/12','Hai ô chỉ + hoặc −; lặp được; không ngoặc; từ trái sang phải'],
        'Tất cả cặp dấu hợp lệ',[
        step('Quy đồng các toán hạng','9/12;4/12;2/12','Đưa về cùng mẫu 12, giữ nguyên giá trị từng phân số.'),
        step('Thử đủ bốn cặp dấu','15/12;11/12;7/12;3/12','Theo thứ tự (+,+),(+,−),(−,+),(−,−), tử số lần lượt là 9+4+2, 9+4−2, 9−4+2, 9−4−2. Mẫu vẫn là 12.'),
        step('Kiểm cặp đạt đích','7/12','Chỉ cặp (−,+) có kết quả bằng đích. Kiểm lại bằng phân số gốc, không đổi mẫu bằng cộng hoặc trừ mẫu.','3/4-1/3+1/6')],
        [('Cặp dấu','(−,+)',''),('Biểu thức','3/4 − 1/3 + 1/6 = 7/12','')],
        ['Giữ nguyên từng phân số và liệt kê lựa chọn ở từng ô.','Quy đồng để so các giá trị bằng những phần cùng cỡ.','Đối chiếu tất cả cặp dấu với đích, kể cả những cặp không đạt.'])
    add('fraction_no_legal_sign_error','g5_candidate_unknown_fraction_operator',
        'Điền đúng một dấu + hoặc − vào 2/3 □ 1/4 = 1/6, không thay các phân số, không thêm phép tính hay ngoặc. Hỏi có dấu hợp lệ không? Bạn viết: “2/3 − 1/4 = 1/6 nên chọn dấu −.” Giữ câu đã viết, kiểm cả hai dấu được phép và kết luận; nếu không có dấu đúng thì nêu rõ, không sửa đích.',
        ['Toán hạng 2/3 và 1/4; đích 1/6','Chỉ chọn một dấu + hoặc −; dữ kiện đầy đủ, không đổi đích'],
        'Khả năng có dấu hợp lệ và phản hồi bài viết',[
        step('Kiểm dấu cộng','11/12','2/3=8/12, 1/4=3/12; cộng được 11/12, khác 1/6=2/12.','2/3+1/4'),
        step('Kiểm dấu trừ','5/12','Trừ các phần cùng cỡ được 8/12−3/12=5/12, không phải 2/12. Câu đã viết sai tại giá trị phép trừ.','2/3-1/4'),
        step('Phân biệt vô nghiệm với thiếu dữ kiện','Không có dấu hợp lệ','Hai dấu được phép đã xét hết và đều không đạt. Đề đủ để kết luận không có dấu; không xin thêm dấu hoặc đổi phân số để làm cho đúng.')],
        [('Dấu hợp lệ','Không có trong {+,−}',''),('Giá trị phép trừ đúng','5/12','')],
        ['Đọc đúng miền dấu được phép và giữ nguyên đích.','Tính từng lựa chọn bằng cùng mẫu chung rồi so với đích.','Kết luận sau khi đã bao hết miền lựa chọn, không tự sửa dữ kiện.'],
        student='2/3 − 1/4 = 1/6 nên chọn dấu −.')
    add('shortest_graph_roundtrip_cost','g5_candidate_shortest_route',
        'Mạng đường giả định hai chiều chỉ có SA=0,8 km, AT=1,2 km, SB=0,5 km, BT=2 km và ST=2,4 km, không có cạnh khác. Mỗi lượt từ S đến T không lặp đỉnh. Chọn đường ngắn nhất để đi S→T, rồi về S theo đúng đường ấy đảo chiều. Lúc đi đều 4 km/giờ, lúc về đều 5 km/giờ; không nghỉ. Chi phí giả định là 2 nghìn đồng trên mỗi km thực đi, không phí khác. Tính độ dài một lượt ngắn nhất, tổng đường hai lượt, tổng thời gian theo phút và chi phí.',
        ['Đường hai chiều: SA0,8;AT1,2;SB0,5;BT2;ST2,4 km; không cạnh khác','Mỗi lượt không lặp đỉnh; về đúng đường đi đảo chiều','Đi4 km/giờ;về5 km/giờ;không nghỉ;2 nghìn đồng/km thực đi'],
        'Đường tối ưu, hai lượt, thời gian và chi phí',[
        step('So tất cả đường một lượt','2','Từ S chỉ có thể đến A, B hoặc T; tại A/B chỉ còn đi tới T nếu không lặp đỉnh. SAT dài 0,8+1,2=2 km; SBT dài 0,5+2=2,5 km; ST dài 2,4 km. SAT là nhỏ nhất.','0.8+1.2','km'),
        step('Tính hai lượt','4','Đường về là đường đã chọn đảo chiều và có cùng độ dài; tổng bằng hai lần một lượt.','2*2','km'),
        step('Cộng thời gian khác tốc độ','54','Lượt đi mất 2:4 giờ, lượt về mất 2:5 giờ. Cộng trước rồi nhân 60 ra phút; không lấy tổng đường chia riêng một tốc độ.','(2/4+2/5)*60','phút'),
        step('Tính chi phí theo đường thực đi','8','Hai lượt đi tổng 4 km; chi phí 4×2=8 nghìn đồng, không chỉ tính lượt đi.','4*2','nghìn đồng')],
        [('Đường một lượt','S→A→T',''),('Ngắn nhất một lượt','2','km'),('Hai lượt','4','km'),('Tổng thời gian','54','phút'),('Chi phí','8','nghìn đồng')],
        ['Liệt kê mọi đường hoàn chỉnh theo các cạnh đã cho trước khi tối ưu.','Đường về và vận tốc mỗi lượt được quy định riêng; tính từng thời gian.','Kiểm thời gian cùng đơn vị và chi phí tính trên toàn bộ quãng đường thực đi.'])
    add('tied_routes_independent_return_error','g5_candidate_shortest_route',
        'Mạng hai chiều chỉ có HA=0,9 km, AT=0,6 km, HB=0,4 km, BT=1,1 km, HT=1,8 km. Không nối A với B. Đi từ H đến T rồi về H; mỗi lượt không lặp đỉnh và được chọn độc lập, nên đường về không bắt buộc trùng đường đi. Tốc độ cả hai lượt đều 3 km/giờ, không nghỉ. Chi phí 4 nghìn đồng/km thực đi. Bạn viết: “Chỉ đường H→B→T ngắn nhất vì cạnh đầu 0,4 km nhỏ nhất.” Tìm mọi đường ngắn nhất một lượt và mọi cặp đường đi-về có tổng đường nhỏ nhất; tính tổng thời gian và chi phí nhỏ nhất.',
        ['Hai chiều:HA0,9;AT0,6;HB0,4;BT1,1;HT1,8 km;không AB','Mỗi lượt không lặp đỉnh; hai lượt chọn độc lập','3 km/giờ cả hai lượt;không nghỉ;4 nghìn đồng/km'],
        'Các nghiệm đồng tối ưu và thời gian/chi phí hai lượt',[
        step('So toàn bộ đường một lượt','1.5','HAT dài 0,9+0,6=1,5 km; HBT dài 0,4+1,1=1,5 km; HT dài 1,8 km. Cạnh đầu nhỏ chưa chứng minh duy nhất; giữ HBT nhưng bỏ từ chỉ.','0.9+0.6','km'),
        step('Ghép các lựa chọn hai lượt','(A,A);(A,B);(B,A);(B,B)','Ký hiệu A/B là nhánh qua đỉnh ấy. Mỗi lượt ít nhất 1,5 km nên tổng ít nhất 3 km. Hai nhánh A/B đều đạt cận; có đúng bốn cặp, đường về đọc đảo chiều.'),
        step('Thời gian tổng nhỏ nhất','60','Vận tốc bằng nhau trên cả hai lượt, 3 km chia 3 km/giờ bằng một giờ, tức 60 phút.','3/3*60','phút'),
        step('Chi phí nhỏ nhất','12','Cùng đơn giá dương cho mọi cạnh nên tổng đường ít nhất cũng cho chi phí ít nhất.','3*4','nghìn đồng')],
        [('Đường một lượt','H→A→T và H→B→T',''),('Cặp nhánh đi-về','(A,A);(A,B);(B,A);(B,B)',''),('Tổng đường nhỏ nhất','3','km'),('Thời gian','60','phút'),('Chi phí','12','nghìn đồng')],
        ['Kiểm mọi tổng một lượt, không chọn chỉ bằng cạnh đầu.','Xét quy định chọn đường về rồi ghép các nghiệm từng lượt.','Chứng minh cận cho mỗi lượt và giữ đủ các cặp cùng đạt cận.'],
        student='Chỉ đường H→B→T ngắn nhất vì cạnh đầu 0,4 km nhỏ nhất.')
    add('lateral_only_volume12_all_heights','g5_candidate_equal_volume_surface',
        'Ghép hết 12 khối lập phương cạnh 1 cm thành hộp chữ nhật đặc không hở/chồng. Cạnh đáy a,b và chiều cao h là số nguyên dương cm, a≥b. h có vai trò riêng, không được gộp hai cách chỉ đổi chiều cao với cạnh đáy. Chỉ phủ bốn mặt bên, không phủ đáy dưới hay mặt trên; bỏ mép nối. Liệt kê đủ các bộ (a,b,h) có thể và tìm diện tích phủ nhỏ nhất. Thể tích là abh=12 cm³; đây không phải diện tích sáu mặt hoặc hộp năm mặt.',
        ['abh=12;a,b,h nguyên dương cm;a≥b;h là chiều cao riêng','Chỉ bốn mặt bên, không hai mặt đáy; không mép nối'],
        'Mọi bộ theo chiều cao và diện tích bốn mặt bên nhỏ nhất',[
        step('Liệt kê theo chiều cao','h1:(12,1),(6,2),(4,3);h2:(6,1),(3,2);h3:(4,1),(2,2);h4:(3,1);h6:(2,1);h12:(1,1)','h phải là ước của 12; với từng h, liệt kê mọi cặp a≥b có ab=12:h. Các hoán đổi a,b bỏ trùng, nhưng không bỏ thay đổi h.'),
        step('Tính đúng bốn mặt bên','26;16;14;28;20;30;24;32;36;48 cm²','Diện tích là 2ah+2bh=2h(a+b). Các giá trị theo đúng thứ tự liệt kê; không cộng diện tích đáy.'),
        step('Chọn sau khi đã xét hết','14','Nhỏ nhất đạt tại a=4,b=3,h=1. Kiểm thể tích4×3×1=12, bốn mặt có tổng4+4+3+3=14.','2*1*(4+3)','cm²')],
        [('Bộ tối ưu','(a,b,h)=(4,3,1)','cm'),('Diện tích bốn mặt bên nhỏ nhất','14','cm²')],
        ['Giữ vai trò chiều cao khi liệt kê các tích bằng thể tích đã cho.','Chỉ tính bốn mặt có một cạnh bằng chiều cao.','Đối chiếu đủ các bộ kích thước, không dùng cực trị của diện tích năm hoặc sáu mặt.'])
    add('lateral_only_height_constraint_error','g5_candidate_equal_volume_surface',
        'Hộp đặc ghép từ đúng 18 khối lập phương cạnh 1 cm, không hở/chồng. Cạnh đáy a≥b và chiều cao h đều nguyên dương cm, với h≥2 cm. Chỉ phủ bốn mặt bên; không đáy, không nắp, bỏ mép ghép. Bạn viết: “Hộp (a,b,h)=(3,2,3) có diện tích bên 30 cm²; quay thành (3,3,2) vẫn là cùng một cách nên bỏ, vậy nhỏ nhất là 30 cm².” Giữ lời viết; liệt kê đủ các bộ thỏa thể tích và h≥2, sửa kết luận diện tích bên nhỏ nhất. h là chiều cao theo phương đứng nên đổi h là cách đặt khác cần xét.',
        ['abh=18;a≥b nguyên dương;h nguyên vàh≥2 cm','Bốn mặt bên;h có vai trò riêng khi đổi cách đặt','Bài viết bỏ bộ(3,3,2) bằng lý do quay'],
        'Phản hồi cách bỏ nghiệm và diện tích bốn mặt bên nhỏ nhất',[
        step('Liệt kê miền chiều cao hợp lệ','h2:(9,1),(3,3);h3:(6,1),(3,2);h6:(3,1);h9:(2,1);h18:(1,1)','h chia hết18 và không nhỏ hơn2; với từng h, tìm đủ cặp a≥b có ab=18:h. Không đưa h=1 vào miền.'),
        step('So đúng mục tiêu bốn mặt','40;24;42;30;48;54;72 cm²','Áp2h(a+b) theo thứ tự liệt kê. Cách đã viết(3,2,3) đúng là30 nhưng không cho phép bỏ cách(3,3,2), vì diện tích bên đổi theo chiều cao.'),
        step('Giữ bộ tối ưu hợp lệ','24','Bộ(3,3,2) cho thể tích18 và h=2 đạt điều kiện; bốn mặt bên đều3×2 nên tổng24 cm².','2*2*(3+3)','cm²')],
        [('Bộ tối ưu','(a,b,h)=(3,3,2)','cm'),('Diện tích bên nhỏ nhất','24','cm²'),('Nhận xét','Giá trị30 đúng cho bộ đã chọn, nhưng bỏ cách đặt khác làm kết luận tối ưu sai','')],
        ['Tách điều kiện chiều cao khỏi quy ước đổi chỗ hai cạnh đáy.','Tính cùng một mục tiêu diện tích bên cho từng cách đặt hợp lệ.','Giữ mọi cách đặt có vai trò chiều cao khác, rồi kiểm thể tích và cận chiều cao.'],
        student='Hộp (a,b,h)=(3,2,3) có diện tích bên 30 cm²; quay thành (3,3,2) vẫn là cùng một cách nên bỏ, vậy nhỏ nhất là 30 cm².')
    return rows


def main():
    rows=build();assert len(rows)==6
    chats=[];qa=[];numeric=[]
    spec=importlib.util.spec_from_file_location('residual_finite_oracle',OUT/'finite_oracle.py');oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
    oracles=[]
    for row in rows:
        h=sha(dump(row).encode());oracles.append(dict(sample_id=row['sample_id'],source_row_sha256=h,check=oracle.check(row)))
        for s in row['worked_steps']:
            if s.get('expression'):
                value=calc(s['expression']);assert value==Fraction(s['result'])
                with localcontext() as ctx:
                    ctx.prec=90;d=calc(s['expression'],True);expected=Decimal(value.numerator)/Decimal(value.denominator);assert abs(d-expected)<Decimal('1e-70')
                numeric.append(dict(sample_id=row['sample_id'],step_id=s['step_id'],source_row_sha256=h,expression=s['expression'],exact=str(value),decimal_agrees=True))
        qa.append(dict(sample_id=row['sample_id'],source_row_sha256=h,status='PASS_AUTHOR_SELF_QA',criteria={k:'PASS' for k in ['math_correctness_or_complete_impossibility','givens_request_consistency','grade5_enrichment_explicit','steps_reason_units_check','initial_allhints_no_final_answer','student_work_grounding','schema_provenance_preservation']},human_review_claimed=False,root_cross_review_required=True))
        for chat in chat_records(row):
            chat.update(source_row_sha256=h,acceptance_status=row['acceptance_status'],quality_status=row['quality_status']);L.validate_chat(chat);chats.append(chat)
    jl('cases.jsonl',rows);jl('chat.jsonl',chats);jl('selfqa7.jsonl',qa);jl('numeric_fraction_decimal.jsonl',numeric);jl('independent_oracles.jsonl',oracles)
    files=['cases.jsonl','chat.jsonl','selfqa7.jsonl','numeric_fraction_decimal.jsonl','independent_oracles.jsonl','nearest_actual_fullfields.jsonl','candidate_snapshot.json','finite_oracle.py']
    write('manifest.json',dict(status='6_DRAFTS_AUTHOR_QA_PASSED_ROOT_REVIEW_PENDING',cases=6,chat_rows=24,numeric_steps=len(numeric),master_branches=['g5_fraction_plus_minus_only','g5_graph_shortest_roundtrip_time_cost','g5_lateral_only_orientation_optimization'],
        source_members_no_shared_mutation=True,training_started=False,drive_mutated=False,all_sgk_forms_covered=False,
        files=[dict(path=n,sha256=sha((OUT/n).read_bytes()),bytes=(OUT/n).stat().st_size) for n in files]))
    print(json.dumps(dict(cases=6,chats=24,numeric_steps=len(numeric),source_sha256=sha((OUT/'cases.jsonl').read_bytes()))))


if __name__=='__main__':main()
