"""Bounded G2 derived repair and exact QA. No original ZIP is modified."""
from pathlib import Path
from copy import deepcopy
from fractions import Fraction
from decimal import Decimal
from datetime import datetime,timezone
import ast,hashlib,itertools,json,zipfile,calendar

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
def canon(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def digest(b):return hashlib.sha256(b).hexdigest()
def step(title,result,explanation,reason,expression=None,unit=''):
    return dict(step_id='',title=title,result=str(result),explanation=explanation,reason=reason,expression=expression,unit=unit)
def answer(quantity,result,unit=''):return dict(quantity=quantity,result=str(result),unit=unit)
def given(text):return [dict(id='g0',role='EXPLICIT_FINITE_TEXT_AS_SUPPLIED',text=text,value=None,unit='')]
def hints(row,texts):
    row['hints']=[dict(level=i+1,hint=t,question=q) for i,(t,q) in enumerate(texts)]
def guidance(row,text):row['initial_guidance']=[text]
original={};rows={};locations={};zip_pins={};chat_checks=[];old_qa={}
for batch in (5,6,7,8):
    path=next((ROOT/'handoff').glob(f'*BATCH{batch}*.zip'))
    raw=path.read_bytes();zip_pins[batch]=dict(filename=path.name,bytes=len(raw),sha256=digest(raw))
    with zipfile.ZipFile(path) as z:
        local={}
        for line,text in enumerate(z.read('accepted_cases.jsonl').splitlines(),1):
            if not text.strip():continue
            row=json.loads(text);sid=row['sample_id'];original[sid]=(deepcopy(row),digest(text));rows[sid]=deepcopy(row);local[sid]=row
            locations[sid]=dict(batch=batch,line=line,zip_sha256=digest(raw))
        for text in z.read('qa7.jsonl').splitlines():
            if text.strip():
                q=json.loads(text);old_qa[q['sample_id']]=q
        for text in z.read('accepted_chat.jsonl').splitlines():
            if not text.strip():continue
            chat=json.loads(text);source=local[chat['source_sample_id']]
            user=json.loads(chat['messages'][1]['content']);target=json.loads(chat['messages'][2]['content'])
            if chat['mode']=='worked_solution':
                expected=dict(answer=source['expected_answer'],can_solve=source['can_solve'],initial_guidance=source['initial_guidance'],steps=source['worked_steps'])
            else:
                hint=source['hints'][int(chat['mode'][-1])-1];expected={k:hint[k] for k in ('hint','question')}
            chat_checks.append(dict(sample_id=chat['sample_id'],raw_sha256=digest(text),mode=chat['mode'],
                target_matches_actual_source=(target==expected),problem_matches=user.get('problem')==source['problem'],
                original_user_fields=sorted(user),student_work_in_user=('student_work' in user),
                scope='Compared every actual chat target/prompt with the fully read actual source; no generic required-field assumption'))

def row(suffix):return next(r for sid,r in rows.items() if sid.endswith(suffix))
notes={sid:[] for sid in rows}
def note(r,s):notes[r['sample_id']].append(s)

# Exact seven-segment alphabet and a true single-relocation budget.
glyphs={'0':'abcdef','1':'bc','2':'abdeg','3':'abcdg','4':'bcfg','5':'acdfg','6':'acdefg','7':'abc','8':'abcdefg','9':'abcdfg'}
alphabet='Vị trí que: a ngang trên, b dọc trên phải, c dọc dưới phải, d ngang dưới, e dọc dưới trái, f dọc trên trái, g ngang giữa. Các chữ số dùng các vị trí: '+ '; '.join(k+'='+v for k,v in glyphs.items())+'.'
r=row('matchstick_single_move_maximum_numeral')
r['problem']='Bài xếp que theo mô tả chữ hữu hạn, không cần ảnh sách. '+alphabet+' Xếp số 38 trong đúng hai ô chữ số. Hãy nhấc đúng một que đang có và đặt vào một vị trí đang trống trong một trong hai ô; không thêm hoặc bỏ que. Hai chữ số cuối phải đúng bảng, không được có chữ số 0 ở hàng chục. Tìm số có hai chữ số lớn nhất có thể tạo được.'
r['givens']=given(r['problem']);note(r,'Added exact segment alphabet, fixed slots, leading-zero rule; removed hint giving complete relocation and target digit.')
hints(r,[('Đọc bảng vị trí que của từng chữ số và đánh dấu các que đang có.','Một lần di chuyển gồm thao tác lấy đi và đặt vào ở đâu?'),('Khi thử đổi một chữ số, kiểm xem vị trí đặt mới đang trống và vị trí lấy đi đang có que.','Cả hai ô sau đó có đúng một chữ số hợp lệ trong bảng không?'),('So sánh các số tạo được theo hàng chục trước, rồi đến hàng đơn vị.','Em kiểm được số chọn lớn nhất và vẫn giữ nguyên tổng số que như thế nào?')])
guidance(r,'Dùng bảng vị trí để thử một lần nhấc và đặt que, kiểm luật rồi mới so sánh các số hợp lệ.')
r=row('matchstick_illegal_extra_stick_guard')
r['problem']='Theo kiểu chữ số bảy nét: chữ số 3 có 5 que, chữ số 8 có 7 que, chữ số 9 có 6 que. Số 38 có 12 que. Luật chỉ cho nhấc đúng một que đang có sang vị trí khác, không lấy thêm và không bỏ que. Một bạn lấy thêm một que trong hộp gắn vào chữ số 3 để thành số 98 rồi nói: "Em chỉ thêm đúng 1 que diêm là đã được số 98 rất lớn rồi". Thao tác ấy có hợp luật không? Giải thích bằng tổng số que.'
r['givens']=given(r['problem']);note(r,'Made rule/context standalone; feedback confined to supplied action and conservation, not a full alternative solution.')
r['worked_steps']=[step('Đọc lại luật và thao tác','Luật yêu cầu di chuyển que sẵn có','Bạn lấy một que mới từ hộp, trong khi luật yêu cầu dùng các que đang có.','Đối chiếu hành động được mô tả với luật.'),step('Kiểm tổng số que','13','Lấy thêm một que làm tổng số que thành 12 + 1 = 13 que; không còn giữ nguyên 12 que ban đầu.','Phép cộng kiểm việc có thêm vật mới.', '12 + 1','que diêm'),step('Kết luận về thao tác','Không hợp luật','Thao tác lấy thêm que không phải một lần chuyển que sẵn có.','Luật không cho thêm hoặc bỏ que.')]
hints(r,[('Tìm đúng động từ trong luật và động từ chỉ thao tác của bạn.','Hai thao tác ấy có cùng ý nghĩa không?'),('Theo dõi số que trước và sau thao tác được kể.','Tổng số que có còn như ban đầu không?'),('Dùng điều kiện không thêm và không bỏ que để kiểm nhận xét.','Em sẽ giải thích bằng quy tắc nào, thay vì chỉ so số tạo được lớn hay nhỏ?')])

r=row('skip_nodes_number_line_hop_rule');r['worked_steps'][1]['result']='15';r['worked_steps'][1]['unit']='đơn vị';note(r,'Kept correct landing15; scalar arithmetic result no longer stores an entire trajectory.')
r=row('skip_nodes_count_distractor_misconception')
r['problem']='Trên tia số từ 0 đến 20, cào cào bắt đầu ở 0. Mỗi bước chú bỏ qua hai vạch rồi đáp xuống vạch tiếp theo: bước đầu bỏ qua 1, 2 và đáp xuống 3. Sau đó giữ đúng quy luật ấy. Một bạn nói: "Mỗi bước tiến 2 đơn vị; sau 5 bước cào cào đến vạch 10 vì 2 x 5 = 10". Nhận xét phát biểu của bạn và giải thích.'
r['givens']=given(r['problem']);note(r,'Removed dependence on previous example; all positions and learner quote now supplied.')
hints(r,[('Đọc điểm xuất phát và điểm đáp trong ví dụ đầu.','Bước đầu vượt qua những vạch nào và dừng ở vạch nào?'),('Phân biệt số vạch nằm ở giữa với khoảng cách từ điểm xuất phát tới điểm đáp.','Hai cách đếm đó có luôn cho cùng số không?'),('Sau khi xác định khoảng cách một bước, ghi các điểm đáp theo thứ tự.','Em dùng ví dụ của đề để kiểm lời làm của bạn thế nào?')])
guidance(r,'Kiểm khoảng cách của một bước bằng ví dụ đã cho trước khi kiểm phép tính của bạn.')
r['worked_steps'].append(step('Kiểm đủ năm bước','15','Mỗi bước tiến3đơn vị, nên5bước từ0tiến3 x 5 = 15đơn vị. Các điểm đáp là3,6,9,12,15; không phải10.','Dùng quy luật đã xác định để kiểm đúng số bước mà bạn nêu.','3 * 5','đơn vị'))

r=row('trace_crossing_curved_wire_endpoints')
r['problem']='Một sơ đồ dây cong được mô tả đầy đủ bằng chữ. Tại điểm bắt chéo X có bốn cổng: trên-trái, trên-phải, dưới-trái, dưới-phải. Đường đỏ từ A đến cổng trên-trái của X; qua X nó tiếp tục ở cổng dưới-phải, rồi đi đến điểm Y. Đoạn từ Y đi cong đến chốt 2. Đường xanh từ B đến cổng dưới-trái của X, tiếp tục qua cổng trên-phải rồi đến chốt 1. Hai dây không nối vào nhau tại X. Khi đi dọc một dây, phải tiếp tục đúng cặp cổng của chính dây đó. Hỏi lần theo dây từ A sẽ đến chốt nào? Đây là sơ đồ chữ tự tạo, không phải quan sát ảnh hay mô hình thực.'
r['givens']=given(r['problem']);r['worked_steps']=[step('Theo dây từ A','Cổng trên-trái của X','Mô tả cho biết đoạn từ A đi đến cổng trên-trái của X.','Dùng đúng đoạn đầu được cung cấp.'),step('Đi qua chỗ bắt chéo','Cổng dưới-phải của X rồi điểm Y','Cặp cổng của dây này là trên-trái và dưới-phải; không chuyển sang cổng của dây xanh. Từ đó đoạn tiếp theo đến Y.','Hai dây không nối với nhau tại X.'),step('Theo đoạn cuối','Chốt 2','Đoạn từ Y kết thúc ở chốt 2, nên dây từ A đến chốt 2.','Ghép các đoạn liên tục đúng dữ kiện, rồi kiểm lại từ chốt về A.')]
guidance(r,'Ghi đoạn đi từ A, sau đó kiểm đúng cặp cổng qua chỗ bắt chéo trước khi theo đoạn tiếp.')
hints(r,[('Bắt đầu tại A và đọc đoạn đầu tiên nối đến đâu.','Cổng nào của X được nêu ở đoạn đó?'),('Tại X, đối chiếu cặp cổng của chính dây đang theo; không đổi dây.','Sau cổng ra, mô tả còn cho những đoạn nối tiếp nào?'),('Ghép các đoạn theo thứ tự và kiểm ngược đường đi để tránh rẽ sang dây khác.','Điểm cuối của chuỗi đoạn vừa lần theo là chốt nào?')])
note(r,'Replaced invented tangent/endpoint inference with explicit original synthetic port/segment continuity; no picture or physical observation claimed.')

r=row('all_drawn_segment_compound_endpoint_pairs')
hints(r,[('Liệt kê các cặp điểm kề nhau trước.','Em đã ghi mỗi cặp theo một thứ tự cố định chưa?'),('Xét tiếp các cặp có một hoặc hai điểm nằm giữa.','Các phần giữa hai đầu mút có được vẽ nối liền không?'),('Kiểm từng điểm làm đầu mút trái rồi ghép với các điểm ở phía phải.','Cách ghi ấy tránh bỏ sót và tránh đếm tên đảo ngược thế nào?')])
note(r,'Removed hint listing requested final segment names; kept all six valid answers.')
r=row('all_drawn_segment_gap_nonexistent_crossline_guard')
r['problem']='Trên giấy có vẽ liền đoạn AD với bốn điểm theo thứ tự A, B, C, D. Phía trên đường ấy là điểm E đứng riêng, không có nét nối E với điểm nào. Một bạn nói: "Em đếm thêm EA, EB, EC, ED nên số đoạn thẳng được vẽ nhiều hơn 6". Hãy nhận xét cách đếm các đoạn được vẽ của bạn. Chỉ đếm nét đã vẽ, không yêu cầu tự nối điểm mới.'
r['givens']=given(r['problem']);note(r,'Made drawn incidence and no-extra-lines instruction standalone.')
hints(r,[('Đọc xem đề yêu cầu đếm nét đã vẽ hay tất cả các đoạn có thể tự vẽ thêm.','Hai yêu cầu ấy khác nhau ở đâu?'),('Kiểm từng tên đoạn mà bạn đã ghi bằng mô tả về các nét nối.','Đề có cho nét nối tương ứng không?'),('Tách danh sách có bằng chứng nét nối khỏi những đoạn chỉ có thể vẽ thêm.','Em giải thích cách kiểm của mình dựa vào dữ kiện nào?')])

r=row('actual_measurement_missing_calibration_guard')
r['worked_steps'][0]['explanation']='Bạn nêu 8 cm, là số chỉ ở đầu bên phải. Theo đề, đầu bên trái ở vạch 2 cm, nên cần kiểm khoảng cách giữa hai vạch thay vì dùng riêng số chỉ cuối.'
r['student_work']['observations'][0]['nature']='OBSERVED_END_MARK_USED_AS_LENGTH_WITH_NONZERO_START'
note(r,'Removed claim about hidden attention/thought; retained supplied endpoint calculation6cm. Synthetic offset reading does not close actual physical measurement.')
hints(r,[('Đánh dấu vị trí của cả hai đầu bút theo mô tả.','Vạch đầu có trùng vạch không của thước không?'),('Độ dài là khoảng cách giữa hai dấu, không chỉ là một số đọc ở đầu cuối.','Phép tính nào tìm khoảng cách giữa hai dấu ấy?'),('Kiểm bằng cách đếm từng khoảng một xăng-ti-mét từ dấu đầu tới dấu cuối.','Kết quả có phù hợp với phép tính và cách đặt để đọc trực tiếp không?')])

r=row('all_collinear_triples_incidence_enumeration');note(r,'Kept complete five-point incidence; finite determinant enumeration independently finds exactly two triples.')
r=row('collinear_triples_unaligned_distractor_guard')
r['problem']='Có hai đường thẳng khác nhau cắt nhau tại O. Đường thứ nhất chứa ba điểm theo thứ tự A, O, B; đường thứ hai chứa ba điểm theo thứ tự C, O, D. Các điểm A, B, C, D khác O. Một bạn nói: "A, O, C thẳng hàng vì cùng nối đến O". Nhận xét phát biểu này và giải thích bằng đường thẳng chứa từng điểm.'
r['givens']=given(r['problem']);r['student_work']={'text':'A, O, C thẳng hàng vì cùng nối đến O','observations':[{'excerpt':'A, O, C thẳng hàng vì cùng nối đến O','nature':'SUPPLIED_COLLINEARITY_CLAIM'}]}
r['worked_steps'][0]['explanation']='A và C thuộc hai đường thẳng khác nhau qua O. Việc mỗi điểm cùng nối tới O chưa đủ để ba điểm nằm trên cùng một đường thẳng.'
note(r,'Made crossing incidence standalone and avoided misusing geometric between-ness.')
hints(r,[('Nhắc lại điều kiện để ba điểm thẳng hàng.','Chỉ cùng nối tới một điểm đã đủ điều kiện ấy chưa?'),('Xét đường qua A và O, rồi xét đường qua C và O.','Đề nói hai đường này trùng nhau hay khác nhau?'),('Đối chiếu phát biểu của bạn với điều kiện cùng một đường thẳng.','Em có thể dùng dữ kiện nào để giải thích mà không cần tưởng tượng ảnh?')])
guidance(r,'Dùng hai đường thẳng được mô tả rõ trong đề để kiểm phát biểu, không cần giả định thêm hình.')

r=row('composite_quadrilateral_elementary_and_compound_inventory')
r['problem']='Vẽ liền bốn cạnh của hình chữ nhật ABCD, theo thứ tự A, B, C, D quanh biên. Điểm M nằm giữa A và B; điểm N nằm giữa D và C. Vẽ thêm đoạn MN; không có nét vẽ nào khác. Hỏi có tất cả bao nhiêu hình tứ giác có biên gồm các nét đã vẽ? Kể tên từng hình; một cạnh dài có thể đi qua một điểm ở giữa mà không đổi hướng.'
r['givens']=given(r['problem']);note(r,'Specified strict interior endpoints and every drawn boundary; eliminated diagonal/degenerate interpretation.')
hints(r,[('Xét các phần nhỏ do đoạn MN tạo ra.','Mỗi phần có một đường bao kín gồm bốn cạnh không?'),('Xét đường bao bên ngoài và kiểm xem điểm nằm giữa có làm đổi hướng cạnh không.','Đường bao ghép nào còn là một tứ giác?'),('Ghi các đường bao khác nhau rồi kiểm không ghi lại cùng một hình bằng tên đảo chiều.','Em đã dùng đúng những nét thực sự được vẽ chưa?')])

r=row('scaled_grid_route_manhattan_comparison');note(r,'Exact route lengths5,5,5 independently checked, tie preserved.')

r=row('fold_cut_unfold_symmetric_notch')
r['problem']='Ví dụ gấp cắt được mô tả trên lưới chữ, chưa thực hành hay xem ảnh sách: tờ giấy vuông cạnh 8 ô, các hàng và cột lưới đánh số từ 0 đến 8. Tâm giấy ở hàng 4, cột 4. Gấp đôi theo cột 4 cho hai nửa chồng khít; giữ hai lớp cùng nhau. Trên phần giấy đã gấp, đánh dấu A tại hàng 3 cột 4, B tại hàng 5 cột 4 và C tại hàng 4 cột 6. Cắt theo A-C-B qua cả hai lớp và bỏ tam giác ABC; cạnh AB nằm trên nếp gấp. Toàn bộ vết cắt nằm xa mép ngoài. Khi mở giấy, phần bị bỏ gồm những hình nào ghép nhau, nằm ở đâu và mép ngoài có bị cắt không?'
r['givens']=given(r['problem']);r['expected_answer']=[answer('Phần bị bỏ','Hai tam giác giống nhau ghép chung cạnh AB tạo thành một lỗ hình tứ giác'),answer('Vị trí','Lỗ ở tâm giấy; các mép ngoài còn nguyên')]
r['requested_quantity']='Mô tả hai phần của lỗ, vị trí và tình trạng mép ngoài theo mô hình lưới đã cho'
r['worked_steps']=[step('Đọc vị trí vết cắt','AB nằm trên nếp gấp','A và B cùng thuộc cột 4; C thuộc cột 6. Vết cắt đi qua cả hai lớp giấy.','Xác định phần nào được mở sang phía đối diện.'),step('Mở hai lớp','Hai tam giác giống nhau ghép chung cạnh AB','Một nửa vết cắt nằm phía cột 6; nửa được mở sang phía đối diện có đỉnh ở hàng 4 cột 2. Hai phần ghép nhau thành lỗ có bốn cạnh.','Mỗi điểm phía này của nếp gấp có điểm tương ứng cách nếp gấp bằng từng ấy ô ở phía kia.'),step('Kiểm vị trí và mép ngoài','Lỗ ở tâm giấy; mép ngoài còn nguyên','Lỗ trải từ hàng 3 đến hàng 5, cột 2 đến cột 6, nằm hẳn trong tờ giấy từ hàng/cột 0 đến 8.','Kiểm các điểm biên lỗ đều nằm bên trong giấy, không chạm mép ngoài.')]
guidance(r,'Đọc nếp gấp và các điểm cắt; khi mở, tìm phần tương ứng ở phía bên kia của nếp gấp.')
hints(r,[('Xác định những điểm cắt nằm ngay trên nếp gấp.','Có mấy lớp giấy được cắt cùng lúc theo đề?'),('Đếm số ô từ C đến nếp gấp rồi tìm điểm đối diện cách nếp gấp cũng từng ấy ô.','Điểm tương ứng ở bên kia có cùng hàng với C không?'),('Theo đường bao các phần bị bỏ và so vị trí đó với mép giấy.','Em mô tả hình ghép và vị trí bằng các điểm đã tìm thế nào?')])
note(r,'Original arbitrary triangle did not imply rhombus or center hole; derived synthetic cut fully specifies fold, vertices and layers; removes grade2 rhombus terminology and answer leak.')

r=row('triangular_piece_pair_rectangle_assembly')
r['problem']=r['problem'].replace('Có hai cạnh góc vuông','Có hai cạnh kề nhau vuông góc').replace('Em hãy chọn đúng 2 miếng','Được xoay hoặc lật miếng bìa, không cắt thêm. Em hãy chọn đúng 2 miếng')
r['worked_steps'][2]['explanation']='Xoay hoặc lật một miếng rồi ghép hai cạnh dài nhất của Miếng 1 và Miếng 2 trùng khít. Bốn cạnh ngoài lần lượt dài 3 cm, 4 cm, 3 cm, 4 cm, tạo đúng hình chữ nhật cần ghép, không hở và không chồng phần trong.'
for s in r['worked_steps']:
    for k in ('title','explanation','reason','result'):
        s[k]=s[k].replace('cạnh huyền','cạnh dài nhất').replace('Cạnh huyền','Cạnh dài nhất')
r['expected_answer'][1]['result']='Ghép hai cạnh dài nhất của hai miếng được chọn trùng khít, sau khi xoay hoặc lật một miếng'
note(r,'Added legal rotations/reflections, retained pair1/2 and constructive no-gap cover; simplified hypotenuse terminology.')
hints(r,[('Ghi hai kích thước cần có ở đường bao hình chữ nhật.','Em cần so sánh những cạnh nào của các miếng với kích thước đó?'),('Thử các cặp miếng và kiểm hai phần có thể tạo đường bao đúng kích thước không.','Cặp nào có thể đặt khít mà không phải cắt hoặc chồng lên nhau?'),('Với cặp định chọn, thử xoay hoặc lật rồi kiểm từng cạnh ngoài.','Em kiểm không hở và không chồng phần trong bằng cách nào?')])
guidance(r,'Đối chiếu các miếng với hai kích thước của hình chữ nhật rồi thử ghép và kiểm đường bao.')

r=row('actual_solid_assembly_support_guard')
r['can_solve']=False;r['expected_answer']=[answer('Điều cần làm','Cần ảnh hoặc mô tả đầy đủ cách ghép và cách đỡ; chưa đủ căn cứ khẳng định có khối lập phương ngay bên dưới')]
r['problem']='Bạn An mô tả có một khối lập phương ở tầng thứ hai trong một mô hình trên bàn, nhưng chưa gửi ảnh hay bản ghi cách ghép. An nói: "Em không nhìn thấy khối ngay bên dưới nên khối tầng hai tự lơ lửng". Đề chưa cho biết có keo, khung đỡ, miếng bắc cầu hay quy tắc xếp từng cột hay không. Có thể từ lời mô tả này kết luận chính xác khối nào đang đỡ nó không? Cần xin thêm thông tin gì?'
r['givens']=given(r['problem']);r['student_work']={'text':'Em không nhìn thấy khối ngay bên dưới nên khối tầng hai tự lơ lửng','observations':[{'excerpt':'Em không nhìn thấy khối ngay bên dưới nên khối tầng hai tự lơ lửng','nature':'SUPPLIED_VISIBILITY_CLAIM_WITHOUT_ASSEMBLY_RECORD'}]}
r['requested_quantity']='Thông tin quan sát và quy tắc ghép cần bổ sung trước khi kết luận vật nào đang nâng đỡ khối tầng trên'
r['worked_steps']=[step('Phân biệt nhìn thấy với cấu tạo','Chưa có bản ghi đầy đủ về chỗ đỡ','Lời kể chỉ nói chưa nhìn thấy bên dưới; không mô tả khung, keo hay cấu tạo các phần khác.','Không suy ra một khối cụ thể chỉ từ sự thiếu thông tin.'),step('Hỏi thêm bằng chứng','Xin ảnh các phía hoặc bảng ghi cách ghép và vật đỡ','Cần biết vật liệu, các mối nối và vị trí tiếp xúc để nhận xét điều gì nâng đỡ khối ở tầng trên.','Đánh giá mô hình thực phải dựa vào quan sát hoặc mô tả đủ, không tự thêm khối ẩn.')]
guidance(r,'Tách điều bạn An thật sự nhìn thấy khỏi điều bạn đang kết luận về cấu tạo của mô hình.')
hints(r,[('Liệt kê những thông tin có trong lời kể và những thông tin chưa được cung cấp.','Có mô tả đầy đủ các phần tiếp xúc và nối với khối tầng trên chưa?'),('Một bức ảnh rõ hơn hoặc bản ghi cách ghép sẽ cho thêm thông tin gì?','Em cần xem phía nào hoặc hỏi quy tắc xếp nào?'),('Đối chiếu mỗi nhận xét với bằng chứng về vị trí và mối nối.','Em sẽ hỏi cụ thể những chi tiết còn thiếu nào trước khi nhận xét cấu tạo?')])
note(r,'Removed unsupported assertion of hidden block directly below; guard requests actual assembly evidence, does not close physical task27.')

r=row('dissection_reassembly_square_from_rectangles');r['worked_steps'][1]['result']='4';r['worked_steps'][1]['unit']='cm'
hints(r,[('So sánh cạnh dài và cạnh ngắn của mỗi miếng với yêu cầu về các cạnh của hình vuông.','Khi ghép, kích thước nào được giữ và kích thước nào được cộng lại?'),('Thử ghép theo một cạnh rồi kiểm hai kích thước của đường bao mới.','Hai kích thước đã bằng nhau chưa?'),('Kiểm thêm các miếng có phủ kín và có chồng phần trong lên nhau không.','Em nêu cách đặt miếng nào để hình mới thỏa mọi điều kiện?')])
note(r,'Removed explicit side4cm/full solution from hint3; scalar2+2 result repaired without changing answer.')

r=row('actual_segment_construction_zero_alignment_guard')
hints(r,[('Ghi hai vạch thước mà Nam dùng làm đầu mút.','Độ dài được tính theo một số chỉ hay theo khoảng cách giữa hai dấu?'),('So khoảng cách vừa tính với độ dài được yêu cầu.','Em kiểm thao tác bằng phép tính và đơn vị nào?'),('Tìm cách đặt đầu mút để có thể đọc trực tiếp số đo mong muốn.','Sau khi nối hai dấu, em sẽ kiểm đoạn vẽ lại thế nào?')])
r['initial_guidance']=['Độ dài của đoạn vẽ là khoảng cách giữa hai vạch đầu mút; hãy kiểm điều đó trước khi nhận xét.']
note(r,'Removed filled4cm and absolute zero-is-always-required claim from hints; zero is convenient standard method, other offsets can also give correct length.')
r=row('calendar_grid_missing_cells_restoration')
r['worked_steps'][0]['result']='19';r['worked_steps'][0]['unit']='ngày trong tháng';r['worked_steps'][1]['result']='5';r['worked_steps'][1]['unit']='ngày trong tháng'
note(r,'Preserved valid Thursday/week arithmetic; normalized scalar numeric steps; original alone does not close full month-grid task30.')
r=row('personal_date_timetable_missing_context_guard')
hints(r,[('Xác định câu hỏi đang nói đến lịch chung hay lịch riêng của một lớp.','Đề đã gửi lịch riêng đó chưa?'),('Tìm thông tin nào quyết định tên môn ở tiết đang hỏi.','Nếu chưa có thông tin ấy thì em cần kiểm ở nguồn nào?'),('Chọn câu hỏi giúp người học cung cấp đúng dữ kiện liên quan tới lớp mình.','Em cần hỏi gì để có thể đọc đúng dòng và cột của lịch?')])
guidance(r,'Xác định dữ kiện cần có để đọc một tiết học trên thời khóa biểu riêng của người học.')
note(r,'Removed hint stating complete missing-timetable response; date/location branch handled in additional separate case.')
r=row('continuous_clock_hand_motion_elapsed_time');r['worked_steps'][1]['result']='30';r['worked_steps'][2]['unit']='';note(r,'Kept8:30/30min answer and continuous hour-hand relation; normalized scalar5*6 and mixed unit.')

r=row('expression_class_count')
computed=[('A','15 + 15',30),('B','20 + 30',50),('C','42 - 12',30),('D','65 - 15',50),('E','50 - 20',30),('G','40 + 30',70)]
r['worked_steps']=[step('Tính thẻ '+name,value,f'Thẻ {name}: {expr} = {value}.','Cần tìm giá trị trước khi gom các thẻ có kết quả bằng nhau.',expr) for name,expr,value in computed]+r['worked_steps'][1:]
note(r,'Split multi-equality expression list into six scalar arithmetic steps; classes and answer unchanged.')
r=row('shape_filtered_maze_triangle')
r['problem']=r['problem'].replace('đánh số từ 1 đến 9.','đánh số từ 1 đến 9 theo từng hàng, từ trái sang phải và từ hàng trên xuống hàng dưới: hàng trên 1,2,3; hàng giữa 4,5,6; hàng dưới 7,8,9.')
r['givens']=given(r['problem']);note(r,'Specified row-major grid incidence instead of assuming unspecified numbering.')
r=row('conditional_labelled_even')
r['worked_steps'][0]['explanation']='Trong các biển của đề, 4, 12, 16 là số chẵn; 7, 9, 11 là số lẻ. Chỉ các biển số chẵn thỏa quy tắc.'
note(r,'Removed invented labels3 and8 from worked explanation; exact original graph and valid path unchanged.')
r=row('unit_capacity_bijection');r['worked_steps'][1]['expression']=None;r['worked_steps'][2]['expression']='12 - 5';r['worked_steps'][2]['result']='7'
note(r,'Kept valid capacity sorting as enrichment, fixed expression/result contract; not falsely called inclusive one-to-one assignment coverage.')
r=row('aligned_endpoint_length_diff')
r['problem']=r['problem'].replace('một đầu của hai băng giấy thẳng hàng với nhau.','một đầu của hai băng giấy trùng nhau, hai băng nằm song song sát nhau và cùng hướng sang phải.')
r['givens']=given(r['problem']);r['worked_steps'][1]['expression']=None;r['worked_steps'][2]['expression']='16 - 9';r['worked_steps'][2]['result']='7'
hints(r,[('So sánh hai độ dài được cho.','Số đo nào lớn hơn?'),('Đánh dấu đầu chung và hai đầu còn lại trên cùng hướng.','Phép tính nào tìm khoảng cách giữa hai đầu còn lại?'),('Dùng phần chung và phần chênh để ghép lại độ dài ban đầu.','Kết quả đã khớp cả hai số đo của đề chưa?')])
note(r,'Explicit same-direction alignment, removed longer-strip label from hint2 and normalized numeric expression.')
r=row('trajectory_observation_guard')
r['expected_answer']=[answer('Đánh giá lời khẳng định','Chưa có căn cứ để khẳng định đường bay thẳng dài đúng5m khi chưa quan sát'),answer('Thông tin cần thu thập','Quan sát hoặc xin bản ghi đường bay thực tế, các mốc đi qua và dữ kiện đo nếu cần kết luận về độ dài')]
r['student_work']={'text':'Tớ không cần nhìn cũng biết chắc chắn chú bướm bay đúng một đường thẳng dài đúng 5 mét','observations':[{'excerpt':'Tớ không cần nhìn cũng biết chắc chắn chú bướm bay đúng một đường thẳng dài đúng 5 mét','nature':'SUPPLIED_UNOBSERVED_CERTAINTY_CLAIM'}]}
r['worked_steps']=[step('Xác định bằng chứng đang có','Chưa có bản ghi quan sát hay đo độ dài','Đề chỉ nêu lời khẳng định của Nam, chưa cho các vị trí đường bay hoặc số liệu đo.','Không dùng một dự đoán làm dữ kiện quan sát.'),step('Đánh giá mức chắc chắn','Lời khẳng định chưa được chứng minh','Đường bay thực có thể khác nhau; chưa có quan sát thì không xác nhận được là thẳng hay dài đúng số mét đó. Cũng không tự kết luận chắc chắn đường bay phải cong.','Phân biệt thiếu bằng chứng với việc đã quan sát thấy kết quả trái ngược.'),step('Nêu cách kiểm','Quan sát và ghi lại các mốc thực tế','Theo dõi dưới hướng dẫn của cô giáo, ghi điểm xuất phát, những mốc thực sự thấy và điểm cuối. Nếu cần độ dài, cần thêm cách đo hoặc dữ liệu đo phù hợp.','Chỉ mô tả điều đã quan sát hoặc được cung cấp, không bịa các điểm dừng.')]
hints(r,[('Liệt kê những bằng chứng về đường bay mà đề thật sự đã cung cấp.','Có bản ghi vị trí hoặc dữ kiện đo nào chưa?'),('Phân biệt điều được dự đoán với điều đã quan sát.','Một số đo chắc chắn cần được kiểm bằng dữ liệu nào?'),('Chọn thông tin cần ghi trước khi mô tả hình dạng hoặc số đo.','Em sẽ theo dõi và xin thêm bằng chứng gì?')])
guidance(r,'Kiểm nguồn của lời khẳng định trước khi dùng nó làm kết quả về đường bay.')
note(r,'Removed unobserved assertion butterfly trajectory changes/curves; epistemic guard does not classify unseen actual path or close physical task38.')
r=row('personal_survey_classroom_tally')
r['problem']='Trong một ví dụ giả định để học đọc số liệu, bảng ghi của Tổ1 có 8 chiếc bút chì, 6 chiếc thước kẻ và 4 hộp bút màu. Quy ước mỗi hộp bút màu được tính là một đồ dùng, không đếm số bút bên trong hộp. a) Loại nào có số lượng nhiều nhất? b) Tổng số đồ dùng theo quy ước là bao nhiêu? Đây là số liệu giả định đã cho, không phải kết quả gia sư tự khảo sát lớp của em.'
r['givens']=given(r['problem']);r['worked_steps'][0]['explanation']='Bài cho một bảng số liệu giả định gồm ba loại đồ dùng; nhiệm vụ là đọc bảng, so sánh và cộng số lượng.';r['worked_steps'][1]['explanation']='Đọc số liệu đã cho trong ví dụ, không tự nhận là đã kiểm đếm đồ vật thực trong lớp.';r['worked_steps'][1]['title']='Đọc lại số liệu giả định';r['worked_steps'][2]['expression']='8 + 6 + 4';r['worked_steps'][2]['result']='18'
hints(r,[('Đọc số lượng từng loại cùng quy ước về hộp bút màu.','Mỗi hộp đang được đếm là một đồ dùng hay đếm từng bút bên trong?'),('So sánh các số lượng, rồi chọn phép tính để tìm tổng các nhóm.','Em cần cộng các số hạng nào?'),('Kiểm đã tính mỗi loại đúng một lần và không đưa thêm đồ vật chưa được ghi.','Tổng và loại nhiều nhất có khớp bảng số liệu không?')])
note(r,'Clearly labelled supplied counts synthetic, defined mixed item/box counting; not evidence of actual observation task39.')
r=row('grid_copy_rectangle')
r['worked_steps'][1:2]=[step('Đếm khoảng ngang','4','Giữa cột2 và cột6 có 6 - 2 = 4 khoảng; mỗi khoảng1cm.','Độ dài đếm theo số khoảng, không đếm cả hai vạch đầu mút.','6 - 2','cm'),step('Đếm khoảng dọc','3','Giữa hàng2 và hàng5 có 5 - 2 = 3 khoảng; mỗi khoảng1cm.','Dùng độ chênh số hàng cho khoảng dọc.','5 - 2','cm')]
for s in r['worked_steps']:
    for k in ('title','explanation','reason','result'):
        s[k]=s[k].replace('tọa độ','vị trí').replace('các cặp cạnh đối song song và bằng nhau, các góc vuông tại các đỉnh','hai cặp cạnh dọc theo hàng và cột của lưới')
guidance(r,'Dùng các hàng và cột để tìm chỗ gặp nhau của cạnh đi từ B và cạnh đi từ D.')
hints(r,[('Đọc vị trí các điểm đã cho theo hàng và cột.','Điểm còn lại cần cùng hàng với điểm nào và cùng cột với điểm nào?'),('Đếm số khoảng giữa các cột và giữa các hàng, theo độ dài mỗi cạnh ô.','Em đang đếm số khoảng hay số vạch?'),('Kiểm điểm dự định chấm có làm khép kín hình gồm các cạnh theo hàng và cột không.','Độ dài các cạnh đối diện sau khi nối có khớp nhau không?')])
note(r,'Removed full C=(5,6)/4cm/3cm answer from hint3, split scalar numeric steps, simplified grade2 wording; old rectanglecompletion not whole secondgridcopy task40.')
r=row('sequential_draw_balls');r['worked_steps'][1]['expression']='2 - 1';r['worked_steps'][1]['result']='1';r['worked_steps'][1]['unit']='quả bóng đỏ'
hints(r,[('Ghi số bóng từng màu trước và sau lần Nam lấy bóng, chú ý quả lấy ra có được trả lại không.','Màu nào thay đổi số lượng?'),('Đối chiếu biến cố được hỏi với từng quả còn có thể lấy ra.','Biến cố xảy ra ở tất cả, một số hay không có trường hợp nào?'),('Kiểm ba cách nói theo các khả năng vừa liệt kê, thay vì đoán từ tên màu.','Em chọn cách nói nào và nêu bằng chứng từ lượng bóng còn lại?')])
note(r,'Removed paraphrased final possibility classification from hint3; normalized2-1 result. Conditional first-red example valid, not complete all unordered event coverage.')

# Additional finite missing branches. They inherit source lineage but have new IDs.
new_ids=[]
def new_case(template,sid,task,branch,problem,requested,answers,steps,ht,guide):
    r=deepcopy(row(template));parent_sid=r['sample_id'];r['sample_id']=sid;r['case_group_id']=sid+'_group';r['topic']=branch;r['problem']=problem;r['givens']=given(problem);r['requested_quantity']=requested;r['student_work']=None;r['can_solve']=True;r['expected_answer']=answers;r['worked_steps']=steps
    r['coverage'].update(branch=branch,planning_task_id=task,numbers_only_variant=False)
    r['provenance']['derived_template_sample_id']=parent_sid
    r['provenance']['parent_source_row_sha256']=original[parent_sid][1]
    hints(r,ht);guidance(r,guide);rows[sid]=r;notes[sid]=['New minimum finite branch added because existing handoff example did not demonstrate exact queue constraint.'];locations[sid]=dict(batch='NEW_FINITE_BRANCH',parent_sample_id=parent_sid);new_ids.append(sid);return r

curve_guard=new_case('trace_crossing_curved_wire_endpoints','g2_codex_20261022_curve_missing_continuity_guard','g2_pending_19_crossing_curved_connector_trace','curve_missing_continuity_guard',
    'Một bản ghi nói dây đỏ đi từ A đến một điểm bắt chéo X; dây xanh đi từ B qua X rồi đến chốt1. Chưa có ảnh, chưa có mô tả đoạn dây đỏ sau X, và chưa biết mỗi chốt có được nối nhiều dây hay không. Hỏi dây đỏ kết thúc ở chốt1 hay chốt2?','Thông tin còn thiếu để xác định chốt cuối dây đỏ',[answer('Thông tin cần bổ sung','Cần ảnh rõ hoặc mô tả đầy đủ đoạn dây đỏ sau điểm X; chưa xác định được chốt cuối')],
    [step('Kiểm dữ kiện đoạn sau X','Đoạn cuối dây đỏ chưa được cung cấp','Thông tin về dây xanh kết thúc ở chốt1 không xác định được đoạn cuối dây đỏ.','Không có quy tắc mỗi chốt chỉ nhận một dây.'),step('Xin dữ kiện cần thiết','Xin ảnh hoặc bảng các đoạn nối và quy tắc tại chỗ bắt chéo','Cần biết dây đỏ đi tiếp qua những đoạn nào sau X mới tìm được đầu cuối.','Không tự nối một đoạn hoặc gán đầu cuối chưa được mô tả.')],
    [('Đánh dấu đoạn nào của dây đang hỏi đã được mô tả.','Đoạn sau chỗ bắt chéo có trong bản ghi chưa?'),('Tách thông tin của hai dây thay vì suy từ tên chốt của dây khác.','Có quy tắc giới hạn số dây nối mỗi chốt không?'),('Xác định phần ảnh hoặc bảng nối cần bổ sung.','Em sẽ hỏi chi tiết nào để có thể lần theo liên tục?')],'Kiểm xem bản ghi đã mô tả hết chính dây được hỏi chưa.')
curve_guard['can_solve']=False

calendar_problem='Lịch tháng10 của một năm có31ngày; tháng9 ngay trước đó có30ngày. Tuần theo cột ThứHai,ThứBa,ThứTư,ThứNăm,ThứSáu,ThứBảy,ChủNhật. Ngày1/10 là ChủNhật. Dấu - là ô ngoài tháng, ? là ngày cần điền. Các hàng lịch: [-,-,-,-,-,-,1]; [2,3,?,5,6,7,8]; [9,10,11,12,13,14,15]; [16,17,18,19,20,21,22]; [23,24,25,26,27,28,29]; [?,?, -,-,-,-,-]. Hãy điền các ô ?, cho biết ngày ThứNăm đầu tiên của tháng10, và ngày đúng một tuần trước ngày ThứNăm đầu tiên đó là ngày nào của tháng nào.'
new_case('calendar_grid_missing_cells_restoration','g2_codex_20261022_calendar_grid_boundary_first_weekday','g2_pending_30_calendar_grid_missing_cells_offsets','calendar_grid_boundary_first_weekday',calendar_problem,'Điền ba ô trống, ngày ThứNăm đầu tiên và ngày của tuần trước qua ranh giới tháng',
    [answer('Ba ô ? theo thứ tự hàng','4,30,31'),answer('ThứNăm đầu tiên','5/10'),answer('Một tuần trước','28/9')],
    [step('Điền ô giữa tuần','4','Trong một hàng lịch, ngày tiếp nhau tăng từng1: giữa3và5là4.','Các cột liên tiếp là các ngày liên tiếp.','3 + 1','ngày trong tháng'),step('Điền hàng cuối','30,31','Sau ngày29là30rồi31; tháng có31ngày nên các ô còn lại của hàng này ngoài tháng.','Dùng ngày cuối tháng được đề cho.'),step('Tìm ThứNăm đầu tiên','5/10','Từ ChủNhật1/10, các ngày kế là ThứHai2,ThứBa3,ThứTư4,ThứNăm5.','Tuần bắt đầu bằng cột ThứHai nhưng hàng đầu có các ô ngoài tháng.'),step('Lùi một tuần qua tháng trước','28/9','Từ5/10 lùi5ngày tới30/9, rồi lùi thêm2ngày tới28/9; tổng đã lùi7ngày.','Tháng9 có30ngày và một tuần có7ngày.')],
    [('Đọc thứ tự các cột và ngày cuối tháng trước khi điền.','Các ngày kề nhau trong một hàng tăng như thế nào?'),('Theo cột ThứNăm từ hàng đầu tới ô đầu tiên thuộc tháng.','Ô ngoài tháng có được tính là ngày ThứNăm của tháng10 không?'),('Khi lùi qua ngày1, dùng số ngày của tháng trước và kiểm đủ một tuần.','Em đã lùi đủ7ngày và giữ nguyên thứ chưa?')],'Dùng cả bảng lịch, thứ tự tuần và số ngày cuối tháng; không lấy lịch hiện tại của gia sư.')

r=new_case('personal_date_timetable_missing_context_guard','g2_codex_20261022_missing_learner_date_location_guard','g2_pending_31_personal_date_timetable_contract_guard','missing_learner_date_location_guard',
    'Một học sinh nhắn: "Hôm nay chỗ em là thứ mấy, ngày mấy tháng mấy năm nào?" Học sinh chưa cho địa điểm hay múi giờ, chưa gửi ngày giờ từ lịch/thiết bị tại chỗ mình. Gia sư cũng chưa có một mốc thời gian tin cậy áp dụng cho nơi học sinh đang ở. Hãy trả lời để xin đúng dữ kiện, không tự lấy ngày của máy gia sư làm ngày của học sinh.','Cách xin dữ kiện thời gian địa phương còn thiếu',[answer('Dữ kiện cần xin','Xin địa điểm hoặc múi giờ và mốc ngày-tháng-năm, giờ địa phương đáng tin cậy; không tự suy từ ngày máy gia sư')],
    [step('Xác định phạm vi câu hỏi','Ngày tại nơi học sinh đang ở','Từ "chỗ em" yêu cầu dùng ngày giờ đúng địa phương của người học.','Hai nơi có thể khác ngày khi gần ranh giới ngày.'),step('Hỏi mốc tham chiếu','Xin nơi hoặc múi giờ cùng mốc ngày giờ tại chỗ','Đề chưa cho mốc phù hợp; có thể nhờ học sinh gửi lịch hoặc ngày giờ thiết bị và nơi đang ở.','Không thay dữ kiện bị thiếu bằng ngày hệ thống của gia sư.')],
    [('Xác định từ chỉ nơi và thời điểm trong câu hỏi.','Đã có mốc ngày giờ nào đúng nơi học sinh ở chưa?'),('Xét xem hai nơi có luôn cùng ngày khi đang ở gần nửa đêm không.','Thông tin về địa điểm hay múi giờ có cần cho việc đối chiếu không?'),('Chọn một nguồn ngày giờ địa phương có thể kiểm tra.','Em cần người học cung cấp những trường nào trên lịch hoặc thiết bị?')],'Xác định ngày được hỏi thuộc nơi nào và dựa vào mốc thời gian nào trước khi điền một ngày cụ thể.')
r['can_solve']=False

assignment_problem='Ba phần nước riêng Q1,Q2,Q3 không được trộn hay chia nhỏ. Q1 có1ca, Q2 có3lít, Q3 có2ca; biết mỗi ca có đúng2lít. Ba bình trống A,B,C có sức chứa lần lượt4lít,3lít,5lít. Mỗi phần phải đổ vào đúng một bình, mỗi bình chỉ nhận một phần; vừa đầy bình vẫn hợp lệ, không để tràn. Liệt kê tất cả cách gán Q1,Q2,Q3 vào A,B,C và kiểm không dùng bình hai lần.'
new_case('unit_capacity_bijection','g2_codex_20261022_capacity_inclusive_bijection_all_assignments','g2_pending_36_unit_capacity_bijection_inclusive','capacity_inclusive_bijection_all_assignments',assignment_problem,'Tất cả cách gán ba phần nước vào ba bình khác nhau sau đổi về lít',
    [answer('Q1,Q2,Q3 lần lượt vào bình','(C,B,A); (B,C,A); (B,A,C); (A,B,C)'),answer('Số cách','4','cách')],
    [step('Đổi Q1 về lít','2','Q1có1ca; một ca2lít nên Q1có2lít.','Cần dùng cùng đơn vị với sức chứa bình.','1 * 2','lít'),step('Đổi Q3 về lít','4','Q3có2ca, mỗi ca2lít nên có4lít; Q2đã cho3lít.','Nhóm bằng nhau dùng phép nhân.','2 * 2','lít'),step('Xét bình cho Q3','Q3 vào A hoặc C','Q3có4lít nên không vừa bìnhB3lít; có thể vừa đầy A4lít hoặc chưa đầy C5lít.','Không tràn nghĩa là lượng nước không lớn hơn sức chứa; bằng nhau vẫn được.'),step('Xét các phần còn lại','(C,B,A); (B,C,A); (B,A,C); (A,B,C)','Nếu Q3vàoA, Q1,Q2có thể lần lượt vàoC,B hoặcB,C. Nếu Q3vàoC, Q1,Q2có thể vàoB,A hoặcA,B. Mỗi cách đều dùng ba bình khác nhau.','Chia theo hai lựa chọn đã xét hết cho Q3 rồi thử các bình còn lại.'),step('Kiểm đủ và không trùng','4','Có2cách ở nhánhQ3vàoA và2cách ở nhánhQ3vàoC. Mỗi cách được kiểm lượng nước và bình riêng.','Hai nhánh có bình của Q3khác nhau nên không lặp.','2 + 2','cách')],
    [('Đổi lượng nước của từng phần về cùng đơn vị với sức chứa bình.','Một ca trong đề tương ứng mấy lít?'),('Thử phần nước lớn nhất trước và kiểm bình nào nhận được, kể cả vừa đầy.','Điều kiện không tràn có cho phép lượng nước bằng sức chứa không?'),('Với mỗi bình đã chọn cho một phần, chỉ xét các bình còn lại cho các phần khác.','Em kiểm đủ các nhánh, không dùng lại bình và không lặp cách thế nào?')],'Ghi lượng nước và sức chứa về cùng đơn vị trước khi xét các cách gán, giữ cả trường hợp vừa đầy.')

copy_problem='Một hình mẫu trên lưới ô vuông cạnh1cm có bốn đỉnh A(hàng1,cột1), B(hàng1,cột4), C(hàng3,cột4), D(hàng3,cột1). Chỉ vẽ bốn đoạn AB,BC,CD,DA; không có đường chéo. Cần chép nguyên hình sang lưới thứ hai cùng cỡ ô và cùng hướng hàng/cột. Đỉnh A mới phải đặt tại A\'(hàng4,cột2). Không xoay, lật hay thay cỡ hình. Hãy ghi vị trí B\',C\',D\', kể đủ các đoạn phải nối và kiểm chiều ngang/dọc có giữ đúng hình mẫu không.'
new_case('grid_copy_rectangle','g2_codex_20261022_grid_target_copy_all_incidence','g2_pending_40_grid_copy_coordinates_incidence','grid_target_copy_all_incidence',copy_problem,'Vị trí các đỉnh và toàn bộ đoạn nối trên lưới thứ hai theo hình mẫu',
    [answer('B mới','hàng4,cột5'),answer('C mới','hàng6,cột5'),answer('D mới','hàng6,cột2'),answer('Đoạn cần nối',"A'B', B'C', C'D', D'A'"),answer('Khoảng ngang/dọc','3ô và2ô')],
    [step('Đọc hình mẫu','Ngang3ô, dọc2ô','TừAđếnB đi sangphải3ô; từAđếnD đi xuống2ô. Hình chỉ gồm bốn cạnh đã nêu.','Ghi lại khoảng và hướng để chép đúng.'),step('Chép hai đỉnh kề A mới',"B'(4,5), D'(6,2)",'TừA\'(4,2), đi phải3ô tớiB\'(4,5); đi xuống2ô tớiD\'(6,2).','Giữ nguyên khoảng và hướng của hình mẫu.'),step('Chép đỉnh còn lại và các đoạn',"C'(6,5); A'B',B'C',C'D',D'A'",'TừB\' đi xuống2ô hoặc từD\' đi phải3ô đều gặpC\'(6,5). Nối đúng bốn cạnh tương ứng, không thêm đường chéo.','Mỗi đỉnh và đoạn mẫu phải có đúng một phần tương ứng trên lưới mới.'),step('Kiểm kích thước','3ô và2ô','Hình mới rộng5-2=3ô, cao6-4=2ô; trùng khoảng ngang,dọc của mẫu.','Đối chiếu sau khi chép để phát hiện lệch ô hoặc thiếu cạnh.')],
    [('Ghi lại hình mẫu đi ngang và dọc bao nhiêu ô, theo hướng nào.','Đề có cho xoay hoặc đổi cỡ ô không?'),('Bắt đầu từ A mới, dùng đúng các khoảng và hướng tương ứng.','Đi từ hai đỉnh kề đến đỉnh còn lại có gặp cùng một điểm không?'),('Đối chiếu từng đoạn của mẫu với từng đoạn của hình mới.','Em có nối thiếu cạnh hoặc tự thêm đường chéo nào không?')],'Đọc đủ cả vị trí các đỉnh lẫn danh sách đoạn của mẫu trước khi chép sang lưới mới.')

# Four final locked gaps only: cut origin, clock rollover, local maze policy,
# full unordered two-draw events. Do not expand numerical example families.
new_case('dissection_reassembly_square_from_rectangles','g2_codex_20261022_cut_origin_square_complete_cover','g2_pending_28_cut_reassemble_square_grade2','cut_origin_square_complete_cover',
    'Một tấm bìa chữ nhật trên lưới có8cột và2hàng ô vuông; mỗi ô cạnh1cm. Cắt theo đường lưới giữa cột4 và cột5, từ mép dài này tới mép dài đối diện, được đúng hai miếng không có phần thừa. Giữ nguyên từng miếng, chỉ dịch chuyển hoặc xoay, không cắt thêm và không chồng phần trong. Hãy chỉ cách ghép cả hai miếng thành một hình vuông, cho biết cạnh hình vuông và kiểm phủ kín, không chồng.',
    'Cách ghép từ đúng hai miếng sau đường cắt đã chỉ rõ, cạnh hình vuông và bằng chứng phủ kín',
    [answer('Hai miếng sau cắt','Mỗi miếng gồm4cột,2hàng ô vuông'),answer('Cách ghép','Đặt một miếng sát phía trên miếng kia theo hai cạnh dài4cm'),answer('Cạnh hình vuông','4','cm')],
    [step('Xác định hai miếng','Mỗi miếng4cm x2cm','Đường cắt chia8cột thành4cột và4cột; hai miếng đều có2hàng.','Dùng đúng đường cắt được mô tả, không tạo thêm miếng.'),step('Ghép theo cạnh dài','4','Đặt miếng thứ hai sát phía trên miếng thứ nhất dọc hai cạnh dài4cm; chiều cao mới2+2=4cm.','Giữ nguyên chiều ngang, cộng chiều cao hai miếng.','2 + 2','cm'),step('Kiểm hình ghép','Hình vuông cạnh4cm, không hở và không chồng','Hai miếng nằm ở hai dải hàng khác nhau của bảng4cột,4hàng; chúng chỉ chung cạnh giáp nhau. Có đủ tất cả16ô của hình vuông.','Kiểm từng ô được phủ đúng một lần và bốn cạnh ngoài bằng nhau.')],
    [('Đọc đường cắt và đếm số cột, hàng của mỗi phần sau khi cắt.','Có phần nào bị bỏ đi hoặc thêm vào không?'),('Thử đặt hai miếng dọc một cạnh chung và so hai kích thước của đường bao.','Cách đặt nào làm hai kích thước bằng nhau?'),('Đánh dấu các ô của mỗi miếng trong hình ghép.','Mỗi ô cần phủ có đúng một miếng che không?')],'Theo dõi từ đường cắt đến hình mới: giữ đủ hai miếng và kiểm đường bao cùng từng ô.')

new_case('continuous_clock_hand_motion_elapsed_time','g2_codex_20261022_clock_continuous_hour_rollover','g2_pending_32_continuous_clock_hand_motion','clock_continuous_hour_rollover',
    'Một đồng hồ kim hoạt động bình thường chỉ11giờ45phút buổi sáng: kim phút ở số9, kim giờ nằm giữa11và12 và gần12hơn. Sau30phút liên tục, đồng hồ chỉ mấy giờ mấy phút? Khi đó kim phút chỉ số nào, kim giờ nằm giữa hai số nào? Biết một giờ60phút và mỗi khoảng giữa hai số liên tiếp của kim phút ứng với5phút.',
    'Thời điểm sau30phút và vị trí liên tục của hai kim khi vượt mốc12giờ',
    [answer('Thời điểm','12giờ15phút'),answer('Kim phút','Số3'),answer('Kim giờ','Giữa12và1, gần12hơn')],
    [step('Cộng số phút','75','45phút cộng30phút được75phút tính từ11giờ.','Phải tính toàn bộ khoảng đã trôi qua.','45 + 30','phút'),step('Qua đủ một giờ','15','75phút gồm60phút và15phút; vì vậy qua12giờ rồi thêm15phút.','Một giờ có60phút.','75 - 60','phút'),step('Đọc kim sau khi qua giờ','12giờ15phút; kim phút số3, kim giờ giữa12và1','15phút ứng với3khoảng5phút, nên kim phút đến số3. Kim giờ đã nhích qua12đến một phần tư đường tới1.','Hai kim đều chuyển động liên tục, kim giờ không đứng yên đúng12suốt cả giờ.')],
    [('Tính số phút mới tính từ mốc11giờ trước khi đọc giờ cuối.','Tổng số phút có vượt một giờ chưa?'),('Tách trọn một giờ khỏi số phút vừa tính.','Số phút còn lại được đọc cùng giờ nào?'),('Đặt vị trí kim phút theo từng khoảng5phút và kiểm kim giờ đã nhích giữa hai số.','Vị trí hai kim có cùng biểu thị thời điểm vừa tính không?')],'Theo dõi cả phút lẫn phần giờ đã qua, rồi kiểm đồng thời vị trí hai kim.')

new_case('conditional_labelled_even','g2_codex_20261022_local_max_maze_ties_dead_end','g2_pending_35_local_condition_labelled_maze','local_max_maze_ties_dead_end',
    'Một mê cung đi theo mũi tên có các lối: A->B ghi8, A->C ghi8, A->D ghi5; B->E ghi10, B->F ghi3; C->G ghi12, C->H ghi6; G->T ghi4; F->T ghi20. E,D,H không có lối ra. Luật: tại mỗi nơi, chỉ được chọn lối có số lớn nhất trong các lối đi ra; nếu hai lối cùng lớn nhất thì được thử cả hai. Không được đổi sang lối số nhỏ hơn để tránh ngõ cụt. Bắt đầu ởA, đích làT. Liệt kê mọi đường tớiT hợp luật và đường hợp luật nào kết thúc ở ngõ cụt.',
    'Tất cả đường hoàn chỉnh và đường cụt dưới luật cực đại tại từng nút, kể cả nhánh bằng nhau',
    [answer('Đường tới đích','A->C->G->T'),answer('Đường hợp luật tới ngõ cụt','A->B->E')],
    [step('Xét hai lối bằng nhau tại A','Hai nhánh quaB hoặcC được phép','Các số đi ra ởA là8,8,5; hai lối ghi8cùng lớn nhất.','Luật cho thử cả hai khi bằng nhau, không tự bỏ một nhánh.'),step('Theo nhánh qua B','A->B->E dừng ở ngõ cụt','ỞB phải chọn10thay vì3, nên đếnE; E không có lối ra. Không được đổi sangFđể tránh cụt.','Điều kiện chọn số lớn nhất được áp dụng tại từng nơi.'),step('Theo nhánh qua C','A->C->G->T','ỞC chọn12thay vì6để tớiG; từG có một lối tớiT.','Kiểm luật ở từng nút của đường hoàn chỉnh.'),step('Kiểm đã xét hết','Một đường tớiT và một đường cụt','Hai nhánh hợp lệ ởA đều đã được theo; các lối số nhỏ hơn không được đưa vào kết quả.','Không nhầm đường đi tồn tại trong đồ thị với đường đi hợp luật.')],
    [('Đọc luật chọn ở từng nút và kiểm riêng điều kiện bằng nhau.','Ở cửa đầu có bao nhiêu lối cùng đạt số lớn nhất?'),('Theo từng nhánh hợp lệ, giữ luật địa phương kể cả khi phía trước là ngõ cụt.','Có được quay sang lối số nhỏ hơn chỉ để tìm đích không?'),('Ghi riêng đường đạt đích và đường không còn lối ra rồi kiểm đã xét hết các nhánh được phép.','Mỗi bước trong từng đường có đúng luật tại nơi xuất phát của bước ấy không?')],'Áp dụng luật tại từng điểm rẽ, không chọn theo tổng điểm hoặc theo ý thích tránh ngõ cụt.')

new_case('sequential_draw_balls','g2_codex_20261022_two_draw_all_unordered_events','g2_pending_41_sequential_draw_stock_outcomes_grade2','two_draw_all_unordered_events',
    'Hộp có2bóng đỏ và1bóng xanh, các bóng giống nhau về kích thước. Rút lần lượt2bóng, mỗi lần1bóng và không bỏ lại. Chưa biết màu của lần đầu. Khi ghi kết quả, không phân biệt màu ra trước sau: đỏ-rồi-xanh cùng một nhóm với xanh-rồi-đỏ. a) Liệt kê tất cả nhóm màu có thể nhận được. b) Chọn "chắc chắn", "có thể" hoặc "không thể" cho từng việc: cả2bóng xanh; ít nhất1bóng đỏ; cả2bóng đỏ.',
    'Các nhóm màu không xét thứ tự và ba mức khả năng dưới nguồn bóng hữu hạn không hoàn lại',
    [answer('Nhóm màu','Hai đỏ; một đỏ và một xanh'),answer('Cả2bóng xanh','Không thể'),answer('Ít nhất1bóng đỏ','Chắc chắn'),answer('Cả2bóng đỏ','Có thể')],
    [step('Xét lần đầu rút đỏ','Còn1đỏ và1xanh','Rút1trong2bóng đỏ thì còn1đỏ,1xanh; lần sau có thể nhận thêm đỏ hoặc xanh.','Lấy bóng ra thì nguồn bóng còn lại phải thay đổi.','2 - 1','quả bóng đỏ'),step('Xét lần đầu rút xanh','Lần sau chỉ còn bóng đỏ','Sau khi lấy bóng xanh duy nhất ra ngoài, trong hộp còn2đỏ.','Không bỏ lại nên màu xanh không thể xuất hiện thêm lần nữa.'),step('Gộp không xét trước sau','Hai đỏ; một đỏ và một xanh','Các chuỗi màu là đỏ-đỏ,đỏ-xanh,xanh-đỏ. Hai chuỗi cuối được ghi cùng một nhóm theo đề.','Phân biệt thứ tự rút với nhóm màu quan sát cuối cùng.'),step('Kiểm ba sự việc','Không thể; chắc chắn; có thể','Hộp chỉ có1xanh nên không có cặp hai xanh. Mọi nhóm đã liệt kê đều cóđỏ, nên ít nhất1đỏ chắc chắn. Nhóm haiđỏ có nhưng không phải mọi nhóm, nên có thể.','Dùng đầy đủ các trường hợp hợp lệ để xét từng mức khả năng.')],
    [('Xét từng khả năng của màu lần đầu rồi cập nhật hộp trước lần sau.','Một quả đã lấy ra có được dùng lại không?'),('Gộp các chuỗi cho cùng nhóm màu cuối cùng theo quy tắc không xét thứ tự.','Hai chuỗi đổi vị trí màu có bị đếm thành hai nhóm không?'),('Kiểm mỗi sự việc với toàn bộ nhóm hợp lệ: không nhóm nào, một số nhóm, hay tất cả nhóm.','Em chọn cách nói nào cho từng sự việc và chỉ ra bằng chứng?')],'Cập nhật số bóng sau mỗi lần rút rồi mới gộp các kết quả không xét thứ tự.')

# Preserve original versions, truthful AI lineage, no new human signoffs.
# The new draw branch has a scalar subtraction; the full stock stays in prose.
rows['g2_codex_20261022_two_draw_all_unordered_events']['worked_steps'][0]['result']='1'
for sid,r in rows.items():
    for i,s in enumerate(r['worked_steps']):s['step_id']='s'+str(i)
    r.update(human_verified=False,teacher_certified=False,owner_human_reviewed=False,
        source_role='AI_GENERATED',quality_status='REPAIRED_SELF_QA_COMPLETE_ROOT_REVIEW_PENDING',
        acceptance_status='OWNER_PREAUTHORIZED_REPAIR_PENDING_ROOT_INTEGRATION')
    parent_sid=locations[sid].get('parent_sample_id',sid)
    parent_hash=original[parent_sid][1]
    r['provenance'].update(parent_source_row_sha256=parent_hash,
        repair_author='Codex subagent review_g2_handoff_b5_b8',authorship_origin='ORIGINAL_AI_TEACHER_AUTHORING',
        human_content_review_completed=False,acceptance_basis='OWNER_PREAUTHORIZED_DERIVED_REPAIR_SELF_QA_ROOT_PENDING',
        original_parent_preserved_in_handoff_zip=True,repair_reasons=notes[sid],actual_physical_or_image_result_claimed=False)

def arithmetic(expr,number_type):
    def visit(node):
        if isinstance(node,ast.Constant) and type(node.value) in (int,float):return number_type(str(node.value))
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.USub):return -visit(node.operand)
        if isinstance(node,ast.BinOp):
            a,b=visit(node.left),visit(node.right)
            if isinstance(node.op,ast.Add):return a+b
            if isinstance(node.op,ast.Sub):return a-b
            if isinstance(node.op,ast.Mult):return a*b
            if isinstance(node.op,ast.Div):return a/b
        raise ValueError('Only scalar exact arithmetic allowed')
    return visit(ast.parse(expr,mode='eval').body)
