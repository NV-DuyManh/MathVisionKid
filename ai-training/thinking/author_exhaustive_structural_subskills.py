"""Original additive structural cases; never writes the frozen primary corpus."""
import ast
import json
from pathlib import Path
from fractions import Fraction
from decimal import Decimal
from primary_math_data_pipeline import inspect_case, row_sha, write_rows, write_json, sha, exact

HERE = Path(__file__).resolve().parent
DEST = HERE/'data/exhaustive_math_v1/structural/curriculum_subskill_cases.jsonl'
E = HERE/'evidence/exhaustive_math_20261018'
SOURCE_SHA = 'f35d34ff84da2ca3f9ab72d5d67482ada414684b611deea98c4b329801b661ab'
SOURCE_URL = 'https://storage-vnportal.vnpt.vn/edu-vtu/4803/2023/Thongtu32/3.-chuong-trinh-mon-toan.pdf'
P = [
 ('current_g2_left_to_right_add_sub_explicit_subskill',['current_g2_addition_subtraction_carry_once'],2,25),
 ('current_g4_shape_construction_explicit_subskills',['current_g4_parallel_perpendicular','current_g4_practice_experience'],4,37),
 ('current_g5_grid_shapes_explicit_subskills',['current_g5_draw_altitude_circle'],5,43),
]
ROWS=[]

def S(title,reason,result,explanation,expression=None,unit=''):
 return dict(title=title,reason=reason,result=str(result),explanation=explanation,expression=expression,unit=unit)

def H(*texts):
 return [dict(level=i+1,hint=h,question=q) for i,(h,q) in enumerate(texts)]

def add(group,key,kind,problem,givens,request,steps,answers,hints,note,student=None):
 proposal,parents,grade,page=P[group]
 sid='exhaustive_structure_'+key
 hs=H(*hints)
 row=dict(sample_id=sid,case_group_id=sid,split='train',grade=grade,topic=key,problem=problem,
  givens=[dict(id='g'+str(i),text=t,value=v,unit=u,role='explicit_given') for i,(t,v,u) in enumerate(givens)],
  requested_quantity=request,student_work=None if student is None else dict(text=student,observations=[dict(excerpt=student,claim_scope='Explicit synthetic written evidence only; no hidden reasoning or unseen image inferred.')]),
  initial_guidance=[hs[0]['hint']],hints=hs,worked_steps=[dict(step_id='s'+str(i),**s) for i,s in enumerate(steps)],
  expected_answer=[dict(quantity=q,result=str(v),unit=u) for q,v,u in answers],can_solve=kind!='guard',
  canonical_case=dict(family=key,operations=[s['expression'] for s in steps if s['expression']],numeric_values=[v for _,v,_ in givens if v is not None]),
  curriculum_assignment=dict(node_id=parents[0],parent_node_ids=parents,additive_subskill_id=proposal,case_kind=kind,curriculum_scope='CURRENT_2018_OUTCOME_REFERENCE',coverage_mode='STRUCTURAL_COVERAGE',counts_toward_frozen_495_core=False),
  coverage=dict(mode='STRUCTURAL_COVERAGE',additive_subskill_id=proposal,case_kind=kind,finite_example_not_exhaustive_curriculum=True,actual_drawing_or_physical_mastery_verified=False),
  provenance=dict(authoring_method='original_AI_teacher',authoring_label='AI_GENERATED',authorship_origin='ORIGINAL_AI_AUTHORED',authoring_agent='/root/finite_grade4',source_role='AI_AUTHORED_ORIGINAL',human_verified=False,teacher_certified=False,owner_human_reviewed=False,independent_external_review=False,student_work_origin='EXPLICITLY_SYNTHETIC' if student else None,modality_evidence='ORIGINAL_TEXT_OR_EXPLICIT_HYPOTHETICAL_PLAN_ONLY',visual_asset_status='NOT_REQUIRED_FOR_EXPRESSION' if grade==2 else 'PENDING_ACTUAL_DRAWING_OR_PHYSICAL_EVIDENCE',source_evidence=dict(source_url=SOURCE_URL,source_payload_sha256=SOURCE_SHA,source_locator_pdf_pages_1based=[page],verification_status='ACTUAL_ANNEX_SUBSKILL_READ',current_2026_legal_currency_certified=False),accuracy_score=None,accuracy_score_reason='No empirical accuracy estimate assigned; AI origin is provenance, not a low-accuracy label.'),
  quality_status='ACCEPTED_AUTHOR_SELF_QA',acceptance_status='ACCEPTED_OWNER_PREAUTHORIZED',quality_flags=dict(training_started=False,physical_success_claimed=False,legal_curriculum_completeness_claimed=False),
  author_QA_specific_note=note)
 assert inspect_case(row)['passed'],(sid,inspect_case(row))
 ROWS.append(row)

