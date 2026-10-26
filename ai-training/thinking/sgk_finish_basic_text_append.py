"""Fourteen finite original data drafts, seven explicit master branches only."""
from pathlib import Path
from fractions import Fraction
from decimal import Decimal
from itertools import product,combinations
from collections import Counter
import json,re
import sgk_finish_g1_text_append as common
from exhaustive_primary_math import chat_records,expression_group
HERE=Path(__file__).parent
OUT=HERE/'cloud_publication/sgk_finish_20261020/remaining_basic_text'
SNAP=OUT/'mapping_snapshot.json'
snapshot=json.loads(SNAP.read_text('utf-8'))
common.SNAP=SNAP;common.snapshot=snapshot;common.MASTERS={m['master_id']:m for m in snapshot['masters']};common.ROWS=[]
s,hs,dump,sha=common.s,common.hs,common.dump,common.sha
ROWS=common.ROWS
def add(master,branch,grade,problem,givens,request,steps,answers,hints,model,decision,student=None):
 common.add(master,branch,problem,givens,request,steps,answers,hints,model,decision,student)
 r=ROWS[-1];r['sample_id']='sgk_finish_basic_20261020_'+branch;r['case_group_id']=r['sample_id']+'_group';r['grade']=grade;r['curriculum_assignment']['grade']=grade;r['curriculum_assignment']['number_limit']=100 if grade==1 else None
 r['coverage']['candidate_ids']=common.MASTERS[master]['candidate_ids'];r['coverage']['master_branch']='G1_SIMPLE_FINITE_WEIGHTED_GRAPH_ONLY' if master=='finite_route_total_optimization' else 'EXPLICIT_FINITE_TEXT_RELATION'
 r['coverage']['pending_other_branches']=['G5 network shortest route then round-trip time'] if master=='finite_route_total_optimization' else []
 if master=='finite_route_total_optimization':
  r['nearest_source_comparison']['actual_page_receipts']=[x for x in r['nearest_source_comparison']['actual_page_receipts'] if x.get('grade')==1]
  r['coverage']['candidate_ids']=['G1V2_ROUTE_TOTAL_LENGTH_COMPARISON'];r['coverage']['pending_candidate_ids']=['g5_candidate_shortest_route']
 if master=='balance_order_substitution_chain':r['coverage']['candidate_ids']=['g3_balance_relation_chain'];r['coverage']['other_grade_aliases_not_claimed_closed']=['balance_orientation_order','g5_candidate_balance_consistency']