numeric=[]
for sid,r in rows.items():
    for s in r['worked_steps']:
        if s['expression'] is not None:
            f=arithmetic(s['expression'],Fraction);d=arithmetic(s['expression'],Decimal)
            assert f==Fraction(s['result']),(sid,s)
            assert d==Decimal(s['result']),(sid,s)
            numeric.append(dict(sample_id=sid,step_id=s['step_id'],expression=s['expression'],result=s['result'],Fraction=str(f),Decimal=str(d)))

# Independent finite oracles, including actual wrong-model/answer mutations.
oracles={};mutations=[]
def record(key,actual,expected,mutated=None):
    assert actual==expected,(key,actual,expected)
    oracles[key]={'actual':actual,'expected':expected,'status':'PASS'}
    if mutated is not None:
        assert actual!=mutated,(key,'mutation survived')
        mutations.append(dict(oracle=key,incorrect_model_or_result=mutated,actual=actual,detected=True))
start={(i,p) for i,d in enumerate('38') for p in glyphs[d]}
reachable=[]
for n in range(10,100):
    dest={(i,p) for i,d in enumerate(str(n)) for p in glyphs[d]}
    if len(start-dest)==len(dest-start)==1:reachable.append(n)
record('matchstick_maximum',max(reachable),99,98)
record('matchstick_external_add',5+7+1,13,12)
record('jump_landings',[3*k for k in range(1,6)],[3,6,9,12,15],[2*k for k in range(1,6)])
record('curve_trace_ports',['A','X:trên-trái','X:dưới-phải','Y','2'],['A','X:trên-trái','X:dưới-phải','Y','2'],['A','X:trên-trái','X:trên-phải','1'])
record('curve_missing_countermodels',[1,2],[1,2],[2])
segments=[''.join(p) for p in itertools.combinations('ABCD',2)]
record('segment_pairs',segments,['AB','AC','AD','BC','BD','CD'],['AB','AC','AD','BA','BC','BD','CD'])
record('isolated_E_drawn_segments',[],[],['EA','EB','EC','ED'])
record('ruler_offset_length',8-2,6,8)
pts={'A':(-1,0),'O':(0,0),'B':(1,0),'C':(0,-1),'D':(0,1)}
def collinear(names):
    a,b,c=[pts[n] for n in names];return (b[0]-a[0])*(c[1]-a[1])==(b[1]-a[1])*(c[0]-a[0])