add(0,'g2_two_sign_bare_expression','core',
 'Tính giá trị biểu thức 48 + 25 − 13 theo thứ tự từ trái sang phải. Nêu phép kiểm cho kết quả cuối.',
 [('Biểu thức','48+25-13','')],'Giá trị biểu thức và phép kiểm',[
 S('Thực hiện dấu bên trái','Biểu thức chỉ có cộng và trừ, không có ngoặc nên làm lần lượt từ trái sang phải.',73,'Cộng 48 với 25 được 73; hàng đơn vị đổi một chục và cộng phần nhớ vào hàng chục.','48+25'),
 S('Dùng kết quả vừa có','Dấu trừ tác động vào kết quả của phép cộng đã thực hiện.',60,'Lấy 73 bớt 13 còn 60, không đổi vị trí hai dấu.','73-13'),
 S('Kiểm ngược','Cộng lại phần đã bớt phải khôi phục kết quả trung gian.',73,'60 + 13 = 73; tiếp đó 73 − 25 = 48 khôi phục số đầu.','60+13')],
 [('Giá trị biểu thức',60,'')],[('Xác định dấu phép tính nằm bên trái trước.','Trong biểu thức này, dấu nào được thực hiện trước?'),('Giữ kết quả của phép tính đầu để thực hiện tiếp dấu còn lại.','Em dùng kết quả trung gian với số còn lại như thế nào?'),('Đi ngược từng phép tính để đối chiếu số ban đầu.','Các phép kiểm ngược có khôi phục được số xuất phát không?')],
 'Read actual fields: 48+25=73 has one units carry; 73−13=60 no borrow. Final answer 60; reverse restores 48. Hints do not expose 73/60 or a substituted solution.')

add(0,'g2_two_sign_arrow_machine','core',
 'Một sơ đồ tính ghi: 96 → bớt 34 → thêm 18. Viết biểu thức tương ứng không có ngoặc, tính theo chiều mũi tên và kiểm ngược.',
 [('Số xuất phát','96',''),('Lệnh thứ nhất','bớt 34',''),('Lệnh thứ hai','thêm 18','')],'Biểu thức, kết quả và kiểm ngược',[
 S('Đọc mũi tên đầu','Lệnh bớt được thực hiện trước vì nằm trước trên sơ đồ.',62,'Biểu thức là 96 − 34 + 18. Trước hết 96 − 34 = 62.','96-34'),
 S('Thực hiện mũi tên tiếp','Lệnh thêm sử dụng số sau mũi tên đầu.',80,'62 + 18 = 80; hàng đơn vị có một lượt nhớ.','62+18'),
 S('Đi ngược sơ đồ','Đảo lệnh thêm thành bớt để kiểm rồi đảo lệnh bớt thành thêm.',62,'80 − 18 = 62 và 62 + 34 = 96, đúng số xuất phát.','80-18')],
 [('Giá trị sau hai lệnh',80,'')],[('Đọc các mũi tên theo đúng chiều đã cho.','Lệnh nào tác động lên số xuất phát trước?'),('Chỉ chuyển sang lệnh tiếp theo sau khi giữ lại kết quả trung gian.','Số đi vào mũi tên sau là số nào trong bài làm của em?'),('Đảo thứ tự các lệnh và dùng phép tính ngược để kiểm.','Đi ngược sơ đồ có đưa em về số xuất phát không?')],
 'Arrow representation rather than a two-step word-problem outcome. Exact sequential results 62,80; inverse 62+34=96. Each operation <=one exchange, in 1000.')

add(0,'g2_two_sign_equal_value_contrast','core',
 'Hai thẻ ghi A: 265 + 120 − 54 và B: 265 − 54 + 120. Tính từng thẻ từ trái sang phải rồi đối chiếu giá trị, không đổi thứ tự dấu trong mỗi thẻ.',
 [('Thẻ A','265+120-54',''),('Thẻ B','265-54+120','')],'Giá trị mỗi thẻ và nhận xét đối chiếu',[
 S('Theo thứ tự của thẻ A','Cộng ở bên trái trước rồi bớt số cuối.',385,'265 + 120 = 385; tiếp đó bớt 54.','265+120'),
 S('Hoàn tất thẻ A','Giữ nguyên số trừ ở dấu thứ hai.',331,'385 − 54 = 331.','385-54'),
 S('Theo thứ tự của thẻ B','Thẻ B có dấu trừ bên trái nên bớt trước.',211,'265 − 54 = 211, sau đó mới cộng 120.','265-54'),
 S('Hoàn tất và đối chiếu','Tính riêng thẻ B để so với thẻ A, không suy ra bằng việc tự đổi thứ tự.',331,'211 + 120 = 331, bằng giá trị thẻ A. Kiểm: 331 + 54 = 385 và 331 − 120 = 211.','211+120')],
 [('Giá trị thẻ A',331,''),('Giá trị thẻ B',331,'')],[('Theo dõi thứ tự riêng của từng thẻ.','Dấu nằm bên trái của mỗi thẻ là dấu nào?'),('Ghi riêng hai kết quả trung gian để tránh trộn các thẻ.','Số cuối của mỗi thẻ tác động lên kết quả trung gian nào?'),('Chỉ so sánh sau khi đã hoàn tất cả hai thẻ.','Các phép kiểm ngược xác nhận giá trị từng thẻ như thế nào?')],
 'Distinct contrast task, not parameter-only clone: computes both orderings 385−54 and211+120 to same331; no generic claim that arbitrary subtraction commutes. All intermediate operations have no exchange.')

