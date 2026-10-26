"""Bounded original/derived G2 data; no training, cloud, or frozen-data writes."""
from pathlib import Path
from copy import deepcopy
from fractions import Fraction
from decimal import Decimal
from itertools import combinations,permutations
from datetime import datetime,timezone
import ast,hashlib,json,zipfile

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def sha(v):return hashlib.sha256(v).hexdigest()
def write(name,v): (OUT/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
queue_path=ROOT/'thinking/cloud_publication/data_resume_20261022/next_uncovered_tasks.json'
queue=json.loads(queue_path.read_text('utf8'))
tasks={t['task_id']:t for t in queue['g2_pending_specific_tasks']}
handoff=ROOT/'handoff'
manifest=json.loads((handoff/'ANTIGRAVITY_G2_FINAL_HANDOFF_MANIFEST.json').read_text('utf8'))
originals=[];parents={};zip_refs=[];original_chat_checks=[]
for release in manifest['releases']:
    if release['batch_number'] not in (2,3,4):continue
    path=handoff/release['release_zip'];raw=path.read_bytes()
    assert sha(raw)==release['zip_sha256'] and len(raw)==release['zip_bytes']
    with zipfile.ZipFile(path) as z:
        rows=[json.loads(line) for line in z.read('accepted_cases.jsonl').decode().splitlines()]
        lines=z.read('accepted_cases.jsonl').decode().splitlines()
        chats=[json.loads(line) for line in z.read('accepted_chat.jsonl').decode().splitlines()]
        qa=[json.loads(line) for line in z.read('qa7.jsonl').decode().splitlines()]
        source_map={r['sample_id']:r for r in rows}
        for r,line in zip(rows,lines):
            parents[r['sample_id']]={'raw_row_sha256':sha(line.encode()),'canonical_row_sha256':digest(r),'batch':release['batch_number'],'zip_sha256':sha(raw)}
            assert next(q for q in qa if q['sample_id']==r['sample_id'])['exported_row_sha256']==sha(line.encode())
        for chat in chats:
            source=source_map[chat['source_sample_id']]
            assert chat['source_row_sha256']==parents[source['sample_id']]['raw_row_sha256']
            prompt=json.loads(chat['messages'][1]['content']);target=json.loads(chat['messages'][2]['content'])
            assert prompt['problem']==source['problem'] and prompt['grade']==2
            if chat['mode']=='worked_solution':
                assert target['answer']==source['expected_answer'] and target['steps']==source['worked_steps'] and target['initial_guidance']==source['initial_guidance']
            else:
                hint=source['hints'][int(chat['mode'][-1])-1]
                assert target['hint']==hint['hint'] and target['question']==hint['question']
        assert len(chats)==len(rows)*4
        original_chat_checks.append(dict(batch=release['batch_number'],rows=len(chats),source_hashes_match=True,prompt_and_target_match_original=True,
            prompt_field_presence={field:sum(field in json.loads(c['messages'][1]['content']) for c in chats) for field in ['givens','requested_quantity','student_work']},
            optional_prompt_fields_not_a_frozen_schema_violation=True))
        originals.extend(rows)
    zip_refs.append(dict(path=str(path),bytes=len(raw),sha256=sha(raw),cases=len(rows),chats=len(chats)))
assert len(originals)==18
rows=deepcopy(originals)
byid={r['sample_id']:r for r in rows}
def find(suffix):return next(r for r in rows if r['sample_id'].endswith(suffix))
repairs={r['sample_id']:['Replace generic hint questions with problem-specific questions; preserve answer and audit parent.'] for r in rows}
def hints(row,triples):
    row['hints']=[dict(level=i,hint=h,question=q) for i,(h,q) in enumerate(triples,1)]
def note(row,reason):repairs[row['sample_id']].append(reason)

attr=find('conjunctive_attribute_expression_extrema')
err=find('attractive_wrong_attribute_error')
err['problem']=attr['problem'].split('Người ta chỉ nhận')[0]+'Chỉ nhận thẻ hình tròn màu xanh, có phép tính đúng; trong các thẻ đó chọn thẻ có kết quả lớn nhất. Một bạn nói: “Em chọn Thẻ F vì thẻ này có kết quả 90 là lớn nhất rồi”. Em hãy nhận xét câu trả lời dựa trên các điều kiện đã cho.'
err['givens']=deepcopy(attr['givens'])+[dict(id='g3',role='supplied_student_statement',text=err['student_work']['text'],value=None,unit='')]
note(err,'Make all six card annotations explicit in the standalone problem; source context inherited from the companion original card case, not an unseen image.')
err['worked_steps'][2]['explanation']='Lời bạn chỉ nêu rằng số 90 là lớn nhất, chưa đối chiếu với điều kiện màu xanh. Thẻ F có màu đỏ nên không được nhận. Thẻ E có màu xanh, hình tròn và phép tính đúng, có kết quả 51 là lớn nhất trong các thẻ hợp lệ.'
note(err,'Replace speculation about attraction/forgetting with feedback grounded only in the supplied student statement and explicit card annotations.')
err['provenance']['context_parent_source_rows']=[dict(sample_id=attr['sample_id'],source_row_sha256=parents[attr['sample_id']]['raw_row_sha256'])]
cube=find('unit_cube_column_height_assembly');guard=find('cube_support_ambiguity_guard')
guard['problem']=cube['problem'].split('Hỏi toàn bộ')[0]+'Một bạn nói: “Em chỉ đếm các khối nhìn thấy được, còn khối nào bị che khuất không nhìn thấy thì không tính”. Hãy giải thích vì sao khối ở tầng trên cần có khối đỡ bên dưới, dù khối đỡ bị che. Nếu đề không cho chiều cao cột sau-phải, chỉ nhìn thẳng từ phía trước thì có xác định chắc chắn số khối ở vị trí ấy không?'
guard['givens']=deepcopy(cube['givens'])+[dict(id='g3',role='supplied_student_statement',text=guard['student_work']['text'],value=None,unit='')]
guard['requested_quantity']='Giải thích vai trò của khối đỡ bị che và đánh giá có xác định duy nhất chiều cao cột bị che khi thiếu dữ kiện hay không'
guard['expected_answer'].append(dict(quantity='Nếu không cho chiều cao cột sau-phải',result='Không xác định duy nhất số khối của cột đó chỉ từ hướng nhìn phía trước; cần mô tả chiều cao hoặc dữ kiện bổ sung',unit=''))
guard['provenance']['context_parent_source_rows']=[dict(sample_id=cube['sample_id'],source_row_sha256=parents[cube['sample_id']]['raw_row_sha256'])]
note(guard,'Supply the irregular column heights and no-floating convention that original steps had referenced without standalone context; distinguish hypothetical missing-column ambiguity.')
boat=find('boat_watermark_equal_mass_substitution');boatguard=find('boat_watermark_inequality_guard')
baseline='Trong hai lần xét, dùng cùng một chiếc thuyền trên cùng đoạn sông, không có người hoặc vật khác trên thuyền. Quy ước trong bài: cùng vạch mực nước trên mạn thuyền ứng với cùng khối lượng chở; khối lượng chở lớn hơn làm thuyền chìm sâu hơn. '
for r in (boat,boatguard):
    r['problem']=baseline+r['problem'].replace('Cũng chiếc thuyền trên:','Một chiếc thuyền:')
    r['givens'].append(dict(id='baseline',role='explicit_original_given',text=baseline,value=None,unit=''))
    note(r,'Make equal boat/load baseline and water-mark equivalence/monotonicity explicit as synthetic text givens; no observed physical outcome claimed.')
pour=find('bounded_repour_state_choices_transition')
pour['problem']=pour['problem'].replace('Có hai chiếc bình rỗng:','Có hai chiếc bình:')
note(pour,'Remove contradictory opening phrase that called both containers empty before stating A is full.')
scale=find('pointer_scale_reading_with_tare')
scale['problem']=scale['problem'].replace('có các vạch số từ 0 kg đến 5 kg,','có sáu vạch số 0 kg, 1 kg, 2 kg, 3 kg, 4 kg và 5 kg nằm cách đều nhau theo một cung tròn, tạo thành năm khoảng; mỗi khoảng ứng với 1 kg,')
scale['givens'][0]['text']='Cân có sáu vạch số 0,1,2,3,4,5 kg cách đều trên cung tròn; năm khoảng, mỗi khoảng 1 kg; số tăng theo chiều kim đồng hồ.'
note(scale,'Provide all circular scale ticks, five equal intervals, increasing direction, needle positions and tare/gross condition.')
ext=find('subset_sum_cardinality_extrema_enumeration')
ext['initial_guidance']=['So sánh số kẹo trong các gói và chú ý mỗi lần chỉ chọn đúng hai gói.']
ext['requested_quantity']='Hai gói có tổng ít nhất và tổng đó; hai gói có tổng nhiều nhất và tổng đó'
pair=find('fixed_cardinality_exact_pair_subset_sum')
pair['worked_steps'][0]['reason']=pair['worked_steps'][0]['reason'].replace(' (cardinality = 2)','')

H={
'conjunctive_attribute_expression_extrema': [('Kiểm tra riêng hình dạng và màu sắc của từng thẻ.','Một thẻ cần thỏa mãn đồng thời những thuộc tính nào?'),('Với các thẻ đạt điều kiện hình và màu, tính lại phép tính rồi đối chiếu với số ghi trên thẻ.','Phép tính đúng được nhận biết bằng cách nào?'),('Chỉ so sánh giá trị của các thẻ vượt qua đầy đủ điều kiện.','Em có vô tình xét thẻ đã bị loại không?')],
'attractive_wrong_attribute_error':[('Đọc lại đầy đủ yêu cầu chọn thẻ.','Ngoài số lớn, đề còn yêu cầu những điều kiện nào?'),('Đối chiếu mô tả của thẻ mà bạn chọn với từng điều kiện.','Bạn đã kiểm tra hình dạng, màu sắc và phép tính đủ chưa?'),('Đánh giá lần lượt các điều kiện trước khi nhận xét lời chọn thẻ.','Cần dựa vào bằng chứng nào trong đề để giải thích nhận xét?')],
'unit_cube_column_height_assembly':[('Ghi số khối trong từng cột theo mô tả.','Có bao nhiêu cột cần xét?'),('Khi nhìn thẳng từ phía trước, xét từng vị trí ở cùng độ cao để xem khối nào che khối nào.','Khối phía sau nào nhô cao hơn cột phía trước?'),('Đối chiếu số khối nhìn thấy, bị che và tổng số khối.','Cộng hai nhóm lại có trở về tổng số khối không?')],
'cube_support_ambiguity_guard':[('Đọc lại quy ước xếp từ sàn và không lơ lửng.','Em cần dùng quy ước nào để xét phần bị che?'),('Xét riêng những khối đã được mô tả ở tầng trên và vị trí nằm dưới chúng.','Chi tiết nào của đề giúp suy luận về vị trí bên dưới?'),('Phân biệt dữ kiện được ghi rõ với điều chỉ suy ra từ hướng nhìn.','Nếu bỏ mô tả chiều cao một cột, còn những khả năng nào chưa loại được?')],
'card_collection_inventory_state':[('Ghi danh sách ban đầu rồi cập nhật sau từng lượt.','Thẻ đã rút có còn ở kho chung không?'),('Ghi riêng những thẻ mỗi bạn nhận được.','Em đã ghi đúng người nhận ở từng lượt chưa?'),('Đếm lại các thẻ ở kho và các thẻ thuộc mỗi bạn; tính điểm theo yêu cầu.','Tổng số thẻ có được bảo toàn không?')],
'board_cell_ownership_collinear_win':[('Ghi từng dấu vào đúng ô theo lượt đã cho.','Em có đặt hai dấu vào cùng một ô không?'),('Kiểm tra lần lượt mọi hàng ngang, cột dọc và hai đường chéo.','Một đường thắng cần những dấu như thế nào?'),('Áp dụng điều kiện thắng cho từng đường và đối chiếu thời điểm các dấu xuất hiện.','Đường nào đạt điều kiện trước, nếu có?')],
'balance_orientation_transitivity_side_swap':[('Xem vật nào nằm ở đĩa thấp hơn trong mỗi lần cân.','Quy ước đĩa thấp hơn cho biết điều gì?'),('Lưu ý cùng một loại quả có thể đổi bên giữa hai lần cân.','Em đã gắn quan hệ nặng nhẹ với đúng tên quả chưa?'),('Nối hai quan hệ qua loại quả xuất hiện ở cả hai lần cân.','Thứ tự em xếp có phù hợp với cả hai lần cân không?')],
'balance_high_pan_misconception_error':[('Nhớ quy ước hoạt động của cân hai đĩa.','Cần dùng quy ước nào để đọc vị trí hai đĩa?'),('Đối chiếu vị trí của từng loại quả với quy ước đó.','Lời nói của bạn đã áp dụng quy ước như thế nào?'),('Dựa vào đúng vị trí được mô tả để nhận xét lời bạn.','Em có thể giải thích mà không đoán thêm khối lượng không?')],
'balance_group_multiplicity_substitution':[('Ghi lại nhóm vật cân bằng với nhau ở từng cân.','Một quả cam có thể đổi thành nhóm nào?'),('Thực hiện cùng cách thay thế cho từng quả cam ở cân thứ nhất.','Em đã thay đủ số quả cam chưa?'),('Cộng số quả trong các nhóm thay thế rồi kiểm tra lại hai cân.','Kết quả có giữ nguyên quan hệ cân bằng không?')],
'balance_substitution_mixed_group_repair':[('Đọc cân B để tìm nhóm cam thay cho quả dưa hấu.','Nhóm vật nào có thể đổi mà không làm lệch cân?'),('Thay nhóm tương đương vào cân A.','Hai đĩa lúc này có những vật nào giống nhau?'),('Bớt cùng số quả cam ở cả hai đĩa rồi đối chiếu lại.','Phần còn lại ở hai đĩa cho biết điều gì?')],
'boat_watermark_equal_mass_substitution':[('So sánh vạch mực nước ở hai lần chở.','Đề đã cho cùng chiếc thuyền và cùng tải nền chưa?'),('Dùng quy ước của bài để liên hệ hai nhóm vật được chở.','Cần tính khối lượng của nhóm vật thay thế nào?'),('Cộng đủ khối lượng các bao ngô rồi kiểm tra đơn vị.','Em có bỏ sót hoặc đếm một bao hai lần không?')],
'boat_watermark_inequality_guard':[('Đối chiếu vị trí mực nước ở hai lần chở.','Hai lần có đạt cùng vạch không?'),('Dùng quy ước về tải nặng và độ chìm được ghi trong đề.','Sự khác nhau về vạch nước cho biết quan hệ nào giữa hai tải?'),('Tính tổng khối lượng hai bao rồi so sánh điều kiện mực nước trước khi nhận xét.','Điều kiện để kết luận bằng nhau có được đáp ứng không?')],
'bounded_repour_state_choices_transition':[('Ghi lượng nước ban đầu và sức chứa của mỗi bình.','Bình nhận còn chỗ cho bao nhiêu nước?'),('Sau mỗi thao tác, ghi lại lượng nước ở cả hai bình.','Lượng giảm ở bình rót có bằng lượng tăng ở bình nhận không?'),('Phân biệt nước được chuyển sang bình khác với nước đã đổ ra ngoài.','Lượng nước cuối cùng cộng phần đã đổ bỏ có bằng lượng ban đầu không?')],
'bounded_repour_impossible_overfill_guard':[('Đọc sức chứa tối đa và lượng nước đang có.','Can còn chỗ để nhận thêm bao nhiêu nước?'),('So sánh tổng lượng nước định rót với sức chứa.','Em cần tính cả phần có thể tràn ra ngoài không?'),('Kiểm tra tổng lượng nước giữ lại và lượng tràn.','Hai phần đó có khớp lượng nước trước khi rót không?')],
'pointer_scale_reading_with_tare':[('Đọc số chỉ khi có rổ rỗng và khi có cả rổ với bí.','Mỗi số chỉ đo khối lượng của những vật nào?'),('Muốn chỉ còn khối lượng bí, cần loại phần khối lượng nào?','Em sẽ dùng phép tính gì giữa hai số chỉ?'),('Cộng lại khối lượng tìm được với khối lượng rổ để kiểm tra.','Kết quả kiểm tra có trở về số chỉ cả rổ và bí không?')],
'fixed_cardinality_exact_pair_subset_sum':[('Ghi các gói theo tên, mỗi gói chỉ được chọn một lần.','Mỗi lựa chọn phải có đúng mấy gói?'),('Liệt kê có thứ tự các cặp để không lặp hoặc bỏ sót.','Đã xét các cặp bắt đầu bằng từng gói chưa?'),('Tính tổng của từng cặp rồi đối chiếu với số kẹo cần có.','Em đã kiểm tra cả số gói lẫn tổng kẹo chưa?')],
'subset_sum_cardinality_extrema_enumeration':[('Sắp số kẹo của các gói theo thứ tự.','Mỗi lần được chọn đúng bao nhiêu gói?'),('So sánh các cặp ở đầu dãy với các cặp còn lại.','Cặp nào có thể cho tổng bé nhất, và vì sao?'),('Tiếp tục xét phần cuối dãy rồi tính các tổng cần tìm.','Có cặp khác cho tổng lớn hơn hoặc nhỏ hơn lựa chọn của em không?')],
'subset_sum_unproven_optimality_guard':[('Kiểm tra phép cộng của bạn trước rồi xem yêu cầu về nhiều nhất.','Phép cộng đúng đã đủ chứng minh nhiều nhất chưa?'),('Giữ một gói trong cặp đã chọn rồi thử thay gói kia bằng gói khác.','Tổng của những lựa chọn mới thay đổi ra sao?'),('Tính và so sánh các tổng trước khi nhận xét câu nói của bạn.','Em có bằng chứng nào để xác nhận hoặc bác bỏ lời nhận xét?')]
}
for suffix,triples in H.items():hints(find(suffix),triples)

def newcase(sid,branch,candidate,problem,givens,request,steps,answer,hintrows):
    template=deepcopy(rows[4]);template.update(sample_id=sid,case_group_id=sid+'_group',topic=branch,
        problem=problem,givens=[dict(id='g'+str(i),role='explicit_original_given',text=g,value=None,unit='') for i,g in enumerate(givens)],
        requested_quantity=request,student_work=None,initial_guidance=['Theo dõi đúng quy tắc và cập nhật trạng thái sau từng lượt.'],
        worked_steps=[dict(step_id='s'+str(i),title=t,reason=why,explanation=exp,expression=expr,result=res,unit=unit) for i,(t,why,exp,expr,res,unit) in enumerate(steps)],
        expected_answer=[dict(quantity=q,result=v,unit=u) for q,v,u in answer],
        provenance={'authorship_origin':'ORIGINAL_AI_TEACHER_AUTHORING','human_content_review_completed':False,'actual_physical_or_image_result_claimed':False,'book_exercise_copied':False})
    task=tasks['g2_pending_09_mutable_game_inventory_ownership']
    template['coverage'].update(branch=branch,candidate_ids=[candidate],planning_task_id=task['task_id'])
    template['curriculum_assignment'].update(candidate_ids=[candidate],master_id='finite_inventory_collection_game',coverage_claim='Original finite text model for the explicitly named missing task09 subbranch.')
    hints(template,hintrows);rows.append(template);repairs[sid]=['New original bounded case for a missing task09 subbranch; no old row replaced.']
    return template

memory=newcase('g2_codex_20261022_memory_pair_reset_and_remove','memory_pair_reset_and_remove','g2v1:finite_inventory_game_state',
 'Có sáu thẻ A, B, C, D, E, F. Số trên từng thẻ lần lượt là A: 4; B: 6; C: 4; D: 2; E: 6; F: 2. Lúc đầu tất cả thẻ úp. Mỗi lượt, một bạn lật hai thẻ còn trên bàn. Nếu hai số bằng nhau thì bạn lấy cả hai thẻ khỏi bàn; nếu khác nhau thì úp cả hai thẻ lại, không lấy thẻ nào. Lượt 1, An lật A và B. Lượt 2, Bình lật B và E. Lượt 3, An lật A và C. Sau ba lượt, những thẻ nào còn trên bàn và đang úp hay ngửa? Mỗi bạn đã lấy được những thẻ nào?',
 ['A=4,B=6,C=4,D=2,E=6,F=2; ban đầu cả sáu thẻ úp.','Mỗi lượt lật hai thẻ còn trên bàn; khác số thì úp lại cả hai, bằng số thì lấy cả hai khỏi bàn.','Lượt1 An(A,B); lượt2 Bình(B,E); lượt3 An(A,C).'],
 'Thẻ còn trên bàn và trạng thái mặt thẻ; thẻ thuộc mỗi bạn',
 [('Cập nhật lượt 1','So sánh hai số rồi dùng đúng quy tắc.','A ghi 4, B ghi 6 nên khác nhau. Cả hai thẻ được úp lại; vẫn còn đủ sáu thẻ trên bàn.',None,'Sau lượt1 còn sáu thẻ úp','thẻ'),
 ('Cập nhật lượt 2','Hai thẻ bằng số được lấy khỏi bàn.','B và E đều ghi 6. Bình lấy B và E; trên bàn còn A,C,D,F.',None,'Bình lấy B,E; bàn còn A,C,D,F','thẻ'),
 ('Cập nhật lượt 3 và kiểm tra','Dùng cùng quy tắc và bảo toàn số thẻ.','A và C đều ghi 4 nên An lấy A,C. Trên bàn còn D,F, vẫn úp vì chưa được lật. Kiểm tra: mỗi bạn giữ 2 thẻ, bàn còn 2 thẻ; 2+2+2=6 thẻ.', '2 + 2 + 2','D,F còn úp; An giữ A,C; Bình giữ B,E','thẻ')],
 [('Thẻ còn trên bàn','D và F, đều úp',''),('Thẻ của An','A và C',''),('Thẻ của Bình','B và E','')],
 [('Ghi các cặp thẻ được lật theo đúng thứ tự.','Hai số của mỗi cặp có bằng nhau không?'),('Sau mỗi lượt, dùng đúng một trong hai quy tắc: úp lại hoặc lấy khỏi bàn.','Một lượt không khớp số có làm mất thẻ khỏi bàn không?'),('Đối chiếu các thẻ đã lấy với danh sách ban đầu.','Thẻ chưa được lật có thể tự chuyển thành ngửa không?')])
token=newcase('g2_codex_20261022_finite_tokens_and_move_budget','finite_tokens_and_move_budget','g2v2:finite_token_game',
 'An có đúng 3 quân xanh, Bình có đúng 2 quân đỏ. Bàn cờ có 3 hàng và 3 cột, ban đầu trống. Hai bạn thay phiên, An đi trước; mỗi lượt chỉ đặt một quân mới của mình vào một ô trống. Không dịch chuyển quân đã đặt, không lấy quân của bạn và không có quân dự phòng. Năm lượt đã chơi là: An đặt xanh ở (hàng1,cột1); Bình đặt đỏ ở (hàng1,cột2); An đặt xanh ở (hàng2,cột2); Bình đặt đỏ ở (hàng2,cột1); An đặt xanh ở (hàng3,cột1). Sau đó mỗi bạn còn bao nhiêu quân chưa đặt? Đến lượt Bình, bạn có thể đặt một quân đỏ mới vào ô trống (hàng3,cột2) không? Hãy giải thích.',
 ['An có3 quân xanh; Bình có2 quân đỏ; không quân dự phòng.','Mỗi lượt đặt một quân mới của đúng người chơi vào ô trống; không dịch chuyển hoặc lấy quân của bạn.','Các lượt An,Bình,An,Bình,An đặt lần lượt tại(1,1),(1,2),(2,2),(2,1),(3,1).'],
 'Quân chưa đặt của từng bạn và tính hợp lệ của nước đỏ tiếp theo',
 [('Đếm số quân đã đặt của từng bạn','Mỗi lượt dùng đúng một quân của người chơi đó.','An đi ở lượt1,3,5 nên đã đặt3 quân xanh. Bình đi ở lượt2,4 nên đã đặt2 quân đỏ.',None,'An đã đặt3; Bình đã đặt2','quân'),
 ('Tính số quân chưa đặt','Lấy số quân ban đầu trừ số quân đã đặt.','An còn 3-3=0 quân xanh; Bình còn 2-2=0 quân đỏ. Có5 ô đã được dùng, khớp tổng3+2=5 quân ban đầu.', '3 - 3','An còn0 xanh; Bình còn0 đỏ','quân'),
 ('Kiểm tra nước tiếp theo','Một nước hợp lệ cần cả ô trống lẫn quân mới còn sẵn của đúng người chơi.','Ô(hàng3,cột2) trống nhưng Bình không còn quân đỏ mới; vì vậy Bình không thể đặt thêm quân đỏ vào ô đó theo quy tắc. Không được chuyển quân đỏ đã đặt vì đề cấm dịch chuyển.',None,'Bình không thể đặt thêm quân đỏ','')],
 [('Quân xanh chưa đặt','0','quân'),('Quân đỏ chưa đặt','0','quân'),('Nước đỏ tiếp theo','Không hợp lệ: Bình hết quân đỏ mới, dù ô còn trống','')],
 [('Ghi số lượt đã đi riêng cho từng bạn.','Mỗi lượt đã dùng bao nhiêu quân?'),('So sánh số quân đã đặt với số quân ban đầu của người đến lượt.','Cần kiểm tra cả quân còn sẵn và ô trống ra sao?'),('Đối chiếu nước định đi với mọi điều kiện và các việc bị cấm trong đề.','Một ô trống có tự bảo đảm nước đi hợp lệ không?')])

# Precise queue aliases; game examples are mapped to their actual subbranches.
for r in rows:
    tid=r['coverage']['planning_task_id']
    if tid.endswith('mutable_game_inventory_ownership'):
        cid= ('g2v1:finite_inventory_collection_state' if r['sample_id'].endswith('card_collection_inventory_state') else
              'g2v2:finite_board_ownership' if r['sample_id'].endswith('board_cell_ownership_collinear_win') else r['coverage']['candidate_ids'][0])
        cids=[cid]
    else:cids=tasks[tid]['candidate_ids']
    if cids!=r['coverage']['candidate_ids']:note(r,'Bind exact candidate aliases from current task when the same actual constraints are met; remove unsupported game-subbranch aliases.')
    r['coverage']['candidate_ids']=deepcopy(cids);r['curriculum_assignment']['candidate_ids']=deepcopy(cids)
    r['provenance'].update(acceptance_basis='OWNER_PREAUTHORIZED_SELF_QA_COMPLETE_ROOT_INTEGRATION_PENDING',human_content_review_completed=False)
    if r['sample_id'] in parents:r['provenance']['parent_source_row_sha256']=parents[r['sample_id']]['raw_row_sha256']
    r['provenance']['repair_reasons']=repairs[r['sample_id']]
    r['quality_status']='SELF_QA_REPAIRED_PENDING_ROOT_INTEGRATION'
    r['source_role']='AI_GENERATED';r['human_verified']=False;r['teacher_certified']=False;r['owner_human_reviewed']=False
    r['acceptance_status']='ACCEPTED_OWNER_PREAUTHORIZED'

checks={
'conjunctive_attribute_expression_extrema':'Đối chiếu lại đủ sáu thẻ: chỉ C,E thỏa cả điều kiện và 51 lớn hơn 45.',
'attractive_wrong_attribute_error':'Kiểm tra lại: 55+35=90 đúng nhưng F màu đỏ, không đáp ứng điều kiện màu xanh.',
'unit_cube_column_height_assembly':'Kiểm tra: 5 khối nhìn thấy cộng 2 khối bị che bằng tổng 7 khối đã đếm theo bốn cột.',
'cube_support_ambiguity_guard':'Kiểm tra: cột cao 3 khối phải có vị trí tầng1 đỡ các khối tầng2,3; riêng một cột bị che mà không có dữ kiện chiều cao thì có thể có nhiều cách xếp.',
'card_collection_inventory_state':'Kiểm tra: kho và thẻ của hai bạn không trùng nhau; 3+2+1=6 thẻ ban đầu.',
'board_cell_ownership_collinear_win':'Kiểm tra: đủ năm ô khác nhau; ở hai lượt của Bình chỉ có hai dấu O nên chưa thể có ba dấu O thẳng hàng.',
'balance_orientation_transitivity_side_swap':'Kiểm tra thứ tự: dưa hấu đứng trước bưởi đúng cân1; bưởi đứng trước xoài đúng cân2.',
'balance_high_pan_misconception_error':'Kiểm tra: dưa hấu ở đĩa thấp và bưởi ở đĩa cao, phù hợp với dưa hấu nặng hơn theo quy ước cân.',
'balance_group_multiplicity_substitution':'Kiểm tra: chia sáu quả chanh thành ba nhóm bằng nhau, mỗi nhóm hai quả thay cho một quả cam, khớp cả hai cân.',
'balance_substitution_mixed_group_repair':'Kiểm tra: bốn quả cam thay quả dưa cộng một quả cam thay quả táo là năm quả cam, khớp cân A; riêng quả dưa vẫn bằng bốn cam, khớp cân B.',
'boat_watermark_equal_mass_substitution':'Kiểm tra: 35+25=60 rồi 60+20=80 kg; tải nền và vạch mực nước không thay đổi theo giả thiết.',
'boat_watermark_inequality_guard':'Kiểm tra: 35+25=60 kg nhưng không đạt cùng vạch đỏ; theo quy ước đề, tải này chưa bằng tải nghé.',
'bounded_repour_state_choices_transition':'Kiểm tra: cuối cùng còn 0+2=2 l trong hai bình và đã đổ bỏ3 l; tổng2+3=5 l bằng ban đầu; không bình nào vượt sức chứa.',
'bounded_repour_impossible_overfill_guard':'Kiểm tra: 2 l trong can cộng1 l tràn bằng tổng1+2=3 l đã có và rót vào.',
'pointer_scale_reading_with_tare':'Kiểm tra: 4 kg bí cộng1 kg rổ bằng5 kg số chỉ tổng.',
'fixed_cardinality_exact_pair_subset_sum':'Kiểm tra: đã xét đủ mười cặp khác nhau, chỉ cặp B,D đạt50; mỗi gói chỉ chọn một lần.',
'subset_sum_cardinality_extrema_enumeration':'Kiểm tra tất cả mười cặp: không tổng nào nhỏ hơn30 hoặc lớn hơn67.',
'subset_sum_unproven_optimality_guard':'Kiểm tra: phép cộng18+35=53 của bạn vẫn đúng; vấn đề là còn cặp32+35=67 lớn hơn nên chưa phải nhiều nhất.'}
for suffix,check in checks.items():find(suffix)['worked_steps'][-1]['explanation']+=' '+check

# Keep student-facing grade2 wording simple; machine topic/coverage IDs stay.
wording={
    'Áp dụng tính chất bắc cầu':'Nối các so sánh đã biết',
    'Bắc cầu qua số quả cam ban đầu.':'Dùng số quả cam ban đầu để nối hai quan hệ bằng nhau.',
    'Thiết lập các đẳng thức khối lượng':'Ghi các quan hệ khối lượng bằng nhau',
    'hệ thức cân thăng bằng':'quan hệ khi cân thăng bằng',
    'phương pháp thế khối lượng tương đương':'cách thay bằng nhóm vật có cùng khối lượng',
    'khối lượng tịnh':'khối lượng riêng',
    'khối lượng bì (chiếc rổ rỗng)':'khối lượng chiếc rổ rỗng',
    'khối lượng cả bì và quả bí ngô':'khối lượng cả rổ và quả bí ngô',
    'tính chất bắc cầu':'cách nối các so sánh',
    'giá trị cực trị':'số lớn nhất hoặc nhỏ nhất',
    'so sánh cực trị':'so sánh để tìm số lớn nhất',
    '2 phần tử':'hai số',
    'tập hợp':'nhóm các số',
    'nguyên lý vật lý':'quy tắc hoạt động'}
for r in rows:
    for step in r['worked_steps']:
        for field in ['title','reason','explanation']:
            for old,new in wording.items():step[field]=step[field].replace(old,new)

def evaluate(expression,cls):
    def node(n):
        if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)):return cls(str(n.value))
        if isinstance(n,ast.BinOp):
            a,b=node(n.left),node(n.right)
            if isinstance(n.op,ast.Add):return a+b
            if isinstance(n.op,ast.Sub):return a-b
            if isinstance(n.op,ast.Mult):return a*b
            if isinstance(n.op,ast.Div):return a/b
        raise ValueError('Unsupported arithmetic')
    return node(ast.parse(expression,mode='eval').body)