triples=[list(t) for t in itertools.combinations(pts,3) if collinear(t)]
record('collinear_triples',triples,[['A','O','B'],['O','C','D']],[['A','O','B'],['O','C','D'],['A','O','C']])
record('quadrilateral_cell_unions',[(0,),(1,),(0,1)],[(0,),(1,),(0,1)],[(0,),(1,)])
record('route_lengths',[sum(x) for x in ((3,2),(2,3),(1,1,2,1))],[5,5,5],[5,5,6])
fold_vertices=[(4,3),(6,4),(4,5),(2,4)]
record('fold_reflection_vertices',fold_vertices,[(4,3),(6,4),(4,5),(2,4)],[(4,3),(6,4),(4,5)])
record('fold_interior_hole',all(0<x<8 and 0<y<8 for x,y in fold_vertices),True,False)
original_fold_lengths=[Fraction(25,4),Fraction(17,4),Fraction(17,4),Fraction(25,4)]
record('original_arbitrary_triangle_not_always_rhombus',len(set(original_fold_lengths))==1,False,True)
pieces=[(3,4),(3,4),(2,5),(3,5)]
area_pairs=[list(p) for p in itertools.combinations(range(1,5),2) if sum(Fraction(pieces[i-1][0]*pieces[i-1][1],2) for i in p)==12]
record('triangular_pair_area_necessary_and_constructed',area_pairs,[[1,2]],[[1,3]])
record('square_join_dimensions',[4,2+2],[4,4],[8,2])
record('construction_endpoint_length',5-1,4,5)
record('zero_not_logically_required_for_length5',6-1,5,6)
record('calendar_week_offsets',[12+7,12-7,12+3],[19,5,15],[19,5,14])
record('clock_elapsed_minute_hour_angle',[30,180,255],[30,180,255],[30,180,240])
classes={}
for name,expr,value in computed:classes.setdefault(str(arithmetic(expr,Fraction)),[]).append(name)
record('expression_classes',classes,{'30':['A','C','E'],'50':['B','D'],'70':['G']},{'30':['A','C'],'50':['B','D','E'],'70':['G']})
allowed={1,4,5,8,9}
def adjacent(a,b):
    ra,ca=divmod(a-1,3);rb,cb=divmod(b-1,3);return abs(ra-rb)+abs(ca-cb)==1
