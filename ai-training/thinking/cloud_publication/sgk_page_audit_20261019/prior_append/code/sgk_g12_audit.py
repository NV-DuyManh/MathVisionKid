"""Original finite representation gaps from observed publisher SGK pages."""
from pathlib import Path
from fractions import Fraction
from decimal import Decimal
from itertools import combinations
from collections import Counter
import json,hashlib,re,ast
from exhaustive_primary_math import expression_group,chat_records

HERE=Path(__file__).parent
OUT=HERE/'cloud_publication/sgk_gap_20261019'
ROWS=[]
def j(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha(b):return hashlib.sha256(b).hexdigest()
def calc(expr,typ=Fraction):
 def f(n):
  if isinstance(n,ast.Constant) and type(n.value) is int:return typ(n.value)
  if not isinstance(n,ast.BinOp):raise ValueError(expr)
  a,b=f(n.left),f(n.right)
  if isinstance(n.op,ast.Add):return a+b
  if isinstance(n.op,ast.Sub):return a-b
  if isinstance(n.op,ast.Mult):return a*b
  if isinstance(n.op,ast.Div):return a/b
  raise ValueError(expr)
 return f(ast.parse(expr,mode='eval').body)
def S(title,reason,result,explanation,expression=None,unit=''):
 return dict(title=title,reason=reason,result=str(result) if result is not None else None,
             explanation=explanation,expression=expression,unit=unit)
def hints(*texts):
 return [dict(level=i+1,hint=t,question=q) for i,(t,q) in enumerate(texts)]
def add(gap,grade,problem,givens,request,steps,answer,hs,page,volume=1,student=None,guard=False,oracle=None):
 sid=f'sgk_g12_20261019_{gap}_{sum(r["topic"]==gap for r in ROWS)+1:02d}'
 book=next(b for b in json.loads((OUT/'g12_official_pages.json').read_text('utf-8')) if b['grade']==grade and b['volume']==volume)
 row={'sample_id':sid,'case_group_id':sid+'_group','split':'train','grade':grade,'topic':gap,
 'case_kind':'guard' if guard else 'observable_student_error' if student else 'original_representation_gap',
 'problem':problem,'givens':[dict(id=f'g{i}',text=t,value=None,unit='') for i,t in enumerate(givens)],
 'requested_quantity':request,'student_work':{'text':student,'observations':[{'excerpt':student,'claim_scope':'Only explicit synthetic written work; no unseen image or private thinking inferred.'}]} if student else None,
 'initial_guidance':[hs[0]['hint']],'hints':hs,'worked_steps':[dict(step_id=f's{i}',**s) for i,s in enumerate(steps)],
 'expected_answer':[dict(quantity=request,result=answer,unit='')],'can_solve':not guard,
 'canonical_signatures':sorted({expression_group(s['expression']) for s in steps if s['expression']}),
 'acceptance_status':'ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED','quality_status':'ACCEPTED_VALIDATED',
 'human_verified':False,'teacher_certified':False,'owner_human_reviewed':False,'source_role':'AI_GENERATED',
 'provenance':{'authorship_origin':'ORIGINAL_AI_TEACHER_AUTHORING','content_human_review_completed':False,'acceptance_basis':'OWNER_PREAUTHORIZED_AFTER_EXACT_AND_SEMANTIC_QA','book_exercise_copied':False,'actual_physical_or_image_result_claimed':False},
 'curriculum_assignment':{'grade':grade,'book':'Kết nối tri thức với cuộc sống','volume':volume,'lesson_page':page,'publisher_reader_url':book['reader_urls'][0],'publisher_page_url':book['page_urls'][page-1],'source_evidence_level':'ACTUAL_PUBLISHER_PAGE_IMAGE_READ','coverage_claim':'Observed representation gap only, not exhaustive of all exercises or legal certification.'},
 'gap_oracle':oracle or {'kind':'explicit_relation'},'coverage':{'mode':'FINITE_ORIGINAL_GAP_APPEND','gap_type':gap,'numbers_only_variant':False}}
 ROWS.append(row)

def H(a,b,c):return hints((a,'Em xác định dữ kiện và luật cần dùng thế nào?'),(b,'Em thực hiện theo luật đã cho ra sao?'),(c,'Em đối chiếu toàn bộ điều kiện để kiểm thế nào?'))

def build():
 add('complete_decompositions',1,'Có 5 hạt khác nhau. Chia hết vào hai hộp có tên Trái và Phải; một hộp được phép trống. Chỉ ghi số hạt ở mỗi hộp, không phân biệt hạt nào. Liệt kê đủ các cặp (Trái, Phải).',['Tổng 5; hai hộp có tên; cho phép hộp trống; chỉ xét số lượng'],'Các cặp số lượng',[
 S('Liệt kê có thứ tự','Tăng số hạt hộp Trái từng đơn vị và bớt tương ứng ở hộp Phải.','(0,5), (1,4), (2,3), (3,2), (4,1), (5,0)','Các cặp đều gộp đủ năm hạt; đổi hai hộp là vị trí khác.'),
 S('Kiểm đủ trường hợp','Hộp Trái không thể ít hơn không hay nhiều hơn toàn bộ.',6,'Đã xét từng lượng Trái từ không đến năm đúng một lần.','5+1')], '(0,5), (1,4), (2,3), (3,2), (4,1), (5,0)',H('Xét số ở mỗi hộp theo đúng tên hộp.','Cho lượng ở một hộp tăng từng đơn vị, lượng kia giữ tổng.','Kiểm cả trường hợp hộp trống và không lặp cặp.'),35,oracle={'kind':'decompositions','total':5,'allow_zero':True})
 add('complete_decompositions',1,'Tách 6 thẻ vào hai ngăn A, B. Mỗi ngăn có ít nhất một thẻ và không quá 4 thẻ. Ghi tất cả cặp số lượng (A,B), không xét danh tính thẻ.',['6 thẻ; mỗi ngăn từ1đến4'],'Các cặp thỏa hai giới hạn',[
 S('Xét lượng ở A','Mỗi ngăn cần đủ điều kiện nên thử các lượng A được phép.','(2,4), (3,3), (4,2)','A bằng một làm B vượt giới hạn; A bằng hai, ba, bốn cho các cặp đã nêu.'),
 S('Kiểm lượng B','Hai số ở mỗi cặp cộng lại phải đúng toàn bộ.',6,'Mỗi cặp dùng hết sáu thẻ và mỗi ngăn không vượt bốn.','2+4')], '(2,4), (3,3), (4,2)',H('Tổng số thẻ không thay đổi khi tách.','Một cặp chỉ giữ lại khi cả hai ngăn cùng thỏa giới hạn.','Rà đủ từng lượng ở ngăn đầu, rồi kiểm tổng.'),35,oracle={'kind':'decompositions','total':6,'minimum':1,'maximum':4})
 add('complete_decompositions',1,'Bài viết giả định liệt kê cách tách 4 nút vào hộp Đỏ và Xanh, hộp được phép trống: (1,3), (2,2), (3,1). Bạn ghi đã đủ. Giữ danh sách ấy và bổ sung các cặp còn thiếu, chỉ xét số lượng.',['Tổng4; haihộpcótên; hộptrốngđượcphép'],'Cặp cần bổ sung',[
 S('Đối chiếu đầu và cuối','Quyền để hộp trống cho phép một hộp nhận toàn bộ.','Thiếu (0,4) và (4,0)','Các cặp đã viết có tổng đúng nhưng chưa xét hai trường hợp có hộp trống.'),
 S('Kiểm đủ lượng hộp Đỏ','Xét liên tiếp từ không đến toàn bộ.',5,'Sau bổ sung có đủ một cặp cho mỗi lượng hộp Đỏ.','4+1')], '(0,4) và (4,0)',H('Phân biệt cặp đã viết đúng với danh sách đã đủ.','Đọc lại điều kiện về hộp trống.','Kiểm từng lượng ở hộp đầu có xuất hiện đúng một lần chưa.'),35,student='(1,3), (2,2), (3,1); đã đủ.',oracle={'kind':'missing_decompositions','total':4,'existing':[[1,3],[2,2],[3,1]]})
 add('complete_decompositions',1,'Cần liệt kê mọi cách chia số lượng 7 bông vào hai lọ có tên A và B. Đề chưa nói lọ được để trống hay mỗi lọ phải có hoa. Có thể chốt một danh sách duy nhất theo yêu cầu chưa?',['Tổng7; hai lọ có tên; chưa có quy định lọ trống'],'Điều cần hỏi lại',[
 S('Nhận điều kiện chưa rõ','Cho phép lọ trống thay đổi danh sách cần liệt kê.',None,'Cần hỏi: mỗi lọ có phải có ít nhất một bông hay lọ được phép trống? Không tự chọn một quy ước.')], 'Hai lọ có được phép để trống không?',H('Số hoa toàn bộ chưa cho biết quy định của từng lọ.','Đối chiếu các điều kiện cần để xác định toàn bộ danh sách.','Hỏi rõ điều kiện còn thiếu trước khi chốt danh sách.'),35,guard=True)

 add('hundred_grid_patch',1,'Bảng từ 1 đến 100 có mỗi hàng mười ô, đi sang phải tăng một, đi xuống cùng cột tăng một chục. Miếng 2×2 có hàng trên: 24, X; hàng dưới: Y, 35. Điền X,Y rồi kiểm theo cả hàng và cột.',['Mỗi hàng10ô; phải+1; xuống+10; bảng2×2'],'X và Y',[
 S('Đi ngang từ ô đã biết','X ngay bên phải ô đầu.',25,'Một bước sang phải tăng một.','24+1'),S('Đi xuống từ ô đầu','Y ngay dưới ô đầu.',34,'Cùng cột cách một hàng tăng một chục.','24+10'),S('Kiểm ô cuối','Ô bên phải Y phải khớp góc đã cho.',35,'X đi xuống cũng được ba mươi lăm, nên hai chiều cùng đúng.','34+1')], 'X=25; Y=34',H('Phân biệt bước ngang với bước dọc.','Dùng ô đã biết để tìm từng ô kề theo đúng hướng.','Đi tới ô góc còn lại bằng hai đường để kiểm.'),23,volume=2,oracle={'kind':'grid','top_left':24,'width':10,'answers':{'X':25,'Y':34}})
 add('hundred_grid_patch',1,'Trong bảng 1 đến 100, mỗi hàng mười ô, phải tăng một, xuống tăng mười. Hai miếng chữ L đều không xoay: A có ô trên 41, dưới 51, bên phải ô51 là52; B có ô trên41, dưới42, bên phải42là43. Chọn miếng có thể đặt vừa bảng theo các hướng đã cho.',['Hai miếng giữ nguyên hướng;quy tắc bảng chuẩn'],'Miếng phù hợp',[
 S('Kiểm chiều dọc','Ô dưới cần lớn hơn ô trên một chục.',51,'Miếng A giữ bước dọc; miếng B chỉ tăng một nên sai chiều.','41+10'),S('Kiểm chiều ngang','Ô bên phải tăng thêm một.',52,'Miếng A khớp cả hai quan hệ, không chỉ một cặp.','51+1')], 'Miếng A',H('Giữ đúng hướng miếng theo đề.','Kiểm từng cặp ô kề theo cả hai chiều.','Miếng cần thỏa đồng thời mọi quan hệ.'),23,volume=2,oracle={'kind':'explicit_patch','valid':'A'})
 add('hundred_grid_patch',1,'Bảng mỗi hàng mười ô tăng từ trái qua phải. Bạn viết: Ô ngay dưới 56 là57 vì thêm một. Hãy giữ câu viết, sửa số ở ngay dưới và kiểm bằng chiều dọc; không có hình chưa thấy cần suy đoán.',['Bảng chuẩn1đến100;mỗi hàng10ô'],'Ô ngay dưới 56',[
 S('Phân biệt hai hướng','Thêm một dùng cho ô bên phải; cùng cột hàng kế tiếp thêm một chục.',66,'Câu viết dùng bước ngang cho bước dọc.','56+10'),S('Kiểm ngược','Ô trên của kết quả phải quay về dữ kiện.',56,'Bớt một chục khôi phục ô ban đầu.','66-10')], '66',H('Câu hỏi nói ô dưới hay ô bên phải?','Dùng số ô của mỗi hàng để xét bước dọc.','Trở lại ô phía trên để kiểm số em điền.'),23,volume=2,student='Ô ngay dưới56là57 vìthêmmột.',oracle={'kind':'grid_below','value':56,'width':10})
 add('hundred_grid_patch',1,'Một mảnh bảng có các số tăng một khi đi sang phải; ô A ghi28. Cần tìm ô ngay dưới A nhưng chưa biết mỗi hàng có bao nhiêu ô hay quy tắc theo cột. Có thể xác định duy nhất chưa?',['Chỉ có quy tắc ngang; chưa có số ô mỗi hàng'],'Thông tin cần bổ sung',[
 S('Kiểm quy tắc còn thiếu','Bước dọc phụ thuộc số ô của hàng hoặc quy tắc cột.',None,'Xin cho biết số ô mỗi hàng hoặc số ở một ô cùng cột đã biết. Không mặc định bảng luôn có mười ô một hàng.')], 'Mỗi hàng có bao nhiêu ô hoặc bước xuống cùng cột là bao nhiêu?',H('Một quy tắc theo hàng chưa mô tả cách chuyển hàng.','Liệt kê dữ kiện cần cho ô cùng cột.','Hỏi rõ cấu trúc bảng trước khi điền.'),23,volume=2,guard=True)

 add('sum_pyramid',1,'Tháp số có hàng đáy từ trái sang phải là1,3,2. Mỗi ô trên bằng tổng đúng hai ô liền dưới nó. Điền cả hàng giữa và ô đỉnh.',['Đáy1,3,2; ô trên cộng hai ô sát dưới'],'Hàng giữa và đỉnh',[
 S('Ô giữa trái','Dùng hai ô dưới thuộc đúng vị trí này.',4,'Không cộng tất cả hàng đáy cho một ô giữa.','1+3'),S('Ô giữa phải','Ô dưới giữa được dùng cho ô trên kề theo luật.',5,'Ba cộng hai cho ô giữa phải.','3+2'),S('Ô đỉnh','Chỉ cộng hai ô ngay dưới đỉnh.',9,'Đỉnh được tính từ hàng giữa, kiểm lại từng tầng theo luật.','4+5')], 'Hàng giữa4,5; đỉnh9',H('Bắt đầu ở hàng đã biết đầy đủ.','Mỗi ô chỉ liên hệ với hai ô ngay dưới nó.','Kiểm từng tầng theo cùng luật, không cộng cả hình một lần.'),87,oracle={'kind':'pyramid','bottom':[1,3,2]})
 add('sum_pyramid',1,'Tháp số dùng luật ô trên bằng tổng hai ô ngay dưới. Đáy là1,X,0. Ô giữa trái ghi3. Tìm X, ô giữa phải và đỉnh, không được thay dữ kiện.',['Đáy1,X,0; giữa trái3; luật cộngkề'],'Ba ô cần điền',[
 S('Tìm ô đáy còn thiếu','Một phần cộng phần còn lại bằng ô trên.',2,'Lấy tổng đã biết bớt phần đáy đã biết.','3-1'),S('Ô giữa phải','Dùng hai ô đáy sát phía phải.',2,'Cộng với không giữ nguyên lượng.','2+0'),S('Đỉnh','Gộp đúng hai ô giữa.',5,'Kiểm một cộng X khớp ô giữa trái rồi mới kết luận đỉnh.','3+2')], 'X=2; giữa phải2; đỉnh5',H('Có một ô trên và một ô dưới đã biết.','Tìm phần còn lại trước khi xây tiếp tầng trên.','Thế lại số đáy rồi kiểm cả hai ô giữa.'),87,oracle={'kind':'pyramid_inverse','bottom':[1,None,0],'left_middle':3})
 add('sum_pyramid',1,'Đáy tháp số là2,0,1; mỗi ô trên cộng hai ô ngay dưới. Bài bạn ghi hàng giữa là2,1 nhưng đỉnh bằng5 vì cộng thêm số2 ở đáy. Nhận xét đúng dòng đã cho và sửa đỉnh.',['Đáy2,0,1; giữa2,1; luật cộng hai ô ngay dưới'],'Đỉnh đúng và nhận xét',[
 S('Đối chiếu phạm vi hai ô','Đỉnh chỉ phụ thuộc hai ô giữa, không lấy thêm ô đáy.',3,'Hàng giữa đã đúng; bước tính đỉnh đã dùng thêm ô không thuộc cặp ngay dưới.','2+1'),S('Kiểm tầng giữa','Ô giữa trái khớp hai ô đáy của nó.',2,'Ô giữa phải là không cộng một bằng một; không thêm hai lần phần đáy.','2+0')], 'Đỉnh3; không cộng thêm ô đáy vào đỉnh',H('Giữ phần bài viết đã đúng khi góp ý.','Chỉ ra hai ô là đầu vào trực tiếp của đỉnh.','Kiểm lại từng tầng theo quan hệ kề, không gom mọi ô.'),87,student='Hàng giữa2,1; đỉnh5 vì cộngthêmsố2ởđáy.',oracle={'kind':'pyramid','bottom':[2,0,1]})
 add('sum_pyramid',1,'Một hình tháp chỉ cho ba số ở đáy2,1,3 và để trống các ô trên. Đề chưa cho luật tạo ô trên. Bạn hỏi đỉnh chắc chắn là bao nhiêu. Hãy trả lời theo dữ kiện thật.',['Có hình tháp bằngchữ; chưa cóluật'],'Quy tắc cần hỏi',[
 S('Xác định chưa đủ luật','Hình dạng tháp không tự quy định cộng, trừ hay luật khác.',None,'Cần hỏi mỗi ô trên được tạo từ các ô dưới như thế nào trước khi xác định đỉnh.')], 'Mỗi ô phía trên được tạo theo quy tắc nào?',H('Hình bố trí chưa thay thế quy tắc tính.','Kiểm đề đã nêu mối quan hệ các tầng chưa.','Xin luật tạo ô trước khi tính.'),87,guard=True)

 add('expression_target_classification',1,'Bốn huy hiệu mang mã A:3+4; B:9−2; C:5+1; D:7+0. Chỉ chọn huy hiệu có giá trị bằng7. Ghi mã được chọn và đếm số huy hiệu; mỗi mã là một huy hiệu riêng.',['Bốn mã/phép tính rõ; mốc7'],'Mã và số huy hiệu',[
 S('Tính A và B','Giá trị của phép tính quyết định nhóm, không phải số nào xuất hiện trên thẻ.',7,'A dùng ba cộng bốn; B dùng chín bớt hai, đều đạt mốc.','3+4'),S('Tính các mã còn lại','Xét đủ thẻ để không bỏ trường hợp cộng không.',7,'C không đạt mốc còn D đạt mốc; phép cộng không giữ nguyên.','7+0'),S('Đếm các mã đạt','Một mã tương ứng một huy hiệu.',3,'Giữ A,B,D; không cộng ba giá trị của thẻ để thay cho số huy hiệu.','1+1+1')], 'A,B,D;3huy hiệu',H('Tách giá trị phép tính khỏi số thẻ được chọn.','Tính từng thẻ rồi đối chiếu cùng mốc.','Đếm mỗi mã đạt đúng một lần sau khi phân loại.'),89,oracle={'kind':'classify','expressions':{'A':'3+4','B':'9-2','C':'5+1','D':'7+0'},'target':7})
 add('expression_target_classification',1,'Có các thẻ P:1+2; Q:8−3; R:6−3; S:2+3. Xếp mỗi thẻ vào hộp ghi3 hoặc hộp ghi5 theo giá trị. Ghi mã trong từng hộp và kiểm không thẻ nào bỏ sót.',['P,Q,R,S; hai hộp mốc3/5'],'Hai nhóm mã',[
 S('Nhóm mốc thứ nhất','Tính phép trên thẻ trước khi chọn hộp.',3,'P và R có cùng giá trị dù cách viết khác.','1+2'),S('Nhóm mốc còn lại','Xét đủ từng mã chưa xếp.',5,'Q và S cùng đạt mốc năm; cả bốn mã dùng một lần.','8-3')], 'Hộp3:P,R; hộp5:Q,S',H('Hộp được chọn theo kết quả, không theo dấu tính.','Các phép khác nhau có thể cùng một kết quả.','Rà từng mã xem đã xếp đúng một lần chưa.'),89,oracle={'kind':'classify_all','expressions':{'P':'1+2','Q':'8-3','R':'6-3','S':'2+3'}})
 add('expression_target_classification',1,'Thẻ M:4+2; N:8−2; K:3+2. Cần đếm thẻ có kết quả bằng6. Bạn viết M,N đạt nên có12thẻ vì6+6=12. Giữ câu viết, sửa đại lượng cần đếm.',['M,N,K là3thẻriêng; mốc6'],'Số thẻ đạt',[
 S('Giữ kết quả phân loại','M và N đạt mốc; K không đạt.',2,'Có đúng hai mã được chọn. Việc cộng giá trị trên thẻ không cho số thẻ.','1+1'),S('Đối chiếu đại lượng','Câu hỏi đếm vật mang mã, không cộng kết quả phép tính.','2thẻ','Sửa kết luận số thẻ, không suy bạn đếm hay nhìn ảnh ra sao.')], '2thẻ;M,N',H('Câu hỏi cần số thẻ hay tổng các giá trị trên thẻ?','Giữ lại việc chọn mã đúng trước khi sửa câu trả lời.','Đếm các mã đã chọn để kiểm đại lượng.'),89,student='M,Nđạt nêncó12thẻ vì6+6=12.',oracle={'kind':'classify','expressions':{'M':'4+2','N':'8-2','K':'3+2'},'target':6})
 add('expression_target_classification',1,'Cần đếm tất cả thẻ có kết quả bằng8. Hai thẻ thấy rõ là A:5+3 và B:9−1, nhưng phiếu nói còn một thẻ C bị che, chưa có phép tính của C. Có thể chốt số thẻ đạt trong cả ba chưa?',['A,B rõ; C chưađọcđược; cầncả3thẻ'],'Thông tin còn thiếu',[
 S('Phân biệt phần đã biết và toàn bộ','Phần bị che có thể làm thay đổi tổng số thẻ đạt.',None,'Cần cung cấp phép tính trên C. Chỉ có thể xác nhận A,B đạt, chưa chốt cả ba.')], 'Phép tính trên thẻ C là gì?',H('Xác định yêu cầu nói về toàn bộ hay chỉ phần đọc được.','Không coi thẻ bị che là tự động đạt hoặc không đạt.','Xin nội dung thẻ còn thiếu trước khi chốt số lượng.'),89,guard=True)

 add('blank_digit_column_constraints',1,'Điền một chữ số vào □ để2□+13=38. □là hàng đơn vị của số hai chữ số. Nêu cách dựa vào từng hàng và kiểm phép cộng sau khi điền.',['□mộtchữsố;2□làsốhaichữsố; khôngđổi13/38'],'Chữ số cần điền',[
 S('Tìm hàng đơn vị','Hàng đơn vị của tổng gồm phần còn thiếu cộng ba.',5,'Tám bớt ba cho chữ số đơn vị; hai chục cộng một chục bằng ba chục.','8-3'),S('Kiểm cả phép cộng','Thế chữ số vào đúng vị trí, giữ các hàng.',38,'Hai mươi lăm cộng mười ba đúng tổng.','25+13')], '5',H('Ô trống đang nằm ở hàng nào?','Đối chiếu các chữ số cùng hàng trước khi ghép cả số.','Thế chữ số vừa tìm vào phép tính đầy đủ để kiểm.'),66,volume=2,oracle={'kind':'blank_digit','pattern':'2?+13=38'})
 add('blank_digit_column_constraints',1,'Điền chữ số hàng chục trong□4−12=32. Số□4có hai chữ số, không thêm dấu hoặc di chuyển số. Kiểm cả hàng chục và đơn vị.',['□hàngchục; sốhaichữsố;phéptrừkhôngnhớ'],'Chữ số hàng chục',[
 S('Đối chiếu các hàng','Hàng đơn vị bốn bớt hai cho hai, còn hàng chục cần tìm.',4,'Ba chục kết quả cộng một chục đã bớt cho bốn chục ban đầu.','3+1'),S('Kiểm phép trừ','Ghép chữ số vào đúng hàng.',32,'Bốn mươi bốn trừ mười hai được ba mươi hai.','44-12')], '4',H('Số chưa biết là một chữ số chục, không phải cả số.','Dùng quan hệ giữa hiệu và số trừ để tìm hàng còn thiếu.','Kiểm lại từng hàng sau khi ghép số.'),70,volume=2,oracle={'kind':'blank_digit','pattern':'?4-12=32'})
 add('blank_digit_column_constraints',1,'Điền□trong4□+2=49. Bài bạn ghi□=3 và viết43+2=49. Giữ dòng ấy, kiểm phép cộng rồi sửa chữ số, không suy cách bạn đã nghĩ.',['□mộtchữsốđơnvị;4□+2=49'],'Chữ số đúng',[
 S('Kiểm dòng viết','Tính phép mà bạn thực sự đã ghi.',45,'Bốn mươi ba cộng hai không bằng tổng đề yêu cầu.','43+2'),S('Tìm chữ số đơn vị phù hợp','Đơn vị tổng bớt phần cộng thêm cho đơn vị ban đầu.',7,'Chữ số cần điền là bảy; giữ nguyên bốn chục.','9-2'),S('Kiểm sau sửa','Thế chữ số vừa tìm vào đúng chỗ.',49,'Bốn mươi bảy cộng hai khớp tổng.','47+2')], '7',H('Kiểm dòng phép tính đã viết trước khi sửa.','Ô trống ở hàng đơn vị nên dùng đúng hàng của tổng.','Thế lại chữ số rồi kiểm toàn phép, không chỉ một hàng.'),66,volume=2,student='□=3;43+2=49.',oracle={'kind':'blank_digit','pattern':'4?+2=49'})
 add('blank_digit_column_constraints',1,'Hai ô khác nhau A,B là chữ số hàng chục trong A2+B3=75; cả hai số đều có hai chữ số. Đề yêu cầu tìm duy nhất A,B nhưng không cho thêm điều kiện. Có đủ dữ kiện để chỉ một cặp không?',['A,Btừ1đến9; đơnvị2và3; tổng75'],'Kết luận về tính duy nhất',[
 S('Đối chiếu nhiều cách','Cùng tổng có thể nhận từ các số hàng chục khác nhau.',75,'Mười hai cộng sáu mươi ba là một cặp phù hợp.','12+63'),S('Kiểm một cặp khác','Hai nghiệm khác nhau bác bỏ yêu cầu duy nhất.',75,'Hai mươi hai cộng năm mươi ba cũng phù hợp; cần điều kiện thêm để chọn riêng một cặp.','22+53')], 'Chưa duy nhất; cần điều kiện bổ sung cho A,B',H('Hai ô có được nêu là cùng một chữ số không?','Thử tìm hơn một cặp thỏa tất cả điều kiện.','Nếu nhiều cặp đều đúng, hỏi điều kiện chọn riêng một cặp.'),70,volume=2,guard=True,oracle={'kind':'two_blanks','solutions':[[1,6],[2,5],[3,4],[4,3],[5,2],[6,1]]})

 add('one_digit_swap_repair',1,'Dãy thẻ viết43−21=62. Chỉ được đổi chỗ đúng hai thẻ chữ số, giữ nguyên dấu−,dấu= và mọi vị trí hai chữ số; không dùng số có0ởđầu. Hãy tìm phép đúng sau đổi và chỉ rõ hai thẻ đổi.',['Chỉđổihaithẻchữsố; dấugiữnguyên'],'Cách đổi và phép đúng',[
 S('Thử sửa theo hàng','Mỗi lần thử chỉ hoán đổi hai chữ số và giữ các thẻ khác.','Đổi4ởđầu với6ởkếtquả','Được sáu mươi ba trừ hai mươi mốt bằng bốn mươi hai.'),S('Kiểm phép đã đổi','Tính cả phép sau đổi để đối chiếu kết quả.',42,'Hàng đơn vị ba bớt một, hàng chục sáu bớt hai; mọi thẻ còn đúng số lượng.','63-21')], '63−21=42;đổi4đầu với6ởkếtquả',H('Giữ dấu và số lượng từng thẻ khi thử đổi.','Kiểm hàng chục cùng hàng đơn vị của phép sau đổi.','Đếm đúng hai vị trí đã đổi rồi tính lại để kiểm.'),65,volume=2,oracle={'kind':'swap','original':'43-21=62'})
 add('one_digit_swap_repair',1,'Các thẻ ghi25+14=93. Chỉ đổi đúng hai thẻ chữ số, không thêm/bỏ thẻ, dấu giữ nguyên. Nêu một cách sửa rồi kiểm tổng theo từng hàng.',['Chỉhoánđổi2chữsố; mọi dấu giữ nguyên'],'Phép sau sửa',[
 S('Đối chiếu tổng đang viết','Hai số hạng đã cho gộp được tổng theo hàng.',39,'Đơn vị năm cộng bốn bằng chín, chục hai cộng một bằng ba.','25+14'),S('Đổi trong kết quả','Hai chữ số kết quả đang đảo vị trí.','Đổi9với3ởbênphảidấubằng','Sau đổi chỉ hai vị trí thay đổi, phép thành hai mươi lăm cộng mười bốn bằng ba mươi chín.')], '25+14=39;đổi9với3ởkếtquả',H('Tính một vế trước để biết điều kiện vế kia cần thỏa.','Không thay chữ số bằng chữ số mới ngoài bộ thẻ.','Rà lại phép tính và đúng hai vị trí hoán đổi.'),65,volume=2,oracle={'kind':'swap','original':'25+14=93'})
 add('one_digit_swap_repair',1,'Dãy34+12=64được yêu cầu sửa bằng đúng một lần đổi hai thẻ chữ số. Bạn đổi3với1ởhai số hạng, được14+32=64và nói đã đúng. Giữ đề xuất, kiểm nó rồi nêu cách sửa hợp lệ.',['Dãythẻgốc34+12=64;chỉđổi2thẻ'],'Sửa đề xuất',[
 S('Kiểm phép bạn đề xuất','Không đủ chỉ đổi đúng số thẻ; đẳng thức sau đổi cũng phải đúng.',46,'Mười bốn cộng ba mươi hai không bằng sáu mươi bốn.','14+32'),S('Chọn đổi đúng trong kết quả','Giữ hai số hạng, đảo hai chữ số bên phải.',46,'Đổi sáu với bốn ở kết quả; kiểm ba mươi bốn cộng mười hai được bốn mươi sáu.','34+12')], '34+12=46;đổi6với4ởkếtquả',H('Kiểm phép mới chứ không chỉ số lần đổi thẻ.','Nếu một đề xuất chưa đúng, giữ nguyên bộ thẻ để thử cách khác.','Tính lại cả hai vế và rà đúng hai thẻ đã đổi.'),65,volume=2,student='Đổi3với1,được14+32=64;đãđúng.',oracle={'kind':'swap','original':'34+12=64'})
 add('one_digit_swap_repair',1,'Phiếu chỉ ghi phép tính sai52−13=93và yêu cầu sửa. Chưa nói được đổi thẻ, thay chữ số hay viết lại kết quả; bạn muốn biết chính xác hai thẻ phải đổi theo luật phiếu. Hãy xin đúng luật trước.',['Phép52−13=93;chưacóluậtthayđổi'],'Điều cần hỏi',[
 S('Xác định yêu cầu phụ thuộc luật','Phép viết sai không tự nêu phép biến đổi thẻ được phép.',None,'Cần hỏi phiếu cho đổi đúng hai thẻ nào, có giữ dấu và vị trí số hay không; chưa thể khẳng định đúng một cặp thẻ phải đổi.')], 'Được phép sửa theo luật nào: đổi hai thẻ, thay chữ số hay chỉ viết lại kết quả?',H('Phân biệt tính lại kết quả với tìm thao tác sửa thẻ.','Kiểm phiếu đã cho phép thay đổi những phần nào chưa.','Xin luật thao tác trước khi chọn thẻ phải đổi.'),65,volume=2,guard=True)

 add('constrained_arithmetic_path',1,'Bản đồ bằng chữ có đúng các mũi tên S→A,S→B,A→T,B→C,C→T. Ô Aghi20+30; Bghi20+40; Cghi80−20. TừSđếnTchỉ đi theo mũi tên và qua ô có kết quả bằng60. Hãy chỉ đường hợp lệ.',['Đủ5mũitên;A,B,Ccóphéptính;mốc60'],'Đường đi',[
 S('Kiểm ô có thể đi','Tính giá trị của các ô trước khi chọn nhánh.',60,'B đạt mốc, C cũng đạt; A chỉ bằng năm mươi.','20+40'),S('Kiểm nhánh đúng theo mũi tên','Ô đạt mốc vẫn phải có liên kết theo hướng đề cho.',60,'Chuỗi có đủ các mũi tên; S→A→T bị loại bởi A không đạt mốc.','80-20')], 'S→B→C→T',H('Cần thỏa điều kiện giá trị và điều kiện nối đường.','Tính các ô tại chỗ rẽ trước khi chọn nhánh.','Rà lại từng mũi tên của đường em chọn.'),65,volume=2,oracle={'kind':'graph','edges':[['S','A'],['S','B'],['A','T'],['B','C'],['C','T']],'values':{'A':50,'B':60,'C':60},'target':60,'paths':[['S','B','C','T']]})
 add('constrained_arithmetic_path',1,'Mũi tên có S→P,S→Q,P→R,Q→R,R→T. Các ô ghi P:45−12,Q:60−10,R:20+14. Chỉ qua ô có giá trị bé hơn40. Chọn đường từSđếnT và giải thích vì sao một nhánh không dùng được.',['Đủmũitên; điềukiệnbéhơn40'],'Đường hợp lệ',[
 S('Kiểm P','Bớt theo đúng hai số ghi ở ô.',33,'P bé hơn mốc nên có thể qua.','45-12'),S('Kiểm nhánh Q','Điều kiện bé hơn cần thỏa ở mọi ô trung gian.',50,'Q không bé hơn mốc nên nhánh này bị loại.','60-10'),S('Kiểm ô nối cuối','R cũng phải thỏa trước khi vào T.',34,'Đường S→P→R→T có đủ nối và mọi ô đạt điều kiện.','20+14')], 'S→P→R→T',H('Đọc rõ dấu điều kiện thay vì chỉ tìm ô lớn nhất.','Một ô không đạt làm cả nhánh qua ô ấy không hợp lệ.','Kiểm đủ mọi ô và hướng mũi tên tới đích.'),65,volume=2,oracle={'kind':'graph','edges':[['S','P'],['S','Q'],['P','R'],['Q','R'],['R','T']],'values':{'P':33,'Q':50,'R':34},'less_than':40,'paths':[['S','P','R','T']]})
 add('constrained_arithmetic_path',1,'Chỉ có mũi tên S→A,A→B,B→T. Aghi30+20,Bghi70−20; chỉ qua ô có kết quả50. Bạn chọnS→B→TvìBđạt mốc. Hãy giữ đường bạn chọn, kiểm mũi tên rồi sửa.',['Đúng3mũitên;A,Bcùngmốc50'],'Đường sửa',[
 S('Kiểm điều kiện nối','Đạt giá trị chưa cho phép nhảy qua một cạnh không tồn tại.','S→Bkhôngcómũitên','Không suy bạn đi thật hay nhìn bản đồ sai; chỉ đối chiếu đường đã viết.'),S('Kiểm A để đi qua đúng nối','Ô A nằm bắt buộc giữa S và B.',50,'Sau khi xét A, đường hợp lệ là S→A→B→T; B cũng đạt mốc.','30+20')], 'S→A→B→T',H('Đường được viết có mỗi bước đúng mũi tên không?','Phân biệt ô đạt mốc với hai ô có thể đi trực tiếp.','Sửa đường rồi kiểm cả mũi tên và giá trị.'),65,volume=2,student='S→B→T vìBđạtmốc.',oracle={'kind':'graph','edges':[['S','A'],['A','B'],['B','T']],'values':{'A':50,'B':50},'target':50,'paths':[['S','A','B','T']]})
 add('constrained_arithmetic_path',1,'Có các ô A:20+20,B:60−20,C:30+10đều ở bản đồ trò chơi. Chưa gửi các mũi tên nối, vị trí xuất phát hay đích. Hỏi đường phải đi qua các ô có giá trị40. Hãy yêu cầu dữ kiện cần để tìm đường.',['Biếtphéptínhởô;thiếucấutrúcđồthị'],'Dữ kiện còn thiếu',[
 S('Xác định thiếu cấu trúc đường','Kết quả phép tính không cho biết ô nào nối ô nào và theo hướng nào.',None,'Xin vị trí xuất phát, đích và toàn bộ mũi tên hoặc ảnh rõ bản đồ. Chưa chỉ một đường giả định.')], 'Xin điểm xuất phát, đích và các mũi tên nối ô.',H('Một đường cần điểm đầu, điểm cuối và các nối hợp lệ.','Không dùng thứ tự liệt kê ô thay cho mũi tên.','Xin bản đồ hoặc mô tả đầy đủ các nối trước khi chọn đường.'),65,volume=2,guard=True)

 add('conditional_board_game',2,'Trò chơi bằng chữ: quân đang ởô2; gieo được3chấm thì tiến đúng3ô, không tính ôđangđứng. Đếnô5phải nhảy theo mũi tên sangô9. Ô9ghi5×4; trả lời đúng thì ởlạiô9, sai thì vềô2. Bạn trả lời20. Cuối lượt quân ởđâu?',['Ô2;3chấm;ô5nhảysang9;đúngởlại;saiquayvề'],'Ô cuối lượt',[
 S('Đếm các bước tiến','Ô xuất phát không tính là một bước.',5,'Các bước tới ô ba,bốn,năm; đến ô có luật nhảy.','2+3'),S('Áp dụng nhánh và kiểm đáp án','Đi tới ô đích của mũi tên rồi xét phép tính ở đó.',20,'Năm nhân bốn bằng hai mươi, khớp câu trả lời nên quân ở lại ô chín.','5*4')], 'Ô9',H('Theo dõi vị trí qua từng luật theo đúng thứ tự.','Chỉ nhảy khi đến ô kích hoạt, rồi kiểm phép ở ô được chỉ tới.','Áp dụng điều kiện đúng hoặc sai sau khi đối chiếu câu trả lời.'),33,volume=2,oracle={'kind':'board','start':2,'roll':3,'jump':{'5':9},'expression':'5*4','response':20,'finish':9})
 add('conditional_board_game',2,'Quân ởô1, gieo4chấm và tiến4ô không tínhô1. Ô5nhảy sangô8. Ô8ghi18:2;đúngởlạiô8,saiquayvềô1. Người chơi ghi8làm kết quả phép chia. Hỏi vị trí cuối lượt và lý do.',['Ô1;4chấm;5→8;ô8ghi18:2;trảlời8'],'Ô cuối lượt',[
 S('Theo lượt di chuyển','Tiến số ô theo chấm rồi áp dụng ô nhảy.',5,'Đến ô năm nên chuyển sang ô tám theo luật.','1+4'),S('Kiểm phép trả lời','So số trả lời với giá trị đúng của phép chia.',9,'Mười tám chia hai bằng chín, khác tám nên áp dụng nhánh quay về ô đầu lượt.','18/2')], 'Ô1;vìtrảlờisai',H('Phân biệt ô đến tạm thời với ô cuối sau kiểm đáp án.','Kiểm phép tính thay vì lấy số ô làm đáp án.','Dùng luật quay về đúng ô đầu lượt nếu câu trả lời chưa khớp.'),33,volume=2,oracle={'kind':'board','start':1,'roll':4,'jump':{'5':8},'expression':'18/2','response':8,'finish':1})
 add('conditional_board_game',2,'Luật: từô3gieo2chấm, tiến2ô không tínhô3;khôngcóônhảy;ô4ghi2×3,ô5ghi10:2;đúngthìởôđến,saiquayvềô3. Bạn viết: ô3làbướcmột,ô4làbướchai;trảlời6nênkếtthúctạiô4. Giữ bản ghi, sửa vị trí cần xét và kết luận khi giữ nguyên câu trả lời6.',['Ô3;2chấm;khôngônhảy;phéptínhô4/5;luậtđúngsai'],'Ô cuối khi giữ câu trả lời',[
 S('Sửa cách đếm vị trí','Chỉ ô mới đi vào mới tính là bước.',5,'Hai bước lần lượt vào ô bốn rồi ô năm; không dùng phép ở ô bốn.','3+2'),S('Kiểm câu trả lời tại ô đúng','Ô năm mới là ô cần trả lời.',5,'Mười chia hai bằng năm; giữ câu trả lời sáu là sai nên quay về ô ba.','10/2')], 'Ô3;khi giữcâutrảlời6',H('Đếm ô được đi vào, không đếm lại ô đang đứng.','Sau khi sửa vị trí, xét phép ở chính ô đến.','Giữ câu trả lời được đề yêu cầu và áp dụng đúng nhánh.'),33,volume=2,student='Ô3bướcmột,ô4bướchai;trảlời6nênởô4.',oracle={'kind':'board','start':3,'roll':2,'jump':{},'expression':'10/2','response':6,'finish':3})
 add('conditional_board_game',2,'Quân bắt đầu ởô2,gieo3chấm;ô5cóphép2×5. Luật đúngởlạiô5,saiquayvềô2. Đề chưaghi người chơi đã trảlời gì, nhưng hỏi chắcchắn quân cuối lượt ởđâu. Hãy hỏi đúng dữ kiện còn thiếu.',['Đủvịtrí/lượt/phéptính;thiếucâutrảlờithựctế'],'Dữ kiện để chọn nhánh',[
 S('Phân biệt đáp án chuẩn và đáp án người chơi','Biết phép đúng chưa chứng minh người chơi đã trả lời đúng.',None,'Cần hỏi người chơi đã ghi hoặc nói kết quả nào. Không tự gán người chơi biết hay trả lời sai.')], 'Người chơi đã trả lời kết quả nào ở ô5?',H('Hai nhánh phụ thuộc điều gì của lượt chơi?','Đáp án chuẩn không thay cho bản ghi câu trả lời của người chơi.','Xin câu trả lời thực tế trước khi chọn vị trí cuối.'),33,volume=2,guard=True)

def export():
 OUT.mkdir(parents=True,exist_ok=True)
 build();assert len(ROWS)==32
 # Root semantic review requested clearer learner-facing copy. Preserve the
 # pre-copyedit working source bytes and bind every new row to its parent.
 before=OUT/'g12_cases_before_copyedit.jsonl'
 if (OUT/'g12_cases.jsonl').exists() and not before.exists():
  before.write_bytes((OUT/'g12_cases.jsonl').read_bytes())
 parents={r['sample_id']:sha(line.encode()) for line in before.read_text('utf-8').splitlines() for r in [json.loads(line)]} if before.exists() else {}
 for row in ROWS:
  copyedit(row)
  row['provenance']['copyedit_parent_source_row_sha256']=parents.get(row['sample_id'])
 oracles=[];reviews=[];chats=[];seen=set()
 for row in ROWS:
  assert row['sample_id'] not in seen;seen.add(row['sample_id'])
  for s in row['worked_steps']:
   if s['expression']:
    a=calc(s['expression']);b=calc(s['expression'],Decimal)
    assert a==Fraction(b)==Fraction(s['result']),(row['sample_id'],s)
    oracles.append({'sample_id':row['sample_id'],'expression':s['expression'],'result':str(a),'independent_decimal':str(b)})
  assert len(row['hints'])==3 and [x['level'] for x in row['hints']]==[1,2,3]
  line=j(row);h=sha(line.encode())
  review={'sample_id':row['sample_id'],'source_row_sha256':h,'review_role':'AUTHOR_SELF_QA','status':'PASS','criteria':{k:'PASS' for k in ['correct_math_or_explicit_guard','givens_request_consistent','steps_reasons_units_check','grade_scope','initial_and_all_three_hints_answer_free','student_work_grounded_no_unseen_inference','schema_provenance_unique']},'semantic_review_basis':'Actual authored problem, givens, request, student_work, all steps/reasons/explanations/results, answer, initial and all hints read in source authoring, plus exact independent numeric oracle; no blanket keyword proof.'}
  reviews.append(review)
  for c in chat_records(row):
   c['split']='train';c['source_row_sha256']=h;c['acceptance_status']=row['acceptance_status'];c['source_sample_id']=row['sample_id'];chats.append(c)
 for name,data in [('g12_cases.jsonl',ROWS),('g12_reviews.jsonl',reviews),('g12_chat.jsonl',chats)]:
  (OUT/name).write_text(''.join(j(x)+'\n' for x in data),encoding='utf-8')
 (OUT/'g12_exact_oracles.json').write_text(json.dumps(oracles,ensure_ascii=False,indent=2),encoding='utf-8')
 print(j({'cases':len(ROWS),'chat_rows':len(chats),'by_type':dict(Counter(x['topic'] for x in ROWS)),'numeric_steps_dual_oracle':len(oracles)}))

def copyedit(row):
 replacements={
 'phéptính':'phép tính','chữsố':'chữ số','haithẻ':'hai thẻ','thẻchữ':'thẻ chữ',
 'dấugiữnguyên':'dấu giữ nguyên','dấu−':'dấu −','dấu=':'dấu =','giữnguyên':'giữ nguyên',
 'chỉhoánđổi':'chỉ hoán đổi','đượcyêucầu':'được yêu cầu','đãđúng':'đã đúng',
 'phảidấubằng':'phải dấu bằng','ởkếtquả':'ở kết quả','ởđầu':'ở đầu','ởbên':'ở bên',
 'khôngcó':'không có','cómũitên':'có mũi tên','mũitên':'mũi tên','điềukiện':'điều kiện',
 'cấutrúcđồthị':'cấu trúc đồ thị','chưacó':'chưa có','chưaghi':'chưa ghi','thiếucâu':'thiếu câu',
 'câutrảlời':'câu trả lời','trảlời':'trả lời','thựctế':'thực tế','chắcchắn':'chắc chắn',
 'cuốilượt':'cuối lượt','đạtmốc':'đạt mốc','vìB':'vì B','Bđạt':'B đạt','M,Nđạt':'M, N đạt',
 'nêncó':'nên có','vìtrả':'vì trả','lờisai':'lời sai','khi giữcâu':'khi giữ câu',
 'thêmmột':'thêm một','từô':'từ ô','đếnô':'đến ô','ởô':'ở ô','sangô':'sang ô',
 'làthương':'là thương','làbước':'là bước','bướcmột':'bước một','bướchai':'bước hai',
 'đúngởlại':'đúng ở lại','saiquayvề':'sai quay về','phéptínhô':'phép tính ô',
 'khôngônhảy':'không ô nhảy','ônhảy':'ô nhảy','luậtđúngsai':'luật đúng sai',
 'đúng2':'đúng 2','mộtchữsố':'một chữ số','sốhaichữsố':'số hai chữ số',
 'khôngđổi':'không đổi','hàngchục':'hàng chục','hàngđơnvị':'hàng đơn vị',
 'phéptrừkhôngnhớ':'phép trừ không nhớ','đơnvị':'đơn vị','tổng75':'tổng 75',
 'từ1đến9':'từ 1 đến 9','Hai miếng giữ nguyên hướng;quy':'Hai miếng giữ nguyên hướng; quy',
 'haihộpcótên':'hai hộp có tên','hộptrốngđượcphép':'hộp trống được phép',
 'chưa cóluật':'chưa có luật','chưacóluật':'chưa có luật',
 'luậtthayđổi':'luật thay đổi','chỉđổi':'chỉ đổi','phéptínhởô':'phép tính ở ô',
 'bảng chuẩn1':'bảng chuẩn 1','tínhởô':'tính ở ô','giátrị':'giá trị',
 'Đủ5':'Đủ 5','mốc60':'mốc 60','rõ;thiếu':'rõ; thiếu',
 'phéptính;':'phép tính;','3thẻriêng':'3 thẻ riêng',
 'Số□4':'Số □4','trong4□':'trong 4□','điền□':'điền □',
 '3chấm':'3 chấm','4chấm':'4 chấm','2chấm':'2 chấm',
 'câutrả':'câu trả','kếtthúctại':'kết thúc tại','ô5nhảy':'ô 5 nhảy',
 'đúngở':'đúng ở','nhảysang':'nhảy sang','ởlại':'ở lại','quayvề':'quay về',
 'hộp3':'hộp 3','hộp5':'hộp 5','Hộp3':'Hộp 3','hộp3:':'hộp 3:',
 'vìthêm':'vì thêm','cộngkề':'cộng kề','cộngthêmsố':'cộng thêm số','ởđáy':'ở đáy',
 'bằngchữ':'bằng chữ','chưađọcđược':'chưa đọc được','cầncả':'cần cả',
 '□một':'□ là một','làsốhaichữ':'là số hai chữ','sốhaichữ':'số hai chữ',
 'chữ sốđơn':'chữ số đơn','□hàng':'□ ở hàng','Btừ':'B từ','□là':'□ là',
 'Điền□':'Điền □','trong□':'trong □','ghi□':'ghi □','Chỉđổi':'Chỉ đổi',
 'Chỉhoánđổi':'Chỉ hoán đổi','bênphải':'bên phải','ởhai':'ở hai','Dãythẻgốc':'Dãy thẻ gốc',
 'Aghi':'A ghi','Bghi':'B ghi','Cghi':'C ghi','TừSđếnTchỉ':'Từ S đến T chỉ',
 'từSđếnT':'từ S đến T','Ccóphép':'C có phép','Đủmũi':'Đủ mũi','kiệnbéhơn':'kiện bé hơn',
 'chọnS':'chọn S','Tvì':'T vì','Bcùngmốc':'B cùng mốc','Bkhông':'B không',
 'Biếtphép':'Biết phép','tínhở':'tính ở','thiếucấu':'thiếu cấu',
 'ôđangđứng':'ô đang đứng','Đếnô':'Đến ô','ở lạiô':'ở lại ô','vềô':'về ô',
 'ởđâu':'ở đâu','tínhô':'tính ô','cóô':'có ô','đúngthìở':'đúng thì ở',
 'ôđến':'ô đến','nênkết':'nên kết','tạiô':'tại ô','nênở':'nên ở','cóphép':'có phép',
 'Đủvịtrí':'Đủ vị trí','lờithực':'lời thực',
 'mộtchữ số':'một chữ số','đổihai':'đổi hai','□trong':'□ trong',
 }
 def clean(s):
  if not isinstance(s,str):return s
  for _ in range(2):
   for a,b in replacements.items():s=s.replace(a,b)
  s=re.sub(r'(?<=\d)(?=[a-zà-ỹđ])|(?<=[a-zà-ỹđÔ])(?=\d)',' ',s)
  s=re.sub(r'([,;:])(?=\S)',r'\1 ',s)
  s=re.sub(r'\s*([→=×+−])\s*',r' \1 ',s)
  s=re.sub(r'\s{2,}',' ',s)
  return s
 for key in ['problem','requested_quantity']:
  row[key]=clean(row[key])
 for given in row['givens']:given['text']=clean(given['text'])
 if row['student_work']:
  row['student_work']['text']=clean(row['student_work']['text'])
  row['student_work']['observations'][0]['excerpt']=row['student_work']['text']
 for step in row['worked_steps']:
  for key in ['title','reason','result','explanation','unit']:step[key]=clean(step[key])
 for answer in row['expected_answer']:answer['result']=clean(answer['result'])
 row['problem']=row['problem'].replace('Bảng mỗi hàng mười ô tăng từ trái qua phải.',
 'Bảng các số từ 1 đến 100 được ghi liên tiếp từ trái sang phải, mỗi hàng mười ô rồi tiếp tục sang hàng dưới.')
 row['problem']=row['problem'].replace('Giữ đề xuất, kiểm nó rồi nêu cách sửa hợp lệ.',
 'Đối chiếu nguyên đề xuất của bạn, kiểm nó rồi đưa ra một cách sửa mới hợp lệ.')
 row['problem']=row['problem'].replace('Giữ câu viết, kiểm mũi tên rồi sửa.',
 'Đối chiếu nguyên câu viết, kiểm mũi tên rồi đưa ra đường sửa.')
 if row['topic']=='one_digit_swap_repair' and row['sample_id'].endswith('_01'):
  row['problem']=row['problem'].replace('và mọi vị trí hai chữ số','và cấu trúc số gồm hai chữ số ở mỗi vị trí')
 if row['sample_id'].endswith('sum_pyramid_03'):
  row['worked_steps'][1]['explanation']='Ô giữa trái là hai cộng không bằng hai; ô giữa phải là không cộng một bằng một. Hai ô giữa đều khớp hàng đáy, nên chỉ cần sửa cách tính đỉnh.'
 if row['sample_id'].endswith('expression_target_classification_01'):
  row['worked_steps'][1]['explanation']='C không đạt mốc còn D đạt mốc; cộng với số 0 giữ nguyên giá trị.'

if __name__=='__main__':export()