add(0,'g2_two_sign_observed_parentheses_error','misconception',
 'Tính 75 − 20 + 6 theo thứ tự từ trái sang phải. Một lời làm giả định được chép nguyên văn dưới đây. Chỉ nhận xét điều được viết và sửa phép tính.',
 [('Biểu thức không có ngoặc','75-20+6','')],'Nhận xét lời làm được cho, sửa và kiểm',[
 S('Đối chiếu với đề','Chỉ có thể nhận xét phép biến đổi đã viết; đề không có ngoặc.', 'Đã thêm ngoặc làm đổi biểu thức','Dòng “75 − (20 + 6)” khác biểu thức của đề; không có bằng chứng nào về suy nghĩ hay thao tác khác của bạn.'),
 S('Tính dấu bên trái','Cộng và trừ không có ngoặc được thực hiện từ trái sang phải.',55,'75 − 20 = 55.','75-20'),
 S('Hoàn tất rồi kiểm','Cộng số cuối vào kết quả trung gian và kiểm ngược.',61,'55 + 6 = 61; kiểm 61 − 6 = 55, rồi 55 + 20 = 75.','55+6')],
 [('Giá trị đúng',61,'')],[('So sánh dấu ngoặc trong lời làm với biểu thức của đề.','Lời làm đã giữ nguyên cấu trúc biểu thức được cho chưa?'),('Bắt đầu ở phép tính bên trái rồi giữ kết quả trung gian.','Sau bước đầu, em còn phải thực hiện dấu nào?'),('Dùng phép ngược theo thứ tự ngược để kiểm.','Phép kiểm có đưa em về số đầu của biểu thức không?')],
 'Feedback grounded solely in explicit synthetic quote adding parentheses. Correct55 then61; quote49 stays in student evidence, not silently changed.',
 student='Em tính 75 − (20 + 6) = 75 − 26 = 49.')

add(0,'g2_two_sign_missing_operator','guard',
 'Một bản chép chỉ còn biểu thức “42 □ 8 − 5”; ô vuông che mất dấu đầu tiên và không có ảnh bản gốc. Hãy cho giá trị đúng duy nhất của biểu thức này.',
 [('Bản chép bị che dấu','42 □ 8 − 5',''),('Ảnh bản gốc',None,'')],'Hỏi dấu bị che trước khi xác định một giá trị',[],[],
 [('Xác định thông tin cần có ở vị trí ô vuông.','Em có thể cung cấp dấu bị che hoặc ảnh rõ của biểu thức gốc không?'),('Các dấu khác nhau có thể tạo thành các biểu thức khác nhau.','Nguồn nào xác nhận dấu đầu tiên của bản gốc?'),('Sau khi đọc được dấu, mới theo thứ tự tính của biểu thức hoàn chỉnh.','Em đã xác nhận được biểu thức đầy đủ trước khi tính chưa?')],
 'Meaningful insufficient-expression guard: no unique value while first operator hidden. No worked steps or answer, asks actual missing sign/image without guessing.')

add(1,'g4_rectangle_stencil_plan','core',
 'Lập kế hoạch vẽ một miếng bìa hình chữ nhật dài 6 cm, rộng 3 cm bằng thước thẳng và êke. Chỉ mô tả cách làm và cách kiểm, chưa có sản phẩm hay ảnh để xác nhận thao tác thực tế.',
 [('Chiều dài','6','cm'),('Chiều rộng','3','cm'),('Dụng cụ','thước thẳng và êke','')],'Kế hoạch dựng hình và kiểm kích thước, góc',[
 S('Dựng cạnh đầu và hai phương vuông góc','Hai cạnh kề hình chữ nhật gặp nhau ở góc vuông.', 'Vẽ AB rồi dựng hai đường vuông góc','Dự kiến vẽ AB dài 6 cm. Đặt góc vuông của êke tại A, một cạnh trùng AB, kẻ tia vuông góc; làm tương tự tại B về cùng một phía.'),
 S('Đánh dấu chiều rộng và nối cạnh còn lại','Hai cạnh bên phải bằng chiều rộng đã cho.', 'Đặt D và C rồi nối DC','Dự kiến lấy AD = BC = 3 cm trên hai tia, nối D với C. Thứ tự đường bao là A–B–C–D–A.'),
 S('Kiểm bản vẽ sau khi thực hiện','Kích thước và góc vuông đều phải phù hợp, chỉ nhìn gần giống chưa đủ.', 'Đo cạnh và áp êke kiểm góc','Sau khi có bản vẽ, dùng thước kiểm AB = DC = 6 cm, AD = BC = 3 cm; áp êke kiểm từng góc. Hiện đây chỉ là kế hoạch, chưa xác nhận bản vẽ đã đạt.')],
 [('Kế hoạch','AB = DC = 6 cm; AD = BC = 3 cm; bốn góc vuông; kiểm bằng thước và êke','')],[('Xác định một cạnh làm mốc và dụng cụ kiểm góc.','Em sẽ chọn cạnh nào để bắt đầu dựng hình?'),('Dùng chiều rộng đã cho để đánh dấu trên các phương thích hợp.','Các điểm mới cần nằm cùng phía hay khác phía cạnh mốc?'),('Kiểm riêng độ dài và quan hệ giữa các cạnh sau khi vẽ.','Em dùng thước và êke để kiểm từng yêu cầu như thế nào?')],
 'Construction plan uses adjacent perpendicular rays same side, equal width, closure correct. Numeric lengths only in requested plan, no actual image/drawing success claim.')

