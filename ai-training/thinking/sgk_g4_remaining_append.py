"""Exactly twenty original draft cases for ten pre-adjudicated G4 forms."""
from pathlib import Path
from fractions import Fraction
from decimal import Decimal,localcontext
from collections import deque
from itertools import combinations,product
import ast,hashlib,json
from exhaustive_primary_math import chat_records,expression_group
RUN=Path(__file__).parent/'cloud_publication/sgk_page_audit_20261019'
OUT=RUN/'g4_remaining_append'
ROWS=[]
def dump(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha(b):return hashlib.sha256(b).hexdigest()
def step(t,r,v,e,expr=None,u=''):return dict(title=t,reason=r,result=str(v),explanation=e,expression=expr,unit=u)
def hints(a,b,c):return [dict(level=i+1,hint=h,question=q) for i,(h,q) in enumerate(zip([a,b,c],['Em cần giữ đúng dữ kiện và quy tắc nào?','Em thực hiện theo quan hệ đó ra sao?','Em kiểm lại đủ các điều kiện bằng cách nào?']))]
def add(topic,problem,givens,request,steps,answers,hs,candidate,oracle,student=None,enrichment=True):
    sid=f'sgk_g4extra_20261019_{topic}_{sum(x["topic"]==topic for x in ROWS)+1:02d}'
    mapping=json.loads((RUN/'g4_audit/remaining_candidate_adjudication.json').read_text(encoding='utf-8'))
    evidence=next(x for x in mapping['candidates'] if x['candidate_id']==candidate)
    loc=evidence['actual_page_receipts'][0]
    ROWS.append(dict(sample_id=sid,case_group_id=sid+'_group',grade=4,topic=topic,split='train',case_kind='observable_student_error' if student else 'original_finite_reasoning',problem=problem,givens=[dict(id=f'g{i}',text=t,value=None,unit='',role='explicit_original_given') for i,t in enumerate(givens)],requested_quantity=request,student_work=dict(text=student,observations=[dict(excerpt=student,claim_scope='Only explicitly supplied synthetic written work; no private thinking or unseen image inferred.')]) if student else None,can_solve=True,initial_guidance=[hs[0]['hint']],hints=hs,worked_steps=[dict(step_id=f's{i}',**s) for i,s in enumerate(steps)],expected_answer=[dict(quantity=q,result=str(v),unit=u) for q,v,u in answers],canonical_signatures=sorted({expression_group(s['expression']) for s in steps if s['expression']}),gap_oracle=oracle,acceptance_status='DRAFT_AWAITING_CONTENT_CROSS_REVIEW',quality_status='AUTHOR_SELF_QA_PENDING_CROSS_REVIEW',human_verified=False,teacher_certified=False,owner_human_reviewed=False,source_role='AI_GENERATED',provenance=dict(authorship_origin='ORIGINAL_AI_TEACHER_AUTHORING',content_human_review_completed=False,acceptance_basis='OWNER_PREAUTHORIZED_PROCESS_CROSS_REVIEW_PENDING',book_exercise_copied=False,actual_physical_or_image_result_claimed=False),curriculum_assignment=dict(grade=4,book='Kết nối tri thức với cuộc sống',volume=1 if loc['book_id']=='g4v1' else 2,lesson_page=loc['printed_page'],publisher_page_url=loc['image_url'],source_image_sha256=loc['image_sha256'],source_evidence_level='ROOT_ACTUAL_PAGE_RECEIPT_AND_EXACT_TRAIN_FIELD_COMPARISON',coverage_claim='Original explicit text analogue of a confirmed finite representation gap; not whole curriculum or visual coverage.',enrichment=enrichment),coverage=dict(mode='FINITE_SUPPLEMENTARY_APPEND_NOT_CORE',new_core_slots_claimed=0,master_candidate=candidate,gap_type=topic,numbers_only_variant=False),nearest_source_comparison=dict(mapping_file='g4_audit/remaining_candidate_adjudication.json',mapping_file_sha256=sha((RUN/'g4_audit/remaining_candidate_adjudication.json').read_bytes()),nearest_actual_valid_train_rows=evidence['nearest_actual_valid_train_rows'],semantic_difference=evidence['semantic_adjudication']),quality_flags=dict(text_description_only_not_vision_training=True,three_hint_levels_answer_free=True,actual_image_or_physical_asset_present=False,app_plan_draft_compatible=False)))

def game_and_shuttle():
    t='board_turn_privilege'
    add(t,'Hai bạn An và Bình luân phiên theo thứ tự An rồi Bình. Quân An ở ô 1; đang đến lượt An. Mỗi lần gieo được k chấm thì tiến k ô, không tính ô đang đứng. Ô 3 là ô xanh: trả lời đúng phép 3 + 5 thì được gieo thêm ngay một lần; ô 4 là ô thường, trả lời đúng 6 − 2 thì hết lượt. Lần đầu An gieo 2 và trả lời 8; lần thêm An gieo 1 và trả lời 4. Không có luật khác. Sau hai lần gieo ấy, quân An ở đâu và đến lượt ai?',['Thứ tự An, Bình; An bắt đầu ô 1','Xanh ô 3 thưởng đúng một lần gieo thêm khi trả lời đúng','Thường ô 4 kết thúc lượt; bản ghi đủ hai lần gieo/câu trả lời'],'Vị trí An và người đến lượt tiếp theo',[
        step('Xét lần gieo đầu','Tiến theo các ô mới vào, rồi kiểm phép tại ô đến.','3','An vào ô 2 rồi ô 3; câu trả lời 8 đúng với 3 + 5 nên áp dụng quyền gieo thêm, chưa chuyển sang Bình.','1+2','ô'),
        step('Xét lần gieo thêm','Lần thêm bắt đầu từ vị trí sau lần đầu.','4','Từ ô 3 tiến một ô đến ô 4. 6 − 2 = 4 đúng; ô thường không cho thêm lượt.','3+1','ô'),
        step('Kiểm thứ tự người chơi','Hết lượt của An thì chuyển cho người kế trong vòng luân phiên.','Bình','An ở ô 4, tiếp theo là Bình. Kiểm cả hai câu trả lời đều khớp; không coi lần gieo thưởng là lượt của Bình.')], [('Vị trí An',4,'ô'),('Người tiếp theo','Bình','')],hints('Tách vị trí quân và quyền chơi lượt tiếp theo.','Đối chiếu câu trả lời thực tế với phép ở chính ô đến trước khi dùng luật ô màu.','Theo dõi lần gieo thưởng riêng với việc chuyển người chơi.'),'board_turn_privilege_transition',dict(kind='board_extra',start=1,rolls=[2,1],answers=[8,4],expected_position=4,expected_next='Bình'))
    add(t,'Hai bạn M và N luân phiên M rồi N; quân M ở ô 1, quân N ở ô 2. Đầu bản ghi đến lượt M và M có đúng một lượt phải bỏ từ trước: bỏ lượt thì không gieo, không đi, xóa dấu phải bỏ rồi chuyển người. Sau đó N gieo 2, vào ô 4 màu đỏ; luật đỏ chỉ ghi thêm đúng một lượt thường tiếp theo của chính người vừa vào ô phải bỏ. Tiếp đó M gieo 1, vào ô 2 thường. Không có luật đúng/sai hay thưởng khác. Liệt kê bốn lượt thường đầu tiên kể từ đầu bản ghi, gồm cả lượt bị bỏ, và vị trí hai quân sau đó.',['M bỏ một lượt ở đầu rồi xóa dấu bỏ','N từ ô 2 gieo 2 vào ô đỏ 4, tự nhận dấu bỏ lượt sau','M sau đó gieo 1 từ ô 1; ô 2 thường'],'Thứ tự hành động và vị trí sau bốn lượt thường',[
        step('Dùng dấu bỏ lượt có sẵn','Bỏ lượt là một lượt thường trong vòng luân phiên nhưng không làm quân đi.','Lượt 1: M bỏ','M vẫn ở ô 1 và xóa dấu bỏ. Tiếp theo chuyển N; không tự dùng một kết quả gieo cho lượt bị bỏ.'),
        step('Ghi vị trí và dấu bỏ của N','Quyền phải bỏ thuộc chính người vào ô đỏ.','4','Lượt 2 N tiến hai ô từ ô 2 đến ô 4; N nhận dấu bỏ lượt thường tiếp theo của N.','2+2','ô'),
        step('Theo dõi lượt xen giữa','N phải bỏ lượt của N, không làm M mất lượt.','2','Lượt 3 M tiến từ ô 1 đến ô 2 thường.','1+1','ô'),
        step('Kiểm lượt thứ tư','Đến N thì dùng và xóa dấu bỏ, không lùi hoặc tiến quân.','Lượt 4: N bỏ','Chuỗi là M bỏ; N gieo; M gieo; N bỏ. Sau đó M ở ô 2, N ở ô 4; cả hai không còn dấu bỏ. Kiểm chỉ có hai lần gieo được cho.')],[('Bốn lượt','M bỏ; N gieo; M gieo; N bỏ',''),('Vị trí cuối','M: 2; N: 4','ô')],hints('Giữ dấu phải bỏ riêng cho từng bạn và giữ thứ tự luân phiên.','Một lượt bị bỏ vẫn trôi qua trong vòng chơi, nhưng không dùng xúc xắc.','Sau khi dùng một dấu bỏ, kiểm đã xóa dấu của đúng người chưa.'),'board_turn_privilege_transition',dict(kind='board_skip',expected_actions=['M_skip','N_move','M_move','N_skip'],expected_positions={'M':2,'N':4}))
    t='boat_shuttle'
    add(t,'Ba người A nặng 60 kg, B nặng 40 kg, C nặng 20 kg cùng ở bờ trái. Thuyền ở bờ trái, chở tối đa 60 kg mỗi chuyến, kể cả đúng 60 kg; mỗi chuyến phải có ít nhất một người và ai cũng chèo được. Không gửi người hoặc thuyền qua bằng cách khác. Tìm một kế hoạch ít chuyến nhất để cả ba người và thuyền sang bờ phải; ghi người trên từng chuyến và kiểm tải.',['A 60 kg, B 40 kg, C 20 kg','Thuyền tối đa 60 kg, cần người chèo mỗi chuyến','Ban đầu tất cả trái; đích tất cả phải, gồm thuyền'],'Kế hoạch hợp lệ và số chuyến ít nhất',[
        step('Đưa hai người nhẹ sang trước','A đi cùng bất kỳ ai cũng quá tải, nên cần bố trí người đưa thuyền về.','60','Chuyến 1 B và C sang phải, tải 40 + 20 = 60 kg. Chuyến 2 C quay trái, tải 20 kg. B ở lại phải.','40+20','kg'),
        step('Đưa người nặng qua và trả thuyền','A phải đi riêng; cần người ở bờ phải đưa thuyền về cho người còn lại.','A sang; B về','Chuyến 3 A sang một mình tải 60 kg. Chuyến 4 B về trái tải 40 kg; A ở lại phải.'),
        step('Hoàn tất và kiểm từng trạng thái','B và C ở trái cùng thuyền nên có thể sang chung theo giới hạn.','5','Chuyến 5 B,C sang tải 60 kg. Mỗi chuyến có người và không quá 60 kg; cuối cùng cả ba và thuyền đều phải.','1+1+1+1+1','chuyến'),
        step('Kiểm tính ít nhất','Nếu chỉ có ba chuyến thì chỉ hai lượt sang và một lượt về.','Không thể chỉ ba chuyến','Một lượt sang phải dành riêng cho A; lượt sang còn lại phải chở B và C để cả ba có thể qua. Nếu A sang trước, chuyến về chỉ có thể do A chèo nên A còn ở trái khi B,C sang sau. Nếu B,C sang trước, một trong hai người phải chèo về và còn ở trái khi A sang riêng sau đó. Một chuyến không chở được cả ba; hai hoặc bốn chuyến đưa thuyền trở về trái, trái đích yêu cầu. Vì vậy năm chuyến là ít nhất.')],[('Số chuyến ít nhất',5,'chuyến'),('Một kế hoạch','B,C →; C ←; A →; B ←; B,C →','')],hints('Ghi bờ của từng người cùng vị trí thuyền sau mỗi chuyến.','Mỗi chuyến về cũng phải có người chèo và chịu giới hạn tải.','Kiểm kế hoạch đã đưa đủ mọi người qua và thử giải thích vì sao ít chuyến hơn không đủ.'),'boat_shuttle_state_plan',dict(kind='shuttle',weights={'A':60,'B':40,'C':20},capacity=60,expected_minimum=5,plan=[['B','C'],['C'],['A'],['B'],['B','C']]))
    add(t,'A nặng 70 kg, B nặng 35 kg, C nặng 25 kg cùng ở bờ trái. Thuyền chở tối đa 60 kg mỗi chuyến, kể cả khi chỉ có một người. Mỗi chuyến phải có người chèo; ai cũng chèo được; không có thuyền khác và không được bỏ bớt đồ để đổi các khối lượng đã cho. Có kế hoạch nào đưa cả ba sang bờ phải đúng luật không?',['A 70 kg; B 35 kg; C 25 kg','Mỗi chuyến tối đa 60 kg, không có cách sang khác'],'Khả năng có kế hoạch đúng luật',[
        step('Kiểm người không thể lên thuyền','Một người đi một mình vẫn phải thỏa giới hạn của chuyến.','10','A nặng hơn mức tối đa 70 − 60 = 10 kg. Thêm người không làm tải giảm.','70-60','kg'),
        step('Kiểm đích yêu cầu đủ mọi người','Bất kỳ kế hoạch hoàn tất đều cần một chuyến chở A sang.','Không có kế hoạch hợp lệ','Ngay cả A đi riêng đã quá tải nên không có chuyến hợp lệ mang A qua. B và C đi được không chứng minh cả ba đi được; không sửa khối lượng hay sức chở để tạo kế hoạch.')],[('Khả năng','Không có kế hoạch hợp lệ','')],hints('Kiểm từng người có thể ở trên một chuyến hợp lệ trước khi lập lịch.','Giới hạn áp dụng cho mọi chuyến, kể cả chuyến chỉ có một người.','Đích yêu cầu tất cả mọi người, không chỉ một nhóm qua được.'),'boat_shuttle_state_plan',dict(kind='shuttle',weights={'A':70,'B':35,'C':25},capacity=60,expected_minimum=None))

def bars_dials_crosswords():
    t='bar_model_to_story'
    add(t,'Sơ đồ bằng chữ có hai thanh biểu thị số sách trên hai giá: thanh Trên gồm một phần bằng trọn thanh Dưới và phần hơn 4 quyển. Ngoặc tổng hai thanh ghi 28 quyển. Hãy đặt một bài toán có lời khớp đủ sơ đồ, rồi giải và kiểm. Có thể có nhiều cách viết câu; chỉ cần nêu một cách đúng.',['Trên = Dưới và thêm 4 quyển','Tổng hai giá 28 quyển'],'Một bài toán phù hợp và số sách mỗi giá',[
        step('Chuyển mỗi quan hệ thành lời','Bài đặt phải giữ cả tổng lẫn chiều hơn kém của hai nhãn.','Một bài toán phù hợp','Hai giá có tất cả 28 quyển sách. Giá trên nhiều hơn giá dưới 4 quyển. Hỏi mỗi giá có bao nhiêu quyển? Đây là một cách đặt, không phải câu văn duy nhất.'),
        step('Tạo hai phần bằng thanh dưới','Bớt phần hơn khỏi tổng thì còn hai lượng bằng nhau.','12','(28 − 4) : 2 = 12 quyển ở giá dưới.','(28-4)/2','quyển'),
        step('Khôi phục thanh trên và kiểm sơ đồ','Thêm lại đúng phần hơn; kiểm cả hai điều kiện.','16','12 + 4 = 16 quyển ở giá trên. Kiểm 16 + 12 = 28 và 16 − 12 = 4, khớp hai nhãn của sơ đồ.','12+4','quyển')],[('Một bài toán','Hai giá có tổng 28 quyển; giá trên hơn giá dưới 4 quyển. Hỏi mỗi giá có mấy quyển?',''),('Giá dưới',12,'quyển'),('Giá trên',16,'quyển')],hints('Đọc riêng tên hai thanh, phần bằng nhau, phần hơn và ngoặc tổng.','Câu hỏi tự đặt phải yêu cầu đại lượng mà sơ đồ còn chưa ghi.','Dùng lời bài toán đã đặt để dựng lại các quan hệ trên hai thanh.'),'bar_model_to_story',dict(kind='bar_sum_difference',total=28,difference=4,expected_small=12,expected_large=16))
    add(t,'Sơ đồ bằng chữ: thanh Đỏ gồm bốn khối bằng nhau, thanh Xanh gồm một khối cùng cỡ. Ngoặc chỉ phần thanh Đỏ dài hơn thanh Xanh ghi 12 viên bi; không có ngoặc tổng. Bạn đặt bài: Đỏ có gấp bốn số bi của Xanh; cả hai có 12 viên; hỏi mỗi hộp có mấy viên? Giữ câu của bạn, sửa dữ kiện không khớp sơ đồ rồi giải bài đúng.',['Đỏ bốn khối; Xanh một khối cùng cỡ','12 viên là phần hơn, không phải tổng'],'Bài toán sửa đúng và số bi mỗi hộp',[
        step('Đối chiếu từng câu với đúng ngoặc','Bốn khối so với một khối cho quan hệ gấp bốn; ngoặc 12 chỉ phần hơn.','Sửa cả hai có 12 thành Đỏ nhiều hơn Xanh 12','Bài đúng có thể viết: Hộp Đỏ có gấp bốn số bi của hộp Xanh và nhiều hơn hộp Xanh 12 viên. Hỏi số bi mỗi hộp? Không tự thêm dữ kiện tổng.'),
        step('Tìm lượng của một khối','Phần hơn gồm ba khối bằng nhau.','4','12 : (4 − 1) = 4 viên, cũng là số bi của Xanh.','12/(4-1)','viên'),
        step('Tìm hộp Đỏ và kiểm','Đỏ có bốn khối, mỗi khối vừa tìm được.','16','4 × 4 = 16 viên. Kiểm 16 − 4 = 12 và 16 = 4 × 4. Tổng thực tế là 20 viên nên câu tổng 12 không khớp sơ đồ.','4*4','viên')],[('Xanh',4,'viên'),('Đỏ',16,'viên'),('Sửa dữ kiện','Đỏ nhiều hơn Xanh 12 viên, không phải cả hai có 12 viên','')],hints('Xác định ngoặc số đang chỉ toàn bộ hay phần chênh lệch.','Giữ các khối bằng nhau và đúng nhãn của từng thanh khi sửa câu.','Kiểm bài sửa bằng cả quan hệ số khối lẫn số ghi tại ngoặc.'),'bar_model_to_story',dict(kind='bar_ratio_difference',ratio=4,difference=12,expected_small=4,expected_large=16),student='Đỏ có gấp bốn số bi của Xanh; cả hai có 12 viên; hỏi mỗi hộp có mấy viên?')
    t='regular_dial_angle'
    add(t,'Mặt đồng hồ mô hình chia một vòng tròn 360° thành 12 khoảng bằng nhau giữa các số liên tiếp. Kim thứ nhất chỉ đúng số 2, kim thứ hai chỉ đúng số 7; chỉ xét góc nhỏ hơn tạo bởi hai kim, không xét chuyển động giữa hai thời điểm. Tính số đo góc ấy và kiểm theo cả hai đường đi quanh mặt số.',['Một vòng 360°, 12 khoảng đều','Hai tia từ tâm qua số 2 và số 7; xét góc nhỏ hơn'],'Số đo góc nhỏ hơn',[
        step('Tìm độ mở mỗi khoảng','Các khoảng bằng nhau phủ đủ một vòng.','30','360 : 12 = 30° cho mỗi khoảng giữa hai số liền nhau.','360/12','độ'),
        step('Đếm hai đường quanh vòng','Hai kim chia vòng thành hai đường có tổng mười hai khoảng.','5 khoảng và 7 khoảng','Từ 2 qua 3,4,5,6 đến 7 có năm khoảng; đường còn lại có bảy. Đường năm khoảng ngắn hơn, không đếm số nhãn thành số khoảng.'),
        step('Tính và kiểm góc','Lấy số khoảng của góc nhỏ nhân độ mở một khoảng.','150','5 × 30 = 150°. Góc phía kia 7 × 30 = 210°; 150 + 210 = 360 và 150 nhỏ hơn 210.','5*30','độ')],[('Góc nhỏ',150,'độ')],hints('Phân biệt số nhãn với số khoảng bằng nhau quanh một vòng.','Hai tia tạo hai phần của vòng; xác định phần được hỏi trước khi nhân.','Kiểm hai phần góc cộng lại có đủ một vòng và phần đã chọn có đúng nhỏ hơn không.'),'regular_dial_angle',dict(kind='dial',sectors=12,start=2,end=7,expected_minor=150))
    add(t,'Vòng quay có tám nan từ cùng một tâm, đánh số 0,1,2,3,4,5,6,7 theo chiều kim đồng hồ, các khoảng đều nhau và một vòng là 360°. Cần góc nhỏ hơn giữa nan 0 và nan 6. Bạn ghi: đi theo chiều kim đồng hồ qua sáu khoảng nên góc nhỏ là 270°. Giữ câu, kiểm và sửa phần chưa đúng.',['Tám khoảng đều quanh 360°','Nan 0 và nan 6; cần góc nhỏ hơn'],'Số đo góc nhỏ và nhận xét',[
        step('Tìm độ mở một khoảng','Chia đều một vòng cho tám khoảng.','45','360 : 8 = 45°; không phải mỗi nan tự có một góc khác nhau.','360/8','độ'),
        step('Kiểm phần vòng được đếm','Đi theo một chiều có thể cho góc lớn hơn, dù số khoảng đếm đúng.','Hai khoảng theo chiều ngược','Sáu khoảng đúng là 270°, nhưng từ nan 0 đi ngược chiều qua nan 7 đến nan 6 chỉ có hai khoảng. Câu hỏi không yêu cầu góc theo chiều kim đồng hồ.'),
        step('Sửa góc nhỏ và kiểm','Chọn đường ít khoảng hơn giữa chính hai nan ấy.','90','2 × 45 = 90°. Kiểm 90 + 270 = 360 và 90 < 270; lỗi nằm ở chọn phần vòng, không nằm ở phép nhân sáu khoảng.','2*45','độ')],[('Góc nhỏ',90,'độ'),('Nhận xét','270° là phần lớn hơn; cần phần hai khoảng','')],hints('Giữ rõ góc theo một chiều đi và góc nhỏ hơn là hai yêu cầu khác nhau.','Thử đếm từ cùng hai nan theo chiều còn lại.','Hai số khoảng phải cộng thành số khoảng của cả vòng.'),'regular_dial_angle',dict(kind='dial',sectors=8,start=0,end=6,expected_minor=90),student='Đi theo chiều kim đồng hồ qua sáu khoảng nên góc nhỏ là 270°.')
    t='numeric_crossword'
    add(t,'Bốn ô chữ số xếp thành lưới hai hàng: hàng trên A,B; hàng dưới C,D. Đọc trái sang phải được hai số AB và CD; đọc trên xuống dưới được AC và BD, đều là số hai chữ số. Các chữ là vị trí, không phải phép nhân. Biết AB bằng 4 × 6, AC bằng 20 + 3 và BD bằng 50 − 4. Điền bốn ô, nêu số CD và kiểm các ô giao nhau.',['Lưới A B / C D','AB=4×6; AC=20+3; BD=50−4','Chữ số đầu của mọi số hai chữ số khác 0'],'Bốn chữ số và số CD',[
        step('Điền hàng có đủ phép tính','Một giá trị hàng xác định chữ số ở đúng hai vị trí.','24','4 × 6 = 24, nên A = 2, B = 4.','4*6',''),
        step('Dùng cột trái chia sẻ ô A','Cột AC phải giữ nguyên chữ số A vừa điền.','23','20 + 3 = 23, khớp A = 2 nên C = 3.','20+3',''),
        step('Dùng cột phải chia sẻ ô B','Cột BD phải giữ nguyên B; không có một ô B khác cho cột.','46','50 − 4 = 46, khớp B = 4 nên D = 6. Hàng dưới CD là 36.','50-4',''),
        step('Kiểm mọi giao điểm','Mỗi ô được dùng nhất quán khi đọc theo hàng và cột.','A=2, B=4, C=3, D=6; CD=36','Đọc lại hàng trên 24, cột trái 23, cột phải 46 đều đúng. Bốn ô không đổi giữa hai cách đọc, các chữ số đầu khác 0.')],[('Các ô','A=2; B=4; C=3; D=6',''),('CD',36,'')],hints('Một ô giao nhau phải giữ cùng chữ số khi đọc theo hàng và cột.','Tính giá trị của một mục có đủ dữ kiện trước, rồi chuyển chữ số sang mục cắt nó.','Đọc lại mọi mục từ cùng một lưới, không sửa riêng một bản sao của ô giao.'),'numeric_crossword_intersections',dict(kind='crossword',clues={'AB':24,'AC':23,'BD':46},expected_solutions=[{'A':2,'B':4,'C':3,'D':6}]))
    add(t,'Lưới chữ số có hàng trên A,B; hàng dưới C,D. AB, CD đọc ngang; AC, BD đọc dọc, tất cả là số hai chữ số. Bốn manh mối được giữ nguyên: AB = 3 × 4; CD = 9 × 3; AC = 12; BD = 24. Có thể điền một lưới thỏa đồng thời cả bốn manh mối không? Nếu không, chỉ ra chỗ xung đột; không được sửa một manh mối để ép có nghiệm.',['Lưới A B / C D; dùng cùng ô khi đọc ngang/dọc','AB=12; CD=27; AC=12; BD=24'],'Khả năng thỏa đồng thời và chỗ xung đột',[
        step('Lấy chữ số từ hàng trên','Manh mối hàng trên xác định cả A và B.','12','3 × 4 = 12 nên A = 1, B = 2.','3*4',''),
        step('Lấy chữ số từ hàng dưới','Cũng phải giữ đúng hai vị trí C,D của hàng dưới.','27','9 × 3 = 27 nên C = 2, D = 7. Cột AC đọc 12, đúng manh mối thứ ba.','9*3',''),
        step('Đối chiếu cột còn lại','Cột BD dùng B và D đã bị hai hàng xác định.','Không có lưới thỏa cả bốn','BD bắt buộc đọc 27, trái manh mối 24. Không thể đổi D thành 4 vì sẽ làm CD sai 27. Hai hàng đã cố định mọi ô nên không còn cách điền khác để tránh xung đột.')],[('Khả năng','Không có lưới thỏa cả bốn manh mối',''),('Xung đột','BD buộc bằng 27 nhưng manh mối ghi 24','')],hints('Kiểm đồng thời mọi mục trên cùng lưới.','Một mục có thể đúng riêng nhưng xung đột với chữ số do mục khác xác định.','Nếu các ô đã bị cố định, thử xem còn quyền thay ô nào mà không làm sai dữ kiện trước.'),'numeric_crossword_intersections',dict(kind='crossword',clues={'AB':12,'CD':27,'AC':12,'BD':24},expected_solutions=[]))

def bounds_sequences_charts():
    t='directional_estimation_bound'
    add(t,'Không cần tính chính xác tích 51 × 21. Hãy chứng minh tích ấy lớn hơn 1000 bằng một tích nhỏ hơn dễ tính; giải thích vì sao chiều so sánh được giữ khi nhân các số dương.',['Hai thừa số 51,21 đều dương','Cần so với 1000, không bắt buộc tính tích chính xác'],'Kết luận và lập luận bằng cận dưới',[
        step('Chọn tích dễ tính ở phía dưới','Giảm từng thừa số dương làm tích giảm.','1000','50 × 20 = 1000; vì 51 > 50 và 21 > 20 nên 51 × 21 > 50 × 21 > 50 × 20.','50*20',''),
        step('Kết luận và kiểm chiều cận','Tích dùng so đã nhỏ hơn tích thật, không phải số làm tròn thay cho tích thật.','51 × 21 > 1000','Cả hai bước giảm đều dùng thừa số dương nên chiều lớn hơn đúng. Đây là chứng minh qua cận dưới, không cần khẳng định tích thật bằng 1000.')],[('So sánh','51 × 21 > 1000','')],hints('Chọn một tích dễ tính nằm đúng phía cần để kết luận.','Xét điều gì xảy ra khi giảm một thừa số mà thừa số kia vẫn dương.','Kiểm cận tìm được có đủ mạnh để so với đúng mốc đề hỏi không.'),'directional_estimation_bound_proof',dict(kind='product_bound',a=51,b=21,lower_a=50,lower_b=20,threshold=1000,expected_relation='>'))
    add(t,'Bạn viết: 199 < 200 nên 199 : 5 > 200 : 5; do đó 199 : 5 > 40. Giữ câu viết, xét lại chiều so sánh và kết luận đúng giữa 199 : 5 với 40; không cần tính thương dưới dạng thập phân.',['Hai số bị chia 199 và 200','Chia cả hai cho cùng số dương 5'],'So sánh đúng và sửa lý do',[
        step('Kiểm phép chia cùng nhóm dương','Chia hai lượng cho cùng số dương không đảo thứ tự lớn bé.','199 : 5 < 200 : 5','Có thể xét chia đều mỗi lượng vào năm phần: lượng ban đầu nhỏ hơn thì mỗi phần nhỏ hơn. Dấu lớn hơn trong câu bạn viết đã đảo sai.'),
        step('Tính cận trên dễ tính','Thương từ số lớn hơn là cận trên, không phải cận dưới.','40','200 : 5 = 40, nên 199 : 5 < 40. Kiểm 40 × 5 = 200 đã lớn hơn 199. Không cần đổi thương thành thập phân.','200/5','')],[('So sánh','199 : 5 < 40',''),('Nhận xét','Chia cùng số dương giữ chiều so sánh','')],hints('Xác định số chia có cùng nhau và dương hay không.','Phân biệt dùng lượng lớn hơn làm cận trên với dùng lượng nhỏ hơn làm cận dưới.','Thử nhân cận dự kiến với số chia để kiểm chiều.'),'directional_estimation_bound_proof',dict(kind='quotient_bound',a=199,upper=200,divisor=5,threshold=40,expected_relation='<'),student='199 < 200 nên 199 : 5 > 200 : 5; do đó 199 : 5 > 40.')
    t='geometric_sequence_local_extension'
    add(t,'Dãy số lượng thẻ có quy tắc đã cho: mỗi vị trí sau gấp đôi vị trí ngay trước. Vị trí thứ tư có 24 thẻ; các số lượng đều nguyên dương. Tìm số thẻ ở vị trí thứ ba và thứ sáu, rồi kiểm bằng quy tắc. Không cần đoán quy tắc từ một hình vẽ.',['Quy tắc sau = trước ×2','Vị trí 4 có 24 thẻ'],'Số lượng ở vị trí 3 và 6',[
        step('Đi ngược một bước','Nếu sau gấp đôi trước thì trước bằng sau chia hai.','12','24 : 2 = 12 thẻ ở vị trí 3; kiểm 12 × 2 = 24.','24/2','thẻ'),
        step('Đi tới vị trí kế tiếp','Từ vị trí 4 đến vị trí 5 là một lần nhân hai.','48','24 × 2 = 48 thẻ ở vị trí 5; chưa phải vị trí 6.','24*2','thẻ'),
        step('Đi tới đúng vị trí cần tìm','Vị trí 6 cách vị trí 4 hai bước theo quy tắc.','96','48 × 2 = 96 thẻ ở vị trí 6. Kiểm 96 : 2 : 2 = 24 về vị trí 4; vị trí 3 là 12.','48*2','thẻ')],[('Vị trí 3',12,'thẻ'),('Vị trí 6',96,'thẻ')],hints('Quy tắc đã được nêu rõ; giữ số vị trí riêng với số lần áp dụng quy tắc.','Đi ngược dùng thao tác ngược của quy tắc đi tới.','Từ kết quả thử trở lại vị trí mốc qua đúng số bước.'),'geometric_sequence_local_extension',dict(kind='declared_double',known_index=4,known_value=24,requested=[3,6],expected=[12,96]))
    add(t,'Phiếu chỉ ghi ba số đầu 2, 4, 8 và không nêu quy tắc. Bạn nói: Số thứ tư chắc chắn là 16 vì mỗi lần gấp đôi. Giữ câu đó, kiểm từ chắc chắn. Hãy nêu hai quy tắc rõ ràng cùng khớp ba số đã ghi nhưng cho số tiếp khác nhau; rồi hỏi thông tin còn thiếu.',['Chỉ có ba số đầu 2,4,8','Chưa được cho quy tắc sinh dãy'],'Nhận xét tính chắc chắn và thông tin cần bổ sung',[
        step('Nêu một cách tiếp tục có điều kiện','Nhân hai là một quy tắc phù hợp ba số, nhưng cần được đề xác nhận.','16','2 nhân hai là 4, 4 nhân hai là 8, rồi 8 nhân hai là 16. Đó là kết quả nếu giữ quy tắc gấp đôi.','8*2',''),
        step('Kiểm một quy tắc khác cũng khớp','Cùng đoạn đầu có thể thuộc một dãy với luật khác.','Theo nhóm lặp 2,4,8: tiếp theo 2','Lặp nguyên nhóm 2,4,8 cũng cho đúng ba số đầu, nhưng vị trí thứ tư quay lại 2. Không sửa ba số đã cho để tạo ví dụ.'),
        step('Giới hạn kết luận và hỏi luật','Hai luật cùng khớp mà cho hai kết quả khác nhau bác bỏ tính chắc chắn.','Cần biết quy tắc của phiếu','Có thể nói 16 nếu đề xác nhận mỗi lần gấp đôi; khi chưa có luật thì hỏi phiếu dùng quy tắc nào. Không coi một cách đoán hợp lý là đáp số duy nhất.')],[('Kết luận','Chưa xác định duy nhất số thứ tư; cần quy tắc',''),('Hai ví dụ','Gấp đôi cho 16; lặp nhóm 2,4,8 cho 2','')],hints('Phân biệt một quy tắc có thể dùng với quy tắc đã được đề cho.','Thử một luật rõ ràng khác vẫn giữ nguyên các số đã biết.','Nếu hai luật hợp lệ cho kết quả khác nhau, xem cần hỏi thêm điều gì.'),'geometric_sequence_local_extension',dict(kind='sequence_ambiguity',prefix=[2,4,8],continuations=[16,2]),student='Số thứ tư chắc chắn là 16 vì mỗi lần gấp đôi.')
    t='chart_causal_guard'
    add(t,'Bảng bán cây giả định ghi tuần trước 12 chậu, tuần sau 20 chậu. Cửa hàng phát tờ rơi từ đầu tuần sau; chưa có dữ liệu về các yếu tố khác hoặc nhóm so sánh. Bạn viết: Tờ rơi chắc chắn làm bán thêm 8 chậu. Giữ câu ấy; tính mức tăng quan sát được và phân biệt nó với kết luận về nguyên nhân.',['Số bán trước 12, sau 20 chậu','Tờ rơi bắt đầu tuần sau; không có dữ liệu kiểm soát yếu tố khác'],'Mức tăng và mức kết luận có bằng chứng',[
        step('Tính điều bảng thực sự ghi','Lấy lượng sau bớt lượng trước để mô tả chênh lệch quan sát.','8','20 − 12 = 8 chậu nhiều hơn trong bảng. Đây là mức tăng giữa hai tuần, không tự là số do tờ rơi gây ra.','20-12','chậu'),
        step('Kiểm từ chắc chắn về nguyên nhân','Hai biến cùng thay đổi theo thời gian chưa loại được các giải thích khác.','Chưa đủ căn cứ quy toàn bộ mức tăng cho tờ rơi','Tờ rơi có thể là một giả thuyết, nhưng bảng không cho biết những yếu tố khác có giữ nguyên không. Không bịa rằng thời tiết, giá hay khách đã thay đổi.'),
        step('Hỏi loại thông tin cần kiểm thêm','Muốn đánh giá nguyên nhân cần bằng chứng liên quan ngoài hai cột số lượng.','Cần dữ liệu so sánh và điều kiện bán','Có thể hỏi có nhóm/đợt tương tự không phát tờ rơi và các điều kiện bán có khác nhau không. Chưa có dữ liệu ấy thì giữ kết luận ở mức tăng quan sát được.')],[('Mức tăng',8,'chậu'),('Nguyên nhân','Chưa đủ căn cứ kết luận tờ rơi gây toàn bộ mức tăng','')],hints('Tách phép tính chênh lệch trong bảng với câu khẳng định về nguyên nhân.','Xem dữ liệu nào thật sự có và dữ liệu nào chưa được cung cấp.','Không tự bổ sung yếu tố khác đã xảy ra; chỉ nêu bằng chứng cần kiểm thêm.'),'chart_causal_inference_guard',dict(kind='causal',observed=[12,20],difference=8,causal_identified=False),student='Tờ rơi chắc chắn làm bán thêm 8 chậu.')
    add(t,'Trong một ngày, quầy A có buổi giới thiệu sản phẩm và bán 30 hộp; quầy B không có buổi giới thiệu và bán 20 hộp. Hai quầy ở hai địa điểm khác nhau; đề không cho lượng khách, giá hay dữ liệu các ngày trước. Hỏi có thể khẳng định buổi giới thiệu gây ra đúng phần chênh lệch số hộp đã bán không? Tính chênh lệch, nêu một giả thuyết phù hợp và giới hạn của nó.',['A có giới thiệu, bán 30 hộp; B không giới thiệu, bán 20 hộp','Khác địa điểm; các điều kiện so sánh khác chưa được ghi'],'Chênh lệch và giới hạn suy luận nguyên nhân',[
        step('Mô tả chênh lệch đã quan sát','Cả hai dữ kiện đều là số hộp bán trong cùng một ngày.','10','30 − 20 = 10 hộp. Bảng cho phép nói A bán nhiều hơn B 10 hộp.','30-20','hộp'),
        step('Nêu giả thuyết mà không coi là chứng minh','Số bán khác nhau chưa cho biết các điều kiện bán có tương đồng hay không.','Giới thiệu có thể liên quan; chưa xác định tác động đúng 10 hộp','Khác địa điểm và chưa có thông tin điều kiện bán nên chưa thể quy đúng 10 hộp cho buổi giới thiệu. Không khẳng định lượng khách hoặc giá thực tế của quầy nào cao hơn.'),
        step('Kiểm câu kết luận có vượt dữ liệu không','Tách so sánh hai giá trị khỏi nguyên nhân tạo hai giá trị.','Cần so sánh tương đồng hơn hoặc dữ liệu bổ sung','Có thể thu số liệu cùng quầy ở điều kiện tương đồng có/không giới thiệu và ghi những điều kiện liên quan. Với dữ kiện hiện tại chỉ chốt chênh lệch quan sát; giả thuyết chưa phải kết quả thử có kiểm soát.')],[('Chênh lệch',10,'hộp'),('Kết luận','Chưa xác định buổi giới thiệu gây ra đúng 10 hộp chênh lệch','')],hints('So sánh số hộp trước, rồi kiểm riêng câu hỏi về nguyên nhân.','Một điểm khác giữa hai quầy chưa cho biết mọi điểm khác có giữ nguyên không.','Giữ giả thuyết ở mức giả thuyết khi chưa có bằng chứng đối chiếu phù hợp.'),'chart_causal_inference_guard',dict(kind='causal',observed=[20,30],difference=10,causal_identified=False))

def races_cycles():
    t='trial_log_race_state'
    add(t,'Có hai quân Chẵn và Lẻ đều ở vạch 0. Mỗi lượt gieo hai xúc xắc; cộng hai số: tổng chẵn thì chỉ quân Chẵn tiến một ô, tổng lẻ thì chỉ quân Lẻ tiến một ô. Quân nào đầu tiên đến ô 2 thắng và trò chơi dừng ngay; không dùng các lượt ghi sau thời điểm dừng. Nhật ký giả định đủ thứ tự: (1,2), (2,2), (3,4), (6,2). Xác định quân thắng, lượt dừng và vị trí hai quân khi dừng.',['Hai quân từ 0; tổng chẵn/lẻ chọn đúng một quân','Đích ô 2; dừng ngay lần đầu có quân tới đích','Nhật ký (1,2),(2,2),(3,4),(6,2)'],'Quân thắng, lượt dừng và trạng thái cuối',[
        step('Xử lí lượt đầu','Tổng là lẻ nên áp dụng đúng nhánh Lẻ.','3','1 + 2 = 3; quân Lẻ đến ô 1, Chẵn vẫn 0. Chưa ai đạt đích.','1+2',''),
        step('Xử lí lượt hai','Mỗi lượt chỉ tiến quân theo loại tổng vừa gieo.','4','2 + 2 = 4 chẵn; Chẵn đến ô 1, Lẻ vẫn 1.','2+2',''),
        step('Xử lí lượt ba và kiểm đích','Phải kiểm thắng sau từng lượt, trước khi dùng kết quả kế tiếp.','7','3 + 4 = 7 lẻ; Lẻ từ 1 đến 2 nên thắng ở lượt 3. Chẵn vẫn ở ô 1.','3+4',''),
        step('Giữ đúng trạng thái khi dừng','Nhật ký có dữ liệu sau điểm dừng không làm trò chơi tiếp tục.','Lẻ thắng; dừng lượt 3; Lẻ 2, Chẵn 1','Không dùng cặp (6,2). Nếu cộng lượt 4 cho Chẵn sẽ xét trạng thái sau khi trò chơi đã kết thúc, trái yêu cầu.')],[('Quân thắng','Lẻ',''),('Lượt dừng',3,'lượt'),('Vị trí khi dừng','Lẻ: 2; Chẵn: 1','ô')],hints('Áp dụng từng kết quả theo thứ tự và ghi vị trí cả hai quân.','Sau mỗi lượt, đối chiếu điều kiện kết thúc trước khi đọc lượt tiếp.','Kiểm kết quả nào thuộc phần trò chơi đã thực sự diễn ra trước khi dừng.'),'trial_log_race_state',dict(kind='parity_race',rolls=[[1,2],[2,2],[3,4],[6,2]],target=2,expected_winner='Lẻ',expected_stop=3,expected_positions={'Chẵn':1,'Lẻ':2}))
    add(t,'Hai quân mang nhãn Tổng 5 và Tổng 6 cùng ở 0. Mỗi lần gieo hai xúc xắc chuẩn có số từ 1 đến 6: nếu tổng là 5 hoặc 6 thì đúng quân mang nhãn ấy tiến một ô; tổng khác không quân nào tiến. Ai tới ô 2 trước thì thắng và dừng. Nhật ký theo thứ tự là (1,4), (2,?), (1,5), trong đó dấu ? là số đã gieo nhưng chưa chép rõ. Có thể chốt duy nhất quân thắng từ bản ghi này không? Chỉ ra hai cách điền hợp lệ chứng minh nhận xét và hỏi dữ kiện cần bổ sung.',['Đích 2; dừng ngay có quân thắng','Nhật ký có một mặt xúc xắc chưa đọc','Mỗi mặt chưa đọc thuộc 1..6 nhưng không được đoán là kết quả thật'],'Tính duy nhất của kết quả và thông tin còn thiếu',[
        step('Ghi trạng thái biết chắc trước ô thiếu','Cặp đầu có tổng 5, nên chỉ quân Tổng 5 tiến.','Tổng 5 ở 1; Tổng 6 ở 0','Sau lượt đầu chưa ai thắng. Kết quả thiếu của lượt hai có thể làm đổi nhánh và thời điểm dừng.'),
        step('Thử một bản chép có thể có','Số 3 là mặt hợp lệ cho vị trí chưa đọc.','5','Nếu ? = 3 thì 2 + 3 = 5; quân Tổng 5 đến ô 2 và thắng ở lượt 2. Đây chỉ là một khả năng, không nhận đã gieo ra 3.','2+3',''),
        step('Thử một bản chép khác','Số 4 cũng là mặt hợp lệ, giữ nguyên các lượt đã rõ.','6','Nếu ? = 4 thì lượt hai tổng 6, Tổng 6 đến ô 1; lượt ba (1,5) tổng 6 đưa nó đến ô 2 và thắng. Kết quả thắng khác bản trước.','2+4',''),
        step('Hỏi đúng phần thiếu','Hai bản hợp lệ cho người thắng khác nhau nên chưa có kết luận duy nhất.','Cần số mặt chưa đọc của lượt thứ hai','Hỏi mặt xúc xắc thứ hai ở lượt 2 thực tế là số nào, hoặc xin bản chép/ảnh rõ. Không thay nó bằng xác suất, số trung bình hay một trong hai ví dụ vừa thử.')],[('Kết luận','Chưa chốt duy nhất quân thắng; cần số chưa đọc ở lượt 2',''),('Hai khả năng','?=3: Tổng 5 thắng lượt 2; ?=4: Tổng 6 thắng lượt 3','')],hints('Đánh dấu thông tin đã rõ và giữ nguyên ô chưa đọc.','Xem các giá trị hợp lệ khác nhau của ô ấy có làm đổi diễn biến trước điểm dừng không.','Các ví dụ thử không thay thế cho kết quả thật; hỏi đúng phần thiếu để chốt.'),'trial_log_race_state',dict(kind='sum_race_missing',rolls=[[1,4],[2,None],[1,5]],target=2,labels=[5,6],example_completions=[3,4]))
    t='closed_operation_cycle'
    add(t,'Máy số đo bắt đầu ở 3/4 m. Theo đúng vòng một chiều, lần lượt cộng 1/2 m, gấp đôi số đo đang có, rồi bớt 7/4 m và trở lại ô xuất phát. Không có thao tác nào khác. Tính các số đo trung gian và kiểm sau một vòng có đúng về số đo ban đầu không.',['Đầu 3/4 m','Cộng 1/2 m; nhân2; trừ7/4 m'],'Các mốc và kiểm điều kiện khép vòng',[
        step('Cộng phần đầu theo cùng đơn vị','Cả hai số đo đều tính bằng mét nên quy đồng rồi cộng.','5/4','3/4 + 1/2 = 5/4 m.','3/4+1/2','m'),
        step('Nhân số đo hiện có','Gấp đôi áp dụng cho mốc vừa tính, không chỉ cho số ban đầu.','5/2','5/4 × 2 = 5/2 m.','(5/4)*2','m'),
        step('Trừ và kiểm trở lại mốc đầu','Vòng chỉ nhất quán nếu số đo sau thao tác cuối bằng số ở ô xuất phát.','3/4','5/2 − 7/4 = 3/4 m, bằng số ban đầu. Kiểm quy đồng 10/4 − 7/4 = 3/4; vòng này khép đúng.','5/2-7/4','m')],[('Các mốc','5/4; 5/2; 3/4','m'),('Khép vòng','Có, trở lại 3/4 m','')],hints('Dùng kết quả của mỗi mũi tên làm đầu vào cho mũi tên tiếp theo.','Giữ đúng thứ tự thao tác và đơn vị của các số đo.','Ngoài tính mốc cuối, cần so nó với số đã ghi ở ô xuất phát.'),'closed_operation_cycle_consistency',dict(kind='cycle',start='3/4',ops=[['add','1/2'],['mul','2'],['sub','7/4']],expected_values=['5/4','5/2','3/4'],expected_closes=True))
    add(t,'Một vòng máy số đo ghi số xuất phát 2/3 m, rồi cộng 1/6 m, nhân số đo đang có với 3, sau đó trừ 5/3 m để quay về ô xuất phát. Bạn ghi: Sau vòng này lại đúng 2/3 m. Giữ cả các thao tác và câu bạn viết; tính kiểm và nêu vòng có nhất quán với nhãn xuất phát không. Không được đổi một phép hoặc đáp số đã cho để ép khép vòng.',['Đầu 2/3 m; cộng 1/6 m; nhân 3; trừ 5/3 m','Bạn khẳng định về 2/3 m'],'Mốc cuối và nhận xét về khẳng định',[
        step('Cộng theo mũi tên đầu','Quy đồng phần ba thành phần sáu để cộng.','5/6','2/3 + 1/6 = 4/6 + 1/6 = 5/6 m.','2/3+1/6','m'),
        step('Dùng mốc vừa có để nhân','Phép nhân ba áp cho cả số đo hiện tại.','5/2','5/6 × 3 = 15/6 = 5/2 m.','(5/6)*3','m'),
        step('Tìm mốc cuối theo phép trừ đã ghi','Không đổi 5/3 để làm kết quả theo ý muốn.','5/6','5/2 − 5/3 = 15/6 − 10/6 = 5/6 m.','5/2-5/3','m'),
        step('Kiểm nhãn tại chỗ khép vòng','Muốn quay về cùng số đo phải bằng số xuất phát.','1/6','5/6 − 2/3 = 1/6 m, khác không. Do đó khẳng định về đúng 2/3 m sai đối với chuỗi thao tác đã cho; giữ dữ kiện và báo bất nhất.','5/6-2/3','m')],[('Mốc cuối','5/6','m'),('Khép vòng','Không; hơn mốc đầu 1/6 m','')],hints('Kiểm các mũi tên đúng như đã ghi trước khi đối chiếu câu kết luận.','Phần số có mẫu khác nhau cần được quy đồng khi cộng hoặc trừ.','So mốc cuối với mốc đầu bằng một phép kiểm, không sửa dữ kiện để chúng bằng nhau.'),'closed_operation_cycle_consistency',dict(kind='cycle',start='2/3',ops=[['add','1/6'],['mul','3'],['sub','5/3']],expected_values=['5/6','5/2','5/6'],expected_closes=False),student='Sau vòng này lại đúng 2/3 m.')

def calc(expr,typ):
    def f(n):
        if isinstance(n,ast.Constant) and type(n.value) is int:return typ(n.value)
        if isinstance(n,ast.BinOp):
            a,b=f(n.left),f(n.right)
            if isinstance(n.op,ast.Add):return a+b
            if isinstance(n.op,ast.Sub):return a-b
            if isinstance(n.op,ast.Mult):return a*b
            if isinstance(n.op,ast.Div):return a/b
        raise ValueError(expr)
    return f(ast.parse(expr,mode='eval').body)

def oracle(o):
    k=o['kind']
    if k=='shuttle':
        names=tuple(o['weights']);n=len(names);full=(1<<n)-1;start=(0,0);target=(full,1);q=deque([(start,0)]);seen={start};distance=None
        while q:
            (mask,side),d=q.popleft()
            if (mask,side)==target:distance=d;break
            available=[i for i in range(n) if bool(mask>>i&1)==bool(side)]
            for count in range(1,len(available)+1):
                for people in combinations(available,count):
                    if sum(o['weights'][names[i]] for i in people)>o['capacity']:continue
                    newmask=mask
                    for i in people:newmask^=1<<i
                    state=(newmask,1-side)
                    if state not in seen:seen.add(state);q.append((state,d+1))
        assert distance==o['expected_minimum'];return dict(minimum=distance,finite_states_seen=len(seen),state_space_size=2**n*2)
    if k=='crossword':
        sols=[]
        for a,b,c,d in product(range(10),repeat=4):
            if not a or not b or not c:continue
            v={'AB':10*a+b,'CD':10*c+d,'AC':10*a+c,'BD':10*b+d}
            if all(v[name]==number for name,number in o['clues'].items()):sols.append(dict(A=a,B=b,C=c,D=d))
        assert sols==o['expected_solutions'];return sols
    if k=='dial':
        step=Fraction(360,o['sectors']);d=(o['end']-o['start'])%o['sectors'];v=min(d,o['sectors']-d)*step;assert v==o['expected_minor'];return dict(clockwise_steps=d,counterclockwise_steps=o['sectors']-d,minor=str(v))
    if k=='bar_sum_difference':
        found=[(small,large) for small in range(o['total']+1) for large in range(o['total']+1) if small+large==o['total'] and large-small==o['difference']];assert found==[(o['expected_small'],o['expected_large'])];return found
    if k=='bar_ratio_difference':
        found=[(s,o['ratio']*s) for s in range(o['difference']+1) if o['ratio']*s-s==o['difference']];assert found==[(o['expected_small'],o['expected_large'])];return found
    if k=='product_bound':
        assert o['a']>o['lower_a']>0 and o['b']>o['lower_b']>0;assert o['lower_a']*o['lower_b']==o['threshold'];return dict(exact_product=o['a']*o['b'],strict_lower_bound=o['threshold'])
    if k=='quotient_bound':
        assert 0<o['a']<o['upper'] and o['divisor']>0;assert Fraction(o['a'],o['divisor'])<Fraction(o['upper'],o['divisor'])==o['threshold'];return dict(exact_quotient=str(Fraction(o['a'],o['divisor'])),upper=o['threshold'])
    if k=='declared_double':
        out=[Fraction(o['known_value'])*Fraction(2)**(i-o['known_index']) for i in o['requested']];assert out==o['expected'];return [str(x) for x in out]
    if k=='sequence_ambiguity':
        double=[2*2**i for i in range(4)];periodic=([2,4,8]*2)[:4];assert double[:3]==periodic[:3]==o['prefix'];assert [double[3],periodic[3]]==o['continuations'];return dict(double=double,periodic=periodic)
    if k=='causal':
        assert o['observed'][1]-o['observed'][0]==o['difference'] and not o['causal_identified'];return dict(observed_difference=o['difference'],logical_models=['All difference assigned to intervention with other causes constant','Intervention effect zero with other conditions producing same two counts'],same_observations=True,unique_causal_effect=False)
    if k=='parity_race':
        pos={'Chẵn':0,'Lẻ':0};trace=[]
        for turn,pair in enumerate(o['rolls'],1):
            who='Chẵn' if sum(pair)%2==0 else 'Lẻ';pos[who]+=1;trace.append(dict(turn=turn,sum=sum(pair),positions=dict(pos)))
            if pos[who]==o['target']:break
        assert turn==o['expected_stop'] and who==o['expected_winner'] and pos==o['expected_positions'];return trace
    if k=='sum_race_missing':
        results=[]
        for face in range(1,7):
            pos={x:0 for x in o['labels']};winner=None;stop=None
            for turn,pair in enumerate(o['rolls'],1):
                s=sum(face if x is None else x for x in pair)
                if s in pos:pos[s]+=1
                if s in pos and pos[s]>=o['target']:winner=s;stop=turn;break
            results.append(dict(missing_face=face,winner=winner,stop=stop))
        assert next(x for x in results if x['missing_face']==3)['winner']==5
        assert next(x for x in results if x['missing_face']==4)['winner']==6
        return results
    if k=='cycle':
        v=Fraction(o['start']);values=[]
        for op,x in o['ops']:
            x=Fraction(x);v={'add':lambda:v+x,'mul':lambda:v*x,'sub':lambda:v-x}[op]();values.append(str(v))
        assert values==o['expected_values'] and (v==Fraction(o['start']))==o['expected_closes'];return dict(values=values,closes=o['expected_closes'])
    if k=='board_extra':
        p=o['start'];trace=[];actor='An'
        for roll,answer in zip(o['rolls'],o['answers']):
            p+=roll;correct=answer==({3:3+5,4:6-2}[p]);extra=(p==3 and correct);trace.append(dict(position=p,answer_correct=correct,extra=extra))
            if not extra:actor='Bình'
        assert p==o['expected_position'] and actor==o['expected_next'];return trace
    if k=='board_skip':
        actors=['M','N'];idx=0;skip={'M':True,'N':False};pos={'M':1,'N':2};rolls=iter([2,1]);actions=[]
        for _ in range(4):
            who=actors[idx]
            if skip[who]:skip[who]=False;actions.append(who+'_skip')
            else:
                pos[who]+=next(rolls);actions.append(who+'_move')
                if pos[who]==4:skip[who]=True
            idx=1-idx
        assert actions==o['expected_actions'] and pos==o['expected_positions'];return dict(actions=actions,positions=pos,remaining_skip=skip)
    raise ValueError(k)

def main():
    ROWS.clear();game_and_shuttle();bars_dials_crosswords();bounds_sequences_charts();races_cycles()
    assert len(ROWS)==20 and len({r['topic'] for r in ROWS})==10
    prior={};comparison=[]
    for f in ['release/accepted_cases.jsonl','g5_append/draft_cases.jsonl']:
        b=(RUN/f).read_bytes();rs=[json.loads(x) for x in b.splitlines()];prior.update({x['sample_id']:x for x in rs});comparison.append(dict(path=f,sha256=sha(b),rows=len(rs),actual_problem_and_topic_read=True,semantic_overlap='78 release: G1 inequality/order/pattern/resource/card equations,16 G4 numeric forms,3 spatial forms. G5 12: tiered tariff,rotated water,timezone table,cube-net repair. None supplies the ten additional requested state/guard/representation tasks. Nearest full-field comparisons retained in mapping; no global archive absence claim.'))
    OUT.mkdir(exist_ok=True);source=[];chat=[];qa=[];checks=[]
    criteria=['correct_math_or_explicit_guard','givens_request_consistent','grade_scope','initial_and_all_three_hints_answer_free','schema_provenance_unique','steps_reasons_units_check','student_work_grounded_no_unseen_inference']
    for r in ROWS:
        assert r['sample_id'] not in prior
        assert all(r['problem']!=x['problem'] for x in prior.values())
        line=dump(r);h=sha(line.encode());source.append(line)
        cr=dict(sample_id=r['sample_id'],source_row_sha256=h,finite_or_logic_oracle=oracle(r['gap_oracle']),numeric_checks=[])
        for s in r['worked_steps']:
            if not s['expression']:continue
            f=calc(s['expression'],Fraction);assert f==Fraction(s['result'])
            with localcontext() as ctx:
                ctx.prec=90;d=calc(s['expression'],Decimal);expected=Decimal(f.numerator)/Decimal(f.denominator);assert abs(d-expected)<Decimal('1e-80')
            cr['numeric_checks'].append(dict(step_id=s['step_id'],expression=s['expression'],fraction_result=str(f),decimal_result=str(d),status='PASS_WITH_90_DIGIT_CONTEXT_AND_1E80_ABSOLUTE_TOLERANCE'))
        checks.append(cr)
        qa.append(dict(sample_id=r['sample_id'],source_row_sha256=h,criteria={c:'PASS' for c in criteria},review_role='AUTHOR_SELF_QA',status='PASS_AUTHOR_SELF_QA_DRAFT_CROSS_REVIEW_PENDING',basis='All actual authored problem/givens/request/student quote/steps/reasons/explanations/answers/initial guidance/three hints read; finite or logic oracle and Fraction/Decimal arithmetic. Enrichment, not new core; no human attestation.'))
        for c in chat_records(r):
            c.update(acceptance_status=r['acceptance_status'],quality_status=r['quality_status'],source_row_sha256=h,human_verified=False,teacher_certified=False);chat.append(dump(c))
    outputs={'cases.jsonl':'\n'.join(source)+'\n','chat.jsonl':'\n'.join(chat)+'\n','self_qa.jsonl':'\n'.join(dump(x) for x in qa)+'\n','oracle_checks.jsonl':'\n'.join(dump(x) for x in checks)+'\n','preauthoring_comparison.json':json.dumps(comparison,ensure_ascii=False,indent=2)+'\n'}
    for name,value in outputs.items():(OUT/name).write_text(value,encoding='utf-8',newline='\n')
    files={name:dict(bytes=len((OUT/name).read_bytes()),sha256=sha((OUT/name).read_bytes())) for name in outputs}
    manifest=dict(case_count=20,chat_count=80,form_count=10,status='DRAFT_AWAITING_CONTENT_CROSS_REVIEW',new_core_slots=0,trained=False,drive_mutated=False,files=files)
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(dump(manifest))

if __name__=='__main__':main()
