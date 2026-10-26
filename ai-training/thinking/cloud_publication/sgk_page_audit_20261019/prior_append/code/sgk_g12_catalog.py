"""Transcribed TOC catalogue; separate actual exercise evidence from TOC only."""
from pathlib import Path
import json,hashlib,re
OUT=Path(__file__).parent/'cloud_publication/sgk_gap_20261019'
TOCS={
(1,1):'''1|8|Các số 0, 1, 2, 3, 4, 5
2|14|Các số 6, 7, 8, 9, 10
3|20|Nhiều hơn, ít hơn, bằng nhau
4|24|So sánh số
5|32|Mấy và mấy
6|38|Luyện tập chung
7|46|Hình vuông, hình tròn, hình tam giác, hình chữ nhật
8|50|Thực hành lắp ghép, xếp hình
9|54|Luyện tập chung
10|56|Phép cộng trong phạm vi 10
11|68|Phép trừ trong phạm vi 10
12|80|Bảng cộng, bảng trừ trong phạm vi 10
13|86|Luyện tập chung
14|92|Khối lập phương, khối hộp chữ nhật
15|96|Vị trí, định hướng trong không gian
16|100|Luyện tập chung
17|102|Ôn tập các số trong phạm vi 10
18|106|Ôn tập phép cộng, phép trừ trong phạm vi 10
19|110|Ôn tập hình học
20|112|Ôn tập chung''',
(1,2):'''21|4|Số có hai chữ số
22|16|So sánh số có hai chữ số
23|22|Bảng các số từ 1 đến 100
24|24|Luyện tập chung
25|28|Dài hơn, ngắn hơn
26|32|Đơn vị đo độ dài
27|36|Thực hành ước lượng và đo độ dài
28|40|Luyện tập chung
29|44|Phép cộng số có hai chữ số với số có một chữ số
30|48|Phép cộng số có hai chữ số với số có hai chữ số
31|52|Phép trừ số có hai chữ số cho số có một chữ số
32|58|Phép trừ số có hai chữ số cho số có hai chữ số
33|64|Luyện tập chung
34|72|Xem giờ đúng trên đồng hồ
35|76|Các ngày trong tuần
36|80|Thực hành xem lịch và giờ
37|84|Luyện tập chung
38|88|Ôn tập các số và phép tính trong phạm vi 10
39|94|Ôn tập các số và phép tính trong phạm vi 100
40|100|Ôn tập hình học và đo lường
41|104|Ôn tập chung''',
(2,1):'''1|6|Ôn tập các số đến 100
2|10|Tia số. Số liền trước, số liền sau
3|13|Các thành phần của phép cộng, phép trừ
4|16|Hơn, kém nhau bao nhiêu
5|19|Ôn tập phép cộng, phép trừ (không nhớ) trong phạm vi 100
6|23|Luyện tập chung
7|26|Phép cộng (qua 10) trong phạm vi 20
8|33|Bảng cộng (qua 10)
9|36|Bài toán về thêm, bớt một số đơn vị
10|38|Luyện tập chung
11|41|Phép trừ (qua 10) trong phạm vi 20
12|47|Bảng trừ (qua 10)
13|50|Bài toán về nhiều hơn, ít hơn một số đơn vị
14|53|Luyện tập chung
15|57|Ki-lô-gam
16|62|Lít
17|66|Thực hành và trải nghiệm với các đơn vị ki-lô-gam, lít
18|70|Luyện tập chung
19|72|Phép cộng (có nhớ) số có hai chữ số với số có một chữ số
20|76|Phép cộng (có nhớ) số có hai chữ số với số có hai chữ số
21|80|Luyện tập chung
22|83|Phép trừ (có nhớ) số có hai chữ số cho số có một chữ số
23|89|Phép trừ (có nhớ) số có hai chữ số cho số có hai chữ số
24|95|Luyện tập chung
25|98|Điểm, đoạn thẳng, đường thẳng, đường cong, ba điểm thẳng hàng
26|102|Đường gấp khúc. Hình tứ giác
27|106|Thực hành gấp, cắt, ghép, xếp hình. Vẽ đoạn thẳng
28|110|Luyện tập chung
29|112|Ngày - giờ, giờ - phút
30|116|Ngày - tháng
31|119|Thực hành và trải nghiệm xem đồng hồ, xem lịch
32|122|Luyện tập chung
33|124|Ôn tập phép cộng, phép trừ trong phạm vi 20, 100
34|129|Ôn tập hình phẳng
35|132|Ôn tập đo lường
36|135|Ôn tập chung''',
(2,2):'''37|4|Phép nhân
38|7|Thừa số, tích
39|9|Bảng nhân 2
40|12|Bảng nhân 5
41|15|Phép chia
42|18|Số bị chia, số chia, thương
43|21|Bảng chia 2
44|24|Bảng chia 5
45|27|Luyện tập chung
46|34|Khối trụ, khối cầu
47|37|Luyện tập chung
48|40|Đơn vị, chục, trăm, nghìn
49|43|Các số tròn trăm, tròn chục
50|47|So sánh các số tròn trăm, tròn chục
51|50|Số có ba chữ số
52|55|Viết số thành tổng các trăm, chục, đơn vị
53|58|So sánh các số có ba chữ số
54|61|Luyện tập chung
55|65|Đề-xi-mét. Mét. Ki-lô-mét
56|71|Giới thiệu tiền Việt Nam
57|73|Thực hành và trải nghiệm đo độ dài
58|75|Luyện tập chung
59|79|Phép cộng (không nhớ) trong phạm vi 1 000
60|83|Phép cộng (có nhớ) trong phạm vi 1 000
61|87|Phép trừ (không nhớ) trong phạm vi 1 000
62|91|Phép trừ (có nhớ) trong phạm vi 1 000
63|97|Luyện tập chung
64|100|Thu thập, phân loại, kiểm đếm số liệu
65|102|Biểu đồ tranh
66|106|Chắc chắn, có thể, không thể
67|108|Thực hành và trải nghiệm thu thập, phân loại, kiểm đếm số liệu
68|110|Ôn tập các số trong phạm vi 1 000
69|113|Ôn tập phép cộng, phép trừ trong phạm vi 100
70|117|Ôn tập phép cộng, phép trừ trong phạm vi 1 000
71|122|Ôn tập phép nhân, phép chia
72|127|Ôn tập hình học
73|131|Ôn tập đo lường
74|134|Ôn tập kiểm đếm số liệu và lựa chọn khả năng
75|136|Ôn tập chung'''}

