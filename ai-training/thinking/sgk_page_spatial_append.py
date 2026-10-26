"""Nine finite original text-described spatial cases; DRAFT only, no Drive mutation."""
from pathlib import Path
from fractions import Fraction
from decimal import Decimal
from itertools import combinations
import ast, hashlib, json
from exhaustive_primary_math import chat_records, expression_group

ROOT=Path(__file__).parent/'cloud_publication/sgk_page_audit_20261019'
OUT=ROOT/'g3_spatial_append'
ROWS=[]
def dump(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha(b):return hashlib.sha256(b).hexdigest()
def step(title,reason,result,explanation,expression=None,unit=''):
 return dict(title=title,reason=reason,result=str(result),explanation=explanation,expression=expression,unit=unit)
def hs(a,b,c):return [dict(level=i+1,hint=h,question=q) for i,(h,q) in enumerate(zip([a,b,c],['Em cần dùng chính xác dữ kiện nào?','Em thực hiện theo các quan hệ đã cho ra sao?','Em kiểm không bỏ sót và không đếm lặp thế nào?']))]
def add(topic,problem,givens,request,steps,answers,hints,page,oracle,student=None):
 sid=f'sgk_page_spatial_20261019_{topic}_{sum(r["topic"]==topic for r in ROWS)+1:02d}'
 receipt=next(json.loads(l) for l in (ROOT/'g3_audit/page_review.jsonl').read_text('utf8').splitlines() if json.loads(l)['book_id']=='g3v1' and json.loads(l)['printed_page']==page)
 ROWS.append(dict(sample_id=sid,case_group_id=sid+'_group',split='train',grade=3,topic=topic,case_kind='observable_student_error' if student else 'original_representation_gap',problem=problem,givens=[dict(id=f'g{i}',text=t,value=None,unit='') for i,t in enumerate(givens)],requested_quantity=request,student_work=dict(text=student,observations=[dict(excerpt=student,claim_scope='Explicit synthetic written evidence only; no hidden reasoning or unseen image inferred.')]) if student else None,initial_guidance=[hints[0]['hint']],hints=hints,worked_steps=[dict(step_id=f's{i}',**s) for i,s in enumerate(steps)],expected_answer=[dict(quantity=q,result=str(v),unit=u) for q,v,u in answers],can_solve=True,gap_oracle=oracle,canonical_signatures=sorted({expression_group(s['expression']) for s in steps if s['expression']}),acceptance_status='DRAFT_AWAITING_CONTENT_CROSS_REVIEW',quality_status='AUTHOR_QA_COMPLETE_PENDING_CROSS_REVIEW',human_verified=False,teacher_certified=False,owner_human_reviewed=False,source_role='AI_GENERATED',provenance=dict(authorship_origin='ORIGINAL_AI_TEACHER_AUTHORING',content_human_review_completed=False,acceptance_basis='OWNER_PREAUTHORIZED_PROCESS_CONTENT_CROSS_REVIEW_PENDING',book_exercise_copied=False,actual_physical_or_image_result_claimed=False),curriculum_assignment=dict(grade=3,book='Kết nối tri thức với cuộc sống',volume=1,lesson_page=page,publisher_reader_url=receipt['reader_url'],publisher_page_url=receipt['public_image_url'],source_image_sha256=receipt['image_sha256'],source_evidence_level='PRIOR_AGENT_ACTUAL_PAGE_RECEIPT_AND_FULL_TRAIN_CONTENT_COMPARISON',coverage_claim='Original explicit text spatial analogue; no physical construction or pixel recognition certified; selected enrichment form only.'),quality_flags=dict(text_description_only_not_vision_training=True,actual_image_or_physical_asset_present=False,three_hint_levels_answer_free=True,app_plan_draft_compatible=False),coverage=dict(mode='FINITE_ORIGINAL_PAGE_GAP_APPEND',gap_type=topic,numbers_only_variant=False)))

def build():
 ROWS.clear()
 t='composite_polygon_enumeration'
 add(t,'Tam giác ABC có D nằm giữa B và C. Đã vẽ đủ AB, AC, BC và AD; ngoài các đoạn đó không có đường nào khác. Chỉ xét các tam giác có đỉnh trong A, B, C, D, mỗi cạnh phải được vẽ trọn. Liệt kê tất cả tam giác, kể cả hình ghép; đổi thứ tự tên vẫn là cùng một hình.',['B, D, C thẳng hàng theo thứ tự; A không nằm trên BC','Có các đoạn AB, AC, BC, AD; không có đoạn khác'],'Danh sách và số tam giác',[
 step('Liệt kê theo đỉnh ngoài đường thẳng','Ba điểm trên cùng một đường không tạo tam giác.','ABD; ADC; ABC','Mọi tam giác phải dùng A. Chọn cặp trong B, D, C được ABD, ADC và ABC; mỗi cặp đều có đủ cạnh đã vẽ.'),
 step('Kiểm hình nhỏ và hình ghép','Hai vùng nhỏ không phải là tất cả các tam giác.','3','ABD và ADC là hai hình nhỏ; ABC dùng đường bao ngoài và gồm cả hai vùng. BDC thẳng hàng nên loại. Không tính lại BAD vì trùng ABD.', '2+1','tam giác')],[('Các tam giác','ABD; ADC; ABC',''),('Số tam giác',3,'tam giác')],hs('Xét các bộ đỉnh, cả hình nhỏ và hình ghép.','Một bộ điểm chỉ tạo tam giác khi không thẳng hàng và đủ các cạnh.','Đổi thứ tự gọi tên không làm xuất hiện hình mới.'),22,dict(kind='triangles',points={'A':[1,2],'B':[0,0],'D':[1,0],'C':[2,0]},segments=[['A','B'],['A','C'],['B','C'],['A','D']],expected=[['A','B','D'],['A','C','D'],['A','B','C']]))
 add(t,'Một hình chữ nhật được chia bằng hai đường thẳng đứng từ mép trên xuống mép dưới thành ba cột liền nhau; không chia ngang. Gọi ba cột từ trái sang phải là 1, 2, 3. Mọi đường ngang, dọc đều được vẽ trọn. Liệt kê mọi hình chữ nhật theo các cột liên tiếp nó phủ. Cùng một miền chỉ tính một lần.',['Ba cột 1, 2, 3; chỉ một hàng','Bốn đường biên đứng và hai đường biên ngang đầy đủ'],'Các miền chữ nhật và tổng số',[
 step('Nhóm theo số cột được phủ','Mỗi chữ nhật phải phủ một dãy cột liên tiếp; bỏ cột giữa sẽ làm miền bị hở.','1; 2; 3; 1–2; 2–3; 1–2–3','Phủ một cột có ba miền; phủ hai cột có hai miền; phủ cả ba có một miền.'),
 step('Cộng các nhóm rời','Các miền thuộc ba nhóm không trùng nhau.','6','Ba cộng hai cộng một bằng sáu hình chữ nhật. Kiểm không có miền chỉ phủ cột 1 và 3 mà bỏ cột 2.', '3+2+1','hình chữ nhật')],[('Các miền','1; 2; 3; 1–2; 2–3; 1–2–3',''),('Tổng số',6,'hình chữ nhật')],hs('Đếm theo bề ngang của miền, không chỉ theo các ô nhỏ.','Một hình chữ nhật cần có đường bao liên tục.','Kiểm các nhóm miền vừa liệt kê có trùng hay thiếu không.'),57,dict(kind='grid_rectangles',columns=3,rows=1,expected=6))
 add(t,'Bảng gồm hai hàng và hai cột ô vuông bằng nhau. Tất cả ba đường ngang và ba đường dọc được vẽ trọn. Cần đếm mọi hình chữ nhật có cạnh nằm trên đường đã vẽ, kể cả hình vuông. Bạn chỉ đếm bốn ô nhỏ rồi ghi: Có 4 hình chữ nhật. Giữ câu đó và sửa bằng cách nhóm các miền.',['Lưới đủ 2 hàng, 2 cột; không có đường chéo','Hình vuông được tính là hình chữ nhật'],'Số hình chữ nhật và nhận xét',[
 step('Bổ sung các miền ghép','Một hình chữ nhật có thể gồm nhiều ô nhỏ.','Bốn ô đơn; hai hàng; hai cột; cả bảng','Có bốn miền một ô, hai miền phủ cả một hàng, hai miền phủ cả một cột và một miền phủ toàn bảng.'),
 step('Kiểm tổng và sửa kết luận','Các nhóm được phân theo số hàng và cột nên không đếm lặp.','9','Bốn cộng hai cộng hai cộng một bằng chín. Bạn đã đếm đúng số ô nhỏ nhưng bỏ các miền ghép; giữ quy ước tính cả hình vuông.', '4+2+2+1','hình chữ nhật')],[('Tổng số',9,'hình chữ nhật'),('Nhận xét','Bốn ô nhỏ chưa gồm các hình ghép','')],hs('Đối chiếu điều được hỏi với những miền bạn đã đếm.','Xét các miền phủ nhiều hàng hoặc nhiều cột.','Kiểm cùng một miền có bị tính lại trong hai nhóm không.'),66,dict(kind='grid_rectangles',columns=2,rows=2,expected=9),student='Có 4 hình chữ nhật vì có bốn ô nhỏ.')
 t='fixed_stick_rectangle_inventory'
 add(t,'Có 14 que thẳng, mỗi que dài 1 cm. Dùng hết que ghép đường bao một hình chữ nhật, không xếp chồng, không bẻ; các góc đều vuông. Mỗi cạnh gồm một số nguyên dương que. Liệt kê mọi cặp dài–rộng tính bằng cm, quy ước dài không ngắn hơn rộng; quay hình không tạo cách mới.',['14 que dài 1 cm; dùng hết trên đường bao','Cạnh nguyên dương; dài ≥ rộng; quay hình không tạo cách mới'],'Các cặp dài–rộng',[
 step('Tìm tổng hai cạnh kề','Hai cạnh đối diện bằng nhau nên chia số que thành hai nửa bằng nhau.','7','Tổng dài và rộng là bảy xăng-ti-mét vì hai lần tổng đó dùng hết mười bốn que.', '14/2','cm'),
 step('Thử rộng tăng dần','Với tổng đã biết, tăng rộng một thì dài giảm một.','6–1; 5–2; 4–3','Rộng một, hai, ba cho các cặp đã nêu. Rộng bốn sẽ làm dài ba, trái quy ước và chỉ là quay cặp trước. Kiểm từng cặp cộng hai cạnh rồi nhân hai đều dùng mười bốn que.')],[('Dài–rộng','6–1; 5–2; 4–3','cm')],hs('Mỗi độ dài của một cạnh còn xuất hiện ở cạnh đối diện.','Giữ một quy ước dài và rộng để tránh đếm lại hình quay.','Sau khi liệt kê, kiểm lại số que của từng đường bao.'),60,dict(kind='stick_pairs',sticks=14,unit_cm=1,include_square=True,expected=[[6,1],[5,2],[4,3]]))
 add(t,'Dùng hết 12 que dài 1 cm ghép một đường bao hình chữ nhật; cạnh là số nguyên dương que, không chồng, không bẻ. Lần này KHÔNG nhận hình vuông. Bạn liệt kê 5 cm × 1 cm, 4 cm × 2 cm và 3 cm × 3 cm. Giữ danh sách ấy, kiểm và sửa; hình quay chỉ tính một lần.',['12 que, mỗi que 1 cm; dùng hết','Loại hình vuông; cùng cặp cạnh khi quay vẫn là một hình'],'Danh sách hợp lệ được sửa',[
 step('Kiểm số que','Mỗi cặp cần hai cạnh dài và hai cạnh rộng.','Cả ba cặp đều dùng 12 que','Năm cộng một, bốn cộng hai và ba cộng ba đều bằng sáu; lấy hai lần đều là mười hai. Không có lỗi về tổng que.'),
 step('Kiểm điều kiện khác hình vuông','Đúng số que chưa đủ nếu trái điều kiện loại hình vuông.','5–1; 4–2','Cặp ba–ba có hai cạnh kề bằng nhau và bốn góc vuông nên là hình vuông, cần loại. Hai cặp còn lại đều thỏa; rộng tăng tiếp sẽ chỉ quay các cặp đã có.')],[('Các cặp dài–rộng','5–1; 4–2','cm'),('Nhận xét','Loại 3–3 vì là hình vuông, không phải vì sai số que','')],hs('Kiểm riêng số que và điều kiện về loại hình.','Một cặp cạnh bằng nhau có thỏa điều kiện lần này không?','Rà các cách khác theo quy ước không đếm hình quay.'),60,dict(kind='stick_pairs',sticks=12,unit_cm=1,include_square=False,expected=[[5,1],[4,2]]),student='Các cặp hợp lệ là 5 cm × 1 cm, 4 cm × 2 cm và 3 cm × 3 cm.')
 add(t,'Có 15 que thẳng dài 1 cm. Muốn dùng hết đúng 15 que ghép đường bao một hình chữ nhật, mỗi cạnh gồm số nguyên dương que, không bẻ hoặc xếp chồng và không dư que. Có làm được không? Giải thích bằng hai cặp cạnh đối diện.',['15 que bằng nhau, dùng hết không dư','Mỗi cạnh nguyên dương; hình chữ nhật có hai cặp cạnh đối diện bằng nhau'],'Khả năng ghép và lý do',[
 step('Ghép mỗi cạnh với cạnh đối diện','Hai cạnh đối diện phải dùng số que bằng nhau.','Tổng số que luôn chia thành các đôi','Một que trên cạnh này có thể ghép đôi với một que tương ứng ở cạnh đối diện. Cả đường bao vì vậy dùng một số chẵn que.'),
 step('Đối chiếu số que được cho','Một số lẻ không thể chia hết thành các đôi.','Không thể dùng hết 15 que','Mười lăm còn lẻ một que khi ghép đôi. Nếu bỏ que, bẻ que hoặc đổi góc thì đã trái luật; không tự thay quy định để tạo một hình.')],[('Khả năng','Không thể ghép theo đúng mọi điều kiện','')],hs('Xét quan hệ giữa một cạnh và cạnh đối diện trước khi thử kích thước.','Số que của cả đường bao có đặc điểm gì khi các cạnh được ghép thành đôi?','Kết luận phải giữ nguyên quy định dùng hết và không bẻ que.'),60,dict(kind='stick_pairs',sticks=15,unit_cm=1,include_square=True,expected=[]))
 t='assembled_cube_painted_faces'
 add(t,'Hai khối lập phương nhỏ A và B bằng nhau được dán sát nhau đúng một mặt trọn; không có khối nào khác. Sơn mọi mặt nhỏ còn lộ ra sau khi dán, kể cả mặt dưới; không sơn mặt bị dán. Không cần tính diện tích. Mỗi khối có mấy mặt nhỏ được sơn và cả cụm có bao nhiêu mặt nhỏ được sơn?',['Hai khối; chỉ cặp A–B tiếp xúc đúng một mặt','Sơn tất cả mặt còn lộ, kể cả dưới; không sơn mặt tiếp xúc'],'Số mặt sơn từng khối và cả cụm',[
 step('Đếm mặt lộ của từng khối','Mỗi khối có sáu mặt, một mặt tiếp xúc bị che.','5','Mỗi khối còn năm mặt để sơn; không chỉ lấy các mặt nhìn thấy từ một phía.', '6-1','mặt nhỏ mỗi khối'),
 step('Gộp hai khối và kiểm mặt chung','Mặt tiếp xúc gồm một mặt của A và một mặt của B, cả hai không được sơn.','10','Hai khối mỗi khối năm mặt cho mười mặt nhỏ được sơn. Kiểm từ mười hai mặt ban đầu, bỏ hai mặt tiếp xúc cũng còn mười.', '5+5','mặt nhỏ')],[('A',5,'mặt nhỏ'),('B',5,'mặt nhỏ'),('Cả cụm',10,'mặt nhỏ')],hs('Xét riêng mặt bị che của mỗi khối.','Một chỗ tiếp xúc che mặt của những khối nào?','Kiểm cả mặt dưới theo đúng quy tắc sơn đã cho.'),66,dict(kind='painted_assembly',cells={'A':[0,0,0],'B':[1,0,0]},expected_faces={'A':5,'B':5},expected_total=10))
 add(t,'Ba khối lập phương bằng nhau A, B, C được ghép thành một hàng thẳng theo thứ tự A–B–C; mỗi hai khối kề nhau dán trọn một mặt. Sơn mọi mặt còn lộ sau ghép, kể cả phía dưới, bỏ các mặt dán. Hỏi từng khối có mấy mặt nhỏ được sơn; có bao nhiêu khối được sơn đúng năm mặt và bao nhiêu khối đúng bốn mặt?',['Hàng thẳng A–B–C; chỉ A–B và B–C tiếp xúc','Sơn mọi mặt ngoài kể cả dưới; không sơn mặt dán'],'Phân loại số mặt được sơn',[
 step('Xét hai đầu hàng','Khối ở đầu chỉ có một khối kề nên bị che một mặt.','5','A và C mỗi khối còn năm mặt. Không tính mặt tiếp xúc là mặt ngoài dù nó thuộc cả khối.', '6-1','mặt nhỏ mỗi khối đầu'),
 step('Xét khối ở giữa','Khối giữa chạm hai khối ở hai mặt khác nhau.','4','B bị che hai mặt nên còn bốn. Vì vậy hai khối được sơn năm mặt và một khối bốn mặt.', '6-2','mặt nhỏ'),
 step('Kiểm toàn cụm','Cộng mặt lộ của từng khối rồi kiểm số mặt bị che.','14','Năm cộng bốn cộng năm bằng mười bốn. Ban đầu mười tám mặt nhỏ, hai chỗ dán che bốn mặt, cũng còn mười bốn.', '5+4+5','mặt nhỏ')],[('Các khối','A: 5; B: 4; C: 5','mặt nhỏ'),('Đúng năm mặt',2,'khối'),('Đúng bốn mặt',1,'khối')],hs('Phân biệt vị trí đầu hàng với vị trí ở giữa.','Đếm số khối kề từng khối trước khi đếm mặt còn lộ.','Đối chiếu tổng số khối trong các nhóm với cả cụm.'),118,dict(kind='painted_assembly',cells={'A':[0,0,0],'B':[1,0,0],'C':[2,0,0]},expected_faces={'A':5,'B':4,'C':5},expected_total=14))
 add(t,'Bốn khối lập phương bằng nhau ghép kín thành một tầng gồm hai hàng và hai cột: hàng trước A, B; hàng sau C, D. Các cặp dán trọn một mặt là A–B, A–C, B–D, C–D; không có tiếp xúc mặt nào khác. Sơn mọi mặt còn lộ, kể cả dưới. Bạn ghi: Mỗi khối có 5 mặt sơn vì đã ghép với một khối. Giữ câu ấy, kiểm số mặt sơn từng khối và toàn cụm.',['Một tầng 2 hàng, 2 cột; cặp tiếp xúc A–B, A–C, B–D, C–D','Không tiếp xúc mặt khác; sơn mọi mặt còn lộ kể cả dưới'],'Số mặt sơn và sửa nhận xét',[
 step('Dùng danh sách tiếp xúc cho từng khối','Một khối có thể tiếp xúc nhiều hơn một khối khác.','Mỗi khối bị che 2 mặt','A kề B và C; B kề A và D; C kề A và D; D kề B và C. Mỗi khối bị che hai mặt khác nhau.'),
 step('Đếm mặt còn lộ','Sáu mặt ban đầu trừ số mặt bị che của chính khối đó.','4','Mỗi khối có bốn mặt nhỏ được sơn. Câu ghi năm mặt đã bỏ sót một chỗ tiếp xúc ở mỗi khối.', '6-2','mặt nhỏ mỗi khối'),
 step('Kiểm toàn cụm','Cộng bốn nhóm mặt thuộc bốn khối khác nhau.','16','Bốn khối mỗi khối bốn mặt được mười sáu mặt nhỏ. Kiểm hai mươi bốn mặt ban đầu, bốn chỗ dán che tám mặt, còn mười sáu.', '4*4','mặt nhỏ')],[('Mỗi khối',4,'mặt nhỏ'),('Cả cụm',16,'mặt nhỏ'),('Nhận xét','Mỗi khối bị che hai mặt, không phải một','')],hs('Dựa vào các cặp tiếp xúc đã cho, không suy từ một hướng nhìn.','Với mỗi khối, đánh dấu đủ các khối kề nó.','Kiểm cả cách cộng mặt lộ và cách bỏ các mặt bị dán.'),118,dict(kind='painted_assembly',cells={'A':[0,0,0],'B':[1,0,0],'C':[0,1,0],'D':[1,1,0]},expected_faces={'A':4,'B':4,'C':4,'D':4},expected_total=16),student='Mỗi khối có 5 mặt sơn vì đã ghép với một khối.')

def calc(expr,typ):
 def f(n):
  if isinstance(n,ast.Constant) and type(n.value) is int:return typ(n.value)
  if isinstance(n,ast.BinOp):
   a,b=f(n.left),f(n.right)
   if isinstance(n.op,ast.Add):return a+b
   if isinstance(n.op,ast.Sub):return a-b
   if isinstance(n.op,ast.Mult):return a*b
   if isinstance(n.op,ast.Div):return a/b
  raise ValueError(expr)
 return f(ast.parse(expr,mode='eval').body)
def oracle(o):
 k=o['kind']
 if k=='grid_rectangles':
  # Enumerate opposite boundary choices rather than the child's size-grouping method.
  rects=[(x1,x2,y1,y2) for x1,x2 in combinations(range(o['columns']+1),2) for y1,y2 in combinations(range(o['rows']+1),2)]
  assert len(rects)==o['expected'];return rects
 if k=='stick_pairs':
  pairs=[]
  for a in range(1,o['sticks']+1):
   for b in range(1,a+1):
    if 2*a+2*b==o['sticks'] and (o['include_square'] or a!=b):pairs.append([a,b])
  pairs.sort(key=lambda x:x[1]);assert pairs==o['expected'];return pairs
 if k=='painted_assembly':
  cells=o['cells'];occupied={tuple(p) for p in cells.values()};faces={}
  for name,p in cells.items():
   faces[name]=sum(tuple(p[i]+d[i] for i in range(3)) not in occupied for d in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)])
  assert faces==o['expected_faces'] and sum(faces.values())==o['expected_total'];return faces
 if k=='triangles':
  pts=o['points']
  def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
  def on(a,b,c):return cross(a,b,c)==0 and all(min(a[i],b[i])<=c[i]<=max(a[i],b[i]) for i in (0,1))
  def edge(a,b):return any(on(pts[u],pts[v],pts[a]) and on(pts[u],pts[v],pts[b]) for u,v in o['segments'])
  found=[tuple(sorted(c)) for c in combinations(pts,3) if cross(*(pts[n] for n in c))!=0 and all(edge(a,b) for a,b in combinations(c,2))]
  assert sorted(found)==sorted(tuple(sorted(c)) for c in o['expected']);return found
 raise ValueError(k)