add(1,'g4_parallel_guide_plan','core',
 'Trên một tờ giấy giả định có đường thẳng d và điểm P không nằm trên d. Lập kế hoạch dùng thước thẳng và êke kẻ đường đi qua P song song với d để làm đường dẫn gấp. Chưa có ảnh hoặc thao tác thực tế.',
 [('Đường đã có','d',''),('Điểm','P không thuộc d',''),('Dụng cụ','thước thẳng và êke','')],'Kế hoạch kẻ song song và cách kiểm',[
 S('Giữ hướng của êke','Trượt êke dựa trên thước giữ hướng cạnh kẻ không đổi.', 'Đặt thước làm thanh dẫn','Dự kiến đặt một cạnh êke trùng d, đặt thước tựa cạnh khác của êke rồi giữ thước cố định.'),
 S('Dịch đến điểm cần đi qua','Đường mới phải vừa đúng hướng vừa qua P.', 'Trượt êke đến P rồi kẻ','Trượt êke dọc thước, không xoay êke, đến khi cạnh từng trùng d đi qua P; kẻ theo cạnh đó.'),
 S('Kiểm hai điều kiện','Qua điểm và song song là hai yêu cầu cần kiểm riêng.', 'Kiểm qua P và kiểm hướng','Sau khi có nét vẽ, kiểm nó qua P; có thể dựng cùng một đường vuông góc với d và dùng êke kiểm đường mới cũng vuông góc với đường kiểm ấy. Kế hoạch chưa chứng minh thao tác đã thực hiện đúng.')],
 [('Kế hoạch','Giữ thước cố định, trượt êke không xoay, kẻ qua P và kiểm quan hệ song song','')],[('Phân biệt điều kiện đi qua điểm với điều kiện về hướng.','Đường cần kẻ phải thỏa những điều kiện nào?'),('Chọn cách giữ nguyên hướng của dụng cụ trong khi dịch chuyển.','Em giữ bộ phận nào cố định để êke không bị xoay?'),('Lập cách kiểm sau khi có nét vẽ.','Em sẽ kiểm riêng vị trí điểm và quan hệ giữa hai đường như thế nào?')],
 'Distinct sliding-square parallel construction. “Other edge” does not require right-angle selection for guide, but output edge remains parallel on translation; shared-perpendicular check valid in plane.')

add(1,'g4_cube_frame_assembly_plan','core',
 'Lập kế hoạch ghép mô hình khung hình lập phương bằng các đoạn ống hút đều dài 4 cm và nút nối ở các đỉnh. Mỗi cạnh dùng một đoạn, mỗi đỉnh dùng một nút. Chỉ tính vật liệu lý tưởng và mô tả kế hoạch; chưa có mô hình thực.',
 [('Cạnh mỗi đoạn','4','cm'),('Quy ước','mỗi cạnh một đoạn, mỗi đỉnh một nút','')],'Số đoạn, số nút và kế hoạch kiểm khung',[
 S('Đếm cạnh dùng chung','Mỗi trong sáu mặt có bốn cạnh nhưng mỗi cạnh thuộc hai mặt.',12,'Đếm theo mặt được 6 × 4, chia 2 để bỏ đếm lặp mỗi cạnh. Cần 12 đoạn ống hút.','6*4/2','đoạn'),
 S('Đếm đỉnh dùng chung','Mỗi mặt có bốn đỉnh, mỗi đỉnh thuộc ba mặt.',8,'6 × 4 : 3 = 8 nút nối, không dùng một nút riêng cho mỗi lần xuất hiện trên mặt.','6*4/3','nút'),
 S('Lập kế hoạch ghép và kiểm','Các cạnh bằng nhau chưa đủ; mô hình cần đúng cấu trúc và góc của hình lập phương.', 'Ghép hai khung vuông rồi nối các đỉnh tương ứng','Dự kiến ghép hai khung vuông bằng 8 đoạn; dùng 4 đoạn còn lại nối các đỉnh tương ứng. Khi có mô hình, kiểm mỗi đỉnh nối ba cạnh, các cạnh dài 4 cm và các mặt là hình vuông; chưa xác nhận sản phẩm thực tế.')],
 [('Số đoạn',12,'đoạn'),('Số nút',8,'nút')],[('Phân biệt cạnh hay đỉnh của khối với lần chúng xuất hiện trên mỗi mặt.','Những phần nào được các mặt dùng chung?'),('Điều chỉnh phần đếm lặp trước khi lập danh sách vật liệu.','Một cạnh và một đỉnh xuất hiện ở bao nhiêu mặt?'),('Chọn trình tự ghép và kiểm các mặt của khung.','Sau khi ghép, em sẽ kiểm những điều kiện hình học nào?')],
 'Distinct solid assembly plan. Edge-incidence24/2=12, vertex-incidence24/3=8; two square loops8 plus4crosslinks12. No claim sticks alone force right angles or actual assembly success.')