GAPS=[
('complete_decompositions',1,1,35,5,['primary_20261018_finite099_g1_words_unknown_category','cloud_pedagogy_v3_013'],'Existing examples find one missing known part; these require enumerating every ordered count pair with bounds, including empty-group policy.'),
('hundred_grid_patch',1,2,23,23,['primary_20261017_g2_numbers_ray_0009_ray_single_unit_tick','primary_20261018_old_g1_numbers_100_0096_forward_number_line_cross_tens_blank'],'Existing cases concern one-dimensional ticks/sequence or geometric tiling; none require simultaneous numeric row/column constraints on a hundred-grid patch.'),
('sum_pyramid',1,1,87,13,['primary_20261016_g1_operations_0003_left_add_add','exhaustive_structure_g2_two_sign_arrow_machine'],'Existing chains use a linear accumulator; sum pyramids have overlapping adjacent inputs and distinct dependency levels, with inverse and local error localization.'),
('expression_target_classification',1,1,89,13,['primary_20261017_g2_tally_0023_classify_pencils:polish_v1','primary_20261018_old_g1_compare_0097_select_card_to_satisfy_strict_inequality'],'Existing tally groups explicit colours or literal numbers by inequality; new cases compute the classification feature and distinguish count of matching expressions from sum of their values.'),
('blank_digit_column_constraints',1,2,66,33,['original_tutor25_g1_04','cloud_pedagogy_v3_013'],'Existing complete-operand column correction and unknown whole addend do not fill a constrained digit within a multi-digit operand or demonstrate non-unique two-digit placeholders.'),
('one_digit_swap_repair',1,2,65,33,['primary_20261017_g1_activities_0008_misconception_tens_units_reversed','original_tutor25_g1_04'],'Existing transcription/place-value corrections may rewrite an answer; no existing task requires conserving the multiset of digit cards under exactly one transposition with fixed signs.'),
('constrained_arithmetic_path',1,2,65,33,['primary_20261017_g2_polyline_0022_sum_every_segment','exhaustive_structure_g2_two_sign_arrow_machine'],'Existing geometric length routes and single-path arithmetic machines do not select a graph path satisfying both adjacency/direction and a predicate on every visited expression value.'),
('conditional_board_game',2,2,33,45,['primary_20261017_g1_activities_0008_count_game_cards','primary_20261017_g1_activities_0008_guard_unseen_card_game'],'Existing game framing merely sums quantities or checks ordering; new tasks combine step-count origin, conditional jump, answer correctness and rollback using actual written response evidence.')]