def main():
 build();assert len(ROWS)==9
 OUT.mkdir(exist_ok=True)
 source=[];chat=[];qas=[];checks=[]
 for r in ROWS:
  line=dump(r);h=sha(line.encode());source.append(line)
  check=dict(sample_id=r['sample_id'],source_row_sha256=h,independent_finite_enumeration=oracle(r['gap_oracle']),numeric_checks=[])
  for s in r['worked_steps']:
   if s['expression']:
    a,b=calc(s['expression'],Fraction),calc(s['expression'],Decimal)
    assert a==Fraction(b)==Fraction(s['result'])
    check['numeric_checks'].append(dict(expression=s['expression'],fraction=str(a),decimal=str(b)))
  checks.append(check)
  qas.append(dict(sample_id=r['sample_id'],source_row_sha256=h,status='AUTHOR_SELF_QA_PASS_CROSS_REVIEW_PENDING',review_role='AUTHOR_SELF_QA',criteria={k:'PASS' for k in ['correct_math_or_explicit_guard','givens_request_consistent','steps_reasons_units_check','grade_scope','initial_and_all_three_hints_answer_free','student_work_grounded_no_unseen_inference','schema_provenance_unique']},basis='Actual authored problem, givens, request, student quote, steps, reasons, explanations, answers, initial guidance and three hints read; finite independent representation oracle and Fraction/Decimal checks. No human or external-review attestation.'))
  for c in chat_records(r):c.update(source_row_sha256=h,acceptance_status=r['acceptance_status'],quality_status=r['quality_status']);chat.append(c)
 for name,rows in [('cases.jsonl',source),('chat.jsonl',[dump(c) for c in chat]),('self_qa.jsonl',[dump(q) for q in qas]),('oracle_checks.jsonl',[dump(c) for c in checks])]:
  (OUT/name).write_text('\n'.join(rows)+'\n',encoding='utf8',newline='\n')
 manifest=dict(case_count=9,chat_count=len(chat),form_count=3,status='DRAFT_AWAITING_CONTENT_CROSS_REVIEW',trained=False,drive_mutated=False,files={p.name:dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in OUT.glob('*.jsonl')})
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(manifest))
if __name__=='__main__':main()
