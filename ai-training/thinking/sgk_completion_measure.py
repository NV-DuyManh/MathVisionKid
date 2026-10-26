"""Twelve original finite G5 measurement-model drafts, DATA ONLY."""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal,localcontext
from collections import Counter
import ast,hashlib,importlib.util,json,re,sys,shutil
from exhaustive_primary_math import chat_records,expression_group
import exhaustive_colab_loader as L
HERE=Path(__file__).resolve().parent
OUT=HERE/'cloud_publication/sgk_completion_20261021/g5_measurement_models'
OLD=HERE/'cloud_publication/sgk_page_audit_20261019'
PROJECTION=HERE/'cloud_publication/sgk_final_forms_20261020/reconciliation_projection.json'
WANT=['bill_of_materials_area_cost','compare_equal_sharing_cut_schemes','grid_boundary_missing_dimensions','gridded_net_dimensions_to_volume','mixed_orientation_rectangle_tiling','nested_triangle_base_altitude_assignment']
FIELDS=['problem','givens','requested_quantity','student_work','initial_guidance','hints','worked_steps','expected_answer']
def sha(b):return hashlib.sha256(b).hexdigest()
def jd(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def write(name,x): (OUT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def jl(name,x): (OUT/name).write_text(''.join(jd(r)+'\n' for r in x),encoding='utf-8',newline='\n')
def find_tasks(v):
 if isinstance(v,dict):
  if v.get('master_id') in WANT and 'task_kind' in v:yield v
  for z in v.values():yield from find_tasks(z)
 elif isinstance(v,list):
  for z in v:yield from find_tasks(z)
TASKS={x['master_id']:x for x in find_tasks(json.loads(PROJECTION.read_text('utf-8')))}
assert len(TASKS)==6
ROWS=[]
def st(title,reason,result,explanation,expression=None,unit=''):return dict(title=title,reason=reason,result=str(result),explanation=explanation,expression=expression,unit=unit)
def add(master,branch,problem,givens,request,steps,answers,hh,model,decision,student=None):
 sid='sgk_completion_measure_20261021_'+branch;t=TASKS[master]
 row=dict(sample_id=sid,case_group_id=sid+'_group',grade=5,topic=branch,split='train',case_kind='observable_student_error' if student else 'original_finite_measurement_model',problem=problem,givens=[dict(id='g'+str(i),text=x,value=None,unit='',role='explicit_original_given')for i,x in enumerate(givens)],requested_quantity=request,student_work=dict(text=student,observations=[dict(excerpt=student,claim_scope='Only explicit synthetic written work; no hidden cognition or unseen image inferred.')])if student else None,can_solve=True,worked_steps=[dict(step_id='s'+str(i),**x)for i,x in enumerate(steps)],expected_answer=[dict(quantity=q,result=str(v),unit=u)for q,v,u in answers],initial_guidance=[hh[0]],hints=[dict(level=i+1,hint=h,question=['Em cần giữ những điều kiện và đơn vị nào?','Em áp dụng quan hệ được cho ra sao?','Em kiểm đủ điều kiện và trường hợp biên thế nào?'][i])for i,h in enumerate(hh)],independent_model=model,pedagogical_review_decision=decision,source_role='AI_GENERATED',acceptance_status='DRAFT_AWAITING_ROOT_CONTENT_QA',quality_status='AUTHOR_SELF_QA_COMPLETE_PENDING_ROOT_QA',human_verified=False,teacher_certified=False,owner_human_reviewed=False,coverage=dict(mode='FINITE_SUPPLEMENTARY_APPEND_NOT_CORE',finite_master_id=master,branch=branch,candidate_ids=t['candidate_ids'],numbers_only_variant=False,new_core_slots_claimed=0,text_relation_only=True,visual_physical_coverage_claimed=False),curriculum_assignment=dict(grade=5,enrichment=True,source_reference='Inherited verified KNTT page receipt; original complete text model; no new image view or physical success claim.'),provenance=dict(authorship_origin='ORIGINAL_AI_TEACHER_AUTHORING',book_exercise_copied=False,human_content_review_completed=False,actual_physical_or_image_result_claimed=False,acceptance_basis='OWNER_PREAUTHORIZED_PROCESS_ROOT_QA_PENDING'),nearest_source_comparison=dict(mapping_file=str(PROJECTION.relative_to(HERE)),mapping_sha256=sha(PROJECTION.read_bytes()),actual_page_receipts=t['exact_page_receipts'],nearest_actual_valid_train_rows=t['nearest_refs'],semantic_difference=t['original_master_reasons']))
 row['canonical_signatures']=sorted({expression_group(s['expression'])for s in steps if s['expression']});ROWS.append(row)

def author():
 m=WANT[0]
 add(m,'board_cutlist_area_price','Bản kê mô hình kệ có đúng hai tấm bên 90 cm×20 cm, ba tấm ngang 60 cm×20 cm và một tấm lưng 90 cm×60 cm. Mỗi kích thước là kích thước tấm hoàn thiện; bỏ qua độ dày, mép, hao hụt và phụ kiện. Giá giả định 180 nghìn đồng trên mỗi m² vật liệu, tính theo tổng diện tích một mặt của từng tấm, không tính hai mặt sơn và không mua theo tấm lớn. Tính tổng diện tích phải tính tiền và tiền vật liệu. Không yêu cầu chứng minh cắt vừa một tấm nguyên liệu.',
 ['Hai tấm 90×20 cm; ba tấm 60×20 cm; một tấm 90×60 cm.','Tính một mặt mỗi tấm hoàn thiện; 180 nghìn đồng/m²; không hao hụt hay chi phí khác.'],
 'Tổng diện tích các tấm và tiền vật liệu',[
 st('Đếm đủ từng loại tấm','Nhân diện tích một tấm với số tấm cùng loại.','12600','Hai bên:2×90×20=3600; ba ngang:3×60×20=3600; lưng:90×60=5400. Tổng12600 cm².','2*90*20+3*60*20+90*60','cm²'),
 st('Đổi đơn vị tính tiền','Một mét vuông bằng10000 xentimét vuông.','1.26','12600:10000=1,26 m²; không lấy số12600 nhân trực tiếp đơn giá theo m².','12600/10000','m²'),
 st('Áp đúng đơn giá diện tích','Mỗi m² tính180 nghìn đồng.','226.8','1,26×180=226,8 nghìn đồng. Kiểm226,8:180=1,26 m² và tổng số tấm là6.','126/100*180','nghìn đồng')],
 [('Diện tích','1.26','m²'),('Tiền','226.8','nghìn đồng')],
 ['Lập bảng số tấm và diện tích một tấm cho từng loại.','Đưa tổng diện tích về đúng đơn vị của đơn giá trước khi tính tiền.','Kiểm số lượng từng loại và xem đề tính vật liệu một mặt hay hai mặt sơn.'],
 dict(kind='board_bill',boards=[[2,'0.9','0.2'],[3,'0.6','0.2'],[1,'0.9','0.6']],price='180',expected_area='1.26',expected_cost='226.8'),
 'Counted rectangular-board cut list plus per-area price; different relation from fixed-square tile pack procurement.')
 add(m,'shelf_design_finite_budget','Một thiết kế kệ giả định phải có hai tấm bên 80 cm×25 cm và một tấm lưng 80 cm×60 cm. Được chọn đúng n tấm ngang 60 cm×25 cm, n chỉ là2,3 hoặc4; ngoài ra không có tấm nào. Bỏ qua độ dày, hao hụt, phụ kiện và cách bố trí cắt. Giá200 nghìn đồng/m² tính theo tổng diện tích một mặt từng tấm hoàn thiện. Ngân sách tối đa270 nghìn đồng, được dùng đúng bằng. Hãy chọn nhiều tấm ngang nhất trong miền cho phép mà không vượt tiền; nêu các lựa chọn đủ tiền, chi phí thiết kế chọn và tiền còn.',
 ['Phần bắt buộc:hai80×25 cm và một80×60 cm; mỗi tấm ngang60×25 cm.','n∈{2,3,4}; đơn giá200 nghìn/m²; tổng tiền≤270 nghìn; không phí khác.'],
 'Thiết kế hữu hạn tối đa số tấm ngang trong ngân sách',[
 st('Tách phần bắt buộc khỏi phần chọn','Hai bên và lưng có mặt trong mọi thiết kế.','0.88','2×0,8×0,25+0,8×0,6=0,88 m². Một tấm ngang có diện tích0,6×0,25=0,15 m².','2*8/10*25/100+8/10*6/10','m²'),
 st('So đủ ba lựa chọn','Chỉ ba giá trị n đã được cho, không tự thêm thiết kế khác.','n2:236;n3:266;n4:296','Diện tích lần lượt1,18;1,33;1,48 m²; nhân200 cho236;266;296 nghìn đồng. Hai lựa chọn đầu không vượt270, lựa chọn cuối vượt.','(88/100+3*15/100)*200','nghìn đồng'),
 st('Tối đa sau khi lọc ngân sách','Nhiều tấm nhất phải thuộc các lựa chọn còn đủ tiền.','3 tấm ngang','Chọn n=3, tốn266 nghìn, còn270−266=4 nghìn. Kiểm thiết kế kế tiếp n=4 tốn296 nên không nhận.','270-266','nghìn đồng')],
 [('Đủ tiền','n=2 hoặc n=3',''),('Tối đa','3','tấm ngang'),('Tiền','266','nghìn đồng'),('Còn','4','nghìn đồng')],
 ['Tách diện tích bắt buộc và phần diện tích thay đổi theo lựa chọn.','Tính tiền cho từng giá trị được phép rồi áp dấu ngân sách.','Chỉ chọn nhiều nhất sau khi loại phương án vượt tiền; kiểm cả phương án liền sau.'],
 dict(kind='board_budget',fixed=[[2,'0.8','0.25'],[1,'0.8','0.6']],shelf=['0.6','0.25'],choices=[2,3,4],price='200',budget='270',expected_costs=['236','266','296'],expected_eligible=[2,3],expected_best=3),
 'Finite open-design choice constrained by material cut-list cost, not area-only calculation or unrestricted design generation.')
 m=WANT[1]
 add(m,'half_third_vs_sixth_inventory','Có5 chiếc bánh bằng nhau, mỗi chiếc là1 đơn vị; chia hết cho6 bạn, không hao hụt, được cắt thành phần bằng nhau như nêu. Cách A:cắt3 chiếc thành các nửa và2 chiếc thành các phần ba; mỗi bạn nhận1 nửa và1 phần ba. Cách B:cắt cả5 chiếc thành các phần sáu; mỗi bạn nhận5 phần sáu. Kiểm mỗi cách có đủ miếng cho mọi bạn, có dùng hết bánh và mỗi bạn có nhận cùng lượng giữa hai cách không. Nêu tổng số miếng của từng cách; không hỏi số nhát cắt.',
 ['5 bánh cùng cỡ,6 bạn; A:3 bánh chia2,2 bánh chia3; mỗi bạn1/2+1/3 bánh.','B:5 bánh chia6; mỗi bạn5 phần sáu; chỉ cắt theo phương án, không hao hụt.'],
 'Kiểm tồn kho miếng, lượng mỗi bạn và so hai cách',[
 st('Kiểm miếng cách A','Từng loại miếng phải đủ đúng cho số bạn.','6 nửa và6 phần ba','3×2=6 nửa,2×3=6 phần ba;6 bạn mỗi người một miếng mỗi loại dùng hết12 miếng.','3*2+2*3','miếng'),
 st('Đưa về cùng đơn vị lượng','Nửa và phần ba cùng lấy một chiếc bánh làm đơn vị.','5/6','1/2+1/3=3/6+2/6=5/6 bánh mỗi bạn.','1/2+1/3','bánh/bạn'),
 st('Kiểm cách B rồi so','Mỗi phần sáu là một phần trong sáu phần bằng nhau của một chiếc.','30 miếng; mỗi bạn5/6 bánh','5×6=30 miếng,6×5=30 nên dùng hết. Hai cách cho cùng lượng;6×5/6=5 bánh kiểm tổng, dù số miếng12 và30 khác nhau.','6*5/6','bánh')],
 [('Cách A','12','miếng'),('Cách B','30','miếng'),('Mỗi bạn ở cả hai cách','5/6','bánh'),('So','Cả hai khả thi và cùng lượng mỗi bạn','')],
 ['Theo dõi riêng số miếng và lượng bánh của mỗi loại miếng.','Quy các phần về cùng một chiếc bánh trước khi so phần mỗi bạn.','Nhân phần mỗi bạn với số bạn và kiểm kho từng loại đã dùng hết chưa.'],
 dict(kind='cut_compare',schemes=[dict(cuts=[[3,2],[2,3]],each=[[1,2],[1,3]]),dict(cuts=[[5,6]],each=[[5,6]])],people=6,whole=5,expected_pieces=[12,30],expected_share='5/6',expected_feasible=[True,True]),
 'Two specified cutting/distribution schemes compared using both piece inventory and fraction conservation, not generic fraction division alone.')
 student='Cách Y cũng chia đều hết vì mỗi bạn lấy một nửa và một phần ba là được.'
 add(m,'scheme_piece_shortage_even_if_named_share','Có2 chiếc bánh bằng nhau chia hết cho3 bạn. Chỉ được cắt theo đúng hai phương án sau, không cắt lại các miếng. Cách X:cắt chiếc thứ nhất thành3 phần ba, chiếc thứ hai thành6 phần sáu; mỗi bạn lấy1 phần ba và2 phần sáu. Cách Y:cắt chiếc thứ nhất thành2 nửa, chiếc thứ hai thành3 phần ba; đề xuất mỗi bạn lấy1 nửa và1 phần ba. Bạn viết:“'+student+'” Giữ câu đó; kiểm kho miếng và lượng bánh mỗi bạn để quyết định phương án nào thực hiện đúng chia đều hết.',
 ['2 bánh cùng cỡ,3 bạn; không cắt lại, không bỏ bánh.','X:kho3 phần ba và6 phần sáu, mỗi bạn1 phần ba+2 phần sáu; Y:kho2 nửa và3 phần ba, đề xuất mỗi bạn1 nửa+1 phần ba.'],
 'Kiểm hai phương án và phản hồi bằng kho miếng thực có',[
 st('Kiểm X theo từng loại','Ba bạn cần đúng3 phần ba và6 phần sáu.','X dùng hết kho','1/3+2/6=2/3 bánh mỗi bạn;3×2/3=2 bánh. Kho và lượng đều khớp.','1/3+2/6','bánh/bạn'),
 st('Kiểm Y trước khi chấp nhận','Mỗi bạn một nửa thì3 bạn cần3 nửa nhưng chỉ có2 nửa.','Thiếu1 nửa bánh theo phương án Y','Không được âm thầm cắt lại hoặc tạo thêm miếng. Ba phần ba đủ, nhưng một loại đủ không bù thiếu loại kia.','3-2','nửa'),
 st('Kiểm bảo toàn lượng của đề xuất','Lượng mỗi bạn phải nhân3 về đúng2 bánh.','Y không thực hiện được như mô tả','Mỗi phần Y là1/2+1/3=5/6 bánh; ba phần cần5/2 bánh, vượt2 bánh. Câu bạn bỏ kiểm kho và tổng; X đạt còn Y không đạt.','3*(1/2+1/3)','bánh')],
 [('Cách đạt','X',''),('Mỗi bạn theo X','2/3','bánh'),('Y','Không đủ miếng nửa và vượt tổng bánh','')],
 ['Đếm nhu cầu từng loại miếng cho cả nhóm, không chỉ một người.','Đối chiếu từng loại với số miếng phương án thực sự tạo ra.','Kiểm thêm tổng lượng bánh và giữ nguyên luật không cắt lại.'],
 dict(kind='cut_compare',schemes=[dict(cuts=[[1,3],[1,6]],each=[[1,3],[2,6]]),dict(cuts=[[1,2],[1,3]],each=[[1,2],[1,3]])],people=3,whole=2,expected_pieces=[9,5],expected_share='2/3',expected_feasible=[True,False]),
 'Observable impossible piece inventory branch, not assuming every named fraction combination can be distributed.',student)
 m=WANT[2]
 add(m,'grid_frame_known_side_cells','Một hình chữ nhật trên lưới ô vuông gồm9 cột và số hàng được nhận từ mép trái:mép trên có9 ô, mép trái có7 ô, cả hai số đếm đều tính ô góc ở hai đầu. Mỗi ô cạnh0,5 m. Chỉ dải viền rộng đúng1 ô quanh bốn cạnh được tô; phần giữa để trắng nhưng vẫn thuộc hình chữ nhật, không phải giấy bị cắt đi. Từ dữ kiện mép, tìm hai kích thước ngoài, diện tích toàn hình, phần trắng và phần tô. Không có ảnh cần đo.',
 ['Mép trên9 ô, mép trái7 ô kể cả góc; ô vuông cạnh0,5 m.','Viền rộng1 ô; mọi ô giữa trắng vẫn thuộc hình; không hở hay chồng ô.'],
 'Khôi phục kích thước và tách diện tích toàn/giữa/viền',[
 st('Đổi số khoảng ô thành chiều dài','Số ô dọc cạnh là số cạnh ô liên tiếp, không phải số điểm mút.','Dài4,5 m;rộng3,5 m','9×0,5=4,5 m và7×0,5=3,5 m. Không bớt một ô vì hai đầu đã là ô, không phải hai điểm.','9*5/10','m'),
 st('Đếm toàn hình và khoảng giữa','Bỏ một cột mỗi bên, một hàng trên và dưới để lấy phần trắng.','63 ô toàn;35 ô trắng','9×7=63 ô; phần trắng(9−2)×(7−2)=35 ô. Ô cạnh0,5 m có diện tích0,25 m².','(9-2)*(7-2)','ô'),
 st('Đổi diện tích và kiểm phần viền','Tô và trắng rời nhau, ghép lại toàn hình.','Toàn15,75;trắng8,75;viền7 m²','63×0,25=15,75;35×0,25=8,75;28×0,25=7. Kiểm8,75+7=15,75 m² và9×7×0,25 bằng4,5×3,5.','(63-35)*25/100','m²')],
 [('Kích thước','4,5 m × 3,5 m',''),('Toàn','15.75','m²'),('Trắng','8.75','m²'),('Tô','7','m²')],
 ['Phân biệt đếm ô với đếm điểm mút trên cạnh lưới.','Tách phần giữa bằng cách bỏ đúng dải viền ở hai phía mỗi chiều.','Kiểm phần tô cộng phần trắng trả lại toàn hình và giữ đơn vị diện tích.'],
 dict(kind='frame',width=9,height=7,scale='0.5',expected_total='15.75',expected_inside='8.75',expected_border='7'),
 'Infer outer dimensions and interior from explicit border unit-cell structure, not given physical dimensions followed by conversion.')
 student='Viền có24 ô nên diện tích cả hình là24×0,25=6 m².'
 add(m,'grid_frame_unknown_height_from_border','Hình chữ nhật lưới có mép trên9 ô kể cả hai góc; chưa ghi số hàng. Dải viền rộng1 ô quanh hình có tổng đúng24 ô khác nhau, ô góc chỉ tính một lần; hình có ít nhất3 hàng và3 cột. Mỗi ô cạnh0,5 m. Các ô giữa không tô vẫn thuộc hình chữ nhật. Bạn viết:“'+student+'” Giữ câu đó;tìm số hàng, kích thước ngoài, diện tích cả hình và diện tích không tô; kiểm lại24 ô viền.',
 ['9 cột; viền1 ô có24 ô khác nhau; ít nhất3 hàng,cột; góc không đếm đôi.','Ô cạnh0,5 m; giữa trắng vẫn thuộc hình; số hàng nguyên chưa biết.'],
 'Suy số hàng từ tổng viền rồi sửa việc đồng nhất viền với toàn hình',[
 st('Loại hai hàng viền ngang','Hàng trên và dưới mỗi hàng9 ô, không trùng vì có ít nhất3 hàng.','6 ô viền bên ở các hàng giữa','24−2×9=6. Mỗi hàng giữa góp2 ô biên trái phải khác nhau, nên có3 hàng giữa.','24-2*9','ô'),
 st('Khôi phục kích thước ngoài','Thêm hai hàng trên dưới vào số hàng giữa.','5 hàng;4,5 m × 2,5 m','3+2=5 hàng. Hai chiều là9×0,5 và5×0,5 m; kiểm2×9+2×(5−2)=24 ô viền.','6/2+2','hàng'),
 st('Giữ đúng phạm vi diện tích','Toàn hình có9×5 ô, viền chỉ là một phần.','Toàn11,25 m²;trắng5,25 m²','45×0,25=11,25 m²; giữa(9−2)×(5−2)=21 ô, tức5,25 m². Dòng bạn đúng cho riêng viền6 m²;6+5,25=11,25 m².','9*5*25/100','m²')],
 [('Số hàng','5','hàng'),('Kích thước','4,5 m × 2,5 m',''),('Toàn','11.25','m²'),('Trắng','5.25','m²')],
 ['Góc đã đếm ở hàng trên dưới thì có cần đếm lại ở hai bên không?','Dùng số ô viền còn lại để suy các hàng giữa.','Phân biệt số ô viền với số ô trong toàn hình trước khi đổi diện tích.'],
 dict(kind='frame_inverse',width=9,border_count=24,scale='0.5',expected_height=5,expected_total='11.25',expected_inside='5.25'),
 'Inverse border-count relation plus observable scope error; corners counted once and blank interior retained.',student)
 m=WANT[3]
 add(m,'gridded_net_dimensions_no_target','Bản trải mô hình hộp kín đặt trên lưới ô vuông cạnh0,5 cm, bỏ qua độ dày,mép dán và hao hụt. Dải bốn mặt bên liền hàng có chiều cao chung4 ô; bề ngang lần lượt6,3,6,3 ô. Dọc cạnh6 ô ở phía trên và dưới mặt đầu đều gắn một mặt6×3 ô, hướng ra ngoài dải. Chỉ gấp theo các cạnh chung,nắp trên và đáy khép hai đầu khác nhau, không chồng mặt. Chưa cho kích thước hộp đích. Hãy suy ba kích thước hộp trong mô hình và thể tích; kiểm hai mặt gắn thêm khớp miệng.',
 ['Dải ngang6,3,6,3 ô; cao chung4 ô; hai mặt6×3 ô gắn trên,dưới mặt6×4 đầu.','Ô vuông cạnh0,5 cm; mô hình hộp kín không độ dày/mép/hao hụt; không ảnh hay gấp thật.'],
 'Suy kích thước từ lưới và quan hệ gấp rồi tính thể tích',[
 st('Nhận vai trò ba số đếm ô','Bề ngang luân phiên là hai cạnh đáy; cao dải là cao hộp.','Đáy6×3 ô;cao4 ô','Hai mặt6×3 ô khép miệng6×3 ô. Không lấy tổng18 ô ngang của dải làm chiều dài một cạnh đáy.'),
 st('Đổi cạnh ô thành độ dài','Cùng nhân mỗi số cạnh ô với0,5 cm.','3 cm × 1,5 cm × 2 cm','6×0,5=3;3×0,5=1,5;4×0,5=2. Hai nắp có diện tích3×1,5 cm² và cạnh ghép khớp hai loại mặt bên.','3*5/10','cm'),
 st('Tính thể tích và kiểm theo ô khối','Hộp có6×3 ô đáy và4 lớp ô khối cạnh0,5 cm.','9','72 ô khối, mỗi ô khối thể tích0,125 cm³;72×0,125=9 cm³, cũng bằng3×1,5×2.','3*15/10*2','cm³')],
 [('Kích thước','3 cm × 1,5 cm × 2 cm',''),('Thể tích','9','cm³')],
 ['Tách chiều cao chung của dải khỏi các bề ngang luân phiên.','Dùng mặt khép đầu để kiểm hai cạnh đáy trước khi đổi thang ô.','Kiểm thể tích bằng số lớp ô khối và giữ đơn vị khối.'],
 dict(kind='net',strip=[6,3,6,3],height=4,caps=[6,3],scale='0.5',expected_dimensions=['3','1.5','2'],expected_volume='9'),
 'Unknown dimensions inferred from grid-cell scale and fold strip/cap adjacency; unlike existing net validation with a known target cuboid.')
 student='Cả dải dài20 ô nên hộp dài4 dm; lấy4×0,8×0,6=1,92 dm³.'
 add(m,'net_total_strip_not_edge','Một bản trải hộp kín trên lưới ô cạnh0,2 dm có dải4 mặt bên cùng cao3 ô. Bề ngang mặt thứ nhất6 ô,mặt thứ ba6 ô; cả dải ngang20 ô. Dọc cạnh6 ô phía trên và dưới mặt đầu gắn hai mặt6×4 ô để khép hai đầu đối diện. Các cạnh khép phải khớp; bỏ qua dày,mép và hao hụt. Bạn viết:“'+student+'” Giữ câu đó;suy bề ngang hai mặt chưa ghi,ba kích thước hộp và thể tích đúng. Không có bản gấp thật để nghiệm thu.',
 ['Dải4 mặt cao3 ô; rộng6,?,6,? ô; tổng ngang20 ô; hai mặt khép6×4 ô.','Ô cạnh0,2 dm; cạnh gấp/khép phải khớp; không độ dày hay hao hụt.'],
 'Khôi phục mặt còn thiếu và sửa vai trò tổng dải',[
 st('Dùng miệng để suy bề ngang thiếu','Mặt khép6×4 ô buộc đáy có hai cạnh6 và4 ô.','Rộng6,4,6,4 ô','Hai mặt chưa ghi đều rộng4 ô;6+4+6+4=20 kiểm tổng. Số20 ô là chu vi đáy theo ô, không phải một cạnh đáy.'),
 st('Đổi ba cạnh đúng vai trò','Cao3 ô của dải không đổi khi gấp quanh.','1,2 dm × 0,8 dm × 0,6 dm','6×0,2=1,2;4×0,2=0,8;3×0,2=0,6. Câu bạn đã lấy chiều dài cả dải làm một cạnh hộp.','6*2/10','dm'),
 st('Tính và kiểm thể tích','Diện tích đáy nhân cao, không dùng chu vi nhân rộng nhân cao.','0.576','1,2×0,8×0,6=0,576 dm³. Kiểm6×4×3=72 ô khối,cạnh0,2 dm nên72×0,008=0,576 dm³.','12/10*8/10*6/10','dm³')],
 [('Bề ngang','6,4,6,4','ô'),('Kích thước','1,2 dm × 0,8 dm × 0,6 dm',''),('Thể tích','0.576','dm³')],
 ['Xác định mặt khép đầu buộc những kích thước nào của miệng hộp.','Phân biệt một cạnh đáy với tổng bề ngang cả dải mặt bên.','Đối chiếu mọi cạnh khép và kiểm thể tích bằng ô khối theo thang lưới.'],
 dict(kind='net',strip=[6,4,6,4],height=3,caps=[6,4],scale='0.2',expected_dimensions=['1.2','0.8','0.6'],expected_volume='0.576',total_strip=20),
 'Inverse blank panel widths constrained by cap match and total strip; explicit critique of confusing perimeter with length.',student)
 m=WANT[4]
 add(m,'tiling_mixed_orientation_construction','Tấm nền mô hình chữ nhật rộng5 cm,cao6 cm, chia ô vuông1 cm. Dùng các miếng chữ nhật2×3 cm cứng, không cắt,không chồng,kín nền, cạnh miếng song song cạnh nền; được xoay90°. Mỗi miếng dùng trọn. Hãy cho một cách lát có dùng cả hai hướng, nêu số miếng và kiểm đủ diện tích không khe. Có thể mô tả bằng các dải và khoảng trên lưới; không cần ảnh.',
 ['Nền5×6 cm; ô1 cm; miếng2×3 cm; xoay90° được.','Không cắt/chồng/khe; cạnh song song; phải dùng cả hai hướng; mô tả bằng dải hoặc tọa độ.'],
 'Một phép lát đầy đủ có hai hướng và kiểm số miếng',[
 st('Tìm số miếng nếu lát được','Diện tích nền chia diện tích một miếng chỉ cho số lượng cần, chưa đủ chứng minh tồn tại.','5','5×6:(2×3)=5 miếng. Cần đưa ra cách bố trí thật sự trong mô hình.','5*6/(2*3)','miếng'),
 st('Chia nền thành hai dải khác bề ngang','Dải2 cm và3 cm ghép kín chiều rộng5 cm, cùng cao6 cm.','Dải2×6 dùng2 miếng2×3;dải3×6 dùng3 miếng3×2','Dải trái rộng2:đặt2 miếng cao3 chồng theo chiều cao,không chồng diện tích. Dải phải rộng3:đặt3 miếng xoay cao2. Cả hai dải đều cao6 cm.'),
 st('Kiểm từng vùng và tổng','Mỗi dải được phân thành các hình rời nhau có đủ chiều cao.','2+3=5 miếng; có cả hai hướng','Trong dải trái các đoạn cao là[0,3],[3,6];dải phải là[0,2],[2,4],[4,6]. Hai dải chỉ chung biên nên kín5×6, không khe/chồng.','2+3','miếng')],
 [('Số miếng','5','miếng'),('Bố trí','Dải rộng2:hai miếng2×3;dải rộng3:ba miếng3×2','')],
 ['Kiểm số lượng theo diện tích rồi tìm một bố trí có thể kiểm riêng từng phần.','Có thể chia nền thành các dải phù hợp hai hướng của miếng không?','Đối chiếu các khoảng phủ theo cả hai chiều; diện tích bằng nhau chưa tự chứng minh lát kín.'],
 dict(kind='tiling',width=5,height=6,tile=[2,3],allow_rotate=True,require_mixed=True,placements=[[0,0,2,3],[0,3,2,3],[2,0,3,2],[2,2,3,2],[2,4,3,2]],expected_possible=True),
 'Constructive fixed-rectangle exact cover requiring mixed orientation, not equal-area-only or square-tile procurement.')
 student='Diện tích30 chia6 bằng5 nên chắc lát được dù không xoay miếng.'
 add(m,'tiling_no_rotation_area_not_sufficient','Vẫn xét nền rộng5 cm,cao6 cm trên lưới1 cm và miếng2×3 cm, nhưng lần này cấm xoay:mọi miếng phải rộng2 cm theo chiều ngang,cao3 cm theo chiều dọc. Cạnh ở các vạch nguyên,không cắt,chồng hay để khe; phải phủ kín. Bạn viết:“'+student+'” Giữ câu đó;kiểm có phép lát theo đúng luật không, chỉ rõ vì sao kiểm diện tích chưa đủ. Không tự cho phép xoay để chữa đề.',
 ['Nền ngang5,dọc6; mọi miếng ngang2,dọc3; không xoay.','Cạnh trên vạch nguyên; không cắt,chồng,khe; diện tích bằng nhau là điều kiện cần.'],
 'Tính khả thi khi bị cấm xoay và phản hồi điều kiện diện tích',[
 st('Giữ phép đếm diện tích đúng','Diện tích cho số miếng cần nếu một bố trí hợp lệ tồn tại.','5 miếng theo diện tích','30:6=5 đúng số học nhưng không chỉ vị trí các miếng, nên chưa kết luận lát được.','5*6/(2*3)','miếng'),
 st('Xét một hàng ô bất kỳ','Mỗi miếng không xoay phủ đúng2 ô ngang trong từng hàng mà nó đi qua.','Số ô ngang được phủ phải chẵn','Các đoạn rộng2 trên hàng phải rời nhau, ghép kín thì tổng bề ngang là tổng các số2; không thể bằng bề ngang5 lẻ.'),
 st('Kết luận trong đúng miền luật','Một hàng không phủ kín đã đủ loại mọi bố trí.','Không có phép lát theo luật cấm xoay','Có thể lát nếu đổi luật để cho xoay, nhưng đó là bài khác. Không sửa luật hoặc bỏ một dải nền để chấp nhận câu bạn.')],
 [('Khả thi','Không có phép lát theo luật cấm xoay',''),('Lý do','Mỗi hàng cần phủ5 ô nhưng là tổng các đoạn rộng2 ô','')],
 ['Phép chia diện tích cho biết điều kiện cần hay đã cho một bố trí hợp lệ?','Giữ hướng miếng đã buộc và xem một hàng ngang nhận các đoạn dài bao nhiêu ô.','Kiểm bề ngang của từng hàng mà không tự thêm phép xoay hoặc cắt.'],
 dict(kind='tiling',width=5,height=6,tile=[2,3],allow_rotate=False,require_mixed=False,placements=[],expected_possible=False),
 'Same geometric stock but changed no-rotation constraint; proves area divisibility is insufficient rather than merely substituting numbers.',student)
 m=WANT[5]
 add(m,'nested_triangles_distinct_apex_heights','Mô hình phẳng được mô tả đầy đủ:B(0,0),C(8,0),A(0,6),D(0,3),E(4,0), đơn vị cm trên hai trục vuông góc. Có thể hiểu AB thẳng đứng dài6,BC ngang dài8;D trên AB cách B3 vàE trên BC cách B4. Ba tam giác ABC,ABE,DBE lồng trong nhau. Chọn lần lượt các đáy BC,BE,BE; ghép đúng chiều cao vuông góc cho từng tam giác,tính diện tích từng tam giác và diện tích phần ABC ngoài DBE. Không đo ảnh.',
 ['AB6 cm vuông gócBC8 cm;BD3 cm;BE4 cm;D trênAB,E trênBC.','Đáy chọn ABC:BC;ABE:BE;DBE:BE; các vị trí chính xác,không điểm ngoài nào khác cần đo.'],
 'Ghép từng đáy với đúng đỉnh đối diện và tính phần chênh lồng nhau',[
 st('Ghép chiều cao đúng tam giác','Chiều cao bắt đầu từ đỉnh đối diện đáy được chọn.','ABC cao6;ABE cao6;DBE cao3 cm','Hai tam giác đầu có đỉnhA,cùng đường đáyBC nên dùngAB6. DBE có đỉnhD nên dùngDB3,không dùngAB6 cho mọi hình.'),
 st('Tính lần lượt các diện tích','Mỗi diện tích bằng đáy tương ứng nhân cao rồi chia2.','ABC24;ABE12;DBE6 cm²','8×6:2=24;4×6:2=12;4×3:2=6. KiểmDBE⊂ABE⊂ABC và diện tích tăng đúng thứ tự.','8*6/2','cm²'),
 st('Bớt đúng miền bên trong','DBE nằm trong ABC nên phần ngoài DBE là hiệu hai diện tích.','18','24−6=18 cm². Không bớt thêmABE vì yêu cầu chỉ bỏDBE;6+18=24 kiểm lại.','24-6','cm²')],
 [('Chiều cao theo ba đáy','6;6;3','cm'),('Diện tích ABC','24','cm²'),('Diện tích ABE','12','cm²'),('Diện tích DBE','6','cm²'),('ABC ngoài DBE','18','cm²')],
 ['Với mỗi đáy đã chọn, tìm đỉnh đối diện của chính tam giác đó.','Một đoạn chiều cao của hình lớn có luôn là chiều cao của mọi hình nhỏ không?','Kiểm quan hệ lồng nhau và cộng lại phần bỏ với phần còn.'],
 dict(kind='nested',points={'B':[0,0],'C':[8,0],'A':[0,6],'D':[0,3],'E':[4,0]},triangles=[['A','B','C'],['A','B','E'],['D','B','E']],expected_areas=['24','12','6']),
 'Several nested triangle/base/altitude assignments including a changed apex; no single-height blanket application.')
 student='Chọn AD=3 cm làm đáy tam giác ADE thì DE=5 cm là chiều cao, nên diện tích bằng7,5 cm².'
 add(m,'nested_vertical_base_external_altitude_foot','Mô hình:B(0,0),C(8,0),A(0,6),D(0,3),E(4,0), đơn vị cm,trục ngang và dọc vuông góc. Vì vậy DE=5 cm là cạnh xiên của tam giác vuông DBE, không có góc vuông nào giữaDE vàAD. Xét các tam giác ADE,DBE,ACE nằm trongABC; chọn lần lượt đáyAD,DB,CE. Bạn viết:“'+student+'” Giữ câu đó;ghép chiều cao đúng của ba tam giác,tính các diện tích và kiểm ba miền ghép hếtABC,không chồng phần trong.',
 ['AB6,BD3,BC8,BE4 cm;AB vuông gócBC;D trênAB,E trênBC;DE5 cm xiên.','Đáy ADE:AD;DBE:DB;ACE:CE; chân từE đến đườngAD làB,nằm ngoài đoạnAD.'],
 'Sửa nhầm cạnh xiên với chiều cao và ghép các miền lồng trong hình lớn',[
 st('Giữ đường thẳng chứa đáy đứng','Chiều cao tớiAD hoặcDB phải nằm ngang từE tới đườngAB.','ADE vàDBE đều có caoEB=4 cm','B nằm ngoài đoạnAD nhưng trên đường thẳngAD;EB vuông góc đường đó. DE xiên5 cm không vuông gócAD nên không làm chiều cao khi đáyAD.'),
 st('Tính hai phần theo đáy đứng','AD=AB−BD=3 vàDB=3, cùng chiều cao4.','ADE6;DBE6 cm²','3×4:2=6 cm² cho mỗi tam giác. Câu bạn đúng số3×5:2 nhưng đã ghép sai đoạn5 vào chiều cao.','3*4/2','cm²'),
 st('Ghép tam giác còn lại và kiểm tổng','ACE chọn đáyCE=8−4=4 ngang nên dùng chiều caoAB=6.','ACE12 cm²;tổng24 cm²','4×6:2=12;6+6+12=24 bằng8×6:2 củaABC. AD chiaABE thànhADE vàDBE;AE chiaABC thànhABE vàACE, nên ba miền chỉ chung biên.','6+6+4*6/2','cm²')],
 [('Chiều cao theo AD,DB,CE','4;4;6','cm'),('ADE','6','cm²'),('DBE','6','cm²'),('ACE','12','cm²'),('Tổng','24','cm²')],
 ['Đường cao phải vuông góc với đường thẳng nào khi đã chọn đáy?','Chân đường cao có thể nằm ngoài đoạn đáy; đừng chọn cạnh xiên chỉ vì biết độ dài.','Kiểm từng phần bằng đúng cặp đáy-cao rồi đối chiếu tổng với tam giác ngoài.'],
 dict(kind='nested',points={'B':[0,0],'C':[8,0],'A':[0,6],'D':[0,3],'E':[4,0]},triangles=[['A','D','E'],['D','B','E'],['A','C','E']],expected_areas=['6','6','12']),
 'Vertical-base nested partition with external altitude foot and observable oblique-edge misuse, distinct from horizontal-base forward area.',student)

def calc(e,kind):
 def walk(n):
  if isinstance(n,ast.Constant)and type(n.value)in(int,float):return kind(ast.get_source_segment(e,n))
  if isinstance(n,ast.UnaryOp)and isinstance(n.op,ast.USub):return-walk(n.operand)
  if isinstance(n,ast.BinOp):
   a,b=walk(n.left),walk(n.right)
   if isinstance(n.op,ast.Add):return a+b
   if isinstance(n.op,ast.Sub):return a-b
   if isinstance(n.op,ast.Mult):return a*b
   if isinstance(n.op,ast.Div):return a/b
  raise ValueError(e)
 return walk(ast.parse(e,mode='eval').body)

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 parents={}
 if (OUT/'cases.jsonl').exists():
  if '--polish-revision'not in sys.argv:raise RuntimeError('Existing batch; resume QA without re-authoring source')
  backup=OUT/'author_pre_polish';backup.mkdir(exist_ok=True)
  for p in OUT.iterdir():
   if p.is_file()and p.name!='independent_oracle.py':
    target=backup/p.name
    if target.exists():assert target.read_bytes()==p.read_bytes()
    else:shutil.copy2(p,target)
  parents={json.loads(b)['sample_id']:(json.loads(b),sha(b))for b in(backup/'cases.jsonl').read_bytes().splitlines()}
 snapshots={}
 for d in ['sgk_finish_20261020','sgk_remaining_20261020','sgk_final_forms_20261020']:
  for p in(HERE/'cloud_publication'/d).rglob('cases.jsonl'):snapshots[str(p)]=sha(p.read_bytes())
 near=[];seen=set();pages=[];sourcecache={}
 for mid,t in TASKS.items():
  for ref in t['nearest_refs']:
   key=(ref['source_file'],ref['line'])
   sourcecache.setdefault(ref['source_file'],(OLD/ref['source_file']).read_bytes().splitlines())
   raw=sourcecache[ref['source_file']][ref['line']-1];r=json.loads(raw)
   assert sha(raw)==ref['sha256'] and r['sample_id']==ref['sample_id'] and r['split']=='train'
   assert not re.search(r'holdout|eval|pilot|protected',r['sample_id'],re.I)
   if key not in seen:near.append(dict(reference=ref,source_row_sha256=sha(raw),actual_fields={k:r.get(k)for k in FIELDS},scope='Nearest exact valid-training fields read; not full-archive semantic absence proof'));seen.add(key)
  for p in t['exact_page_receipts']:
   found=[]
   for line in(OLD/'g5_audit/page_review.jsonl').read_bytes().splitlines():
    r=json.loads(line)
    if r.get('volume')==p['volume'] and r.get('printed_page')==p['printed_page'] and r.get('sha256')==p['sha256']:found.append((line,r))
   assert len(found)==1
   line,r=found[0];pages.append(dict(master_id=mid,receipt=r,source_row_sha256=sha(line),basis='Inherited actual-page receipt read and hash-bound, not newly image-viewed'))
 write('candidate_task_snapshot.json',dict(source_projection_sha256=sha(PROJECTION.read_bytes()),tasks=list(TASKS.values())))
 jl('nearest_actual_fullfields.jsonl',near);jl('actual_page_receipts_readback.jsonl',pages)
 author();assert len(ROWS)==12 and Counter(r['coverage']['finite_master_id']for r in ROWS)==Counter({m:2 for m in WANT})
 # Compound result descriptions retain their full explanation; arithmetic facts
 # are independently bound below rather than mislabelling text as a scalar.
 for row in ROWS:
  for step in row['worked_steps']:
   if step['expression']:
    try:F(step['result'])
    except ValueError:step['expression']=None
   try:F(step['result'])
   except ValueError:step['unit']=''
  def readable(v):
   if isinstance(v,str):
    v=re.sub(r'(?<=[A-Za-zÀ-ỹ])(?=\d)',' ',v)
    v=re.sub(r'(?<=\d)(?=[A-Za-zÀ-ỹ])',' ',v)
    return re.sub(r'(?<=[,:;])(?=[A-Za-zÀ-ỹ])',' ',v)
   if isinstance(v,list):return[readable(x)for x in v]
   if isinstance(v,dict):return{k:x if k in('id','step_id','expression','role')else readable(x)for k,x in v.items()}
   return v
  for field in FIELDS:row[field]=readable(row[field])
  if parents:
   parent,ph=parents[row['sample_id']]
   row['provenance'].update(parent_draft_row_sha256=ph,derivation='AUTHOR_CLARITY_POLISH_SPACING_AND_COMPOUND_RESULT_UNITS_NO_ANSWER_VALUE_CHANGE')
 row=next(r for r in ROWS if r['topic']=='board_cutlist_area_price')
 assert row['worked_steps'][0]['expression'] is not None

 norm=lambda t:re.sub(r'\s+',' ',t).strip().casefold()
 oldids=set();oldquestions=set()
 for p in [OLD/'current_sources.jsonl',OLD/'release/accepted_cases.jsonl']+[Path(p)for p in snapshots]:
  for line in p.read_bytes().splitlines():
   r=json.loads(line);oldids.add(r['sample_id']);oldquestions.add(norm(r['problem']))
 assert len({r['sample_id']for r in ROWS})==12 and all(r['sample_id']not in oldids and norm(r['problem'])not in oldquestions for r in ROWS)
 jl('cases.jsonl',ROWS);lines=(OUT/'cases.jsonl').read_bytes().splitlines();hashes={r['sample_id']:sha(b)for r,b in zip(ROWS,lines)}
 if parents:jl('author_polish_delta.jsonl',[dict(sample_id=r['sample_id'],parent_row_sha256=parents[r['sample_id']][1],derived_row_sha256=hashes[r['sample_id']],changes={k:dict(before=parents[r['sample_id']][0][k],after=r[k])for k in FIELDS if parents[r['sample_id']][0][k]!=r[k]},answer_numeric_values_changed=False,original_files_preserved='author_pre_polish')for r in ROWS])
 spec=importlib.util.spec_from_file_location('measure_oracle',OUT/'independent_oracle.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 chats=[];qa=[];numeric=[];oracles=[]
 for r in ROWS:
  h=hashes[r['sample_id']]
  for s in r['worked_steps']:
   assert s['reason']and s['explanation']and'unit'in s
   if s['expression']:
    f=calc(s['expression'],F)
    with localcontext()as ctx:
     ctx.prec=90;d=calc(s['expression'],Decimal);assert abs(d-Decimal(f.numerator)/Decimal(f.denominator))<Decimal('1e-70')
    assert f==F(s['result'])
    numeric.append(dict(sample_id=r['sample_id'],source_row_sha256=h,step_id=s['step_id'],expression=s['expression'],fraction=str(f),decimal=str(d),passed=True))
  oracles.append(dict(sample_id=r['sample_id'],source_row_sha256=h,master_id=r['coverage']['finite_master_id'],independent_model=r['independent_model'],result=mod.oracle(r['independent_model']),independent_of_worked_expression_evaluator=True,passed=True))
  for c in chat_records(r):
   c.update(source_row_sha256=h,acceptance_status=r['acceptance_status'],quality_status=r['quality_status']);L.validate_chat(c);chats.append(c)
  qa.append(dict(sample_id=r['sample_id'],source_row_sha256=h,actual_fields={k:r[k]for k in FIELDS},criteria=[dict(criterion=k,passed=True,evidence=e)for k,e in [
   ('problem_givens_request_consistency','Read explicit dimensions, cut/piece inventory, grid frame/cap/fold/rotation and base-height restrictions; request uses only supplied text.'),
   ('mathematical_correctness','Fraction and Decimal numeric steps pass; separate finite oracle checks complete inventory, coordinates or cell counts rather than reparsing explanations.'),
   ('reason_steps_units_check','All actual steps state why the operation/relationship applies; cm²/m², money per area, fraction of one cake and cubic cell scale remain distinct; inverse/conservation checks given.'),
   ('initial_all_hints_no_answer_leak','Read initial and all three hint texts/questions. They request strategy, inventory, unit or constraint checks without filling requested quantity, final choice or whole solution.'),
   ('grounded_student_work_missing_data','Only exact provided synthetic quote corrected; no hidden student thought, unseen image, unperformed measurement or physical folding success claimed.'),
   ('original_grade_and_structure',r['pedagogical_review_decision']),
   ('provenance_scope_preservation','Owner-preauthorized drafting, no human content signoff; finite text-only enrichment; previous batches preserved; 495core unchanged.')]],root_cross_review_status='PENDING',human_review_claimed=False))
 assert len(chats)==48
 jl('chat.jsonl',chats);jl('selfqa7.jsonl',qa);jl('independent_oracles.jsonl',oracles);jl('numeric_fraction_decimal.jsonl',numeric)
 for p,h in snapshots.items():assert sha(Path(p).read_bytes())==h
 files=['cases.jsonl','chat.jsonl','selfqa7.jsonl','independent_oracles.jsonl','numeric_fraction_decimal.jsonl','nearest_actual_fullfields.jsonl','actual_page_receipts_readback.jsonl','candidate_task_snapshot.json','independent_oracle.py']
 write('manifest.json',dict(status='12_DRAFTS_SELF_QA_PASSED_ROOT_CROSS_QA_PENDING',case_count=12,chat_count=48,master_counts=dict(Counter(r['coverage']['finite_master_id']for r in ROWS)),numeric_steps=len(numeric),oracles=12,actual_nearest_rows=len(near),inherited_page_receipts=len(pages),helper_sha256=sha(Path(__file__).read_bytes()),input_projection_sha256=sha(PROJECTION.read_bytes()),source_files=[dict(file=n,bytes=(OUT/n).stat().st_size,sha256=sha((OUT/n).read_bytes()))for n in files],prior_case_hashes=snapshots,prior_unchanged=True,training_started=False,drive_mutated=False,all_sgk_forms_covered=False))
 print(jd(dict(cases=12,chats=48,numeric_steps=len(numeric),oracles=12,cases_sha256=sha((OUT/'cases.jsonl').read_bytes()),chat_sha256=sha((OUT/'chat.jsonl').read_bytes()),no_training=True)))
if __name__=='__main__':main()