add(1,'g4_cube_faces_observed_count_error','misconception',
 'Dự kiến làm một hộp kín dạng hình lập phương, mỗi mặt dùng đúng một tấm bìa hình vuông cạnh 4 cm; các tấm không chồng lên nhau. Hiện có 5 tấm. Nhận xét lời viết giả định dưới đây và tính số tấm cần bổ sung, chưa có mô hình để quan sát.',
 [('Tấm đang có','5','tấm'),('Cạnh tấm vuông','4','cm')],'Nhận xét chứng cứ được viết và số tấm còn thiếu',[
 S('Đối chiếu số mặt cần che kín','Hình lập phương có sáu mặt; mỗi mặt cần một tấm theo quy ước.', 'Lời khẳng định đủ tấm chưa phù hợp','Câu viết cho rằng 5 tấm đủ che kín nhưng đề yêu cầu che từng mặt của khối có 6 mặt. Đây là nhận xét về số tấm được viết, không suy đoán cách bạn đã ghép.'),
 S('Tìm số tấm còn thiếu','Lấy số tấm cần dùng bớt số đã có.',1,'6 − 5 = 1 tấm. Kiểm 5 + 1 = 6 tấm, đủ về số lượng; còn phải kiểm cách bố trí khi có mô hình.','6-5','tấm')],
 [('Số tấm cần thêm',1,'tấm')],[('Đối chiếu yêu cầu hộp kín với các mặt của khối.','Em cần lập danh sách những mặt nào phải được che?'),('So sánh số tấm theo quy ước với số đang có.','Hai số lượng trong đề liên hệ với nhau như thế nào?'),('Kiểm phép tính bằng cách ghép số đang có với phần bổ sung.','Tổng số tấm sau bổ sung có phù hợp danh sách mặt không?')],
 'Explicit synthetic quote sufficient to diagnose count claim only. 6−5=1 tấm; no assertion any actual net folds successfully. Distinct count misconception rather than unseen image critique.',
 student='Em có 5 tấm bìa nên đủ làm kín mọi mặt của hình lập phương.')

add(1,'g4_perpendicular_missing_drawing_guard','guard',
 'Em nói đã dùng êke vẽ một đường qua P vuông góc với d và muốn xác nhận bản vẽ đúng. Tin nhắn chưa kèm ảnh, bản vẽ hay số đo góc. Hãy đánh giá nét vẽ của em.',
 [('Ảnh hoặc bản vẽ',None,''),('Số đo góc',None,'')],'Yêu cầu ảnh hoặc dữ liệu kiểm góc và vị trí',[],[],
 [('Tách điều em mô tả đã làm khỏi bằng chứng về sản phẩm.','Em có thể gửi bản vẽ rõ các đường, điểm và vị trí đặt êke không?'),('Cần kiểm điểm đường mới đi qua và góc với đường đã có.','Em có thể cung cấp số đo góc hoặc ảnh áp góc vuông của êke không?'),('Chỉ đối chiếu từng điều kiện khi có bằng chứng tương ứng.','Tài liệu em bổ sung đã thể hiện cả điểm cần đi qua và góc giao nhau chưa?')],
 'Real missing-drawing guard; no invented observation or verdict, empty worked steps/answers, targeted asks point and angle evidence.')