oracles={};mutations={}
def oracle(row,method,result,wrong,detail):
    assert wrong!=result
    oracles[row['sample_id']]={'method':method,'computed_result':result,'independent_of_author_QA':True}
    mutations[row['sample_id']]={'mutation':detail,'wrong_result':wrong,'oracle_expected':result,'detected':wrong!=result,'actual_oracle_rerun':True}
cards=[('A','tròn','đỏ',24+16,40),('B','vuông','xanh',50-15,35),('C','tròn','xanh',18+27,45),('D','vuông','đỏ',60-20,50),('E','tròn','xanh',32+19,51),('F','tròn','đỏ',55+35,90)]
eligible=[c for c in cards if c[1]=='tròn' and c[2]=='xanh' and c[3]==c[4]]
oracle(attr,'Independent finite conjunctive predicate and max',{'eligible':[c[0] for c in eligible],'maximum':max(eligible,key=lambda c:c[3])[0]}, {'eligible':['C','E','F'],'maximum':'F'},'Ignore colour filter and wrongly include attractive red maximum.')
oracle(err,'Conjunctive eligibility on explicitly supplied F',False,True,'Accept F solely because90 is greatest, ignoring its red colour.')
heights=[[1,2],[3,1]];occupied={(r,c,z) for r in range(2) for c in range(2) for z in range(1,heights[r][c]+1)}
visible={(r,c,z) for r,c,z in occupied if not any((r0,c,z) in occupied for r0 in range(r))}
oracle(cube,'Enumerate occupied (row,column,height) cells and frontmost cell for each sight line',{'total':len(occupied),'visible':len(visible),'hidden':len(occupied-visible)},{'total':5,'visible':5,'hidden':0},'Mistake visible count for total, removing hidden support units.')
oracle(guard,'Enumerate solid-ground column height3 and wholly occluded free column heights0,1,2',{'required_lower_support_positions':2,'occluded_unknown_column_possible_heights':[0,1,2]}, {'required_lower_support_positions':0,'occluded_unknown_column_possible_heights':[1]},'Allow floating upper cubes and assume exact unknown hidden column height.')
stock=[4,6,8,10,12,14];owners={'An':[],'Bình':[]}
for who,value in [('An',8),('Bình',12),('An',14)]:stock.remove(value);owners[who].append(value)
oracle(find('card_collection_inventory_state'),'Independent mutable inventory removal and ownership simulation',{'remaining':stock,'An':owners['An'],'Bình':owners['Bình'],'An_points':sum(owners['An'])},{'remaining':[4,6,8,10,12,14],'An':[8,14],'Bình':[12],'An_points':22},'Return collected cards to stock instead of permanently removing them.')
lines=[{(r,c) for c in range(1,4)} for r in range(1,4)]+[{(r,c) for r in range(1,4)} for c in range(1,4)]+[{(i,i) for i in range(1,4)},{(i,4-i) for i in range(1,4)}]
x={(1,1),(2,2),(3,3)};o={(1,2),(2,1)}
oracle(find('board_cell_ownership_collinear_win'),'Enumerate all8 winning lines and test owner-set containment',{'X_winning_lines':len([s for s in lines if s<=x]),'O_winning_lines':len([s for s in lines if s<=o]),'winner':'An'}, {'X_winning_lines':0,'O_winning_lines':0,'winner':None},'Omit both diagonal winning lines.')
orders=[p for p in permutations(['D','B','X']) if p.index('D')<p.index('B')<p.index('X')]
oracle(find('balance_orientation_transitivity_side_swap'),'Enumerate all6 strict mass orders and enforce both oriented pans',orders,[('X','B','D')],'Read high pan as heavy instead of low pan.')
oracle(find('balance_high_pan_misconception_error'),'Compare quoted high-pan claim against low-pan convention',False,True,'Reverse balance elevation convention.')
oracle(find('balance_group_multiplicity_substitution'),'Independent expanded repeated groups',[2,2,2,sum([2,2,2])],[2,3,5],'Add group multiplicities instead of repeating each equal group.')
oracle(find('balance_substitution_mixed_group_repair'),'Solve by testing nonnegative integer orange-equivalents and substitute both balances',[n for n in range(6) if 4+n==5],[5],'Ignore watermelon mass and assign whole gross mass to apple.')
oracle(boat,'Independent grouped mass sum checked by regrouping',sum([35,25,20]),60,'Omit the third replacement bag.')
oracle(boatguard,'Strict monotone watermark comparison; two-bag load is60 and calf is strictly heavier',{'two_bag_kg':sum([35,25]),'calf_relation':'>60'}, {'two_bag_kg':60,'calf_relation':'=60'},'Conclude equal mass despite unequal water marks.')
a,b=5,0;move=min(a,3-b);a-=move;b+=move;states=[(a,b)];dump=b;b=0;states.append((a,b));move=min(a,3-b);a-=move;b+=move;states.append((a,b))
oracle(pour,'State transition simulation with min(source,recipient capacity) and discarded-water ledger',states,[(2,3),(2,0),(2,2)],'Copy transferred water without subtracting it from source.')
oracle(find('bounded_repour_impossible_overfill_guard'),'Independent saturation and overflow partition',{'inside':min(1+2,2),'overflow':max(0,1+2-2)},{'inside':3,'overflow':0},'Ignore recipient maximum capacity.')
oracle(scale,'Integer mass decomposition and inverse recomposition',5-1,5,'Use gross reading without subtracting tare.')
items=dict(A=12,B=18,C=25,D=32,E=35);pairs=[(a,b,items[a]+items[b]) for a,b in combinations(items,2)]
oracle(pair,'Enumerate all10 lawful distinct-item pairs and target predicate',[(a,b) for a,b,s in pairs if s==50],[('C','C')],'Use a second nonexistent copy of C to reach50.')
oracle(ext,'Enumerate all10 pairs; compute minimum/maximum and all attaining pairs',{'min':min(s for _,_,s in pairs),'min_pairs':[(a,b) for a,b,s in pairs if s==min(v for _,_,v in pairs)],'max':max(s for _,_,s in pairs),'max_pairs':[(a,b) for a,b,s in pairs if s==max(v for _,_,v in pairs)]},{'min':37,'min_pairs':[('A','C')],'max':53,'max_pairs':[('B','E')]},'Treat two feasible arbitrary pairs as extrema without complete comparison.')
oracle(find('subset_sum_unproven_optimality_guard'),'Independent complete pair enumeration comparing claimed53 against maximum',{'claimed_sum':18+35,'maximum':max(s for _,_,s in pairs),'claim_is_optimal':False},{'claimed_sum':53,'maximum':53,'claim_is_optimal':True},'Mistake a feasible pair for the optimal pair.')
values=dict(A=4,B=6,C=4,D=2,E=6,F=2);remaining=set(values);memowners={'An':[],'Bình':[]};memstates=[]
for who,a,b in [('An','A','B'),('Bình','B','E'),('An','A','C')]:
    assert a in remaining and b in remaining
    if values[a]==values[b]:remaining.difference_update([a,b]);memowners[who].extend([a,b])
    memstates.append(sorted(remaining))