def build():
 books=json.loads((OUT/'g12_official_pages.json').read_text('utf-8'))
 source=OUT/'current_source_all_pedagogic.jsonl'
 old=[json.loads(x) for x in source.read_text('utf-8').splitlines()]
 oldindex={r['sample_id']:r for r in old}
 lessons=[];gaps=[]
 for book in books:
  g,v=book['grade'],book['volume']
  for line in TOCS[g,v].splitlines():
   n,page,title=line.split('|',2);n,page=int(n),int(page)
   toc_page=(4 if n<=10 else 5) if g==1 and v==1 else (2 if n<=33 else 3) if g==1 else (4 if n<=21 else 5) if v==1 else (2 if n<=58 else 3)
   lessons.append({'grade':g,'volume':v,'lesson_number':n,'title':title,'start_printed_page':page,
    'reader_url':book['reader_urls'][0], 'lesson_start_image_url':book['page_urls'][page-1],
    'toc_image_url':book['page_urls'][toc_page-1],'evidence_level':'ACTUAL_TOC_PAGE_READ',
    'all_lesson_exercises_read':False,'type_completeness_status':'PENDING_ALL_EXERCISE_PAGE_AUDIT',
    'observed_gap_types':[x[0] for x in GAPS if x[1:3]==(g,v) and x[4]==n]})
 for topic,g,v,page,lesson,near,reason in GAPS:
  book=next(b for b in books if b['grade']==g and b['volume']==v)
  candidates=[]
  for sid in near:
   r=oldindex[sid]
   candidates.append({'sample_id':sid,'actual_source_row_sha256':hashlib.sha256(next(l.encode() for l in source.read_text('utf-8').splitlines() if json.loads(l)['sample_id']==sid)).hexdigest(),
    'actual_problem':r['problem'],'fields_read':['problem','givens','requested_quantity','student_work','initial_guidance','worked_steps','expected_answer','hints']})
  gaps.append({'gap_type':topic,'grade':g,'volume':v,'lesson_number':lesson,'source_printed_page':page,
    'source_page_url':book['page_urls'][page-1],'source_page_sha256':hashlib.sha256((OUT/f'g{g}v{v}_p{page}.png').read_bytes()).hexdigest(),
    'evidence_level':'ACTUAL_EXERCISE_PAGE_IMAGE_READ','semantic_difference':reason,'nearest_existing_examples':candidates,
    'new_cases':4,'new_case_ids':[f'sgk_g12_20261019_{topic}_{i:02d}' for i in range(1,5)],
    'modality_limit':'Original explicit text/schema representations; not observed photo/physical activity validation.'})
 payload={'schema':'sgk_g12_catalog.v1','date':'2026-10-19','publisher_primary_source':'https://taphuan.nxbgd.vn',
 'books':[{'grade':b['grade'],'volume':b['volume'],'detail_url':b['detail_url'],'reader_url':b['reader_urls'][0],
           'reader_html_sha256':b['reader_html_sha256'],'public_image_pages':len(b['page_urls'])} for b in books],
 'lessons':lessons,'numbered_lessons':len(lessons),'additional_first_lesson':{'grade':1,'volume':1,'title':'Tiết học đầu tiên','page':6,'evidence_level':'ACTUAL_TOC_PAGE_READ'},
 'exercise_types_actually_read':gaps,'semantic_gap_scope':{'old_source_cases_loaded':len(old),'g1g2_cases':sum(r.get('grade',99)<=2 for r in old),
 'comparison_method':'Screened actual G1/G2 problems and structured topics; read full nearest actual source fields and supplied current extension cases. No novelty accepted solely from absent keywords. Arithmetic-only exhaustive domains cannot cover graph/digit/branch representation constraints.',
 'all5683_cases_claimed_full_semantic_read':False,'source_file_sha256':hashlib.sha256(source.read_bytes()).hexdigest()},
 'untouched_lesson_page_policy':'Every lesson without ACTUAL_EXERCISE_PAGE_IMAGE_READ remains pending exercise-form audit. TOC coverage is not proof of complete textbook types.',
 'official_2026_status':'Public current publisher portal verified 19Oct2026. No claim that every existing legacy book page was changed in2026, nor legal certification of whole curriculum.',
 'skills_applied':[]}
 assert len(lessons)==116
 (OUT/'sgk_g12_catalog.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'lessons':len(lessons),'gaps':len(gaps),'oldcases':len(old)},ensure_ascii=False))

if __name__=='__main__':build()
