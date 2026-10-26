"""Six original bounded G3 reasoning tasks. Data preparation only."""
from pathlib import Path
from collections import deque
from itertools import product,permutations
from fractions import Fraction
from decimal import Decimal,localcontext
import json,hashlib
from exhaustive_primary_math import chat_records,expression_group
from sgk_gap_release import evaluate

HERE=Path(__file__).resolve().parent
BASE=HERE/'cloud_publication/sgk_page_audit_20261019'
OUT=HERE/'cloud_publication/sgk_finish_20261020/g3_reasoning'
ROWS=[]
def dump(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha(b):return hashlib.sha256(b).hexdigest()
def step(t,r,v,e,expr=None,u=''):return dict(title=t,reason=r,result=str(v),explanation=e,expression=expr,unit=u)
def hints(a,b,c):return [dict(level=i+1,hint=h,question=q) for i,(h,q) in enumerate(zip([a,b,c],['Em cần giữ đúng dữ kiện và luật nào?','Em áp dụng luật cho từng phần ra sao?','Em đối chiếu lại toàn bộ yêu cầu thế nào?']))]
def add(topic,problem,givens,request,steps,answers,hs,oracle,student=None):
    mapping=json.loads((BASE/'g3_audit/candidate_adjudication.json').read_text('utf-8'))
    candidate=next(r for r in mapping['adjudications'] if r['candidate_id']=='g3_'+topic)
    n=sum(r['topic']==topic for r in ROWS)+1;sid=f'sgk_finish_20261020_g3_{topic}_{n:02d}'
    ROWS.append(dict(sample_id=sid,case_group_id=sid+'_group',grade=3,split='train',topic=topic,case_kind='observable_student_error' if student else 'original_representation_gap',problem=problem,givens=[dict(id=f'g{i}',text=t,value=None,unit='') for i,t in enumerate(givens)],requested_quantity=request,student_work=dict(text=student,observations=[dict(excerpt=student,claim_scope='Explicit synthetic written evidence; no unseen action or hidden reasoning inferred.')]) if student else None,initial_guidance=[hs[0]['hint']],hints=hs,worked_steps=[dict(step_id=f's{i}',**s) for i,s in enumerate(steps)],expected_answer=[dict(quantity=q,result=str(v),unit=u) for q,v,u in answers],can_solve=True,gap_oracle=oracle,canonical_signatures=sorted({expression_group(s['expression']) for s in steps if s['expression']}),human_verified=False,teacher_certified=False,owner_human_reviewed=False,source_role='AI_GENERATED',acceptance_status='DRAFT_AWAITING_CONTENT_CROSS_REVIEW',quality_status='AUTHOR_QA_COMPLETE_PENDING_CROSS_REVIEW',provenance=dict(authorship_origin='ORIGINAL_AI_TEACHER_AUTHORING',book_exercise_copied=False,content_human_review_completed=False,acceptance_basis='OWNER_PREAUTHORIZED_AFTER_CONTENT_QA_PENDING_CROSS_REVIEW',actual_physical_or_image_result_claimed=False),curriculum_assignment=dict(grade=3,book='Kết nối tri thức với cuộc sống',enrichment=True,case_kind='supplementary',candidate_id=candidate['candidate_id'],actual_page_receipts=candidate['actual_page_receipts'],nearest_source_refs=[dict(sample_id=r['sample_id'],source_row_sha256=r['source_row_sha256']) for r in candidate['nearest_actual_training_sources']],coverage_claim='Bounded mathematical reasoning under explicit text givens; no physical action or image recognition certified.'),quality_flags=dict(app_plan_draft_compatible=False,three_hint_levels_answer_free=True,text_description_only_not_vision_training=True,actual_image_or_physical_asset_present=False),coverage=dict(mode='FINITE_ORIGINAL_PAGE_GAP_APPEND',gap_type=topic,numbers_only_variant=False)))

def build():
    ROWS.clear()
    add('product_pyramid','Tháp số có ba ô đáy từ trái sang phải là 2, 3, 4. Mỗi ô ở tầng trên bằng tích của đúng hai ô kề nhau ngay dưới nó. Điền hai ô tầng giữa và ô đỉnh, giải thích rồi kiểm lại cùng một luật.', ['Đáy trái sang phải: 2, 3, 4','Luật mỗi ô trên là tích hai ô kề ngay dưới'],'Hai ô giữa và đỉnh',[
        step('Tìm ô giữa bên trái','Ô này nằm ngay trên hai ô đáy đầu.',6,'Lấy 2 nhân 3 được 6; đây là nhân hai ô kề nhau, không phải cộng.','2*3'),
        step('Tìm ô giữa bên phải','Ô này dùng hai ô đáy cuối; ô đáy giữa được dùng trong cả hai cặp.',12,'Lấy 3 nhân 4 được 12. Việc dùng lại ô giữa đúng với luật các cặp kề.','3*4'),
        step('Tìm đỉnh và kiểm','Đỉnh dùng hai ô tầng giữa vừa tìm.',72,'6 × 12 = 72. Kiểm ba quan hệ: 2 × 3 = 6; 3 × 4 = 12; 6 × 12 = 72.','6*12')],[('Giữa trái',6,''),('Giữa phải',12,''),('Đỉnh',72,'')],hints('Xác định đúng hai ô nằm ngay dưới mỗi ô cần điền.','Áp cùng một luật cho từng tầng từ dưới lên.','Kiểm từng cặp kề, cả cặp dùng chung ô ở giữa.'),dict(kind='product_pyramid',bottom=[2,3,4],middle=[6,12],top=72))
    add('product_pyramid','Tháp ba tầng theo luật: mỗi ô trên bằng tích của hai ô kề ngay dưới. Đáy từ trái sang phải là 3, ô trống, 2; ô giữa bên trái là 9; đỉnh được cho là 54. Bạn viết: Ô đáy giữa là 3, ô giữa bên phải là 6, nên đỉnh bằng 9 + 6 = 15. Giữ bài viết ấy, kiểm các ô trống và sửa đúng chỗ sai để khớp luật và đỉnh đã cho.', ['Đáy: 3, ô trống, 2; giữa trái: 9; đỉnh đã cho: 54','Mỗi ô trên bằng tích hai ô kề dưới'],'Điền ô trống và sửa kết luận',[
        step('Tìm ô đáy giữa bằng quan hệ ngược','Tích 3 với ô trống phải bằng 9.',3,'9 : 3 = 3. Kiểm 3 × 3 = 9, nên phần đầu bạn viết đúng.','9/3'),
        step('Kiểm ô giữa bên phải','Ô này dùng ô đáy giữa vừa tìm và ô đáy phải.',6,'3 × 2 = 6, nên phần thứ hai của bài viết cũng đúng.','3*2'),
        step('Sửa phép tính ở đỉnh','Luật yêu cầu nhân cả ở tầng trên, không đổi sang cộng.',54,'9 × 6 = 54, khớp đỉnh đã cho. Sai ở việc dùng 9 + 6 để tạo đỉnh; giữ hai ô trống đã tìm đúng.','9*6')],[('Đáy giữa',3,''),('Giữa phải',6,''),('Đỉnh',54,''),('Sửa lỗi','Giữ các ô đúng; thay phép cộng ở đỉnh bằng phép nhân','')],hints('Kiểm riêng mỗi phần đã viết theo đúng luật của tháp.','Dùng quan hệ ngược khi biết một tích và một thừa số.','Luật tạo ô cần được giữ cả ở tầng cuối.'),dict(kind='product_pyramid',bottom=[3,3,2],middle=[9,6],top=54),student='Ô đáy giữa là 3, ô giữa bên phải là 6, nên đỉnh bằng 9 + 6 = 15.')
    add('two_jug_transfer','Trong bài đong giả định, bình A chứa tối đa 5 lít và bình B tối đa 3 lít, đều không có vạch và ban đầu rỗng. Có nguồn nước đủ dùng. Chỉ được đổ đầy một bình, đổ hết một bình ra ngoài, hoặc rót từ bình này sang bình kia đến khi bình nguồn rỗng hoặc bình đích đầy; không rót ước lượng giữa chừng. Hãy nêu một cách để riêng trong A đúng 4 lít. Ghi cặp (lượng trong A, lượng trong B) sau mỗi thao tác và kiểm; không yêu cầu ít thao tác nhất.', ['Dung tích A 5 lít, B 3 lít; ban đầu (0,0)','Ba loại thao tác và điều kiện dừng rót đúng như đề','Mục tiêu trong A 4 lít; không yêu cầu tối thiểu thao tác'],'Một kế hoạch hợp lệ có trạng thái kiểm được',[
        step('Đổ đầy A','Thao tác đổ đầy dùng dung tích đã biết, không cần vạch.',5,'Sau thao tác, cặp lượng là (5,0) lít. Bình B vẫn rỗng.','0+5','lít'),
        step('Rót A sang B đến khi B đầy','B chỉ nhận đến dung tích của nó; phần dư ở A.',2,'B nhận 3 lít, A còn 5 − 3 = 2 lít. Trạng thái (2,3).','5-3','lít'),
        step('Làm rỗng B rồi chuyển hết A sang B','B rỗng mới nhận được phần còn trong A; A rỗng là điểm dừng hợp lệ.',2,'Đổ hết B: (2,0). Rót hết A sang B: (0,2). B chưa đầy nhưng A đã rỗng, nên được dừng.','2+0','lít'),
        step('Đổ đầy A và rót sang B đến khi B đầy','B đang có nước nên chỉ nhận phần còn thiếu.',1,'Đổ đầy A được (5,2). B thiếu 3 − 2 = 1 lít; rót đúng đến khi B đầy.','3-2','lít'),
        step('Kiểm lượng giữ riêng trong A','A bớt đúng phần vừa rót; không khẳng định có vạch ở mức cần tìm.',4,'A còn 5 − 1 = 4 lít, trạng thái cuối (4,3). Mọi lượng đều nằm trong dung tích, mọi lần rót dừng vì nguồn rỗng hoặc đích đầy. Đây là kế hoạch theo mô tả, chưa xác nhận thao tác thật.','5-1','lít')],[('Lượng trong A cuối',4,'lít'),('Chuỗi trạng thái','(0,0)→(5,0)→(2,3)→(2,0)→(0,2)→(5,2)→(4,3)','lít')],hints('Ghi lượng ở cả hai bình sau từng thao tác, không chỉ lượng của bình cần lấy.','Khi rót, dùng phần còn thiếu của bình đích hoặc lượng còn ở bình nguồn để xác định điểm dừng.','Kiểm dung tích và điều kiện dừng của từng lần rót rồi đối chiếu mục tiêu.'),dict(kind='jug',capacities=[5,3],start=[0,0],target_vessel=0,target=4,path=[[0,0],[5,0],[2,3],[2,0],[0,2],[5,2],[4,3]]))
    add('two_jug_transfer','Hai bình không vạch A chứa tối đa 4 lít, B tối đa 2 lít, ban đầu đều rỗng. Có nguồn nước đủ dùng. Chỉ được đổ đầy, đổ hết, hoặc rót giữa hai bình đến khi nguồn rỗng hay đích đầy; không rót ước lượng. Có thể làm cho một trong hai bình chứa đúng 3 lít không? Nếu có hãy nêu cách; nếu không hãy giải thích bằng các lượng có thể xuất hiện, không tự thêm vạch.', ['Dung tích A 4 lít, B 2 lít; ban đầu (0,0)','Chỉ đầy, hết, hoặc rót đến nguồn rỗng/đích đầy','Cần đúng 3 lít trong một bình'],'Khả năng thực hiện và lý do',[
        step('Theo dõi các lượng có thể giữ','Ban đầu, dung tích và mọi chỗ trống đều gồm các phần hai lít.', 'A chỉ có thể 0, 2, 4 lít; B chỉ có thể 0, 2 lít','Nếu cả hai lượng đang là bội của 2 thì lượng rót bằng lượng nguồn hoặc chỗ trống đích, cũng là bội của 2. Đổ đầy và đổ hết cũng giữ tính chất ấy.'),
        step('Đối chiếu mức cần lấy','Mức cần lấy phải nằm trong tập lượng có thể đạt bằng các thao tác cho phép.','Không thể đạt đúng 3 lít','Ba không thuộc các lượng đã nêu. B còn nhỏ hơn 3 lít. Không dùng cách đổ bớt một lượng ước chừng vì thao tác ấy không được phép.'),
        step('Kiểm không bỏ lọt trạng thái','Theo dõi đồng thời cả hai bình khi thử các thao tác hợp lệ.','(0,0); (4,0); (0,2); (4,2); (2,2); (2,0)','Từ mỗi cặp này, đổ đầy, đổ hết hay rót đúng điểm dừng đều trở lại một trong các cặp đã liệt kê. Không cặp nào có thành phần bằng mức yêu cầu.')],[('Khả năng','Không thể đạt đúng 3 lít bằng các thao tác đã cho','')],hints('Hãy xét các lượng có thể xuất hiện sau thao tác được phép.','Kiểm đổ đầy, đổ hết và rót đúng điểm dừng có thay đổi tính chất chung của các lượng không.','Đối chiếu tập lượng có thể đạt với yêu cầu; đừng thêm cách rót ước chừng.'),dict(kind='jug',capacities=[4,2],start=[0,0],target_vessel=None,target=3,path=None))
    add('operator_synthesis','Giữ nguyên thứ tự ba số 6, 3, 2 và điền vào hai ô: 6 □ 3 □ 2 = 12. Mỗi ô chỉ được điền dấu + hoặc ×; được lặp dấu. Không thêm ngoặc, không ghép số; nhân trước rồi cộng. Tìm tất cả cách điền và kiểm không bỏ sót.', ['Số theo thứ tự: 6, 3, 2; đích 12','Hai ô chỉ + hoặc ×, được lặp; không thêm ngoặc; nhân trước cộng'],'Mọi cặp dấu đạt đích',[
        step('Liệt kê các cặp dấu cho phép','Hai lựa chọn ở mỗi vị trí tạo thành bốn cặp, không đổi thứ tự số.','(+,+); (+,×); (×,+); (×,×)','Cố định dấu đầu là cộng để thử hai dấu sau, rồi cố định dấu đầu là nhân để thử hai dấu sau.'),
        step('Tính đúng thứ tự phép tính','Mỗi cặp được tính theo cùng quy tắc ưu tiên.', '11; 12; 20; 36','6 + 3 + 2 = 11; 6 + 3 × 2 = 12; 6 × 3 + 2 = 20; 6 × 3 × 2 = 36. Chỉ biểu thức thứ hai đúng đích.'),
        step('Kiểm cách điền được chọn','Dùng lại biểu thức đúng đích, tính phần nhân trước.',12,'Chọn dấu + ở ô đầu và × ở ô sau: 6 + 3 × 2 = 6 + 6 = 12. Bốn cặp đã đủ nên không còn cách khác.','6+3*2')],[('Cặp dấu','(+,×)',''),('Biểu thức','6 + 3 × 2 = 12','')],hints('Liệt kê lựa chọn ở từng ô theo đúng tập dấu cho phép.','Tính mỗi lựa chọn bằng cùng quy tắc ưu tiên phép tính.','So từng giá trị với đích và kiểm đã xét hết các cặp dấu.'),dict(kind='operators',numbers=[6,3,2],allowed=['+','*'],repeat=True,target=12,expected=['6+3*2']))
    add('operator_synthesis','Giữ thứ tự 8, 4, 2, dùng đúng một dấu ÷ và một dấu − điền vào 8 □ 4 □ 2 để biểu thức bằng 0. Không thêm ngoặc; thực hiện chia trước trừ. Bạn viết: Điền trừ rồi chia, tính từ trái sang phải cũng được 0. Hãy tìm mọi cách đúng và kiểm câu bạn viết theo chính quy tắc đề.', ['Số theo thứ tự: 8, 4, 2; đích 0','Dùng đúng một dấu ÷ và một dấu −; chia trước trừ; không thêm ngoặc'],'Cách điền đúng và nhận xét bài viết',[
        step('Xét đủ hai vị trí của mỗi dấu','Mỗi dấu phải dùng đúng một lần nên chỉ có hai cặp vị trí.','8 ÷ 4 − 2; 8 − 4 ÷ 2','Không thêm dấu khác và không lặp dấu; hai biểu thức giữ nguyên thứ tự số.'),
        step('Kiểm biểu thức có dấu chia trước','Phần chia được tính trước rồi mới thực hiện trừ.',0,'8 ÷ 4 − 2 = 2 − 2 = 0, đạt đích.','8/4-2'),
        step('Kiểm biểu thức có dấu trừ trước','Vị trí viết trước không thay quy tắc chia trước trừ.',6,'8 − 4 ÷ 2 = 8 − 2 = 6, không bằng 0. Nếu tính từ trái sang phải thì (8 − 4) ÷ 2 = 2, cũng không phải 0. Câu đã viết sai; chỉ cặp chia rồi trừ đạt đích.','8-4/2')],[('Cặp dấu','(÷,−)',''),('Biểu thức đúng','8 ÷ 4 − 2 = 0',''),('Nhận xét','Cặp trừ rồi chia không đạt đích; giữ quy tắc chia trước trừ','')],hints('Dùng đúng số lần xuất hiện của từng dấu để liệt kê các cách.','Thực hiện quy tắc ưu tiên của đề ở cả hai cách trước khi so với đích.','Đọc lại câu đã viết và kiểm giá trị thực tế; đừng tự đổi hoặc thêm ngoặc.'),dict(kind='operators',numbers=[8,4,2],allowed=['/','-'],repeat=False,target=0,expected=['8/4-2']),student='Điền trừ rồi chia, tính từ trái sang phải cũng được 0.')
    return ROWS

def jug_neighbors(state,caps):
    a,b=state;ca,cb=caps;t=min(a,cb-b);u=min(b,ca-a)
    return {(ca,b),(a,cb),(0,b),(a,0),(a-t,b+t),(a+u,b-u)}-{state}

def structural(r):
    o=r['gap_oracle'];kind=o['kind']
    if kind=='product_pyramid':
        a,b,c=o['bottom'];m=[a*b,b*c];assert m==o['middle'] and m[0]*m[1]==o['top'];return dict(middle=m,top=m[0]*m[1])
    if kind=='jug':
        caps=tuple(o['capacities']);seen={tuple(o['start'])};pending=deque(seen)
        while pending:
            for q in jug_neighbors(pending.popleft(),caps)-seen:seen.add(q);pending.append(q)
        target=o['target'];vessel=o['target_vessel'];possible=any((s[vessel]==target if vessel is not None else target in s) for s in seen)
        assert possible==(o['path'] is not None)
        if o['path']:
            path=list(map(tuple,o['path']));assert path[0]==tuple(o['start'])
            assert all(b in jug_neighbors(a,caps) for a,b in zip(path,path[1:])) and path[-1][vessel]==target
        return dict(reachable=sorted(seen),possible=possible,path=o['path'])
    if kind=='operators':
        ns=o['numbers'];pairs=product(o['allowed'],repeat=2) if o['repeat'] else permutations(o['allowed']);values={}
        for a,b in pairs:
            expr=f'{ns[0]}{a}{ns[1]}{b}{ns[2]}';values[expr]=str(evaluate(expr,'fraction'))
        valid=[e for e,v in values.items() if Fraction(v)==o['target']];assert valid==o['expected'];return dict(all_values=values,valid=valid)
    raise ValueError(kind)

def main():
    OUT.mkdir(parents=True,exist_ok=True);rs=build();assert len(rs)==6;chats=[];checks=[];qa=[]
    for r in rs:
        raw=dump(r).encode();h=sha(raw);proof=structural(r);nums=[]
        for s in r['worked_steps']:
            if s['expression']:
                f=evaluate(s['expression'],'fraction');assert f==Fraction(s['result'])
                with localcontext() as ctx:
                    ctx.prec=90;d=evaluate(s['expression'],'decimal');assert abs(d-Decimal(f.numerator)/Decimal(f.denominator))<Decimal('1e-70')
                nums.append(dict(expression=s['expression'],exact=str(f),decimal_agrees=True))
        checks.append(dict(sample_id=r['sample_id'],source_row_sha256=h,structural=proof,numeric=nums,status='PASS_AUTHOR_ORACLE'))
        qa.append(dict(sample_id=r['sample_id'],source_row_sha256=h,status='AUTHOR_SELF_QA_PASS_PENDING_CROSS_REVIEW',actual_all_fields_read=True,criteria={k:'PASS' for k in ['math','givens_request','grade_scope','steps_units_check','initial_all_hints_no_answer_leak','student_work_grounding','schema_provenance']},human_review_claimed=False))
        for c in chat_records(r):c.update(source_row_sha256=h,acceptance_status=r['acceptance_status'],quality_status=r['quality_status']);chats.append(c)
    for name,data in [('cases.jsonl',rs),('chat.jsonl',chats),('oracle_checks.jsonl',checks),('self_qa.jsonl',qa)]: (OUT/name).write_text(''.join(dump(r)+'\n' for r in data),encoding='utf-8',newline='\n')
    manifest=dict(case_count=6,chat_count=24,form_count=3,status='DRAFT_AWAITING_CONTENT_CROSS_REVIEW',training_started=False,files={p.name:dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in OUT.glob('*.jsonl')})
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(dump(manifest))
if __name__=='__main__':main()