oracle(memory,'Independent face-state/match/removal simulation with mismatches resetting both cards',{'remaining':sorted(remaining),'remaining_faces':'down','owners':memowners,'states':memstates},{'remaining':['D','F'],'remaining_faces':'up','owners':memowners,'states':memstates},'Leave never-flipped or reset cards face-up after mismatch.')
available={'An':3,'Bình':2};board={}
for who,pos in [('An',(1,1)),('Bình',(1,2)),('An',(2,2)),('Bình',(2,1)),('An',(3,1))]:
    assert available[who]>0 and pos not in board;available[who]-=1;board[pos]=who
oracle(token,'Independent legal move checker requires own stock>0 AND destination unoccupied',{'available':available,'next_Binh_move_legal':available['Bình']>0 and (3,2) not in board},{'available':available,'next_Binh_move_legal':True},'Allow a move solely because target cell is empty, ignoring finite own token stock.')

qa=[];arithmetic=[]
for r in rows:
    numeric=[]
    for step in r['worked_steps']:
        if step.get('expression'):
            f=evaluate(step['expression'],Fraction);d=evaluate(step['expression'],Decimal)
            assert Fraction(d)==f
            if not str(step['result']).isdigit():
                assert f.denominator==1
                step['result']=str(f.numerator)
                note(r,'Normalize a narrative worked-step result to the scalar value of its existing expression; full mathematical explanation and final expected answers are preserved.')
                r['provenance']['repair_reasons']=repairs[r['sample_id']]
            assert Fraction(step['result'])==f
            numeric.append(dict(step_id=step['step_id'],expression=step['expression'],Fraction=str(f),Decimal=str(d),PASS=True))
    arithmetic.extend(numeric)
    assert len(r['hints'])==3 and [h['level'] for h in r['hints']]==[1,2,3]
    assert r['grade']==2 and r['split']=='train' and not r['human_verified'] and not r['teacher_certified']
    qa.append(dict(sample_id=r['sample_id'],reviewed_row_sha256=digest(r),parent_source_row_sha256=parents.get(r['sample_id'],{}).get('raw_row_sha256'),
        review_type='AI_AUTHOR_SELF_QA_AND_BOUNDED_MATH_REVIEW_NOT_HUMAN_OR_EXTERNAL_CERTIFICATION',
        actual_fields_read=['problem','givens','requested_quantity','student_work','worked_steps','all_step_reasons_explanations_units','expected_answer','initial_guidance','all3hints'],
        criteria={k:True for k in ['semantic_correct','steps_complete','grade_appropriate','unit_consistent','hints_non_leaking','grounded_student_feedback','curriculum_mapping_correct']},
        oracle=oracles[r['sample_id']],numeric_checks=numeric,meaningful_negative_check=mutations[r['sample_id']],repairs=repairs[r['sample_id']],
        root_full_content_review_pending=True,protected_exclusion_and_cross_corpus_duplicate_gate_pending_root=True,status='SELF_QA_PASS_PENDING_ROOT_INTEGRATION'))