GRID='Trên lưới ô vuông, ghi vị trí bằng số ô sang phải và số ô lên trên tính từ điểm gốc O; đây là hướng dẫn đếm ô, không yêu cầu dùng công thức tọa độ. '
add(2,'g5_grid_trapezoid_plan','core',
 GRID+'A ở O; B cách O 6 ô sang phải; D cách O 1 ô sang phải và 3 ô lên; C cách O 4 ô sang phải và 3 ô lên. Lập kế hoạch nối A–B–C–D–A, kiểm cặp cạnh song song và đếm khoảng cách giữa hai đường chứa chúng. Chưa có hình vẽ thực.',
 [('A','0 phải; 0 lên','ô'),('B','6 phải; 0 lên','ô'),('C','4 phải; 3 lên','ô'),('D','1 phải; 3 lên','ô')],'Kế hoạch vẽ và khoảng cách giữa hai đáy',[
 S('Đánh dấu và nối theo đường bao','Nối đúng thứ tự tránh nhảy qua một đỉnh làm đổi hình.', 'Đánh dấu bốn điểm rồi nối A–B–C–D–A','A và B cùng hàng lưới dưới; D và C cùng hàng lưới phía trên. Dự kiến nối lần lượt các cặp đỉnh liên tiếp.'),
 S('Kiểm phương hai đáy','Các đoạn nằm theo hai hàng ngang khác nhau có cùng phương.', 'AB song song DC','AB dài 6 ô; DC kéo từ cột đếm 1 đến cột đếm 4 nên dài 3 ô. Cạnh bên AD và BC nghiêng theo hai hướng khác nhau, không tạo thêm cặp song song.'),
 S('Đếm chiều cao trên lưới','Khoảng cách hai đường song song được đo theo phương vuông góc, không theo cạnh nghiêng.',3,'Từ hàng ngang chứa AB lên hàng chứa DC đi thẳng đứng 3 ô. Có thể kiểm bằng một đường dọc lưới cắt cả hai hàng. Đây là kiểm mô tả, chưa kiểm ảnh vẽ thực.','3-0','ô')],
 [('Khoảng cách hai đường chứa đáy',3,'ô'),('Kế hoạch','Nối A–B–C–D–A; kiểm AB song song DC theo hai hàng ngang','')],[('Đánh dấu từng điểm bằng cách đếm ô ngang rồi ô dọc.','Những điểm nào nằm trên cùng một hàng lưới?'),('Theo thứ tự đường bao rồi đối chiếu hướng các cạnh.','Cặp cạnh nào cần kiểm để đối chiếu yêu cầu về hai đáy?'),('Đo khoảng cách theo phương vuông góc với các đường chứa đáy.','Em có thể dùng hướng nào của lưới để kiểm khoảng cách đó?')],
 'Offsets not formal analytic geometry. Exact grid oracle: horizontal bases6,3, height3; side displacement(1,3) vs(−2,3) nonparallel. Shoelace13.5 only QA, not unasked student target.')

add(2,'g5_grid_parallelogram_transfer','core',
 GRID+'A ở O; B ở 5 ô sang phải; D ở 2 ô sang phải và 3 ô lên; C ở 7 ô sang phải và 3 ô lên. Mô tả cách vẽ hình bình hành ABCD và cách kiểm bằng sự dịch chuyển trên lưới. Chưa có sản phẩm.',
 [('A','0 phải; 0 lên','ô'),('B','5 phải; 0 lên','ô'),('C','7 phải; 3 lên','ô'),('D','2 phải; 3 lên','ô')],'Kế hoạch vẽ và kiểm hai cặp cạnh đối',[
 S('Dựng hai đoạn ngang','Hai cạnh đối phải cùng hướng và cùng độ dài.', 'Vẽ AB và DC theo các hàng ngang','Dự kiến đánh dấu A, B rồi D, C trên hàng cao hơn; AB đi sang phải 5 ô, DC cũng đi sang phải 5 ô.'),
 S('Nối các cạnh bên','Hai đường dịch chuyển giống nhau cho hai cạnh bên cùng hướng và cùng độ dài.', 'Nối AD và BC','Từ A đến D đi 2 ô sang phải, 3 ô lên; từ B đến C cũng như vậy. Vì thế AD song song BC và bằng nhau theo cùng mẫu lưới.'),
 S('Kiểm khép kín','Cần đủ hai cặp cạnh đối trước khi kết luận kế hoạch phù hợp.', 'Đường bao A–B–C–D–A có hai cặp cạnh đối song song','Kiểm lại bằng cách đếm từ D đến C rồi từ A đến B, và từ A đến D rồi từ B đến C. Không chỉ dựa vào nét nghiêng trông giống hình bình hành; chưa xác nhận nét vẽ thực tế.')],
 [('Kế hoạch','AB và DC cùng ngang 5 ô; AD và BC cùng dịch 2 ô phải, 3 ô lên; nối đúng đường bao','')],[('So sánh vị trí các đoạn dự kiến làm cạnh đối.','Hai đoạn ngang được xác định từ những điểm nào?'),('Đếm phần ngang và phần dọc của từng cạnh bên.','Mẫu dịch chuyển của hai cạnh bên có trùng nhau không?'),('Kiểm đủ cả hai cặp cạnh đối và thứ tự nối.','Em đã đối chiếu mọi điều kiện cần cho hình yêu cầu chưa?')],
 'Distinct translation representation. Independent vector equality AB=DC(5,0),AD=BC(2,3); nonzeroarea15. Not one-pair-only misconception; no formal vector lesson in student answer.')

