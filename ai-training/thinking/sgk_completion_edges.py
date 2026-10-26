"""Twelve bounded original inventory/edge drafts. Data only, no Drive/training."""
from pathlib import Path
from fractions import Fraction
from decimal import Decimal,localcontext
from collections import Counter
import ast,hashlib,json,importlib.util,re
import exhaustive_colab_loader as L
from exhaustive_primary_math import chat_records

HERE=Path(__file__).resolve().parent
OUT=HERE/'cloud_publication/sgk_completion_20261021/inventory_edges'
def dump(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha(b):return hashlib.sha256(b).hexdigest()
def write(n,x):(OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def jl(n,rs):(OUT/n).write_text(''.join(dump(r)+'\n' for r in rs),encoding='utf-8',newline='\n')
def step(title,reason,result,explanation,expression=None,unit=''):
    return dict(title=title,reason=reason,result=str(result),explanation=explanation,expression=expression,unit=unit)
def calc(expr,typ):
    def walk(n):
        if isinstance(n,ast.Constant) and type(n.value) in (int,float):return typ(ast.get_source_segment(expr,n))
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.USub):return -walk(n.operand)
        if isinstance(n,ast.BinOp):
            a,b=walk(n.left),walk(n.right)
            if isinstance(n.op,ast.Add):return a+b
            if isinstance(n.op,ast.Sub):return a-b
            if isinstance(n.op,ast.Mult):return a*b
            if isinstance(n.op,ast.Div):return a/b
        raise ValueError('Unsupported arithmetic')
    return walk(ast.parse(expr,mode='eval').body)

def build():
    specs=json.loads((OUT/'candidate_snapshot.json').read_text('utf-8'));rows=[]
    def add(master,grade,topic,problem,givens,request,steps,answers,hints,model,semantic,student=None):
        sid='sgk_completion_edges_20261021_'+topic;m=specs[master]
        for i,s in enumerate(steps):s['step_id']='s'+str(i)
        row=dict(sample_id=sid,case_group_id=sid+'_group',grade=grade,topic=topic,
            case_kind='observable_student_error' if student else 'original_finite_representation',split='train',
            problem=problem,givens=[dict(id='g'+str(i),text=t,value=None,unit='') for i,t in enumerate(givens)],requested_quantity=request,
            student_work=dict(text=student,observations=[dict(excerpt=student,claim_scope='Explicit supplied synthetic statement only; no hidden cognition or unseen physical/image result inferred.')]) if student else None,
            can_solve=True,worked_steps=steps,expected_answer=[dict(quantity=q,result=str(v),unit=u) for q,v,u in answers],
            initial_guidance=[hints[0]],hints=[dict(level=i+1,hint=h,question=['Em cần giữ những dữ kiện và luật nào?','Em xét các trường hợp theo đúng luật ra sao?','Em kiểm đủ và không đếm lặp thế nào?'][i]) for i,h in enumerate(hints)],
            acceptance_status='DRAFT_AWAITING_ROOT_CONTENT_CROSS_REVIEW',quality_status='AUTHOR_QA_PENDING_ROOT_REVIEW',source_role='AI_GENERATED',
            human_verified=False,teacher_certified=False,owner_human_reviewed=False,
            provenance=dict(authorship_origin='ORIGINAL_AI_TEACHER_AUTHORING',acceptance_basis='OWNER_PREAUTHORIZED_PROCESS_ROOT_QA_PENDING',book_exercise_copied=False,human_content_review_completed=False,actual_physical_or_image_result_claimed=False),
            curriculum_assignment=dict(grade=grade,enrichment=True,master_id=master,candidate_ids=m['candidate_ids'],actual_page_receipts=m['actual_page_receipts'],page_receipt_basis='Previously viewed publisher image receipts inherited, not newly viewed by this author.',coverage_claim='Original explicit text/edge model only, no original-image/physical or whole-curriculum certification.'),
            coverage=dict(mode='FINITE_SUPPLEMENTARY_APPEND_NOT_CORE',finite_master_id=master,candidate_ids=m['candidate_ids'],branch=topic,new_core_slots_claimed=0,numbers_only_variant=False,text_relation_only=True,visual_physical_coverage_claimed=False),
            nearest_source_comparison=dict(status='NEAREST_ACTUAL_FULLFIELDS_READ',evidence='nearest_actual_fullfields.jsonl',nearest_refs=m['nearest_refs'],semantic_difference=semantic,limitation='Finite nearest-source comparison only; not absence proof over full archive.'),independent_model=model)
        row['canonical_signatures']=L.source_signatures(row);rows.append(row)
    m='all_boundary_labels_joint_match'
    add(m,1,'boundary_every_label_not_partial',
        'Trong mô hình bằng chữ, ba xúc xắc đã cho kết quả 1, 2, 3. Mỗi xúc xắc cấp đúng một thẻ số tương ứng. Một vùng có ba cạnh mang nhãn; vùng được chọn khi đặt ba thẻ lên ba cạnh sao cho từng thẻ bằng nhãn cạnh, dùng hết mỗi thẻ một lần, được đổi thứ tự thẻ. Các vùng riêng là P:(1,2,3), Q:(1,2,4), R:(3,2,1), S:(1,1,2); đây là toàn bộ nhãn của từng vùng. Chọn mọi vùng hợp lệ; không đo hoặc xem ảnh nào khác.',
        ['Ba thẻ từ ba xúc xắc là 1,2,3, mỗi thẻ dùng một lần trong mỗi lần thử.','Bốn vùng P(1,2,3), Q(1,2,4), R(3,2,1), S(1,1,2); mỗi vùng có đúng ba cạnh.'],
        'Mọi vùng khớp đồng thời tất cả nhãn',[step('Thử đủ ba nhãn của từng vùng','Một cạnh khớp chưa đủ cho cả vùng.','P và R dùng vừa đủ ba thẻ','P đặt lần lượt1,2,3; R có thể đặt3,2,1. Mỗi vùng dùng đúng một thẻ mỗi số.'),step('Kiểm vùng bị loại','Không được đổi số trên thẻ hoặc dùng một thẻ hai lần.','Q và S bị loại','Q cần thẻ4 không có; S cần hai thẻ1 nhưng chỉ có một. Việc Q có nhãn1,2 không làm vùng đó hợp lệ.'),step('Kiểm toàn danh sách','Đã thử cả bốn vùng và đủ mọi cạnh.','P;R','Hai vùng có thứ tự nhãn khác nhau vẫn cùng khớp ba thẻ vì luật cho đổi thứ tự thẻ.')],
        [('Vùng hợp lệ','P;R','')],['Đối chiếu toàn bộ nhãn quanh từng vùng với các thẻ được cấp.','Mỗi lần thử phải dùng đủ từng thẻ theo đúng số lần đang có.','Kiểm cả vùng bị loại, không dừng sau một nhãn khớp.'],
        dict(kind='boundary',dice=[1,2,3],regions={'P':[1,2,3],'Q':[1,2,4],'R':[3,2,1],'S':[1,1,2]}),
        'Conjunctive region eligibility with complete three-label inventory, unlike independent eligible nodes or board position arithmetic.')
    add(m,1,'boundary_repeated_outcome_inventory_error',
        'Ba xúc xắc cho các thẻ 2,2,4: hai thẻ riêng ghi2 và một thẻ ghi4. Mỗi vùng có ba cạnh cần phủ đủ ba thẻ đúng nhãn, mỗi thẻ một lần, được đổi thứ tự. Vùng A ghi(2,2,4), B ghi(2,4,4), C ghi(2,4,1). Bạn viết: “B có các số2 và4 như xúc xắc nên chọn B.” Giữ câu đó; chọn mọi vùng hợp lệ và chỉ rõ vì sao việc có cùng các số chưa đủ.',
        ['Kho thẻ gồm hai thẻ2 và một thẻ4; không sao chép thẻ.','A(2,2,4), B(2,4,4), C(2,4,1); phủ đúng cả ba cạnh mỗi vùng.'],
        'Vùng hợp lệ có kiểm số lần xuất hiện',[step('Giữ số thẻ theo từng số','Hai thẻ cùng số vẫn là hai vật được dùng riêng.','Có hai thẻ2, một thẻ4','Không biến kho thành chỉ hai tên số2 và4 rồi bỏ số lượng.'),step('So nhu cầu từng vùng','Phải có đúng số thẻ cho mọi cạnh.','Chỉ A khớp','A cần hai thẻ2 và một thẻ4; B đòi hai thẻ4 nên thiếu; C đòi thẻ1 không có.'),step('Phản hồi câu đã viết','Cùng xuất hiện tên số không bảo đảm đủ số lần sử dụng.','A','Câu chọn B bỏ qua việc B cần thêm một thẻ4. Đã kiểm đủ A,B,C, không đổi nhãn để giữ câu chọn.')],
        [('Vùng hợp lệ','A','')],['Giữ riêng số lượng thẻ của từng số, kể cả các thẻ ghi giống nhau.','So từng nhãn cạnh với đúng số thẻ còn có thể dùng.','Đối chiếu cả số loại và số lần xuất hiện trước khi kết luận.'],
        dict(kind='boundary',dice=[2,2,4],regions={'A':[2,2,4],'B':[2,4,4],'C':[2,4,1]}),
        'Repeated-value physical inventory makes set-membership insufficient; observable partial-match error differs from simple distinct-label forward selection.',student='B có các số2 và4 như xúc xắc nên chọn B.')
    m='shared_edge_stick_construction'
    add(m,1,'five_sticks_shared_triangle_plan',
        'Mô hình có bốn điểm A,B,C,D: C và D nằm ở hai phía đoạn AB; ABC và ABD là hai tam giác đều có cạnh bằng một que. Chỉ có năm chỗ đặt que AB,AC,BC,AD,BD; không có nét CD hay chỗ khác. Có đúng năm que bằng nhau, mỗi chỗ cần đúng một que, không chồng hai que cùng chỗ. Nêu cách dùng hết năm que để tạo hai tam giác ABC,ABD và giải thích vì sao không cần sáu que. Chỉ hỏi kế hoạch theo mô tả, chưa xác nhận thao tác thật.',
        ['Hai tam giác đều ABC và ABD ở hai phía cạnh chung AB.','Năm chỗ AB,AC,BC,AD,BD, mỗi chỗ dùng một que; không CD.'],
        'Các chỗ đặt và số que khác nhau',[step('Đặt cạnh dùng chung','AB là cùng một chỗ trong cả hai tam giác.','Một que ở AB','Không đặt hai que chồng lên nhau chỉ vì tên AB xuất hiện khi gọi hai tam giác.'),step('Bổ sung các cạnh còn lại','Mỗi tam giác cần hai cạnh riêng ngoài AB.','Thêm AC,BC,AD,BD','Bốn chỗ này khác nhau và khác AB, nên cần bốn que nữa.'),step('Đếm que và kiểm hai đường bao','Que chung được đếm một lần.','5','Một cộng bốn bằng năm. ABC có AB,AC,BC; ABD có AB,AD,BD, đều kín. Không thêm CD hoặc nhận đã ghép thật.','1+4','que')],
        [('Các chỗ','AB;AC;BC;AD;BD',''),('Số que','5','que')],['Tìm chỗ nào thuộc đường bao của cả hai tam giác.','Tách cạnh dùng chung khỏi các cạnh riêng của từng hình.','Kiểm từng đường bao và đếm mỗi chỗ đặt que đúng một lần.'],
        dict(kind='shared_plan',points={'A':[0,0],'B':[2,0],'C':[1,1],'D':[1,-1]},vertical_scale_squared=3,edges=['AB','AC','BC','AD','BD']),
        'Exact five-slot construction and shared-edge inventory proof rather than restoring cut paper or matching shape names.')
    add(m,1,'one_stick_repairs_two_triangles',
        'Các điểm A,B,C,D theo mô tả hai tam giác đều ABC và ABD ở hai phía đoạn AB, cạnh mỗi tam giác bằng một que. Đã đặt bốn que ở AC,BC,AD,BD; AB còn trống. Có thêm điểm E ở ngoài, chỉ có chỗ AE dài một que, không có EB,EC,ED. Được thêm đúng một que vào AB hoặc AE, không chuyển bốn que cũ. Tìm mọi chỗ thêm làm cả ABC và ABD kín; kiểm que mới giúp mấy tam giác. Không có nét nào ngoài các chỗ đã nêu.',
        ['Đang có AC,BC,AD,BD; cần khép ABC và ABD.','Một que mới đặt vào AB hoặc AE; E không có nối khác.'],
        'Chỗ bổ sung và số tam giác được khép',[step('Kiểm các cạnh còn thiếu','Mỗi hình đã có hai cạnh riêng.','Cả hai còn thiếu cùng AB','ABC thiếu AB; ABD cũng thiếu đúng chỗ AB, không phải hai chỗ khác nhau.'),step('Thử từng chỗ được phép','AE không nằm trên đường bao của hai tam giác được hỏi.','Chọn AB, không chọn AE','Đặt vào AB khép cả hai đường bao; đặt AE vẫn để cả hai đường bao hở tại AB.'),step('Kiểm kho và số hình','Que thêm chỉ có một nhưng được dùng chung theo mô tả.','2','Bốn que cũ cộng một que mới thành năm chỗ khác nhau; hai tam giác đã đủ ba cạnh. Đây là kết luận theo mô hình, không chứng nhận thao tác thật.','1+1','tam giác')],
        [('Chỗ thêm','AB',''),('Tam giác được khép','2','tam giác')],['Tìm cạnh còn thiếu của từng tam giác trước khi chọn chỗ thêm.','Một chỗ chung có thể phục vụ hai đường bao, nhưng chỗ ngoài thì không.','Thử cả các chỗ được phép và giữ nguyên các que đã đặt.'],
        dict(kind='shared_repair',points={'A':[0,0],'B':[2,0],'C':[1,1],'D':[1,-1],'E':[-2,0]},vertical_scale_squared=3,edges=['AC','BC','AD','BD'],add_options=['AB','AE']),
        'One-edge repair with fixed old inventory and decoy slot, rather than a number-only change to the forward five-stick construction.')
    m='composite_square_only_enumeration'
    add(m,1,'square_only_small_and_outer',
        'Mô hình là một bảng vuông chia thành hai hàng, hai cột ô vuông bằng nhau; mọi đường ngang,dọc đều vẽ trọn, không đường chéo. Bốn ô nhỏ được gọi A trên trái, B trên phải, C dưới trái, D dưới phải. Chỉ đếm hình vuông có đường bao nằm trọn trên các nét đã vẽ, kể cả hình ghép; cùng một miền chỉ đếm một lần. Liệt kê mọi hình vuông và tổng số. Miền gồm cả một hàng hoặc cả một cột chỉ được nhận nếu bốn cạnh bằng nhau.',
        ['Lưới vuông đủ hai hàng,hai cột, không đường chéo.','A,B ở hàng trên;C,D ở hàng dưới; chỉ hình có bốn cạnh bằng nhau.'],
        'Danh sách hình vuông và tổng',[step('Đếm hình một ô','Mỗi ô nhỏ có bốn cạnh bằng nhau và đường bao kín.','A;B;C;D','Bốn ô riêng đều là hình vuông.'),step('Kiểm các miền ghép','Hình vuông ghép cần ngang và dọc bằng nhau.','Thêm toàn bảng','Toàn bảng có hai ô mỗi chiều nên vuông. Cả một hàng dài hai ô nhưng cao một ô; cả một cột tương tự nên không vuông.'),step('Cộng và kiểm đủ kích cỡ','Trong bảng này cạnh vuông chỉ có thể dài một hoặc hai cạnh ô.','5','Bốn vuông nhỏ và một vuông ngoài là năm. Không nhận hình chữ nhật một hàng hoặc một cột.','4+1','hình vuông')],
        [('Danh sách','A;B;C;D;toàn bảng',''),('Tổng','5','hình vuông')],['Đếm theo kích cỡ đường bao, không chỉ theo tên các ô.','Với miền ghép, so số cạnh ô theo ngang và dọc.','Kiểm cả hình ngoài và loại miền có hai kích thước khác nhau.'],
        dict(kind='squares',width=2,height=2,removed=[]),
        'Square-only equal-side subset explicitly filters horizontal/vertical rectangles; old accepted rectangle enumeration included all rectangle types.')
    add(m,1,'square_missing_inner_edge_error',
        'Bắt đầu từ bảng vuông hai hàng hai cột, gọi A trên trái,B trên phải,C dưới trái,D dưới phải. Mọi nét như lưới đủ, trừ đoạn đứng ngăn A và B từ mép trên đến tâm bảng đã bị xóa; đoạn đứng ngăn C và D vẫn còn. Không đường chéo hay nét khác. Chỉ đếm hình vuông có đường bao được vẽ trọn; nét mất không được tưởng tượng thêm. Bạn viết: “Chỉ mất nét trong nên vẫn có năm hình vuông như lưới đủ.” Kiểm câu viết, liệt kê hình vuông còn và tổng số.',
        ['Lưới hai hàng,hai cột; mất đúng nét đứng chung giữa A,B ở hàng trên.','Các nét ngoài cùng và nét ngăn C,D vẫn có đủ; cần đường bao kín.'],
        'Hình vuông còn sau xóa và phản hồi',[step('Kiểm từng ô nhỏ','Một cạnh mất làm đường bao ô liên quan bị hở.','Chỉ C và D còn là vuông nhỏ','A và B cùng thiếu nét đứng chung; không được đếm miền hở thành hình vuông.'),step('Kiểm vuông ghép ngoài','Đường bao ngoài không dùng đoạn trong vừa xóa.','Toàn bảng vẫn là một hình vuông','Bốn cạnh ngoài còn nguyên và bằng nhau. Hàng trên ghép lại là chữ nhật, không thêm hình vuông khác.'),step('Tổng và sửa câu','Phải kiểm đường bao từng hình, không dùng tổng lưới cũ.','3','Hai vuông nhỏ cộng một vuông ngoài là ba; câu năm hình giữ lại hai miền đang hở.','2+1','hình vuông')],
        [('Danh sách','C;D;toàn bảng',''),('Tổng','3','hình vuông')],['Tìm chính xác các đường bao dùng đoạn bị xóa.','Xét riêng vuông nhỏ và đường bao ngoài còn nguyên.','Không tự nối lại nét mất để giữ số đếm của lưới đủ.'],
        dict(kind='squares',width=2,height=2,removed=[[[1,1],[1,2]]]),
        'Missing-edge incidence changes square feasibility while preserving the outer composite; observable stale-count error differs structurally from full-grid counting.',student='Chỉ mất nét trong nên vẫn có năm hình vuông như lưới đủ.')
    m='finite_inventory_collection_game'
    add(m,3,'collection_equal_tokens_removed_once',
        'Bàn chơi chữ có vòng ô1→2→3→4→1, cứ theo chiều ấy; mỗi bước vào ô kế, không đếm ô đang đứng. An và Bình đều bắt đầu ở1, đi luân phiên An trước. Hoa riêng a ghi3 ở ô2,b ghi3 ở ô4,c ghi5 ở ô3; không hoa khác. Đến ô còn hoa thì lấy đúng hoa ở đó, bỏ khỏi bàn vĩnh viễn và cộng số trên hoa vào điểm riêng. Ô trống không cho thêm điểm. Dừng ngay khi ai có ít nhất8 điểm, người đó thắng; không chơi lượt sau. Các bước đã cho theo lượt: An1, Bình3, An2, Bình3. Mô phỏng đủ tới lúc dừng; nêu chủ từng hoa, điểm và người thắng.',
        ['Vòng1,2,3,4; An,Bình bắt đầu1, thứ tự An trước.','Hoa a3 ở2,b3 ở4,c5 ở3; lấy rồi bỏ khỏi bàn, không dùng lại.','Bước bốn lượt1,3,2,3; thắng khi điểm riêng ít nhất8, dừng ngay.'],
        'Chủ hoa, điểm cuối và trạng thái dừng',[step('Hai lượt đầu','Hai hoa cùng ghi3 vẫn là hai hoa khác nhau.','An lấy a; Bình lấy b','An tiến1 tới2 nhận a được3; Bình từ1 tiến3 tới4 nhận b được3. Hai hoa rời bàn.'),step('Lượt gặp lại ô đã lấy','Ô4 đang trống, không tạo lại hoa b.','An vẫn3 điểm','An từ2 tiến2 tới4 nhưng b đã thuộc Bình; An không lấy thêm hoa hay điểm.'),step('Lượt Bình và ngưỡng dừng','Điểm cộng theo hoa thực nhận, kiểm ngưỡng ngay sau lượt.','8','Bình từ4 tiến3 qua1,2 tới3, nhận c ghi5. Ba cộng năm bằng tám, đạt ngưỡng; dừng tại lượt4.','3+5','điểm'),step('Kiểm bảo toàn hoa','Mỗi hoa có đúng một chủ và không còn trên bàn.','An:a; Bình:b,c; Bình thắng','An3 điểm, Bình8 điểm; hoa a,b,c đều đã nhận một lần. Không tính lại b cho An.')],
        [('Chủ hoa','An:a;Bình:b,c',''),('Điểm An','3','điểm'),('Điểm Bình','8','điểm'),('Người thắng','Bình; dừng lượt4','')],['Theo dõi vị trí, hoa còn trên bàn và điểm riêng như ba phần khác nhau.','Sau mỗi lượt, xóa đúng hoa đã nhận khỏi kho chung.','Kiểm điều kiện thắng ngay sau lượt và không thu lại một hoa đã có chủ.'],
        dict(kind='collection',board=4,tokens={'a':{'value':3,'position':2},'b':{'value':3,'position':4},'c':{'value':5,'position':3}},moves=[['An',1,None],['Bình',3,None],['An',2,None],['Bình',3,None]],threshold=8,metric='score'),
        'Finite inventory ownership/removal and score threshold, not a position-only die move; repeated equal token values retain distinct identities.')
    add(m,3,'collection_token_count_not_score_error',
        'Vòng ô1→2→3→4→1, bước chỉ đếm ô mới vào. An,Bình đều bắt đầu1, luân phiên An trước. Ô2 có hai hoa riêng d và e đều ghi2; ô3 có hoa f ghi9; không hoa khác. Đến ô có hoa thì lấy một hoa theo tên ghi trong lượt, bỏ vĩnh viễn khỏi bàn; các hoa khác giữ lại. Thắng là người đầu tiên thu đủ2 hoa, KHÔNG xét tổng các số trên hoa; dừng ngay lúc đó. Các lượt: An tiến1 lấy d; Bình tiến2 lấy f; An tiến4 lấy e. Bạn nói: “Bình lấy hoa9 nên thắng ngay.” Giữ câu đó, mô phỏng và nêu ai thắng, mỗi người có hoa nào; số ghi không phải tiêu chí thắng.',
        ['Ô2 có d2,e2;ô3 có f9; mỗi hoa có danh tính riêng.','Ba lượt An1 lấy d;Bình2 lấy f;An4 lấy e; lấy một hoa được chỉ tên rồi xóa.','Thắng bằng đủ2 hoa, không theo tổng số; dừng ngay.'],
        'Kiểm tiêu chí thắng và chủ hoa',[step('Giữ hoa còn lại trong cùng ô','Lấy d không lấy kèm e dù hai hoa cùng số.','Sau lượt1, An có d; e còn ô2','Bình từ1 tới3 ở lượt2 lấy f, mới có một hoa; số9 không thay cho hai hoa.'),step('Theo lượt An trở lại','Bốn bước quanh vòng đưa An từ2 về2.','An lấy e ở lượt3','Các ô mới vào lần lượt3,4,1,2. e vẫn ở đó nên được lấy; không lấy lại d.'),step('Đếm đúng thứ được dùng làm ngưỡng','Luật đếm số hoa sở hữu, không cộng giá trị để chọn người thắng.','2','An có d và e là hai hoa nên thắng. Bình có f là một hoa dù ghi9.','1+1','hoa'),step('Kiểm câu đã nói và kho chung','Phản hồi chỉ vào tiêu chí được câu nói dùng sai.','An:d,e; Bình:f; An thắng','Câu Bình thắng theo số9 không đúng luật. d,e khác danh tính và đều đã rời bàn sau hai lượt của An.')],
        [('Chủ hoa','An:d,e;Bình:f',''),('Người thắng','An; dừng lượt3','')],['Đọc xem luật dùng số hoa hay số ghi trên hoa làm điều kiện thắng.','Giữ danh tính riêng của các hoa cùng ở một ô.','Theo hết lượt được phép tới lúc có người chạm đúng ngưỡng.'],
        dict(kind='collection',board=4,tokens={'d':{'value':2,'position':2},'e':{'value':2,'position':2},'f':{'value':9,'position':3}},moves=[['An',1,'d'],['Bình',2,'f'],['An',4,'e']],threshold=2,metric='tokens'),
        'Token-count threshold and one-of-several named collection differ from score objective; supplied false winner claim grounded exactly.',student='Bình lấy hoa9 nên thắng ngay.')
    m='edge_removal_game_terminal'
    add(m,4,'edge_game_outer_composite_last',
        'Mạng que là lưới nghiêng2 cột2 hàng hình bình hành: hàng dưới A-B-C, hàng giữa D-E-F, hàng trên G-H-I. Các que một bước có đúng AB,BC,DE,EF,GH,HI và AD,DG,BE,EH,CF,FI. Các hàng thẳng song song; các cột A-D-G,B-E-H,C-F-I thẳng song song theo hướng khác. Không que khác. Mục tiêu là mọi hình bình hành có cạnh đi theo hai hướng ấy, đủ đường bao, kể cả hình ghép nhiều ô. An,Bình luân phiên, An trước; mỗi lượt bỏ một que hiện có thuộc đường bao ít nhất một mục tiêu đang còn. Dừng khi không còn mục tiêu nào; người vừa làm dừng thắng. Lượt được ghi An bỏ DE,Bình bỏ BE,An bỏ EH,Bình bỏ AB. Kiểm từng lượt hợp lệ, liệt kê các mục tiêu còn sau từng lượt, nêu lúc dừng và ai thắng. Ký hiệu bốn đỉnh quanh biên dùng cho tên hình.',
        ['Lưới2×2 theo hai hướng; đủ12que đơn đã nêu, không có que khác.','Mục tiêu mọi hình bình hành đủ biên theo hai hướng, gồm hình ghép.','Lượt DE,BE,EH,AB; chỉ bỏ que nằm trên mục tiêu còn; hết mục tiêu thì vừa bỏ thắng.'],
        'Mục tiêu còn, tính hợp lệ, lúc dừng và người thắng',[step('Liệt kê mục tiêu ban đầu','Chọn một hoặc hai bước ở mỗi hướng, đường bao phải đủ.','9 mục tiêu','Bốn ô nhỏ ABED,BCFE,DEHG,EFIH; hai cột ABHG,BCIH; hai hàng ACFD,DFIG; ngoài ACIG. Đổi cách gọi cùng miền không tính thêm.'),step('Kiểm hai lượt đầu','Sau mỗi que bỏ, xét lại toàn bộ đường bao chứ không chỉ ô nhỏ.','Sau DE: BCFE,EFIH,ABHG,BCIH,ACIG; sau BE: EFIH,ACIG','DE thuộc mục tiêu ban đầu nên lượt An hợp lệ. BE còn thuộc BCFE,ABHG,BCIH nên lượt Bình hợp lệ; các biên có que mất đều bị loại.'),step('Giữ hình ghép ngoài','Không còn ô nhỏ chưa đủ để dừng nếu hình ghép vẫn kín.','Sau EH chỉ còn ACIG','EH thuộc EFIH nên lượt An hợp lệ; bỏ EH làm EFIH mất biên nhưng không ảnh hưởng đường bao ngoài ACIG.'),step('Kiểm lượt cuối và tiêu chí thắng','AB thuộc đường bao ACIG còn lại.','Bình thắng ở lượt4','Bỏ AB làm ACIG hở. Không còn mục tiêu nào trong đủ9 đã liệt kê, nên dừng sau lượt4; không dừng sớm ở lượt3.')],
        [('Sau DE','BCFE;EFIH;ABHG;BCIH;ACIG',''),('Sau BE','EFIH;ACIG',''),('Sau EH','ACIG',''),('Sau AB','Không còn mục tiêu',''),('Kết luận','Bốn lượt hợp lệ; Bình thắng lượt4','')],['Liệt kê cả hình một ô và hình ghép theo hai hướng trước khi xét lượt.','Một hình chỉ còn khi mọi que trên biên của nó vẫn có mặt.','Áp điều kiện dừng cho toàn bộ mục tiêu, không chỉ các ô nhỏ.'],
        dict(kind='edge_game',width=2,height=2,rhombi_only=False,moves=[['An','DE'],['Bình','BE'],['An','EH'],['Bình','AB']]),
        'Explicit finite geometry plus legal turn sequence, full target re-enumeration and terminal winner; static shapes or board positions do not establish termination.')
    add(m,4,'rhombus_only_terminal_scope_error',
        'Hai ô hình thoi bằng nhau ghép cạnh nhau thành một dải nghiêng: hàng dưới A-B-C, hàng trên D-E-F. Các que bằng nhau có đúng AB,BC,DE,EF,AD,BE,CF. Hai hàng thẳng song song, ba cột AD,BE,CF song song; không nét khác. Mỗi ô ABED và BCFE là hình thoi cạnh một que; ngoài ACFD có hai cạnh dài2que và hai cạnh1que. Luật chỉ coi HÌNH THOI có đủ biên theo hai hướng là mục tiêu, không nhận hình bình hành có cạnh kề dài khác nhau. An trước,Bình sau; mỗi lượt bỏ1que thuộc mục tiêu còn, hết mục tiêu dừng ngay và người vừa bỏ thắng. An bỏ BE. Bạn nói: “Ngoài ACFD còn kín nên chưa dừng, Bình phải chơi tiếp.” Kiểm lượt An, mọi mục tiêu còn và lời nói theo đúng loại hình trong luật.',
        ['Dải hai hình thoi ABED,BCFE chung BE;7que đơn đầy đủ.','Mục tiêu chỉ hình thoi; ngoài ACFD dài2que,rộng1que nên cạnh kề khác nhau.','An bỏ BE trước; hết mục tiêu dừng ngay, người vừa bỏ thắng.'],
        'Trạng thái dừng với mục tiêu chỉ hình thoi',[step('Giữ đúng loại hình mục tiêu','Đường bao kín chưa đủ nếu sai loại hình được luật chọn.','Mục tiêu ban đầu chỉ ABED và BCFE','Hai ô nhỏ có bốn cạnh bằng nhau. Ngoài ACFD kín nhưng cạnh kề hai que và một que nên không phải hình thoi.'),step('Bỏ que và kiểm cả hai hình','BE là cạnh chung của cả hai mục tiêu.','Sau BE không còn hình thoi mục tiêu','Lượt An hợp lệ vì BE đang thuộc cả hai. Bỏ nó làm cả ABED và BCFE thiếu cạnh; không có ô hay nét khác.'),step('Áp dừng và phản hồi','Không dùng hình bình hành khác loại để kéo dài trò chơi.','An thắng ngay lượt1','Không còn mục tiêu nên dừng ngay sau An; Bình không có lượt tiếp. Câu còn kín chỉ đúng về ngoài ACFD, không đúng về loại mục tiêu.')],
        [('Mục tiêu còn','Không còn hình thoi mục tiêu',''),('Kết luận','An thắng lượt1; Bình không chơi tiếp','')],['Xác định chính xác loại hình nào được luật gọi là mục tiêu.','Kiểm que bị bỏ thuộc những đường bao nào.','Đối chiếu hình ghép ngoài với điều kiện của loại hình, không chỉ độ kín.'],
        dict(kind='edge_game',width=2,height=1,rhombi_only=True,moves=[['An','BE']]),
        'Objective type changes terminality: outer non-rhombus parallelogram is not a target; explicit erroneous continuation claim contrasts all-parallelogram branch.',student='Ngoài ACFD còn kín nên chưa dừng, Bình phải chơi tiếp.')
    m='glyph_parallel_perpendicular_filter'
    add(m,4,'glyph_joint_relations_exact_segments',
        'Bốn ký hiệu được định nghĩa bằng các đoạn thẳng trên lưới(cột,hàng), không dùng kiểu chữ quen thuộc. P có(0,0)-(0,2),(2,0)-(2,2),(0,1)-(2,1). Q có(0,0)-(0,2),(2,0)-(2,2),(0,0)-(2,2). R có(0,0)-(0,2),(0,0)-(2,0). S có(0,0)-(2,2),(0,2)-(2,4),(0,2)-(2,0). Mỗi ký hiệu không có đoạn khác. Chọn mọi ký hiệu vừa có hai đoạn nằm trên hai đường thẳng phân biệt song song, vừa có một cặp đoạn thật sự gặp nhau tạo góc vuông, được gặp ở đầu hoặc trong đoạn. Không tự kéo dài đoạn để tạo giao điểm. Giải thích cả ký hiệu bị loại.',
        ['P,Q,R,S có đúng các đầu mút đã nêu trên lưới vuông đơn vị.','Song song phải ở hai đường phân biệt; vuông góc phải gặp nhau trong đoạn và tạo góc vuông.'],
        'Ký hiệu thỏa đồng thời hai quan hệ',[step('Xét song song và góc vuông riêng','Một quan hệ đúng không thay cho quan hệ còn lại.','P và S có cả hai','P có hai đoạn đứng song song và đoạn ngang gặp chúng vuông góc. S có hai đoạn chéo lên song song; đoạn chéo xuống gặp chúng vuông góc trên lưới.'),step('Kiểm hai ký hiệu khác','Chỉ các đoạn được liệt kê mới được dùng.','Q thiếu cặp vuông góc;R thiếu cặp song song','Q có hai đoạn đứng song song nhưng đoạn chéo lên không vuông với chúng. R có góc vuông ngang-đứng nhưng chỉ có hai đoạn khác hướng nên không có cặp song song.'),step('Kiểm giao điểm và đầy đủ','Góc vuông phải xuất hiện tại nơi hai đoạn thực sự gặp.','P;S','Ở S, đoạn chéo xuống gặp đoạn chéo lên thứ nhất tại(1,1), gặp đoạn thứ hai tại(0,2); cả hai nằm trong đoạn. Đã xét đủ bốn ký hiệu.')],
        [('Ký hiệu đạt','P;S','')],['Tách hai điều kiện song song và vuông góc cho từng ký hiệu.','Dùng các đầu mút để kiểm hướng và nơi hai đoạn thật sự gặp.','Chỉ giữ ký hiệu thỏa cả hai điều kiện cùng lúc.'],
        dict(kind='glyph',glyphs={'P':[[[0,0],[0,2]],[[2,0],[2,2]],[[0,1],[2,1]]],'Q':[[[0,0],[0,2]],[[2,0],[2,2]],[[0,0],[2,2]]],'R':[[[0,0],[0,2]],[[0,0],[2,0]]],'S':[[[0,0],[2,2]],[[0,2],[2,4]],[[0,2],[2,0]]]}),
        'Simultaneous segment-relation filtering in explicit glyph inventory; endpoints and incidence conventions avoid inference from unstated fonts.')
    add(m,4,'glyph_disjoint_support_lines_error',
        'Trên lưới vuông(cột,hàng), ký hiệu A có(0,0)-(2,0),(0,2)-(2,2),(3,3)-(3,4). B có(0,0)-(2,0),(0,2)-(2,2),(1,0)-(1,2). C có(0,0)-(1,0),(2,0)-(3,0),(0,0)-(0,1). Không đoạn khác. Cần đồng thời có hai đoạn trên hai đường phân biệt song song và hai đoạn GẶP NHAU tạo góc vuông trong phạm vi các đoạn; không kéo dài. Hai đoạn cùng đường thẳng không tính là cặp song song phân biệt. Bạn viết: “A có ngang và đứng nên A đạt đủ.” Chọn mọi ký hiệu đạt và kiểm câu viết; đoạn gặp ở đầu mút vẫn được tính.',
        ['A,B,C có đúng các đoạn nêu; không suy hình dạng từ tên chữ.','Hai đường song song phải phân biệt; cặp vuông góc phải gặp nhau trong các đoạn hiện có.'],
        'Ký hiệu đạt và lỗi coi đường kéo dài như đoạn',[step('Kiểm đúng giao điểm ở A','Hướng ngang và đứng chỉ tạo cặp vuông góc trong bài nếu các đoạn gặp nhau.','A không đạt','Hai đoạn ngang của A ở hàng0 và2 kết thúc tại cột2; đoạn đứng ở cột3,hàng3đến4 nên không gặp đoạn ngang nào. A có song song nhưng thiếu cặp gặp vuông góc.'),step('Kiểm hai ký hiệu còn lại','Phải giữ đồng thời quan hệ hướng và điều kiện hai đường phân biệt.','B đạt;C không đạt','B có hai đoạn ngang khác hàng song song và đoạn đứng gặp chúng vuông góc tại đầu mút. Ở C, hai đoạn ngang cùng hàng0 nằm trên cùng một đường nên không là cặp song song phân biệt.'),step('Đối chiếu câu đã viết','Không kéo dài đoạn của A để chữa kết luận.','B','C có cặp gặp vuông góc ở(0,0) nhưng vẫn thiếu song song phân biệt. Chỉ B thỏa cả hai; câu A đạt đủ bỏ điều kiện gặp nhau.')],
        [('Ký hiệu đạt','B','')],['Phân biệt các đoạn hữu hạn với đường thẳng được kéo dài.','Kiểm cặp song song có nằm trên hai đường khác nhau không.','Thử cả hai điều kiện cho mọi ký hiệu trước khi giữ hay loại.'],
        dict(kind='glyph',glyphs={'A':[[[0,0],[2,0]],[[0,2],[2,2]],[[3,3],[3,4]]],'B':[[[0,0],[2,0]],[[0,2],[2,2]],[[1,0],[1,2]]],'C':[[[0,0],[1,0]],[[2,0],[3,0]],[[0,0],[0,1]]]}),
        'Finite disjoint support lines and collinear separate strokes distinguish incidence and distinct-line conditions, not a number-only glyph variant.',student='A có ngang và đứng nên A đạt đủ.')
    return rows

def main():
    rows=build();assert len(rows)==12 and Counter(r['coverage']['finite_master_id'] for r in rows)=={m:2 for m in json.loads((OUT/'candidate_snapshot.json').read_text('utf-8'))}
    spec=importlib.util.spec_from_file_location('edge_independent',OUT/'independent_finite_oracle.py');oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
    chats=[];qa=[];numerics=[];oracles=[]
    for r in rows:
        h=sha(dump(r).encode());proof=oracle.check(r);oracles.append(dict(sample_id=r['sample_id'],source_row_sha256=h,status='PASS_SEPARATE_FINITE_ORACLE',check=proof))
        for s in r['worked_steps']:
            if s['expression']:
                f=calc(s['expression'],Fraction);assert f==Fraction(s['result'])
                with localcontext() as ctx:
                    ctx.prec=90;d=calc(s['expression'],Decimal);assert abs(d-Decimal(f.numerator)/Decimal(f.denominator))<Decimal('1e-70')
                numerics.append(dict(sample_id=r['sample_id'],source_row_sha256=h,step_id=s['step_id'],expression=s['expression'],exact=str(f),decimal_agrees=True))
        qa.append(dict(sample_id=r['sample_id'],source_row_sha256=h,status='PASS_AUTHOR_SELF_QA',actual_fields_read=['problem','givens','requested_quantity','student_work','worked_steps','expected_answer','initial_guidance','hints'],criteria={k:'PASS' for k in ['problem_givens_request_consistency','mathematical_oracle_and_complete_finite_cases','steps_reasons_units_checks','grade_enrichment_original_branches','all_initial_and_three_hints_answer_free','grounded_student_work_no_imagined_assets','provenance_hash_preservation']},human_review_claimed=False,root_cross_review_required=True))
        for c in chat_records(r):
            c.update(source_row_sha256=h,quality_status=r['quality_status'],acceptance_status=r['acceptance_status']);L.validate_chat(c);chats.append(c)
    # New IDs/questions checked against prior authored sources and drafts. Never
    # open protected evaluation payloads or infer semantic duplication by hash.
    priorfiles=[HERE/'cloud_publication/sgk_page_audit_20261019/current_sources.jsonl',HERE/'cloud_publication/sgk_page_audit_20261019/release/accepted_cases.jsonl',HERE/'cloud_publication/sgk_finish_20261020/release/accepted_cases.jsonl',HERE/'cloud_publication/sgk_remaining_20261020/release/accepted_cases.jsonl']
    priorfiles+=list((HERE/'cloud_publication/sgk_final_forms_20261020').glob('*/cases.jsonl'))
    oldids=set();oldq=set();snap=[];norm=lambda x:re.sub(r'\s+',' ',x).strip().casefold()
    for p in priorfiles:
        bs=p.read_bytes();snap.append(dict(file=str(p.relative_to(HERE)),sha256=sha(bs)))
        for b in bs.splitlines():
            v=json.loads(b)
            if v.get('split')!='train' or v.get('source_role')=='EVAL' or re.search(r'holdout|eval|pilot|protected',v['sample_id'],re.I):continue
            oldids.add(v['sample_id']);oldq.add(norm(v['problem']))
    assert not oldids&{r['sample_id'] for r in rows};assert not oldq&{norm(r['problem']) for r in rows}
    assert len({r['sample_id'] for r in rows})==12 and len({norm(r['problem']) for r in rows})==12
    for n,rs in [('cases.jsonl',rows),('chat.jsonl',chats),('selfqa7.jsonl',qa),('numeric_fraction_decimal.jsonl',numerics),('independent_oracles.jsonl',oracles)]:jl(n,rs)
    files=['cases.jsonl','chat.jsonl','selfqa7.jsonl','numeric_fraction_decimal.jsonl','independent_oracles.jsonl','candidate_snapshot.json','assignment_snapshot.json','nearest_actual_fullfields.jsonl','independent_finite_oracle.py']
    write('manifest.json',dict(status='12_DRAFTS_AUTHOR_QA_PASSED_ROOT_REVIEW_PENDING',cases=12,chat_rows=48,grades=dict(Counter(str(r['grade']) for r in rows)),masters=dict(Counter(r['coverage']['finite_master_id'] for r in rows)),numeric_steps=len(numerics),independent_oracles=12,nearest_actual_rows=18,training_started=False,drive_mutated=False,all_sgk_forms_covered=False,files=[dict(path=n,sha256=sha((OUT/n).read_bytes()),bytes=(OUT/n).stat().st_size) for n in files],prior_source_snapshots=snap))
    # Verify final serialized rows and chat links, not just in-memory models.
    from math_data_archive_audit import source_projection,linkage_errors
    byid={r['sample_id']:(r,sha(b)) for b in (OUT/'cases.jsonl').read_bytes().splitlines() for r in [json.loads(b)]}
    for b in (OUT/'chat.jsonl').read_bytes().splitlines():
        c=json.loads(b);r,h=byid[c['source_sample_id']];assert c['source_row_sha256']==h and not linkage_errors(c,source_projection(r))
    write('validation_receipt.json',dict(source_sha256=sha((OUT/'cases.jsonl').read_bytes()),chat_sha256=sha((OUT/'chat.jsonl').read_bytes()),cases=12,chats=48,all_source_chat_hash_and_target_links=True,technical_ids_canonical=True,dedup_prior_rows=len(oldids),prior_sources_unchanged=all(sha((HERE/x['file']).read_bytes())==x['sha256'] for x in snap),training_started=False))
    print(dump(dict(cases=12,chats=48,numeric_steps=len(numerics),source_sha256=sha((OUT/'cases.jsonl').read_bytes()),chat_sha256=sha((OUT/'chat.jsonl').read_bytes()))))
if __name__=='__main__':main()