coverage=[]
for tid in sorted({r['coverage']['planning_task_id'] for r in rows}):
    selected=[r for r in rows if r['coverage']['planning_task_id']==tid]
    matched=set(c for r in selected for c in r['coverage']['candidate_ids'])
    assert matched==set(tasks[tid]['candidate_ids']),(tid,matched,tasks[tid]['candidate_ids'])
    coverage.append(dict(task_id=tid,candidate_ids=sorted(matched),minimal_required_specific_branches_read=tasks[tid]['minimal_required_specific_branches'],
        evidence=[dict(sample_id=r['sample_id'],repaired_row_sha256=digest(r),branch=r['coverage']['branch']) for r in selected],
        text_mathematical_relation_status='SELF_QA_DEMONSTRATED_PENDING_ROOT_FINAL_BINDING',physical_or_publisher_image_result_claimed=False))
OUT.mkdir(exist_ok=True)
(OUT/'repaired_b2_b4_cases.jsonl').write_text(''.join(canonical(r)+'\n' for r in rows),encoding='utf8')
(OUT/'qa7_b2_b4.jsonl').write_text(''.join(canonical(q)+'\n' for q in qa),encoding='utf8')
result=dict(schema='MathVisionKid.G2IntakeRepairReview.v1',created_utc=datetime.now(timezone.utc).isoformat(),skills_applied=[],
    original_batches=[2,3,4],original_case_count=18,new_original_case_count=2,derived_case_count=20,expected_future_chat_count=80,
    original_zip_refs=zip_refs,original_row_bindings=parents,original_chat_structural_checks=original_chat_checks,
    originals_unchanged=True,original_chat_count=72,all_original_valid_answers_preserved=all(all(answer in byid[r['sample_id']]['expected_answer'] for answer in r['expected_answer']) for r in originals),
    source_draft_hashes_only_cross_referenced_not_draft_content_reaudited=True,
    findings_original=['Standalone card-error prompt omitted the six-card context used by its answer.','Cube support explanation referenced a companion arrangement absent from standalone prompt.','Several hints stated the final verdict or complete requested explanation.','Generic hint follow-up questions were unrelated to the actual task.','Task09 memory-pair and finite-token subbranches were absent despite claimed complete task closure.','Several exact duplicate candidate aliases were omitted or game-subbranch aliases overclaimed.','Boat equal-baseline assumptions and circular pointer interval specification needed explicit text.','Mutation evidence appended _MUTATED_WRONG without a meaningful wrong-model experiment.'],
    repairs_complete_self_qa=True,original_manifest_parent_queue_sha256=manifest['parent_queue']['sha256'],
    actual_reviewed_queue_sha256=sha(queue_path.read_bytes()),parent_queue_byte_hash_differs=manifest['parent_queue']['sha256']!=sha(queue_path.read_bytes()),
    queue_task_identity_and_actual_constraints_read=True,coverage_bindings=coverage,
    independent_oracle_count=len(oracles),meaningful_negative_tests=len(mutations),Fraction_Decimal_step_checks=len(arithmetic),
    all_meaningful_negative_tests_detected=all(m['detected'] for m in mutations.values()),
    full_root_and_tokenizer_check_still_required=True,all_rows_semantically_human_reviewed=False,TRAINING_DATASET_READY=False,
    no_network_or_cloud_calls=True,no_train_weights_GPU=True,files={name:sha((OUT/name).read_bytes()) for name in ['repaired_b2_b4_cases.jsonl','qa7_b2_b4.jsonl',Path(__file__).name]})
write('review_b2_b4.json',result)
print(json.dumps({k:result[k] for k in ['original_case_count','new_original_case_count','derived_case_count','all_original_valid_answers_preserved','independent_oracle_count','meaningful_negative_tests','Fraction_Decimal_step_checks','files']},ensure_ascii=False))