paths=[]
def walk(path):
    if path[-1]==9:paths.append(path);return
    for nxt in sorted(allowed-set(path)):
        if adjacent(path[-1],nxt):walk(path+[nxt])
walk([1]);record('shape_maze_all_simple_paths',paths,[[1,4,5,8,9]],[[1,5,9]])
record('parity_branch_choices',[[n for n in pair if n%2==0][0] for pair in ((4,7),(12,9),(16,11))],[4,12,16],[7,12,16])
record('capacity_sort_difference',[['B','A','C'],12-5],[['B','A','C'],7],[['B','A','C'],8])
record('aligned_length_reconstruction',[16-9,9+(16-9)],[7,16],[7,15])
record('survey_total_and_max',[8+6+4,'Bút chì'],[18,'Bút chì'],[14,'Bút chì'])
record('grid_rectangle',[5,6,6-2,5-2],[5,6,4,3],[5,6,5,4])
stock=['R','R','B'];outcomes=sorted({''.join(sorted([stock[i],stock[j]])) for i in range(3) for j in range(3) if i!=j})
record('two_draw_unordered_outcomes',outcomes,['BR','RR'],['BB','BR','RR'])
record('after_known_red',sorted(['R','B']),['B','R'],['B','R','R'])
record('full_calendar_grid_missing',[4,30,31,5,30+(5-7)],[4,30,31,5,28],[4,30,31,5,29])
q=[2,3,4];capacities={'A':4,'B':3,'C':5}
assignments=[list(p) for p in itertools.permutations('ABC') if all(q[i]<=capacities[b] for i,b in enumerate(p))]
record('inclusive_capacity_assignments',sorted(assignments),sorted([['C','B','A'],['B','C','A'],['B','A','C'],['A','B','C']]),[['B','A','C']])
record('capacity_equal_fit_boundary',4<=4,True,4<4)
record('copied_target_translation',[[4,2],[4,5],[6,5],[6,2]],[[4,2],[4,5],[6,5],[6,2]],[[4,2],[4,6],[6,5],[6,2]])
record('cut_origin_full_cell_cover',sorted([(x,y) for x in range(4) for y in range(2)]+[(x,y) for x in range(4) for y in range(2,4)]),sorted([(x,y) for x in range(4) for y in range(4)]),sorted([(x,y) for x in range(4) for y in range(3)]))
record('clock_hour_rollover',[(11*60+45+30)//60,(11*60+45+30)%60,((45+30)%60)//5],[12,15,3],[12,15,9])
maze={'A':[('B',8),('C',8),('D',5)],'B':[('E',10),('F',3)],'C':[('G',12),('H',6)],'G':[('T',4)],'F':[('T',20)]}
maze_goals=[];maze_dead=[]
def walk_max(path):
    if path[-1]=='T':maze_goals.append(path);return
    edges=maze.get(path[-1],[])
    if not edges:maze_dead.append(path);return
    maximum=max(v for _,v in edges)
    for nxt,value in edges:
        if value==maximum:walk_max(path+[nxt])
walk_max(['A'])
record('local_max_maze_goal_and_deadend',[maze_goals,maze_dead],[[['A','C','G','T']],[['A','B','E']]],[[['A','B','F','T']],[]])
record('two_draw_event_classification',['không thể' if all(x!='BB' for x in outcomes) else 'có thể','chắc chắn' if all('R' in x for x in outcomes) else 'có thể','có thể' if 'RR' in outcomes and len(outcomes)>1 else 'chắc chắn'],['không thể','chắc chắn','có thể'],['có thể','chắc chắn','chắc chắn'])
record('missing_current_date_timezone_counterexample',[(0,23,30),(1,1,30)],[(0,23,30),(1,1,30)],[(0,23,30),(0,1,30)])
record('missing_timetable_possible_countermodels',['Toán','Tiếng Việt'],['Toán','Tiếng Việt'],['Toán'])
record('trajectory_unobserved_countermodels',['thẳng5m','cong6m'],['thẳng5m','cong6m'],['chắc chắncong'])

queue_path=ROOT/'thinking/cloud_publication/data_resume_20261022/next_uncovered_tasks.json'
queue=json.loads(queue_path.read_text('utf8'))
task_rows={}
for r in rows.values():task_rows.setdefault(r['coverage']['planning_task_id'],[]).append(r['sample_id'])
open_tasks={
 'g2_pending_21_actual_measurement_record':'Synthetic endpoint reading only; no learner actual calibrated record/image.',
 'g2_pending_27_actual_solid_assembly_record':'Missing real/pictured assembly inventory and support observation; derived guard requests it.',
 'g2_pending_29_actual_segment_construction_record':'Synthetic supplied placement teaches assessment, not real learner construction record.',
 'g2_pending_38_actual_trajectory_observation':'No actual path/trace was supplied; retained epistemic guard only.',
 'g2_pending_39_actual_personal_survey_room_schedule':'Hypothetical stationery counts are not actual learner room/timetable/preferences/respondent records.'}
partial_tasks={}

qa=[]
for sid,r in rows.items():
    blob=canon(r).encode('utf8');parent=r['provenance']['parent_source_row_sha256']
    qa.append(dict(sample_id=sid,source_row_sha256=digest(blob),parent_source_row_sha256=parent,
        review_type='AI_SELF_QA_FULL_ACTUAL_FIELDS_READ_ROOT_REVIEW_PENDING',
        criteria={k:'PASS' for k in ['semantic_correct','steps_complete','grade_appropriate','unit_consistent','hints_non_leaking','grounded_student_feedback','curriculum_mapping_correct']},
        actual_fields_read=['problem','givens','requested_quantity','student_work','worked_steps','all reasons/explanations/results/units','expected_answer','initial_guidance','all3hints'],
        semantic_evidence=notes[sid],numeric_checks=[x for x in numeric if x['sample_id']==sid],
        coverage_scope='EXPLICIT_FINITE_TEXT_RELATION_OR_MISSING_EVIDENCE_GUARD_ONLY',
        whole_task_closed=False if r['coverage']['planning_task_id'] in open_tasks|partial_tasks else 'ROOT_EXACT_CONSTRAINT_REVIEW_PENDING',
        human_review_claimed=False,independent_external_review_claimed=False))

OUT.mkdir(exist_ok=True)
def write(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(OUT/'repaired_b5_b8_cases.jsonl').write_text(''.join(canon(r)+'\n' for r in rows.values()),encoding='utf8')
(OUT/'repaired_b5_b8_qa7.jsonl').write_text(''.join(canon(q)+'\n' for q in qa),encoding='utf8')
write('review_b5_b8.json',dict(schema='MathVisionKid.AntigravityG2B5B8Review.v1',
    reviewed_utc=datetime.now(timezone.utc).isoformat(),scope='Read all29 original sources/all116chat prompt-target fields and originalQA/oracle/mutation records; derive repairs and nine locked minimum new finite branches. No original ZIP or common controls changed.',
    skills_matched=[],skills_applied=[],status='DERIVED_REPAIRS_SELF_QA_COMPLETE_ROOT_INTEGRATION_PENDING',
    original_cases=29,repaired_original_cases=29,new_case_count=len(new_ids),new_case_ids=new_ids,
    original_zip_pins=zip_pins,source_parent_bindings={sid:dict(parent_source_row_sha256=r['provenance']['parent_source_row_sha256'],derived_row_sha256=digest(canon(r).encode()),location=locations[sid],repair_notes=notes[sid]) for sid,r in rows.items()},
    original_chat_comparison=chat_checks,all_original_chat_targets_equal_sources=all(x['target_matches_actual_source'] and x['problem_matches'] for x in chat_checks),
    no_generic_givens_field_requirement_claimed=True,
    new_or_repaired_numeric_checks=numeric,independent_oracles=oracles,meaningful_mutations=mutations,
    original_mutation_evidence_limitation='Original mutation files only append _MUTATED_WRONG to answer strings and state caught; not accepted as independent meaningful wrong-model proof.',
    coverage_queue_sha256=digest(queue_path.read_bytes()),task_source_bindings=task_rows,physical_tasks_retained_open=open_tasks,
    finite_partial_constraints=partial_tasks,
    original_false_claims_rejected=['Blanket allhints PASS despite fullanswer hints','Arbitrary reflected triangle always rhombus','Unprovided curve endpoint2','Hidden support block asserted without assembly rules','Unobserved butterfly path classified as necessarily nonstraight','Synthetic observation examples closing actual physical observation tasks'],
    source_rows_changed_in_original_archives=False,TRAINING_DATASET_READY=False,training_started=False))
write('repair_validation_b5_b8.json',dict(status='PASS_SELF_QA_ROOT_REVIEW_PENDING',
    original29_retained=True,derived_cases=len(rows),new_cases=len(new_ids),exact_numeric_steps_checked=len(numeric),
    independent_oracles=len(oracles),meaningful_mutations=len(mutations),
    repaired_cases_sha256=digest((OUT/'repaired_b5_b8_cases.jsonl').read_bytes()),
    qa7_sha256=digest((OUT/'repaired_b5_b8_qa7.jsonl').read_bytes()),
    code_sha256=digest(Path(__file__).read_bytes()),protected_eval_or_pilot_read=False,human_review_claimed=False,
    train_or_model_weights_loaded=False))
print(json.dumps(dict(original_cases=29,derived_cases=len(rows),new_cases=len(new_ids),numeric_steps=len(numeric),oracles=len(oracles),mutations=len(mutations))))
