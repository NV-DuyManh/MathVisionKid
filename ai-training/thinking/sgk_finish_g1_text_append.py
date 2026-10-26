"""Ten bounded original G1 text drafts from a saved six-master mapping snapshot.
Calendar authoring cancelled by root because actual old sources cover it.
No network/training/old-source mutation. G2 outputs are read-only comparators.
"""
from pathlib import Path
from fractions import Fraction
from decimal import Decimal
from itertools import permutations
from collections import Counter
import json,hashlib,ast,re
from exhaustive_primary_math import chat_records,expression_group
HERE=Path(__file__).parent
OUT=HERE/'cloud_publication/sgk_finish_20261020/g1_text_append'
OLD=HERE/'cloud_publication/sgk_page_audit_20261019'
SNAP=OUT/'mapping_snapshot.json'
snapshot=json.loads(SNAP.read_text('utf-8'))
assert snapshot['source_sha256']=='bb9a183aa49544a534238ad6742cf0f6c2941e4a3761a77f11ffb94510c08cdc'
MASTERS={m['master_id']:m for m in snapshot['masters']}
FIELDS=['problem','givens','requested_quantity','student_work','initial_guidance','hints','worked_steps','expected_answer']
def dump(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha(b):return hashlib.sha256(b).hexdigest()
def s(title,reason,result,explanation,expression=None,unit=''):
 return dict(title=title,reason=reason,result=str(result),explanation=explanation,expression=expression,unit=unit)
def hs(a,b,c):return [dict(level=i+1,hint=h,question=q) for i,(h,q) in enumerate(zip([a,b,c],['Em cần giữ những dữ kiện nào?','Em thực hiện theo luật đã cho ra sao?','Em kiểm đủ điều kiện thế nào?']))]
ROWS=[]
def add(master,branch,problem,givens,request,steps,answers,hints,model,decision,student=None):
 ev=MASTERS[master];assert master!='calendar_anchor_day_offset'
 sid='sgk_finish_g1_20261020_'+branch
 ROWS.append(dict(sample_id=sid,case_group_id=sid+'_group',grade=1,topic=branch,split='train',case_kind='observable_student_error' if student else 'original_finite_reasoning',problem=problem,givens=[dict(id=f'g{i}',text=g,value=None,unit='',role='explicit_original_given') for i,g in enumerate(givens)],requested_quantity=request,student_work=dict(text=student,observations=[dict(excerpt=student,claim_scope='Only this synthetic written work; no hidden thinking or unseen image inferred.')]) if student else None,can_solve=True,initial_guidance=[hints[0]['hint']],hints=hints,worked_steps=[dict(step_id=f's{i}',**st) for i,st in enumerate(steps)],expected_answer=[dict(quantity=q,result=str(v),unit=u) for q,v,u in answers],canonical_signatures=sorted({expression_group(st['expression']) for st in steps if st['expression']}),independent_model=model,pedagogical_review_decision=decision,acceptance_status='DRAFT_AWAITING_ROOT_CONTENT_QA',quality_status='AUTHOR_SELF_QA_COMPLETE_PENDING_ROOT_QA',human_verified=False,teacher_certified=False,owner_human_reviewed=False,source_role='AI_GENERATED',provenance=dict(authorship_origin='ORIGINAL_AI_TEACHER_AUTHORING',human_content_review_completed=False,book_exercise_copied=False,actual_physical_or_image_result_claimed=False,acceptance_basis='OWNER_PREAUTHORIZED_PROCESS_ROOT_QA_PENDING'),curriculum_assignment=dict(grade=1,enrichment=True,number_limit=100,book='Kết nối tri thức với cuộc sống',modality='EXPLICIT_ORIGINAL_TEXT_ONLY'),coverage=dict(mode='FINITE_SUPPLEMENTARY_APPEND_NOT_CORE',finite_master_id=master,new_core_slots_claimed=0,branch=branch,numbers_only_variant=False,visual_physical_coverage_claimed=False),nearest_source_comparison=dict(mapping_snapshot_file=str(SNAP.relative_to(HERE)),mapping_snapshot_sha256=sha(SNAP.read_bytes()),original_resume_queue_sha256=snapshot['source_sha256'],actual_page_receipts=ev['actual_page_receipts'],nearest_refs=ev['nearest_refs'],semantic_difference=ev['reasons'])))

def author():
 m='attribute_filter_then_extremum'
 add(m,'attribute_tied_maximum','Bảng thẻ ghi rõ: A là hình tròn đỏ mang số 18; B là hình tròn đỏ mang số 18; C là hình tròn đỏ mang số 12; D là hình vuông đỏ mang số 30; E là hình tròn xanh mang số 25. Chỉ xét các thẻ vừa tròn vừa đỏ. Ghi mọi thẻ mang số lớn nhất trong nhóm đó. Hai thẻ khác nhau vẫn phải giữ dù cùng số.',['A tròn đỏ18;B tròn đỏ18;C tròn đỏ12;D vuông đỏ30;E tròn xanh25','Lọc cả tròn và đỏ rồi lấy mọi thẻ lớn nhất'],'Mọi nhãn đạt lớn nhất sau lọc',[
 s('Lọc cả hai thuộc tính','Một thẻ chỉ đạt khi vừa tròn vừa đỏ.','A, B, C','D không tròn; E không đỏ nên không được đưa vào nhóm so số.'),s('Tìm giá trị lớn nhất','Trong nhóm đã lọc mười tám lớn hơn mười hai.','Giá trị lớn nhất 18','A và B cùng mang giá trị ấy, C nhỏ hơn.'),s('Kiểm các nhãn bằng nhau','Đề yêu cầu mọi thẻ đạt cực trị, không chỉ một giá trị.','A và B','Giữ đủ cả hai nhãn, không chọn D vì ba mươi nằm ngoài nhóm đủ thuộc tính.')],[('Thẻ lớn nhất','A và B','')],hs('Lọc đủ các thuộc tính trước khi so số.','Giữ nhãn thẻ đi cùng số sau khi lọc.','Nếu nhiều thẻ cùng đạt cực trị, kiểm đã giữ đủ nhãn chưa.'),dict(kind='attribute',items={'A':[18,True,True],'B':[18,True,True],'C':[12,True,True],'D':[30,False,True],'E':[25,True,False]},expected_eligible=['A','B','C'],expected_max=['A','B']),'Compared G2 regions_intersection_extrema: ordinary filter+max is shared; this branch adds all tied identity extrema, absent from the G2 unique-extremum case.')
 add(m,'attribute_empty_subset','Có thẻ P là hình vuông vàng mang 8; Q là hình tròn xanh mang 15; R là hình tam giác vàng mang 20. Chỉ chọn thẻ vừa tròn vừa vàng rồi tìm thẻ có số bé nhất trong nhóm chọn. Bạn viết “P bé nhất vì 8 nhỏ nhất”. Kiểm câu viết và nêu có thẻ nào đáp ứng yêu cầu không.',['P vuông vàng8;Q tròn xanh15;R tam giác vàng20','Cần cả tròn và vàng trước khi lấy nhỏ nhất'],'Kết luận về nhóm rỗng',[
 s('Kiểm từng thẻ theo hai điều kiện','Đạt một thuộc tính chưa đủ.','Không thẻ nào vừa tròn vừa vàng','P và R vàng nhưng không tròn; Q tròn nhưng không vàng.'),s('Đánh giá câu viết','P mang số nhỏ nhất toàn bảng nhưng không thuộc nhóm được hỏi.','Không chọn P','Chỉ nhận xét câu đã viết, không suy học sinh đã quan sát ảnh như thế nào.'),s('Kiểm có thể lấy cực trị không','Không có phần tử trong nhóm nên không có thẻ bé nhất của nhóm.','Không có thẻ đáp ứng','Không thay màu hay hình của thẻ và không gọi số không là đáp số nhỏ nhất.')],[('Kết luận','Không có thẻ vừa tròn vừa vàng; không có thẻ bé nhất trong nhóm','')],hs('Kiểm xem nhóm đủ điều kiện có thẻ nào trước.','Một số nhỏ toàn bảng chưa chắc thuộc nhóm được hỏi.','Khi không có thẻ đạt, giữ đúng kết luận thay vì chọn từ ngoài nhóm.'),dict(kind='attribute',items={'P':[8,False,True],'Q':[15,True,False],'R':[20,False,True]},expected_eligible=[],expected_max=[]),'New empty-subset guard: no maximum/minimum answer fabricated, unlike G2 nonempty overlap examples.',student='P bé nhất vì 8 nhỏ nhất.')
 m='repeated_value_identity_assignment'
 add(m,'identity_equal_and_lower','Ba bạn An, Bình, Chi có ba điểm được ghi trên ba phiếu: 7, 7, 9; mỗi bạn nhận đúng một phiếu, dùng hết phiếu. Biết An và Bình bằng điểm nhau, Chi nhiều điểm hơn An. Tìm điểm từng bạn và kiểm có bỏ mất phiếu nào không.',['Điểm multiset7,7,9;An=Bình;Chi>An','Mỗi bạn một phiếu,dùng hết'],'Điểm gắn với từng danh tính',[
 s('Dùng điều kiện bằng nhau','Cần hai phiếu có cùng giá trị cho hai bạn bằng điểm.','An và Bình đều 7 điểm','Chỉ giá trị bảy lặp hai lần; chín chỉ có một phiếu.'),s('Gắn phiếu còn lại','Sau khi hai bạn nhận hai phiếu bảy, chỉ còn phiếu chín.','Chi 9 điểm','Chín nhiều hơn bảy nên đáp ứng thêm điều kiện Chi hơn An.'),s('Kiểm đa tập và danh tính','Hai phiếu cùng giá trị vẫn là hai phiếu dành cho hai người.','An7; Bình7; Chi9','Đã dùng đúng bảy,bảy,chín một lần mỗi phiếu; không nhầm sắp dãy với xác định người nhận.')],[('Điểm','An 7; Bình 7; Chi 9','điểm')],hs('Tìm giá trị có đủ số phiếu để các bạn bằng điểm.','Gắn điểm với đúng tên theo quan hệ của đề.','Kiểm số lần xuất hiện mỗi điểm cùng điều kiện hơn và bằng.'),dict(kind='identity',values=[7,7,9],names=['An','Bình','Chi'],predicate='AeqB_Clarger',expected=[[7,7,9]]),'Distinct from G2 cards_repeated_value_inventory: equality/strict-order constraints between people rather than additive equations between arithmetic slots; no digit-card construction.')
 add(m,'identity_not_unique','Ba bạn Mai, Nam, Hà nhận ba phiếu điểm 6, 8, 8, mỗi bạn đúng một phiếu và dùng hết. Chỉ biết Mai không ít điểm hơn Hà; chưa có điều kiện nào khác về Nam. Có xác định duy nhất điểm từng bạn không? Liệt kê các cách phân điểm phù hợp, không tự thêm điều kiện Mai phải hơn Hà.',['Đa tập6,8,8;Mai không ít hơn Hà','Không ít hơn có tính bằng;không điều kiện khác về Nam'],'Các cách và tính duy nhất',[
 s('Xét Hà nhận điểm thấp','Nếu Hà nhận sáu thì hai phiếu còn lại đều tám.','Mai8; Nam8; Hà6','Mai tám không ít hơn Hà sáu, nên đây là một cách hợp lệ.'),s('Xét Hà nhận điểm cao','Nếu Hà nhận tám thì Mai không được nhận sáu.','Mai8; Nam6; Hà8','Mai và Hà bằng tám vẫn đạt không ít hơn; phiếu sáu dành cho Nam. Không có luật cấm Nam ít điểm hơn Hà.'),s('Kiểm hết và giới hạn kết luận','Hà chỉ có thể nhận sáu hoặc tám và cả hai đã xét.','Có hai cách, chưa xác định duy nhất','Hai phiếu tám đổi danh tính vật lý không tạo cách điểm mới. Hai cách trên khác điểm của Nam và Hà; cần thêm thông tin liên quan nếu muốn chốt một cách.')],[('Các cách điểm','Mai8, Nam8, Hà6; hoặc Mai8, Nam6, Hà8','điểm'),('Tính duy nhất','Chưa xác định duy nhất','')],hs('Xét từng giá trị mà người làm mốc có thể nhận.','Giữ nghĩa không ít hơn gồm cả bằng nhau.','Phân biệt đổi hai phiếu cùng số với đổi điểm của một người.'),dict(kind='identity',values=[6,8,8],names=['Mai','Nam','Hà'],predicate='AgeC',expected=[[8,6,8],[8,8,6]]),'Branch uses weak-order constraint with two feasible score assignments and honest ambiguity, unlike unique equality assignment or G2 arithmetic-card equations. Duplicate card identity swaps do not count as distinct score assignments.')
 m='pair_relation_stage_path'
 add(m,'pair_gate_unique','Đường chữ chỉ có mũi tên S→A, S→B, A→C, B→D, C→T, D→T. A ghi 3, B ghi 6, C ghi 7, D ghi 5. Muốn đến T phải qua đúng một cổng đầu A/B rồi một cổng sau C/D; tổng hai số cổng phải bằng 10. Tìm đường đúng và kiểm cả mũi tên lẫn tổng.',['S-A-C-T hoặcS-B-D-T theo mũi tên đã cho','A3,B6,C7,D5;tổng hai cổng10'],'Đường với quan hệ cặp cổng',[
 s('Liệt kê cặp có nối','Chỉ ghép cổng đầu với cổng sau nếu có mũi tên.','A,C hoặc B,D','Không ghép A với D hay B với C vì không có mũi tên đó.'),s('Tính tổng của từng cặp nối','Luật áp vào hai nhãn cùng đường, không kiểm từng nhãn riêng.',10,'A,C cho ba cộng bảy bằng mười; B,D cho sáu cộng năm bằng mười một.','3+7'),s('Kiểm cả tuyến', 'Đường đúng cần qua cặp đạt tổng và nối đủ S tới T.','S → A → C → T','Ba mũi tên đều có. Cặp còn lại không đạt tổng nên không còn đường hợp lệ khác.')],[('Đường','S → A → C → T','')],hs('Liệt kê cặp cổng thật sự được nối qua hai tầng.','Áp dụng quan hệ cho cả cặp thay vì từng số riêng.','Kiểm lại tất cả mũi tên và tổng của cặp được chọn.'),dict(kind='pairgate',edges=[['S','A'],['S','B'],['A','C'],['B','D'],['C','T'],['D','T']],values={'A':3,'B':6,'C':7,'D':5},target=10,expected=[['S','A','C','T']]),'Distinct from G2 prescribed_result_sequence: joint sum relation, not separate per-position results; route collection sum G2 is accumulated after route choice, not two-stage eligibility.')
 add(m,'pair_gate_disconnected_sum','Chỉ có mũi tên S→P, S→Q, P→R, Q→U, R→T, U→T. P ghi 2, Q ghi 5, R ghi 5, U ghi 8. Qua một cổng đầu rồi một cổng sau, tổng hai số phải bằng 10. Bạn chọn S→P→U→T vì 2+8=10. Kiểm đường và cho biết có đường hợp lệ nào không.',['Mũi tên đầy đủ;P2,Q5,R5,U8','Tổng10;phải đi theo nối'],'Kiểm cặp đạt tổng nhưng không nối',[
 s('Kiểm đúng câu đã viết','Tổng đúng không tạo ra mũi tên mới.','P → U không có','Câu viết bị loại ở nối P tới U, dù hai cộng tám bằng mười.'),s('Tính hai cặp thật sự nối','Chỉ P,R và Q,U xuất hiện trên đường đi.',7,'P,R cho hai cộng năm bằng bảy; Q,U cho năm cộng tám bằng mười ba.','2+5'),s('Kiểm hết và kết luận','Mỗi nhánh đã được xét đủ cả tổng và mũi tên.','Không có đường thỏa','Cặp Q,R cũng có tổng mười nhưng không có nối Q→R. Không vẽ thêm đường để giữ đáp số học sinh.')],[('Kết luận','Đường viết sai nối; không có đường thỏa','')],hs('Đối chiếu từng bước đường viết với mũi tên có thật.','Kiểm tổng trên các cặp được nối, không ghép tùy ý.','Một cặp đạt tổng nhưng không nối có thể dùng được không?'),dict(kind='pairgate',edges=[['S','P'],['S','Q'],['P','R'],['Q','U'],['R','T'],['U','T']],values={'P':2,'Q':5,'R':5,'U':8},target=10,expected=[]),'Branch jointly requires adjacency and pair sum; full enumeration certifies no path. Feedback grounded in supplied path.',student='S→P→U→T vì 2+8=10.')
 m='ordered_itinerary_weekday_map'
 add(m,'itinerary_week_rollover','Trong chuyến đi giả định, mỗi ngày ghé đúng một nơi theo thứ tự: vườn hoa, bảo tàng, thư viện, hồ cá. Ghé vườn hoa vào thứ Sáu; ngày sau ghé nơi kế tiếp, đi cả cuối tuần, không nghỉ ngày nào. Ghé thư viện và hồ cá vào những thứ nào?',['Thứ tự4 nơi;vườnhoa thứSáu;1nơi/ngày;không nghỉ'],'Thứ của hai chặng cuối',[
 s('Gắn nơi đầu với ngày bắt đầu','Điểm đầu tính ngay ngày bắt đầu, chưa phải ngày sau.','Vườn hoa thứ Sáu; bảo tàng thứ Bảy','Mỗi chuyển sang nơi kế tiếp tương ứng tiến một ngày.'),s('Tiếp tục qua cuối tuần','Sau thứ Bảy là Chủ nhật, sau Chủ nhật là thứ Hai.','Thư viện Chủ nhật; hồ cá thứ Hai','Không bỏ qua cuối tuần vì đề nói đi cả cuối tuần.'),s('Kiểm thứ tự và số ngày chuyển','Bốn nơi liên tiếp có ba lần chuyển ngày.',3,'Từ thứ Sáu qua thứ Bảy, Chủ nhật tới thứ Hai đúng ba lần; đã gắn từng nơi một lần.','4-1','lần chuyển')],[('Thư viện','Chủ nhật',''),('Hồ cá','Thứ Hai','')],hs('Gắn nơi đầu với chính ngày xuất phát.','Mỗi nơi kế ứng với ngày liền sau theo vòng tuần.','Kiểm cả cuối tuần và số lần chuyển giữa các nơi.'),dict(kind='itinerary',stops=['vườn hoa','bảo tàng','thư viện','hồ cá'],anchor_index=0,anchor_weekday=4,expected=[4,5,6,0]),'Maps ordered stops to successive days with explicit no-rest rule and rollover, not a static calendar lookup.')
 add(m,'itinerary_back_from_last','Một chuyến đi có ba nơi theo đúng thứ tự nhà hát, công viên, trại cây. Mỗi ngày ghé một nơi, ba ngày liên tiếp không nghỉ. Trại cây được ghé vào thứ Hai. Bạn viết “nhà hát cũng thứ Hai vì chuyến đi có thứ Hai”. Tìm thứ của nhà hát và công viên rồi kiểm câu viết.',['Thứ tự nhàhát,côngviên,trạicây;1nơi/ngày liên tiếp','Nơi cuối thứHai;không nghỉ'],'Suy ngày chặng đầu từ chặng cuối',[
 s('Đi lùi theo đúng thứ tự','Nơi ngay trước trại cây phải ở ngày liền trước thứ Hai.','Công viên Chủ nhật','Không gán ngày của nơi cuối cho mọi nơi trong chuyến đi.'),s('Lùi thêm một ngày','Nhà hát ở trước công viên một chặng.','Nhà hát thứ Bảy','Ngày liền trước Chủ nhật là thứ Bảy; có hai lần chuyển giữa ba nơi.'),s('Kiểm xuôi và phản hồi','Đọc từ đầu tới cuối phải khôi phục ngày chặng cuối.','Thứ Bảy → Chủ nhật → thứ Hai','Câu nhà hát cũng thứ Hai sai vì nhà hát nằm trước trại cây hai ngày, không cùng ngày.')],[('Nhà hát','Thứ Bảy',''),('Công viên','Chủ nhật','')],hs('Dùng ngày của nơi đã biết làm mốc, giữ thứ tự các nơi.','Nếu nơi hỏi đứng trước mốc, đi lùi từng ngày.','Đọc lại xuôi để kiểm ngày nơi cuối.'),dict(kind='itinerary',stops=['nhà hát','công viên','trại cây'],anchor_index=2,anchor_weekday=0,expected=[5,6,0]),'Inverse stop/day mapping with explicit supplied anchor, not guessing current weekday; feedback exact supplied statement.',student='Nhà hát cũng thứ Hai vì chuyến đi có thứ Hai.')
 m='repeated_digit_symbol_predicate'
 add(m,'two_digit_matching_symbols','Các thẻ ghi 11, 12, 22, 20, 33, 30, mỗi thẻ ghi một số đầy đủ. Chọn mọi số có hai chữ số mà chữ số hàng chục giống chữ số hàng đơn vị. Nêu vì sao mỗi thẻ còn lại không đạt.',['Thẻ11,12,22,20,33,30','Sốhai chữsố;hai kýhiệu chữsố giốngnhau'],'Các thẻ thỏa chữ số giống nhau',[
 s('So hai chữ số của từng thẻ','Luật hỏi hai ký hiệu tại hai hàng, không hỏi có bằng số thẻ khác không.','11, 22, 33 đạt','Một-một, hai-hai, ba-ba giống nhau theo từng thẻ.'),s('Kiểm thẻ loại','Cả hai hàng phải cùng một ký hiệu.','12, 20, 30 không đạt','Trong mười hai chữ số một khác hai; trong hai mươi và ba mươi, chữ số đầu khác không ở cuối.'),s('Kiểm đầy đủ','Mỗi thẻ cần được kiểm đúng một lần.','Chọn 11, 22, 33','Sáu thẻ đều đã được xét; không chọn theo thứ tự hay độ lớn của số.')],[('Thẻ chọn','11, 22, 33','')],hs('Đọc riêng chữ số hàng chục và hàng đơn vị trên từng thẻ.','So hai ký hiệu trong cùng một số.','Kiểm đủ cả các thẻ chọn và các thẻ bị loại.'),dict(kind='digits',numbers=[11,12,22,20,33,30],expected=[11,22,33]),'Equality of two digit symbols across supplied finite numbers, not fixed-value digit filter; no algebra required.')
 add(m,'digit_length_guard','Có các thẻ số 0, 10, 44, 55, 100, không viết thêm chữ số 0 ở đầu. Chỉ chọn số có đúng hai chữ số và hai chữ số ấy giống nhau. Bạn chọn cả 0, 44, 55, 100 vì nói “0 và 100 cũng có chữ số lặp”. Kiểm và sửa danh sách, giữ cách viết trên thẻ.',['Thẻ0,10,44,55,100;không thêm0đầu','Đúng2chữsố vàhai chữsố giốngnhau'],'Danh sách sửa có kiểm số chữ số',[
 s('Kiểm độ dài trước','Phải có đúng hai chữ số đang viết trên thẻ.','Chỉ xét tiếp 10, 44, 55','Không có hai chữ số ở thẻ không; một trăm có ba chữ số. Không tự viết 0 thành 00.'),s('Kiểm sự giống nhau trong nhóm còn','Số mười có hai chữ số khác nhau.','44 và 55','Hai thẻ bốn-bốn và năm-năm thỏa; mười bị loại.'),s('Phản hồi câu viết và kiểm','Có ký hiệu lặp trong một số chưa đủ nếu sai điều kiện đúng hai chữ số.','Danh sách đúng: 44, 55','Một trăm có hai chữ số không nhưng tổng ba chữ số nên không đạt. Đã giữ nguyên cách viết mọi thẻ.')],[('Danh sách sửa','44, 55','')],hs('Đếm số chữ số đang được viết, không tự thêm ký hiệu.','Sau khi đủ độ dài, mới kiểm chữ số có giống nhau không.','Cần thỏa cả hai điều kiện trên cùng thẻ.'),dict(kind='digits',numbers=[0,10,44,55,100],expected=[44,55]),'Length guard distinguishes single digit, three-digit 100 and no implicit leading zeros; feedback tied to stated mistaken list.',student='Chọn 0, 44, 55, 100 vì 0 và 100 cũng có chữ số lặp.')

def evalexpr(expr,typ):
 def w(n):
  if isinstance(n,ast.Constant) and type(n.value) is int:return typ(n.value)
  if isinstance(n,ast.BinOp):
   a,b=w(n.left),w(n.right)
   if isinstance(n.op,ast.Add):return a+b
   if isinstance(n.op,ast.Sub):return a-b
   if isinstance(n.op,ast.Mult):return a*b
   if isinstance(n.op,ast.Div):return a/b
  raise ValueError(expr)
 return w(ast.parse(expr,mode='eval').body)
def finite_oracle(m):
 k=m['kind']
 if k=='attribute':
  eligible=[n for n,(v,a,b) in m['items'].items() if a and b];maxes=[n for n in eligible if m['items'][n][0]==max(m['items'][x][0] for x in eligible)] if eligible else [];assert eligible==m['expected_eligible'] and maxes==m['expected_max'];return dict(eligible=eligible,all_max_labels=maxes,empty=not eligible)
 if k=='identity':
  candidates=sorted(set(permutations(m['values'])));solutions=[]
  for a,b,c in candidates:
   if ((a==b and c>a) if m['predicate']=='AeqB_Clarger' else (a>=c)):solutions.append([a,b,c])
  assert solutions==m['expected'];return dict(all_distinct_score_assignments=[list(x) for x in candidates],solutions=solutions,distinct_value_solution_count=len(solutions))
 if k=='pairgate':
  routes=[]
  for a,b in m['edges']:
   if a!='S':continue
   for c,d in m['edges']:
    if c==b and [d,'T'] in m['edges']:routes.append(['S',b,d,'T'])
  totals=[dict(route=p,total=m['values'][p[1]]+m['values'][p[2]]) for p in routes];valid=[r['route'] for r in totals if r['total']==m['target']];assert valid==m['expected'];return dict(all_connected_stage_routes=totals,valid=valid)
 if k=='itinerary':
  cycle=['Thứ Hai','Thứ Ba','Thứ Tư','Thứ Năm','Thứ Sáu','Thứ Bảy','Chủ nhật'];weekdays=[]
  for i in range(len(m['stops'])):
   day=m['anchor_weekday'];offset=i-m['anchor_index']
   while offset>0:day=0 if day==6 else day+1;offset-=1
   while offset<0:day=6 if day==0 else day-1;offset+=1
   weekdays.append(day)
  assert weekdays==m['expected'];return dict(stop_day_pairs=[[p,cycle[d]] for p,d in zip(m['stops'],weekdays)],start_anchor_counted_as_its_stop=True)
 if k=='digits':
  # Character inspection independent of numeric place-value arithmetic.
  tests=[dict(number=n,written=str(n),length=len(str(n)),same_symbols=len(set(str(n)))==1) for n in m['numbers']];selected=[x['number'] for x in tests if x['length']==2 and x['same_symbols']];assert selected==m['expected'];return dict(tests=tests,selected=selected)
 raise ValueError(k)

def main():
 author();assert len(ROWS)==10
 counts=Counter(r['coverage']['finite_master_id'] for r in ROWS);assert len(counts)==5 and set(counts.values())=={2}
 # Revalidate the saved actual source bytes; no dependency on mutable live queue.
 reviews_old=[json.loads(b) for b in (OUT/'nearest_actual_full_field_review.jsonl').read_bytes().splitlines()]
 for rec in reviews_old:
  r=rec['receipt'];b=(OLD/r['source_file']).read_bytes().splitlines()[r['line']-1];assert sha(b)==r['sha256'];x=json.loads(b);assert rec['actual_fields']=={f:x.get(f) for f in FIELDS}
 numeric=[];oracles=[]
 for r in ROWS:
  for st in r['worked_steps']:
   assert st['reason'] and st['explanation'] and 'unit' in st
   if st['expression']:
    f=evalexpr(st['expression'],Fraction);d=evalexpr(st['expression'],Decimal);assert f==Fraction(st['result']) and d==Decimal(st['result']);numeric.append(dict(sample_id=r['sample_id'],step_id=st['step_id'],expression=st['expression'],Fraction=str(f),Decimal=str(d)))
  assert not any(re.search(r'[0-9=]',h['hint']+h['question']) for h in r['hints'])
  oracles.append(dict(sample_id=r['sample_id'],family=r['coverage']['finite_master_id'],model=r['independent_model'],oracle=finite_oracle(r['independent_model']),passed=True,independent_of_worked_expression_evaluator=True))
 def write(name,rows):
  b=('\n'.join(dump(r) for r in rows)+'\n').encode();(OUT/name).write_bytes(b);return dict(path=name,bytes=len(b),rows=len(rows),sha256=sha(b))
 manifest=[write('cases.jsonl',ROWS)]
 lines=(OUT/'cases.jsonl').read_bytes().splitlines();selfqa=[];chats=[]
 for row,b in zip(ROWS,lines):
  h=sha(b)
  for c in chat_records(row):c.update(acceptance_status=row['acceptance_status'],quality_status=row['quality_status'],source_row_sha256=h);chats.append(c)
  criteria=[dict(criterion=n,passed=True,evidence=e) for n,e in [
   ('problem_givens_request_consistency','Actual full fields included; complete explicit original finite data.'),('mathematical_correctness','Every expression Fraction/Decimal checked; distinct finite family oracle executed.'),('reasons_units_checks','Every step has reason/explanation/unit; final step checks all relation constraints.'),('initial_and_three_hints_answer_free','Actual initial and all three hint/question strings reviewed; no final labels/results supplied.'),('student_work_grounding','Only actual synthetic written work discussed; no imagined image, private thought or physical result.'),('originality_grade_and_semantic_difference',row['pedagogical_review_decision']),('provenance_finite_and_acceptance','Draft pending root QA; grade1 finite enrichment <=100; no human/external attestation claimed.')]]
  selfqa.append(dict(sample_id=row['sample_id'],source_file='cases.jsonl',source_row_sha256=h,hash_basis='Exact UTF-8 row excluding line terminator',actual_fields={f:row[f] for f in FIELDS},criteria=criteria,pedagogical_decision=row['pedagogical_review_decision'],reviewer='g1_text_author_actual_full_field_review',human_review_claimed=False,root_cross_review_status='PENDING'))
 manifest += [write('chat.jsonl',chats),write('selfqa7.jsonl',selfqa),write('independent_oracles.jsonl',oracles),write('numeric_fraction_decimal.jsonl',numeric)]
 for name in ['mapping_snapshot.json','nearest_actual_full_field_review.jsonl']:
  b=(OUT/name).read_bytes();manifest.append(dict(path=name,bytes=len(b),sha256=sha(b),rows=len(b.splitlines()) if name.endswith('jsonl') else None))
 g2path=HERE/'cloud_publication/sgk_finish_20261020/g2_append/cases.jsonl'
 g2=[json.loads(b) for b in g2path.read_bytes().splitlines()]
 compareids=['regions_intersection_extrema','cards_repeated_value_inventory','sequence_graph_labels','sequence_graph_calculations','route_dead_end_sum']
 comparisons=[]
 for x in g2:
  if x['topic'] in compareids:
   comparisons.append(dict(sample_id=x['sample_id'],source_file=str(g2path.relative_to(HERE)),source_row_sha256=next(sha(b) for b in g2path.read_bytes().splitlines() if json.loads(b)['sample_id']==x['sample_id']),actual_fields={f:x[f] for f in FIELDS}))
 manifest.append(write('g2_readonly_overlap_comparisons.jsonl',comparisons))
 assert len(chats)==40
 oldq={json.loads(b)['problem'] for f in ['current_sources.jsonl','release/accepted_cases.jsonl'] for b in (OLD/f).read_bytes().splitlines()};assert not any(r['problem'] in oldq for r in ROWS)
 cancellation=dict(master_id='calendar_anchor_day_offset',status='CANCELLED_NO_AUTHORING',basis='Root direct message: old g3_calendar_occurrences_schedule + calendar_month_boundary cover offset; no replacement rows.')
 summary=dict(status='10_DRAFTS_AUTHOR_QA_PASS_ROOT_QA_PENDING',cases=len(ROWS),chat=len(chats),master_counts=dict(counts),numeric_steps=len(numeric),finite_oracles=len(oracles),mapping_original_sha256=snapshot['source_sha256'],manifest=manifest,cancelled=[cancellation],crossgrade_reconciliation=[dict(master='attribute_filter_then_extremum',status='BASE_FORM_SHARED_WITH_G2; NEW_TIE_AND_EMPTY_BRANCHES_ONLY',rationale='G2 nonempty region intersection max/min has unique extrema. These branches preserve all tied identities and reject empty subset extrema.'),dict(master='repeated_value_identity_assignment',status='DISTINCT_PREDICATE_FROM_G2_ARITHMETIC_CARDS',rationale='G1 equality/order score constraints between named recipients; G2 arithmetic slot sum/difference constraints. No duplicated additive equations or card layout.')],pending=['Root full-field cross-review/acceptance of these10 drafts','Calendar no longer pending authoring; mapper owns queue closure','Other masters outside these six remain owned by root; no global completion claim'],limitations=['Text-only finite enrichment; no visual/physical coverage.','No training, network/Drive, app/git, registry/context/state/source changes.','Old sources and G2 final cases remain immutable.'])
 (OUT/'manifest.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n','utf-8');print(dump(dict(cases=len(ROWS),chat=len(chats),masters=len(counts),numeric=len(numeric),manifest=manifest)))
if __name__=='__main__':main()