def author():
 m='role_specific_equation_pool'
 add(m,'role_pool_all_additions',1,'Có ba hộp số dùng để chọn số cho phép cộng a+b=c. Hộp đầu a có 2, 4; hộp thứ hai b có 1, 3; hộp kết quả c có 3, 7. Mỗi dòng chọn đúng một số từ đúng hộp của nó. Các số được dùng lại giữa các dòng; không chuyển số sang hộp khác. Liệt kê mọi phép cộng đúng.',['a:{2,4};b:{1,3};c:{3,7}','Dùng lại giữa dòng;không đổi hộp'],'Mọi phép theo vai trò hộp',[
 s('Thử đủ bốn cặp số hạng','Hai lựa chọn đầu ghép hai lựa chọn sau tạo bốn cặp.','2+1; 2+3; 4+1; 4+3','Không cần dùng hết số cùng lúc; mỗi phép là một lần chọn độc lập.'),s('Đối chiếu với hộp kết quả','Một tổng chỉ hợp lệ nếu chính hộp kết quả chứa nó.','2+1=3; 4+3=7','Hai cặp còn lại đều cho năm, hộp kết quả không có năm.'),s('Kiểm vai trò và đầy đủ','Đúng số học chưa đủ nếu đổi vị trí hộp.','Hai phép đã liệt kê','Ba không ở hộp đầu nên không thêm 3+4=7, dù đúng số học. Đã kiểm đủ bốn cặp.')],[('Mọi phép','2+1=3; 4+3=7','')],hs('Giữ mỗi số trong đúng vai trò của hộp.','Thử từng cặp số hạng rồi tìm tổng trong hộp kết quả.','Đẳng thức đúng có đáp ứng đúng hộp và luật dùng lại không?'),dict(kind='rolepool',A=[2,4],B=[1,3],C=[3,7],op='+',expected=[[2,1,3],[4,3,7]]),'Role-restricted Cartesian product with row reuse; not shared inventory assignment or unrestricted card permutation.')
 add(m,'role_pool_subtraction_error',1,'Lập a−b=c từ ba hộp: a có 9, 7; b có 2, 4; c có 3, 5. Mỗi dòng lấy một số đúng hộp, dùng lại được giữa các dòng. Bạn viết 9−4=5 và 7−3=4. Kiểm hai dòng rồi liệt kê mọi phép đúng theo luật.',['a9,7;b2,4;c3,5','Mỗi vai trò đúng hộp;dùng lại giữa dòng'],'Kiểm và liệt kê phép trừ hợp lệ',[
 s('Kiểm hai dòng đã viết','Phép trừ đúng vẫn có thể dùng sai hộp.','9−4=5 hợp lệ; 7−3=4 sai hộp','Ba không có trong hộp b, bốn không trong hộp c, dù bảy bớt ba bằng bốn.'),s('Thử các cặp đúng hai hộp đầu','Giữ số bị trừ và số trừ đúng vai trò.','9−2=7;9−4=5;7−2=5;7−4=3','Chỉ dòng cho kết quả bảy bị loại vì hộp c không có bảy.'),s('Kiểm danh sách cuối','Tất cả bốn cặp đã xét, ba kết quả thuộc hộp c.','9−4=5;7−2=5;7−4=3','Kết quả năm được dùng ở hai dòng vì đề cho dùng lại; không bỏ một phép chỉ vì tổng hợp dùng số năm hai lần.')],[('Mọi phép','9−4=5;7−2=5;7−4=3','')],hs('Kiểm từng số trong dòng viết thuộc đúng hộp nào.','Xét các cặp đúng vai trò rồi đối chiếu kết quả.','Áp dụng luật dùng lại giữa các dòng thay vì tự đặt giới hạn mới.'),dict(kind='rolepool',A=[9,7],B=[2,4],C=[3,5],op='-',expected=[[9,4,5],[7,2,5],[7,4,3]]),'Subtraction orientation and wrong-role synthetic feedback; independent row reuse permits equal outputs.',student='9−4=5 và 7−3=4.')
 m='arrival_schedule_eligibility'
 add(m,'arrival_at_start_allowed',1,'Buổi sáng hội chợ có ba buổi bắt đầu: vẽ lúc 8 giờ, kể chuyện lúc 9 giờ, xếp hình lúc 10 giờ. Lan đến đúng 9 giờ sáng. Quy định được dự nếu đến trước hoặc đúng lúc bắt đầu; đến sau thì không được vào. Không cần thời gian đi giữa các buổi và chỉ hỏi từng buổi riêng. Lan đủ điều kiện dự những buổi nào?',['Sáng:vẽ8,kể9,xếp10;đến9','Đến≤giờ bắt đầu;hỏi riêng không thời lượng'],'Các buổi đủ điều kiện',[
 s('So buổi trước giờ đến','Đến chín là sau khi buổi tám bắt đầu.','Không dự buổi vẽ','Không đổi luật thành được vào muộn.'),s('Kiểm trường hợp đúng giờ','Quy định có tính cả đến đúng giờ bắt đầu.','Được kể chuyện và xếp hình','Đúng chín kịp kể chuyện; chín trước mười nên kịp xếp hình.'),s('Kiểm phạm vi câu trả lời','Đề chỉ xét điều kiện vào từng buổi, không hỏi lịch dự đồng thời.','Hai buổi đạt điều kiện vào','Không suy thời lượng hay khả năng dự cả hai trọn vẹn khi chưa có dữ kiện đó.')],[('Buổi đủ điều kiện','Kể chuyện và xếp hình','')],hs('So thời điểm đến với giờ bắt đầu từng buổi.','Đọc quy định có tính trường hợp đúng giờ không.','Chỉ kết luận điều kiện được hỏi từ dữ kiện đã có.'),dict(kind='arrival',arrival=9,events={'vẽ':8,'kể chuyện':9,'xếp hình':10},strict=False,expected=['kể chuyện','xếp hình']),'Inclusive start threshold over several events, separated from missing duration/overlap inference.')
 add(m,'arrival_strict_before',1,'Các buổi chiều bắt đầu lần lượt: nhạc lúc 2 giờ, ghép tranh lúc 3 giờ, gấp giấy lúc 4 giờ. Bình đến đúng 3 giờ chiều. Luật chỉ cho vào nếu đã đến trước giờ bắt đầu, không cho vào khi đến đúng giờ. Bạn ghi “ghép tranh và gấp giấy đều được”. Kiểm danh sách theo luật, xét từng buổi riêng.',['Chiều:nhạc2,ghép3,gấp4;đến3','Phải đến trước,không gồm bằng'],'Danh sách sửa với cận chặt',[
 s('Kiểm buổi bằng giờ đến','Luật yêu cầu trước, khác trước hoặc bằng.','Ghép tranh không đạt','Đến đúng ba không là trước ba, nên dòng viết chọn ghép tranh chưa đúng.'),s('Kiểm hai buổi còn lại','Cùng buổi chiều nên so trực tiếp các số giờ.','Nhạc không đạt; gấp giấy đạt','Ba sau hai nên nhạc đã bắt đầu; ba trước bốn nên gấp giấy đáp ứng.'),s('Kiểm đủ ba buổi','Mỗi buổi đã so với cùng thời điểm đến và cùng luật chặt.','Chỉ gấp giấy','Không thêm thời gian đi hoặc sửa giờ để giữ lựa chọn ban đầu.')],[('Buổi đủ điều kiện','Chỉ gấp giấy','')],hs('Đọc từ trước trong luật theo đúng nghĩa chặt.','Kiểm riêng buổi bắt đầu đúng giờ đến.','Rà lại cả buổi trước, bằng và sau giờ đến.'),dict(kind='arrival',arrival=3,events={'nhạc':2,'ghép tranh':3,'gấp giấy':4},strict=True,expected=['gấp giấy']),'Strict boundary and exact supplied student list, contrasting inclusive case by rule rather than numeric substitution.',student='Ghép tranh và gấp giấy đều được.')
 m='two_group_transfer_then_compare'
 add(m,'transfer_equalizes',1,'Khay A có 12 bút, khay B có 8 bút. Chuyển đúng 2 bút từ A sang B, không thêm hay bỏ bút ra ngoài. Tìm lượng mỗi khay sau chuyển, rồi so sánh và kiểm tổng.',['A12,B8;chuyển2 A→B;không mất/thêm'],'Hai lượng sau và so sánh',[
 s('Cập nhật nơi cho','Hai bút rời A nên bớt ở A.',10,'A còn mười bút.','12-2','bút'),s('Cập nhật nơi nhận','Cùng hai bút đó vào B nên thêm ở B.',10,'B có mười bút; không chỉ sửa một khay.','8+2','bút'),s('So và kiểm tổng bảo toàn','Hai lượng mới bằng nhau và tổng không đổi.',20,'Mười cộng mười bằng hai mươi, bằng mười hai cộng tám ban đầu. A và B bằng nhau.','10+10','bút')],[('A',10,'bút'),('B',10,'bút'),('So sánh','Bằng nhau','')],hs('Theo dõi cả nơi cho và nơi nhận cùng một lần chuyển.','Lượng rời bên này đi vào bên kia.','So sau khi cập nhật cả hai và kiểm tổng không đổi.'),dict(kind='transfer',A=12,B=8,k=2,expected=[10,10]),'Two coupled opposite updates and equality; not sequential operations in one container.')
 add(m,'transfer_reverses_order',1,'Hộp Đỏ có 14 thẻ, hộp Xanh có 10 thẻ. Chuyển 3 thẻ từ Đỏ sang Xanh; không có thẻ nào ra ngoài. Bạn viết “Đỏ còn 11, Xanh vẫn 10 nên Đỏ nhiều hơn”. Giữ câu viết, sửa lượng sau chuyển và tìm bên nhiều hơn cùng số thẻ hơn.',['Đỏ14,Xanh10;chuyển3 Đỏ→Xanh','Không thêm/mất;student không cậpnhật nhận'],'Sửa hai trạng thái và hướng so sánh',[
 s('Kiểm phần nơi cho','Bớt ba ở Đỏ là đúng.',11,'Đỏ còn mười một đúng như câu viết.','14-3','thẻ'),s('Sửa nơi nhận','Ba thẻ từ Đỏ phải được thêm vào Xanh.',13,'Xanh thành mười ba, không còn mười.','10+3','thẻ'),s('So lượng mới và kiểm','Hướng nhiều hơn có thể đổi sau một lần chuyển.',2,'Xanh hơn Đỏ hai thẻ. Mười một cộng mười ba bằng hai mươi bốn, khớp tổng cũ; câu so sánh ban đầu dùng lượng nhận chưa cập nhật.','13-11','thẻ')],[('Đỏ',11,'thẻ'),('Xanh',13,'thẻ'),('Bên hơn','Xanh hơn Đỏ 2 thẻ','')],hs('Giữ phần tính đúng trong câu viết và kiểm phần còn thiếu.','Bên nhận phải thay đổi cùng lúc với bên cho.','Chỉ so hai lượng ở cùng thời điểm sau chuyển.'),dict(kind='transfer',A=14,B=10,k=3,expected=[11,13]),'Order reversal and grounded partial-correct-work feedback; no inferred image error.',student='Đỏ còn 11, Xanh vẫn 10 nên Đỏ nhiều hơn.')
 m='finite_route_total_optimization'
 add(m,'route_global_minimum',1,'Bản đồ chữ chỉ có các đường một chiều và độ dài: S→A 2 m, A→T 9 m; S→B 4 m, B→T 3 m; S→C 3 m, C→T 6 m. Không có đường khác, chỉ đi từ S tới T một lượt. Chọn mọi đường ngắn nhất, tính tổng từng đường để chứng minh.',['Ba nhánh đầy đủ;SA2,AT9,SB4,BT3,SC3,CT6 mét','Một chiều,không đường khác,một lượt'],'Đường ngắn nhất qua mọi tổng',[
 s('Tính nhánh qua A','Đường nối tiếp cộng cả hai chặng.',11,'S→A→T dài mười một mét.','2+9','m'),s('Tính nhánh qua B và C','Phải xét cả nhánh còn lại trước khi kết luận ít nhất.','B:7 m; C:9 m','B có bốn cộng ba bằng bảy; C có ba cộng sáu bằng chín.'),s('So toàn bộ miền đường','Có đúng ba nhánh nên so ba tổng là đã đủ.','Chỉ S→B→T, dài 7 m','Bảy nhỏ hơn chín và mười một. Chọn cạnh đầu nhỏ nhất tới A sẽ không cho tổng nhỏ nhất.')],[('Đường ngắn nhất','S→B→T',''),('Độ dài',7,'m')],hs('Liệt kê các đường hoàn chỉnh từ đầu tới đích.','Cộng đủ các chặng của từng đường trước khi so.','Một đoạn đầu ngắn có bảo đảm cả đường ngắn nhất không?'),dict(kind='weighted_routes',edges=[['S','A',2],['A','T',9],['S','B',4],['B','T',3],['S','C',3],['C','T',6]],expected_min=7,expected_routes=[['S','B','T']]),'G1 simple branch only: compare all finite path weights; no G5 network/time/round-trip closure.')
 add(m,'route_tied_minima_error',1,'Chỉ có đường một chiều S→P 3 m, P→T 4 m; S→Q 5 m, Q→T 2 m; S→R 2 m, R→T 8 m. Không có nối khác. Chỉ hỏi chuyến đi một lượt từ S tới T. Bạn ghi “chỉ S→P→T ngắn nhất”. Kiểm mọi đường và sửa từ chỉ nếu cần.',['SP3,PT4,SQ5,QT2,SR2,RT8 mét;chỉ3nhánh','Một chiều,một lượt'],'Mọi đường đồng ngắn nhất',[
 s('Giữ tổng đường đã chọn','P tạo đường hợp lệ và có hai chặng.',7,'Ba cộng bốn bằng bảy mét.','3+4','m'),s('Kiểm các đối thủ đầy đủ','Một đường đạt độ dài nào đó chưa chứng minh duy nhất.','Q:7 m; R:10 m','Năm cộng hai bằng bảy, hai cộng tám bằng mười.'),s('Sửa phạm vi từ chỉ','Có hai đường bằng độ dài nhỏ nhất.','S→P→T và S→Q→T cùng ngắn nhất','Cả hai đều bảy mét, đều ngắn hơn đường qua R. Không thêm đường ghép giữa các nhánh vì đề không có nối.')],[('Đường ngắn nhất','S→P→T và S→Q→T',''),('Độ dài',7,'m')],hs('Kiểm các đường còn lại dù đường bạn chọn hợp lệ.','Phân biệt một đường đạt cực trị với đường duy nhất đạt.','Giữ mọi nhánh có tổng cùng nhỏ nhất.'),dict(kind='weighted_routes',edges=[['S','P',3],['P','T',4],['S','Q',5],['Q','T',2],['S','R',2],['R','T',8]],expected_min=7,expected_routes=[['S','P','T'],['S','Q','T']]),'Tie of global route totals and student uniqueness correction; no physical or G5 branch claim.',student='Chỉ S→P→T ngắn nhất.')
 m='bounded_factor_pair_enumeration'
 add(m,'factor_pairs_unordered',3,'Có 24 nút cần xếp thành hình chữ nhật đầy đủ hàng. Số hàng và số nút mỗi hàng đều là số nguyên từ 2 đến 12, kể cả hai mốc. Chỉ liệt kê dạng với số hàng không lớn hơn số nút mỗi hàng, để hai cách quay đổi hàng và cột không tính hai lần. Tìm mọi cặp và kiểm đầy đủ.',['Tích24;mỗi số2..12;sốhàng≤mỗi hàng','Quay đổi không tính lại'],'Mọi cặp không kể thứ tự',[
 s('Giới hạn số hàng cần thử','Số hàng không lớn hơn số mỗi hàng, nên nếu hàng từ năm thì tích ít nhất hai mươi lăm.','Chỉ thử hàng 2, 3, 4','Đã dùng điều kiện giới hạn để không bỏ cặp sau bốn.'),s('Tìm đối tác chia hết','Mỗi số hàng phải chia hết số nút toàn bộ.','(2,12), (3,8), (4,6)','Hai mươi bốn chia hai,ba,bốn lần lượt cho mười hai,tám,sáu; mọi số đều trong khoảng cho phép.'),s('Kiểm tích và quy ước','Từng cặp khôi phục hai mươi bốn, không ghi cặp quay lại.',24,'Bốn nhân sáu bằng hai mươi bốn; hai nhân mười hai và ba nhân tám cũng vậy. Không thêm (6,4) vì số hàng vượt số mỗi hàng.','4*6','nút')],[('Cặp hàng,mỗi hàng','(2,12);(3,8);(4,6)','')],hs('Giữ cận của cả hai số và quy tắc có tính đổi thứ tự không.','Thử số hàng rồi tìm số mỗi hàng bằng chia hết.','Giải thích vì sao những số hàng còn lại không tạo cặp mới.'),dict(kind='factor',target=24,low=2,high=12,ordered=False,expected=[[2,12],[3,8],[4,6]]),'Both unknown factors with finite lower/upper bounds and no rotation duplicates; not one-factor inverse.')
 add(m,'factor_pairs_ordered_bounds',3,'Một bảng có 18 ô, số hàng và số ô mỗi hàng đều từ 2 đến 9. Hàng và cột có vai trò khác nhau: 2 hàng mỗi hàng 9 ô khác 9 hàng mỗi hàng 2 ô. Chỉ nhận bảng có số hàng nhiều hơn 3. Liệt kê mọi cặp (số hàng, số ô mỗi hàng).',['Tích18;mỗi số2..9;sốhàng>3','Có thứ tự hàng/cột'],'Các cặp có thứ tự và cận riêng',[
 s('Lập các cặp theo số hàng','Xét hàng từ bốn đến chín và chỉ giữ khi mười tám chia hết.','Hàng 6 hoặc 9','Hàng bốn,năm,bảy,tám không cho số ô mỗi hàng nguyên.'),s('Tính số ô mỗi hàng','Tổng số ô chia số hàng cho lượng mỗi hàng.','(6,3), (9,2)','Hai cặp đều có số mỗi hàng trong hai đến chín.'),s('Kiểm cận riêng và thứ tự','Các cặp (2,9),(3,6) đúng tích nhưng không vượt ba hàng.',18,'Chín nhân hai bằng mười tám; sáu nhân ba cũng vậy. Không thêm cặp đảo bị loại bởi điều kiện số hàng.','9*2','ô')],[('Các cặp','(6,3);(9,2)','')],hs('Phân biệt điều kiện chung cho hai số với điều kiện chỉ số hàng.','Xét từng số hàng trong phạm vi còn lại.','Kiểm cặp đảo có còn đáp ứng cận riêng không.'),dict(kind='factor',target=18,low=2,high=9,ordered=True,min_first_exclusive=3,expected=[[6,3],[9,2]]),'Ordered roles plus asymmetric constraint; distinct from unordered rotation quotient.')
 m='bounded_inventory_target_sum'
 add(m,'inventory_fixed_cardinality',3,'Có đúng bốn quả cân riêng mang nhãn A:2 kg, B:3 kg, C:5 kg, D:6 kg. Chọn đúng hai quả khác nhau để tổng bằng 8 kg, không dùng lại quả nào. Liệt kê mọi cặp nhãn, đổi thứ tự hai quả không tính cách mới.',['A2,B3,C5,D6 kg;đúng2quả;tổng8','Mỗi quả một lần,không phân thứtự'],'Mọi cặp hai quả đạt đích',[
 s('Liệt kê mọi cặp khác nhau','Bốn vật chọn hai không kể thứ tự cho sáu cặp.','AB, AC, AD, BC, BD, CD','Không dùng AA hay ghi cả AB lẫn BA.'),s('Tính và lọc tổng','Từng cặp phải có đúng hai quả và đúng tám kg.','AD và BC','AB năm; AC bảy; AD tám; BC tám; BD chín; CD mười một kg.'),s('Kiểm nguồn và tính đầy đủ','Đã xét đủ sáu cặp của kho bốn quả.','A,D hoặc B,C','Không thêm quả ba thứ hai hay ghép ngoài kho. Hai cặp đều có tổng tám và dùng hai nhãn khác nhau.')],[('Cặp','A,D hoặc B,C','')],hs('Đếm theo các vật có nhãn, giữ đúng số lượng cần chọn.','Xét các cặp khác nhau rồi tính tổng từng cặp.','Kiểm không lặp vật, không lặp thứ tự và không thiếu cặp.'),dict(kind='subset',items={'A':2,'B':3,'C':5,'D':6},target=8,count=2,expected=[['A','D'],['B','C']]),'Fixed-cardinality finite inventory subset, not adding all weights or unrestricted positive distribution.')
 add(m,'inventory_no_extra_duplicate',3,'Kho bình có đúng A:2 l, B:2 l, C:5 l, D:7 l; A và B là hai bình riêng. Chỉ được chọn các bình có thật, mỗi bình nhiều nhất một lần, có thể chọn số bình bất kỳ. Không đổ bớt trong bình. Muốn đủ đúng 6 l. Bạn viết “chọn ba bình 2 l”. Kiểm có cách chọn nào không.',['A2,B2,C5,D7 l;dùng mỗi bình≤1','Tổng6;không đổ bớt;không bình khác'],'Tính khả thi dưới giới hạn kho',[
 s('Kiểm lời chọn so với kho','Kho chỉ có hai bình dung tích hai lít.','Không có ba bình 2 l','Phép cộng ba phần hai có thể bằng sáu nhưng cần một bình không có trong danh sách.'),s('Loại bình vượt hoặc làm lẻ phần thiếu','D riêng đã vượt sáu; C năm cần thêm một nhưng không có bình một.','Không chọn D hay C để đạt sáu','D không thể bớt nước; ghép C với bất kỳ bình còn lại đều vượt sáu.'),s('Kiểm phần kho còn lại','Chỉ A và B thì nhiều nhất hai cộng hai.',4,'Hai bình hai chỉ được bốn lít, chưa đủ sáu. Đã xét hết trường hợp dùng/không dùng C,D, nên không có cách chọn.','2+2','l')],[('Kết luận','Không có cách chọn đúng 6 l theo kho','')],hs('Kiểm số vật thật sự có trước khi lập tổng.','Không tự làm xuất hiện thêm bình hoặc đổ bớt.','Chia trường hợp theo bình lớn rồi kiểm phần kho nhỏ còn lại.'),dict(kind='subset',items={'A':2,'B':2,'C':5,'D':7},target=6,count=None,expected=[]),'Bounded multiplicity and infeasibility; no unbounded coin-change assumption.',student='Chọn ba bình 2 l.')
 m='balance_order_substitution_chain'
 add(m,'balance_transitive_substitution',3,'Cân hai đĩa đã chỉnh thăng bằng khi trống. Quy ước đĩa thấp hơn là bên nặng hơn. Các quả cầu cùng loại có khối lượng bằng nhau và dương. Lần 1: một hộp X cân bằng hai cầu đỏ R. Lần 2: một cầu R bên trái thấp hơn một cầu xanh G bên phải. Lần 3: một cầu G cân bằng hộp Y. So khối lượng X với Y và giải thích qua các quan hệ, không cần tìm số gam.',['Cân chuẩn;thấp=nặng;khối lượngdương','X=R+R;R>G;G=Y;đồng loại bằng nhau'],'So sánh qua thế và bắc cầu',[
 s('Đọc hướng cân','Đĩa trái thấp ở lần hai nên R nặng hơn G.','R > G','Không đảo dấu vì nhìn đĩa cao hơn.'),s('Thế vật bằng nhau','G và Y cân bằng nên thay G bằng Y trong so sánh.','R > Y','Vậy một cầu đỏ đã nặng hơn Y.'),s('Gộp thêm khối lượng dương và kiểm','X bằng hai R, nên nặng hơn một R rồi nặng hơn Y.','X nặng hơn Y','Chuỗi X > R > Y nhất quán với cả ba bản ghi; không bịa khối lượng gam từng vật.')],[('So sánh','X nặng hơn Y','')],hs('Dùng đúng quy ước hướng đĩa để đọc quan hệ.','Thay các vật bằng khối lượng nhau nhưng giữ danh tính loại cầu.','Kiểm chuỗi so sánh và điều kiện khối lượng dương.'),dict(kind='balance_order',expected='X>Y'),'Explicit pan direction, substitution and transitivity; equality-only source does not supply this chain.')
 add(m,'balance_common_object_cancellation',3,'Cân đã chỉnh đúng, đĩa thấp nặng hơn. Các vật cùng tên là cùng loại khối lượng không đổi. Lần 1, đĩa trái có A và C, đĩa phải có B và C; đĩa trái cao hơn. Lần 2, B cân bằng D. Học sinh viết “A nặng hơn D vì đĩa trái cao hơn”. Hãy kiểm, so A với D, không đoán số đo.',['Lần1:A+C trái cao hơn B+C phải','Lần2:B=D;C giống nhau;cao=nhẹ'],'Sửa hướng cân và bỏ phần chung',[
 s('Đọc hướng theo quy ước','Trái cao hơn nghĩa là tổng bên trái nhẹ hơn.','A+C nhẹ hơn B+C','Câu viết dùng cao hơn để kết luận nặng hơn là đảo hướng.'),s('Bỏ phần có khối lượng giống nhau','Hai bên đều có đúng một vật C cùng khối lượng.','A nhẹ hơn B','Bỏ cùng phần C giữ chiều so sánh, không phải tự lấy mất vật ở riêng một bên.'),s('Thế và kiểm kết luận','B và D bằng nhau nên so A với D cùng chiều như với B.','A nhẹ hơn D','Thế D vào vị trí B khôi phục quan hệ A+C nhẹ hơn D+C, phù hợp bản ghi trái cao. Không nêu số gam chưa biết.')],[('So sánh','A nhẹ hơn D','')],hs('Kiểm cao và thấp có nghĩa gì theo quy ước đã cho.','Tìm phần giống nhau có mặt ở cả hai đĩa.','Sau khi thế vật bằng nhau, kiểm chiều so sánh còn đúng không.'),dict(kind='balance_cancel',expected='A<D'),'Common-object cancellation then equality substitution with grounded orientation-error correction.',student='A nặng hơn D vì đĩa trái cao hơn.')

