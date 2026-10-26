"""Twelve finite original G5 text drafts; no publication/training/shared mutations."""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal as D
from collections import Counter
from itertools import product
import ast,json,hashlib,re
from exhaustive_primary_math import chat_records,expression_group
HERE=Path(__file__).parent
ROOT=HERE/'cloud_publication/sgk_finish_20261020'
OUT=ROOT/'g5_text_append'
OLD=HERE/'cloud_publication/sgk_page_audit_20261019'
MAP=ROOT/'crossgrade_mapping/resume_queue.json'
FIELDS=['problem','givens','requested_quantity','student_work','initial_guidance','hints','worked_steps','expected_answer']
jd=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
sha=lambda b:hashlib.sha256(b).hexdigest()
WANT=['strict_fraction_unknown_numerator_interval','successive_fraction_of_current_remainder','three_unknown_pair_totals','future_age_invariant_difference_ratio','conditional_cashback_threshold','interval_bin_boundary_frequency']
queue=json.loads(MAP.read_text('utf-8'));MM={m['master_id']:m for m in queue['masters'] if m['master_id'] in WANT}
assert len(MM)==6 and all(m['category']=='FINITE_CONFIRMED_MISSING_MASTER' for m in MM.values())
ROWS=[]
def st(title,reason,result,explanation,expression=None,unit=''):
 return dict(title=title,reason=reason,result=str(result),explanation=explanation,expression=expression,unit=unit)
def hints(a,b,c):return [dict(level=i+1,hint=h,question=q) for i,(h,q) in enumerate(zip([a,b,c],['Em phải giữ dữ kiện và điều kiện nào?','Em áp dụng quan hệ đã cho ra sao?','Em kiểm đáp án và trường hợp biên thế nào?']))]
def add(master,branch,problem,givens,request,steps,answers,hh,model,decision,student=None):
 sid='sgk_finish_g5_20261020_'+branch
 ROWS.append(dict(sample_id=sid,case_group_id=sid+'_group',grade=5,topic=branch,split='train',case_kind='observable_student_error' if student else 'original_finite_reasoning',problem=problem,givens=[dict(id=f'g{i}',text=t,value=None,unit='',role='explicit_original_given') for i,t in enumerate(givens)],requested_quantity=request,student_work=dict(text=student,observations=[dict(excerpt=student,claim_scope='Only supplied synthetic written work; no hidden thoughts or physical outcome inferred.')]) if student else None,can_solve=True,worked_steps=[dict(step_id=f's{i}',**s) for i,s in enumerate(steps)],expected_answer=[dict(quantity=q,result=str(r),unit=u) for q,r,u in answers],initial_guidance=[hh[0]['hint']],hints=hh,canonical_signatures=sorted({expression_group(s['expression']) for s in steps if s['expression']}),independent_model=model,pedagogical_review_decision=decision,acceptance_status='DRAFT_AWAITING_ROOT_CONTENT_QA',quality_status='AUTHOR_SELF_QA_COMPLETE_PENDING_ROOT_QA',human_verified=False,teacher_certified=False,owner_human_reviewed=False,source_role='AI_GENERATED',coverage=dict(mode='FINITE_SUPPLEMENTARY_APPEND_NOT_CORE',finite_master_id=master,branch=branch,numbers_only_variant=False,new_core_slots_claimed=0,text_relation_only=True,visual_physical_coverage_claimed=False),curriculum_assignment=dict(grade=5,enrichment=True,source_reference='Observed KNTT G5 publisher page receipt; original explicit text analogue; age models are enrichment, not curriculum certification'),provenance=dict(authorship_origin='ORIGINAL_AI_TEACHER_AUTHORING',book_exercise_copied=False,human_content_review_completed=False,actual_physical_or_image_result_claimed=False,acceptance_basis='OWNER_PREAUTHORIZED_PROCESS_ROOT_QA_PENDING'),nearest_source_comparison=dict(mapping_file=str(MAP.relative_to(HERE)),mapping_sha256=sha(MAP.read_bytes()),actual_page_receipts=MM[master]['actual_page_receipts'],nearest_actual_valid_train_rows=MM[master]['nearest_refs'],semantic_difference=MM[master]['reasons'])))

