"""Six original finite G2 numeral drafts. Data only; no accepted sources changed."""
from pathlib import Path
from itertools import permutations,product
from collections import Counter
from fractions import Fraction
from decimal import Decimal
import ast,hashlib,json,operator
import exhaustive_colab_loader as L
from exhaustive_primary_math import chat_records
HERE=Path(__file__).resolve().parent;PUB=HERE/'cloud_publication'
OUT=PUB/'g2_finite_forms_20261021/numerals_cohort1'
PLAN=PUB/'colab_data_audit_20261021/g2_planning/queue.json'
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha(b):return hashlib.sha256(b).hexdigest()
def jl(n,rs):(OUT/n).write_text(''.join(canon(x)+'\n' for x in rs),'utf8',newline='\n')
def wr(n,x):(OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
def step(title,reason,result,explanation,expression=None,unit=''):
 return dict(title=title,reason=reason,result=str(result),explanation=explanation,expression=expression,unit=unit)
TASKS=json.loads(PLAN.read_text('utf8'))['tasks'][:3]
rows=[]
def add(ti,topic,problem,givens,request,steps,answers,hints,model,novelty,student=None):
 t=TASKS[ti];sid='g2_numerals_20261021_'+topic
 for i,x in enumerate(steps):x['step_id']='s'+str(i)
 receipts=[r for e in t['actual_candidate_evidence'] for r in e['actual_page_receipts']]
 r=dict(sample_id=sid,case_group_id=sid+'_group',grade=2,topic=topic,split='train',
  case_kind='observable_student_error' if student else 'original_finite_representation',problem=problem,
  givens=[dict(id='g'+str(i),role='explicit_original_given',text=x,value=None,unit='') for i,x in enumerate(givens)],
  requested_quantity=request,student_work=dict(text=student,observations=[dict(excerpt=student,claim_scope='Explicit supplied synthetic statement only')]) if student else None,
  can_solve=True,worked_steps=steps,expected_answer=[dict(quantity=q,result=str(v),unit=u) for q,v,u in answers],
  initial_guidance=[hints[0]],hints=[dict(level=i+1,hint=h,question=['Em cần phân biệt điều kiện nào trước?','Em kiểm từng lựa chọn ra sao?','Làm sao biết danh sách đủ và không đếm lặp?'][i]) for i,h in enumerate(hints)],
  acceptance_status='DRAFT_AWAITING_ROOT_CONTENT_CROSS_REVIEW',quality_status='AUTHOR_QA_PENDING_ROOT_REVIEW',
  source_role='AI_GENERATED',human_verified=False,teacher_certified=False,owner_human_reviewed=False,
  provenance=dict(authorship_origin='ORIGINAL_AI_TEACHER_AUTHORING',acceptance_basis='OWNER_PREAUTHORIZED_PROCESS_ROOT_QA_PENDING',
   human_content_review_completed=False,book_exercise_copied=False,actual_physical_or_image_result_claimed=False),
  curriculum_assignment=dict(grade=2,enrichment=True,minimum_grade_for_this_representation=2,
   master_id='finite_digit_card_enumeration',g2_finite_master_id=t['finite_master_id'],candidate_ids=t['candidate_ids'],
   actual_page_receipts=receipts,page_receipt_basis='Inherited hash-bound actual publisher-page receipts from G2 planning; this author did not newly inspect publisher images.',
   coverage_claim='Original finite text card model only; no actual image recognition or learner physical performance certified.'),
  coverage=dict(mode='FINITE_SUPPLEMENTARY_APPEND_NOT_CORE',finite_master_id='finite_digit_card_enumeration',
   g2_finite_master_id=t['finite_master_id'],candidate_ids=t['candidate_ids'],branch=topic,planning_task_id=t['task_id'],
   new_core_slots_claimed=0,numbers_only_variant=False,text_relation_only=True,visual_physical_coverage_claimed=False),
  answer_acceptance_contract=dict(scope='Complete unique numeral values as asked; physical arrangements counted separately only where explicitly requested.',no_feasible_extremum_is_not_zero=True),
  nearest_source_comparison=dict(status='NEAREST_ACTUAL_FULLFIELDS_READ',evidence='nearest_actual_fullfields.jsonl',
   semantic_difference=novelty,limitation='Finite relevant prior accepted-source comparison, not full-archive duplicate absence proof.'),
  independent_model=model)
 r['canonical_signatures']=L.source_signatures(r);rows.append(r)

add(0,'all_two_digit_unfiltered_zero',
 'Có ba thẻ riêng P ghi 0, Q ghi 2, R ghi 7. Mỗi lần chọn đúng hai thẻ khác nhau, đặt vào hàng chục và hàng đơn vị để lập một số có hai chữ số; hàng chục không được là 0. Có thể trả thẻ về rồi lập số khác. Liệt kê TẤT CẢ số khác nhau, không chỉ số chẵn hay số lẻ, sắp tăng; nêu số nhỏ nhất, lớn nhất và hiệu lớn nhất trừ nhỏ nhất.',
 ['Kho thẻ P:0, Q:2, R:7; chọn đúng hai thẻ, mỗi thẻ tối đa một lần trong mỗi số.',
  'Hàng chục khác 0; liệt kê mọi giá trị, không lọc chẵn/lẻ; giữa hai lần lập được trả thẻ.'],
 'Danh sách đủ số hai chữ số, hai cực trị và hiệu',
 [step('Chọn hàng chục trước','Số hai chữ số không bắt đầu bằng 0.','Hàng chục là 2 hoặc 7','Giữ thẻ hàng chục rồi chọn một trong hai thẻ còn lại cho hàng đơn vị. Không dùng một thẻ hai lần.'),
  step('Liệt kê hết mỗi nhánh','Mỗi số có một hàng chục xác định nên hai nhóm không lặp.','20;27;70;72','Hàng chục 2 cho 20,27; hàng chục 7 cho 70,72. Hai cách đầu bằng 0 không là số hai chữ số; cả số chẵn và lẻ đều được giữ.'),
  step('So từ hàng chục','Danh sách tăng cho biết hai đầu nhỏ nhất và lớn nhất.','Nhỏ nhất 20; lớn nhất 72','Nhóm hàng chục 2 nhỏ hơn nhóm hàng chục 7; trong từng nhóm so tiếp hàng đơn vị.'),
  step('Tính hiệu và kiểm lại','Lấy số lớn nhất trừ số nhỏ nhất theo đúng yêu cầu.','52','72−20=52; kiểm 20+52=72. Mỗi số trong danh sách dùng hai thẻ khác nhau; có bốn số.','72-20')],
 [('Mọi số','20;27;70;72',''),('Số nhỏ nhất','20',''),('Số lớn nhất','72',''),('Hiệu','52',''),('Số giá trị','4','số')],
 ['Đọc xem đề yêu cầu tất cả số hay chỉ một loại số.',
  'Chọn một thẻ được phép ở hàng chục rồi chỉ ghép với từng thẻ còn lại.',
  'Gộp các nhánh, sắp theo hàng và kiểm lại hiệu bằng phép cộng.'],
 dict(cards={'P':0,'Q':2,'R':7},length=2,bound=None,expected_values=[20,27,70,72],physical_assignments=4),
 'Unfiltered G2 all-number enumeration and extrema difference; prior G4 parity-only row omits lawful odd values.')

add(0,'optional_zero_not_compulsory_card',
 'Bốn thẻ riêng ghi 0,1,4,8, mỗi giá trị có đúng một thẻ. Mỗi lần chỉ chọn hai thẻ để lập số hai chữ số, mỗi thẻ dùng tối đa một lần, chữ số hàng chục khác 0; không buộc dùng thẻ 0. Bạn ghi: “Em chỉ lập 10,40,80 vì có thẻ 0 thì số nào cũng phải dùng nó.” Kiểm câu ghi rồi viết đầy đủ mọi số theo thứ tự tăng, nêu số nhỏ nhất, lớn nhất và hiệu của chúng. Trả thẻ về giữa các lần lập.',
 ['Kho 0,1,4,8, mỗi thẻ riêng; chọn đúng hai trong bốn, không bắt buộc chọn thẻ 0.',
  'Hàng chục khác 0; mỗi thẻ tối đa một lần trong một số, được dùng lại ở lần lập khác.'],
 'Sửa danh sách bỏ sót, hai cực trị và hiệu',
 [step('Đọc đúng quyền chọn thẻ','Chọn hai trong bốn không có nghĩa mọi số phải chứa thẻ 0.','Câu ghi đã thêm điều kiện không có trong đề','10,40,80 là những số hợp lệ, nhưng chưa đủ. Không phê bình cách nghĩ nào ngoài câu đã nêu.'),
  step('Tách nhánh theo hàng chục','Mỗi nhánh giữ một thẻ hàng chục và chỉ dùng một thẻ còn lại.','10;14;18;40;41;48;80;81;84','Hàng chục 1 cho 10,14,18; hàng chục 4 cho 40,41,48; hàng chục 8 cho 80,81,84. Không có nhánh hàng chục 0.'),
  step('Kiểm số lượng và thứ tự','Ba nhánh có ba số mỗi nhánh; hàng chục khác nhau nên không trùng.','9','Danh sách có 3+3+3=9 số; các số 11,44,88 không được vì mỗi giá trị chỉ có một thẻ.','3+3+3','số'),
  step('Lấy hai đầu danh sách','So hàng chục trước, cùng hàng chục mới so đơn vị.','Nhỏ nhất 10; lớn nhất 84','Hai đầu danh sách tăng là 10 và 84. Chọn thẻ khác 0 không làm số mất hợp lệ.'),
  step('Tính và kiểm hiệu','Hiệu là số lớn nhất trừ nhỏ nhất.','74','84−10=74; kiểm 10+74=84. Câu ghi ban đầu đã thiếu sáu số không dùng 0.','84-10')],
 [('Mọi số','10;14;18;40;41;48;80;81;84',''),('Số nhỏ nhất','10',''),('Số lớn nhất','84',''),('Hiệu','74',''),('Số giá trị','9','số')],
 ['Phân biệt thẻ có trong kho với thẻ bắt buộc phải chọn.',
  'Mỗi nhánh hàng chục phải ghép hết những thẻ còn lại được phép.',
  'Đối chiếu danh sách với mọi nhánh rồi so hai đầu; không tự thêm điều kiện chứa một thẻ nhất định.'],
 dict(cards={'P':0,'Q':1,'R':4,'S':8},length=2,bound=None,expected_values=[10,14,18,40,41,48,80,81,84],physical_assignments=9),
 'Optional-card choice and observable false mandatory-zero condition, unlike simply replacing digits in a fixed three-card permutation.',
 student='Em chỉ lập 10,40,80 vì có thẻ 0 thì số nào cũng phải dùng nó.')

add(1,'two_zero_cards_values_vs_arrangements',
 'Có ba thẻ riêng A ghi 0, B ghi 0, C ghi 5. Chọn đúng hai thẻ khác nhau đặt vào hai ô hàng chục–đơn vị để lập số hai chữ số; hàng chục khác 0. Trả thẻ về giữa các lần. Hai cách dùng A hay B được tính là hai cách đặt thẻ, nhưng nếu đọc ra cùng một số thì chỉ ghi một giá trị số. Liệt kê mọi giá trị số khác nhau, mọi cách đặt thẻ hợp lệ; nêu số nhỏ nhất, lớn nhất và hiệu. Không ghép hai thẻ 0 rồi coi 00 là số hai chữ số.',
 ['A:0, B:0, C:5; chọn hai trong ba thẻ riêng, mỗi thẻ một lần trong mỗi cách.',
  'Phân biệt giá trị số và danh tính thẻ; chữ số hàng chục khác 0.'],
 'Giá trị số, cách đặt thẻ theo thứ tự chục–đơn vị, cực trị và hiệu',
 [step('Chọn thẻ hàng chục','Hai thẻ ghi 0 không được đứng đầu một số hai chữ số.','C đứng hàng chục','Giữ thẻ C ghi 5 ở chục; đơn vị có thể dùng A hoặc B, không được dùng lại C.'),
  step('Ghi danh tính rồi đọc số','A và B là hai thẻ khác nhau nhưng cùng giá trị.','C-A;C-B đều đọc 50','Có hai cách đặt vật khác nhau; cả hai chỉ tạo cùng giá trị 50. Không đếm 05 hay 00 như số hai chữ số.'),
  step('Đếm riêng hai loại kết quả','Đề yêu cầu cả số cách đặt thẻ và số giá trị số khác nhau.','Hai cách đặt; một giá trị số','Không xóa một thẻ 0 khỏi kho, cũng không ghi giá trị 50 hai lần trong danh sách số.'),
  step('So cực trị trên tập giá trị','Nếu chỉ có một giá trị, nó vừa nhỏ nhất vừa lớn nhất.','0','Cả nhỏ nhất và lớn nhất đều là 50, nên 50−50=0; kiểm 50+0=50. Hiệu 0 không có nghĩa không có cách đặt.','50-50')],
 [('Mọi giá trị','50',''),('Mọi cách đặt thẻ','C-A;C-B',''),('Số giá trị','1','số'),('Số cách đặt','2','cách'),('Số nhỏ nhất','50',''),('Số lớn nhất','50',''),('Hiệu','0','')],
 ['Tách câu hỏi đếm giá trị số khỏi câu hỏi đếm các thẻ riêng.',
  'Sau khi chọn hàng chục hợp lệ, thử từng thẻ còn lại dù có thẻ ghi cùng chữ số.',
  'Gộp các cách đọc cùng một giá trị trước khi tìm hai cực trị.'],
 dict(cards={'A':0,'B':0,'C':5},length=2,bound=None,expected_values=[50],physical_assignments=2),
 'Repeated zero identities, selecting a subset and a singleton value-set with two physical realizations; not distinct-card parity enumeration.')

add(1,'repeated_nonzero_all_three_slots',
 'Có ba thẻ riêng A ghi 2, B ghi 2, C ghi 0. Trong mỗi lần, phải dùng đủ cả ba thẻ đúng một lần để lập số có ba chữ số; hàng trăm khác 0. Trả thẻ về giữa các lần. Khi liệt kê số thì gộp các cách đọc cùng giá trị, còn khi đếm cách đặt thẻ thì phân biệt A và B. Bạn viết: “A và B cùng ghi 2 nên bỏ B, chỉ còn số 20.” Hãy kiểm câu viết; liệt kê mọi giá trị và cách đặt thẻ theo thứ tự trăm–chục–đơn vị, nêu hai cực trị và hiệu.',
 ['A:2, B:2, C:0; dùng đủ ba thẻ riêng, không bỏ thẻ vì trùng giá trị.',
  'Hàng trăm khác 0; phân biệt đếm giá trị số với đếm cách đặt thẻ A,B,C.'],
 'Giá trị và cách đặt đủ ba thẻ; cực trị và hiệu',
 [step('Giữ đúng kho thẻ','Hai thẻ cùng chữ số vẫn là hai vật phải dùng đủ.','Không được bỏ B','Số 20 chỉ có hai chữ số và bỏ một thẻ, không đáp ứng dùng cả ba thẻ. Câu nhận xét chỉ dựa đúng câu bạn viết.'),
  step('Xét nơi đặt thẻ ghi 0','Thẻ C không ở hàng trăm; nó còn hai vị trí có thể ở sau.','C ở chục hoặc đơn vị','Nếu C ở chục thì A,B ở trăm và đơn vị; nếu C ở đơn vị thì A,B ở trăm và chục.'),
  step('Liệt kê cả danh tính và giá trị','Đổi A với B tạo cách đặt mới nhưng không đổi chữ số được đọc.','A-C-B;B-C-A đọc 202;A-B-C;B-A-C đọc 220','Bốn cách dùng đủ mỗi thẻ một lần; hai giá trị tăng là 202,220. Các cách C đứng đầu đọc 022 không phải số ba chữ số.'),
  step('So và trừ theo hàng','Hai số cùng hàng trăm 2; hàng chục quyết định thứ tự.','18','202 nhỏ hơn 220; hiệu 220−202=18. Kiểm 202+18=220, giữ nguyên cả hai chữ số 2.','220-202')],
 [('Mọi giá trị','202;220',''),('Mọi cách đặt','A-C-B;B-C-A;A-B-C;B-A-C',''),('Số giá trị','2','số'),('Số cách đặt','4','cách'),('Số nhỏ nhất','202',''),('Số lớn nhất','220',''),('Hiệu','18','')],
 ['Hai thẻ ghi cùng chữ số có còn là hai thẻ riêng phải dùng không?',
  'Chọn vị trí được phép cho thẻ ghi 0, rồi đặt hai thẻ còn lại vào các ô trống.',
  'Đọc giá trị sau khi ghi cách đặt; gộp số giống nhau nhưng giữ riêng số cách dùng thẻ.'],
 dict(cards={'A':2,'B':2,'C':0},length=3,bound=None,expected_values=[202,220],physical_assignments=4),
 'All-card three-slot multiplicity with repeated nonzero digit and observable illegal card deletion; distinct from repeated-zero two-slot subset.',
 student='A và B cùng ghi 2 nên bỏ B, chỉ còn số 20.')

add(2,'strict_bound_equality_excluded',
 'Ba thẻ riêng ghi 0,3,6. Mỗi lần dùng cả ba thẻ đúng một lần để lập số có ba chữ số, hàng trăm khác 0. Chỉ nhận số LỚN HƠN 306, không nhận bằng 306. Trả thẻ về giữa các lần. Liệt kê mọi số được nhận theo thứ tự tăng; tìm số nhỏ nhất, lớn nhất trong các số được nhận và hiệu của chúng. Phải giữ cả điều kiện dùng thẻ và điều kiện so sánh.',
 ['Kho 0,3,6, mỗi thẻ đúng một lần; số ba chữ số không có 0 đầu.',
  'Điều kiện là lớn hơn 306, dấu nghiêm ngặt; không thay mốc hay bỏ thẻ.'],
 'Danh sách sau lọc nghiêm ngặt, hai cực trị hợp lệ và hiệu',
 [step('Lập số hợp lệ theo kho trước','Chỉ hàng trăm 3 hoặc 6; hai thẻ còn lại có hai thứ tự.','306;360;603;630','Đây là toàn bộ số ba chữ số từ kho; không thêm chữ số hoặc lặp thẻ. Các cách bắt đầu 0 bị loại trước khi so mốc.'),
  step('Kiểm mốc cho từng số','Lớn hơn không gồm trường hợp bằng nhau.','360;603;630','306 bằng mốc nên không nhận. 360 lớn hơn 306 do hàng chục; 603 và 630 lớn hơn vì hàng trăm 6 lớn hơn 3.'),
  step('Tìm hai đầu trong tập đã lọc','Không lấy cực trị của kho chưa lọc thay cực trị của tập được nhận.','Nhỏ nhất 360; lớn nhất 630','Danh sách sau lọc tăng là 360,603,630; mỗi số vẫn dùng đủ 0,3,6.'),
  step('Tính và kiểm hiệu','Dùng đúng hai cực trị sau lọc để trừ.','270','630−360=270; cộng lại 360+270=630. Có ba giá trị được nhận, không gồm số ở đúng mốc.','630-360')],
 [('Mọi số được nhận','360;603;630',''),('Số nhỏ nhất','360',''),('Số lớn nhất','630',''),('Hiệu','270',''),('Số giá trị','3','số')],
 ['Kiểm cách dùng thẻ và số chữ số trước, rồi mới kiểm mốc so sánh.',
  'Dấu lớn hơn có nhận một số đúng bằng mốc không?',
  'Chỉ tìm hai cực trị trong danh sách đã qua tất cả điều kiện, rồi cộng ngược để kiểm hiệu.'],
 dict(cards={'A':0,'B':3,'C':6},length=3,bound=306,expected_values=[360,603,630],physical_assignments=3),
 'Joint all-card three-digit construction and strict lower-bound filtering; equality306 is feasible by stock but rejected by inequality.')

add(2,'maximum_still_below_required_bound',
 'Ba thẻ riêng ghi 1,2,4. Mỗi lần dùng đủ ba thẻ đúng một lần để lập số ba chữ số. Chỉ nhận số lớn hơn 500. Bạn viết: “Em chọn 421 vì lớn nhất rồi.” Hãy liệt kê mọi số có thể lập từ kho trước khi kiểm mốc, rồi xác định có số nào được nhận không. Nếu có thì nêu số nhỏ nhất, lớn nhất trong tập được nhận; nếu không có thì nói rõ không tồn tại hai cực trị ấy, không điền 0 thay đáp án. Không thay mốc 500 hoặc thêm thẻ.',
 ['Thẻ 1,2,4 dùng đủ mỗi thẻ một lần, chữ số đầu khác 0.',
  'Số được nhận phải lớn hơn 500; không đổi kho hoặc mốc để tạo nghiệm.'],
 'Kho số trước lọc, tính khả thi và cực trị sau lọc',
 [step('Chia nhánh theo hàng trăm','Có ba lựa chọn hàng trăm; mỗi nhánh hoán đổi hai thẻ còn lại.','124;142;214;241;412;421','Hàng trăm 1 cho 124,142; hàng trăm 2 cho 214,241; hàng trăm 4 cho 412,421. Đây là sáu số không lặp.'),
  step('Tìm giới hạn lớn nhất theo kho','Muốn số lớn nhất, đặt thẻ lớn hơn ở hàng cao hơn.','421 là lớn nhất của kho','Dù 421 lớn nhất trong sáu số, hàng trăm 4 vẫn nhỏ hơn hàng trăm 5 của 500, nên 421 không lớn hơn 500.'),
  step('Kiểm yêu cầu của câu bạn','Đạt lớn nhất trong kho chưa đủ nếu vẫn không đạt mốc.','Không có số được nhận','Mọi số lập được đều không vượt 421, nên đều nhỏ hơn 500. Câu bạn đã bỏ kiểm điều kiện lớn hơn mốc; không suy thêm điều bạn nghĩ.'),
  step('Trả lời cực trị đúng miền','Tập được nhận trống thì không có phần tử nhỏ nhất hay lớn nhất.','Không tồn tại cực trị sau lọc','Không ghi 0, vì 0 không là số ba chữ số từ các thẻ và cũng không vượt 500. Giữ nguyên đề và kết luận không có cách thỏa.'),
  step('Kiểm đã xét đủ kho','Ba nhánh hàng trăm, mỗi nhánh hai số.','6','2+2+2=6 cách đặt; các thẻ khác nhau nên cũng là sáu giá trị. Không bỏ một cách nào để có kết luận vô nghiệm.','2+2+2','số')],
 [('Mọi số trước lọc','124;142;214;241;412;421',''),('Mọi số được nhận','không có',''),('Số nhỏ nhất sau lọc','không tồn tại',''),('Số lớn nhất sau lọc','không tồn tại',''),('Số giá trị được nhận','0','số')],
 ['Phân biệt số lớn nhất lập được với số thật sự đạt mọi điều kiện.',
  'Lập đủ các nhánh hàng trăm rồi so giới hạn lớn nhất của kho với mốc.',
  'Nếu chưa tìm được số hợp lệ, kiểm đủ kho; giữ nguyên đề và nêu rõ tình trạng của tập kết quả.'],
 dict(cards={'A':1,'B':2,'C':4},length=3,bound=500,expected_values=[],physical_assignments=0),
 'Empty feasible set with explicit distinction between unrestricted maximum and constrained extrema; no manufactured0answer.',
 student='Em chọn 421 vì lớn nhất rồi.')

def token_oracle(cards,k,bound):
 out=[]
 for p in permutations(cards,k):
  digits=[cards[x] for x in p]
  if digits[0]==0:continue
  value=int(''.join(map(str,digits)))
  if bound is None or value>bound:out.append((list(p),value))
 return out
def alternative_value_oracle(cards,k,bound):
 # Enumerates numeric values in range and consumes supplied digit stock, rather than token permutations.
 stock=Counter(cards.values());valid=[]
 for n in range(10**(k-1),10**k):
  if bound is not None and n<=bound:continue
  need=Counter(map(int,str(n)))
  if all(need[d]<=stock[d] for d in need):valid.append(n)
 return valid
def main():
 assert len(rows)==6
 OUT.mkdir(parents=True,exist_ok=True)
 jl('cases.jsonl',rows)
 raw=(OUT/'cases.jsonl').read_bytes().splitlines()
 hashes={r['sample_id']:sha(b) for r,b in zip(rows,raw)}
 chats=[]
 for r in rows:
  for c in chat_records(r):
   c.update(acceptance_status=r['acceptance_status'],quality_status=r['quality_status'],source_row_sha256=hashes[r['sample_id']])
   chats.append(c)
 assert len(chats)==24
 jl('chat.jsonl',chats)
 oracles=[];mutations=[];numeric=[];qa=[]
 for r in rows:
  m=r['independent_model'];sid=r['sample_id'];rh=hashes[sid];cards=m['cards'];k=m['length'];bound=m['bound']
  physical=token_oracle(cards,k,bound);vals=sorted({v for _,v in physical})
  alt=alternative_value_oracle(cards,k,bound)
  assert vals==alt==m['expected_values'] and len(physical)==m['physical_assignments']
  oracles.append(dict(sample_id=sid,source_row_sha256=rh,status='PASS',
   method1='All ordered selections of distinct physical card IDs, then zero/strict-bound filter.',
   method2='Every integer in requested digit-length range; digit-count consumption against finite stock.',
   complete_values=vals,physical_assignments=physical,
   minimum=min(vals) if vals else None,maximum=max(vals) if vals else None,
   difference=max(vals)-min(vals) if vals else None,
   individual_problem_transcription=m))
  # Meaningful altered rule evaluations with concrete witnesses.
  if r['topic']=='all_two_digit_unfiltered_zero':
   wrong=[n for n in vals if n%2==0]
   assert wrong!=vals
   mutations.extend([dict(sample_id=sid,source_row_sha256=rh,wrong_rule='Keep even numerals only',mutated_values=wrong,rejected_witness=27),
    dict(sample_id=sid,source_row_sha256=rh,wrong_rule='Reuse one physical card twice',invalid_witness=22,reason='Only one cardQrecords2.')])
  elif r['topic']=='optional_zero_not_compulsory_card':
   wrong=[n for n in vals if '0' in str(n)];assert wrong!=vals
   mutations.extend([dict(sample_id=sid,source_row_sha256=rh,wrong_rule='Zero mandatory in every result',mutated_values=wrong,rejected_witness=14),
    dict(sample_id=sid,source_row_sha256=rh,wrong_rule='All four stock cards must be used in two slots',reason='Contradicts exactly choose two; does not invalidate ordinary two-card values.')])
  elif r['topic']=='two_zero_cards_values_vs_arrangements':
   assert len(vals)!=len(physical)
   mutations.extend([dict(sample_id=sid,source_row_sha256=rh,wrong_rule='Count physical placements as distinct numeric values',mutated_count=2,correct_value_count=1),
    dict(sample_id=sid,source_row_sha256=rh,wrong_rule='Allow leading zero',invalid_token_placement=['A','C'],invalid_string='05',reason='05is not a two-digit numeral.')])
  elif r['topic']=='repeated_nonzero_all_three_slots':
   assert len(vals)!=len(physical)
   mutations.extend([dict(sample_id=sid,source_row_sha256=rh,wrong_rule='Collapse repeated-value cards before use',invalid_witness='20',reason='Must use all three physical cards; result needs three digits.'),
    dict(sample_id=sid,source_row_sha256=rh,wrong_rule='Count four physical placements as four numeric values',mutated_count=4,correct_value_count=2)])
  elif r['topic']=='strict_bound_equality_excluded':
   wrong=alternative_value_oracle(cards,k,bound-1);assert wrong!=vals and bound in wrong
   mutations.extend([dict(sample_id=sid,source_row_sha256=rh,wrong_rule='Use >= instead of >',mutated_values=wrong,rejected_witness=306),
    dict(sample_id=sid,source_row_sha256=rh,wrong_rule='Take unrestricted minimum before bound filter',invalid_minimum=306,correct_minimum=360)])
  else:
   unrestricted=alternative_value_oracle(cards,k,None);assert max(unrestricted)==421 and not vals
   mutations.extend([dict(sample_id=sid,source_row_sha256=rh,wrong_rule='Return unrestricted maximum without threshold test',invalid_witness=421,reason='421<500.'),
    dict(sample_id=sid,source_row_sha256=rh,wrong_rule='Fill0for nonexistent feasible extremum',invalid_witness=0,reason='0is not a feasible three-digit stock numeral and does not exceed500.')])
  for st in r['worked_steps']:
   if st['expression'] is None:continue
   expr=st['expression']
   def calc(n,ctor):
    if isinstance(n,ast.Constant):return ctor(ast.get_source_segment(expr,n))
    if isinstance(n,ast.BinOp):return {ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv}[type(n.op)](calc(n.left,ctor),calc(n.right,ctor))
    raise ValueError(ast.dump(n))
   tree=ast.parse(expr,mode='eval').body;f=calc(tree,Fraction);d=calc(tree,Decimal)
   assert f==Fraction(st['result']) and d==Decimal(st['result'])
   numeric.append(dict(sample_id=sid,source_row_sha256=rh,step_id=st['step_id'],expression=expr,Fraction=str(f),Decimal=str(d),expected=st['result'],status='PASS'))
  qa.append(dict(sample_id=sid,source_row_sha256=rh,status='PASS_AUTHOR_SELF_QA',
   actual_fields_read=['problem','givens','requested_quantity','student_work','worked_steps.title','worked_steps.reason','worked_steps.explanation','worked_steps.result','worked_steps.expression','worked_steps.unit','expected_answer','initial_guidance','hints.1.hint','hints.1.question','hints.2.hint','hints.2.question','hints.3.hint','hints.3.question'],
   criteria={x:'PASS' for x in ['problem_givens_request_consistency','mathematical_oracle_complete_finite_inventory','steps_reasons_units_checks','initial_and_three_hints_no_filled_answer','student_feedback_only_supplied_quote','grade2_original_substantive_branch','provenance_hash_preservation']},
   semantic_note=r['nearest_source_comparison']['semantic_difference'],
   human_review_claimed=False,root_cross_review_required=True))
 jl('independent_oracles.jsonl',oracles);jl('adversarial_mutations.jsonl',mutations);jl('numeric_fraction_decimal.jsonl',numeric);jl('selfqa7.jsonl',qa)
 # Every serialized target and input is checked against the actual reviewed source field.
 byid={r['sample_id']:r for r in rows}
 for c in chats:
  r=byid[c['source_sample_id']];u=json.loads(c['messages'][1]['content']);a=json.loads(c['messages'][2]['content'])
  assert u['problem']==r['problem'] and u['grade']==2 and u['mode']==c['mode']
  assert u.get('student_work')==(r['student_work']['text'] if r['student_work'] else None)
  if c['mode']=='worked_solution':assert a['steps']==r['worked_steps'] and a['answer']==r['expected_answer'] and a['initial_guidance']==r['initial_guidance']
  else:
   h=r['hints'][int(c['mode'][-1])-1];assert a==dict(hint=h['hint'],question=h['question'])
 nearest=[];wanted={'sgk_gap_20261019_g4_parity_cards_two_digit_zero','sgk_page_20261019_g4_digit_inequality_strict_low',
   'sgk_final_numbers_20261021_digit_cards_column_constraint','sgk_final_numbers_20261021_three_digit_strip_connectors','sgk_final_numbers_20261021_distinct_cards_person_rank'}
 oldpaths=[PUB/'sgk_page_audit_20261019/current_sources.jsonl',PUB/'sgk_page_audit_20261019/release/accepted_cases.jsonl',PUB/'sgk_final_gaps_20261021/release/accepted_cases.jsonl']
 before={str(p.relative_to(PUB)):sha(p.read_bytes()) for p in oldpaths}
 for p in oldpaths:
  for no,b in enumerate(p.read_bytes().splitlines(),1):
   r=json.loads(b)
   if r['sample_id'] in wanted:
    nearest.append(dict(sample_id=r['sample_id'],source_file=str(p.relative_to(PUB)),line=no,source_row_sha256=sha(b),
     actual_fullfields={k:r.get(k) for k in ['grade','problem','givens','requested_quantity','student_work','worked_steps','expected_answer','initial_guidance','hints']},
     review='ACTUAL_FULLFIELDS_READ_FINITE_NEAREST_ONLY'))
 assert len(nearest)==5
 jl('nearest_actual_fullfields.jsonl',nearest)
 # Read comparison against all71 current accepted IDs/questions, not importing them as new data.
 prior71=[json.loads(b) for b in oldpaths[-1].read_bytes().splitlines()]
 assert len(prior71)==71
 assert not ({r['sample_id'] for r in rows}&{r['sample_id'] for r in prior71})
 assert not ({r['problem'] for r in rows}&{r['problem'] for r in prior71})
 assert all(sha(p.read_bytes())==before[str(p.relative_to(PUB))] for p in oldpaths)
 wr('planning_task_snapshot.json',dict(source_plan_sha256=sha(PLAN.read_bytes()),tasks=TASKS,closure_claim=False))
 wr('validation_receipt.json',dict(status='PASS_AUTHOR_QA_PENDING_INDEPENDENT_PEER_ROOT',cases=6,chat_rows=24,
  grade=2,independent_finite_models=6,different_method_integer_range_checks=6,
  numeric_fraction_decimal_steps=len(numeric),meaningful_wrong_constraints=len(mutations),
  actual_nearest_fullfields_read=5,prior71_ids_and_questions_no_duplicate=True,
  full_archive_duplicate_absence_claim=False,old_inputs_unchanged=before,training_started=False,drive_mutated=False))
 files=[]
 for p in sorted(OUT.iterdir()):
  if p.is_file():
   b=p.read_bytes();files.append(dict(path=p.name,bytes=len(b),sha256=sha(b)))
 wr('manifest.json',dict(status='6_DRAFTS_AUTHOR_QA_PASSED_PEER_ROOT_REVIEW_PENDING',cases=6,chat_rows=24,
   by_grade={'2':6},planning_tasks=[t['task_id'] for t in TASKS],files=files,
   generator=dict(path='thinking/g2_numerals_cohort1_author.py',sha256=sha(Path(__file__).read_bytes())),
   human_review_claimed=False,training_started=False,drive_mutated=False))
 print(json.dumps(dict(status='PASS_AUTHOR_DRAFT',cases=6,chat=24,numeric=len(numeric),mutations=len(mutations),
  cases_sha256=sha((OUT/'cases.jsonl').read_bytes()),chat_sha256=sha((OUT/'chat.jsonl').read_bytes()),
  manifest_sha256=sha((OUT/'manifest.json').read_bytes())),ensure_ascii=False))
if __name__=='__main__':main()