def routes(edges):
 out=[]
 def go(u,p,total):
  if u=='T':out.append(dict(route=p,total=total));return
  for a,b,w in edges:
   if a==u and b not in p:go(b,p+[b],total+w)
 go('S',['S'],0);return out
def oracle(m):
 k=m['kind']
 if k=='rolepool':
  tests=[];valid=[]
  for a,b,c in product(m['A'],m['B'],m['C']):
   computed=a+b if m['op']=='+' else a-b;ok=computed==c;tests.append([a,b,c,ok])
   if ok:valid.append([a,b,c])
  assert valid==m['expected'];return dict(all_role_triples=tests,valid=valid)
 if k=='arrival':
  selected=[n for n,t in m['events'].items() if (m['arrival']<t if m['strict'] else m['arrival']<=t)];assert selected==m['expected'];return dict(selected=selected,comparisons=[[n,m['arrival'],t] for n,t in m['events'].items()])
 if k=='transfer':
  # Object identities moved between explicit sets, independent of subtraction text.
  a=set(range(m['A']));b=set(range(100,100+m['B']));move=set(sorted(a)[:m['k']]);a-=move;b|=move;assert [len(a),len(b)]==m['expected'];assert len(a|b)==m['A']+m['B'] and not a&b;return dict(after=[len(a),len(b)],total=len(a|b),moved_ids=sorted(move))
 if k=='weighted_routes':
  allp=routes(m['edges']);minimum=min(p['total'] for p in allp);best=[p['route'] for p in allp if p['total']==minimum];assert minimum==m['expected_min'] and best==m['expected_routes'];return dict(all_routes=allp,minimum=minimum,all_minimum_routes=best)
 if k=='factor':
  # Enumerate array cells, not division by a guessed known factor.
  pairs=[]
  for a in range(m['low'],m['high']+1):
   for b in range(m['low'],m['high']+1):
    cells={(r,c) for r in range(a) for c in range(b)}
    if len(cells)==m['target'] and (m['ordered'] or a<=b) and a>m.get('min_first_exclusive',0):pairs.append([a,b])
  assert pairs==m['expected'];return dict(domain_pairs_checked=(m['high']-m['low']+1)**2,valid=pairs)
 if k=='subset':
  labels=list(m['items']);tested=[];valid=[]
  for mask in product([0,1],repeat=len(labels)):
   chosen=[n for n,on in zip(labels,mask) if on];total=sum(m['items'][n] for n in chosen);eligible=(m['count'] is None or len(chosen)==m['count']);tested.append(dict(chosen=chosen,total=total,cardinality_ok=eligible))
   if eligible and total==m['target']:valid.append(chosen)
  assert sorted(valid)==sorted(m['expected']);return dict(all_inventory_subsets=tested,valid=valid)
 if k=='balance_order':
  assignments=[]
  for R,G in product(range(1,9),repeat=2):
   if R>G:
    X=2*R;Y=G;assert X>Y;assignments.append([X,Y,R,G])
  # Symbolic reason valid for all positive masses: X=R+R>R>G=Y.
  return dict(bounded_regression_assignments=assignments,unbounded_relation_proof=['R>0 => R+R>R','R>G and G=Y => R>Y','X=R+R => X>Y'],conclusion='X>Y')
 if k=='balance_cancel':
  assignments=[]
  for A,B,C in product(range(1,9),repeat=3):
   if A+C<B+C:
    D=B;assert A<D;assignments.append([A,B,C,D])
  return dict(bounded_regression_count=len(assignments),unbounded_relation_proof=['A+C<B+C => A<B by equal positive translation cancellation','B=D => A<D'],conclusion='A<D')
 raise ValueError(k)

