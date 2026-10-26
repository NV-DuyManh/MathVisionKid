"""Twelve finite original geometric-relation drafts. No Drive/state/training."""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal,localcontext
from collections import Counter
import hashlib,json,re,importlib.util
from exhaustive_primary_math import chat_records,expression_group
from sgk_gap_release import evaluate
import exhaustive_colab_loader as L

HERE=Path(__file__).resolve().parent
OUT=HERE/'cloud_publication/sgk_completion_20261021/geometric_relations'
BASE=HERE/'cloud_publication/sgk_remaining_20261020/reconciliation'
OLD=HERE/'cloud_publication/sgk_page_audit_20261019'
MASTERS=['equal_area_geometric_regrouping','equal_area_transfer_cancellation','missing_parallelogram_vertex','occlusion_partial_layer_order','tangent_circle_alignment_lengths','specified_area_preserving_dissection']
FIELDS=['problem','givens','requested_quantity','student_work','initial_guidance','hints','worked_steps','expected_answer']
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def read(p):return json.loads(p.read_text('utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def jl(p,rs):p.write_text(''.join(dump(r)+'\n' for r in rs),encoding='utf-8',newline='\n')
def s(title,reason,result,explanation,expression=None,unit=''):return dict(title=title,reason=reason,result=str(result),explanation=explanation,expression=expression,unit=unit)
def hs(a,b,c):return [dict(level=i+1,hint=t,question=q) for i,(t,q) in enumerate(zip([a,b,c],['Em cần giữ những dữ kiện nào?','Em áp dụng quan hệ đã cho ra sao?','Em kiểm đủ các điều kiện thế nào?']))]
ROWS=[]
TASKS={}
NEAREST={}
def add(master,branch,grade,problem,givens,request,steps,answers,hints,model,note,student=None):
    sid='sgk_completion_rel_20261021_'+branch
    task=TASKS[master]
    ROWS.append(dict(sample_id=sid,case_group_id=sid+'_group',grade=grade,topic=branch,split='train',case_kind='observable_student_error' if student else 'original_finite_reasoning',problem=problem,givens=[dict(id=f'g{i}',text=t,value=None,unit='',role='explicit_original_given') for i,t in enumerate(givens)],requested_quantity=request,student_work=dict(text=student,observations=[dict(excerpt=student,claim_scope='Only this supplied synthetic text; no hidden thought, unseen image or physical result inferred.')]) if student else None,can_solve=True,initial_guidance=[hints[0]['hint']],hints=hints,worked_steps=[dict(step_id=f's{i}',**st) for i,st in enumerate(steps)],expected_answer=[dict(quantity=q,result=str(v),unit=u) for q,v,u in answers],canonical_signatures=sorted({expression_group(st['expression']) for st in steps if st['expression']}),independent_model=model,pedagogical_review_decision=note,acceptance_status='DRAFT_AWAITING_ROOT_CONTENT_QA',quality_status='AUTHOR_SELF_QA_COMPLETE_PENDING_ROOT_QA',human_verified=False,teacher_certified=False,owner_human_reviewed=False,source_role='AI_GENERATED',provenance=dict(authorship_origin='ORIGINAL_AI_TEACHER_AUTHORING',human_content_review_completed=False,book_exercise_copied=False,actual_physical_or_image_result_claimed=False,acceptance_basis='OWNER_PREAUTHORIZED_PROCESS_ROOT_QA_PENDING'),curriculum_assignment=dict(grade=grade,enrichment=True,modality='EXPLICIT_ORIGINAL_TEXT_MODEL_ONLY',candidate_ids=task['candidate_ids'],original_page_receipts=task['exact_page_receipts'],receipt_basis='Inherited previously-viewed image receipts; no new page image viewing claimed by this author.',lower_grade_aliases_not_automatically_closed=master=='specified_area_preserving_dissection'),coverage=dict(mode='FINITE_SUPPLEMENTARY_APPEND_NOT_CORE',finite_master_id=master,branch=branch,new_core_slots_claimed=0,numbers_only_variant=False,text_relation_only=True,visual_physical_coverage_claimed=False),nearest_source_comparison=dict(queue_file='sgk_remaining_20261020/reconciliation/next_uncovered_tasks.json',queue_sha256=sha((BASE/'next_uncovered_tasks.json').read_bytes()),actual_nearest_refs=NEAREST[master],semantic_difference=task['original_master_reasons'])))

def author():
 m=MASTERS[0]
 add(m,'halves_regroup_three_equal_parts',3,
 'Tờ mô hình gồm 6 ô vuông cạnh 1 cm, hàng trên đánh số 1,2,3 từ trái sang phải, hàng dưới 4,5,6. Mỗi ô được chia theo đường chéo từ góc dưới trái đến góc trên phải thành hai tam giác bằng nhau: L là phần dưới phải, U là phần trên trái. Phần A gồm cả ô1, tam giác L của ô2 và U của ô5; phần B gồm cả ô3, U của ô2 và L của ô5; phần C gồm cả ô4 và ô6. Không có phần khác. Được tịnh tiến các tam giác trong lập luận để ghép lại ô vuông, không làm đổi miếng. Chứng minh ba phần bằng diện tích, tính mỗi phần và gọi phần A của cả tờ.',
 ['Sáu ô bằng nhau, mỗi ô 1 cm²; mỗi đường chéo chia thành hai nửa bằng diện tích.','A=ô1+L2+U5; B=ô3+U2+L5; C=ô4+ô6; dùng đúng các phần đã nêu.'],
 'Diện tích ba phần và phần A so với cả tờ',[
 s('Ghép các nửa cùng cỡ','L và U của các ô cùng cỡ có thể ghép theo cạnh chéo thành một ô vuông.','L2 ghép U5 thành một ô; U2 ghép L5 thành một ô','Hai miếng nằm hai phía cạnh chéo, không chồng và không để hở, nên mỗi cặp có diện tích một ô.'),
 s('Đếm theo ô diện tích','Mỗi phần gồm hai ô diện tích sau khi ghép.',2,'A gồm ô1 và một ô ghép; B gồm ô3 và một ô ghép; C có hai ô nguyên. Mỗi ô là 1 cm².','1+1','cm²'),
 s('Kiểm cả tờ và gọi phần','Ba phần rời nhau phủ đủ sáu ô, nên ba phần bằng nhau tạo cả tờ.','A bằng 1/3 cả tờ','Ô2 và ô5 mỗi ô dùng cả L lẫn U đúng một lần; ô1,3,4,6 cũng dùng đúng một lần. Ba phần mỗi phần 2 cm² có tổng 6 cm².')],
 [('A',2,'cm²'),('B',2,'cm²'),('C',2,'cm²'),('Phần A','1/3','tờ')],
 hs('Đưa các tam giác về cùng ô vuông làm đơn vị so diện tích.','Theo dõi mỗi nửa ô để ghép mà không dùng lại một miếng.','Kiểm ba phần phủ đúng cả tờ rồi mới gọi tên phần được hỏi.'),
 dict(kind='half_cells',total_cells=6,groups={'A':['1L','1U','2L','5U'],'B':['3L','3U','2U','5L'],'C':['4L','4U','6L','6U']},expected_areas={'A':'2','B':'2','C':'2'},expected_selected_fraction='1/3'),
 'Geometric regrouping proves equality from specified complementary half-cells rather than assuming all pieces equal. Grade3 uses area units and a unit fraction, no coordinate algebra.')
 add(m,'piece_count_not_area_count',3,
 'Tờ mô hình là hình vuông 2 hàng 2 cột, mỗi ô vuông cạnh 1 cm. Hai ô hàng trên giữ nguyên làm phần P. Mỗi ô hàng dưới cắt đúng một đường chéo tạo hai tam giác bằng nhau; cả bốn tam giác hàng dưới là phần Q. Không mất giấy, không chồng. Bạn viết: Q có 4 miếng còn P có 2 miếng nên diện tích Q gấp đôi P. Giữ câu đó, so diện tích hai phần bằng cách ghép và tính diện tích từng phần.',
 ['P có hai ô vuông nguyên cạnh 1 cm.','Q có bốn tam giác, từng cặp là hai nửa của một ô cùng cỡ; tổng thể là tờ 2×2 ô.'],
 'So diện tích P,Q và phản hồi cách đếm miếng',[
 s('Chọn cùng đơn vị','Một tam giác chỉ là nửa ô, không bằng một miếng vuông nguyên.','Hai tam giác cùng ô ghép thành một ô','Giữ nguồn gốc từng cặp đường chéo; bốn tam giác ghép lại đúng hai ô hàng dưới.'),
 s('Đếm diện tích theo ô','Cả P và Q cùng chiếm hai ô đơn vị.',2,'P có hai ô nguyên; Q ghép được hai ô. Mỗi phần đều 2 cm².','1+1','cm²'),
 s('Đối chiếu câu đã viết','Đếm số miếng khác cỡ không cho tỉ số diện tích.','P và Q bằng diện tích','Tổng hai phần 2+2=4 cm² đúng cả tờ. Câu gấp đôi đã coi mỗi tam giác bằng một ô vuông, điều này trái cách cắt đã cho.')],
 [('P',2,'cm²'),('Q',2,'cm²'),('So sánh','Bằng diện tích','')],
 hs('So cỡ từng loại miếng theo cùng ô vuông mốc.','Ghép lại các tam giác có nguồn gốc cùng đường chéo.','Kiểm diện tích hai phần cộng lại bằng diện tích cả tờ.'),
 dict(kind='half_cells',total_cells=4,groups={'P':['1L','1U','2L','2U'],'Q':['3L','3U','4L','4U']},expected_areas={'P':'2','Q':'2'}),
 'Distinct piece-count error: four half-square triangles versus two complete squares, with explicit no-gap regrouping and observable written claim.',student='Q có 4 miếng còn P có 2 miếng nên diện tích Q gấp đôi P.')
 m=MASTERS[1]
 add(m,'common_region_congruent_triangle_cancellation',4,
 'Hình chữ nhật R trên lưới có bốn góc (0,0),(4,0),(4,3),(0,3), mỗi đơn vị dài 1 cm. T là tam giác có các đỉnh (0,0),(2,0),(0,2). U là bản tịnh tiến của T sang phải 2 cm và lên 1 cm, nên có các đỉnh (2,1),(4,1),(2,3). Hai tam giác chỉ nằm trong R, không chồng diện tích. C là phần còn lại của R sau khi bỏ cả T và U. Miền M gồm C với T; miền N gồm C với U. So diện tích M,N và tính mỗi miền; giải thích bằng phần chung C, không dựa vào dáng đặt.',
 ['R là chữ nhật 4×3 cm; T và U bằng nhau do tịnh tiến, mỗi tam giác là nửa ô vuông 2×2 cm.','C=R bỏ T và U; M=C ghép T, N=C ghép U; các phần trong mỗi miền không chồng.'],
 'Diện tích M,N và căn cứ từ phần chung',[
 s('Xác định hai phần thay nhau','Tịnh tiến giữ miếng; mỗi tam giác là nửa hình vuông 2×2 cm.',2,'Ô vuông diện tích 4 cm², hai tam giác chéo bằng nhau nên mỗi tam giác 2 cm².','2*2/2','cm²'),
 s('Giữ phần chung một lần','R gồm C,T,U không chồng nên bỏ hai tam giác khỏi diện tích 12 cm².',8,'C có diện tích 12−2−2=8 cm². Trong M và N đều có đúng cùng phần C.','4*3-2-2','cm²'),
 s('Ghép phần bằng nhau vào cùng phần chung','Thay T bằng U không đổi diện tích vì T và U bằng nhau.',10,'M=8+2=10 cm² và N=8+2=10 cm². Bỏ C chung ở hai miền còn đúng hai tam giác bằng nhau, kiểm lại cả hai cách.','8+2','cm²')],
 [('M',10,'cm²'),('N',10,'cm²'),('So sánh','Bằng diện tích','')],
 hs('Xác định phần nào có mặt trong cả hai miền và phần nào thay nhau.','Dùng phép tịnh tiến và ô vuông mốc để kiểm hai tam giác.','Khi cộng diện tích, kiểm từng phần chỉ được tính một lần trong mỗi miền.'),
 dict(kind='common_triangles',rectangle=[[0,0],[4,0],[4,3],[0,3]],T=[[0,0],[2,0],[0,2]],U=[[2,1],[4,1],[2,3]],expected_triangle_area='2',expected_C='8',expected_regions='10'),
 'Explicit congruent triangles, shared common region, disjoint partition and two equal reconstructed regions; no assumption from appearance.')
 add(m,'transfer_overlap_breaks_area_claim',4,
 'Tờ vuông 2×2 cm chia thành bốn ô vuông 1×1 cm, mỗi ô cắt một đường chéo từ dưới trái đến trên phải. Nhấc riêng tam giác dưới phải T của ô dưới trái, rồi tịnh tiến T sang phải 1 cm đặt trùng khít lên tam giác dưới phải vốn còn nằm ở ô dưới phải; không di chuyển phần khác. Hỏi diện tích vùng mặt phẳng còn được ít nhất một lớp giấy phủ sau phép đặt. Bạn viết: Chỉ cắt chuyển giấy, không bỏ giấy nên vùng phủ vẫn là 4 cm². Giữ câu đó, chỉ rõ điều kiện nào khiến lập luận giữ diện tích vùng phủ không áp dụng.',
 ['Cả tờ gồm tám nửa ô bằng nhau, mỗi nửa ô diện tích 1/2 cm².','T chuyển từ nửa ô dưới trái sang vị trí nửa ô dưới phải đã có giấy; hai lớp trùng khít ở chỗ đến, phần khác giữ nguyên.'],
 'Diện tích vùng phủ sau chuyển và phản hồi',[
 s('Phân biệt lượng giấy với vùng phủ','Nơi chồng hai lớp vẫn chỉ là một vùng của mặt phẳng.','Có một nửa ô bị hở và một nửa ô bị chồng','Dời T không tạo thêm vùng phủ ở chỗ đến vì tam giác đích vốn đã phủ; chỗ T cũ không còn lớp nào.'),
 s('Tính vùng còn phủ','Cả tờ 4 cm² mất đúng một nửa ô ở vị trí cũ.',3.5,'Vùng phủ là 4−1/2=3,5 cm². Tổng diện tích các miếng giấy theo từng lớp vẫn là 4 cm², nhưng đó không phải đại lượng được hỏi.','4-1/2','cm²'),
 s('Kiểm điều kiện cắt ghép','Bảo toàn diện tích miền ghép cần các miếng không chồng và phủ kín miền đích.','Lập luận trong câu không áp dụng cho vùng phủ','Phép đặt đã tạo chồng và hở. Đếm bảy nửa ô có phủ cho 7×1/2=3,5 cm², không đếm nửa ô có hai lớp hai lần.')],
 [('Vùng phủ',3.5,'cm²'),('Điều kiện bị vi phạm','Các miếng không chồng và không để hở miền đích','')],
 hs('Theo dõi riêng vị trí cũ và vị trí đến của miếng được chuyển.','Đại lượng cần đếm là vùng có ít nhất một lớp, không phải tổng diện tích theo từng lớp.','Kiểm các điều kiện chồng và hở trước khi dùng tính chất bảo toàn của hình ghép.'),
 dict(kind='half_transfer',initial=['1L','1U','2L','2U','3L','3U','4L','4U'],remove='1L',landing='2L',expected_union_area='7/2',expected_paper_area='4'),
 'Necessary disjointness condition checked by explicit overlapping half-cell transfer, distinct from congruent common-region cancellation.',student='Chỉ cắt chuyển giấy, không bỏ giấy nên vùng phủ vẫn là 4 cm².')
 m=MASTERS[2]
 add(m,'ordered_parallelogram_fourth_vertex',4,
 'Trên lưới chính xác, vị trí viết (cột,hàng), A(1,1), B(4,1), C(5,3). A,B,C là ba đỉnh liên tiếp theo đúng thứ tự của hình bình hành ABCD, các cạnh không tự cắt. Tìm vị trí D và nêu hai cặp cạnh đối song song để kiểm. Các điểm đã cho bằng chữ; không có ảnh cần đo.',
 ['A(1,1), B(4,1), C(5,3); ba đỉnh liên tiếp A→B→C.','ABCD là hình bình hành, đỉnh cuối D chưa biết; vị trí trên lưới là chính xác.'],
 'Đỉnh D và kiểm hai cặp cạnh đối',[
 s('Giữ cùng bước cho hai cạnh đối','Từ B đến C đi phải một ô và lên hai ô; từ A đến D cần cùng bước.','D ở cột 2, hàng 3','A ở cột1,hàng1, đi phải1 lên2 đến (2,3). Không đi tiếp từ C theo cùng bước vì D không nằm trên cạnh BC kéo dài.'),
 s('Kiểm cặp cạnh còn lại','AB đi ngang phải ba ô, nên DC cũng phải ngang phải ba ô.','AB song song DC; BC song song AD','D(2,3) đến C(5,3) đúng phải3; A đến D và B đến C đều phải1 lên2. Hai cặp cạnh đối bằng bước và song song.'),
 s('Kiểm sự xác định','Thứ tự ba đỉnh liên tiếp đã cố định hai cạnh xuất phát từ A và B.','Chỉ D(2,3)','Cùng bước từ A chỉ đến một ô. Các điểm khác không cùng đáp ứng hai cặp cạnh đối theo thứ tự ABCD đã cho.')],
 [('D','(2,3)',''),('Cạnh đối','AB song song DC; BC song song AD','')],
 hs('Đọc rõ ba đỉnh đã cho có theo thứ tự quanh hình hay không.','Lặp bước trên lưới ở cạnh đối tương ứng.','Kiểm cả hai cặp cạnh đối và thứ tự đường bao.'),
 dict(kind='parallelogram_ordered',A=[1,1],B=[4,1],C=[5,3],expected_D=[2,3]),
 'Reconstruct missing vertex from two parallel-side relations rather than only classify a completed shape.')
 add(m,'unordered_three_vertices_all_completions',4,
 'Ba điểm P(2,2), Q(5,2), R(3,4) trên lưới là ba trong bốn đỉnh của một hình bình hành, nhưng chưa cho thứ tự quanh hình. Đỉnh thứ tư D phải là một điểm lưới có cột từ 0 đến 6, hàng từ 0 đến 4, kể cả các cận. Cần hình bình hành không suy biến, không tự cắt. Bạn viết: Chỉ có D(6,4) vì nối P,Q,R theo thứ tự đã viết. Tìm mọi vị trí D hợp lệ; giữ đúng việc đề chưa cho ba đỉnh liên tiếp.',
 ['P(2,2), Q(5,2), R(3,4), chưa có thứ tự đỉnh.','D thuộc lưới cột0..6,hàng0..4; hình bình hành không suy biến.'],
 'Mọi đỉnh D và nhận xét tính duy nhất',[
 s('Xét ba cách chọn đỉnh ở giữa hai cạnh','Một trong ba điểm đã cho có thể là đỉnh chung của hai cạnh kề.','Xét lần lượt P, Q hoặc R là đỉnh chung','Không được mặc định thứ tự P,Q,R vì đề chỉ nói là ba đỉnh, không nói liên tiếp theo danh sách.'),
 s('Lặp bước ở hai cạnh đối','Với mỗi đỉnh chung, dùng hai bước tới hai điểm còn lại để hoàn thiện hình.','D(6,4), D(0,4), hoặc D(4,0)','Nếu đỉnh chung P, ghép bước P→Q và P→R cho D(6,4). Nếu chung Q thì D(0,4); nếu chung R thì D(4,0). Cả ba nằm trong miền lưới.'),
 s('Kiểm đủ và sửa từ chỉ','Ba điểm không thẳng hàng nên ba cách trên đều cho hình có diện tích khác không.','Có ba vị trí hợp lệ','Hai cạnh đối của mỗi cách có cùng bước. Đỉnh chung chỉ có thể là P,Q hoặcR, đã xét hết; D(6,4) đúng nhưng không duy nhất.')],
 [('Mọi D','(0,4);(4,0);(6,4)',''),('Số vị trí',3,'vị trí')],
 hs('Phân biệt ba điểm là đỉnh với ba đỉnh đã được cố định thứ tự.','Thử từng điểm đã cho làm đỉnh chung của hai cạnh kề.','Kiểm mọi vị trí suy ra với cận lưới và hai cặp cạnh đối.'),
 dict(kind='parallelogram_unordered',points=[[2,2],[5,2],[3,4]],bounds=[0,6,0,4],expected_Ds=[[0,4],[4,0],[6,4]]),
 'Underordered input yields all three finite completions; different logical branch from unique consecutive-vertex reconstruction.',student='Chỉ có D(6,4) vì nối P,Q,R theo thứ tự đã viết.')
 m=MASTERS[3]
 add(m,'layer_partial_order_all_consistent_orders',4,
 'Bốn tấm phẳng A,B,C,D được đặt thành bốn lớp toàn cục khác nhau, mỗi tấm ở một lớp, không đan xuyên. “X che Y” trong bài có nghĩa cả tấm X ở lớp phía trước cả tấm Y. Dữ kiện chữ chỉ có A che B, B che C và A che D; không có ràng buộc nào khác. Liệt kê mọi thứ tự từ trước ra sau và cho biết có xác định duy nhất không. Không có ảnh để suy thêm quan hệ.',
 ['A trước B; B trước C; A trước D.','Bốn lớp toàn cục khác nhau, không đan xuyên; không có điều kiện khác.'],
 'Mọi thứ tự lớp và tính duy nhất',[
 s('Dùng chuỗi đã buộc','A trước B, B trước C nên A trước cả B và C; A còn trước D.','A phải đứng đầu; B trước C','Không biết D trước hay sau B,C. Không lấy việc D được nhắc cuối làm dữ kiện lớp.'),
 s('Chèn lớp chưa có quan hệ với chuỗi còn lại','Sau A, giữ B trước C rồi đặt D ở các vị trí còn có thể.','A-D-B-C; A-B-D-C; A-B-C-D','D có thể trướcB, giữaB,C hoặc sauC. Mỗi thứ tự đều giữ A trướcD và A trướcB trướcC.'),
 s('Kiểm hết và giới hạn kết luận','Ba vị trí của D sau A đã xét đủ.',3,'Có ba thứ tự nên chưa xác định duy nhất. Muốn chọn một thứ tự cần thêm quan hệ liên quan D với B hoặc C.','1+1+1','thứ tự')],
 [('Thứ tự','A-D-B-C;A-B-D-C;A-B-C-D',''),('Tính duy nhất','Chưa duy nhất','')],
 hs('Chuyển mỗi quan hệ che thành một điều kiện trước-sau được đề định nghĩa.','Giữ các quan hệ đã buộc nhưng không tự thêm quan hệ cho cặp chưa biết.','Thử lại từng danh sách với mọi dữ kiện, rồi kiểm có còn vị trí chưa xét.'),
 dict(kind='layer_orders',labels=['A','B','C','D'],edges=[['A','B'],['B','C'],['A','D']],expected_orders=[['A','B','C','D'],['A','B','D','C'],['A','D','B','C']]),
 'Partial order from explicit occlusion semantics, three admissible total orders rather than fixed queue position.')
 add(m,'layer_cycle_incompatible_claims',4,
 'Ba tấm A,B,C phải nằm ở ba lớp toàn cục trước-sau khác nhau, không đan xuyên. Theo định nghĩa này, tấm ở trước tấm thứ hai và tấm thứ hai ở trước tấm thứ ba thì tấm thứ nhất cũng ở trước tấm thứ ba. Báo cáo chữ ghi đồng thời A che B, B che C, C che A. Có sắp được cả ba tấm thỏa hết báo cáo không? Nếu chỉ bỏ dòng C che A, những dòng còn lại buộc quan hệ nào giữa A và C? Không tưởng tượng ảnh hoặc cách luồn tấm qua nhau.',
 ['A trước B; B trước C; C trước A theo báo cáo.','Mỗi tấm có đúng một lớp toàn cục; quan hệ trước-sau bắc cầu, không đan xuyên.'],
 'Tính khả thi và quan hệ nếu bỏ dòng cuối',[
 s('Theo hai dòng đầu','Quan hệ trước-sau bắc cầu được đề cho rõ.','Hai dòng đầu buộc A trước C','A đứng trướcB rồiB trướcC nên A phải ở trướcC, không tùy ý chọn theo hình dung.'),
 s('Đối chiếu dòng còn lại','Hai lớp khác nhau không thể mỗi lớp đều ở trước lớp kia.','Không có thứ tự thỏa cả ba dòng','Dòng C trướcA trái với A trướcC đã buộc. Đây là mâu thuẫn của dữ kiện đầy đủ, không phải cần đo thêm ảnh.'),
 s('Kiểm yêu cầu khi bỏ đúng một dòng','Giữ A trướcB vàB trướcC sau khi bỏ dòng C trướcA.','A trước C; thứ tự A-B-C','Thứ tự ấy thỏa hai dòng còn lại; không sửa thêm dòng khác hoặc tự cho các tấm đan xuyên.')],
 [('Cả ba dòng','Không có thứ tự hợp lệ',''),('Khi bỏ dòng cuối','A trước C; thứ tự A-B-C','')],
 hs('Lần theo các quan hệ đã được ghi và quy tắc trước-sau toàn cục.','So những quan hệ suy ra với từng dòng báo cáo còn lại.','Giữ đúng tập dòng đang được yêu cầu kiểm, không tự thêm cách đan xuyên.'),
 dict(kind='layer_orders_remove',labels=['A','B','C'],edges=[['A','B'],['B','C'],['C','A']],remove=['C','A'],expected_orders=[],expected_after=[['A','B','C']]),
 'Inconsistent cycle under explicit global-layer semantics; no unsupported claim about general local woven occlusions.')
 m=MASTERS[4]
 add(m,'tangent_row_rectangle_full_extents',3,
 'Ba hình tròn bằng nhau bán kính 2 cm nằm thành một hàng ngang, tâm O1,O2,O3 theo thứ tự trái sang phải trên cùng đường thẳng. Hai hình kề nhau tiếp xúc ngoài đúng một điểm, không chồng. Khung chữ nhật ôm khít: cạnh trái chạm điểm ngoài cùng trái của hình thứ nhất, cạnh phải chạm điểm ngoài cùng phải của hình thứ ba; cạnh trên và dưới chạm cả ba hình. Tính chiều dài, chiều rộng khung và khoảng cách O1 đến O3. Các quan hệ tiếp xúc đã cho, không cần đo ảnh.',
 ['Ba hình tròn cùng bán kính2 cm, tâm thẳng hàng theo thứ tự; kề nhau tiếp xúc ngoài.','Khung ôm khít ngoài cùng trái/phải và trên/dưới; không thêm khoảng trống.'],
 'Hai kích thước khung và đoạn nối tâm đầu-cuối',[
 s('Đổi từ bán kính sang bề ngang mỗi hình','Đường kính gồm hai bán kính trên cùng một đường thẳng.',4,'Mỗi hình tròn rộng 2+2=4 cm; khung trên-dưới cũng cách nhau một đường kính.','2+2','cm'),
 s('Ghép bề ngang theo tiếp xúc','Ba hình chỉ chạm tại điểm nên ba đường kính nối tiếp không chồng độ dài.',12,'Khung dài 4+4+4=12 cm, rộng4 cm; không chỉ tính hai khoảng giữa tâm.','4*3','cm'),
 s('Tách đoạn tâm với toàn khung','Hai tâm kề nhau cách tổng hai bán kính, có hai khoảng tâm kề.',8,'O1O3=4+4=8 cm. Kiểm 8 cộng bán kính2 ở mỗi đầu bằng chiều dài khung12 cm.','4*2','cm')],
 [('Dài khung',12,'cm'),('Rộng khung',4,'cm'),('O1O3',8,'cm')],
 hs('Trên hàng tâm, phân biệt đường kính của hình với khoảng giữa hai tâm kề.','Đếm các phần nối tiếp đúng theo điều kiện tiếp xúc và ôm khít.','So chiều dài toàn khung với đoạn tâm đầu-cuối và các bán kính ở hai đầu.'),
 dict(kind='circle_forward',count=3,radius='2',expected_length='12',expected_width='4',expected_center_span='8'),
 'Tangent aligned-circle chain supplies full rectangle extents and center span; no circle circumference or physical construction claim.')
 add(m,'tangent_row_inverse_gap_count_error',3,
 'Bốn hình tròn bằng nhau xếp một hàng ngang, các tâm thẳng hàng, hai hình kề tiếp xúc ngoài, không chồng. Khung chữ nhật ôm khít bốn hình như sau: trái/phải chạm các điểm ngoài cùng của hai hình đầu-cuối, trên/dưới chạm các hình. Chiều dài khung là 24 cm. Bạn viết: Có 3 khoảng giữa tâm nên đường kính là 24:3=8 cm. Giữ câu đó, tìm bán kính mỗi hình và khoảng cách giữa tâm hình thứ nhất với tâm hình thứ tư; chỉ rõ 24 cm đo đoạn nào.',
 ['Bốn hình bằng nhau, các tâm trên một đường, hình kề tiếp xúc ngoài.','Khung dài24 cm đo từ điểm ngoài cùng trái đến điểm ngoài cùng phải, không phải đoạn tâm đầu-cuối.'],
 'Bán kính, đoạn tâm đầu-cuối và phản hồi',[
 s('Xác định phần của toàn chiều dài','Toàn khung gồm bốn đường kính nối tiếp, kể cả hai bán kính ở hai đầu.',6,'Đường kính=24:4=6 cm. Ba khoảng giữa tâm chưa gồm phần từ cạnh khung đến tâm đầu và từ tâm cuối đến cạnh khung.','24/4','cm'),
 s('Tìm bán kính','Một bán kính bằng nửa đường kính.',3,'Bán kính=6:2=3 cm; không chia chiều dài khung cho số khoảng tâm.','6/2','cm'),
 s('Tính đúng đoạn giữa hai tâm ngoài cùng','Có ba khoảng tâm kề, mỗi khoảng bằng một đường kính.',18,'Đoạn tâm đầu-cuối=3×6=18 cm. Kiểm18+3+3=24, khôi phục đúng khung đã cho.','3*6','cm')],
 [('Bán kính',3,'cm'),('Đoạn tâm đầu-cuối',18,'cm'),('Đoạn24 cm','Toàn khung gồm bốn đường kính, không phải ba khoảng tâm','')],
 hs('Đối chiếu hai đầu của số đo đã cho với hai đầu của đoạn nối tâm.','Xác định chiều dài khung chứa bao nhiêu bề ngang hình tròn.','Kiểm bằng cách cộng các khoảng tâm và phần từ tâm tới cạnh khung.'),
 dict(kind='circle_inverse',count=4,length='24',expected_radius='3',expected_center_span='18'),
 'Inverse length relation and observable confusion between four object widths and three center gaps, distinct from a forward-radius numerical substitution.',student='Có 3 khoảng giữa tâm nên đường kính là 24:3=8 cm.')
 m=MASTERS[5]
 add(m,'trapezoid_midcut_halfturn_rectangle',5,
 'Hình thang vuông mô hình ABCD theo thứ tự đường bao có A(0,0),B(8,0),C(5,4),D(0,4), mỗi đơn vị lưới dài1 cm. N(0,2) là trung điểm AD, M(6,5;2) là trung điểm BC; trong ký hiệu riêng (6,5;2), tọa độ ngang là6,5 và đứng là2. Cắt đúng đoạn NM, được phần dưới ABMN và phần trên NMCD. Giữ phần dưới. Quay phần trên nửa vòng quanh M: N đến N′(13,2), C đến C′(8,0), D đến D′(13,0), M giữ nguyên. Không kéo giãn, không thêm bản sao. Chứng minh hình ghép là chữ nhật không chồng/hở; tìm kích thước và diện tích, rồi so chu vi trước và sau. Cho BC dài5 cm.',
 ['Hình thang đáy8 cm và5 cm, cao4 cm; trung điểm hai cạnh bên ở cao2 cm.','Các điểm ảnh sau nửa vòng đã cho: N′(13,2),C′(8,0),D′(13,0); M(6,5;2); chỉ dùng đúng hai miếng.','BC=5 cm; các cạnh còn lại đọc được từ tọa độ; hỏi cả diện tích và chu vi.'],
 'Hình ghép, diện tích và sự thay đổi chu vi',[
 s('Kiểm mép nối và đường bao','Sau quay, cạnh MC của miếng trên trùng cạnh MB của miếng dưới vì C′=B.','Hai miếng gặp đúng trên MB, ở hai phía của mép nối','Miếng dưới phủ bên trái mép MB; miếng quay phủ bên phải. Mép trên ghép từ0 tới6,5 rồi13 ở cao2; mép dưới từ0 tới8 rồi13 ở cao0. Hai mép đứng ở cột0 và13, nên không có chồng diện tích hoặc khe hở.'),
 s('Đọc kích thước và tính diện tích','Đường bao ghép là chữ nhật dài13 cm,cao2 cm.',26,'13×2=26 cm². Mỗi miếng giữ nguyên diện tích và chúng phủ kín không chồng, nên đây cũng là diện tích hình thang ban đầu.','13*2','cm²'),
 s('So diện tích với chu vi','Cắt ghép giữ diện tích nhưng các mép trong/ngoài thay đổi.','Chu vi cũ22 cm; mới30 cm','Chu vi hình thang=8+5+5+4=22 cm; chữ nhật=2×(13+2)=30 cm. Kiểm 26=(8+5)×4:2; không suy chu vi bằng nhau từ diện tích bằng nhau.')],
 [('Chữ nhật','13 cm × 2 cm',''),('Diện tích',26,'cm²'),('Chu vi cũ',22,'cm'),('Chu vi mới',30,'cm')],
 hs('Theo dõi từng đỉnh của đúng miếng được chuyển và xác định mép nối.','Kiểm các miếng nằm hai phía mép chung và bốn cạnh ngoài của hình ghép.','Tính riêng diện tích và đường bao; việc giữ một đại lượng không tự giữ đại lượng kia.'),
 dict(kind='trapezoid_rotate',lower=[[0,0],[8,0],['6.5',2],[0,2]],upper=[[0,2],['6.5',2],[5,4],[0,4]],center=['6.5',2],target=[[0,0],[13,0],[13,2],[0,2]],expected_area='26',expected_overlap='0',expected_dimensions=['13','2'],expected_perimeters=['22','30']),
 'Complete midpoint-cut/halfturn dissection of a right trapezoid, explicit vertex images and no-gap union. Chosen grade5 branch only; inherited G3/G4 dissection aliases remain pending.')
 add(m,'trapezoid_translate_overlap_counterexample',5,
 'Hình thang vuông A(0,0),B(10,0),C(4,8),D(0,8) trên lưới1 cm được cắt ở đoạn nối N(0,4) với M(7,4), hai trung điểm cạnh bên. Miếng dưới là ABMN, miếng trên là NMCD. Một bạn giữ miếng dưới rồi chỉ tịnh tiến miếng trên sang phải7 cm,xuống4 cm, không quay. Miếng trên lúc đó có các đỉnh (7,0),(14,0),(11,4),(7,4). Bạn viết: Dịch miếng trên như vậy được chữ nhật14×4 cm kín không chồng, nên vùng phủ là56 cm². Giữ lời viết; tìm phần chồng và phần hở so với chữ nhật [0,14]×[0,4], tính diện tích vùng thực phủ. Nêu phép đặt sửa được hình ghép, vẫn dùng hai miếng và không kéo giãn. Có thể xét quay miếng trên nửa vòng quanh M.',
 ['Miếng dưới có đỉnh (0,0),(10,0),(7,4),(0,4); miếng trên sau tịnh tiến có đỉnh (7,0),(14,0),(11,4),(7,4).','Đích cần kiểm là chữ nhật0≤x≤14,0≤y≤4; từng đơn vị dài1 cm, không thêm miếng.','Phép thay thế được xét là nửa vòng quanh M(7,4), không phải tịnh tiến.'],
 'Chồng/hở, diện tích phủ thật và cách đặt đúng',[
 s('Kiểm phần hai miếng cùng che','Miếng dưới kéo tới x=10 ở đáy, trong khi miếng dịch bắt đầu từx=7.','Chồng tam giác (7,0),(10,0),(7,4)','Ở mép trên, miếng dịch chỉ tới x=11 nên còn hở tam giác (11,4),(14,4),(14,0) của chữ nhật đích. Mỗi tam giác có đáy3 cm,cao4 cm.'),
 s('Đếm vùng phủ một lần','Tổng diện tích hai miếng bằng diện tích hình thang56 cm², nhưng phần chồng6 cm² đã bị đếm hai lần.',50,'Phần chồng=3×4:2=6 cm²; vùng phủ=56−6=50 cm². Phần hở6 cm² cũng cho14×4−6=50 cm².','56-3*4/2','cm²'),
 s('Sửa cách đặt và kiểm','Nửa vòng quanh M gửi N tới(14,4),C tới(10,0),D tới(14,0), không giống các điểm sau tịnh tiến.','Quay nửa vòng quanh M cho chữ nhật14×4 cm','Hai miếng mới chỉ chung cạnh MB, không chồng diện tích; mép trên phủ0..7 rồi7..14, mép dưới phủ0..10 rồi10..14. Vùng phủ khi đặt đúng là56 cm². Không sửa các điểm của phép tịnh tiến để gọi nó là phép quay.')],
 [('Phần chồng','Tam giác (7,0),(10,0),(7,4), diện tích6 cm²',''),('Phần hở','Tam giác (11,4),(14,4),(14,0), diện tích6 cm²',''),('Vùng phủ sau tịnh tiến',50,'cm²'),('Phép sửa','Nửa vòng quanh M, ghép chữ nhật14×4 cm','')],
 hs('So từng mép của hai miếng đã dịch với hình chữ nhật cần phủ.','Vùng chồng phải được tính một lần khi đo phần mặt phẳng có phủ.','Đối chiếu ảnh của từng đỉnh dưới hai phép đặt trước khi kết luận phép nào ghép kín.'),
 dict(kind='trapezoid_bad_translate',lower=[[0,0],[10,0],[7,4],[0,4]],upper_original=[[0,4],[7,4],[4,8],[0,8]],upper_bad=[[7,0],[14,0],[11,4],[7,4]],center=[7,4],target=[[0,0],[14,0],[14,4],[0,4]],expected_overlap='6',expected_gap='6',expected_bad_union='50',expected_good_union='56'),
 'Wrong translation versus correct midpoint halfturn tested on exact piece positions; demonstrates actual overlap/gap and difference between piece-area sum and geometric union.',student='Dịch miếng trên như vậy được chữ nhật14×4 cm kín không chồng, nên vùng phủ là56 cm².')

def snapshot_inputs():
 q=read(BASE/'next_uncovered_tasks.json');global TASKS,NEAREST
 TASKS={t['master_id']:t for t in q['global_master_tasks'] if t['master_id'] in MASTERS};assert set(TASKS)==set(MASTERS)
 selected={
 MASTERS[0]:[532,534],MASTERS[1]:[120,308],MASTERS[2]:[626,627,120],MASTERS[3]:[277],MASTERS[4]:[709,515],MASTERS[5]:[728,727]}
 old=OLD/'current_sources.jsonl';lines=old.read_bytes().splitlines();captured=[]
 for master,linenos in selected.items():
  refs=[]
  for lineno in linenos:
   b=lines[lineno-1];r=json.loads(b);assert r['split']=='train' and not any(v in r['sample_id'].casefold() for v in ['holdout','eval','pilot','protected'])
   ref=dict(sample_id=r['sample_id'],source_file='current_sources.jsonl',line=lineno,sha256=sha(b))
   matching=[x for x in TASKS[master]['nearest_refs'] if x['sample_id']==r['sample_id']]
   if matching:assert matching[0]['sha256']==ref['sha256']
   refs.append(ref);captured.append(dict(master_id=master,reference=ref,actual_fields={k:r.get(k) for k in FIELDS},grade=r['grade'],selection_basis='Exact task nearest reference' if matching else 'Additional actually read relevant fixed queue/area comparator; does not replace old task metadata.'))
  NEAREST[master]=refs
 write(OUT/'candidate_snapshot.json',dict(queue_sha256=sha((BASE/'next_uncovered_tasks.json').read_bytes()),masters=[TASKS[k] for k in MASTERS],selection='Six assigned exact masters only; no original queue changes.',image_receipts_newly_viewed=False))
 jl(OUT/'nearest_actual_fullfields.jsonl',captured)

def validate_and_write():
 assert len(ROWS)==12 and len({r['sample_id'] for r in ROWS})==12
 spec=importlib.util.spec_from_file_location('relation_oracle',OUT/'independent_relation_oracle.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 qa=[];numeric=[];oracles=[];mutations=[];chats=[]
 for r in ROWS:
  b=dump(r).encode();h=sha(b);sid=r['sample_id'];oracle=mod.verify(r)
  oracles.append(dict(sample_id=sid,source_row_sha256=h,status='PASS_AUTHOR_SEPARATE_ORACLE',oracle=oracle))
  mutation=json.loads(dump(r))
  try:mutation['expected_answer'][0]['result']=str(F(mutation['expected_answer'][0]['result'])+1)
  except ValueError:mutation['expected_answer'][0]['result']='INCORRECT_MUTATED_ANSWER'
  try:mod.verify(mutation)
  except (AssertionError,ValueError):mutations.append(dict(sample_id=sid,source_row_sha256=h,wrong_answer_detected=True))
  else:raise AssertionError('oracle failed to reject wrong answer '+sid)
  prev={}
  for st in r['worked_steps']:
   assert st['reason'] and st['explanation'] and 'unit'in st
   if st.get('expression'):
    expr=re.sub(r'\{(s\d+)\}',lambda x:'('+str(F(prev[x[1]]))+')',st['expression']);f=evaluate(expr,'fraction');assert f==F(st['result'])
    with localcontext() as ctx:
     ctx.prec=90;d=evaluate(expr,'decimal');assert abs(d-Decimal(f.numerator)/Decimal(f.denominator))<Decimal('1e-70')
    numeric.append(dict(sample_id=sid,source_row_sha256=h,step_id=st['step_id'],expression=expr,exact=str(f),fraction_decimal_agree=True))
   prev[st['step_id']]=st['result']
  criteria=[dict(criterion=k,passed=True,evidence=v) for k,v in [
   ('actual_problem_givens_request_consistency',r['pedagogical_review_decision']),('mathematical_and_finite_oracle','Separate finite/geometric oracle checks exact answer values; every numeric expression passes Fraction and Decimal.'),('worked_steps_reason_units_check','Actual steps explain why relation/operation applies, retain requested unit, and check coverage/inverse/alternatives.'),('guidance_and_three_hints','Actual initial and all hint texts/questions read; no requested filled answer, final label or whole solution supplied.'),('grounded_student_work_and_assets','Corrections quote only supplied synthetic student work; explicit model, no unseen image or physical result claimed.'),('grade_and_substantive_branch_diversity','Declared grade-specific text enrichment; pairs change logic/ordering/feasibility/motion role, not merely constants.'),('source_provenance_hash_and_limits','Original AI authorship and draft status retained; no human signoff; exact row hash, nearest refs and inherited page receipts bound.')]]
  qa.append(dict(sample_id=sid,source_row_sha256=h,status='AUTHOR_SELF_QA_PASSED_PENDING_ROOT',criteria=criteria,actual_fields={k:r[k] for k in FIELDS},human_review_claimed=False))
  for c in chat_records(r):
   c.update(source_row_sha256=h,acceptance_status=r['acceptance_status'],quality_status=r['quality_status']);L.validate_chat(c)
   target=json.loads(c['messages'][2]['content'])
   if c['mode']=='worked_solution':assert target['steps']==r['worked_steps'] and target['answer']==r['expected_answer']
   else:
    hi=r['hints'][int(c['mode'][-1])-1];assert target==dict(hint=hi['hint'],question=hi['question'])
   chats.append(c)
 # Compare exact questions/IDs with existing sources without evaluating sealed data.
 existing=[]
 for path in [OLD/'current_sources.jsonl',OLD/'release/accepted_cases.jsonl',HERE/'cloud_publication/sgk_finish_20261020/release/accepted_cases.jsonl',HERE/'cloud_publication/sgk_remaining_20261020/release/accepted_cases.jsonl']:
  existing += [json.loads(b) for b in path.read_bytes().splitlines() if b.strip()]
 for folder in [HERE/'cloud_publication/sgk_final_forms_20261020/g5_exact_text',HERE/'cloud_publication/sgk_final_forms_20261020/g5_residual_text']:
  existing += [json.loads(b) for b in (folder/'cases.jsonl').read_bytes().splitlines() if b.strip()]
 norm=lambda v:re.sub(r'\s+',' ',v).strip().casefold()
 oldids={r['sample_id'] for r in existing};oldquestions={norm(r['problem']) for r in existing}
 assert not any(r['sample_id'] in oldids or norm(r['problem']) in oldquestions for r in ROWS)
 outputs={'cases.jsonl':ROWS,'chat.jsonl':chats,'selfqa7.jsonl':qa,'independent_oracles.jsonl':oracles,'numeric_fraction_decimal.jsonl':numeric,'adversarial_answer_mutations.jsonl':mutations}
 for name,items in outputs.items():jl(OUT/name,items)
 saved=[json.loads(b) for b in (OUT/'cases.jsonl').read_bytes().splitlines()];assert saved==ROWS
 assert len(chats)==48 and len({c['sample_id'] for c in chats})==48
 for r in saved:assert [g['id'] for g in r['givens']]==[f'g{i}' for i in range(len(r['givens']))] and [s['step_id'] for s in r['worked_steps']]==[f's{i}' for i in range(len(r['worked_steps']))]
 manifest=dict(status='12_DRAFTS_AUTHOR_QA_COMPLETE_PENDING_ROOT',cases=12,chat_rows=48,by_grade=dict(Counter(str(r['grade']) for r in ROWS)),masters=dict(Counter(r['coverage']['finite_master_id'] for r in ROWS)),numeric_steps=len(numeric),separate_oracles=12,wrong_answer_mutations_rejected=len(mutations),actual_nearest_rows_read=12,helper_sha256=sha(Path(__file__).read_bytes()),oracle_helper_sha256=sha((OUT/'independent_relation_oracle.py').read_bytes()),files={p.name:dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in sorted(OUT.iterdir()) if p.is_file() and p.suffix in ['.jsonl','.py']},training_started=False,drive_mutated=False,old_state_mutated=False,limits=['Original explicit text/grid models only; inherited image receipts not newly viewed.','Grade5 trapezoid branch does not close lower-grade dissection aliases.','Root/peer exact-content review required; no human content attestation or accuracy guarantee.'])
 write(OUT/'manifest.json',manifest);write(OUT/'validation_receipt.json',dict(status='PASS_DRAFT_NOT_ACCEPTED',cases=12,chat_rows=48,numeric_steps=len(numeric),independent_oracles=12,source_chat_hash_links=48,all_technical_ids_canonical=True,exact_duplicate_checks_passed=True,preserved_input_snapshot_sha256=sha((BASE/'next_uncovered_tasks.json').read_bytes()),training_started=False));print(dump(manifest))

def main():
 OUT.mkdir(parents=True,exist_ok=True);snapshot_inputs();author();validate_and_write()
if __name__=='__main__':main()