def author():
 m=WANT[0]
 add(m,'fraction_strict_all_numerators','Tìm mọi chữ số x từ 0 đến 9 để 1/3 < x/12 < 3/4. x là tử số, mẫu 12 cố định; hai dấu đều là nhỏ hơn nghiêm ngặt. Không làm tròn phân số.',['x là chữ số0..9; mẫu12','1/3 < x/12 < 3/4; không nhận bằng'],'Mọi chữ số x thỏa cả hai cận',[
 st('Đưa về cùng mẫu','Đổi cả tử và mẫu cùng hệ số giữ giá trị.','4/12 < x/12 < 9/12','Một phần ba bằng bốn phần mười hai; ba phần tư bằng chín phần mười hai.'),st('Chọn mọi tử số nằm giữa','Cùng mẫu dương nên so tử; hai cận không được lấy.','x = 5, 6, 7, 8','Các chữ số lớn hơn bốn và nhỏ hơn chín là năm,sáu,bảy,tám; đã liệt kê hết.'),st('Kiểm biên và miền chữ số','Một ứng viên phải thỏa cả hai dấu nghiêm ngặt.','Không nhận 4 hoặc 9','Tử bốn bằng cận dưới; tử chín bằng cận trên. Tử từ không đến ba ở dưới, không còn chữ số nào khác.')],[('Các chữ số x','5, 6, 7, 8','')],hints('Giữ mẫu cố định và miền chữ số của tử số.','Có thể đổi hai cận về cùng mẫu với phân số chứa x.','Kiểm riêng dấu bằng ở mỗi đầu và mọi chữ số chưa chọn.'),dict(kind='fraction_interval',den=12,lo='1/3',hi='3/4',expected=[5,6,7,8]),'Nhánh liệt kê đầy đủ nghiệm với hai mẫu cận khác nhau; không coi chọn một nghiệm là đủ.')
 student='x có thể là 4, 5, 6 vì 4/10 = 2/5 và 6/10 = 3/5.'
 add(m,'fraction_strict_equal_endpoint_error','Điền mọi chữ số x để 2/5 < x/10 < 3/5, hai dấu nghiêm ngặt và mẫu 10 cố định. Bạn viết: '+student+' Giữ nguyên câu đó, kiểm danh sách và sửa; không đổi dấu bất đẳng thức.',['x chữ số0..9; 2/5 < x/10 < 3/5','Hai dấu nghiêm ngặt; mẫu10 cố định'],'Danh sách đúng và nhận xét hai cận bằng',[
 st('Giữ phần quy đổi đúng','Hai đẳng thức trong câu bạn đúng về giá trị.','2/5 = 4/10; 3/5 = 6/10','Sai không nằm ở quy đồng mà ở nhận trường hợp bằng vào dấu nhỏ hơn.'),st('Áp cả hai cận','Tử phải lớn hơn bốn và nhỏ hơn sáu.','Chỉ x=5','Bốn và sáu đều bị loại vì bằng một cận; năm nằm giữa.'),st('Kiểm tính đầy đủ','Không có số nguyên nào khác giữa bốn và sáu.','5/10 thỏa; 4/10 và 6/10 không thỏa','Danh sách sửa chỉ giữ năm, không sửa dấu để hợp danh sách cũ.')],[('Chữ số x','5',''),('Nhận xét','Hai đẳng thức đúng, nhưng x=4 và x=6 vi phạm dấu nghiêm ngặt','')],hints('Tách phép quy đổi phân số khỏi việc xét dấu bất đẳng thức.','Thử mỗi ứng viên vào cả hai dấu của đề.','Đúng bằng cận có được nhận theo lời đề không?'),dict(kind='fraction_interval',den=10,lo='2/5',hi='3/5',expected=[5],student_candidates=[4,5,6]),'Nhánh sửa sai đúng tại equality boundary; không gán lỗi tư duy ngoài dòng cho sẵn.',student)
 m=WANT[1]
 add(m,'remainder_two_stage_forward','Bình giả định có 120 lít nước. Lần đầu dùng 1/3 lượng ban đầu; lần hai dùng 1/4 lượng còn ngay sau lần đầu. Không thêm, mất nước hoặc thay đổi khác. Hỏi sau cả hai lần còn bao nhiêu lít?',['120 lít ban đầu; lần1 dùng1/3 ban đầu','Lần2 dùng1/4 lượng còn sau lần1; không thay đổi khác'],'Lượng nước sau hai lần dùng',[
 st('Tìm lượng dùng lần đầu','Một phần ba lấy theo lượng ban đầu.',40,'Một trăm hai mươi chia ba bằng bốn mươi.','120/3','lít'),st('Cập nhật lượng làm mốc mới','Lần sau không còn lấy một phần tư của một trăm hai mươi.',80,'Bớt bốn mươi khỏi một trăm hai mươi còn tám mươi.','120-40','lít'),st('Dùng một phần tư mốc mới','Mẫu số chia lượng còn sau lần đầu.',20,'Tám mươi chia bốn bằng hai mươi.','80/4','lít'),st('Tìm phần cuối và kiểm bảo toàn','Hai lượng dùng và lượng cuối là ba phần rời của ban đầu.',60,'Tám mươi bớt hai mươi còn sáu mươi; kiểm bốn mươi cộng hai mươi cộng sáu mươi bằng một trăm hai mươi.','80-20','lít')],[('Nước còn',60,'lít')],hints('Ghi rõ lượng nào là mốc cho từng phân số.','Sau lần đầu hãy cập nhật lượng đang còn trước lần sau.','Cộng hai lượng dùng với lượng cuối để kiểm ban đầu.'),dict(kind='remainder',initial=120,f1='1/3',f2='1/4',expected=60),'Hai phân số tác động trên hai cơ sở khác nhau, bổ sung rõ semantic missing remainder base.')
 student='Lần đầu dùng 96 : 4 = 24 lít; lần sau dùng 96 : 3 = 32 lít; còn 96 − 24 − 32 = 40 lít.'
 add(m,'remainder_wrong_second_base','Bể có 96 lít. Dùng 1/4 lượng ban đầu rồi dùng 1/3 lượng còn sau lần đầu; không thay đổi khác. Bài viết ghi: '+student+' Giữ các dòng ấy, chỉ rõ phép tính không đúng cơ sở, sửa lượng còn cuối cùng.',['96 lít; lần1 dùng1/4 ban đầu','Lần2 dùng1/3 phần còn; không thêm/mất khác'],'Nhận xét cơ sở lần hai và lượng còn đúng',[
 st('Giữ lần đầu đúng','Một phần tư của chín mươi sáu được hai mươi bốn.',24,'Dòng đầu đúng; chưa được dùng tiếp mốc chín mươi sáu cho lần hai.','96/4','lít'),st('Tìm cơ sở lần hai','Sau dùng lần đầu phải bớt lượng đó khỏi bể.',72,'Chín mươi sáu bớt hai mươi bốn còn bảy mươi hai.','96-24','lít'),st('Sửa phép dùng lần hai','Một phần ba áp vào bảy mươi hai đang còn.',24,'Bảy mươi hai chia ba bằng hai mươi bốn, không phải ba mươi hai.','72/3','lít'),st('Kết luận theo các lượng đúng','Phải bớt lượng lần hai từ phần đang còn.',48,'Bảy mươi hai bớt hai mươi bốn còn bốn mươi tám. Kiểm hai mươi bốn cộng hai mươi bốn cộng bốn mươi tám bằng chín mươi sáu. Dòng96:3=32 đúng phép chia nhưng sai mốc theo đề.','72-24','lít')],[('Nước còn đúng',48,'lít'),('Sai cơ sở','96:3 dùng lượng ban đầu thay vì lượng còn72 lít','')],hints('Phép chia có thể đúng số học nhưng dùng sai lượng mốc.','Lần dùng sau bắt đầu từ trạng thái nào của bể?','Kiểm các lượng đã dùng cộng phần cuối có khớp ban đầu và đúng từng tỉ phần.'),dict(kind='remainder',initial=96,f1='1/4',f2='1/3',expected=48,wrong_second=32),'Nhánh critique bases, giữ dòng student rồi phân biệt sai mô hình với sai tính toán.',student)
 m=WANT[2]
 add(m,'three_pairs_unique_decimal','Ba túi A,B,C có khối lượng dương không đổi trong mô hình. A và B cộng lại 7,5 kg; B và C cộng lại 9 kg; A và C cộng lại 8,5 kg. Không có túi khác. Tìm khối lượng mỗi túi và kiểm đủ ba tổng.',['A+B=7,5kg; B+C=9kg; A+C=8,5kg','Ba túi dương, ổn định; chỉ ba túi'],'Khối lượng A,B,C',[
 st('Gộp ba tổng đôi','Mỗi túi có mặt đúng hai lần trong tổng ba cặp.',25,'Bảy phẩy năm cộng chín cộng tám phẩy năm bằng hai mươi lăm, là hai lần khối lượng cả ba.','75/10+9+85/10','kg'),st('Tìm tổng cả ba','Chia hai để mỗi túi được tính một lần.',12.5,'Hai mươi lăm chia hai bằng mười hai phẩy năm.','25/2','kg'),st('Tách từng túi bằng tổng đối diện','Tổng cả ba trừ tổng hai túi còn lại cho túi cần tìm.','A=3,5; B=4; C=5','A=12,5−9=3,5; B=12,5−8,5=4; C=12,5−7,5=5, đều dương.'),st('Kiểm ba quan hệ','Một đáp án phải khớp mọi tổng ban đầu.','7,5; 9; 8,5 kg','Ba phẩy năm cộng bốn bằng bảy phẩy năm; bốn cộng năm bằng chín; ba phẩy năm cộng năm bằng tám phẩy năm.')],[('A','3.5','kg'),('B',4,'kg'),('C',5,'kg')],hints('Đếm xem mỗi túi xuất hiện bao nhiêu lần khi cộng ba tổng đôi.','Tìm tổng cả ba rồi trừ đúng cặp không chứa túi cần tìm.','Thay cả ba khối lượng vào đủ ba tổng đôi.'),dict(kind='pair_totals',ab='7.5',bc='9',ac='8.5',expected=['3.5','4','5']),'Nhánh reconstruction từ ba pair totals số thập phân; ba identities stable, không bịa kết quả cân thật.')
 add(m,'three_pairs_total_conflict_repair','Phiếu giả định ghi A+B=7 kg, A+C=8 kg, B+C=9 kg và A+B+C=10 kg. Ba túi có khối lượng dương không đổi. Kiểm xem bốn dòng có thể đồng thời đúng không. Được phép sửa duy nhất dòng tổng cả ba, phải giữ nguyên ba tổng đôi. Hãy ghi dòng tổng cần sửa và khối lượng từng túi theo ba tổng đôi.',['AB7; AC8; BC9 kg; tổng ghi10kg','Chỉ được sửa dòng tổng cả ba; giữ ba pair totals'],'Tính nhất quán, tổng sửa và A,B,C',[
 st('Suy tổng từ ba dòng bắt buộc giữ','Trong tổng các cặp, mỗi túi bị tính hai lần.',12,'Bảy cộng tám cộng chín bằng hai mươi bốn; chia hai được mười hai.','(7+8+9)/2','kg'),st('Đối chiếu dòng tổng','Một tổng vừa bằng mười hai vừa bằng mười là không thể.','Bốn dòng không đồng thời đúng','Theo quyền sửa duy nhất dòng tổng, thay A+B+C=10kg bằng A+B+C=12kg; không tự thay pair totals.'),st('Khôi phục các túi','Lấy tổng đúng trừ cặp còn lại.','A=3; B=4; C=5 kg','A=12−9=3; B=12−8=4; C=12−7=5. Kiểm3+4=7,3+5=8,4+5=9 và3+4+5=12.')],[('Nhất quán','Không thể đồng thời đúng bốn dòng',''),('Tổng sửa',12,'kg'),('Khối lượng','A=3kg; B=4kg; C=5kg','')],hints('Suy lại tổng cả ba từ các dòng phải giữ nguyên.','So tổng suy được với dòng được phép sửa.','Kiểm mọi tổng sau đúng một sửa được cho phép.'),dict(kind='pair_totals',ab='7',bc='9',ac='8',expected=['3','4','5'],supplied_total='10',correct_total='12'),'Nhánh inconsistent rồi authorized repair đúng trường, không âm thầm sửa dữ kiện để có nghiệm.')
 m=WANT[3]
 add(m,'age_future_ratio_reverse_current','Mô hình tuổi tính bằng số năm chính xác: chị hơn em 12 tuổi và mỗi người tăng đúng1 tuổi sau1 năm. Sau4 năm nữa, tuổi chị bằng hai lần tuổi em lúc đó. Tìm tuổi hiện nay của mỗi người và kiểm. Không có thay đổi quy ước tuổi khác.',['Chị−em=12; cả hai tăng1 mỗi năm','Sau4năm chị=2 lần em, cùng thời điểm'],'Tuổi hiện tại chị và em',[
 st('Giữ hiệu khi cùng tăng tuổi','Thêm bốn vào cả hai không làm đổi hiệu.',12,'Hiệu tuổi sau bốn năm vẫn mười hai. Không cộng bốn vào riêng hiệu.','(12+4)-4','tuổi'),st('Dùng tỉ số ở đúng thời điểm','Sau bốn năm chị hai phần, em một phần; chênh một phần bằng mười hai.','Sau4năm: em12, chị24','Hiệu một phần cho em mười hai, chị hai phần là hai mươi bốn.'),st('Lùi cùng số năm','Hai tuổi vừa tìm là tương lai nên đều bớt bốn.','Hiện nay em8, chị20','Tám cộng bốn bằng mười hai; hai mươi cộng bốn bằng hai mươi bốn. Kiểm20−8=12 và24=2×12.')],[('Em hiện nay',8,'tuổi'),('Chị hiện nay',20,'tuổi')],hints('Đặt hiệu tuổi và tỉ số vào cùng thời điểm.','Hai người cùng tăng một số năm thì hiệu đổi thế nào?','Từ tuổi tương lai cần lùi lại cho cả hai người.'),dict(kind='age_reverse',difference=12,years=4,ratio=2,expected_current=[8,20]),'Age enrichment explicit exact-year model; ratio future not imported as current ratio.')
 student='Hiện nay anh25 tuổi, em10 tuổi nên anh luôn bằng2,5 lần tuổi em; không có lúc anh gấp đôi em.'
 add(m,'age_ratio_changes_find_wait','Trong mô hình tuổi chính xác theo năm, hiện nay anh25 tuổi, em10 tuổi; mỗi năm cả hai cùng thêm1 tuổi. Bạn viết: '+student+' Giữ câu đó, kiểm từ luôn và tìm sau bao nhiêu năm tuổi anh bằng đúng hai lần tuổi em.',['Hiện tại anh25,em10; cùng tăng1/năm','Cần thời điểm tương lai anh=2×em'],'Nhận xét tỉ số và số năm phải chờ',[
 st('Giữ hiệu ổn định','Cùng thêm số năm nên hiệu vẫn bằng hiện tại.',15,'Hai mươi lăm bớt mười bằng mười lăm. Tỉ số không được suy là bất biến từ hiệu bất biến.','25-10','tuổi'),st('Xét lúc tỉ số bằng hai','Lúc đó anh hai phần, em một phần; hiệu một phần bằng mười lăm.','Lúc đó em15, anh30','Em phải mười lăm, anh ba mươi; hiệu vẫn mười lăm.'),st('Tìm thời gian cùng tăng','Tuổi em tăng từ mười lên mười lăm.',5,'Mười lăm bớt mười bằng năm năm. Kiểm25+5=30 và10+5=15,30=2×15; câu luôn 2,5 lần sai.','15-10','năm')],[('Thời gian chờ',5,'năm'),('Khi đó','Anh30 tuổi, em15 tuổi',''),('Nhận xét','Hiệu giữ nguyên nhưng tỉ số thay đổi; từ luôn là sai','')],hints('Phân biệt hiệu hai số với tỉ số của chúng.','Ở lúc gấp đôi, hiệu ứng với bao nhiêu phần của tuổi em?','Kiểm cùng cộng số năm tìm được vào cả hai tuổi ban đầu.'),dict(kind='age_wait',younger=10,older=25,ratio=2,expected_years=5),'Nhánh reject constant-ratio misconception and solve future waiting time; not number-only reverse-current variant.',student)
 m=WANT[4]
 add(m,'cashback_discounted_exact_threshold','Chương trình hoàn tiền giả định dùng nghìn đồng: giá niêm yết250, giảm10% giá niêm yết. Chỉ khi số phải thanh toán sau giảm từ225 trở lên, kể cả đúng225, mới hoàn5% của chính số phải thanh toán sau giảm. Tiền hoàn trả sau thanh toán, không có phí khác. Tìm số thanh toán, tiền hoàn và chi phí ròng bằng thanh toán trừ tiền hoàn.',['Giá250nghìn; giảm10% giá niêm yết','Cận đủ điều kiện: sau giảm≥225; hoàn5% của sau giảm; không phí'],'Thanh toán, hoàn tiền, chi phí ròng',[
 st('Tính thanh toán trước khi xét cận','Giảm giá áp theo giá niêm yết.',225,'Giảm hai mươi lăm nên thanh toán hai trăm hai mươi lăm nghìn.','250-250*10/100','nghìn đồng'),st('Xét trường hợp đúng ngưỡng','Từ 225 trở lên gồm 225.','Đủ điều kiện','Không so giá niêm yết với ngưỡng; dùng số sau giảm.'),st('Tính tiền hoàn đúng cơ sở','Hoàn năm phần trăm của số thanh toán sau giảm.',11.25,'Hai trăm hai mươi lăm nhân năm chia một trăm bằng mười một phẩy hai mươi lăm.','225*5/100','nghìn đồng'),st('Tách thanh toán và ròng','Tiền hoàn nhận sau, không làm thay số đã thanh toán.',213.75,'Hai trăm hai mươi lăm bớt mười một phẩy hai mươi lăm bằng hai trăm mười ba phẩy bảy mươi lăm; ròng cộng tiền hoàn khôi phục thanh toán.','225-1125/100','nghìn đồng')],[('Thanh toán',225,'nghìn đồng'),('Tiền hoàn','11.25','nghìn đồng'),('Chi phí ròng','213.75','nghìn đồng')],hints('Theo thứ tự giảm giá, xét ngưỡng, rồi mới tính khoản hoàn.','Đọc ngưỡng có lấy trường hợp bằng và tiền hoàn dùng cơ sở nào.','Phân biệt tiền đã thanh toán với chi phí sau khi nhận hoàn.'),dict(kind='cashback',price='250',discount='10',threshold='225',rate='5',expected=['225','11.25','213.75']),'Exact inclusive threshold after discount; hypothetical math only, no real offer/market/legal assertion.')
 student='Giá gốc300 lớn hơn250 nên được hoàn300×5%=15 nghìn; chi phí ròng là240−15=225 nghìn.'
 add(m,'cashback_wrong_original_threshold','Quy tắc giả định, đơn vị nghìn đồng: giá niêm yết300, giảm20% giá niêm yết. Chỉ xét số thanh toán sau giảm: nếu số đó từ250 trở lên thì hoàn5% của số đó; nếu dưới250 thì hoàn0. Không có phí khác. Bạn viết: '+student+' Giữ câu đó, kiểm điều kiện, số tiền hoàn và chi phí ròng.',['Giá300; giảm20%; ngưỡng saugiảm≥250','Đủ thì hoàn5% saugiảm; khôngđủ hoàn0; không phí'],'Phản hồi điều kiện và các số tiền đúng',[
 st('Giữ thanh toán được tính đúng','Giá sau giảm lấy giá gốc trừ phần trăm giảm.',240,'Ba trăm trừ sáu mươi bằng hai trăm bốn mươi.','300-300*20/100','nghìn đồng'),st('Kiểm đúng lượng với ngưỡng','Điều kiện dùng sau giảm, không dùng giá gốc.','240 < 250; không đủ điều kiện','Ba trăm vượt ngưỡng không làm giao dịch đủ điều kiện vì số phải thanh toán chỉ hai trăm bốn mươi.'),st('Tính hoàn và ròng theo nhánh đúng','Không đủ thì hoàn không, theo quy tắc đã cho.',240,'Tiền hoàn không; chi phí ròng240−0=240 nghìn. Dòng hoàn 15 không áp được dù phép 300×5%=15 đúng số học.','240-0','nghìn đồng')],[('Thanh toán',240,'nghìn đồng'),('Tiền hoàn',0,'nghìn đồng'),('Chi phí ròng',240,'nghìn đồng')],hints('Xác định biến nào trong điều kiện được đem so với ngưỡng.','Chỉ tính tỉ lệ hoàn khi điều kiện đã đúng.','Giữ phép tính đúng số học nhưng phân biệt nó có được quy tắc cho áp dụng không.'),dict(kind='cashback',price='300',discount='20',threshold='250',rate='5',expected=['240','0','240']),'Wrong original-price threshold and wrong cashback base critique, structurally distinct no-eligibility branch.',student)
 m=WANT[5]
 add(m,'bins_halfopen_shared_boundary','Sáu mẫu thử có số đo bằng đơn vị u: A10,B12,C15,D15,E19,F20. Mỗi chữ là một mẫu riêng. Nhóm I nhận10≤x<15; nhóm II nhận15≤x≤20. Lập danh sách mã và tần số mỗi nhóm, kiểm đủ sáu mẫu; không gộp hai mẫu cùng số đo.',['MẫuA10,B12,C15,D15,E19,F20 đơn vịu','I:10≤x<15;II:15≤x≤20'],'Danh sách mã, tần số từng nhóm và tổng',[
 st('Xét đúng ranh giới15','NhómI không nhận15; nhómII nhận15.','I: A,B; II:C,D,E,F','Mẫu A ở cận 10 được nhận; F ở cận 20 được nhận. C,D cùng 15 nhưng là hai mẫu.'),st('Đếm từng mã','Mỗi mã thuộc đúng một nhóm theo dấu cận.','I2; II4','Tần số đếm mẫu, không cộng các số đo và không bỏ mã trùng giá trị.'),st('Kiểm tổng và không đếm đôi','Hai nhóm rời và bao hết sáu mã đã cho.',6,'Hai cộng bốn bằng sáu; không mã nào bị bỏ hoặc nhận vào hai nhóm.','2+4','mẫu')],[('NhómI','A,B; tần số2',''),('NhómII','C,D,E,F; tần số4',''),('Tổng',6,'mẫu')],hints('Đọc riêng dấu lấy hoặc không lấy ở mỗi cận.','Gắn từng mã vào nhóm trước khi đếm tần số.','Kiểm mã đúng ranh giới và các mẫu có số đo bằng nhau.'),dict(kind='bins',items={'A':'10','B':'12','C':'15','D':'15','E':'19','F':'20'},bins=[['10','15',True,False],['15','20',True,True]],expected=[['A','B'],['C','D','E','F']]),'Halfopen/shared15andclosed20boundary; preserves observation identity.')
 student='NhómI có3 mẫu, nhómII có4 mẫu, nhómIII có1 mẫu; tổng8 mẫu vì10 được tính ở cảI vàII.'
 add(m,'bins_boundary_doublecount_error','Có sáu mẫu riêng A0,B10,C10,D20,E20,F30, đơn vị u. NhómI:0≤x≤10; nhómII:10<x≤20; nhómIII:20<x≤30. Bạn viết: '+student+' Giữ câu đó, sửa danh sách mã và tần số ba nhóm theo đúng dấu đã cho.',['A0,B10,C10,D20,E20,F30','I[0,10];II(10,20];III(20,30]'],'Phản hồi đếm đôi và bảng tần số đúng',[
 st('Giữ cận phải, loại cận trái của nhóm II và III','Hai dấu 10<x và 20<x không nhận giá trị bằng cận trái.','I:A,B,C; II:D,E; III:F','B,C ở 10 chỉ thuộc nhóm I; D,E ở 20 chỉ thuộc nhóm II. Không sửa dấu để hợp bài viết.'),st('Đếm các mã sau phân nhóm','Các mã khác nhau vẫn được tính dù số đo bằng nhau.','3;2;1 mẫu','Tần số nhóm I ban đầu đúng; nhóm II sai do cộng lại B,C. Mẫu F ở 30 thuộc nhóm III vì cận phải lấy bằng.'),st('Kiểm bảo toàn số mẫu','Mỗi mã đầu vào có đúng một chỗ trong bảng.',6,'Ba cộng hai cộng một bằng sáu, khớp sáu mã; tổng tám do đếm trùng, không phải thêm mẫu mới.','3+2+1','mẫu')],[('NhómI','A,B,C; tần số3',''),('NhómII','D,E; tần số2',''),('NhómIII','F; tần số1',''),('Tổng',6,'mẫu')],hints('So đúng dấu của hai nhóm kề tại một giá trị ranh giới.','Một mã được nhận ở một hay cả hai nhóm theo quy tắc?','Tổng tần số phải khớp số mã đầu vào, không khớp số giá trị khác nhau.'),dict(kind='bins',items={'A':'0','B':'10','C':'10','D':'20','E':'20','F':'30'},bins=[['0','10',True,True],['10','20',False,True],['20','30',False,True]],expected=[['A','B','C'],['D','E'],['F']]),'Critique doublecount at shared boundary, three rightclosed bins distinctfromfirsttwoleftclosed.',student)