def main():
 # Saved full-field bytes must still match before authoring.
 oldreviews=[json.loads(b) for b in (OUT/'nearest_actual_full_field_review.jsonl').read_bytes().splitlines()]
 for rec in oldreviews:
  ref=rec['receipt'];b=(common.OLD/ref['source_file']).read_bytes().splitlines()[ref['line']-1];assert sha(b)==ref['sha256'];x=json.loads(b);assert rec['actual_fields']=={f:x.get(f) for f in common.FIELDS}
 author();assert len(ROWS)==14;counts=Counter(r['coverage']['finite_master_id'] for r in ROWS);assert len(counts)==7 and set(counts.values())=={2}
 numeric=[];oracles=[]
 for row in ROWS:
  for st in row['worked_steps']:
   assert st['reason'] and st['explanation'] and 'unit' in st
   if st['expression']:
    f=common.evalexpr(st['expression'],Fraction);d=common.evalexpr(st['expression'],Decimal);assert f==Fraction(st['result']) and d==Decimal(st['result']);numeric.append(dict(sample_id=row['sample_id'],step_id=st['step_id'],expression=st['expression'],Fraction=str(f),Decimal=str(d)))
  assert not any(re.search(r'[0-9=]',h['hint']+h['question']) for h in row['hints']);oracles.append(dict(sample_id=row['sample_id'],family=row['coverage']['finite_master_id'],model=row['independent_model'],oracle=oracle(row['independent_model']),passed=True,independent_of_worked_expression_evaluator=True))
 def write(name,rows):
  b=('\n'.join(dump(r) for r in rows)+'\n').encode();(OUT/name).write_bytes(b);return dict(path=name,bytes=len(b),rows=len(rows),sha256=sha(b))
 manifest=[write('cases.jsonl',ROWS)];selfqa=[];chats=[]
 for row,b in zip(ROWS,(OUT/'cases.jsonl').read_bytes().splitlines()):
  h=sha(b)
  for c in chat_records(row):c.update(quality_status=row['quality_status'],acceptance_status=row['acceptance_status'],source_row_sha256=h);chats.append(c)
  criteria=[dict(criterion=n,passed=True,evidence=e) for n,e in [('problem_givens_request','Actual original full fields below; finite rules supplied explicitly.'),('mathematical_correctness','Exact Fraction/Decimal for expressions, plus family-specific finite oracle; balance includes symbolic all-positive proof.'),('worked_reasons_units_check','Every step includes reason, explanation, unit; checks constraints and completeness.'),('guidance_three_hints_answer_free','Actual initial and all three hints/questions reviewed; no requested results filled.'),('student_work_grounded','Only actual synthetic statements assessed; no imagined image or physical action.'),('originality_grade_branch_scope',row['pedagogical_review_decision']),('provenance_and_draft_status','DRAFT pending root QA; no human/external attestation; branch IDs explicit; no G5 closure from G1.')]]
  selfqa.append(dict(sample_id=row['sample_id'],source_file='cases.jsonl',source_row_sha256=h,hash_basis='exact UTF-8 row excluding newline',actual_fields={f:row[f] for f in common.FIELDS},criteria=criteria,pedagogical_decision=row['pedagogical_review_decision'],reviewer='basic_text_author_actual_full_field_review',human_review_claimed=False,root_cross_review_status='PENDING'))
 manifest += [write('chat.jsonl',chats),write('selfqa7.jsonl',selfqa),write('independent_oracles.jsonl',oracles),write('numeric_fraction_decimal.jsonl',numeric)]
 for name in ['mapping_snapshot.json','nearest_actual_full_field_review.jsonl']:
  b=(OUT/name).read_bytes();manifest.append(dict(path=name,bytes=len(b),sha256=sha(b),rows=len(b.splitlines()) if name.endswith('jsonl') else None))
 comparisons=[]
 for folder,topics in [('g2_append',{'route_dead_end_sum','route_shared_node_once','local_branch_not_global','cards_shared_inventory_conflict','cards_repeated_value_inventory'}),('g1_text_append',{'pair_gate_unique','pair_gate_disconnected_sum','identity_equal_and_lower'})]:
  p=OUT.parent/folder/'cases.jsonl'
  for b in p.read_bytes().splitlines():
   row=json.loads(b)
   if row['topic'] in topics:comparisons.append(dict(sample_id=row['sample_id'],source_path=str(p.relative_to(HERE)),source_row_sha256=sha(b),actual_fields={f:row[f] for f in common.FIELDS}))
 manifest.append(write('own_new_source_comparisons.jsonl',comparisons))
 oldq={json.loads(b)['problem'] for f in ['current_sources.jsonl','release/accepted_cases.jsonl'] for b in (common.OLD/f).read_bytes().splitlines()};assert not any(r['problem'] in oldq for r in ROWS)
 summary=dict(status='14_DRAFTS_AUTHOR_QA_PASS_ROOT_QA_PENDING',cases=14,chat=len(chats),master_counts=dict(counts),grade_counts=dict(Counter(str(r['grade']) for r in ROWS)),numeric_steps=len(numeric),family_oracles=len(oracles),manifest=manifest,mapping_source_sha256=snapshot['source_sha256'],pending=['Root full-field cross-review of14drafts','G5 finite_route_total_optimization network plus round-trip-time branch remains pending; these2 only cover G1 simple directed graph comparison','Other master branches not assigned here remain owned by root'],limitations=['Original explicit text analogues; no actual image/physical competency claim.','Finite oracle covers represented domains, not all archive numeric variants.','No training, Drive/network writes, shared state/context, app/git or old-source edits.'])
 (OUT/'manifest.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n','utf-8');print(dump(dict(cases=14,chat=len(chats),masters=7,numeric=len(numeric),manifest=manifest)))
if __name__=='__main__':main()