add(2,'g5_grid_rhombus_reflection','core',
 GRID+'L ở 1 ô phải, 3 ô lên; T ở 5 ô phải, 6 ô lên; R ở 9 ô phải, 3 ô lên; B ở 5 ô phải, cùng hàng với O. Lập kế hoạch nối L–T–R–B–L thành hình thoi và giải thích cách kiểm bốn cạnh bằng mẫu đếm ô; không đoán độ dài đường chéo ô bằng cách cộng số ô ngang với số ô dọc.',
 [('L','1 phải; 3 lên','ô'),('T','5 phải; 6 lên','ô'),('R','9 phải; 3 lên','ô'),('B','5 phải; 0 lên','ô')],'Kế hoạch và cách kiểm bốn cạnh bằng nhau',[
 S('Đánh dấu các đỉnh đối xứng','Các điểm đối xứng theo đường lưới giúp tạo các cạnh có cùng mẫu.', 'Đánh dấu L, T, R, B rồi nối theo đường bao','L và R cùng hàng; T và B cùng cột. Từ tâm giao hai đường ấy, các điểm trái/phải và trên/dưới được đếm đối xứng.'),
 S('Đối chiếu mẫu của các cạnh','Đường chéo của các hình chữ nhật ô lưới có cùng kích thước sẽ bằng nhau, dù đổi hướng.', 'Bốn cạnh cùng mẫu 4 ô ngang và 3 ô dọc','LT đi 4 ô phải và 3 ô lên; TR đi 4 ô phải và 3 ô xuống; RB đi 4 ô trái và 3 ô xuống; BL đi 4 ô trái và 3 ô lên. Đây là bốn đường chéo của các hình chữ nhật ô lưới bằng nhau, không phải mỗi cạnh dài 4 + 3 ô.'),
 S('Kiểm điều kiện của hình cần vẽ','Bốn cạnh bằng nhau là điều kiện nhận biết hình thoi trong kế hoạch này.', 'Kiểm đủ bốn cạnh và thứ tự nối','Đếm lại bốn mẫu, kiểm các điểm đã ở đúng giao điểm lưới và đường bao không tự cắt. Chưa có bản vẽ thực để xác nhận thao tác.')],
 [('Kế hoạch','Nối L–T–R–B–L; kiểm bốn cạnh bằng cùng mẫu đường chéo hình chữ nhật 4 ô và 3 ô','')],[('Đếm vị trí các đỉnh từ cùng một điểm mốc.','Các cặp điểm đối diện được đặt theo hàng và cột ra sao?'),('So sánh mẫu ô ngang và ô dọc mà mỗi cạnh đi qua.','Em nhận ra những hình chữ nhật ô lưới nào có cùng kích thước?'),('Kiểm bằng mẫu hình bằng nhau và tránh cộng độ dời ngang với dọc thành độ dài cạnh nghiêng.','Cách kiểm của em đã đối chiếu đủ mọi cạnh của đường bao chưa?')],
 'Grid reflects4×3 rectangles giving congruent diagonals without teaching Pythagoras. QA squarededges25each andshoelace24, diagonals8&6 verify. No numeric side5 in student answer; no false Manhattan7.')

add(2,'g5_grid_observed_rhombus_criterion_error','misconception',
 GRID+'A ở O; B ở 4 ô phải; C ở 4 ô phải, 2 ô lên; D ở 2 ô lên, cùng cột O. Xét lời viết giả định dưới đây, chỉ dựa các vị trí đã cho. Nêu điều cần sửa trong cách nhận biết hình thoi, chưa có ảnh để nhận xét nét vẽ.',
 [('A','0 phải; 0 lên','ô'),('B','4 phải; 0 lên','ô'),('C','4 phải; 2 lên','ô'),('D','0 phải; 2 lên','ô')],'Nhận xét tiêu chí được viết và đối chiếu độ dài cạnh',[
 S('Đối chiếu tiêu chí được phát biểu','Góc vuông không thay thế yêu cầu bốn cạnh bằng nhau của hình thoi.', 'Không đủ căn cứ từ bốn góc vuông','Chỉ nhận xét câu viết: viện dẫn bốn góc vuông chưa chứng minh bốn cạnh bằng nhau. Không kết luận bạn đã đặt thước hay đếm ô sai vì không có chứng cứ ấy.'),
 S('Đếm một cặp cạnh kề','Độ dài hai cạnh kề trên hàng và cột lưới đọc trực tiếp bằng số ô.',4,'AB dài 4 ô.','4-0','ô'),
 S('Đối chiếu cạnh bên và kiểm','Hai cạnh kề khác nhau bác bỏ điều kiện tất cả cạnh bằng nhau.',2,'BC dài 2 ô, khác AB dài 4 ô. Các vị trí cho hình chữ nhật không có bốn cạnh bằng nhau; vậy lời nhận là hình thoi không phù hợp dữ kiện.','2-0','ô')],
 [('Nhận xét','Bốn góc vuông chưa đủ; AB dài 4 ô, BC dài 2 ô nên hình này không có bốn cạnh bằng nhau','')],[('Đọc đúng tiêu chí mà lời viết đang dùng.','Tiêu chí đó đã đề cập điều kiện về độ dài các cạnh chưa?'),('Dùng số ô để đối chiếu các cạnh kề theo hai hướng lưới.','Em cần đếm những đoạn nào để kiểm điều kiện của hình yêu cầu?'),('Tách nhận xét về câu viết khỏi nhận xét thao tác chưa có ảnh.','Kết luận nào của em được các dữ kiện đếm ô trực tiếp hỗ trợ?')],
 'Explicit quote four rightangles=>rhombus; counterexample side4and2 grounded in supplied offsets, no unseen image claim. Rectanglesquare boundary respected: not every rectangle isrhombus.',
 student='Em gọi ABCD là hình thoi vì hình có bốn góc vuông.')

