"""Bounded 24 original finite geometry drafts; existing artifacts immutable; no training/Drive."""
from pathlib import Path
from fractions import Fraction
from decimal import Decimal,localcontext
from collections import Counter
import hashlib,json,re,importlib.util,copy,sys
import exhaustive_colab_loader as L
from exhaustive_primary_math import chat_records
from sgk_completion_edges import step,calc
HERE=Path(__file__).resolve().parent
OUT=HERE/'cloud_publication/sgk_final_gaps_20261021/geometry_inventory'
def dumps(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha(b):return hashlib.sha256(b).hexdigest()
def write(n,x):(OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def jl(n,rs):(OUT/n).write_text(''.join(dumps(r)+'\n' for r in rs),encoding='utf-8',newline='\n')
def build():
    tasks=json.loads((OUT/'candidate_snapshot.json').read_text('utf-8'));rows=[]
    def add(master,grade,branch,problem,request,steps,answer,hints,model,expected,difference,student=None,candidates=None,scope=None):
        t=tasks[master];sid='sgk_final_geometry_20261021_'+branch
        for i,s in enumerate(steps):s['step_id']='s'+str(i)
        ids=candidates or t['candidate_ids']
        row=dict(sample_id=sid,case_group_id=sid+'_group',grade=grade,topic=branch,case_kind='observable_student_error' if student else 'original_finite_representation',split='train',
          problem=problem,givens=[dict(id='g0',text=problem,value=None,unit='',role='EXPLICIT_FINITE_TEXT_AS_SUPPLIED')],requested_quantity=request,
          student_work=dict(text=student,observations=[dict(excerpt=student,claim_scope='Only the explicitly supplied synthetic statement; no inferred hidden cognition or unseen image/physical result.')]) if student else None,
          can_solve=True,worked_steps=steps,expected_answer=[dict(quantity=q,result=str(v),unit=u) for q,v,u in answer],
          initial_guidance=[hints[0]],hints=[dict(level=i+1,hint=h,question=['Em cần giữ đúng những dữ kiện và luật nào?','Em thử và ghi các trường hợp hợp lệ thế nào?','Em kiểm đủ điều kiện, không bỏ sót hay đếm lặp ra sao?'][i]) for i,h in enumerate(hints)],
          acceptance_status='DRAFT_AWAITING_ROOT_CONTENT_CROSS_REVIEW',quality_status='AUTHOR_SELF_QA_ROOT_REVIEW_PENDING',source_role='AI_GENERATED',human_verified=False,teacher_certified=False,owner_human_reviewed=False,
          provenance=dict(authorship_origin='ORIGINAL_AI_TEACHER_AUTHORING',acceptance_basis='OWNER_PREAUTHORIZED_PROCESS_ROOT_QA_PENDING',book_exercise_copied=False,human_content_review_completed=False,actual_physical_or_publisher_image_result_claimed=False),
          curriculum_assignment=dict(grade=grade,enrichment=True,master_id=master,candidate_ids=ids,actual_page_receipts=t['exact_page_receipts'],page_receipt_basis='Previously viewed publisher receipts inherited; this author does not claim a new view.',coverage_claim=scope or 'This explicit original finite text model only; no publisher image/physical result or whole-curriculum certification.'),
          coverage=dict(mode='FINITE_SUPPLEMENTARY_APPEND_NOT_CORE',finite_master_id=master,candidate_ids=ids,branch=branch,new_core_slots_claimed=0,numbers_only_variant=False,text_relation_only=True,visual_physical_coverage_claimed=False),
          nearest_source_comparison=dict(status='NEAREST_ACTUAL_FULLFIELDS_READ',evidence='nearest_actual_fullfields.jsonl',nearest_refs=t['nearest_refs'],semantic_difference=difference,limitation='Only bounded nearest valid-training sources, not an absence proof over archives.'),
          independent_model=model,independent_expected=expected)
        row['canonical_signatures']=L.source_signatures(row);rows.append(row)
    st=step
    def cells(s):return [[ord(c)-65 if False else (ord(c)-65)%3,2-(ord(c)-65)//3] for c in s]
    whole=cells('ABCDEFGHI');fixed=cells('ABDEG')
    m='complementary_irregular_boundary_match'
    add(m,1,'notched_piece_exact_complement',
      'Mô hình bằng chữ là bảng 3 hàng, 3 cột ô vuông bằng nhau: hàng trên A B C, hàng giữa D E F, hàng dưới G H I. Miếng P liền nhau che đúng A,B,D,E,G. Muốn lấp kín bảng, ghép thêm đúng một miếng, không chồng và không cắt. Các miếng đang được đặt thử theo nhãn ô: Q che C,F,H,I; R che C,F,I; S che C,E,H,I. Chỉ tịnh tiến từ bàn phụ đến đúng vị trí thử đã nêu, không xoay hay lật; các nhãn xác định chỗ cuối. Chọn mọi miếng ghép kín với P và kiểm cả mép lõm. Không cần ảnh ngoài mô tả.',
      'Miếng bổ sung hợp lệ',
      [st('Tìm phần bảng chưa được phủ','Phải bù đúng những ô ngoài P, kể cả ô ở chỗ lõm.','C,F,H,I','P đã chiếm A,B,D,E,G; đọc đủ chín ô thấy bốn ô còn lại nối thành miếng gấp khúc.'),
       st('Thử từng miếng theo chỗ đã nêu','Đủ số ô chưa bảo đảm khớp đúng vị trí.','Q đạt; R,S không đạt','Q phủ đúng C,F,H,I; R thiếu H. S che E đã có P và vẫn để hở F, dù S có bốn ô.'),
       st('Kiểm mép chung và cả bảng','Không chồng và không hở phải đúng đồng thời.','Q','Ghép P với Q dùng mỗi ô của bảng một lần; cạnh ô H tiếp giáp G và I nên góc lõm được bù, không chỉ khớp một cạnh.')],
      [('Miếng hợp lệ','Q','')],['Ghi các ô đã có miếng cố định và các ô còn trống.','Đối chiếu vị trí từng ô của miếng thử, không chỉ đếm số ô.','Kiểm chỗ lõm, chỗ chồng và chỗ hở cho mọi miếng được cho.'],
      dict(kind='boundary',whole=whole,fixed=fixed,options={'Q':cells('CFHI'),'R':cells('CFI'),'S':cells('CEHI')},turns=[0]),
      dict(valid=['Q:0']),'Irregular concave complementary cell-boundary selection with overlap and gap decoys; not two triangles restored along a known cut.')
    add(m,1,'notched_piece_rotation_without_reflection',
      'Bảng và miếng P như sau: hàng trên A B C, giữa D E F, dưới G H I, mọi ô bằng nhau; P cố định ở A,B,D,E,G. Miếng Q trên khay 3×3 giống bảng đang che A,B,D,G; miếng R che A,D,G,H. Được xoay cả khay một phần tư vòng, nửa vòng hoặc ba phần tư vòng quanh ô E, hoặc giữ nguyên, rồi chuyển khay trùng đúng chín ô bảng. Không được lật mặt khay, trượt lệch ô, cắt hoặc chồng. Chọn mọi miếng và góc xoay ghép kín với P. Bạn nói: “Lật R cũng được vì hình trông gần giống.” Kiểm câu đó đúng luật đã cho.',
      'Miếng, phép xoay hợp lệ và điều kiện không lật',
      [st('Cố định phần cần bù','Phần trống vẫn phải đúng C,F,H,I.','Tìm một thanh ba ô với ô nhô đúng phía','Không xoay P và không đổi nhãn ô của bảng. Mỗi miếng thử phải phủ phần bù, chứ không chỉ có cùng số ô.'),
       st('Thử bốn hướng của từng khay','Luật chỉ có bốn hướng xoay, không có phép lật.','Q xoay nửa vòng; R không có hướng đạt','Q:A,B,D,G sau nửa vòng thành I,H,F,C. R có thanh ba ô và nhánh ở phía ngược; thử đủ bốn hướng vẫn không trùng C,F,H,I.'),
       st('Kiểm câu và đường bao','Một phép bị cấm không thể dùng để hợp thức hóa đáp án.','Chỉ Q xoay 180 độ','Khay Q đúng hướng phủ bốn ô trống và không chạm vào phần trong của P. Câu lật R không tuân điều kiện không lật; không nhận là cách ghép.')],
      [('Cách ghép','Q xoay nửa vòng (180 độ); R không đạt','')],['Giữ nguyên bảng đích và phần đã có khi thử quay khay.','Liệt kê từng hướng xoay được phép cho mỗi miếng.','Phân biệt xoay trên mặt bàn với lật mặt và kiểm từng ô sau đổi hướng.'],
      dict(kind='boundary',whole=whole,fixed=fixed,options={'Q':cells('ABDG'),'R':cells('ADGH')},turns=[0,1,2,3]),
      dict(valid=['Q:180']),'Legal rotation versus forbidden reflection of asymmetric notched polyomino; exact four-orientation completeness, not number-only complement.',
      student='Lật R cũng được vì hình trông gần giống.')
    m='composite_shape_square_nonaligned_inventory'
    pts=dict(A=[0,0],B=[4,0],C=[4,4],D=[0,4],E=[2,0],F=[4,2],G=[2,4],H=[0,2],O=[2,2])
    ed=['AB','BC','CD','DA','EG','FH','EF','FG','GH','HE']
    for damaged in [False,True]:
      branch='tilted_square_complete_inventory' if not damaged else 'tilted_square_missing_side'
      pr='Một hình vuông lớn ABCD có các góc theo thứ tự quanh biên; E,F,G,H lần lượt ở giữa AB,BC,CD,DA. O là giữa bảng. Đã vẽ đủ bốn cạnh ngoài, đường E-O-G và H-O-F; thêm các nét nối E-F,F-G,G-H,H-E tạo một hình vuông nghiêng. Không có nét khác. '+('Riêng nét E-F bị xóa hoàn toàn; mọi nét khác giữ nguyên. ' if damaged else '')+'Chỉ đếm hình vuông có bốn cạnh được vẽ trọn; hình nghiêng vẫn được tính, cùng một miền không đếm lại. Liệt kê theo các đỉnh và tổng số; không tự nối nét chưa có. Các ô nhỏ AEOH,EBFO,OFCG,HOGD là hình vuông.'
      add(m,1,branch,pr,'Mọi hình vuông còn đường bao',
       [st('Nhóm các hình vuông cùng hướng với bảng','Mỗi ô nhỏ có bốn cạnh bằng nhau và góc như góc tờ giấy.','AEOH;EBFO;OFCG;HOGD;ABCD','Bốn ô nhỏ và hình vuông ngoài đều có đường bao đủ. Miền một hàng hai ô là chữ nhật dài nên không thêm vào.'),
        st('Kiểm hướng nghiêng','Không dựa vào việc cạnh có nằm ngang hay không.','Không còn vuông nghiêng EFGH' if damaged else 'EFGH cũng là hình vuông','EFGH có bốn cạnh bằng nhau, các góc vuông. '+('Nhưng E-F đã mất nên biên hở, không đếm; các đoạn khác không thay thế được cạnh nghiêng ấy.' if damaged else 'Nó dùng các nét nối các điểm giữa; đường bao trọn nên phải tính thêm, dù không trùng ô nhỏ.')),
        st('Kiểm đủ kích cỡ và hướng','Các nét chỉ có hai hướng ngang-dọc và hai hướng nghiêng đã nêu.','5' if damaged else '6','Ngoài nhóm ô nhỏ, bảng ngoài và EFGH, không có bốn cạnh đã vẽ nào khép thêm một hình vuông khác. '+('Năm hình còn lại không dùng nét E-F.' if damaged else 'Bốn nhỏ cộng một ngoài cộng một nghiêng là sáu.'),'4+1' if damaged else '4+1+1','hình vuông')],
       [('Danh sách','AEOH;EBFO;OFCG;HOGD;ABCD'+('' if damaged else ';EFGH'),''),('Tổng','5' if damaged else '6','hình vuông')],
       ['Nhóm các đường bao theo hướng và kích cỡ, kể cả hướng nghiêng.','Mỗi hình cần đủ bốn cạnh thật sự có trong mô tả.','Kiểm tên hình có chỉ cùng một miền bị đổi thứ tự hay không.'],
       dict(kind='squares',points=pts,edges=[e for e in ed if not damaged or e!='EF']),
       dict(shapes=sorted(['AEHO','BEFO','CFGO','DGHO','ABCD']+([] if damaged else ['EFGH']))),
       'Non-axis square from midpoint diamond alongside axis-aligned sub-squares; '+('deleting one oblique boundary while preserving axis squares.' if damaged else 'complete inventory checks rotated versus orientation-biased counting.'))
    m='fixed_piece_assembly_feasibility'
    tri=[[0,0],[2,0],[0,2]]
    add(m,3,'triangle_pair_selection_fixed_target',
      'Ba miếng tam giác giấy đều vuông. A và B có hai cạnh tạo góc vuông dài 2 ô và 2 ô; C có hai cạnh tạo góc vuông dài 4 ô và 1 ô. Mỗi ô có cạnh bằng nhau. Chọn đúng hai miếng trong A,B,C để phủ bảng vuông 2 ô × 2 ô. Được xoay từng miếng các góc một phần tư vòng và chuyển nguyên miếng để các đỉnh vào nút ô; không lật, cắt, chồng hoặc thò khỏi bảng. Chọn mọi cặp có thể ghép kín và nêu một cách xếp cho cặp đạt. Hỏi theo mô hình, không xác nhận đã cắt ghép thật.',
      'Mọi cặp ghép kín và cách xếp',
      [st('Kiểm miếng có đặt lọt bảng không','Miếng muốn tham gia phải nằm trọn trong bảng.','C không đặt lọt','C có một cạnh theo hướng ô dài 4 ô; ở các hướng xoay được phép, bề ngang hoặc bề dọc vẫn trải 4 ô, vượt cạnh bảng 2 ô. Không cắt C để làm nó lọt.'),
       st('Thử hai miếng còn lại','Hai tam giác cùng cỡ có thể nằm hai phía đường chéo.','A và B','Đặt A vào nửa dưới-trái của bảng, B vào nửa trên-phải, hai cạnh xiên trùng nhau trên đường chéo. Mỗi miếng có hai cạnh góc vuông 2 ô.'),
       st('Kiểm mọi cặp và phần phủ','Có ba cặp AB,AC,BC; cặp chứa C đã bị loại.','Chỉ AB','AB có chung mép nhưng không chung phần trong, ngoài là đúng bảng 2×2 nên không hở. AC và BC không thể vì C không lọt, dù mỗi cặp có tổng diện tích bằng diện tích bảng.')],
      [('Cặp hợp lệ','AB',''),('Cách ghép','A và B nằm hai phía một đường chéo của bảng vuông','')],
      ['Kiểm từng miếng có thể nằm trọn trong bảng theo các phép xoay được cho.','Với cặp còn có thể, thử ghép các cạnh và kiểm phần trong.','Liệt kê mọi cặp, không dùng tổng diện tích làm bằng chứng duy nhất.'],
      dict(kind='pair_assembly',pieces={'A':tri,'B':tri,'C':[[0,0],[4,0],[0,1]]},target_size=[2,2]),
      dict(valid_pairs=['AB']),'Selecting among fixed triangular pieces with congruent and equal-area nonfit decoys; quarter-turn placement enumeration, not guaranteed original-cut restoration.',
      candidates=['fixed_piece_assembly_feasibility','g2v1:piece_tiling'])
    add(m,4,'equal_area_nonfit_thin_rectangle',
      'Có hai miếng tam giác vuông cân A,B, mỗi miếng có hai cạnh góc vuông dài 2 cm. Bảng đích là hình chữ nhật dài 4 cm, rộng 1 cm, các cạnh theo hai hướng của lưới ô vuông 1 cm. Chỉ xoay miếng một phần tư vòng, nửa vòng hoặc ba phần tư vòng và tịnh tiến sao cho đỉnh nằm ở nút lưới; không lật, cắt, chồng hoặc thò ra. Bạn nói: “Tổng diện tích bằng nhau nên chắc chắn ghép kín.” Kiểm khả năng ghép, không đổi hình đích hoặc cho phép xoay thêm góc khác.',
      'Khả năng ghép với phép xoay đã cho',
      [st('Kiểm diện tích như điều kiện cần','Mỗi tam giác bằng nửa hình vuông cạnh 2 cm.','4','Diện tích mỗi miếng là 2 cm², hai miếng là 4 cm²; bảng 4×1 cũng 4 cm². Điều này chỉ loại được sai tổng, chưa chứng minh đặt lọt.','(2*2/2)*2','cm²'),
       st('Kiểm bề dọc theo phép xoay','Các phép xoay một phần tư vòng giữ hai cạnh góc vuông song song các cạnh bảng.','Không miếng nào nằm trọn trong dải rộng 1 cm','Mỗi hướng cho phép vẫn có độ trải 2 cm theo bề dọc. Tịnh tiến không giảm độ trải ấy; dải bảng chỉ rộng 1 cm.'),
       st('Kiểm kết luận của câu nói','Ghép kín bắt buộc từng miếng ở trong bảng.','Không thể ghép theo luật','Không có hướng và vị trí hợp lệ ngay cho một miếng, nên hai miếng không ghép được. Giữ kết quả diện tích đúng nhưng bác bỏ suy luận đủ diện tích là chắc chắn ghép được.')],
      [('Khả năng','Không thể ghép theo các phép đã cho','')],['Tách điều kiện tổng diện tích khỏi điều kiện một miếng có đặt lọt hay không.','Xét độ trải của miếng theo mọi hướng được phép.','Nếu có miếng không thể nằm trong bảng thì kết luận cho cả cách ghép phải xét điều đó.'],
      dict(kind='pair_assembly',pieces={'A':tri,'B':tri},target_size=[4,1]),dict(valid_pairs=[]),
      'Equal-area impossibility under explicitly restricted transforms; thin bounding-box obstruction rather than absence of a found arrangement.',
      student='Tổng diện tích bằng nhau nên chắc chắn ghép kín.')
    m='fixed_piece_silhouette_placement'
    house=[[[0,0],[2,0],[2,2],[0,2]],[[0,2],[2,2],[1,3]]]
    pieces=[house[0],[[0,2],[1,2],[1,3]],[[1,2],[2,2],[1,3]]]
    add(m,1,'square_two_triangles_house_silhouette',
      'Bóng ngôi nhà được mô tả gồm thân vuông 2 ô × 2 ô và mái là tam giác ở trên, chân mái trùng cả cạnh trên của thân, đỉnh mái ở giữa và cao thêm 1 ô. Có đúng một miếng vuông P bằng thân và hai miếng tam giác vuông cân Q,R, mỗi miếng có hai cạnh ngắn dài 1 ô. Được xoay trên bàn và chuyển nguyên miếng, không lật, cắt, chồng hoặc bỏ miếng. Nêu cách dùng cả ba miếng phủ kín ngôi nhà. Hướng lên và ô vuông đều được đề quy định; không dựa ảnh chưa cho.',
      'Vị trí cả ba miếng và kiểm phủ kín',
      [st('Đặt miếng có đường bao khớp thân','Thân và P đều vuông cùng cỡ.','P phủ phần thân','Đặt bốn cạnh P trùng bốn cạnh thân; P không phủ lên vùng mái ở phía trên.'),
       st('Chia mái theo đường từ đỉnh xuống giữa chân','Hai bên đường chia là hai tam giác vuông cân đúng cỡ Q,R.','Q bên trái mái; R bên phải mái','Mỗi miếng có cạnh ngang 1 ô ở nửa chân mái và cạnh đứng 1 ô ở giữa mái. Hai cạnh đứng chung nhau tạo mép trong, không phải phần giấy bị chồng.'),
       st('Kiểm toàn bóng','Ba miếng đều được dùng, mỗi miền bên trong chỉ phủ một lần.','Ghép kín ngôi nhà','P không lấn mái, Q và R chỉ gặp nhau ở mép; hai nửa chân mái nối thành cả chân mái. Không để một tam giác phủ lên tam giác kia rồi bỏ hở nửa mái.')],
      [('Cách đặt','P ở thân; Q trái mái; R phải mái, hai cạnh đứng ngắn gặp nhau ở giữa mái','')],
      ['Tách bóng đích theo các phần có đường bao được mô tả rõ.','Thử đường chia để các miếng mái chỉ gặp nhau ở mép.','Kiểm đủ từng miếng, cả chỗ nối thân và mái, không che chồng.'],
      dict(kind='partition',target=house,pieces=pieces),dict(areas=['4','1/2','1/2'],total='5'),
      'Fixed square plus two small triangular pieces in a non-square house silhouette; complete no-overlap/no-gap placement.',
      candidates=['G1V1_MULTIPIECE_SILHOUETTE_ASSET'])
    diamond=[[0,1],[1,0],[2,1],[1,2]]
    ps=[[[1,1],diamond[i],diamond[(i+1)%4]] for i in range(4)]
    add(m,4,'four_triangles_rotated_diamond_placement',
      'Trên lưới vuông 1 cm, bóng đích có bốn đỉnh (0,1),(1,0),(2,1),(1,2), thứ tự quanh biên; cặp số là (cột,hàng). Có đúng bốn miếng tam giác vuông cân có hai cạnh góc vuông 1 cm, ký hiệu A,B,C,D. Được xoay các góc một phần tư vòng và tịnh tiến nguyên miếng để đỉnh nằm ở nút lưới, không lật/cắt/chồng. Đặt một đỉnh góc vuông của mỗi miếng ở (1,1), hai đỉnh còn lại lần lượt là hai đỉnh bóng kề nhau: A phía dưới-trái, B dưới-phải, C trên-phải,D trên-trái. Kiểm kế hoạch có dùng đúng miếng và phủ kín không; không lấy hình vuông đứng cạnh 2 cm thay bóng nghiêng.',
      'Kiểm vị trí bốn miếng theo bóng nghiêng',
      [st('Đối chiếu hình mỗi vị trí','Tâm (1,1) cách mỗi đỉnh bóng một ô theo ngang hoặc dọc.','Mỗi vị trí là tam giác vuông cân đúng cỡ','Hai cạnh từ tâm đến hai đỉnh kề nhau vuông góc và cùng 1 cm; các vị trí đổi sang nhau bằng xoay một phần tư vòng. Không cần lật.'),
       st('Kiểm miền chung','Các đoạn từ tâm tới bốn đỉnh chia bóng thành bốn miền.','Chỉ chung cạnh, không chồng phần trong','A,B,C,D chiếm lần lượt đủ bốn miền quanh tâm. Cạnh ngoài của từng miền chính là một cạnh của bóng nghiêng.'),
       st('Kiểm diện tích và đường bao','Tổng diện tích là cách kiểm thêm sau khi kiểm vị trí.','2','Mỗi miếng bằng nửa ô vuông; bốn miếng phủ 2 cm². Đường bao là bốn cạnh nghiêng đã cho, không phải bảng vuông cạnh 2 cm có diện tích 4 cm².','4*(1*1/2)','cm²')],
      [('Kế hoạch','Hợp lệ; bốn miếng kín bóng nghiêng, không hở/chồng',''),('Diện tích bóng','2','cm²')],
      ['Đối chiếu các cạnh và góc của từng vị trí với miếng được cấp.','Kiểm các miền ở quanh tâm gặp nhau ở mép hay chồng phần trong.','So đường bao ngoài và tổng diện tích sau khi dùng đủ kho miếng.'],
      dict(kind='partition',target=[diamond],pieces=ps),dict(areas=['1/2']*4,total='2'),
      'Four-piece quarter-turn silhouette placement in rotated diamond with exact incidence and border proof.',
      candidates=['silhouette_piece_assembly'])
    tangram=[[[0,0],[4,0],[2,2]],[[0,0],[2,2],[0,4]],[[2,4],[4,2],[4,4]],[[2,2],[3,1],[4,2],[3,3]],[[4,0],[4,2],[3,1]],[[1,3],[2,2],[3,3]],[[0,4],[1,3],[3,3],[2,4]]]
    add(m,5,'seven_piece_tangram_exact_square_inventory',
      'Bóng đích là hình vuông trên lưới (cột,hàng) có đỉnh (0,0),(4,0),(4,4),(0,4), đơn vị 1 cm. Bộ tangram đúng bảy miếng: L1,L2 là hai tam giác vuông cân có hai cạnh góc vuông bằng đường chéo của ô vuông cạnh 2 cm; M là tam giác vuông cân có hai cạnh góc vuông 2 cm; S là hình vuông cạnh bằng đường chéo ô vuông 1 cm; T1,T2 là tam giác vuông cân có hai cạnh góc vuông bằng đường chéo ô vuông 1 cm; P là hình bình hành có các cạnh dài 2 cm và đường chéo ô vuông 1 cm, góc nhọn 45 độ. Được quay, tịnh tiến nguyên miếng và lật P; không cắt hay chồng. Đề xuất vị trí đỉnh theo biên: L1:(0,0),(4,0),(2,2); L2:(0,0),(2,2),(0,4); M:(2,4),(4,2),(4,4); S:(2,2),(3,1),(4,2),(3,3); T1:(4,0),(4,2),(3,1); T2:(1,3),(2,2),(3,3); P:(0,4),(1,3),(3,3),(2,4). Kiểm toàn bộ đề xuất, không chỉ tổng diện tích. Nếu T2 bị đặt trùng T1 thì tổng diện tích miếng vẫn có đủ hay kế hoạch vẫn hợp lệ?',
      'Kiểm đủ bảy vị trí và phản ví dụ chồng miếng',
      [st('Đối chiếu hình và cỡ của từng miếng','Tọa độ lưới xác định độ dài, góc và đường bao cụ thể.','Đủ L1,L2,M,S,T1,T2,P đúng hình','L1,L2 có diện tích 4 cm² mỗi miếng; M và S mỗi miếng 2 cm²; T1,T2 mỗi miếng 1 cm²; P là bình hành 2 cm². Mỗi vị trí tương ứng một miếng, không thêm miếng thứ tám.'),
       st('Kiểm kín và không chồng','Các miền trong đề xuất phải rời nhau và đều nằm trong bóng.','Đề xuất ban đầu phủ kín','L1,L2 phủ nửa dưới-trái, các miếng còn lại chia nửa trên-phải. T1 gặp S dọc cạnh (3,1)-(4,2); T2 gặp S dọc (2,2)-(3,3); P gặp T2 dọc (1,3)-(3,3). M gặp S/P theo đường từ (2,4) tới (4,2), tất cả chỉ chung mép.'),
       st('Kiểm tổng và phản ví dụ','Tổng diện tích đúng là cần nhưng không thay kiểm chồng/hở.','16','Tổng 4+4+2+2+1+1+2=16 cm² bằng bóng. Nếu T2 đặt trùng T1 thì miền của T2 cũ bị hở 1 cm² và miền T1 bị chồng 1 cm², nên kế hoạch sửa sai dù tổng diện tích giấy vẫn 16 cm².','4+4+2+2+1+1+2','cm²')],
      [('Đề xuất gốc','Hợp lệ; đủ bảy miếng, không hở/chồng',''),('Tổng diện tích','16','cm²'),('T2 trùng T1','Không hợp lệ: chồng 1 cm² và hở 1 cm²','')],
      ['Đối chiếu từng đa giác với đúng miếng trong bộ trước khi cộng diện tích.','Kiểm lần lượt các cạnh chung và các miền bên trong theo tọa độ.','Thử phân biệt diện tích giấy cộng dồn với diện tích phần bóng thực sự được phủ.'],
      dict(kind='partition',target=[[[0,0],[4,0],[4,4],[0,4]]],pieces=tangram),
      dict(areas=['4','4','2','2','1','1','2'],total='16'),
      'Actual seven classic tangram piece geometry, explicit target placement, legal flips, complete polygon no-gap/no-overlap and duplicate-placement counterexample.',
      candidates=['g5_candidate_tangram_assembly'])
    m='geometric_edge_removal_relocation'
    ptri=dict(A=[0,0],B=[2,0],C=[0,2],D=[1,0],E=[0,1],F=[1,1])
    etri=['AD','DB','AE','EC','BF','FC','DE','DF','EF']
    add(m,1,'remove_internal_stick_recount_all_triangles',
      'Một tam giác đều lớn ABC có mỗi cạnh dài hai que. D ở giữa AB,E ở giữa AC,F ở giữa BC. Có đúng chín que ở AD,DB,AE,EC,BF,FC,DE,DF,EF; ba nét trong nối các điểm giữa. Các que bằng nhau, không nét khác. Bỏ đúng que EF, không thêm hoặc chuyển que khác. Liệt kê mọi tam giác còn có đường bao kín, kể cả tam giác lớn; đổi thứ tự tên không đếm lại.',
      'Mọi tam giác sau bỏ EF',
      [st('Lập danh sách trước thay đổi','Ba điểm giữa chia hình lớn thành bốn tam giác nhỏ.','ADE;BDF;CEF;DEF;ABC','Bốn tam giác nhỏ cùng tam giác lớn đều đủ biên. Các bộ điểm thẳng hàng trên một cạnh không tạo tam giác.'),
       st('Loại đúng đường bao dùng EF','Chỉ hình có cạnh bị mất mới mất đường bao kín.','CEF và DEF bị loại','Hai hình đó đều cần EF. ADE dùng AD,AE,DE; BDF dùng BD,BF,DF; ABC dùng các que ngoài nên không bị mất biên.'),
       st('Kiểm cả hình ghép','Mất nét trong không tự làm mất đường bao ngoài.','3','Còn ADE,BDF,ABC là ba tam giác. Không giữ CEF,DEF bằng cách tưởng tượng lại que vừa bỏ.','2+1','tam giác')],
      [('Các tam giác','ADE;BDF;ABC',''),('Tổng','3','tam giác')],
      ['Ghi mọi đường bao trước khi bỏ que, gồm cả hình ngoài.','Đánh dấu những đường bao thực sự dùng que được bỏ.','Kiểm lại các hình còn đủ cạnh và không tính bộ đỉnh thẳng hàng.'],
      dict(kind='triangle_remove',points=ptri,edges=etri,remove=['EF']),
      dict(before=['ABC','ADE','BDF','CEF','DEF'],after=['ABC','ADE','BDF']),
      'Exact one-stick removal changes both corner and central triangles; recount all surviving composites rather than static enumeration.',
      candidates=['G1V2_REMOVE_MATCHES_TRIANGLE_COUNT_ASSET'])
    pr=dict(A=[0,0],B=[1,0],C=[2,0],D=[0,1],E=[1,1],F=[2,1],J=[4,0],K=[5,0],L=[6,0],M=[7,0])
    add(m,4,'relocate_three_sticks_complete_rhombi',
      'Mô hình có dải hai ô hình thoi bằng nhau: hàng dưới A-B-C, hàng trên D-E-F; hai hướng tạo góc 60 độ, mỗi bước ngang hoặc nghiêng đều dài một que. Chỗ của dải là AB,BC,DE,EF,AD,BE,CF. Xa bên phải có bốn điểm J-K-L-M thẳng hàng với ba chỗ JK,KL,LM mỗi chỗ một que; không nối với dải. Ban đầu đúng bảy que ở AB,AD,DE,EF,JK,KL,LM. Chuyển đúng ba que, mỗi que rời một chỗ cũ và đến một chỗ trống khác trong BC,BE,CF; không chồng, không cắt, giữ bảy que. Tìm mọi bộ chỗ lấy và đặt sao cho cuối cùng có hai hình thoi. Chỉ đếm đường bao theo hai hướng dải; hình ngoài cạnh 2 que và 1 que không phải hình thoi.',
      'Bộ ba chỗ lấy, đặt và các hình thoi cuối',
      [st('Xác định cạnh bắt buộc của mỗi hình thoi','Dải chỉ có hai ô cạnh một que; ngoài dài-rộng khác nhau nên không thêm hình thoi.','ABED cần AB,BE,DE,AD; BCFE cần BC,CF,EF,BE','Muốn đủ cả hai ô phải giữ AB,AD,DE,EF và thêm đúng BC,BE,CF. Các que xa không thể khép thêm hình theo hai hướng.'),
       st('Chọn ba que được chuyển','Giữ nguyên bốn cạnh bắt buộc đã có.','Lấy JK,KL,LM; đặt BC,BE,CF','Có đúng ba que thừa ở xa, tương ứng ba chỗ trống. Đổi cách gán từng que vào ba chỗ vẫn cùng bộ lấy/đặt, không tạo bộ hình mới.'),
       st('Kiểm kho và tính đủ','Không làm mất cạnh nào cần và không tạo thêm que.','Hai hình thoi ABED và BCFE','Bảy que cuối đúng AB,BC,DE,EF,AD,BE,CF. Mỗi ô kín có bốn cạnh bằng nhau; ngoài ACFD có hai cạnh dài hai que nên loại. Nếu lấy một trong bốn que giữ lại thì một ô hở, vì chỗ mới chỉ cho BC,BE,CF nên không thể sửa.')],
      [('Chỗ lấy','JK;KL;LM',''),('Chỗ đặt','BC;BE;CF',''),('Hình thoi','ABED;BCFE','')],
      ['Liệt kê cạnh bắt buộc của từng hình mục tiêu trước khi chuyển.','Giữ riêng chỗ đang có que và chỗ trống được phép nhận.','Kiểm mọi que lấy đi có làm hở một cạnh không thể đặt lại không.'],
      dict(kind='rhombus_move',points=pr,edges=['AB','AD','DE','EF','JK','KL','LM'],new_slots=['BC','BE','CF'],budget=3,goal=2),
      dict(plans=[dict(removed=['JK','KL','LM'],added=['BC','BE','CF'],rhombi=['ABDE','BCEF'])]),
      'Exactly three physical equal-length moves with restricted empty slots, all 35 removal sets checked; conservation, unique set and final rhombus type proof.',
      candidates=['geometric_matchstick_relocation'])
    m='irregular_region_unit_area_count'
    add(m,1,'irregular_staircase_full_unit_cells',
      'Bảng ô vuông bằng nhau có ba hàng đánh số từ dưới lên. Vùng tô màu gồm đúng các ô sau: hàng dưới tô ba ô liền từ trái; hàng giữa tô hai ô liền từ trái; hàng trên tô một ô bên trái. Các ô không nêu thì không tô. Các ô chỉ chung mép, không có ô bị tô hai lần. Lấy một ô vuông nhỏ làm một đơn vị phủ. Vùng màu chứa bằng mấy đơn vị? Không coi cả khung chữ nhật bao ngoài là vùng tô.',
      'Số đơn vị ô vuông trong vùng không chữ nhật',
      [st('Đếm riêng từng hàng đã tô','Số ô của khung có cả ô trắng không được hỏi.','Hàng dưới ba; giữa hai; trên một','Đánh dấu từng ô tô trong hàng, không kéo dài hàng trên hoặc giữa cho bằng hàng dưới.'),
       st('Gộp các hàng không chồng','Mỗi ô có duy nhất một hàng nên được đếm một lần.','6','Ba cộng hai cộng một bằng sáu ô vuông đơn vị.','3+2+1','đơn vị ô vuông'),
       st('Kiểm bằng phần trắng','Khung 3×3 còn ba ô trắng, không thuộc màu.','Sáu đơn vị màu','Hai ô trắng ở hàng trên và một ở hàng giữa không được thêm vào vùng. Chỉ đếm sáu ô được mô tả có tô.')],
      [('Số đơn vị','6','đơn vị ô vuông')],
      ['Theo đường biên tô màu từng hàng thay vì chỉ nhìn khung bao ngoài.','Đếm mỗi ô tô đúng một lần và bỏ ô không tô.','Có thể kiểm bằng số ô trắng nằm trong khung.'],
      dict(kind='unit_cells',full=['a','b','c','d','e','f'],halves=[]),dict(units='6'),
      'Nonrectangular stair-step region full-cell area unit inventory distinct from independent object counting and grid rectangle enumeration.')
    add(m,1,'diagonal_half_cells_regroup_without_doublecount',
      'Một vùng giấy trong lưới gồm hai ô vuông tô trọn A,B và bốn nửa ô là C-trái-dưới,D-phải-trên,E-trái-dưới,F-phải-trên. Mỗi ô C,D,E,F được chia theo đường chéo từ góc trái-trên đến góc phải-dưới; chỉ nửa đã ghi được tô. Các ô A đến F khác nhau, không trùng vị trí; ngoài sáu ô ấy không tô. Một nửa trái-dưới và một nửa phải-trên của các ô bằng nhau ghép thành đúng một ô vuông; được chuyển các nửa để kiểm nhưng không sao chép. Vùng tô có lượng giấy bằng mấy ô vuông trọn? Bạn viết: “Có sáu ô chạm màu nên tính sáu ô trọn.” Hãy kiểm.',
      'Số ô vuông trọn tương đương vùng tô',
      [st('Tách ô trọn và nửa ô','Chạm màu không có nghĩa cả ô được tô.','Hai ô trọn; bốn nửa ô','A,B tô cả ô. C,D,E,F mỗi ô chỉ có một nửa nên không tính từng ô đó như ô trọn.'),
       st('Ghép các nửa bổ sung','Hai nửa khác phía ghép vừa đúng một ô, không phủ chồng.','C ghép D; E ghép F','Mỗi cặp dùng một nửa trái-dưới và một nửa phải-trên theo cùng đường chéo, tổng thành một ô trọn. Đã dùng đủ bốn nửa đúng một lần.'),
       st('Cộng và kiểm câu','Đơn vị là giấy bằng một ô trọn, không là số ô có dính màu.','4','Hai ô trọn cũ và hai ô ghép là bốn đơn vị. Câu sáu ô trọn đã tính cả phần chưa tô của bốn ô có nửa màu.','2+1+1','đơn vị ô vuông')],
      [('Số ô trọn tương đương','4','đơn vị ô vuông')],
      ['Phân biệt ô được tô trọn với ô chỉ được tô một phần.','Ghép các phần bổ sung theo đúng đường chéo và không dùng lại phần đã ghép.','Kiểm tổng theo đơn vị ô trọn, không theo số ô chạm màu.'],
      dict(kind='unit_cells',full=['A','B'],halves=['C:LD','D:RU','E:LD','F:RU']),dict(units='4'),
      'Explicit diagonal half-cell regrouping for area equivalence, child-level two-halves language without formal fraction arithmetic.',
      student='Có sáu ô chạm màu nên tính sáu ô trọn.')
    m='midpoint_grid_multi_piece_dissection'
    for shifted in [False,True]:
      o=[3,1] if shifted else [3,2]
      pieces=[[[0,0],[2,0],[2,2],[0,2]],[[0,2],[2,2],[2,4],[0,4]]]+[[o,[2,0],[4,0]],[o,[4,0],[4,4]],[o,[4,4],[2,4]],[o,[2,4],[2,0]]]
      add(m,4,'six_piece_wrong_midpoint_equal_area_error' if shifted else 'six_piece_midpoint_complete_dissection',
       'Tờ giấy vuông cạnh 4 ô, ô vuông đơn vị bằng nhau. M,N là điểm giữa cạnh dưới và trên; nối MN chia thành hai chữ nhật 2×4. Lấy I,J giữa hai cạnh đứng của nửa trái, nối IJ để nửa trái thành hai vuông 2×2. Trong nửa phải, '+('chọn P ở giữa theo ngang nhưng cách cạnh dưới 1 ô; P không ở giữa theo dọc' if shifted else 'chọn P là giao hai đường chéo, tức ở giữa cả ngang và dọc')+'. Nối P với cả bốn góc nửa phải. Các nét vừa nêu là toàn bộ đường cắt, không cắt các đường chéo phụ để tìm P. Cần kiểm số miếng, kín/không chồng và diện tích các miếng theo ô vuông. '+('Bạn nói: “P nhìn ở giữa nên bốn tam giác đều bằng nhau.” Kiểm câu đó.' if shifted else 'Bốn tam giác có nhất thiết cùng hình dạng với nhau không?'),
       'Sáu miền cắt, diện tích và vai trò điểm giữa',
       [st('Liệt kê vùng theo những đoạn đã cắt','Nối P với bốn góc chia một chữ nhật thành bốn tam giác.','Hai vuông trái và bốn tam giác phải','Các đường trong nửa trái chỉ tạo hai ô vuông 2×2. Nửa phải có bốn tam giác quanh P; không coi đường chéo chỉ dùng định vị P là đường cắt thêm.'),
        st('Kiểm diện tích từng miền','Diện tích các tam giác phụ thuộc khoảng cách P tới cạnh tương ứng.','4;4;1;2;3;2' if shifted else '4;4;2;2;2;2','Hai vuông có diện tích bốn ô mỗi miếng. '+('Nửa phải: tam giác đáy dưới rộng2,cao1 bằng1; bên phải đáy4,cao1 bằng2; đáy trên rộng2,cao3 bằng3; bên trái bằng2. P không là điểm giữa nên không có bốn diện tích bằng nhau.' if shifted else 'Tam giác kề cạnh dưới/trên là nửa chữ nhật2×2, bằng2 ô; tam giác kề cạnh đứng là nửa chữ nhật4×1, cũng bằng2 ô. Cùng diện tích không có nghĩa cùng hình dạng: các đáy và độ cao khác nhau.')),
        st('Kiểm cả tờ giấy','Các miền tạo thành do chia liên tiếp, không bỏ hoặc phủ lại giấy.','16','Tổng diện tích vẫn là16 ô vuông; P nằm trong nửa phải nên các tam giác chỉ chung các cạnh từ P, không chồng trong và không có khe. '+('Câu bằng nhau sai ở việc gọi P là giữa theo dọc.' if shifted else 'Hai loại tam giác có hình dạng khác nhau dù cùng diện tích.'),'4+4+1+2+3+2' if shifted else '4+4+2+2+2+2','ô vuông')],
       [('Diện tích theo thứ tự: hai vuông, dưới, phải, trên, trái','4;4;1;2;3;2' if shifted else '4;4;2;2;2;2','ô vuông'),('Số miếng','6','miếng'),('Phủ kín','Có, không chồng phần trong','')],
       ['Phân biệt nét thật sự cắt với nét chỉ dùng để tìm điểm.','Gọi từng miền theo cạnh ngoài tương ứng rồi so khoảng cách tới điểm trong.','Kiểm tổng diện tích và mép chung; không suy bằng nhau từ vẻ gần giữa.'],
       dict(kind='partition',target=[[[0,0],[4,0],[4,4],[0,4]]],pieces=pieces),
       dict(areas=['4','4','1','2','3','2'] if shifted else ['4','4','2','2','2','2'],total='16'),
       'Exact six-piece midpoint dissection with complete coverage; '+('off-midpoint counterexample preserves partition but changes area equality.' if shifted else 'equal-area noncongruent triangular pieces distinguished, no implied physical cut.'),
       student='P nhìn ở giữa nên bốn tam giác đều bằng nhau.' if shifted else None)
    m='nonaxis_composite_quadrilateral_enumeration'
    hp=dict(O=[0,0],A=[1,0],B=[0,1],C=[-1,1],D=[-1,0],E=[0,-1],F=[1,-1])
    he=['AB','BC','CD','DE','EF','FA','OA','OB','OC','OD','OE','OF']
    for missing in [False,True]:
      names=['ABCO','BCDO','CDEO','DEFO','AEFO','ABFO'] if not missing else ['BCDO','CDEO','DEFO','AEFO']
      add(m,4,'three_direction_rhombi_complete' if not missing else 'three_direction_rhombi_missing_outer',
       'Một lục giác đều ABCDEF có sáu đỉnh theo thứ tự quanh biên và tâm O. Mọi cạnh ngoài và sáu đoạn OA,OB,OC,OD,OE,OF đều có độ dài một que, tạo sáu tam giác đều. '+('Đoạn AB đã bị xóa hoàn toàn, các đoạn khác giữ nguyên. ' if missing else '')+'Không có nét khác. Cần liệt kê mọi hình bình hành và trong đó mọi hình thoi có bốn đỉnh trong A,B,C,D,E,F,O; cạnh phải được vẽ trọn, có thể đi qua O nếu thẳng hàng. Đổi thứ tự gọi cùng bốn đỉnh không tính thêm. Không nhận hình chỉ có ba góc vì O nằm thẳng trên cạnh.',
       'Mọi bình hành, hình thoi trong mạng ba hướng',
       [st('Ghép các cặp tam giác kề nhau','Hai tam giác đều kề nhau có mép ngoài là hình thoi.',';'.join(names),'Ghi mỗi hình bằng bộ bốn đỉnh để không đếm lại khi xoay tên. '+('Hai cặp dùng tam giác OAB bị loại vì mất AB.' if missing else 'Có sáu vị trí ghép quanh tâm, bao gồm các hình có hướng khác nhau.')),
        st('Kiểm mọi cạnh và loại hình','Một bộ bốn điểm không đủ nếu cạnh không được vẽ hoặc một góc bị thẳng.','Các bình hành này đều là hình thoi','Bốn cạnh của mỗi hình được giữ đều là một que nên bằng nhau, từng cặp cạnh đối song song. Những đường nối qua tâm theo đường thẳng là đường chéo hoặc cạnh phải xét đúng, không tự tạo một đường nối chéo chưa vẽ.'),
        st('Kiểm tính đủ','Theo từng cặp hướng của mạng, hai đường đối diện phải nối bằng các nét có sẵn.','4' if missing else '6','Mạng chỉ có ba hướng cạnh. Thử các cặp hướng cho đúng các bộ vừa liệt kê; không có bình hành cạnh hai que vì sẽ cần đường song song nằm ngoài lục giác hoặc đường nối chưa vẽ. Đếm mỗi bộ bốn đỉnh một lần.', '6-2' if missing else '2+2+2','hình')],
       [('Bộ đỉnh bình hành',';'.join(names),''),('Bộ đỉnh hình thoi',';'.join(names),''),('Số mỗi loại','4' if missing else '6','hình')],
       ['Chọn đường bao kín theo từng cặp hướng, không chỉ theo hàng ngang-dọc.','Kiểm đủ bốn cạnh và bốn góc thật sự, kể cả đường qua tâm.','Ghi một bộ bốn đỉnh cho mỗi miền để tránh đếm lặp khi đổi thứ tự.'],
       dict(kind='quads',points=hp,edges=[e for e in he if not missing or e!='AB']),
       dict(parallelograms=sorted(names),rhombi=sorted(names)),
       'Three-direction equilateral hexagon-spoke network, unlike two-direction rectangular lattice; complete simple quadrilateral inventory'+(' with deleted oblique boundary.' if missing else '.'))
    m='seven_segment_glyph_inventory_relocation'
    alphabet='Mỗi ô chữ số có bảy vị trí: a ngang trên, b đứng phải-trên, c đứng phải-dưới, d ngang dưới, e đứng trái-dưới, f đứng trái-trên, g ngang giữa. Bảng chuẩn: 0=abcdef;1=bc;2=abdeg;3=abcdg;4=bcfg;5=acdfg;6=acdefg;7=abc;8=abcdefg;9=abcdfg. Mỗi vị trí được ghi có đúng một que, vị trí khác trống; các que bằng nhau. '
    add(m,1,'seven_segment_exact_four_stick_build',
      alphabet+'Chỉ dựng đúng một chữ số theo bảng, dùng hết bốn que trong một ô; không chồng que, không có kiểu chữ khác. Chọn mọi chữ số có thể dựng và ghi các vị trí đặt que. Không thêm nét để chữ trông đẹp hơn.',
      'Mọi chữ số dùng đúng bốn que',
      [st('Dùng bảng vị trí, không dùng nét viết tay','Mỗi vị trí có một que nên đếm số chữ trong mã.','Số que các chữ số 0..9: 6,2,5,5,4,5,6,3,7,6','Các mã dùng vị trí khác nhau trong cùng ô. Không gom hai vị trí thành một que dài hoặc tách một que thành hai.'),
       st('Đối chiếu đúng số que có','Dùng hết bốn que nghĩa là mã có đúng bốn vị trí.','Chữ số 4, vị trí b,c,f,g','Các chữ số khác cần ít hơn hoặc nhiều hơn bốn que theo bảng đã đếm, nên không được nhận dù quen nét khác.'),
       st('Kiểm cả kho và khuôn chữ','Các vị trí b,c,f,g đều khác nhau và tạo đúng mã chuẩn.','Chỉ 4','Dùng bốn que một lần và không để thừa. Đây là mã của chữ số bốn trong bảng, không phải hoán đổi thẻ chữ số.')],
      [('Chữ số','4',''),('Vị trí','b;c;f;g','')],
      ['Đếm các vị trí được bật trong từng mã chuẩn.','So số vị trí cần với đúng kho que được cấp.','Kiểm không đổi kiểu chữ hoặc ghép hai vị trí vào một que.'],
      dict(kind='seven_build',count=4),dict(digits=[4]),
      'Physical seven-segment glyph construction with fixed match count, not moving whole numeric cards.',
      candidates=['G1V2_MATCHSTICK_DIGIT_ASSET'])
    add(m,1,'seven_segment_one_move_equation_unique',
      alphabet+'Ba ô chữ số theo thứ tự trong đẳng thức 6 + 4 = 4. Các dấu + và = in sẵn, không phải que và không được sửa. Chuyển đúng một que: lấy khỏi một vị trí đang có trong ba ô rồi đặt vào một vị trí đang trống khác của ba ô; có thể cùng ô, không chồng hoặc dùng nét ngoài bảng. Cuối cùng cả ba ô vẫn là đúng một chữ số chuẩn. Tìm mọi đẳng thức đúng có thể được, nêu chỗ lấy và đặt. Dấu và số ô giữ nguyên.',
      'Mọi sửa đẳng thức hợp lệ bằng một que',
      [st('Giữ đúng phép và kho','Mỗi ứng viên cuối phải thay đúng một vị trí mất và một vị trí thêm.','Chỉ xét sửa trong các ô chữ số','Dấu in sẵn không được biến thành dấu khác. Có thể chuyển trong cùng một ô nhưng không xóa hẳn một chữ số.'),
       st('Đối chiếu mã và giá trị','Mã 6 là acdefg; bỏ giữa g rồi thêm phải-trên b sẽ thành abcdef.','6 thành 0 bằng g sang b trong ô đầu','Hai ô 4 giữ bcfg. Đẳng thức thành 0+4=4, đúng theo phép cộng; tổng que không đổi.'),
       st('Kiểm đủ mọi ô và vị trí','Mọi cách đều là chọn một que có và một chỗ trống rồi kiểm lại ba mã.','4','Duyệt đủ các vị trí của cả ba ô theo bảng chỉ thu được đẳng thức 0+4=4. Những đổi mã khác không thỏa phép cộng hoặc cần thêm lượt.','0+4','')],
      [('Đẳng thức','0+4=4',''),('Cách chuyển','Ô đầu: g sang b','')],
      ['Giữ nguyên dấu in sẵn và đánh dấu những vị trí đang có que.','Một cách chuyển phải tạo mã chuẩn ở cả ô bị lấy lẫn ô được đặt.','Tính lại đẳng thức sau mỗi cách hợp lệ, không chỉ xem chữ số có đẹp.'],
      dict(kind='seven',initial='644',budget=1,equation=True),
      dict(layouts=['044'],minimum=None),'Exact one physical segment move, fixed operators and digit slots, all legal removals/additions enumerated for equation repair.',
      candidates=['G1V2_SINGLE_MATCH_EQUATION_REPAIR'])
    add(m,4,'seven_segment_fixed_slots_global_minimum',
      alphabet+'Hai ô liền nhau đang ghi 69, trái là hàng chục, phải là hàng đơn vị. Chuyển đúng một que từ một vị trí đang có đến một vị trí trống khác ở hai ô; không sửa khung, không lật toàn ô, không chuyển cả chữ số. Cuối cùng vẫn đúng hai chữ số chuẩn, hàng chục không được 0. Tìm số nhỏ nhất có thể, nêu mọi số hợp lệ để chứng minh đã xét đủ và cách chuyển cho số nhỏ nhất.',
      'Số nhỏ nhất với đúng một que và hai ô',
      [st('Xét các mã cuối theo vị trí thay đổi','Một lần chuyển tương ứng đúng một chỗ mất và một chỗ thêm.','58;60;66;83;85;99','Từ mã của 6 và 9, duyệt mọi chỗ lấy và mọi chỗ trống. Loại ô không còn mã chuẩn và chữ số hàng chục 0; các giá trị hợp lệ không lặp là danh sách này.'),
       st('So các số hai chữ số','So hàng chục trước, rồi hàng đơn vị khi hàng chục bằng nhau.','58','Trong danh sách chỉ 58 có hàng chục 5; các số khác có hàng chục từ6 trở lên. Được 58 bằng lấy e ở ô trái của6 đặt e ở ô phải của9.'),
       st('Kiểm chuyển và tính tối thiểu','Mã6 bỏ e thành5; mã9 thêm e thành8.','Một que; 58 nhỏ nhất','Cả hai ô đều chuẩn, không số0 đầu, đúng một chỗ mất/thêm. Kết luận tối thiểu dựa trên toàn danh sách, không chỉ do tìm thấy một số nhỏ hơn69.')],
      [('Mọi số hợp lệ','58;60;66;83;85;99',''),('Số nhỏ nhất','58',''),('Chuyển','e ô trái sang e ô phải','')],
      ['Liệt kê ứng viên theo chỗ lấy và chỗ đặt thật sự của một que.','Giữ điều kiện mỗi ô còn đúng mã chữ số và không có số không đứng đầu.','So toàn bộ số hợp lệ theo hàng để chứng minh nhỏ nhất.'],
      dict(kind='seven',initial='69',budget=1),dict(layouts=['58','60','66','83','85','99'],minimum=58),
      'Complete global minimum under fixed digit-count/no-leading-zero convention and exact physical move conservation.',
      candidates=['seven_segment_single_move_minimum','g2v1:seven_segment_relocation'])
    add(m,4,'seven_segment_digit_count_change_two_moves',
      alphabet+'Có ba ô tách rời trái→phải. Ban đầu ô1 ghi1,ô2 ghi1,ô3 trống hoàn toàn: 11_. Mỗi que thuộc đúng một vị trí của một ô, không được đặt nối hai ô. Chuyển đúng HAI que khác nhau, mỗi que từ một vị trí ban đầu có que đến một vị trí ban đầu trống khác; không chuyển tạm, không đặt lại chỗ cũ. Cuối cùng mỗi ô phải là một chữ số chuẩn hoặc trống hoàn toàn; các ô có chữ số phải liền nhau, bỏ ô trống ở hai đầu khi đọc; không có0 đầu một số nhiều chữ số. Tìm mọi bố cục cuối, số nhỏ nhất, cách làm đổi số lượng chữ số. Giải thích vì sao đúng một lần chuyển không thể làm đổi số ô có chữ số theo các luật này. Ký hiệu _ nghĩa là ô trống, không phải chữ số0.',
      'Tối thiểu khi cho đổi số lượng chữ số và ngân sách hai que',
      [st('Giữ toàn kho và điều kiện ô trống','Ban đầu có bốn que, không mất hoặc thêm que.','Mã tổng bốn que chỉ có 4 hoặc cặp11','Một chữ số dùng bốn que chỉ là4; hai chữ số cùng dùng ít nhất hai que mỗi ô nên chỉ có1 và1. Ba chữ số cần ít nhất sáu que nên không thể.'),
       st('Duyệt bố cục đúng hai chỗ mất/thêm','Không coi ô hỏng còn một que là ô trống hợp lệ.','4__;_4_;_11','Giữ bc của ô1, chuyển b,c của ô2 sang f,g của ô1 được4__. Tương tự giữ ô2 và chuyển que ô1 sang f,g ô2 được_4_. Chuyển cả bc ô1 sang bc ô3 được_11. Đặt4 ở ô3 cần chuyển cả bốn que nên loại; giữ11_ là không chuyển nên loại.'),
       st('So số và kiểm một lượt không đủ','Bỏ ô trống đầu/cuối khi đọc nên hai bố cục4 cùng giá trị.','Số nhỏ nhất 4; số chữ số giảm từ hai còn một','4 nhỏ hơn11. Với một que, không thể làm một ô có chữ số thành trống vì chữ số ít nhất có hai que; cũng không thể biến ô trống thành chữ số bằng một que. Do đó đổi số ô có chữ số cần nhiều hơn một chuyển trong layout tách rời này.')],
      [('Bố cục cuối','4__;_4_;_11',''),('Số nhỏ nhất','4',''),('Cách đổi số chữ số','Lấy b,c ô2 đặt f,g ô1; đọc 4',''),('Một que có đổi số chữ số không','Không theo layout tách rời này','')],
      ['Đếm tổng que và phân biệt ô trống hoàn toàn với ô có nét không chuẩn.','Xét từng bố cục theo đúng số chỗ mất và thêm, giữ các ô có số liền nhau.','So giá trị sau khi bỏ ô trống đầu/cuối; kiểm riêng lập luận về một lượt.'],
      dict(kind='seven',initial='11_',budget=2,empty=True),
      dict(layouts=['4__','_11','_4_'],minimum=4),
      'Digit-count-changing branch is actually enumerable with two physical moves; one-move count-change impossibility is explicit rather than silently borrowing arbitrary handwriting layout.',
      candidates=['seven_segment_relocation_with_digit_count_change'])
    m='solid_visible_face_direction_binding'
    faces=[dict(direction='trước',label='đỏ',dots=2,visible=True),dict(direction='trên',label='xanh',dots=5,visible=True),dict(direction='phải',label='vàng',dots=3,visible=True)]
    add(m,1,'cube_marked_faces_fixed_view',
      'Đề quy định góc nhìn từ phía trước-phải và cao hơn một khối hộp. Bảng mô tả các mặt nhìn thấy: mặt trước màu đỏ có2chấm; mặt trên màu xanh có5chấm; mặt phải màu vàng có3chấm. Ba mặt còn lại không được mô tả và không áp dụng luật xúc xắc “hai mặt đối tổng7”. Hỏi màu của mặt trước, trên, phải theo đúng thứ tự và tổng chấm chỉ trên hai mặt trên-phải. Có biết tổng chấm cả sáu mặt không? Đây là bảng mặt được cho bằng chữ, không nhận là đã đọc một ảnh.',
      'Gắn nhãn theo hướng, tổng chọn mặt và giới hạn mặt khuất',
      [st('Giữ góc nhìn và nhãn mặt','Hướng được đề cho gắn với một mặt cụ thể, không theo màu quen thuộc.','Trước đỏ; trên xanh; phải vàng','Đọc ba cặp hướng-màu trong bảng; không tráo mặt trên với mặt trước chỉ vì cả hai đều nhìn thấy.'),
       st('Chỉ chọn các mặt được hỏi để cộng','Không cộng cả ba mặt khi chỉ hỏi trên-phải.','8','Trên có5chấm, phải có3chấm, cộng được8chấm; hai chấm trước không thuộc yêu cầu.','5+3','chấm'),
       st('Kiểm giới hạn dữ kiện','Mặt khuất chưa được mô tả nên không có số chấm để cộng.','Chưa biết tổng sáu mặt','Đề không nói là xúc xắc chuẩn và cấm suy luật đối tổng7. Cần thêm số chấm trên ba mặt còn lại nếu muốn tổng cả khối.')],
      [('Màu theo trước,trên,phải','đỏ;xanh;vàng',''),('Chấm trên-phải','8','chấm'),('Tổng sáu mặt','Chưa đủ dữ kiện','')],
      ['Gắn từng nhãn mặt với đúng hướng trong góc nhìn đã cho.','Chọn đúng các hướng câu hỏi yêu cầu trước khi cộng.','Tách dữ kiện đã nêu khỏi mặt khuất chưa có thông tin.'],
      dict(kind='faces',faces=faces,asked_directions=['trên','phải']),dict(labels=['xanh','vàng'],sum=8),
      'Marked face directions and requested face sum with explicit unknown hidden-face guard, distinct from whole-solid classification.')
    faces2=[dict(direction='trước',label='sao',dots=1,visible=True),dict(direction='trên',label='tròn',dots=4,visible=True),dict(direction='phải',label='tam giác',dots=2,visible=True)]
    add(m,1,'face_direction_wrong_label_not_shape_name',
      'Trong cùng một góc nhìn cố định của một hộp, bảng đã cho ghi: mặt trước dán ngôi sao có1chấm; mặt trên dán hình tròn có4chấm; mặt bên phải dán tam giác có2chấm. Các nhãn là hình vẽ trên mặt, không nói mặt hộp biến thành hình tròn hay tam giác. Bạn viết: “Nhãn tam giác ở trên, nhãn tròn ở bên phải.” Hãy sửa đúng hai nhãn theo bảng rồi nêu nhãn trước-trên-phải; đếm chấm trên mặt trên thôi, không quay hộp.',
      'Sửa gắn nhãn theo hướng của mặt',
      [st('Đối chiếu nguyên câu với bảng','Bảng đã cố định mặt mang mỗi nhãn, không yêu cầu suy từ hình dáng nhãn.','Câu viết đổi chỗ nhãn tròn và tam giác','Nhãn tròn được ghi ở mặt trên, tam giác ở mặt phải. Không có dữ kiện quay hộp để đổi hướng chúng.'),
       st('Gắn đủ ba hướng','Mỗi hướng được hỏi có một nhãn theo bảng.','Trước sao; trên tròn; phải tam giác','Giữ sao ở trước và sửa hai nhãn bị tráo đúng về hướng của chúng. Các nhãn chỉ là hình dán trên mặt.'),
       st('Đếm đúng mặt trên và kiểm','Câu hỏi cuối chỉ yêu cầu một hướng.','4','Mặt trên có4chấm; không lấy2chấm mặt phải. Đọc lại ba cặp trước-sao,trên-tròn,phải-tam giác để kiểm câu sửa.','4','chấm')],
      [('Nhãn trước,trên,phải','sao;tròn;tam giác',''),('Chấm mặt trên','4','chấm')],
      ['Đọc bảng theo hướng của mặt, không theo tên hình dán.','So từng phần câu đã viết với cặp hướng-nhãn được cho.','Giữ nguyên góc nhìn và chỉ đếm mặt được câu hỏi chọn.'],
      dict(kind='faces',faces=faces2,asked_directions=['trên']),dict(labels=['tròn'],sum=4),
      'Observable top/right label reversal with shape-on-face versus shape-of-face distinction, not speculative image interpretation.',
      student='Nhãn tam giác ở trên, nhãn tròn ở bên phải.')
    faces3=[dict(direction='trên',label='A',dots=1,visible=False),dict(direction='trước',label='A-trước',dots=6,visible=True),dict(direction='phải',label='A-phải',dots=4,visible=True),dict(direction='trên',label='B',dots=5,visible=True),dict(direction='trước',label='B-trước',dots=2,visible=True),dict(direction='phải',label='B-phải',dots=3,visible=True)]
    add(m,2,'top_faces_occlusion_selection',
      'Có hai khối vuông A,B. B đặt ngay trên A, che kín toàn bộ mặt trên của A; mặt trên của B không bị che. Theo góc nhìn trước-phải, bảng ghi: A trước6chấm,phải4chấm,trên1chấm nhưng mặt trên A bị B che; B trước2chấm,phải3chấm,trên5chấm. Hỏi tổng chấm trên những mặt TRÊN NHÌN THẤY, không phải mọi mặt được nêu số. Không cộng mặt trước/phải và không coi biết số mặt khuất là đang nhìn thấy nó.',
      'Chọn mặt trên đồng thời nhìn thấy',
      [st('Lọc theo hướng trước','Chỉ các mặt được gọi là trên mới là ứng viên.','Trên A ghi1; trên B ghi5','Các số6,4,2,3 ở mặt trước/phải không được đưa vào tổng này.'),
       st('Lọc tiếp theo bị che hay không','Đã biết một số không có nghĩa mặt đó đang nhìn thấy.','Chỉ mặt trên B được tính','Mặt trên A nằm dưới B và bị che kín; mặt trên B không bị che nên thỏa đồng thời hai điều kiện.'),
       st('Tổng và kiểm điều kiện kép','Không cộng1của A vì sai điều kiện nhìn thấy.','5','Tổng chỉ có5chấm của mặt trên B. Cộng1+5 sẽ là tổng hai mặt trên có dữ kiện, khác tổng mặt trên nhìn thấy được hỏi.','5','chấm')],
      [('Mặt được tính','Mặt trên B',''),('Tổng','5','chấm')],
      ['Lọc mặt theo hướng rồi xét riêng tình trạng che khuất được đề mô tả.','Không coi mọi số trong bảng là đều thuộc tổng cần tìm.','Kiểm từng mặt được cộng có thỏa cả hai điều kiện cùng lúc không.'],
      dict(kind='faces',faces=faces3,asked_directions=['trên']),dict(labels=['B'],sum=5),
      'G2 explicit top-face visibility with occlusion and side-face exclusion; no claim of actual publisher image understanding.',
      candidates=['g2v1:solid_visible_face_directions'],scope='G2 explicit table visibility/occlusion branch only, inherited external G2 page binding retained separately; no image certification.')
    return rows

def main():
    OUT.mkdir(parents=True,exist_ok=True);rows=build();assert len(rows)==24
    asset_spec=importlib.util.spec_from_file_location('geometry_assets',OUT/'original_assets.py');A=importlib.util.module_from_spec(asset_spec);asset_spec.loader.exec_module(A)
    for r in rows:
        r['original_question_assets']=[A.create(r,OUT)]
    spec=importlib.util.spec_from_file_location('independent_geometry',OUT/'independent_geometry_oracle.py');O=importlib.util.module_from_spec(spec);spec.loader.exec_module(O)
    chats=[];qa=[];proofs=[];numeric=[];mutations=[]
    for r in rows:
        h=sha(dumps(r).encode());result=O.check(r)
        proofs.append(dict(sample_id=r['sample_id'],source_row_sha256=h,result=result,status='PASS_INDEPENDENT_COMPLETE_FINITE_ORACLE'))
        for s in r['worked_steps']:
            if s['expression']:
                f=calc(s['expression'],Fraction);assert f==Fraction(s['result'])
                with localcontext() as ctx:
                    ctx.prec=90;d=calc(s['expression'],Decimal);assert abs(d-Decimal(f.numerator)/Decimal(f.denominator))<Decimal('1e-70')
                numeric.append(dict(sample_id=r['sample_id'],source_row_sha256=h,step_id=s['step_id'],expression=s['expression'],fraction=str(f),decimal_agrees=True))
        # Each mutated expectation must be rejected by the exact model, independent of prose/token gates.
        bad=copy.deepcopy(r);key=next(iter(bad['independent_expected']));v=bad['independent_expected'][key]
        bad['independent_expected'][key]=v+['WRONG'] if isinstance(v,list) else v+1 if isinstance(v,int) else str(v)+'_WRONG'
        try:O.check(bad)
        except AssertionError:pass
        else:raise AssertionError('mutation not rejected')
        mutations.append(dict(sample_id=r['sample_id'],source_row_sha256=h,changed_expected_field=key,rejected=True))
        bad=copy.deepcopy(r);bm=bad['independent_model'];kind=bm['kind'];change=''
        if kind=='boundary':
            bm['fixed'].append(next(p for p in bm['whole'] if p not in bm['fixed']));change='fixed piece now covers one required complementary cell'
        elif kind in ('squares','quads'):
            if 'EF' in bm['edges'] and kind=='squares':bm['edges'].remove('EF')
            elif kind=='squares':bm['edges'].append('EF')
            elif 'AB' in bm['edges']:bm['edges'].remove('AB')
            else:bm['edges'].append('AB')
            change='one real boundary removed/restored; stale inventory must fail'
        elif kind=='pair_assembly':
            bm['target_size']=[2,2] if bm['target_size']==[4,1] else [4,1];change='equal-area target changes shape; stale feasibility must fail'
        elif kind=='partition':
            bm['pieces'][-1]=copy.deepcopy(bm['pieces'][-2]);change='one piece duplicated in place of another, creating interior overlap and gap'
        elif kind=='triangle_remove':bm['remove']=[];change='claimed removed stick is actually retained'
        elif kind=='rhombus_move':bm['budget']=2;change='only two physical moves allowed, cannot fill three required slots'
        elif kind=='unit_cells':bm['full'].append(bm['full'][0]);change='one full cell identity counted twice'
        elif kind=='seven_build':bm['count']=3;change='physical stock reduced to three sticks'
        elif kind=='seven':bm['budget']=0;change='exact physical move budget changed to zero'
        elif kind=='faces':bm['asked_directions']=['trước'];change='direction selection changed, old labels/sum invalid'
        try:O.check(bad)
        except AssertionError:pass
        else:raise AssertionError(('model mutation not rejected',r['sample_id']))
        mutations.append(dict(sample_id=r['sample_id'],source_row_sha256=h,changed_model_condition=change,rejected=True))
        qa.append(dict(sample_id=r['sample_id'],source_row_sha256=h,status='PASS_AUTHOR_SEMANTIC_SELF_QA_ROOT_CROSS_REVIEW_PENDING',actual_fields_read=['problem','givens','requested_quantity','student_work','worked_steps','expected_answer','initial_guidance','hints'],criteria={k:'PASS' for k in ['problem_givens_request_consistency','independent_exact_math_and_finite_completeness','steps_operation_reasons_units_and_checks','grade_original_representation_and_scope','all_initial_three_hints_no_answer_or_final_label','feedback_grounded_and_no_unseen_assets','provenance_hash_and_preservation']},semantic_note=r['nearest_source_comparison']['semantic_difference'],human_review_claimed=False))
        for c in chat_records(r):
            c.update(source_row_sha256=h,quality_status=r['quality_status'],acceptance_status=r['acceptance_status']);L.validate_chat(c);chats.append(c)
    priorfiles=[HERE/'cloud_publication/sgk_page_audit_20261019/current_sources.jsonl']
    priorfiles+=list((HERE/'cloud_publication').glob('sgk_*/release/accepted_cases.jsonl'))
    oldids=set();oldq=set();pins=[];norm=lambda x:re.sub(r'\s+',' ',x).strip().casefold()
    for p in priorfiles:
        bs=p.read_bytes();pins.append(dict(file=str(p.relative_to(HERE)),sha256=sha(bs)))
        for b in bs.splitlines():
            v=json.loads(b)
            if v.get('split')!='train' or v.get('source_role')=='EVAL' or re.search(r'holdout|eval|pilot|protected',v['sample_id'],re.I):continue
            oldids.add(v['sample_id']);oldq.add(norm(v['problem']))
    assert not oldids&{r['sample_id'] for r in rows}
    assert not oldq&{norm(r['problem']) for r in rows}
    assert len({r['sample_id'] for r in rows})==24 and len({norm(r['problem']) for r in rows})==24
    for n,rs in [('cases.jsonl',rows),('chat.jsonl',chats),('selfqa7.jsonl',qa),('independent_oracles.jsonl',proofs),('numeric_fraction_decimal.jsonl',numeric),('adversarial_mutations.jsonl',mutations)]:jl(n,rs)
    from math_data_archive_audit import source_projection,linkage_errors
    byid={r['sample_id']:(r,sha(b)) for b in (OUT/'cases.jsonl').read_bytes().splitlines() for r in [json.loads(b)]}
    for b in (OUT/'chat.jsonl').read_bytes().splitlines():
        c=json.loads(b);r,h=byid[c['source_sample_id']];assert c['source_row_sha256']==h and not linkage_errors(c,source_projection(r))
    coverage=[]
    for master in sorted({r['coverage']['finite_master_id'] for r in rows}):
        selected=[r for r in rows if r['coverage']['finite_master_id']==master]
        coverage.append(dict(master_id=master,accepted=False,status='DRAFT_CROSS_REVIEW_PENDING',case_ids=[r['sample_id'] for r in selected],grade_branches=[dict(grade=r['grade'],branch=r['topic'],candidate_ids=r['coverage']['candidate_ids']) for r in selected],remaining='Actual publisher-image/physical competence not claimed. Grade and exact candidate branches only as listed; no blanket closure.'))
    write('coverage_matrix.json',dict(masters=coverage,core_added=0,global_complete_claimed=False))
    files=['cases.jsonl','chat.jsonl','selfqa7.jsonl','independent_oracles.jsonl','numeric_fraction_decimal.jsonl','adversarial_mutations.jsonl','coverage_matrix.json','candidate_snapshot.json','assignment_snapshot.json','nearest_actual_fullfields.jsonl','independent_geometry_oracle.py','original_assets.py']+[str(p.relative_to(OUT)).replace('\\','/') for p in sorted((OUT/'assets').glob('*.svg'))]
    write('manifest.json',dict(cases=24,chats=96,masters=10,grades=dict(Counter(str(r['grade']) for r in rows)),numeric_steps=len(numeric),independent_oracles=24,mutation_rejections=len(mutations),nearest_actual_rows=len((OUT/'nearest_actual_fullfields.jsonl').read_bytes().splitlines()),prior_rows=len(oldids),prior_preservation=pins,files=[dict(path=n,sha256=sha((OUT/n).read_bytes()),bytes=(OUT/n).stat().st_size) for n in files],status='AUTHOR_SELF_QA_PASSED_ROOT_REVIEW_PENDING',training_started=False,drive_mutated=False))
    receipt=dict(cases=24,chats=96,source_sha256=sha((OUT/'cases.jsonl').read_bytes()),chat_sha256=sha((OUT/'chat.jsonl').read_bytes()),source_chat_rawhash_linkage_all=True,numeric_steps=len(numeric),independent_oracles=24,mutation_rejections=len(mutations),no_duplicate_prior_ids_or_problem=True,prior_sources_unchanged=all(sha((HERE/p['file']).read_bytes())==p['sha256'] for p in pins),training_started=False,drive_mutated=False)
    write('validation_receipt.json',receipt);print(dumps(receipt))
if __name__=='__main__':main()

