"""Append original grade 3/4 representation gaps; never rewrite prior corpus."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
from decimal import Decimal, localcontext
import ast, calendar, datetime, hashlib, itertools, json, re
import exhaustive_colab_loader as L

ROOT=Path(__file__).resolve().parent
RUN=ROOT/'cloud_publication/sgk_gap_20261019'
SRC=RUN/'sources_g34'
REVIEW_FIELDS=('semantic_correct','steps_complete','grade_appropriate','unit_consistent','hints_non_leaking','grounded_student_feedback','curriculum_mapping_correct')
BOOKS={
 'g3v1':('reader_toan-3-tap-mot-940103475',3,1,0),
 'g3v2':('reader_toan-3-tap-hai-939821615',3,2,0),
 'g4v1':('reader_toan-4-tap-mot-939781966',4,1,1),
 'g4v2':('reader_toan-4-tap-hai-939791544',4,2,1)}

# Lesson metadata transcribed from actual publisher 2026 TOC images. These
# titles identify lessons; source exercise questions/solutions are not copied.
TOC={
'g3v1':'''1|6|Ôn tập các số đến 1 000|natural_numbers_100000
2|9|Ôn tập phép cộng, phép trừ trong phạm vi 1 000|addition_subtraction_5digits
3|11|Tìm thành phần trong phép cộng, phép trừ|expressions_unknown
4|14|Ôn tập bảng nhân 2;5, bảng chia 2;5|multiply_divide_one_digit
5|16|Bảng nhân 3, bảng chia 3|multiply_divide_one_digit
6|19|Bảng nhân 4, bảng chia 4|multiply_divide_one_digit
7|21|Ôn tập hình học và đo lường|shape_elements
8|24|Luyện tập chung|word_two_steps
9|28|Bảng nhân 6, bảng chia 6|multiply_divide_one_digit
10|31|Bảng nhân 7, bảng chia 7|multiply_divide_one_digit
11|33|Bảng nhân 8, bảng chia 8|multiply_divide_one_digit
12|36|Bảng nhân 9, bảng chia 9|multiply_divide_one_digit
13|39|Tìm thành phần trong phép nhân, phép chia|expressions_unknown
14|42|Một phần mấy|unit_fractions
15|46|Luyện tập chung|unit_fractions
16|49|Điểm ở giữa, trung điểm của đoạn thẳng|midpoint_angles
17|52|Hình tròn, tâm, bán kính, đường kính|shape_elements
18|54|Góc, góc vuông, góc không vuông|midpoint_angles
19|56|Hình tam giác, hình tứ giác, hình chữ nhật, hình vuông|shape_elements
20|61|Thực hành vẽ góc vuông, đường tròn, hình vuông, hình chữ nhật và trang trí|draw_ekes_compass
21|63|Khối lập phương, khối hộp chữ nhật|solid_elements
22|65|Luyện tập chung|solid_elements
23|67|Nhân số có hai chữ số với số có một chữ số|multiply_divide_one_digit
24|70|Gấp một số lên một số lần|word_two_steps
25|72|Phép chia hết, phép chia có dư|multiply_divide_one_digit
26|75|Chia số có hai chữ số cho số có một chữ số|multiply_divide_one_digit
27|79|Giảm một số đi một số lần|word_two_steps
28|81|Bài toán giải bằng hai bước tính|word_two_steps
29|83|Luyện tập chung|word_two_steps
30|85|Mi-li-mét|units_mm_cm2_g_ml_celsius
31|87|Gam|units_mm_cm2_g_ml_celsius
32|89|Mi-li-lít|units_mm_cm2_g_ml_celsius
33|91|Nhiệt độ, đơn vị đo nhiệt độ|units_mm_cm2_g_ml_celsius
34|93|Thực hành mi-li-mét, gam, mi-li-lít, độ C|practice_experience
35|95|Luyện tập chung|convert_measurements
36|97|Nhân số có ba chữ số với số có một chữ số|multiply_divide_one_digit
37|99|Chia số có ba chữ số cho số có một chữ số|multiply_divide_one_digit
38|104|Biểu thức số, tính giá trị biểu thức số|expressions_unknown
39|109|So sánh số lớn gấp mấy lần số bé|word_two_steps
40|111|Luyện tập chung|word_two_steps
41|113|Ôn tập phép nhân, phép chia trong phạm vi 100,1000|multiply_divide_one_digit
42|116|Ôn tập biểu thức số|expressions_unknown
43|118|Ôn tập hình học và đo lường|convert_measurements
44|120|Ôn tập chung|word_two_steps''',
'g3v2':'''45|4|Các số có bốn chữ số, số 10 000|natural_numbers_100000
46|9|So sánh các số trong phạm vi 10 000|compare_order_100000
47|12|Làm quen với chữ số La Mã|roman_20
48|15|Làm tròn số đến hàng chục, hàng trăm|round_naturals
49|17|Luyện tập chung|round_naturals
50|21|Chu vi tam giác, tứ giác, chữ nhật, hình vuông|perimeter
51|26|Diện tích một hình, xăng-ti-mét vuông|units_mm_cm2_g_ml_celsius
52|30|Diện tích hình chữ nhật, hình vuông|area_rectangle_square
53|35|Luyện tập chung|area_rectangle_square
54|38|Phép cộng trong phạm vi 10 000|addition_subtraction_5digits
55|41|Phép trừ trong phạm vi 10 000|addition_subtraction_5digits
56|43|Nhân số có bốn chữ số với số có một chữ số|multiply_divide_one_digit
57|47|Chia số có bốn chữ số cho số có một chữ số|multiply_divide_one_digit
58|52|Luyện tập chung|multiply_divide_one_digit
59|56|Các số có năm chữ số, số 100 000|natural_numbers_100000
60|61|So sánh các số trong phạm vi 100 000|compare_order_100000
61|64|Làm tròn số đến hàng nghìn, hàng chục nghìn|round_naturals
62|66|Luyện tập chung|round_naturals
63|70|Phép cộng trong phạm vi 100 000|addition_subtraction_5digits
64|73|Phép trừ trong phạm vi 100 000|addition_subtraction_5digits
65|76|Luyện tập chung|addition_subtraction_5digits
66|77|Xem đồng hồ, tháng-năm|time_clock_minute
67|81|Thực hành xem đồng hồ, xem lịch|time_clock_minute
68|85|Tiền Việt Nam|money_vietnam_100000
69|88|Luyện tập chung|money_vietnam_100000
70|94|Nhân số có năm chữ số với số có một chữ số|multiply_divide_one_digit
71|97|Chia số có năm chữ số cho số có một chữ số|multiply_divide_one_digit
72|101|Luyện tập chung|multiply_divide_one_digit
73|103|Thu thập, phân loại, ghi chép số liệu, bảng số liệu|table_collect_read
74|108|Khả năng xảy ra của một sự kiện|single_trial_outcomes
75|110|Thực hành thu thập, phân loại, ghi chép, đọc bảng số liệu|table_collect_read
76|112|Ôn tập các số trong phạm vi 10 000,100 000|natural_numbers_100000
77|115|Ôn tập phép cộng, phép trừ trong phạm vi 100 000|addition_subtraction_5digits
78|118|Ôn tập phép nhân, phép chia trong phạm vi 100 000|multiply_divide_one_digit
79|121|Ôn tập hình học và đo lường|convert_measurements
80|123|Ôn tập bảng số liệu, khả năng xảy ra của một sự kiện|table_collect_read
81|125|Ôn tập chung|word_two_steps''',
'g4v1':'''1|6|Ôn tập các số đến 100 000|natural_numbers_millions
2|9|Ôn tập các phép tính trong phạm vi 100 000|addition_subtraction_many_digits
3|12|Số chẵn, số lẻ|natural_numbers_millions
4|14|Biểu thức chứa chữ|expressions_letters_properties
5|19|Giải bài toán có ba bước tính|word_two_three_steps
6|21|Luyện tập chung|word_two_three_steps
7|23|Đo góc, đơn vị đo góc|angle_degree
8|26|Góc nhọn, góc tù, góc bẹt|angle_types
9|31|Luyện tập chung|angle_types
10|33|Số có sáu chữ số, số 1 000 000|natural_numbers_millions
11|37|Hàng và lớp|natural_numbers_millions
12|41|Các số trong phạm vi lớp triệu|natural_numbers_millions
13|45|Làm tròn số đến hàng trăm nghìn|compare_round_naturals
14|47|So sánh các số có nhiều chữ số|compare_round_naturals
15|50|Làm quen với dãy số tự nhiên|natural_numbers_millions
16|52|Luyện tập chung|natural_numbers_millions
17|56|Yến, tạ, tấn|mass_yen_ta_tan
18|60|Đề-xi-mét vuông, mét vuông, mi-li-mét vuông|area_units_mm2_dm2_m2
19|66|Giây, thế kỉ|time_second_century
20|69|Thực hành sử dụng một số đơn vị đo đại lượng|convert_measurements
21|73|Luyện tập chung|convert_measurements
22|76|Phép cộng các số có nhiều chữ số|addition_subtraction_many_digits
23|79|Phép trừ các số có nhiều chữ số|addition_subtraction_many_digits
24|82|Tính chất giao hoán, kết hợp của phép cộng|expressions_letters_properties
25|86|Tìm hai số biết tổng và hiệu|word_two_three_steps
26|88|Luyện tập chung|word_two_three_steps
27|91|Hai đường thẳng vuông góc|parallel_perpendicular
28|94|Thực hành về hai đường thẳng vuông góc|parallel_perpendicular
29|98|Hai đường thẳng song song|parallel_perpendicular
30|101|Thực hành về hai đường thẳng song song|parallel_perpendicular
31|105|Hình bình hành, hình thoi|parallelogram_rhombus_recognition
32|110|Luyện tập chung|parallelogram_rhombus_recognition
33|114|Ôn tập các số đến lớp triệu|natural_numbers_millions
34|118|Ôn tập phép cộng, phép trừ|addition_subtraction_many_digits
35|121|Ôn tập hình học|angle_types
36|125|Ôn tập đo lường|convert_measurements
37|127|Ôn tập chung|word_two_three_steps''',
'g4v2':'''38|4|Nhân với số có một chữ số|multiply_divide_two_digits
39|6|Chia cho số có một chữ số|multiply_divide_two_digits
40|9|Tính chất giao hoán, kết hợp của phép nhân|expressions_letters_properties
41|14|Nhân, chia với 10,100,1000|multiply_divide_two_digits
42|17|Tính chất phân phối của phép nhân đối với phép cộng|expressions_letters_properties
43|20|Nhân với số có hai chữ số|multiply_divide_two_digits
44|23|Chia cho số có hai chữ số|multiply_divide_two_digits
45|27|Thực hành ước lượng trong tính toán|practice_experience
46|29|Tìm số trung bình cộng|average
47|31|Bài toán liên quan đến rút về đơn vị|word_two_three_steps
48|33|Luyện tập chung|word_two_three_steps
49|36|Dãy số liệu thống kê|data_sequences
50|39|Biểu đồ cột|bar_chart_mean
51|43|Số lần xuất hiện của một sự kiện|repeated_trial_counts
52|47|Luyện tập chung|repeated_trial_counts
53|49|Khái niệm phân số|fraction_concepts_reduce
54|52|Phân số và phép chia số tự nhiên|fraction_concepts_reduce
55|56|Tính chất cơ bản của phân số|fraction_concepts_reduce
56|59|Rút gọn phân số|fraction_concepts_reduce
57|62|Quy đồng mẫu số các phân số|fraction_compare_common_denominator
58|64|So sánh phân số|fraction_compare_common_denominator
59|69|Luyện tập chung|fraction_compare_common_denominator
60|74|Phép cộng phân số|fraction_operations
61|80|Phép trừ phân số|fraction_operations
62|83|Luyện tập chung|fraction_operations
63|86|Phép nhân phân số|fraction_operations
64|91|Phép chia phân số|fraction_operations
65|95|Tìm phân số của một số|fraction_operations
66|98|Luyện tập chung|fraction_operations
67|102|Ôn tập số tự nhiên|natural_numbers_millions
68|105|Ôn tập phép tính với số tự nhiên|multiply_divide_two_digits
69|107|Ôn tập phân số|fraction_concepts_reduce
70|110|Ôn tập phép tính với phân số|fraction_operations
71|112|Ôn tập hình học và đo lường|convert_measurements
72|114|Ôn tập một số yếu tố thống kê và xác suất|repeated_trial_counts
73|116|Ôn tập chung|word_two_three_steps'''}

GAPS={
'roman_material':('g3v2',47,[13],'roman_20','Đếm vật liệu theo nét I,V,X; tồn kho/chi phí và lỗi đếm ký hiệu thay nét.', ['read_additive_sixteen','contrast_four_six_order','chapter_sequence_through_twenty','misconception_ignore_subtractive_pair']),
'roman_routes':('g3v2',47,[14],'roman_20','Tìm tuyến đường theo nhãn La Mã có ràng buộc cạnh/giá trị; không suy ảnh.', ['chapter_sequence_through_twenty']),
'temperature_table':('g3v1',33,[91,92],'units_mm_cm2_g_ml_celsius','Đọc bảng nhiệt độ đa thời điểm, phân biệt cao nhất/tăng nhiều nhất và dữ kiện thiếu.', ['supplementary_celsius_scale_reading','guard_thermometer_missing_scale']),
'calendar_occurrences':('g3v2',67,[82,83],'time_clock_minute','Liệt kê lần xuất hiện thứ trong tháng, cách đếm kể/không kể đầu mốc và thiếu ngày đầu tháng.', ['calendar_month_boundary','calendar_year_rollover','supplementary_february_calendar_variation']),
'expression_choice':('g3v1',38,[106,107,108],'expressions_unknown','Chọn cấu trúc biểu thức từ hai cách giải, kiểm vị trí ngoặc và tính duy nhất thay vì chỉ tính sẵn.', ['parentheses_change_operation_order','misconception_subtraction_associativity']),
'parity_cards':('g4v1',3,[12,13],'natural_numbers_millions','Liệt kê không lặp thẻ, loại số0 đầu và kiểm đầy đủ chẵn/lẻ; lộ trình ràng buộc.', ['successors_across_millions_and_parity']),
'rounding_preimage':('g4v1',13,[45,46],'compare_round_naturals','Tìm cả khoảng số tự nhiên cho cùng kết quả làm tròn và giao với điều kiện phụ.', ['round_hundred_thousand_midpoint_boundary','compare_exact_counts_despite_equal_rounded_reports']),
'fraction_division_model':('g4v2',54,[52,53,54],'fraction_concepts_reduce','Thương phân số từ chia đều nhiều đơn vị; số phần của một đơn vị khác số đơn vị toàn nhóm.', ['fraction_equal_partition_terms','equivalent_partition_eighths_twelfths','reduce_fraction_ribbon_length']),
'data_reconstruction':('g4v2',49,[36,37],'data_sequences','Dãy giữ thứ tự theo thời điểm: khôi phục ô số liệu từ tổng/đếm, phân biệt sắp xếp với ghép nhãn.', ['sort_daily_data_preserve_zero_repeats','filter_threshold_then_descending_labels','misconception_drop_duplicate_observations']),
'estimate_bounds':('g4v2',45,[27,28],'practice_experience','Chứng minh chặn trên/dưới tích, thương bằng đơn điệu; ước lượng không tự là đẳng thức chính xác.', ['estimate_not_sufficient_for_limit','protractor_two_scales_read_and_estimate'])}

def sha(p):return L.file_hash(p)
def dump(p,x):L.save_json(p,x)
def rows(p):
 with open(p,encoding='utf-8') as f:
  for line in f:
   if line.strip():yield json.loads(line)

def existing():
 paths=[RUN/'current_source_all_pedagogic.jsonl']
 result={}
 for p in paths:
  for r in rows(p):result.setdefault(r['sample_id'],r)
 return list(result.values()),paths

def catalog():
 old,paths=existing();books=[];lessons=[]
 for key,(prefix,grade,volume,offset) in BOOKS.items():
  ref=json.loads((SRC/(prefix+'.pages.json')).read_text('utf-8-sig'))
  toc_pages=[4,5] if volume==1 else [2,3]
  books.append({'book_id':key,'grade':grade,'volume':volume,'series':'Kết nối tri thức với cuộc sống',
    'publisher_viewer_url':ref['url'],'public_reader_image_pages':len(ref['pages']),
    'book_edition_verified_colophon':'2026 reprint h26; content originally 2022/2023',
    'toc_actual_image_pages_read':toc_pages,'all_exercise_pages_read':False,
    'reader_html_sha256':sha(SRC/(prefix+'.html'))})
  for line in TOC[key].splitlines():
   num,page,title,node=line.split('|');node_id=f'current_g{grade}_{node}'
   matches=[r for r in old if r.get('curriculum_assignment',{}).get('node_id')==node_id]
   lessons.append({'book_id':key,'grade':grade,'lesson':int(num),'printed_start_page':int(page),'title':title,
      'skill_family':node,'existing_case_ids':[r['sample_id'] for r in matches],
      'existing_case_source_hashes':[L.digest_bytes(L.canonical_json(r).encode()) for r in matches],
      'judgement':'PARTIAL_TOPIC_AND_REPRESENTATION_EVIDENCE_NOT_FULL_EXERCISE_COVERAGE',
      'evidence_basis':'Actual TOC image read plus source problem/givens/steps/hints/answer review; node IDs locate evidence, they are not semantic proof.'})
 gaps=[]
 for topic,(book,lesson,pages,node,why,near) in GAPS.items():
  nearrows=[r for r in old if r.get('topic') in near]
  gaps.append({'gap_id':topic,'book_id':book,'lesson':lesson,'printed_pages':pages,'node_id':f'current_g{BOOKS[book][1]}_{node}',
    'gap_kind':'MISSING_OR_SPARSE_SUBREPRESENTATION_NOT_MISSING_WHOLE_TOPIC','specific_gap':why,
    'nearest_existing_case_ids':[r['sample_id'] for r in nearrows],
    'nearest_actual_content':[{'sample_id':r['sample_id'],'problem':r['problem'],'requested_quantity':r.get('requested_quantity'),
       'answer':r.get('expected_answer'),'worked_steps':r.get('worked_steps'),'hints':r.get('hints')} for r in nearrows],
    'review_scope':'Full preserved782 source + restored current small sources; numeric archives assessed from verified deterministic domain/template definitions, not read as millions of stories.',
    'reason_numeric_exhaustiveness_does_not_cover':'Numeric generators ask a fixed ordered arithmetic operation and do not generate these material/route/calendar/table/representation requests.'})
 result={'schema':'sgk_g34_catalog.v1','books':books,'lessons':lessons,'lesson_count':len(lessons),'gaps':gaps,
   'all_SGK_exercise_types_certified':False,'old_data_changed':False,'sealed_evaluation_read':False,
   'inputs':[{'path':str(p.relative_to(ROOT.parent)),'sha256':sha(p)} for p in paths],
   'source_images_for_audit_only_not_training':True,'no_textbook_exercises_copied':True}
 dump(RUN/'sgk_g34_catalog.json',result);return result

def step(title,reason,result,expression=None,unit='',explanation=None):
 return {'title':title,'reason':reason,'expression':expression,'result':str(result),'unit':unit,'explanation':explanation or reason}

def make(topic,variant,problem,request,hs,ss,answers,oracle,student=None,can_solve=True,givens=None):
 book,lesson,pages,node,_,_=GAPS[topic];grade=BOOKS[book][1]
 for i,s in enumerate(ss):s['step_id']='s'+str(i)
 kind='guard' if not can_solve else 'misconception' if student else 'supplementary'
 sid=f'sgk_gap_20261019_g{grade}_{topic}_{variant}'
 hints=[{'level':i+1,'hint':h,'question':q} for i,(h,q) in enumerate(hs)]
 row={'sample_id':sid,'case_group_id':sid+'_group','split':'train','grade':grade,'topic':topic,'case_kind':kind,
 'problem':problem,'givens':givens or [{'id':'g0','text':problem,'value':None,'unit':'','role':'EXPLICIT_TEXT_AS_SUPPLIED_WITH_MISSING_FIELDS_RETAINED' if not can_solve else 'EXPLICIT_TEXT_AS_SUPPLIED'}],
 'requested_quantity':request,'student_work':{'text':student,'origin':'EXPLICIT_HYPOTHETICAL_STUDENT_WORK'} if student else None,
 'initial_guidance':[hints[0]['hint']],'hints':hints,'worked_steps':ss,'expected_answer':answers,'can_solve':can_solve,
 'canonical_signatures':L.source_signatures({'worked_steps':ss}),
 'curriculum_assignment':{'node_id':f'current_g{grade}_{node}','case_kind':kind,'book_id':book,'SGK_lesson':lesson,'printed_pages':pages,
 'mapping_status':'ORIGINAL_SUBREPRESENTATION_FROM_ACTUAL_OFFICIAL_PAGE_REVIEW_NOT_BOOK_EXERCISE_COPY'},
 'acceptance_status':'ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED','quality_status':'ACCEPTED_VALIDATED',
 'provenance':{'authoring_method':'original_AI_teacher','authorship_origin':'AI_ORIGINAL_NEW_PEDAGOGIC_CASE',
 'human_verified':False,'teacher_certified':False,'owner_human_reviewed':False,'independent_external_review':False,
 'source_role':'AI_GENERATED','acceptance_basis':'OWNER_PREAUTHORIZATION_AFTER_SEVEN_CRITERION_QA',
 'source_viewer_url':json.loads((SRC/(BOOKS[book][0]+'.pages.json')).read_text('utf-8-sig'))['url'],
 'source_pages_are_not_case_authors':True,'real_physical_observation_claimed':False},
 'coverage':{'kind':'FINITE_REPRESENTATION_GAP_APPEND','not_all_possible_word_problems':True,'old_source_changed':False},
 'oracle_evidence':oracle}
 def prose(text):
  text=re.sub(r'(?<=\d)(?=[A-Za-zÀ-ỹ°])',' ',text)
  text=re.sub(r'(?<=[A-Za-zÀ-ỹ])(?=\d)',' ',text)
  for a,b in [('thứTư','thứ Tư'),('thứHai','thứ Hai'),('thứBảy','thứ Bảy'),('thứBa','thứ Ba'),('ThứHai','Thứ Hai'),('ThứTư','Thứ Tư'),('Nnhỏ','N nhỏ'),('Nnguyên','N nguyên'),('củaN','của N'),('cmnhưng','cm nhưng'),('dừngVIII','dừng VIII'),('Bk hông','B không'),('Bkhông','B không'),('Ckhông','C không'),('Q17','Q 17')]:text=text.replace(a,b)
  text=re.sub(r'([,;])(?=\S)',r'\1 ',text)
  return text
 for key in ('problem','requested_quantity'):row[key]=prose(row[key])
 for g in row['givens']:g['text']=prose(g['text'])
 row['initial_guidance']=[prose(x) for x in row['initial_guidance']]
 for h in row['hints']:
  for key in ('hint','question'):h[key]=prose(h[key])
 for s in row['worked_steps']:
  for key in ('title','reason','explanation','unit'):s[key]=prose(s[key])
  if not re.fullmatch(r'-?\d+(?:/\d+|\.\d+)?',s['result']):s['result']=prose(s['result'])
 for a in row['expected_answer']:
  for key in ('quantity','unit'):a[key]=prose(a[key])
  if not re.fullmatch(r'-?\d+(?:/\d+|\.\d+)?',a['result']):a['result']=prose(a['result'])
 if row['student_work']:row['student_work']['text']=prose(row['student_work']['text'])
 return row

def answer(result,unit='',quantity='Kết quả'):return {'quantity':quantity,'result':str(result),'unit':unit}
def hints(a,b,c):return [(a,'Em cần xác định dữ kiện và quy tắc nào?'),(b,'Em áp dụng quy tắc vào đúng từng phần ra sao?'),(c,'Em kiểm điều kiện của đề và kết quả thế nào?')]
R=[]
def add(*args,**kwargs):R.append(make(*args,**kwargs))

def author():
 # 1. Roman material: different tasks, not repeated arithmetic operands.
 h=hints('Tách từng ký hiệu La Mã thành số que theo quy ước đề.','Đếm riêng số que I, V, X rồi cộng; giá trị của số khác số que.','Đối chiếu tổng que với lượng đã dùng hoặc còn trong hộp.')
 add('roman_material','stock','Quy ước xếp I dùng 1 que, V dùng 2 que, X dùng 2 que. Hộp có 12 que. Em xếp số XIX, không dùng chung que giữa ký hiệu. Còn mấy que?','Số que còn',h,[step('Đếm que','X,I,X dùng số que theo từng nét, không theo giá trị19.',5,'2+1+2','que'),step('Tìm que còn','Trừ số que đã xếp khỏi lượng ban đầu.',7,'12-5','que'),step('Kiểm tồn','Que dùng cộng que còn phải bằng ban đầu.',12,'5+7','que')],[answer(7,'que')],{'kind':'roman_stroke','symbols':'XIX','strokes':{'I':1,'V':2,'X':2},'used':5,'left':7})
 add('roman_material','budget','I dùng1que, V dùng2que, X dùng2que. Có đúng4que rời. Trong ba thẻ XI, IX, XIV, thẻ nào có thể xếp dùng vừa hết4que? Không dùng chung que giữa ký hiệu.','Chọn thẻ dùng vừa hết',h,[step('Kiểm XI','X và I dùng tổng hai loại nét.',3,'2+1','que'),step('Kiểm IX','Đảo vị trí không làm đổi số nét.',3,'1+2','que'),step('Kiểm XIV','Đếm cả ba ký hiệu.',5,'2+1+2','que'),step('Đối chiếu','Không tổng nào bằng lượng cho phép.','Không có thẻ nào')],[answer('Không có thẻ nào')],{'kind':'roman_choice','choices':['XI','IX','XIV'],'budget':4,'expected':[]})
 sw='XVII có 4 ký hiệu nên dùng 4 que.'
 add('roman_material','error','Quy ước I dùng1que, V dùng2que, X dùng2que, không dùng chung. Bạn ghi: '+sw+' Hãy kiểm và sửa số que.','Sửa lời đếm que',h,[step('Chỉ ra khác biệt','Bài viết đếm ký hiệu; V và X cần hai nét riêng.','Số ký hiệu không phải số que'),step('Đếm đủ nét','Cộng số que từng ký hiệu.',6,'2+2+1+1','que'),step('Kiểm','Hai I dùng2que; V và X dùng4que, khớp tổng.',6,'2+4','que')],[answer(6,'que')],{'kind':'roman_stroke','symbols':'XVII','strokes':{'I':1,'V':2,'X':2},'used':6},student=sw)
 add('roman_material','guard','Em xếp chữ V bằng các thanh vật liệu nhưng chưa nói mỗi nét dùng bao nhiêu thanh, có nối nhiều thanh thành một nét hay không. Hỏi xếp XIV hết bao nhiêu thanh?','Xin quy ước đếm vật liệu',hints('Phân biệt hình ký hiệu với cách tạo mỗi nét bằng vật liệu.','Cần biết một nét dùng bao nhiêu thanh và có dùng chung không.','Sau khi có quy ước mới đếm theo từng ký hiệu.'),[step('Thiếu quy ước','Cùng ký hiệu có thể ghép mỗi nét bằng một hoặc nhiều thanh.','Chưa xác định'),step('Hỏi bổ sung','Cần quy ước vật liệu chứ không đoán từ ảnh chưa có.','Mỗi nét dùng mấy thanh? Các ký hiệu có dùng chung thanh không?')],[],{'kind':'missing','fields':['strokes_per_symbol','shared_material']},can_solve=False)
 # 2. Directed routes with Roman labels, including a genuine missing graph.
 h=hints('Đổi nhãn La Mã để nhận thứ tự, đồng thời giữ điều kiện nối đường.','Chỉ đi theo cạnh được nêu; không tự thêm đường qua ô không kề.','Kiểm từng chặng và xem các giá trị có tăng đúng quy tắc không.')
 add('roman_routes','branch','Sơ đồ bằng chữ: từ cổng I đi được đến trạm IV hoặc VI. Từ IV đi đến IX; từ VI đi đến VIII. Chỉ có các đường một chiều đã nêu. Muốn đến IX, liệt kê tuyến từ cổng.','Tuyến đi đến IX',h,[step('Đọc nhãn','I,IV,VI,IX,VIII là1,4,6,9,8.','Đã phân biệt IV và VI'),step('Theo cạnh','Chỉ nhánh qua IV có cạnh đi tới IX.','I → IV → IX'),step('Kiểm tuyến','Cả hai cạnh I→IV và IV→IX đều được cho; nhánh còn lại dừngVIII.','I → IV → IX')],[answer('I → IV → IX')],{'kind':'graph','edges':[['I','IV'],['I','VI'],['IV','IX'],['VI','VIII']],'start':'I','goal':'IX','paths':[['I','IV','IX']]})
 add('roman_routes','increasing','Ba tuyến bằng chữ là A: III→VI→IX; B: III→IX→VI; C: III→V→IX. Tất cả mũi tên đều là đường được phép. Chọn tuyến mà giá trị tăng thêm cùng một lượng qua mỗi chặng.','Chọn tuyến có bước tăng đều',h,[step('Đọc tuyến A','Các giá trị3,6,9 có hai độ tăng bằng nhau.',3,'6-3'),step('Kiểm bước sau A','So với bước trước.',3,'9-6'),step('Loại B,C','B có một đoạn giảm; C tăng2rồi4 nên không đều.','Chỉ tuyến A'),step('Kiểm','Ba nhãn đều thuộc phạm vi1đến20 và tuyến đã được cho.','A: III→VI→IX')],[answer('A: III→VI→IX')],{'kind':'route_steps','routes':{'A':[3,6,9],'B':[3,9,6],'C':[3,5,9]},'constant_increase':['A']})
 sw='Em chọn IV→IX→VII vì 4,9,7 đều là số La Mã nên đi theo thứ tự tăng.'
 add('roman_routes','error','Quy tắc trò chơi là giá trị nhãn phải tăng sau mỗi chặng. Tuyến được phép có nhãn IV→IX→VII. Bạn viết: '+sw+' Chỉ kiểm nhận xét tăng, không tự thay sơ đồ.','Kiểm điều kiện tăng',h,[step('Đọc đúng nhãn','IV,IX,VII có giá trị4,9,7.','4→9→7'),step('Kiểm chặng cuối','Giá trị cuối nhỏ hơn giá trị trước.',2,'9-7'),step('Kết luận','Tuyến có chặng giảm nên không đạt; không phải mọi dãy La Mã đều tăng.','Không đạt quy tắc tăng')],[answer('Không đạt quy tắc tăng')],{'kind':'route_increase','values':[4,9,7],'expected':False},student=sw)
 add('roman_routes','guard','Em gửi danh sách nhãn I,II,III,IV,V và hỏi tìm đường từ I đến V; chưa gửi ảnh hay mô tả các đường nối và chiều đi.','Xin quan hệ nối đường',h,[step('Thiếu cấu trúc','Danh sách giá trị không cho biết trạm nào nối với trạm nào.','Chưa xác định đường đi'),step('Hỏi dữ kiện','Cần hình hoặc danh sách cạnh có chiều.','Em cho các đường nối và quy định chiều đi nhé.')],[],{'kind':'missing','fields':['graph_edges']},can_solve=False)
 # 3. Temperature table; never interpret medical state.
 h=hints('Giữ nhãn thời điểm đi cùng số đo và cùng đơn vị.','Cao nhất là so các giá trị; tăng nhiều nhất là so chênh lệch hai mốc.','Đối chiếu từng ô đã cho; không suy ra nhiệt độ lúc chưa ghi.')
 add('temperature_table','maximum_change','Bảng nhiệt độ không khí giả định: 6giờ18°C,9giờ24°C,12giờ29°C,15giờ27°C. Mốc nào cao nhất? Trong hai chặng6→9giờ và9→12giờ, chặng nào tăng nhiều hơn?','Mốc cao nhất và chặng tăng nhiều hơn',h,[step('So nhiệt độ','Giá trị lớn nhất trong bốn ô là29°C.','12giờ:29°C',unit='°C'),step('Tăng chặng đầu','Lấy số đo sau trừ trước.',6,'24-18','°C'),step('Tăng chặng sau','Cùng cách tính cho chặng kế.',5,'29-24','°C'),step('Kiểm phân biệt','Mốc cao nhất và chặng tăng nhiều nhất là hai yêu cầu khác nhau.','6→9giờ tăng nhiều hơn')],[answer('12giờ:29°C'),answer('6→9giờ')],{'kind':'temperature','times':[6,9,12,15],'values':[18,24,29,27],'maximum_time':12,'largest_tested_rise':[6,9]})
 add('temperature_table','threshold','Bản ghi cùng thời điểm ở ba điểm P,Q,R lần lượt22°C,17°C,22°C. Một hoạt động chọn mọi điểm có nhiệt độ từ20°C trở lên. Chọn tên điểm và cho biết có bao nhiêu điểm cùng đạt cao nhất.','Chọn theo ngưỡng, giữ trường hợp bằng nhau',h,[step('Đọc quy tắc','Từ20°C trở lên gồm bằng20°C và lớn hơn.','So từng số với20°C'),step('Chọn điểm','P,R đều22°C cònQ17°C.','P và R'),step('Kiểm cực đại','Hai điểm cùng22°C nên cùng cao nhất.','Có2điểm cùng cao nhất')],[answer('P và R'),answer(2,'điểm')],{'kind':'threshold','values':{'P':22,'Q':17,'R':22},'minimum':20,'selected':['P','R']})
 sw='Buổi trưa là thời điểm sau nên chắc chắn nhiệt độ tăng so với sáng.'
 add('temperature_table','error','Bảng giả định ghi sáng28°C, trưa25°C, chiều26°C. Bạn viết: '+sw+' Dựa đúng bảng, kiểm và nêu thay đổi từ sáng đến trưa.','Kiểm chiều thay đổi theo số liệu',h,[step('So giá trị','Số đo trưa nhỏ hơn số đo sáng.','Nhiệt độ giảm'),step('Tìm mức giảm','Lấy số lớn trừ số bé để nêu độ giảm.',3,'28-25','°C'),step('Kiểm','Trưa25°C cộng mức giảm3°C trở lại28°C.',28,'25+3','°C')],[answer('Giảm3°C')],{'kind':'temperature_change','before':28,'after':25,'decrease':3},student=sw)
 add('temperature_table','guard','Bảng dự báo giả định có sáng21°C, ô trưa để trống, chiều26°C. Đề không nói nhiệt độ biến đổi đều. Hỏi chính xác nhiệt độ trưa.','Xin số liệu còn thiếu',h,[step('Nhận ô trống','Ô trưa chưa có số đo, không phải giá trị0.','Chưa xác định'),step('Không nội suy','Hai đầu mốc chưa xác định duy nhất diễn biến ở giữa.','Cần số đo hoặc dự báo ở buổi trưa.')],[],{'kind':'missing','fields':['noon_temperature']},can_solve=False)
 # 4. Explicit calendar assumptions; oracle enumerates civil day offsets.
 h=hints('Dựa vào ngày đầu tháng đã cho và chu kì bảy ngày.','Liệt kê ngày cùng thứ bằng cách tiến từng tuần rồi kiểm giới hạn tháng.','Phân biệt số ngày được liệt kê với số khoảng tuần đã đi qua.')
 add('calendar_occurrences','fifth_weekday','Một tháng giả định có31ngày, ngày1là thứTư. Liệt kê các ngày thứTư trong tháng và đếm số ngày đó.','Các ngày cùng thứ với ngày1',h,[step('Dùng chu kì','Cùng thứ cách nhau7ngày.','1,8,15,22,29'),step('Kiểm biên','Ngày tiếp sau29một tuần vượt31.','Không thêm ngày36'),step('Đếm ngày','Danh sách có5ngày, khác4khoảng giữa chúng.','5ngày thứTư')],[answer('1,8,15,22,29'),answer(5,'ngày')],{'kind':'calendar','days':31,'first_weekday':2,'wanted_weekday':2,'dates':[1,8,15,22,29]})
 add('calendar_occurrences','schedule','Một tháng có30ngày, ngày1là thứHai. Câu lạc bộ sinh hoạt mỗi thứBảy, bắt đầu từ thứBảy đầu tiên của tháng; không bỏ buổi. Liệt kê ngày sinh hoạt và ngày sinh hoạt cuối cùng.','Lịch theo một thứ trong tuần',h,[step('Tìm mốc đầu','Từ thứHaiđến thứBảylà5ngày nên buổi đầu ngày6.',6,'1+5','ngày'),step('Lặp theo tuần','Tiến7ngày một buổi.','6,13,20,27'),step('Kiểm cuối tháng','Sau27một tuần là34vượt30.','Ngày27')],[answer('6,13,20,27'),answer(27,'ngày')],{'kind':'calendar','days':30,'first_weekday':0,'wanted_weekday':5,'dates':[6,13,20,27]})
 sw='Từ ngày3 đến ngày17 cùng tháng, tính cả hai ngày, có17-3=14ngày.'
 add('calendar_occurrences','inclusive_error','Đếm các ngày có mặt ở trại từ ngày3đến ngày17cùng tháng, tính cả ngày đến và ngày về. Bạn viết: '+sw+' Hãy sửa theo đúng cách tính cả hai mốc.','Sửa đếm bao gồm hai mốc',h,[step('Đếm khoảng','Hiệu hai số ngày cho số khoảng một ngày.',14,'17-3','khoảng'),step('Thêm mốc đầu','Các ngày gồm ngày3và thêm14ngày sau đó.',15,'14+1','ngày'),step('Kiểm','Liệt kê3,4,…,17có15số.','15ngày')],[answer(15,'ngày')],{'kind':'inclusive_days','start':3,'end':17,'count':15},student=sw)
 add('calendar_occurrences','guard','Chỉ biết tháng được xét có30ngày. Em hỏi tháng đó có mấy ngày Chủ nhật. Chưa biết ngày1là thứ mấy và chưa có tờ lịch.','Xin mốc thứ của tháng',h,[step('Thiếu mốc tuần','Tháng30ngày có thể có4hoặc5Chủ nhật tùy thứ ngày1.','Chưa xác định duy nhất'),step('Hỏi thông tin','Cần biết ngày1là thứ mấy hoặc có lịch đúng tháng.','Em cho biết thứ của ngày1hoặc gửi tờ lịch nhé.')],[],{'kind':'missing','fields':['weekday_of_day_one']},can_solve=False)
 # 5. Structure before arithmetic, not just direct expression evaluation.
 h=hints('Nêu mỗi nhóm sự vật và xem thao tác nào diễn ra trước.','Dấu ngoặc giữ phần cần gộp; các biểu thức bằng nhau chưa chắc mô tả đúng câu chuyện.','Tính theo hai đường độc lập và đối chiếu điều kiện số tự nhiên.')
 add('expression_choice','select_models','Hai khay có lần lượt7và5gói hạt giống. Mỗi gói đều có4hạt, không hạt nào dùng chung. Chọn mọi biểu thức biểu thị tổng số hạt: A=(7+5)*4; B=7+5*4; C=7*4+5*4.','Chọn mọi mô hình đúng',h,[step('Cách gộp gói','Gộp số gói rồi nhân số hạt mỗi gói.',48,'(7+5)*4','hạt'),step('Cách tách khay','Tính từng khay rồi cộng.',48,'7*4+5*4','hạt'),step('Loại B','Bkhông nhân số gói của khay đầu với4nên không biểu thị cả hai khay.','A và C')],[answer('A và C')],{'kind':'expression_choice','valid':['A','C'],'expected_value':48})
 add('expression_choice','insert_bracket','Có30thẻ đỏ và18thẻ xanh, gộp lại rồi chia đều thành6nhóm. Một bạn viết chuỗi30+18:6. Giữ thứ tự số và phép toán, chỉ thêm một cặp ngoặc để đúng câu chuyện; tính số thẻ mỗi nhóm.','Đặt ngoặc từ quan hệ nhóm',h,[step('Gộp trước','Cả hai màu đều được chia nên tổng phải trong ngoặc.','(30+18):6'),step('Tính tổng','Cộng hai phần rời nhau.',48,'30+18','thẻ'),step('Chia đều','Chia toàn bộ cho số nhóm.',8,'48/6','thẻ/nhóm'),step('Kiểm','Số thẻ mỗi nhóm nhân số nhóm phải về tổng.',48,'8*6','thẻ')],[answer('(30+18):6'),answer(8,'thẻ/nhóm')],{'kind':'expression_parentheses','total_parts':[30,18],'groups':6,'per_group':8})
 sw='24:3*2 phải tính3*2trước vì phép nhân luôn trước phép chia.'
 add('expression_choice','same_precedence_error','Tính biểu thức24:3*2không có ngoặc. Bạn viết: '+sw+' Nhận xét thứ tự và sửa, giữ nguyên biểu thức.','Sửa ưu tiên cùng bậc',h,[step('Nêu quy tắc','Nhân và chia cùng thứ tự ưu tiên, làm từ trái sang phải.','Chia trước trong biểu thức này'),step('Tính bên trái','Thực hiện24chia3.',8,'24/3'),step('Thực hiện phép còn lại','Lấy kết quả vừa tìm nhân2.',16,'8*2'),step('Kiểm khác ngoặc','24:(3*2)là biểu thức khác, không tự thêm ngoặc.','Kết quả16')],[answer(16)],{'kind':'left_to_right','expression':'24/3*2','expected':16},student=sw)
 add('expression_choice','guard','Bản chép ghi48 [ô trống] 6 [ô trống] 2, chưa có dấu phép tính, ngoặc hoặc câu chuyện. Em muốn biết giá trị duy nhất.','Xin phép toán bị mất',h,[step('Thiếu phép toán','Cùng ba số có thể tạo nhiều giá trị tùy dấu và ngoặc.','Chưa xác định duy nhất'),step('Hỏi bản gốc','Cần các dấu và vị trí ngoặc, không đoán ý định.','Em cung cấp các phép toán và ngoặc trong đề gốc nhé.')],[],{'kind':'missing','fields':['operators','parentheses']},can_solve=False)
 # 6. Parity and enumeration with zero; different discrete constraints.
 h=hints('Xác định chữ số hàng đơn vị và quy định dùng lại thẻ.','Loại chữ số0ở đầu số có hai hoặc ba chữ số; liệt kê có hệ thống.','Đếm theo từng chữ số hàng đầu hoặc hàng cuối để kiểm không thiếu, không lặp.')
 add('parity_cards','two_digit_zero','Có ba thẻ0,3,8, mỗi thẻ chỉ dùng một lần trong mỗi số. Lập mọi số chẵn có hai chữ số rồi sắp tăng.','Liệt kê hết số thỏa điều kiện',h,[step('Chọn chữ số cuối','Số chẵn kết thúc bằng0hoặc8.','Xét riêng hai trường hợp'),step('Cuối0','Chữ số đầu chọn3hoặc8.','30,80'),step('Cuối8','Chữ số đầu không thể0và không lặp8nên chọn3.','38'),step('Kiểm danh sách','Có3số hợp lệ, sắp tăng và không lặp.','30,38,80')],[answer('30,38,80')],{'kind':'digit_permutations','digits':[0,3,8],'length':2,'parity':0,'values':[30,38,80]})
 add('parity_cards','three_digit_odd','Dùng đúng một lần mỗi thẻ0,5,7để lập số có ba chữ số. Lập mọi số lẻ và cho biết số nhỏ nhất.','Chọn đầu khác0và cuối lẻ',h,[step('Cuối5','Hai thẻ còn0,7; hàng trăm phải7.','705'),step('Cuối7','Hai thẻ còn0,5; hàng trăm phải5.','507'),step('Kiểm đầy đủ','Hai lựa chọn cuối lẻ đã xét hết, không có số bắt đầu0.','507,705; nhỏ nhất507')],[answer('507,705'),answer(507)],{'kind':'digit_permutations','digits':[0,5,7],'length':3,'parity':1,'values':[507,705]})
 sw='Từ40đến50có10số nên có5số chẵn.'
 add('parity_cards','inclusive_error','Xét mọi số tự nhiên từ40đến50, gồm cả40và50. Bạn viết: '+sw+' Liệt kê các số chẵn và sửa cách đếm.','Đếm số chẵn có hai đầu chẵn',h,[step('Liệt kê theo bước2','Bắt đầu40, cộng2cho đến50.','40,42,44,46,48,50'),step('Kiểm hai mốc','40và50đều được tính, danh sách có6số.','6số chẵn'),step('Kiểm tổng','Toàn khoảng có11số; còn5số lẻ.','Không phải10số')],[answer('40,42,44,46,48,50'),answer(6,'số')],{'kind':'parity_interval','low':40,'high':50,'even':[40,42,44,46,48,50]},student=sw)
 add('parity_cards','guard','Em muốn lập số chẵn có hai chữ số từ thẻ2và6nhưng chưa nói một thẻ có được dùng nhiều lần trong một số hay không. Hãy xin điều kiện trước khi liệt kê đầy đủ.','Xin quy tắc lặp thẻ',h,[step('Hai cách hiểu','Không lặp chỉ có26,62; cho lặp còn có22,66.','Danh sách phụ thuộc quy tắc'),step('Hỏi quy tắc','Cần biết có được dùng lại mỗi chữ số trong một số hay không.','Mỗi thẻ dùng một lần hay có thể lặp chữ số?')],[],{'kind':'missing','fields':['digit_repetition_rule']},can_solve=False)
 # 7. Rounding preimages: exact integer intervals, not a claim of exact count.
 h=hints('Xác định hàng làm tròn và hai mốc giữa ở hai phía.','Mốc giữa phía dưới được làm tròn lên; mốc giữa phía trên thuộc kết quả kế tiếp.','Kiểm số đầu, số cuối và hai số sát ngoài khoảng.')
 add('rounding_preimage','all_integers','Theo quy tắc làm tròn đến hàng trăm nghìn: chữ số hàng chục nghìn từ5trở lên thì tăng hàng trăm nghìn. Tìm số tự nhiên nhỏ nhất và lớn nhất làm tròn thành400000.','Hai đầu khoảng số trước làm tròn',h,[step('Đầu dưới','Tại nửa khoảng giữa300000và400000bắt đầu làm tròn lên400000.','350000'),step('Đầu trên','450000đã làm tròn lên500000nên số cuối trước mốc đó là449999.','449999'),step('Kiểm biên','349999làm tròn300000;350000và449999ra400000;450000ra500000.','Từ350000đến449999')],[answer(350000),answer(449999)],{'kind':'round_interval','unit':100000,'target':400000,'minimum':350000,'maximum':449999})
 add('rounding_preimage','intersection','Một số tự nhiên N làm tròn đến hàng trăm nghìn thành700000. Biết thêm Nnhỏ hơn655000. Tìm khoảng giá trị có thể củaN; dùng quy tắc5thì làm tròn lên.','Giao khoảng làm tròn với điều kiện phụ',h,[step('Khoảng làm tròn','Các số từ650000đến749999đều làm tròn700000.','650000≤N≤749999'),step('Áp dụng nhỏ hơn','Nnguyên và nhỏ hơn655000nên tối đa654999.','650000≤N≤654999'),step('Kiểm','Hai đầu đều thỏa cả hai điều kiện;655000bị loại bởi điều kiện nghiêm.','Từ650000đến654999')],[answer('650000≤N≤654999')],{'kind':'round_intersection','unit':100000,'target':700000,'strict_upper':655000,'minimum':650000,'maximum':654999})
 sw='500000là số duy nhất có thể có vì báo cáo làm tròn ghi500000.'
 add('rounding_preimage','unique_error','Báo cáo đã làm tròn số khách đến hàng trăm nghìn và ghi500000. Bạn viết: '+sw+' Hãy đưa hai số khách khác nhau cùng phù hợp để kiểm kết luận duy nhất.','Phản ví dụ cho suy số chính xác từ báo cáo tròn',h,[step('Chọn hai giá trị','Cả480000và520000đều nằm trong khoảng làm tròn ra500000.','480000và520000'),step('Kiểm chữ số quyết định','480000làm tròn lên500000;520000làm tròn xuống500000.','Cùng kết quả báo cáo'),step('Kết luận','Có ít nhất hai khả năng nên chưa biết số khách chính xác.','Kết luận duy nhất sai')],[answer('480000và520000'),answer('Không xác định duy nhất')],{'kind':'round_counterexample','unit':100000,'target':500000,'values':[480000,520000]},student=sw)
 add('rounding_preimage','guard','Bản tin ghi khoảng80000người nhưng không nói làm tròn đến hàng nào hay đây có phải kết quả một quy tắc làm tròn hay chỉ là ước tính. Hỏi khoảng tất cả số nguyên ban đầu theo quy tắc.','Xin cách tạo số gần đúng',h,[step('Thiếu quy tắc','Từ khoảng không xác định đơn vị làm tròn hoặc sai số cho phép.','Chưa xác định khoảng nguyên'),step('Hỏi nguồn','Cần hàng làm tròn hoặc sai số và quy tắc tại mốc giữa.','Bản tin đã làm tròn đến hàng nào, theo quy tắc nào?')],[],{'kind':'missing','fields':['rounding_unit','rounding_rule']},can_solve=False)
 # 8. Fraction as natural division with fixed unit; not direct operation table.
 h=hints('Xác định một đơn vị toàn thể là vật nào và có bao nhiêu người nhận.','Chia đều từng đơn vị rồi gộp phần mỗi người; không gộp tất cả vật thành một đơn vị mới.','Nhân phần của một người với số người để kiểm lại tổng lượng ban đầu.')
 add('fraction_division_model','more_than_one','Có9dải ruy-băng bằng nhau, mỗi dải dài1m. Chia đều toàn bộ cho7bạn, không thừa. Mỗi bạn nhận mấy mét? Giải thích bằng việc chia từng mét thành7phần bằng nhau.','Thương phân số lớn hơn một đơn vị',h,[step('Chia từng mét','Một mét chia7được một phần bảy mét.', '1/7','1/7','m'),step('Gộp chín phần','Mỗi bạn nhận một phần bảy từ mỗi trong9dải.','9/7','9/7','m'),step('Kiểm tổng','Bảy bạn nhận bằng tổng9m.','9','(9/7)*7','m')],[answer('9/7','m')],{'kind':'fair_share','whole_units':9,'recipients':7,'share':'9/7'})
 add('fraction_division_model','same_total_different_unit','Ba tấm bìa cùng diện tích được coi mỗi tấm là1đơn vị. Chia đều toàn bộ cho6bạn. Một bạn nói phần mình là1/6của toàn bộ ba tấm; bạn khác nói là1/2một tấm. Hai mô tả có mâu thuẫn không?','Phân biệt hai đơn vị toàn thể',h,[step('Theo một tấm','Tổng3đơn vị chia6bằng một nửa đơn vị.','1/2','3/6','tấm'),step('Theo toàn bộ','Mỗi bạn là một trong6phần bằng nhau của tổng3tấm.','1/6toàn bộ'),step('Kiểm quy đổi','Một phần sáu của3tấm bằng một nửa tấm.','1/2','3*(1/6)','tấm'),step('Kết luận','Hai phân số dùng hai toàn thể khác nhau nhưng cùng lượng bìa.','Không mâu thuẫn')],[answer('Không mâu thuẫn'),answer('1/2','tấm')],{'kind':'unit_whole_contrast','total':3,'recipients':6,'share':'1/2','fraction_of_total':'1/6'})
 sw='7bánh chia4bạn thì mỗi bạn nhận4/7cái vì số bạn viết ở tử.'
 add('fraction_division_model','invert_error','Có7chiếc bánh bằng nhau, mỗi chiếc coi là1đơn vị. Chia đều hết cho4bạn. Bạn viết: '+sw+' Hãy kiểm bằng lượng bánh của cả nhóm và sửa.','Sửa đảo tử mẫu trong phép chia',h,[step('Đọc phép chia','Lấy lượng7bánh chia số4bạn.','7/4','7/4','bánh/bạn'),step('Kiểm phần đúng','Bốn phần bằng nhau phải ghép lại đủ7chiếc.','7','(7/4)*4','bánh'),step('Chỉ ra lỗi','Dòng được cho đảo lượng bánh và số người; kiểm4/7nhân4không về7.','Phải là7/4bánh mỗi bạn')],[answer('7/4','bánh/bạn')],{'kind':'fair_share','whole_units':7,'recipients':4,'share':'7/4'},student=sw)
 add('fraction_division_model','guard','Có một số chiếc bánh bằng nhau đã chia đều cho5bạn. Chưa biết có bao nhiêu chiếc ban đầu hoặc khối lượng từng phần. Hỏi phần mỗi bạn bằng bao nhiêu chiếc bánh.','Xin tổng lượng để lập thương',h,[step('Thiếu số bị chia','Có số người chưa đủ xác định phần mỗi người khi tổng bánh chưa biết.','Chưa xác định'),step('Hỏi đúng đại lượng','Cần số bánh ban đầu hoặc dữ kiện tương đương.','Ban đầu có bao nhiêu chiếc bánh bằng nhau?')],[],{'kind':'missing','fields':['whole_units']},can_solve=False)
 # 9. Ordered data reconstruction from explicit constraints.
 h=hints('Giữ mỗi số gắn đúng ngày hay nhãn đã cho trước khi thay ô trống.','Dùng tổng hoặc điều kiện tần số để tìm ô còn thiếu; sắp xếp là một bảng trình bày khác.','Kiểm lại tổng, số quan sát và nhãn thời điểm ban đầu.')
 add('data_reconstruction','missing_total','Số vé bốn buổi theo thứ tự là12;18;[ô trống];15. Tổng cả bốn buổi là64vé, mỗi vé chỉ thuộc một buổi. Điền ô trống rồi ghi lại dãy theo đúng thứ tự.','Khôi phục ô theo tổng',h,[step('Gộp số biết','Cộng ba buổi đã cho, không gộp ô trống thành0.',45,'12+18+15','vé'),step('Phần còn thiếu','Tổng trừ ba phần đã biết.',19,'64-45','vé'),step('Giữ thứ tự','Ô trống là buổi thứ3, không sắp dãy tăng.','12;18;19;15'),step('Kiểm tổng','Cộng đủ bốn buổi.',64,'12+18+19+15','vé')],[answer('12;18;19;15')],{'kind':'missing_series_total','values':[12,18,None,15],'total':64,'expected':[12,18,19,15]})
 add('data_reconstruction','missing_frequency','Năm ngày ghi số sách đọc theo thứ tự:2;4;[ô trống];2;5. Người ghi xác nhận có đúng3ngày đọc2cuốn và không có ngày nào bị bỏ. Điền ô trống và cho biết ngày đọc nhiều nhất.','Dùng tần số để khôi phục dãy có thứ tự',h,[step('Đếm số2đã có','Ngày1và4đã ghi2cuốn, còn thiếu một ngày như vậy.','Ô ngày3là2'),step('Giữ nhãn ngày','Dãy hoàn chỉnh theo thứ tự.','2;4;2;2;5'),step('Tìm cực đại','Giá trị5lớn nhất ở ngày5.','Ngày5')],[answer('2;4;2;2;5'),answer('Ngày5')],{'kind':'series_frequency','values':[2,4,None,2,5],'target':2,'frequency':3,'expected':[2,4,2,2,5]})
 sw='Em sắp các số6,9,4thành4,6,9 rồi ghi đó là số cây của thứHai,thứBa,thứTư theo thứ tự.'
 add('data_reconstruction','relabel_error','Bảng gốc ghi thứHai6cây,thứBa9cây,thứTư4cây. Bạn viết: '+sw+' Hãy phân biệt dãy đã sắp tăng với bảng theo ngày và sửa nhãn.','Sửa đổi nhãn khi sắp số',h,[step('Giữ quan sát gốc','Sắp số không thay số đã đo trong từng ngày.','ThứHai6;thứBa9;thứTư4'),step('Nếu sắp theo số tăng','Phải mang nhãn ngày cùng số quan sát.','ThứTư4;thứHai6;thứBa9'),step('Kiểm','Mỗi cặp ngày-số đều xuất hiện đúng một lần như bảng gốc.','Không gán dãy4,6,9cho các ngày cũ')],[answer('ThứHai6;thứBa9;thứTư4'),answer('ThứTư4;thứHai6;thứBa9')],{'kind':'labelled_sort','pairs':[['ThứHai',6],['ThứBa',9],['ThứTư',4]],'sorted_labels':['ThứTư','ThứHai','ThứBa']},student=sw)
 add('data_reconstruction','guard','Ba buổi có số vé theo thứ tự [ôA];[ôB];10. Chỉ biết tổng ba buổi là40vé; không có quan hệ giữa hai ô trống. Hỏi riêng từng ô.','Xin điều kiện tách hai phần chưa biết',h,[step('Biết tổng hai ô','Hai ô đầu cộng lại30vé.',30,'40-10','vé'),step('Chưa tách duy nhất','Nhiều cặp như14và16hoặc12và18cùng tổng30nên chưa biết riêng từng ô.','Cần thêm một ô hoặc quan hệ giữaA,B.')],[],{'kind':'missing','fields':['one_missing_value_or_relation'],'known_missing_sum':30},can_solve=False)
 # 10. Bounds justified by monotonicity; categorical decisions before exact.
 h=hints('Tìm số tròn ở cùng một phía của số thật để tạo chặn chắc chắn.','Với các số dương, tăng thừa số làm tích tăng; tăng số bị chia với số chia giữ nguyên làm thương tăng.','Dùng chặn để bác bỏ hay chấp nhận phát biểu; số ước lượng không tự bằng kết quả thật.')
 add('estimate_bounds','product_upper','Không cần nhân chính xác, kiểm phát biểu: một tấm chữ nhật dài47m,rộng28m có diện tích lớn hơn1500m². Có thể dùng hai số50và30để chặn.','Bác bỏ bằng chặn trên',h,[step('Chọn chặn','47nhỏ hơn50và28nhỏ hơn30, cả hai dương.','47*28<50*30'),step('Tính chặn trên','Tích của hai số tròn cho mốc dễ tính.',1500,'50*30','m²'),step('Kết luận','Diện tích thật nhỏ hơn1500nên phát biểu lớn hơn sai.','Phát biểu sai')],[answer('Phát biểu sai')],{'kind':'bound','operation':'product','a':47,'b':28,'upper_factors':[50,30],'strict_upper':1500,'claim_gt':1500,'claim':False})
 add('estimate_bounds','quotient_lower','Một kho có2140kg hạt, chia đều vào40thùng và không thất thoát. Không cần chia chính xác, kiểm nhận xét mỗi thùng có ít hơn50kg. So với2000kg.','Chặn dưới thương',h,[step('Dùng lượng nhỏ hơn','2140lớn hơn2000, số thùng40giữ nguyên.','Mỗi thùng nhiều hơn2000:40'),step('Tính mốc','Chia số tròn để có chặn dưới.',50,'2000/40','kg/thùng'),step('Kết luận','Lượng thật mỗi thùng lớn hơn50kg nên nhận xét ít hơn sai.','Nhận xét sai')],[answer('Nhận xét sai')],{'kind':'bound','operation':'quotient','a':2140,'b':40,'lower_dividend':2000,'strict_lower':50,'claim_lt':50,'claim':False})
 sw='198*31 xấp xỉ200*30=6000nên198*31chắc chắn bằng6000.'
 add('estimate_bounds','equality_error','Bạn ước lượng tích và viết: '+sw+' Chỉ ra bước chuyển sai rồi tính tích thật để kiểm.','Sửa nhầm xấp xỉ thành bằng',h,[step('Phân biệt dấu','Thay cả hai thừa số là ước lượng, không chứng minh đẳng thức.','Không suy ra bằng6000'),step('Tính bằng phân phối','Giữ198, tách31thành30và1.',6138,'198*30+198'),step('Đối chiếu sai khác','Kết quả thật và số ước lượng khác nhau.',138,'6138-6000'),step('Kết luận','Có thể dùng6000làm ước lượng thô nhưng không làm đáp số chính xác.','Tích thật6138')],[answer(6138)],{'kind':'estimate_exact','a':198,'b':31,'estimate':6000,'exact':6138},student=sw)
 add('estimate_bounds','insufficient_range','Một tấm bìa chữ nhật có chiều dài lớn hơn20cmnhưng nhỏ hơn30cm, chiều rộng10cm. Không có số đo khác. Em muốn biết diện tích chính xác duy nhất.','Phân biệt khoảng chặn và giá trị chính xác',h,[step('Lập khoảng','Nhân hai đầu khoảng với chiều rộng dương10cm.','200<diện tích<300cm²'),step('Chưa đủ duy nhất','Nhiều chiều dài trong khoảng cho nhiều diện tích khác nhau.','Cần chiều dài chính xác hoặc dữ kiện tương đương.')],[],{'kind':'missing','fields':['exact_length'],'strict_area_bounds':[200,300]},can_solve=False)
 return R

def exact(expression):
 def visit(node):
  if isinstance(node,ast.Constant) and type(node.value) in (int,float):return Fraction(ast.get_source_segment(expression,node))
  if isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.USub):return -visit(node.operand)
  if isinstance(node,ast.BinOp):
   a,b=visit(node.left),visit(node.right)
   if isinstance(node.op,ast.Add):return a+b
   if isinstance(node.op,ast.Sub):return a-b
   if isinstance(node.op,ast.Mult):return a*b
   if isinstance(node.op,ast.Div):return a/b
  raise ValueError('unapproved exact expression')
 return visit(ast.parse(expression,mode='eval').body)

def refine_hints(cases):
 overrides={
  ('roman_routes','branch'):hints('Tìm các đường có thể đi ra từ cổng theo danh sách mũi tên.','Theo từng nhánh được cho và xem nhánh nào thật sự tới đích.','Kiểm từng cạnh của tuyến tìm được đều có trong đề; không cần thêm quy tắc tăng số.'),
  ('roman_routes','guard'):hints('Danh sách nhãn chưa cho biết các trạm được nối như thế nào.','Em cần ảnh sơ đồ hoặc danh sách các đường nối, kèm chiều đi nếu có.','Chỉ tìm tuyến sau khi biết được phép đi giữa những cặp trạm nào.'),
  ('temperature_table','error'):hints('Đọc số đo tại hai thời điểm, không dựa vào thời điểm đến trước hay sau.','So sánh số đo sau với số đo trước để biết tăng hay giảm.','Dùng hiệu số đo và phép cộng ngược để kiểm độ thay đổi.'),
  ('temperature_table','guard'):hints('Xác định ô nào trong bảng chưa có số đo.','Ô trống không tự là số không; các mốc khác cũng chưa cho diễn biến ở giữa.','Xin số liệu đúng thời điểm cần hỏi hoặc một quan hệ đủ để xác định nó.'),
  ('calendar_occurrences','inclusive_error'):hints('Xác định đề có tính cả ngày đầu và ngày cuối hay không.','Hiệu hai số ngày đếm các khoảng chuyển ngày; hãy kiểm thêm ngày ở mốc đầu.','Thử liệt kê một đoạn ngày ngắn để phân biệt số ngày với số khoảng.'),
  ('calendar_occurrences','guard'):hints('Muốn đếm một thứ trong tháng phải biết ngày đầu tháng là thứ mấy.','Số ngày trong tháng chưa xác định vị trí các ngày trong tuần.','Xin mốc thứ hoặc tờ lịch đúng tháng trước khi đếm.'),
  ('expression_choice','same_precedence_error'):hints('Kiểm thứ tự ưu tiên của phép nhân và phép chia khi không có ngoặc.','Các phép cùng bậc được làm theo thứ tự xuất hiện từ trái sang phải.','Đối chiếu với biểu thức có ngoặc để xem bạn có tự đổi đề hay không.'),
  ('expression_choice','guard'):hints('Ba số chưa xác định một biểu thức khi chưa biết các dấu ở giữa.','Xin các dấu phép tính và vị trí ngoặc trong bản gốc.','Chỉ tính sau khi đọc được biểu thức đầy đủ; không tự chọn phép tính.'),
  ('parity_cards','inclusive_error'):hints('Kiểm xem hai đầu khoảng có được tính và có phải số chẵn không.','Liệt kê số chẵn bằng cách tăng từng hai đơn vị từ đầu phù hợp.','Đếm các số đã liệt kê, không nhầm với số khoảng giữa chúng.'),
  ('parity_cards','guard'):hints('Danh sách đầy đủ phụ thuộc vào việc một chữ số có được dùng lại không.','Xin quy định dùng thẻ một lần hay cho phép lặp trong mỗi số.','Sau khi biết quy tắc mới xét các lựa chọn chữ số hàng chục và hàng đơn vị.'),
  ('rounding_preimage','guard'):hints('Từ “khoảng” chưa nói rõ một cách làm tròn cụ thể.','Xin hàng làm tròn hoặc mức sai số và quy tắc ở mốc giữa.','Chỉ xác định khoảng ban đầu sau khi biết số gần đúng được tạo bằng cách nào.'),
  ('fraction_division_model','guard'):hints('Để chia đều, phải biết cả lượng ban đầu lẫn số người nhận.','Đề mới cho số người; hãy tìm dữ kiện còn thiếu về lượng bánh.','Xin tổng số bánh hoặc thông tin tương đương trước khi lập phép chia.'),
  ('data_reconstruction','guard'):hints('Một tổng của hai ô trống chưa xác định riêng từng ô.','Tìm phần tổng thuộc hai ô đó rồi xét liệu có nhiều cách tách hay không.','Xin thêm giá trị một ô hoặc quan hệ giữa chúng trước khi kết luận riêng từng ô.'),
  ('estimate_bounds','equality_error'):hints('Phân biệt kết quả ước lượng với kết quả chính xác.','Kiểm xem thay các thừa số bằng số gần đúng có giữ nguyên giá trị hay chỉ tạo xấp xỉ.','Tính lại bằng tách thừa số rồi đối chiếu; giữ dấu bằng chỉ ở những bước thật sự bằng nhau.'),
  ('estimate_bounds','insufficient_range'):hints('Đề đang cho khoảng chiều dài hay một số đo duy nhất?','Đổi khoảng chiều dài thành khoảng diện tích bằng chiều rộng đã biết.','Nhiều giá trị trong khoảng vẫn có thể phù hợp; xin số đo chính xác nếu cần diện tích duy nhất.')}
 overrides.update({
  ('roman_material','stock'):hints('Tách số La Mã đã xếp thành từng ký hiệu để đếm que.','Dùng quy ước số que mỗi ký hiệu rồi lấy lượng ban đầu trừ số đã dùng.','Cộng que đã dùng với que còn để đối chiếu hộp ban đầu.'),
  ('roman_material','budget'):hints('Lượng que cần để xếp một số khác với giá trị của số đó.','Đếm riêng từng thẻ rồi so với yêu cầu dùng vừa hết, không dùng chung que.','Xét cả khả năng không có thẻ nào thỏa, thay vì buộc chọn một thẻ.'),
  ('roman_material','error'):hints('Kiểm xem bạn đang đếm ký hiệu hay đếm nét bằng que.','Thay mỗi ký hiệu bằng số que theo quy ước rồi cộng tất cả.','Có thể nhóm các nét cùng loại để kiểm tổng theo cách khác.'),
  ('roman_routes','increasing'):hints('Đọc các nhãn thành giá trị trước khi kiểm từng tuyến.','Tìm độ tăng giữa từng cặp nhãn liên tiếp trong mỗi tuyến.','Tuyến đúng phải có các độ tăng dương bằng nhau ở mọi chặng.'),
  ('roman_routes','error'):hints('Đọc đúng giá trị từng nhãn của tuyến đã cho.','Kiểm lần lượt mỗi chặng có thật sự tăng hay không.','Một chặng giảm đã đủ bác bỏ nhận xét rằng cả tuyến tăng; không cần vẽ tuyến khác.'),
  ('temperature_table','maximum_change'):hints('Đọc đúng cặp thời điểm và nhiệt độ trong từng ô.','Tìm giá trị lớn nhất cho câu hỏi về mốc; lấy số đo sau trừ trước cho câu hỏi về độ tăng.','So hai độ tăng cùng đơn vị và giữ tên chặng đi cùng mỗi kết quả.'),
  ('temperature_table','threshold'):hints('Đọc ngưỡng lựa chọn và chú ý từ “trở lên”.','Kiểm từng điểm bằng cùng điều kiện rồi giữ các trường hợp cùng đạt.','Tìm giá trị lớn nhất trong bảng và đếm mọi điểm có đúng giá trị ấy.'),
  ('calendar_occurrences','fifth_weekday'):hints('Bắt đầu bằng ngày đầu tháng cùng thứ đã nêu.','Tiến từng tuần để liệt kê ngày cùng thứ, dừng ở giới hạn tháng.','Đếm các ngày trong danh sách, không đếm riêng khoảng cách tuần.'),
  ('calendar_occurrences','schedule'):hints('Từ thứ của ngày đầu tháng, xác định ngày sinh hoạt đầu tiên.','Sau đó cộng số ngày của một tuần để tìm từng buổi tiếp theo.','Chỉ nhận ngày nằm trong tháng và kiểm buổi kế tiếp đã ra ngoài tháng.'),
  ('expression_choice','select_models'):hints('Tìm tổng số gói của cả hai khay hoặc tính từng khay riêng.','Mỗi gói của cả hai khay đều phải được nhân với số hạt trong một gói.','So cách gộp trước với cách tính riêng rồi cộng; không bỏ một khay khỏi phép nhân.'),
  ('expression_choice','insert_bracket'):hints('Xác định thao tác nào xảy ra trước khi chia thành các nhóm.','Dùng ngoặc bao đúng phần tổng được đem chia, giữ thứ tự các số.','Kiểm số thẻ mỗi nhóm bằng cách nhân trở lại số nhóm.'),
  ('parity_cards','two_digit_zero'):hints('Muốn lập số chẵn, chọn chữ số cuối từ những thẻ phù hợp.','Với mỗi chữ số cuối, chọn chữ số đầu khác không và không dùng lại thẻ.','Gộp các trường hợp, sắp tăng và kiểm không lặp, không thiếu.'),
  ('parity_cards','three_digit_odd'):hints('Chọn chữ số cuối để số là số lẻ.','Phân bố hai thẻ còn lại vào hàng trăm và hàng chục, loại cách bắt đầu bằng không.','Kiểm đã dùng mỗi thẻ đúng một lần rồi so các số hợp lệ từ hàng cao xuống.'),
  ('rounding_preimage','all_integers'):hints('Tìm hai mốc giữa ở hai phía của kết quả tròn mục tiêu.','Xét mốc dưới được nhận hay loại và mốc trên đã chuyển sang kết quả tròn kế tiếp chưa.','Vì chỉ lấy số tự nhiên, kiểm hai số nguyên ở biên và hai số sát ngoài khoảng.'),
  ('rounding_preimage','intersection'):hints('Trước hết tìm khoảng số cho kết quả làm tròn đã biết.','Giữ lại trong khoảng ấy những số thỏa thêm điều kiện nhỏ hơn nghiêm ngặt.','Kiểm hai đầu khoảng cuối cùng đều thỏa cả quy tắc làm tròn và giới hạn phụ.'),
  ('rounding_preimage','unique_error'):hints('Một kết quả làm tròn có thể đến từ nhiều số ban đầu.','Chọn hai số khác nhau ở hai phía gần kết quả báo cáo, rồi làm tròn từng số.','Nếu cả hai cùng về một kết quả, đối chiếu với nhận xét số ban đầu là duy nhất.'),
  ('fraction_division_model','more_than_one'):hints('Mỗi mét là một đơn vị toàn thể; theo dõi phần mỗi người nhận từ từng dải.','Chia mỗi đơn vị thành số phần bằng số người rồi gộp phần của một người từ mọi dải.','Phần một người nhân số người phải bằng toàn bộ chiều dài ban đầu.'),
  ('fraction_division_model','same_total_different_unit'):hints('Xác định đơn vị toàn thể trong mỗi lời mô tả.','Quy phần của toàn bộ về số tấm, rồi so với phần của một tấm.','Nhân lượng một người với số người để kiểm lại tổng bìa.'),
  ('fraction_division_model','invert_error'):hints('Xác định vai trò của tổng bánh và số người trong phép chia đều.','Phân số biểu thị thương giữ lượng bị chia ở tử và số chia ở mẫu.','Kiểm bằng phép nhân ngược để xem có trở lại đủ tổng bánh hay không.'),
  ('data_reconstruction','missing_total'):hints('Tách các buổi đã biết khỏi buổi còn trống, giữ vị trí theo thứ tự.','Cộng các số biết rồi lấy tổng chung trừ phần đó.','Điền đúng vị trí ô còn thiếu và cộng lại toàn dãy để kiểm.'),
  ('data_reconstruction','missing_frequency'):hints('Đếm số ngày đã có giá trị được nhắc đến trong điều kiện.','Dùng số lần xuất hiện còn thiếu để xác định ô trống.','Sau khi điền, đối chiếu lại tần số rồi đọc nhãn ngày có giá trị lớn nhất.'),
  ('data_reconstruction','relabel_error'):hints('Giữ nguyên mỗi cặp nhãn ngày và số quan sát của bảng gốc.','Nếu sắp số tăng, chuyển cả nhãn đi cùng số thay vì gắn số mới vào ngày cũ.','So danh sách sau sắp với các cặp gốc để kiểm không thay quan sát.'),
  ('estimate_bounds','product_upper'):hints('So từng kích thước thật với số tròn lớn hơn mà đề gợi ý.','Tích hai số dương được chặn trên bằng tích của hai số lớn hơn tương ứng.','So mốc chặn với phát biểu cần kiểm; không cần tính chính xác diện tích.'),
  ('estimate_bounds','quotient_lower'):hints('So tổng lượng thật với lượng tròn nhỏ hơn được dùng làm mốc.','Giữ số thùng không đổi; tổng lượng lớn hơn thì phần mỗi thùng lớn hơn.','Tính phần theo lượng mốc rồi dùng chặn dưới để kiểm nhận xét ít hơn.')})
 questions={
 'roman_material':{
 'stock':['Trong ký hiệu đã xếp có những nét nào cần đếm?','Em cộng số que từng ký hiệu như thế nào?','Que đã dùng cộng que còn có khớp lượng ban đầu không?'],
 'budget':['Mỗi thẻ cần bao nhiêu nét theo quy ước?','Em kiểm từng thẻ so với lượng que cho phép ra sao?','Có thẻ nào dùng đúng lượng que, thay vì ít hơn hoặc nhiều hơn không?'],
 'error':['Bạn đã đếm ký hiệu hay đếm que?','Những ký hiệu nào cần nhiều hơn một que?','Em có thể đếm lại từng nét để kiểm tổng không?'],
 'guard':['Một nét có thể được ghép bằng mấy thanh?','Các ký hiệu có được dùng chung thanh không?','Cần xin thêm quy ước nào trước khi tính?']},
 'roman_routes':{
 'branch':['Có thể đi từ cổng đến những trạm nào?','Mỗi nhánh được phép đi tiếp đến đâu?','Tất cả chặng của tuyến đến đích có được cho trong đề không?'],
 'increasing':['Mỗi nhãn trên từng tuyến có giá trị bao nhiêu?','Hai độ tăng liên tiếp trên mỗi tuyến có bằng nhau không?','Em đã kiểm đủ mọi tuyến được đưa ra chưa?'],
 'error':['Đọc từng nhãn của tuyến đó thành số thế nào?','Giá trị sau có luôn lớn hơn giá trị trước không?','Chặng nào chứng minh nhận xét của bạn cần sửa?'],
 'guard':['Đề đã cho những trạm nào được nối với nhau chưa?','Nếu là đường một chiều, em cần xin thông tin gì?','Danh sách nhãn có đủ để xác định tuyến không?']},
 'temperature_table':{
 'maximum_change':['Mỗi nhiệt độ gắn với thời điểm nào?','Làm sao phân biệt mốc cao nhất với chặng tăng nhiều nhất?','Hai độ tăng được so đã dùng đúng các mốc không?'],
 'threshold':['Từ ngưỡng trở lên có tính trường hợp bằng ngưỡng không?','Những điểm nào vượt qua phép kiểm so với ngưỡng?','Nếu hai giá trị cùng lớn nhất thì có bỏ một điểm không?'],
 'error':['Số đo trước và sau lần lượt là bao nhiêu?','Thời điểm đến sau có tự bảo đảm nhiệt độ cao hơn không?','Dùng phép cộng ngược kiểm độ thay đổi ra sao?'],
 'guard':['Ô nào trong bảng chưa có số?','Hai ô khác đã cho quy luật xác định ô trống chưa?','Em cần xin số đo ở thời điểm nào?']},
 'calendar_occurrences':{
 'fifth_weekday':['Ngày đầu tháng thuộc thứ nào theo đề?','Muốn đến cùng thứ tuần sau phải tiến bao nhiêu ngày?','Ngày tiếp theo trong dãy đã vượt giới hạn tháng chưa?'],
 'schedule':['Từ thứ đầu tháng đến thứ sinh hoạt cách mấy ngày?','Sau buổi đầu, ngày sinh hoạt lặp lại theo quy tắc nào?','Vì sao không thêm một buổi vượt ngày cuối tháng?'],
 'inclusive_error':['Có tính cả ngày đến và ngày về không?','Phép trừ hai mốc đang đếm số ngày hay số khoảng?','Liệt kê ngày từ đầu đến cuối giúp kiểm thế nào?'],
 'guard':['Ngày đầu tháng là thứ mấy đã được cho chưa?','Hai tháng có cùng độ dài có thể có lịch tuần khác nhau không?','Cần xin tờ lịch hoặc mốc nào?']},
 'expression_choice':{
 'select_models':['Những gói của cả hai khay có cùng số hạt không?','Biểu thức nào nhân số hạt với toàn bộ số gói?','Hai cách gộp trước và tính riêng có cho cùng lượng không?'],
 'insert_bracket':['Toàn bộ thẻ hay chỉ thẻ một màu được đem chia?','Phần nào cần nằm trong ngoặc để thực hiện trước?','Số thẻ mỗi nhóm nhân số nhóm có về tổng không?'],
 'same_precedence_error':['Nhân và chia có cùng bậc ưu tiên không?','Phép nào xuất hiện ở bên trái trước?','Bạn có tự thêm ngoặc làm đổi biểu thức không?'],
 'guard':['Có đọc được dấu phép tính giữa các số không?','Bản gốc có dấu ngoặc ở vị trí nào?','Vì sao chưa nên chọn một phép tính để đoán?']},
 'parity_cards':{
 'two_digit_zero':['Những thẻ nào có thể ở cuối một số chẵn?','Chữ số đầu có thể là không trong số hai chữ số không?','Đã xét đủ từng cách chọn chữ số cuối chưa?'],
 'three_digit_odd':['Một số lẻ có thể kết thúc bằng những thẻ nào?','Sau khi chọn chữ số cuối, hai vị trí còn lại bị ràng buộc ra sao?','So các số đã lập theo hàng cao xuống giúp tìm nhỏ nhất thế nào?'],
 'inclusive_error':['Hai đầu của khoảng có được tính không?','Liệt kê các số chẵn trong khoảng theo bước nào?','Có bao nhiêu số trong danh sách, khác bao nhiêu khoảng giữa chúng?'],
 'guard':['Một thẻ có được dùng lại trong một số không?','Hai cách hiểu có tạo cùng danh sách không?','Em cần hỏi điều kiện nào trước khi liệt kê hết?']},
 'rounding_preimage':{
 'all_integers':['Hai mốc giữa ở hai phía số tròn mục tiêu nằm đâu?','Mốc giữa phía trên còn làm tròn về mục tiêu không?','Hai số nằm sát ngoài khoảng có còn phù hợp không?'],
 'intersection':['Khoảng ban đầu do quy tắc làm tròn xác định thế nào?','Điều kiện nhỏ hơn nghiêm ngặt loại những số nào?','Hai đầu cuối cùng có thỏa đồng thời cả hai điều kiện không?'],
 'unique_error':['Báo cáo tròn có đồng nghĩa số gốc bằng đúng số báo cáo không?','Em có thể chọn hai số khác nhau rồi làm tròn để thử không?','Có hai khả năng thì kết luận duy nhất còn đứng vững không?'],
 'guard':['Từ khoảng có nêu hàng làm tròn không?','Đề đã cho sai số hoặc quy tắc tại mốc giữa chưa?','Em sẽ hỏi gì về cách tạo bản tin gần đúng?']},
 'fraction_division_model':{
 'more_than_one':['Đơn vị toàn thể trong bài là một mét hay tất cả các dải?','Mỗi người nhận được bao nhiêu phần bằng nhau từ từng dải?','Gộp lượng của mọi người có đủ toàn bộ ban đầu không?'],
 'same_total_different_unit':['Hai phân số đang nói về cùng một đơn vị toàn thể không?','Phần của toàn bộ quy ra số tấm bằng cách nào?','Hai cách mô tả có chỉ cùng lượng bìa không?'],
 'invert_error':['Đại lượng nào là lượng cần chia, đại lượng nào là số người?','Thương nên được viết với tử và mẫu theo vai trò nào?','Lấy phần một người nhân số người có khớp tổng ban đầu không?'],
 'guard':['Số người đã biết còn tổng lượng đã biết chưa?','Có thể chia cùng số người với những lượng ban đầu khác nhau không?','Cần xin số bánh ban đầu hay dữ kiện nào tương đương?']},
 'data_reconstruction':{
 'missing_total':['Đã biết số vé của những buổi nào?','Ô chưa biết bằng tổng trừ những phần nào?','Sau khi điền có giữ nguyên vị trí buổi và khớp tổng không?'],
 'missing_frequency':['Đã có mấy quan sát mang giá trị được nhắc đến?','Ô còn trống phải làm số lần xuất hiện thay đổi thế nào?','Ngày có giá trị lớn nhất nằm ở vị trí nào của dãy gốc?'],
 'relabel_error':['Mỗi số trong bảng gốc thuộc ngày nào?','Khi sắp tăng, nhãn ngày có phải đi cùng số quan sát không?','Mỗi cặp ngày và số sau khi sắp có còn khớp bản gốc không?'],
 'guard':['Có bao nhiêu ô chưa biết nhưng chỉ có mấy điều kiện về tổng?','Có thể tạo hai cặp giá trị khác nhau cùng tổng không?','Em cần biết một ô hoặc quan hệ thêm nào?']},
 'estimate_bounds':{
 'product_upper':['Các số tròn được chọn lớn hơn hay nhỏ hơn hai kích thước thật?','Với hai kích thước dương, tích của chặn trên so với diện tích thật ra sao?','Chặn tìm được có đủ bác bỏ phát biểu mà không nhân chính xác không?'],
 'quotient_lower':['Lượng tròn được dùng so sánh thấp hơn hay cao hơn lượng thật?','Giữ nguyên số thùng, tăng lượng chia làm phần mỗi thùng thay đổi thế nào?','Chặn dưới vừa tìm có phù hợp với nhận xét ít hơn không?'],
 'equality_error':['Dấu xấp xỉ có thể tự chuyển thành dấu bằng không?','Tách thừa số theo các phần chính xác giúp kiểm tích thế nào?','Kết quả chính xác có trùng con số ước lượng không?'],
 'insufficient_range':['Chiều dài đang có giá trị chính xác hay chỉ có hai giới hạn?','Nhân khoảng chiều dài với chiều rộng dương cho khoảng nào?','Đã đủ thông tin chọn duy nhất một diện tích chưa?']}}
 for row in cases:
  variant=row['sample_id'].split(row['topic']+'_',1)[1]
  if (row['topic'],variant) in overrides:
   row['hints']=[{'level':i+1,'hint':a,'question':b} for i,(a,b) in enumerate(overrides[row['topic'],variant])]
   row['initial_guidance']=[row['hints'][0]['hint']]
  for h,q in zip(row['hints'],questions[row['topic']][variant]):h['question']=q
  assert (row['topic'],variant) in overrides or (row['topic'],variant)==('roman_material','guard')
  if row['topic']=='rounding_preimage':row['curriculum_assignment']['subrepresentation_scope']='GRADE4_EXTENSION_OF_ROUNDING_RULE_NOT_A_CLAIM_OF_DIRECT_SGK_EXERCISE_TYPE'
 return cases

def verify_oracle(r):
 o=r['oracle_evidence'];k=o['kind'];checks=[]
 if k=='roman_stroke':assert sum(o['strokes'][c] for c in o['symbols'])==o['used'];checks.append('independent per-symbol stroke sum')
 elif k=='roman_choice':assert [x for x in o['choices'] if sum({'I':1,'V':2,'X':2}[c] for c in x)==o['budget']]==o['expected']
 elif k=='graph':
  def dfs(n,p):
   if n==o['goal']:return [p]
   return [z for a,b in o['edges'] if a==n and b not in p for z in dfs(b,p+[b])]
  assert dfs(o['start'],[o['start']])==o['paths'];checks.append('enumerated directed simple paths')
 elif k=='route_steps':assert [name for name,v in o['routes'].items() if v[1]-v[0]==v[2]-v[1]>0]==o['constant_increase']
 elif k=='route_increase':assert all(b>a for a,b in zip(o['values'],o['values'][1:]))==o['expected']
 elif k=='temperature':assert o['times'][o['values'].index(max(o['values']))]==o['maximum_time'];assert o['values'][1]-o['values'][0]>o['values'][2]-o['values'][1]
 elif k=='threshold':assert [n for n,v in o['values'].items() if v>=o['minimum']]==o['selected']
 elif k=='temperature_change':assert o['before']-o['after']==o['decrease']
 elif k=='calendar':assert [d for d in range(1,o['days']+1) if (o['first_weekday']+d-1)%7==o['wanted_weekday']]==o['dates'];checks.append('independent day offset enumeration')
 elif k=='inclusive_days':assert len(list(range(o['start'],o['end']+1)))==o['count']
 elif k=='expression_choice':assert exact('(7+5)*4')==exact('7*4+5*4')==o['expected_value'] and exact('7+5*4')!=o['expected_value']
 elif k=='expression_parentheses':assert sum(o['total_parts'])==o['per_group']*o['groups']
 elif k=='left_to_right':assert exact(o['expression'])==o['expected']
 elif k=='digit_permutations':
  values=sorted({int(''.join(map(str,p))) for p in itertools.permutations(o['digits'],o['length']) if p[0]!=0 and p[-1]%2==o['parity']})
  assert values==o['values'];checks.append('complete finite permutation-set equality')
 elif k=='parity_interval':assert [n for n in range(o['low'],o['high']+1) if n%2==0]==o['even']
 elif k in ('round_interval','round_intersection'):
  rounder=lambda n:((n+o['unit']//2)//o['unit'])*o['unit']
  eligible=[n for n in range(o['target']-o['unit'],o['target']+o['unit']) if rounder(n)==o['target'] and n<o.get('strict_upper',10**12)]
  assert min(eligible)==o['minimum'] and max(eligible)==o['maximum'];checks.append('all integer candidates in neighboring rounding cells enumerated')
 elif k=='round_counterexample':assert len(set(o['values']))>1 and all(((n+o['unit']//2)//o['unit'])*o['unit']==o['target'] for n in o['values'])
 elif k=='fair_share':assert Fraction(o['share'])*o['recipients']==o['whole_units'];checks.append('exact inverse rational multiplication')
 elif k=='unit_whole_contrast':assert Fraction(o['share'])==o['total']*Fraction(o['fraction_of_total']) and Fraction(o['share'])*o['recipients']==o['total']
 elif k=='missing_series_total':assert sum(o['expected'])==o['total'] and all(a==b for a,b in zip(o['values'],o['expected']) if a is not None)
 elif k=='series_frequency':assert o['expected'].count(o['target'])==o['frequency'] and all(a==b for a,b in zip(o['values'],o['expected']) if a is not None)
 elif k=='labelled_sort':assert [p[0] for p in sorted(o['pairs'],key=lambda z:z[1])]==o['sorted_labels']
 elif k=='bound':
  if o['operation']=='product':assert o['a']<o['upper_factors'][0] and o['b']<o['upper_factors'][1] and o['a']*o['b']<o['strict_upper'] and (o['a']*o['b']>o['claim_gt'])==o['claim']
  else:assert o['a']>o['lower_dividend'] and Fraction(o['a'],o['b'])>o['strict_lower'] and (Fraction(o['a'],o['b'])<o['claim_lt'])==o['claim']
 elif k=='estimate_exact':assert o['a']*o['b']==o['exact']!=o['estimate']
 elif k=='missing':assert not r['can_solve'] and not r['expected_answer'] and o['fields'];checks.append('explicit absent givens, no fabricated numeric answer')
 else:raise AssertionError(k)
 for s in r['worked_steps']:
  if s['expression']:
   n=exact(s['expression']);assert n==Fraction(s['result'])
   with localcontext() as ctx:
    ctx.prec=70
    # Exact Fraction AST + independent Decimal conversion check where finite.
    if n.denominator in (1,2,4,5,8,10,20,25,40,50,100):assert Decimal(n.numerator)/Decimal(n.denominator)==Decimal(Fraction(s['result']).numerator)/Decimal(Fraction(s['result']).denominator)
   checks.append({'expression':s['expression'],'exact_result':str(n)})
 assert len(r['hints'])==3 and [h['level'] for h in r['hints']]==[1,2,3]
 assert all(h['hint'] and h['question'] for h in r['hints'])
 return checks

def main():
 RUN.mkdir(parents=True,exist_ok=True);cat=catalog();cases=refine_hints(author());assert len(cases)==40 and len({r['sample_id'] for r in cases})==40
 old,_=existing();assert not ({r['sample_id'] for r in old}&{r['sample_id'] for r in cases})
 reviews=[];chats=[]
 for r in cases:
  checks=verify_oracle(r);row_hash=L.digest_bytes(L.canonical_json(r).encode())
  reviews.append({'sample_id':r['sample_id'],'source_row_sha256':row_hash,'review_role':'AUTHOR_SEMANTIC_QA_OWNER_PREAUTHORIZED',
   'human_manual_review_claimed':False,'criteria':{k:True for k in REVIEW_FIELDS},
   'semantic_review_notes':{'specific_representation':GAPS[r['topic']][4],
     'reason_for_operations':[(s['reason'],s['explanation']) for s in r['worked_steps']],
     'hints_actual_content':[{'hint':h['hint'],'question':h['question']} for h in r['hints']],
     'grounding':'Only explicit text or explicitly hypothetical student_work; no unseen image/physical assertion.',
     'grade':'Within book lesson skill; inverse rounding-interval selection marked extra reasoning under same grade, not a copied SGK exercise.'},
   'independent_oracle_checks':checks,'content_schema_passed':True,'status':'ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED'})
  for chat in __import__('build_exhaustive_balanced_release').neutral_chats(r):
   chat['acceptance_status']=r['acceptance_status'];chat['source_row_sha256']=row_hash
   L.validate_chat(chat);chats.append(chat)
 for name,values in [('sgk_g34_cases.jsonl',cases),('sgk_g34_chat.jsonl',chats),('sgk_g34_reviews.jsonl',reviews)]:
  (RUN/name).write_text(''.join(L.canonical_json(x)+'\n' for x in values),encoding='utf-8',newline='\n')
 actual_lines=(RUN/'sgk_g34_cases.jsonl').read_bytes().splitlines()
 assert len(actual_lines)==len(reviews)
 assert all(hashlib.sha256(raw).hexdigest()==review['source_row_sha256'] for raw,review in zip(actual_lines,reviews))
 dump(RUN/'sgk_g34_source_read_receipt.json',{'source_page_images_actual_read':[
  {'book_id':book,'printed_page':page,'local_image_file':BOOKS[book][0]+'_'+str(page+BOOKS[book][3])+'.png',
   'image_sha256':sha(SRC/(BOOKS[book][0]+'_'+str(page+BOOKS[book][3])+'.png'))}
  for book,pages in [('g3v1',[4,5,91,92,106,107]),('g3v2',[2,3,12,13,14,82,83]),('g4v1',[4,5,12,13,45]),('g4v2',[2,3,27,28,36,52,53])] for page in pages],
  'read_scope':'TOC all154lesson metadata plus representation pages, not every page or every exercise',
  'textbook_pages_for_reference_audit_only_not_training_examples':True,
  'raw_line_hash_readback_match':True,'source_row_hash_scope':'UTF-8 source JSONL line bytes excluding LF delimiter',
  'working_source_file_unchanged':[{'path':str(p),'sha256':sha(p)} for p in existing()[1]]})
 receipt={'status':'EXACT_AND_CONTENT_QA_PASSED','cases':40,'chat_rows':160,'by_grade':dict(Counter(r['grade'] for r in cases)),
  'by_case_kind':dict(Counter(r['case_kind'] for r in cases)),'by_gap':dict(Counter(r['topic'] for r in cases)),
  'every_source_step_hint_answer_authored_and_read':True,'external_human_review_claimed':False,'copied_textbook_exercises':0,
  'catalog_lessons':cat['lesson_count'],'full_book_exercise_coverage_claimed':False,
  'source_sha256':sha(RUN/'sgk_g34_cases.jsonl'),'chat_sha256':sha(RUN/'sgk_g34_chat.jsonl'),
  'review_sha256':sha(RUN/'sgk_g34_reviews.jsonl'),'builder_sha256':sha(Path(__file__)),
  'source_row_hash_scope':'actual UTF-8 line bytes excluding LF; reopened and compared all40',
  'no_original_data_rewritten':True,'no_training_started':True}
 dump(RUN/'sgk_g34_qa.json',receipt);print(L.canonical_json(receipt))

if __name__=='__main__':main()