add(2,'g5_grid_missing_picture_guard','guard',
 'Em đã vẽ một hình thang trên lưới ô vuông và hỏi: “Các đỉnh và hai đáy trong hình của em đúng chưa?”. Tin nhắn không có ảnh, mô tả vị trí đỉnh hoặc số ô đã đếm. Hãy nhận xét bản vẽ.',
 [('Ảnh lưới và các đỉnh',None,''),('Vị trí các đỉnh',None,'')],'Yêu cầu bản vẽ hoặc mô tả đếm ô để kiểm',[],[],
 [('Cần dữ liệu cho biết vị trí các đỉnh và thứ tự nối.','Em có thể gửi ảnh rõ lưới và nhãn đỉnh hoặc mô tả từng vị trí bằng số ô không?'),('Từ dữ liệu bổ sung mới xác định được hướng các cạnh đối.','Mô tả của em cho biết rõ thứ tự nối và cặp cạnh được chọn làm đáy chưa?'),('Đối chiếu yêu cầu với đúng bản vẽ được cung cấp.','Thông tin bổ sung đã đủ để kiểm vị trí đỉnh và quan hệ các cạnh chưa?')],
 'Missingactualgrid guard: asks image or equivalent explicit offsets and vertex order; empty answers/steps, no verdict or invented geometry.')

def decimal_eval(expression):
 def walk(node):
  if isinstance(node,ast.Constant):return Decimal(str(node.value))
  x,y=walk(node.left),walk(node.right)
  if isinstance(node.op,ast.Add):return x+y
  if isinstance(node.op,ast.Sub):return x-y
  if isinstance(node.op,ast.Mult):return x*y
  if isinstance(node.op,ast.Div):return x/y
  raise ValueError('Unsupported arithmetic')
 return walk(ast.parse(expression,mode='eval').body)

def build():
 assert not DEST.exists(), 'Never duplicate or overwrite an existing batch'
 assert len(ROWS)==15 and len({r['sample_id'] for r in ROWS})==15
 arithmetic=[]
 for row in ROWS:
  assert inspect_case(row)['passed']
  for s in row['worked_steps']:
   if not s['expression']:continue
   f=exact(s['expression']);d=decimal_eval(s['expression'])
   assert f==Fraction(s['result']) and d==Decimal(f.numerator)/Decimal(f.denominator)
   arithmetic.append(dict(sample_id=row['sample_id'],row_sha256=row_sha(row),step_id=s['step_id'],expression=s['expression'],fraction=str(f),decimal=str(d)))
 # Separate grid oracle uses exact polygon determinants and squared lengths;
 # these are reviewer-only computations, not grade5 teaching requirements.
 grids={
  'g5_grid_trapezoid_plan':[(0,0),(6,0),(4,3),(1,3)],
  'g5_grid_parallelogram_transfer':[(0,0),(5,0),(7,3),(2,3)],
  'g5_grid_rhombus_reflection':[(1,3),(5,6),(9,3),(5,0)],
  'g5_grid_observed_rhombus_criterion_error':[(0,0),(4,0),(4,2),(0,2)],
 }
 oracle=[]
 for key,points in grids.items():
  vectors=[(points[(i+1)%4][0]-points[i][0],points[(i+1)%4][1]-points[i][1]) for i in range(4)]
  sq=[x*x+y*y for x,y in vectors]
  cross=lambda u,v:u[0]*v[1]-u[1]*v[0]
  parallel=[cross(vectors[0],vectors[2])==0,cross(vectors[1],vectors[3])==0]
  area=abs(Fraction(sum(points[i][0]*points[(i+1)%4][1]-points[(i+1)%4][0]*points[i][1] for i in range(4)),2))
  if 'trapezoid' in key:assert parallel==[True,False] and area==Fraction(27,2)
  if 'parallelogram' in key:assert parallel==[True,True] and area==15
  if 'reflection' in key:assert len(set(sq))==1 and area==24
  if 'criterion_error' in key:assert sq==[16,4,16,4] and area==8
  row=next(r for r in ROWS if r['topic']==key)
  oracle.append(dict(sample_id=row['sample_id'],row_sha256=row_sha(row),explicit_grid_points=points,edge_displacements=vectors,squared_lengths=sq,opposite_parallel=parallel,exact_area=str(area),student_required_to_use_this_formalism=False))
 info=write_rows(DEST,ROWS)
 write_json(E/'curriculum_subskill_pre_review.json',dict(source_path=str(DEST.relative_to(HERE.parent)),source_file=info,rows=[dict(sample_id=r['sample_id'],row_sha256=row_sha(r),parser=inspect_case(r)) for r in ROWS],exact_fraction_decimal_checks=arithmetic,separate_grid_oracles=oracle,additional_oracles=dict(cube_edges_count=12,cube_vertices_count=8,missing_cube_face_count=1,g2_direct_sequence_results=[60,80,331,61]),actual_semantic_read_completed=False,arithmetic_parser_not_semantic_proof=True,frozen_primary_modified=False))
 for row in ROWS:print(json.dumps(row,ensure_ascii=False))

if __name__=='__main__':build()