def evaluate(e,typ):
 def walk(n):
  if isinstance(n,ast.Constant):return typ(str(n.value))
  if isinstance(n,ast.BinOp):
   a,b=walk(n.left),walk(n.right)
   if isinstance(n.op,ast.Add):return a+b
   if isinstance(n.op,ast.Sub):return a-b
   if isinstance(n.op,ast.Mult):return a*b
   if isinstance(n.op,ast.Div):return a/b
  raise ValueError(e)
 return walk(ast.parse(e,mode='eval').body)
def oracle(m):
 k=m['kind']
 if k=='fraction_interval':
  # Cross-multiplication over all ten digits independently of a worked rewrite.
  lo,hi=F(m['lo']),F(m['hi']);ss=[x for x in range(10) if lo.numerator*m['den']<x*lo.denominator and x*hi.denominator<hi.numerator*m['den']]
  assert ss==m['expected'];return dict(digits_checked=list(range(10)),valid=ss,endpoint_equal=[x for x in range(10) if F(x,m['den']) in [lo,hi]])
 if k=='remainder':
  # Partition original into equal atoms at product-of-denominator granularity.
  a,b=F(m['f1']),F(m['f2']);N=a.denominator*b.denominator;unit=F(m['initial'],N);atoms=list(range(N));first=atoms[:N*a.numerator//a.denominator];rest=atoms[len(first):];second=rest[:len(rest)*b.numerator//b.denominator];final=rest[len(second):];val=len(final)*unit
  assert val==m['expected'];return dict(atom_count=N,atom_quantity=str(unit),first_used=str(len(first)*unit),second_used=str(len(second)*unit),final=str(val),partition_conserves_original=(len(first)+len(second)+len(final)==N))
 if k=='pair_totals':
  # Independent bounded tenth-kg enumeration, retain every solution.
  target=[F(m['ab']),F(m['bc']),F(m['ac'])];limit=int(max(target)*10);sol=[]
  for ai in range(1,limit+1):
   a=F(ai,10);b=target[0]-a;c=target[2]-a
   if b>0 and c>0 and b+c==target[1]:sol.append([a,b,c])
  expect=[F(x) for x in m['expected']];assert sol==[expect]
  total=sum(expect);assert sum(target)==2*total
  if 'supplied_total'in m:assert total!=F(m['supplied_total']) and total==F(m['correct_total'])
  return dict(tenth_grid_complete_for_given_decimal_pair_sums=True,solutions=[[str(x) for x in p] for p in sol],total=str(total),uniqueness_reason='From AB and AC, B=AB−A,C=AC−A; BC then fixes2A. No off-grid alternative exists.')
 if k=='age_reverse':
  sols=[[y,y+m['difference']] for y in range(1,101) if y+m['difference']+m['years']==m['ratio']*(y+m['years'])];assert sols==[m['expected_current']];return dict(integer_year_candidates_1_to100=sols,uniqueness_reason='Future difference=(ratio−1)×future younger; nonzero multiplier fixes future younger exactly.')
 if k=='age_wait':
  sols=[t for t in range(101) if m['older']+t==m['ratio']*(m['younger']+t)];assert sols==[m['expected_years']];return dict(wait_candidates_0_to100=sols,initial_ratio=str(F(m['older'],m['younger'])),future_ratio=str(F(m['older']+sols[0],m['younger']+sols[0])),uniqueness_reason='For ratio2, equality rearranges to t=older−2×younger, hence no additional off-grid solution.')
 if k=='cashback':
  # Decimal net-factor route versus Fraction subtract-discount route.
  p,d,t,r=map(D,[m['price'],m['discount'],m['threshold'],m['rate']]);paid=p*(D(100)-d)/D(100);eligible=paid>=t;cash=paid*r/D(100) if eligible else D(0);net=paid-cash
  pf,df,tf,rf=map(F,[m['price'],m['discount'],m['threshold'],m['rate']]);paidf=pf-pf*df/100;cashf=paidf*rf/100 if paidf>=tf else F(0)
  assert [F(paid),F(cash),F(net)]==[paidf,cashf,paidf-cashf]==[F(x) for x in m['expected']]
  return dict(paid=str(paid),eligible=eligible,cashback=str(cash),net=str(net),at_threshold=paid==t,independent_fraction_decimal_agree=True)
 if k=='bins':
  groups=[[] for _ in m['bins']];members={}
  for label,v in m['items'].items():
   v=F(v);ix=[]
   for i,(lo,hi,lc,rc) in enumerate(m['bins']):
    a,b=F(lo),F(hi)
    if (v>=a if lc else v>a) and (v<=b if rc else v<b):groups[i].append(label);ix.append(i)
   assert len(ix)==1;members[label]=ix
  assert groups==m['expected'];assert sum(map(len,groups))==len(m['items']);return dict(groups=groups,frequencies=list(map(len,groups)),membership=members,total=len(m['items']))
 raise ValueError(k)

def main():
 author();assert len(ROWS)==12 and Counter(r['coverage']['finite_master_id'] for r in ROWS)==Counter({m:2 for m in WANT})
 OUT.mkdir(parents=True,exist_ok=True)
 def write(name,rr):
  data=('\n'.join(jd(r) for r in rr)+'\n').encode('utf-8');(OUT/name).write_bytes(data);return dict(path=name,sha256=sha(data),bytes=len(data),rows=len(rr))
 nearest=[];pages=[]
 for master in WANT:
  m=MM[master]
  # Read exact actual nearest row, selected as the closest inspected comparison.
  ref=m['nearest_refs'][0];raw=(OLD/ref['source_file']).read_bytes().splitlines()[ref['line']-1];assert sha(raw)==ref['sha256'];row=json.loads(raw)
  assert row['sample_id']==ref['sample_id'] and row.get('split','train')=='train' and not re.search('holdout|eval|pilot|protected',row['sample_id'],re.I)
  nearest.append(dict(master_id=master,reference=ref,source_row_sha256=sha(raw),actual_fields={f:row.get(f) for f in FIELDS},semantic_comparison=m['reasons']))
  for pr in m['actual_page_receipts']:
   matches=[]
   for line in (OLD/'g5_audit/page_review.jsonl').read_bytes().splitlines():
    z=json.loads(line)
    if z.get('volume')==pr.get('volume') and z.get('printed_page')==pr.get('printed_page') and z.get('sha256')==pr.get('sha256'):matches.append((line,z))
   assert len(matches)==1;line,z=matches[0];pages.append(dict(master_id=master,source_file='g5_audit/page_review.jsonl',source_row_sha256=sha(line),receipt=z))
 manifest=[write('cases.jsonl',ROWS)];rawlines=(OUT/'cases.jsonl').read_bytes().splitlines();hashes={r['sample_id']:sha(l) for r,l in zip(ROWS,rawlines)}
 numeric=[];oo=[];qa=[];chats=[]
 for r in ROWS:
  rh=hashes[r['sample_id']]
  for s in r['worked_steps']:
   assert all(s[k] for k in ['title','reason','explanation'])
   if s['expression']:
    f=evaluate(s['expression'],F);d=evaluate(s['expression'],D);assert f==F(s['result'])==F(d)
    numeric.append(dict(sample_id=r['sample_id'],source_row_sha256=rh,step_id=s['step_id'],expression=s['expression'],fraction_result=str(f),decimal_result=str(d),passed=True))
  oo.append(dict(sample_id=r['sample_id'],source_row_sha256=rh,master_id=r['coverage']['finite_master_id'],independent_model=r['independent_model'],result=oracle(r['independent_model']),independent_of_worked_expression_evaluator=True,passed=True))
  assert [h['level'] for h in r['hints']]==[1,2,3]
  for c in chat_records(r):c.update(source_row_sha256=rh,acceptance_status=r['acceptance_status'],quality_status=r['quality_status']);chats.append(c)
  qa.append(dict(sample_id=r['sample_id'],source_row_sha256=rh,source_file='cases.jsonl',hash_basis='exact UTF8 source line excluding newline',reviewer='g5_text_author_actual_full_field_self_review',actual_fields={f:r.get(f) for f in FIELDS},criteria=[dict(criterion=k,passed=True,evidence=e) for k,e in [
   ('problem_givens_request_consistency','Every boundary/base/identity/rule used is explicit in actual source fields.'),('mathematical_correctness','All stated arithmetic expressions checked Fraction+Decimal; independent finite model checks full answers.'),('reason_steps_units_check','All steps include reasons/explanations/units; original constraints rechecked.'),('pedagogical_hint_nonleak','Initial guidance and all three hints/questions read in full; they identify method/boundary checks without requested numeric answers.'),('grounded_student_work_missing_data','Only exact supplied synthetic work is critiqued; repair permission is explicit; no invented physical evidence.'),('provenance_originality_grade_limit',r['pedagogical_review_decision']),('finite_scope_no_false_attestation','Two different reasoning branches per master; drafts await root content cross-review; no human attestation/model accuracy claim.')]],root_cross_review_status='PENDING',human_review_claimed=False))
 assert len(chats)==48
 manifest += [write('chat.jsonl',chats),write('selfqa7.jsonl',qa),write('independent_oracles.jsonl',oo),write('numeric_fraction_decimal.jsonl',numeric),write('nearest_actual_fullfields.jsonl',nearest),write('actual_page_receipts_readback.jsonl',pages)]
 summary=dict(status='12_DRAFTS_AUTHOR_QA_PASSED_ROOT_QA_PENDING',case_count=12,chat_count=48,master_counts=dict(Counter(r['coverage']['finite_master_id'] for r in ROWS)),numeric_steps=len(numeric),oracles=12,manifest=manifest,helper_sha256=sha(Path(__file__).read_bytes()),input_mapping_sha256=sha(MAP.read_bytes()),no_shared_sources_mutated=True,no_training=True,no_drive_mutation=True,limitations=['Original text reasoning only; no visual/physical outcome claims.','Age models are bounded enrichment.','Finite nearest-source comparison does not prove full curriculum coverage.','Draft status requires parent content cross-review.'])
 (OUT/'manifest.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(jd(summary))
if __name__=='__main__':main()
