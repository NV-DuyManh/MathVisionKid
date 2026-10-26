"""Finite original Grade-1 text forms from actual page audit; local drafts only."""
from pathlib import Path
from fractions import Fraction
from decimal import Decimal
from itertools import permutations
import ast, hashlib, json
from exhaustive_primary_math import expression_group, chat_records

ROOT=Path(__file__).parent/'cloud_publication/sgk_page_audit_20261019'
OUT=ROOT/'g1_append'
ROWS=[]
def dump(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha(b):return hashlib.sha256(b).hexdigest()
def step(title,reason,result,explanation,expression=None,unit=''):
 return dict(title=title,reason=reason,result=str(result) if result is not None else None,explanation=explanation,expression=expression,unit=unit)
def hs(a,b,c):return [dict(level=i+1,hint=t,question=q) for i,(t,q) in enumerate(zip([a,b,c],['Em cần theo dõi những dữ kiện nào?','Em áp dụng điều kiện đã cho như thế nào?','Em kiểm đủ từng điều kiện ra sao?']))]
def add(topic,problem,givens,request,steps,answer,hints,page,oracle,student=None,guard=False):
 sid=f'sgk_page_g1_20261019_{topic}_{sum(x["topic"]==topic for x in ROWS)+1:02d}'
 book=next(x for x in json.loads((ROOT/'prior_append/data/g12_official_pages.json').read_text('utf-8')) if x['grade']==1 and x['volume']==1)
 receipt=next(json.loads(l) for l in (ROOT/'g1v1_audit/page_review.jsonl').read_text('utf-8').splitlines() if json.loads(l)['printed_page']==page)
 ROWS.append(dict(sample_id=sid,case_group_id=sid+'_group',split='train',grade=1,topic=topic,case_kind='guard' if guard else 'observable_student_error' if student else 'original_representation_gap',problem=problem,givens=[dict(id=f'g{i}',text=t,value=None,unit='') for i,t in enumerate(givens)],requested_quantity=request,student_work=dict(text=student,observations=[dict(excerpt=student,claim_scope='Explicit synthetic written work only; no hidden thought or unseen image inferred.')]) if student else None,initial_guidance=[hints[0]['hint']],hints=hints,worked_steps=[dict(step_id=f's{i}',**s) for i,s in enumerate(steps)],expected_answer=[dict(quantity=request,result=answer,unit='')],can_solve=not guard,canonical_signatures=sorted({expression_group(s['expression']) for s in steps if s['expression']}),acceptance_status='DRAFT_AWAITING_CONTENT_CROSS_REVIEW',quality_status='AUTHOR_QA_COMPLETE_PENDING_CROSS_REVIEW',human_verified=False,teacher_certified=False,owner_human_reviewed=False,source_role='AI_GENERATED',provenance=dict(authorship_origin='ORIGINAL_AI_TEACHER_AUTHORING',content_human_review_completed=False,acceptance_basis='OWNER_PREAUTHORIZED_PROCESS_CONTENT_CROSS_REVIEW_PENDING',book_exercise_copied=False,actual_physical_or_image_result_claimed=False),curriculum_assignment=dict(grade=1,book='Kết nối tri thức với cuộc sống',volume=1,lesson_page=page,publisher_reader_url=book['reader_urls'][0],publisher_page_url=receipt['publisher_page_url'],source_image_sha256=receipt['source_image_sha256'],source_evidence_level='ACTUAL_PUBLIC_PUBLISHER_IMAGE_VIEWED',coverage_claim='Original text analogue of observed form; no physical or vision outcome certified.'),gap_oracle=oracle,coverage=dict(mode='FINITE_ORIGINAL_PAGE_GAP_APPEND',gap_type=topic,numbers_only_variant=False)))

def build():
 ROWS.clear()
 t='add_group_strict_comparison'
 add(t,'Khay A có 4 hạt, khay B có 7 hạt. Chỉ được lấy thêm đúng một túi cho A. Túi P có 2 hạt, Q có 3 hạt, R có 4 hạt. Chọn mọi túi làm A có nhiều hạt hơn B sau khi thêm.',['A có 4 hạt; B có 7 hạt','Chọn đúng một trong P: 2, Q: 3, R: 4 hạt'],'Túi dùng được',[
 step('Tính lượng mới','Phải cộng phần trong túi vào lượng đang có trước khi so.','8','Bốn cộng hai được sáu; bốn cộng ba được bảy; bốn cộng bốn được tám.','4+4','hạt'),
 step('So theo yêu cầu chặt','Nhiều hơn khác với bằng nhau.','Chỉ R','Sáu ít hơn bảy; bảy bằng bảy nên P và Q đều không đạt. Tám nhiều hơn bảy nên chọn R; đã xét đủ ba túi.')], 'Chỉ túi R',hs('Tính lượng của khay sau khi thêm từng túi, rồi mới so.','Điều kiện nhiều hơn có chấp nhận hai lượng bằng nhau không?','Rà lại cả túi bị loại, không chỉ túi em chọn.'),23,dict(kind='add_strict',start=4,target=7,options={'P':2,'Q':3,'R':4},relation='>',valid=['R']))
 add(t,'Giá có 8 quyển sách. Cô đặt thêm đúng một chồng rồi muốn số sách vẫn ít hơn 12 quyển. Chồng A có 2 quyển, B có 4 quyển, C có 5 quyển. Chọn mọi chồng dùng được và giải thích trường hợp bằng mốc.',['Ban đầu 8 quyển','Thêm đúng một chồng A: 2, B: 4, C: 5; sau thêm phải ít hơn 12'],'Chồng dùng được',[
 step('Xét từng tổng','Thêm sách làm số sách tăng theo số quyển trong chồng.','10','Tính tám cộng hai, tám cộng bốn và tám cộng năm.','8+2','quyển'),
 step('Đối chiếu mốc','Ít hơn mốc không gồm trường hợp bằng mốc.','Chỉ A','Mười ít hơn mười hai; mười hai bằng mốc và mười ba vượt mốc. Chỉ chồng A đáp ứng, kiểm đã dùng đúng một chồng.')], 'Chỉ chồng A',hs('Tách số đang có với số sẽ được thêm.','So từng tổng với mốc và giữ đúng nghĩa ít hơn.','Kiểm số chồng được chọn theo đúng luật.'),23,dict(kind='add_strict',start=8,target=12,options={'A':2,'B':4,'C':5},relation='<',valid=['A']))
 add(t,'Hộp Đỏ có 5 viên bi, hộp Xanh có 9 viên. Chọn thêm đúng một túi vào hộp Đỏ: M có 3 viên, N có 4 viên, K có 5 viên. Bạn ghi: Chọn N vì 5 + 4 = 9 nên hộp Đỏ nhiều hơn hộp Xanh. Giữ dòng ấy, nhận xét và chọn túi đúng.',['Đỏ 5 viên; Xanh 9 viên; M: 3, N: 4, K: 5','Sau thêm, Đỏ phải nhiều hơn Xanh'],'Nhận xét và túi đúng',[
 step('Giữ phép cộng đúng','Cần tách tính toán khỏi kết luận so sánh.',9,'N cho chín viên, đúng phép cộng nhưng chỉ bằng hộp Xanh.','5+4','viên'),
 step('Kiểm mọi túi','Tổng phải vượt mốc mới thỏa yêu cầu.',10,'M cho tám, N cho chín, K cho mười. Chỉ K vượt chín; không sửa phép cộng đúng để hợp thức kết luận sai.','5+5','viên')], 'N chỉ làm hai hộp bằng nhau; chọn K',hs('Kiểm riêng phép cộng và câu kết luận của bạn.','Quan hệ nhiều hơn yêu cầu gì so với mốc?','Đối chiếu toàn bộ các túi trước khi kết luận.'),23,dict(kind='add_strict',start=5,target=9,options={'M':3,'N':4,'K':5},relation='>',valid=['K']),student='Chọn N vì 5 + 4 = 9 nên hộp Đỏ nhiều hơn hộp Xanh.')
 t='construct_equations_from_number_cards'
 add(t,'Có ba thẻ số 2, 5, 7. Mỗi phép dùng đủ ba thẻ, mỗi thẻ đúng một lần; chỉ có một dấu cộng hoặc trừ và một dấu bằng, dạng a + b = c hoặc a − b = c. Liệt kê mọi phép đúng.',['Ba thẻ số riêng 2, 5, 7','Dùng đủ mỗi thẻ một lần trong mỗi phép; chỉ cộng hoặc trừ'],'Các phép đúng',[
 step('Tìm quan hệ toàn bộ và hai phần','Phép cộng gộp hai phần thành thẻ còn lại.',7,'Hai cộng năm bằng bảy, nên năm cộng hai cũng bằng bảy.','2+5'),
 step('Viết phép trừ liên quan','Lấy toàn bộ bớt từng phần được phần kia.',5,'Bảy trừ hai bằng năm; bảy trừ năm bằng hai. Hai số nhỏ cộng không cho thẻ khác ngoài bảy; phép trừ phải bắt đầu bằng thẻ lớn nhất.','7-2')], '2 + 5 = 7; 5 + 2 = 7; 7 − 2 = 5; 7 − 5 = 2',hs('Mỗi phép cần giữ đúng đủ ba thẻ số.','Tìm thẻ có thể là toàn bộ rồi xét hai phần.','Kiểm từng phép và số lần dùng mỗi thẻ.'),107,dict(kind='equation_cards',cards=[2,5,7],valid=['2+5=7','5+2=7','7-2=5','7-5=2']))
 add(t,'Bộ thẻ có 1, 3, 4, 6. Chọn ba thẻ khác nhau để lập phép cộng đúng dạng a + b = c; mỗi thẻ chọn dùng một lần, một thẻ để lại. Liệt kê mọi phép và nêu thẻ để lại.',['Thẻ 1, 3, 4, 6; chọn đúng ba','Chỉ dạng a + b = c'],'Phép cộng và thẻ để lại',[
 step('Tìm bộ ba có quan hệ tổng','Kết quả phải là một thẻ trong bộ, không viết thêm số.',4,'Một cộng ba bằng bốn. Các cặp khác không cho một thẻ còn lại trong bộ.','1+3'),
 step('Xét thứ tự hai số hạng','Đổi thứ tự hai số hạng vẫn dùng đúng cùng ba thẻ.','1 + 3 = 4; 3 + 1 = 4','Cả hai phép để lại thẻ 6. Kiểm các thẻ 1, 3, 4 dùng một lần và không dùng thẻ 6.')], '1 + 3 = 4 và 3 + 1 = 4; đều để lại thẻ 6',hs('Kết quả cũng phải lấy từ bộ thẻ đã cho.','Thử các cặp thẻ và xem có thẻ còn lại bằng tổng không.','Sau mỗi phép, kiểm thẻ nào đã dùng và thẻ nào để lại.'),107,dict(kind='equation_cards',cards=[1,3,4,6],operation='+',valid=['1+3=4','3+1=4']))
 add(t,'Bộ thẻ gồm 0, 4, 7. Mỗi phép phải dùng đủ ba thẻ, mỗi thẻ một lần, dạng a + b = c hoặc a − b = c. Bạn viết 4 + 0 = 4 và nói đã dùng đủ thẻ. Giữ phép bạn viết, kiểm luật rồi cho biết có lập được phép đúng nào theo luật không.',['Bộ gồm đúng một thẻ 0, một thẻ 4, một thẻ 7','Mỗi phép dùng đủ ba thẻ một lần'],'Kiểm luật và khả năng lập phép',[
 step('Phân biệt đẳng thức đúng với dùng thẻ đúng','Giá trị phép tính đúng chưa bảo đảm đủ bộ thẻ.',4,'Bốn cộng không bằng bốn là đúng số học, nhưng viết 4 hai lần và bỏ thẻ 7.','4+0'),
 step('Kiểm khả năng của bộ thẻ','Hai thẻ nhỏ cộng không thành thẻ lớn; trừ hai thẻ khác không cho thẻ còn lại.','Không có phép hợp lệ','Không với bốn chỉ gộp thành bốn, không phải bảy. Bảy bớt bốn là ba, không có thẻ ba. Những phép chứa không cũng cần lặp thẻ còn lại. Đã xét các quan hệ có thể.')], 'Phép viết đúng số học nhưng sai luật thẻ; không có phép hợp lệ',hs('Kiểm số lần xuất hiện của từng thẻ trong phép đã viết.','Một phép hợp lệ phải đúng cả số học lẫn luật dùng thẻ.','Xét đủ vai trò của thẻ không trước khi kết luận.'),107,dict(kind='equation_cards',cards=[0,4,7],valid=[]),student='4 + 0 = 4; đã dùng đủ thẻ.')
 t='ordinal_after_insertion'
 add(t,'Từ đầu hàng đến cuối hàng là An, Bình, Chi, Dũng. Hà vào giữa Bình và Chi, các bạn cũ giữ thứ tự. Sau đó Dũng đứng thứ mấy tính từ đầu? Viết lại hàng để kiểm.',['Đầu → An, Bình, Chi, Dũng → cuối','Chèn Hà ngay sau Bình, trước Chi'],'Vị trí mới của Dũng',[
 step('Cập nhật đúng chỗ chèn','Bạn mới vào trước Chi nên các bạn sau vị trí đó lùi một hạng.','An, Bình, Hà, Chi, Dũng','Giữ An trước Bình và Chi trước Dũng; chỉ thêm Hà vào khe đã cho.'),
 step('Đếm từ đầu đã cố định','Mỗi người chiếm một vị trí trong hàng mới.',5,'Đếm An thứ nhất, Bình thứ hai, Hà thứ ba, Chi thứ tư, Dũng thứ năm; trước Dũng có bốn bạn.','4+1','vị trí')], 'Dũng đứng thứ 5',hs('Viết hàng ban đầu theo đúng chiều đầu đến cuối.','Chèn tên mới vào đúng khe và giữ thứ tự các tên cũ.','Đếm lại từ đầu hàng, mỗi người một vị trí.'),105,dict(kind='insert_rank',initial=['An','Bình','Chi','Dũng'],insert='Hà',after='Bình',target='Dũng',rank=5))
 add(t,'Hàng từ trước ra sau là Gấu, Thỏ, Mèo, Cáo. Sóc vào giữa Mèo và Cáo; các bạn cũ giữ thứ tự. Bạn ghi: Thỏ đổi thành thứ ba vì có thêm một bạn. Giữ câu ấy, kiểm vị trí Thỏ và Sóc.',['Gấu, Thỏ, Mèo, Cáo theo chiều trước → sau','Sóc chèn sau Mèo, trước Cáo'],'Vị trí Thỏ và Sóc',[
 step('Đặt bạn mới đúng khe','Chèn phía sau một người không thêm ai vào trước người đó.','Gấu, Thỏ, Mèo, Sóc, Cáo','Thỏ vẫn chỉ có Gấu ở trước, nên không tự tăng hạng của tất cả.'),
 step('Đếm hai vị trí cần hỏi','Dùng cùng đầu hàng để đánh số.','Thỏ thứ 2; Sóc thứ 4','Thỏ ở vị trí hai; sau Mèo là Sóc ở vị trí bốn. Kiểm đủ năm bạn và thứ tự cũ không đổi.')], 'Thỏ vẫn thứ 2; Sóc thứ 4',hs('Xác định vị trí chèn ở trước hay sau bạn cần hỏi.','Không phải mọi người đều đổi hạng khi thêm người vào hàng.','Viết hàng mới rồi kiểm từng vị trí được hỏi.'),105,dict(kind='insert_rank',initial=['Gấu','Thỏ','Mèo','Cáo'],insert='Sóc',after='Mèo',targets={'Thỏ':2,'Sóc':4}),student='Thỏ đổi thành thứ ba vì có thêm một bạn.')
 add(t,'Bốn bạn xếp từ đầu đến cuối: Lan, Minh, Nga, Phúc. Một bạn mới sẽ đứng ngay trước Minh hoặc ngay sau Phúc; chưa chọn chỗ nào. Em hỏi Nga chắc chắn đứng thứ mấy sau khi thêm bạn. Có đủ dữ kiện để chốt một vị trí không?',['Lan, Minh, Nga, Phúc từ đầu → cuối','Có hai chỗ còn chưa chọn: trước Minh hoặc sau Phúc'],'Thông tin cần thêm',[
 step('Đối chiếu hai cách chèn','Hạng của Nga phụ thuộc bạn mới có đứng trước Nga không.','Hai khả năng khác nhau','Chèn trước Minh làm hàng Lan, bạn mới, Minh, Nga, Phúc nên Nga thứ tư. Chèn sau Phúc thì Nga vẫn thứ ba. Cần hỏi đã chọn chỗ nào, chưa chốt một hạng.')], 'Chưa đủ; cần biết bạn mới đứng trước Minh hay sau Phúc',hs('Điều chưa chọn có thể làm thay đổi số người trước Nga.','Xét riêng hai cách được phép, không tự chọn một cách.','Nếu hai cách cho hạng khác nhau, cần hỏi quyết định còn thiếu.'),105,dict(kind='insert_guard',possible_ranks=[4,3],can_solve=False),guard=True)
 t='ordinal_from_both_ends'
 add(t,'Năm thẻ đặt từ trái sang phải là A, B, C, D, E. Thẻ B đứng thứ mấy từ trái và thứ mấy từ phải? Các thẻ không đổi chỗ.',['Trái → A, B, C, D, E → phải'],'Hai vị trí của B',[
 step('Đếm từ trái','Đầu đếm thay đổi tên vị trí nhưng không di chuyển thẻ.','Thứ 2 từ trái','A thứ nhất rồi B thứ hai.'),
 step('Đổi sang đầu phải','Đếm lại từ E, mỗi thẻ một lần.','Thứ 4 từ phải','Từ phải là E, D, C, B, A. B thứ tư; hai hạng cộng lại bằng sáu vì chính B được tính trong cả hai lượt.')], 'B thứ 2 từ trái và thứ 4 từ phải',hs('Giữ nguyên dãy thẻ, xác định đầu bắt đầu đếm.','Đổi đầu đếm, không đảo vị trí thật của các thẻ.','Đọc hai lượt đếm để kiểm cùng một thẻ được hỏi.'),98,dict(kind='both_ends',items=['A','B','C','D','E'],target='B',left=2,right=4))
 add(t,'Có 7 bạn xếp một hàng. Từ đầu hàng nhìn về cuối, Huy đứng thứ 3. Không ai đổi chỗ. Huy đứng thứ mấy khi đếm từ cuối hàng? Giải thích bằng số bạn ở hai phía.',['Có 7 bạn; Huy thứ 3 từ đầu','Một hàng giữ nguyên thứ tự'],'Vị trí Huy từ cuối',[
 step('Tách người trước và sau Huy','Thứ ba gồm hai người trước rồi đến chính Huy.',4,'Bảy bạn bớt hai người trước và bớt Huy còn bốn người sau.','7-2-1','bạn'),
 step('Đếm từ cuối tới Huy','Đi qua những người sau Huy rồi tính thêm chính Huy.',5,'Bốn người sau được đếm trước, Huy là người thứ năm từ cuối. Kiểm hai người trước, Huy và bốn người sau đủ bảy.','4+1','vị trí')], 'Huy thứ 5 từ cuối',hs('Phân biệt số người trước một bạn với thứ hạng của bạn đó.','Tách cả hàng thành trước, chính bạn, và sau.','Khi đếm từ cuối, nhớ tính cả người đang được hỏi.'),98,dict(kind='both_ends_count',count=7,left=3,right=5))
 add(t,'Sáu con thú đứng từ trái sang phải: Voi, Gấu, Thỏ, Mèo, Sóc, Cáo. Bạn ghi: Mèo thứ 4 từ trái nên cũng thứ 4 từ phải. Giữ câu đó và sửa phần chưa đúng.',['Trái → Voi, Gấu, Thỏ, Mèo, Sóc, Cáo → phải'],'Vị trí đúng của Mèo',[
 step('Giữ phần đúng','Đếm từ trái đúng theo danh sách cho.','Thứ 4 từ trái','Voi, Gấu, Thỏ rồi Mèo: phần đầu câu đúng.'),
 step('Đếm lại từ phải','Hai đầu khác nhau nên không sao chép nguyên hạng.','Thứ 3 từ phải','Cáo thứ nhất, Sóc thứ hai, Mèo thứ ba. Kiểm ba con bên trái và hai con bên phải cùng Mèo đủ sáu.')], 'Mèo thứ 4 từ trái, thứ 3 từ phải',hs('Kiểm hai vế của câu theo hai đầu đếm riêng.','Hạng từ một đầu chưa tự là hạng từ đầu kia.','Đếm từng tên từ phải sang trái và dừng đúng con cần hỏi.'),98,dict(kind='both_ends',items=['Voi','Gấu','Thỏ','Mèo','Sóc','Cáo'],target='Mèo',left=4,right=3),student='Mèo thứ 4 từ trái nên cũng thứ 4 từ phải.')
 t='periodic_attribute_pattern'
 add(t,'Luật xâu hạt là lặp nguyên nhóm Đỏ, Xanh, Xanh từ trái sang phải. Dãy đang ghi: Đỏ, Xanh, Xanh, Đỏ, Xanh, □, Đỏ, □, Xanh. Điền hai ô và nêu nhóm lặp để kiểm.',['Nhóm lặp theo đúng thứ tự: Đỏ, Xanh, Xanh','Ô trống ở vị trí 6 và 8'],'Hai màu còn thiếu',[
 step('Chia theo nhóm lặp','Luật cho lặp cả nhóm, không chỉ xen kẽ hai màu.','Đỏ, Xanh, Xanh | Đỏ, Xanh, □ | Đỏ, □, Xanh','Mỗi nhóm có ba vị trí tương ứng với luật.'),
 step('So cùng vị trí trong nhóm','Vị trí thứ hai và thứ ba của mỗi nhóm đều theo mẫu.','Ô 6: Xanh; ô 8: Xanh','Điền rồi đọc từng nhóm, cả ba đều là Đỏ, Xanh, Xanh. Không suy màu bằng số màu khác nhau trong nhóm.')], 'Ô 6 màu Xanh; ô 8 màu Xanh',hs('Tách dãy thành các nhóm đúng độ dài của luật.','So ô trống với cùng vị trí trong nhóm mẫu.','Đọc cả nhóm sau khi điền, không chỉ hai ô lân cận.'),55,dict(kind='periodic',pattern=['Đỏ','Xanh','Xanh'],length=9,blanks=[6,8],valid=['Xanh','Xanh']))
 add(t,'Dãy thẻ theo luật lặp: tam giác, tròn, vuông, chữ nhật. Mười thẻ đầu đều tuân luật. Thẻ thứ 10 mang hình gì? Hãy chia nhóm để giải, không cần ảnh.',['Nhóm bốn hình theo thứ tự cố định','Hỏi vị trí thứ 10 tính từ trái'],'Hình ở thẻ thứ 10',[
 step('Đếm hết các nhóm đầy đủ','Hai nhóm đủ dùng tám vị trí.',8,'Nhóm đầu chiếm một đến bốn; nhóm tiếp chiếm năm đến tám.','4+4','thẻ'),
 step('Đếm tiếp trong nhóm mới','Vị trí chín bắt đầu lại nhóm, vị trí mười là vị trí tiếp theo.','Hình tròn','Thứ chín là tam giác, thứ mười là tròn. Kiểm bằng đọc đủ mười hình theo cùng luật.')], 'Hình tròn',hs('Xác định độ dài của một nhóm lặp.','Đánh dấu các nhóm đầy đủ rồi đếm phần còn lại.','Nhớ bắt đầu lại nhóm từ hình đầu sau mỗi nhóm đủ.'),113,dict(kind='periodic_position',pattern=['tam giác','tròn','vuông','chữ nhật'],position=10,valid='tròn'))
 add(t,'Luật xếp là lặp hình vuông, hình vuông, hình tròn. Bạn viết: vuông, vuông, tròn, vuông, tròn, tròn và nói đã đúng luật. Giữ dãy bạn viết, xác định vị trí đầu tiên sai và sửa đúng vị trí ấy; các vị trí khác giữ nguyên.',['Nhóm lặp: vuông, vuông, tròn','Dãy đã viết có 6 vị trí'],'Vị trí đầu tiên sai và cách sửa',[
 step('Kiểm nhóm đầu','Nhóm đầu đã trùng nguyên mẫu.','Ba vị trí đầu đúng','Không sửa các vị trí đúng chỉ vì màu hay hình lặp lại.'),
 step('Đối chiếu nhóm thứ hai','Mỗi vị trí của nhóm sau phải khớp vị trí tương ứng của nhóm đầu.','Vị trí 5 sai; đổi thành vuông','Nhóm sau cần vuông, vuông, tròn. Vị trí bốn và sáu đúng, chỉ vị trí năm cần sửa. Đọc lại cả sáu để kiểm.')], 'Vị trí 5; đổi tròn thành vuông',hs('Đối chiếu dãy đã viết với đúng nhóm mẫu.','Tìm chỗ khác đầu tiên, không thay cả dãy.','Sau khi sửa một vị trí, kiểm các nhóm còn lại vẫn đúng.'),111,dict(kind='periodic_error',pattern=['vuông','vuông','tròn'],actual=['vuông','vuông','tròn','vuông','tròn','tròn'],first_error=5),student='Vuông, vuông, tròn, vuông, tròn, tròn; đã đúng luật.')
 t='resource_assignment_inequality'
 add(t,'Có hai chuồng A nuôi 2 con dê và B nuôi 4 con dê. Xe P chở 3 bó cỏ, xe Q chở 5 bó cỏ. Mỗi chuồng nhận đúng một xe, mỗi xe dùng một lần. Ở mỗi chuồng, số bó phải nhiều hơn số dê. Ghép xe với chuồng và kiểm.',['A: 2 dê; B: 4 dê; P: 3 bó; Q: 5 bó','Mỗi xe, mỗi chuồng dùng đúng một lần; bó > dê'],'Cách ghép',[
 step('Xét chuồng cần nhiều cỏ hơn','Chuồng có bốn dê không thể nhận xe chỉ có ba bó.','B nhận Q','Năm nhiều hơn bốn nên Q đáp ứng cho B; P không đáp ứng cho B.'),
 step('Ghép phần còn lại rồi kiểm','Mỗi xe chỉ dùng một lần.','A nhận P','Ba nhiều hơn hai, nên A nhận P. Hai chuồng đều đạt và hai xe đã dùng đúng một lần.')], 'A nhận P; B nhận Q',hs('Một cách ghép phải thỏa điều kiện ở cả hai chuồng.','Xét chuồng có ít xe đáp ứng hơn trước.','Kiểm riêng từng cặp và kiểm mỗi xe chỉ dùng một lần.'),27,dict(kind='assignment',needs={'A':2,'B':4},resources={'P':3,'Q':5},strict=True,valid=[{'A':'P','B':'Q'}]))
 add(t,'Ba đội có số bạn là A: 1, B: 3, C: 5. Có ba khay bánh P: 2 chiếc, Q: 4 chiếc, R: 6 chiếc. Mỗi đội nhận đúng một khay, mỗi khay dùng một lần; số bánh của khay phải nhiều hơn số bạn của đội. Tìm mọi cách chia khay.',['Ba đội: 1, 3, 5 bạn; ba khay: 2, 4, 6 chiếc','Mỗi khay dùng một lần; bánh phải nhiều hơn bạn'],'Mọi cách chia',[
 step('Bắt đầu từ đội đông nhất','Đội năm bạn chỉ có khay sáu chiếc đáp ứng.','C nhận R','Hai và bốn đều không vượt năm, nên R buộc dành cho C.'),
 step('Xét hai đội còn lại','Sau khi dùng R, khay cho B phải vượt ba.','B nhận Q; A nhận P','B nhận bốn chiếc, A nhận hai chiếc. Mỗi khay vượt số bạn đội nhận. Các lựa chọn đều bị điều kiện buộc nên chỉ một cách.')], 'Chỉ A nhận P, B nhận Q, C nhận R',hs('Không thể dùng lại một khay cho hai đội.','Giải quyết đội khó được đáp ứng trước rồi xét khay còn lại.','Kiểm đủ ba đội và giải thích vì sao không còn cách khác.'),27,dict(kind='assignment',needs={'A':1,'B':3,'C':5},resources={'P':2,'Q':4,'R':6},strict=True,valid=[{'A':'P','B':'Q','C':'R'}]))
 add(t,'Hai bàn A và B lần lượt có 2 bạn và 4 bạn. Hộp P có 4 bút, Q có 5 bút. Mỗi bàn nhận một hộp khác nhau, số bút phải nhiều hơn số bạn ở từng bàn. Bạn viết: A nhận Q, B nhận P; vì bốn bút đủ cho bốn bạn nên đạt. Giữ cách bạn ghép, kiểm rồi sửa.',['A: 2 bạn; B: 4 bạn; P: 4 bút; Q: 5 bút','Mỗi hộp dùng một lần; cần nhiều hơn, không phải chỉ đủ'],'Nhận xét và cách ghép sửa',[
 step('Kiểm cách đã ghi','Điều kiện phải áp dụng riêng cho từng bàn.','B nhận P chưa đạt','A có năm bút nhiều hơn hai bạn, nhưng B có bốn bút bằng bốn bạn. Đủ mỗi bạn một bút chưa phải nhiều hơn.'),
 step('Đổi cách phân công và kiểm','Q là hộp duy nhất vượt số bạn ở B.','A nhận P; B nhận Q','B nhận năm vượt bốn; A nhận bốn vượt hai. Hai hộp vẫn dùng đúng một lần, nên cách sửa hợp lệ.')], 'Cách cũ sai ở B; sửa A nhận P, B nhận Q',hs('Đọc chính xác yêu cầu nhiều hơn trong luật.','Kiểm mỗi bàn thay vì chỉ tổng số bút của hai hộp.','Sau khi đổi, kiểm cả điều kiện từng bàn và số lần dùng hộp.'),27,dict(kind='assignment',needs={'A':2,'B':4},resources={'P':4,'Q':5},strict=True,valid=[{'A':'P','B':'Q'}]),student='A nhận Q, B nhận P; vì bốn bút đủ cho bốn bạn nên đạt.')
 t='two_sided_strict_bound_selection'
 add(t,'Có các thẻ 3, 5, 6, 8, 9. Chọn mọi thẻ có số lớn hơn 5 và nhỏ hơn 9 cùng lúc. Giải thích cả hai thẻ ở đúng mốc.',['Các thẻ 3, 5, 6, 8, 9','Điều kiện đồng thời: số > 5 và số < 9'],'Các thẻ đạt',[
 step('Kiểm cận dưới','Thẻ phải vượt năm, không chỉ bằng năm.','Giữ xét 6, 8, 9','Ba và năm không vượt năm nên loại; chưa kết luận chín vì còn cận trên.'),
 step('Kiểm cận trên','Các thẻ còn lại phải nhỏ hơn chín.','Chọn 6 và 8','Chín bằng cận trên nên không được chọn. Sáu và tám đều vượt năm và bé hơn chín; đã kiểm đủ từng thẻ.')], 'Thẻ 6 và 8',hs('Một thẻ cần vượt qua cả hai điều kiện.','Các số đúng bằng mốc có thỏa dấu chặt không?','Kiểm lại từng thẻ chọn với cả cận dưới và cận trên.'),104,dict(kind='bounds',cards=[3,5,6,8,9],low=5,high=9,valid=[6,8]))
 add(t,'Các vé ghi 20, 21, 24, 28, 30. Vé được vào khu trò chơi phải ghi số lớn hơn 20 và nhỏ hơn 30. Bạn chọn 20, 24, 30 vì cả ba nằm trong khoảng từ hai mươi đến ba mươi. Giữ danh sách đó, loại thẻ sai rồi bổ sung thẻ còn thiếu.',['Vé 20, 21, 24, 28, 30','Yêu cầu lớn hơn 20 và nhỏ hơn 30'],'Danh sách được sửa',[
 step('Kiểm hai đầu danh sách','Dấu lớn hơn và nhỏ hơn đều không nhận mốc bằng.','Loại 20 và 30; giữ 24','Hai mốc không thỏa, còn hai mươi tư vượt hai mươi và chưa đến ba mươi.'),
 step('Rà các vé chưa chọn','Sửa danh sách cần đủ mọi vé thỏa, không chỉ bỏ vé sai.','Bổ sung 21 và 28','Hai mươi mốt và hai mươi tám cũng thỏa cả hai điều kiện. Danh sách cuối là 21, 24, 28; không lặp hoặc bỏ vé đạt.')], '21, 24, 28',hs('Kiểm phần đúng và phần sai của danh sách riêng.','Đối chiếu dấu chặt với các vé đúng bằng mốc.','Rà cả các vé bạn chưa chọn để danh sách đầy đủ.'),104,dict(kind='bounds',cards=[20,21,24,28,30],low=20,high=30,valid=[21,24,28]),student='Chọn 20, 24, 30 vì cả ba nằm trong khoảng từ hai mươi đến ba mươi.')
 add(t,'Các thẻ ghi 5, 6, 7, 8. Luật yêu cầu chọn số lớn hơn 6 và nhỏ hơn 7 cùng lúc. Bạn nói phải chọn ít nhất một thẻ vì đã có đủ thẻ hai mốc. Có thẻ nào dùng được không? Giải thích theo thứ tự đếm.',['Thẻ 5, 6, 7, 8','Đồng thời lớn hơn 6 và nhỏ hơn 7'],'Khả năng chọn thẻ',[
 step('Xét các thẻ không vượt cận dưới','Thẻ bằng cận dưới vẫn chưa thỏa.','Loại 5 và 6','Năm bé hơn sáu, sáu bằng sáu; cả hai không lớn hơn sáu.'),
 step('Kiểm các thẻ còn lại','Vượt cận dưới chưa đủ nếu không nhỏ hơn cận trên.','Không có thẻ dùng được','Bảy bằng bảy và tám lớn hơn bảy, nên đều không nhỏ hơn bảy. Trong dãy số đếm, sáu và bảy liền nhau; không phải bài nào cũng có lựa chọn đạt.')], 'Không có thẻ nào dùng được',hs('Không tự buộc phải chọn nếu không thẻ nào thỏa luật.','Xét điều kiện dưới rồi kiểm tiếp điều kiện trên.','Dùng thứ tự đếm để kiểm kết luận không có lựa chọn.'),104,dict(kind='bounds',cards=[5,6,7,8],low=6,high=7,valid=[]),student='Phải chọn ít nhất một thẻ vì đã có đủ thẻ hai mốc.')

def calc(expr,typ):
 def f(n):
  if isinstance(n,ast.Constant) and type(n.value) is int:return typ(n.value)
  if not isinstance(n,ast.BinOp):raise ValueError(expr)
  a,b=f(n.left),f(n.right)
  if isinstance(n.op,ast.Add):return a+b
  if isinstance(n.op,ast.Sub):return a-b
  raise ValueError(expr)
 return f(ast.parse(expr,mode='eval').body)
def oracle_check(o):
 k=o['kind']
 if k=='add_strict':
  out=[a for a,b in o['options'].items() if (o['start']+b>o['target'] if o['relation']=='>' else o['start']+b<o['target'])];assert out==o['valid'];return out
 if k=='equation_cards':
  out=[]
  for a,b,c in permutations(o['cards'],3):
   for op in ['+'] if o.get('operation')=='+' else ['+','-']:
    if (a+b if op=='+' else a-b)==c:out.append(f'{a}{op}{b}={c}')
  assert sorted(out)==sorted(o['valid']);return sorted(out)
 if k=='insert_rank':
  a=o['initial'][:];a.insert(a.index(o['after'])+1,o['insert']);assert all(a.index(x)+1==v for x,v in o.get('targets',{o.get('target'):o.get('rank')}).items());return a
 if k=='insert_guard':assert len(set(o['possible_ranks']))>1 and not o['can_solve'];return o['possible_ranks']
 if k=='both_ends':
  assert o['items'].index(o['target'])+1==o['left'];assert list(reversed(o['items'])).index(o['target'])+1==o['right'];return [o['left'],o['right']]
 if k=='both_ends_count':assert o['count']-o['left']+1==o['right'];return o['right']
 if k in ['periodic','periodic_position','periodic_error']:
  p=o['pattern']
  if k=='periodic':out=[p[(i-1)%len(p)] for i in o['blanks']];assert out==o['valid'];return out
  if k=='periodic_position':out=p[(o['position']-1)%len(p)];assert out==o['valid'];return out
  out=next(i+1 for i,v in enumerate(o['actual']) if v!=p[i%len(p)]);assert out==o['first_error'];return out
 if k=='assignment':
  out=[]
  for perm in permutations(o['resources']):
   a=dict(zip(o['needs'],perm))
   if all(o['resources'][a[n]]>v for n,v in o['needs'].items()):out.append(a)
  assert sorted(map(dump,out))==sorted(map(dump,o['valid']));return out
 if k=='bounds':out=[x for x in o['cards'] if o['low']<x<o['high']];assert out==o['valid'];return out
 raise ValueError(k)

def export():
 build();assert len(ROWS)==21 and len({r['sample_id'] for r in ROWS})==21
 OUT.mkdir(exist_ok=True)
 source=[];chats=[];reviews=[];oracles=[]
 for row in ROWS:
  evidence={'sample_id':row['sample_id'],'finite_oracle_result':oracle_check(row['gap_oracle']),'numeric_checks':[]}
  for s in row['worked_steps']:
   if s['expression']:
    a=calc(s['expression'],Fraction);b=calc(s['expression'],Decimal);assert a==Fraction(b)==Fraction(s['result']);evidence['numeric_checks'].append(dict(expression=s['expression'],fraction=str(a),decimal=str(b)))
  line=dump(row);h=sha(line.encode('utf-8'));source.append(line)
  evidence['source_row_sha256']=h;oracles.append(evidence)
  reviews.append(dict(sample_id=row['sample_id'],source_row_sha256=h,status='AUTHOR_SELF_QA_PASS_CROSS_REVIEW_PENDING',review_role='AUTHOR_SELF_QA',criteria={k:'PASS' for k in ['correct_math_or_explicit_guard','givens_request_consistent','steps_reasons_units_check','grade_scope','initial_and_all_three_hints_answer_free','student_work_grounded_no_unseen_inference','schema_provenance_unique']},basis='Actual full authored fields read in authoring; exact Fraction/Decimal arithmetic plus independent finite enumeration/sequence oracle. This is not independent external or owner human content review.'))
  for c in chat_records(row):c['source_row_sha256']=h;c['acceptance_status']=row['acceptance_status'];chats.append(c)
 for name,data in [('cases.jsonl',source),('chat.jsonl',[dump(c) for c in chats]),('self_qa.jsonl',[dump(x) for x in reviews]),('oracle_checks.jsonl',[dump(x) for x in oracles])]:
  (OUT/name).write_text('\n'.join(data)+'\n',encoding='utf-8',newline='\n')
 manifest=dict(case_count=len(ROWS),chat_count=len(chats),topics={t:sum(r['topic']==t for r in ROWS) for t in sorted({r['topic'] for r in ROWS})},status='DRAFT_AWAITING_CONTENT_CROSS_REVIEW',files={p.name:dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in OUT.glob('*.jsonl')},network_used=False,trained=False)
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(manifest,ensure_ascii=False))
if __name__=='__main__':export()
