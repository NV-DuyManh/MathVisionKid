"""Original bounded comparison and approximate-count drafts, pending peer review."""
import copy,json
from fractions import Fraction as F
from primary_math_data_pipeline import (HERE,DEFAULT_ROOT,read_rows,write_rows,write_json,sha,row_sha,
    inspect_case,mapping_error,protections,answer_signatures,normalized,curate)


def main():
    path=DEFAULT_ROOT/'authored_batches/g2_compare_estimate_0010.jsonl'
    if path.exists():print('Batch exists; continue review instead of reauthoring.');return
    bp=DEFAULT_ROOT/'curriculum_blueprint.json';blueprint=json.loads(bp.read_text('utf-8'))
    nodes={n['node_id']:n for n in blueprint['nodes']}
    template=read_rows(DEFAULT_ROOT/'authored_batches/g1_geometry_0004.jsonl')[0];rows=[]
    def add(suffix,nodeid,slot,problem,givens,steps,answers,initial,hints,kind='core',student=None):
        r=copy.deepcopy(template);node=nodes[nodeid];sid='primary_20261017_g2_compare_estimate_0010_'+suffix
        r.update(sample_id=sid,case_group_id=sid,grade=2,topic=suffix,problem=problem,
            givens=[{'id':'g'+str(i),'text':t,'value':v,'unit':u,'role':role} for i,(t,v,u,role) in enumerate(givens)],
            requested_quantity='; '.join(q for q,v,u in answers) if answers else 'Dữ kiện đủ để ước lượng có cơ sở',
            student_work=student,initial_guidance=initial,
            hints=[{'level':i+1,'hint':h,'question':q} for i,(h,q) in enumerate(hints)],
            worked_steps=[{'step_id':'s'+str(i),'title':t,'reason':why,'expression':expr,'result':str(v),'unit':u,'explanation':ex}
                for i,(t,why,expr,v,u,ex) in enumerate(steps)],
            expected_answer=[{'quantity':q,'result':str(v),'unit':u} for q,v,u in answers],can_solve=bool(answers),
            canonical_case={'family':suffix,'operations':[s[2] for s in steps if s[2] and '{s' not in s[2]],
                'numeric_values':[str(v) for t,v,u,role in givens if v is not None]})
        r['curriculum_assignment']={'node_id':nodeid,'curriculum_scope':node['curriculum_scope'],'case_kind':kind}
        if kind=='core':
            info=next(s for s in node['authoring_plan']['core_cases'] if s['case_slot']==slot)
            r['curriculum_assignment'].update({k:info[k] for k in ('case_slot','context_variant','method_variant')})
        r['provenance'].update(authoring_label='AI_TEACHER',authoring_agent='root',
            source_evidence=node['source_evidence'],blueprint_sha256=sha(bp.read_bytes()),
            source_kind='ORIGINAL_EXPLICIT_HYPOTHETICAL_TEXT_DESCRIPTION' if answers else 'ORIGINAL_MISSING_INFORMATION_GUARD',
            student_work_origin='EXPLICITLY_SYNTHETIC' if student else None,
            content_review_status='PENDING_INDEPENDENT_CONTENT_REVIEW',visual_or_physical_outcome_verified=False)
        r['quality_flags']['approximate_and_exact_counts_must_remain_distinct']=nodeid=='current_g2_estimate_tens'
        rows.append(r)

    add('compare_digit_count_boundary','current_g2_compare_order_1000','core_01',
        'Hai thẻ số ghi 98 và 103. Thẻ nào ghi số lớn hơn? Giải thích bằng hàng trăm và kiểm rằng không chỉ so chữ số cuối.',
        [('Thẻ 98','98','','first_number'),('Thẻ 103','103','','second_number')],
        [('Xét hàng trăm','103 có một trăm, còn 98 chưa đủ một trăm.',None,'103 lớn hơn 98','',
          '103 có 1 trăm và 3 đơn vị. 98 không có trăm, nên 103 lớn hơn 98.'),
         ('Kiểm cách so','Chữ số cuối không quyết định cả số khi các hàng cao hơn khác nhau.',None,'thẻ 103','',
          'Dù 8 lớn hơn 3, không được chỉ dùng hai chữ số cuối để so cả số. Chọn thẻ 103; viết 98 < 103.')],
        [('Thẻ ghi số lớn hơn','thẻ 103','')],
        ['Xác định mỗi số có hàng cao nhất nào.','Đọc giá trị cả số thay vì chỉ nhìn chữ số cuối.'],
        [('Chú ý sự khác nhau ở mốc một trăm.','Mỗi số có bao nhiêu trăm?'),
         ('Nếu các hàng cao hơn khác nhau, hãy dùng giá trị hàng đó để quyết định trước.','So chữ số cuối riêng lẻ có xét đủ giá trị cả số không?'),
         ('Đối chiếu số em chọn với giá trị hàng trăm của cả hai thẻ rồi ghi quan hệ.','Lý do em dùng có phù hợp với các hàng của hai số không?')])

    add('compare_shared_hundreds_zero_tens','current_g2_compare_order_1000','core_02',
        'So sánh 430 và 403. Hai số dùng cùng ba chữ số nhưng vị trí khác nhau. Hãy xét hàng trăm, hàng chục và chỉ xét hàng đơn vị khi cần.',
        [('Số 430','430','','first_number'),('Số 403','403','','second_number')],
        [('Giữ hàng trăm bằng nhau','Cả hai có 4 trăm nên cần chuyển sang hàng chục.',None,'cùng 4 trăm','',
          '430 và 403 đều có 4 trăm. Chưa thể kết luận chỉ từ hàng trăm.'),
         ('So hàng chục trước hàng đơn vị','430 có 3 chục, 403 có 0 chục; hàng chục đã khác nên không để hàng đơn vị đảo kết luận.',None,'430 lớn hơn 403','',
          '3 chục nhiều hơn 0 chục nên 430 > 403. Không kết luận ngược chỉ vì 0 ở hàng đơn vị của 430 bé hơn 3 ở hàng đơn vị của 403.')],
        [('Quan hệ hai số','430 lớn hơn 403','')],
        ['Chữ số giống nhau chưa có nghĩa hai số có cùng giá trị.','So các hàng theo thứ tự từ cao xuống thấp.'],
        [('Bắt đầu với hàng cao nhất có mặt ở hai số.','Hai chữ số hàng trăm có bằng nhau không?'),
         ('Khi hàng trăm bằng nhau, chuyển sang hàng chục trước.','Hàng chục của hai số có còn bằng nhau không?'),
         ('Dừng ở hàng đầu tiên khác nhau và kiểm lại giá trị của hàng đó.','Em có để một hàng thấp hơn làm đảo kết luận từ hàng cao hơn không?')])

    add('sort_four_descending','current_g2_compare_order_1000','core_03',
        'Xếp bốn số 705, 750, 507, 570 từ lớn đến bé. Mỗi số dùng đúng một lần. Hãy kiểm từng cặp đứng cạnh nhau sau khi xếp.',
        [('705','705','','input_number'),('750','750','','input_number'),('507','507','','input_number'),('570','570','','input_number')],
        [('Chia theo hàng trăm','Nhóm có nhiều trăm hơn đứng trước trong thứ tự từ lớn đến bé.',None,'nhóm 7 trăm trước nhóm 5 trăm','',
          '705, 750 có 7 trăm; 507, 570 có 5 trăm. Hai số có 7 trăm đứng trước hai số có 5 trăm.'),
         ('Xếp trong mỗi nhóm và kiểm','Khi cùng hàng trăm, so hàng chục; giữ đúng chiều lớn đến bé.',None,'750, 705, 570, 507','',
          'Trong nhóm 7 trăm: 750 > 705. Trong nhóm 5 trăm: 570 > 507. Dãy là 750, 705, 570, 507. Kiểm thêm 705 > 570 và kiểm mỗi số xuất hiện một lần.')],
        [('Dãy từ lớn đến bé','750, 705, 570, 507','')],
        ['Đề yêu cầu chiều từ lớn đến bé, không phải chiều ngược lại.','Mỗi lần xét hàng trăm trước, rồi hàng chục hoặc đơn vị khi cần.'],
        [('Chia các số theo số trăm để giảm số cặp phải so.','Nhóm nào cần đứng trước theo chiều đề yêu cầu?'),
         ('Trong các số cùng hàng trăm, dùng hàng chục để xếp tiếp.','Em đã giữ cùng một chiều so trong từng nhóm chưa?'),
         ('Đọc các cặp liền nhau và kiểm đủ bốn số không lặp.','Có cặp nào đang đi ngược chiều lớn đến bé không?')])

    wrong='Dãy tăng dần của em là 271, 217, 127, 172.'
    add('misconception_wrong_sort_direction','current_g2_compare_order_1000',None,
        'Bài yêu cầu xếp 271, 217, 127, 172 từ bé đến lớn. Một bạn ghi giả định: '+wrong+' Hãy chỉ ra một cặp chưa đúng chiều rồi xếp lại đủ bốn số. Không đoán lý do bạn làm ngoài dòng đã ghi.',
        [('Các số cần xếp: 271, 217, 127, 172',None,'','four_given_numbers')],
        [('Kiểm một cặp trong dòng viết','Trong dãy tăng dần, số đứng trước phải bé hơn số đứng sau.',None,'cặp 271, 217 chưa đúng chiều','',
          '271 đứng trước 217 trong dòng bạn viết nhưng 271 lớn hơn 217, nên dãy chưa tăng dần. Điều này cho thấy thứ tự sai ở cặp đó, chưa cho biết bạn đã dùng quy tắc nào.'),
         ('Xếp lại theo các hàng rồi kiểm','So hàng trăm trước, cùng hàng trăm thì so hàng chục.',None,'127, 172, 217, 271','',
          'Các số có 1 trăm đứng trước các số có 2 trăm. Trong từng nhóm: 127 < 172 và 217 < 271. Dãy đúng là 127, 172, 217, 271; kiểm 172 < 217 và dùng đủ mỗi số một lần.')],
        [('Dãy từ bé đến lớn','127, 172, 217, 271','')],
        ['Đối chiếu chiều đề yêu cầu với từng cặp trong dòng bạn ghi.','Chỉ nhận xét thứ tự được cho, không suy cách bạn đã nghĩ.'],
        [('Muốn tăng dần, mỗi số đứng trước cần bé hơn số ngay sau.', 'Em có thể chọn một cặp liền nhau trong dòng đã viết để kiểm không?'),
         ('Phân các số theo hàng trăm trước khi xếp lại.', 'Nhóm hàng trăm nào cần đứng trước trong chiều bé đến lớn?'),
         ('Trong từng nhóm cùng hàng trăm, so tiếp hàng chục rồi kiểm đủ các số.', 'Dãy sửa của em có thỏa chiều yêu cầu ở mọi cặp liền nhau không?')],kind='misconception',
        student={'text':wrong,'observations':[{'excerpt':'271, 217','claim_scope':'This written adjacent pair descends although ascending order was requested; no unstated sorting strategy inferred.'}]})

    add('estimate_from_ten_reference','current_g2_estimate_tens','core_01',
        'Trong một tình huống giả định, người quan sát đếm đủ 10 hạt làm nhóm mẫu. So với nhóm đó, toàn bộ rổ được mô tả là khoảng bốn nhóm có lượng hạt tương tự; chưa đếm hết từng hạt trong rổ. Hãy nêu một ước lượng theo nhóm mười và nói rõ đó có phải số đếm chính xác không.',
        [('Nhóm mẫu đếm đủ 10 hạt','10','hạt/nhóm mẫu','reference_group'),('Cả rổ nhìn cỡ 4 nhóm tương tự','4','nhóm (ước lượng)','estimated_group_count')],
        [('Ước theo nhóm mẫu','Dùng bốn nhóm cỡ mười làm lượng đại diện, chưa biết số hạt chính xác.','10+10+10+10',40,'hạt (ước lượng)',
          'Bốn nhóm cỡ mười cho mức ước lượng khoảng 40 hạt.'),
         ('Giữ đúng độ chắc chắn','Nhóm tương tự được mô tả bằng khoảng, nên tổng là ước lượng chứ chưa phải đếm chính xác.',None,'chưa biết số đếm chính xác','',
          'Nói khoảng 40 hạt, không khẳng định chắc chắn đúng 40. Muốn biết chính xác, cần đếm tất cả hạt hoặc chia nhóm rồi đếm đủ cả phần thừa.')],
        [('Ước lượng số hạt',40,'hạt (ước lượng)'),('Kết luận về số đếm chính xác','chưa biết số đếm chính xác','')],
        ['Nhóm mẫu đã biết lượng; mô tả cả rổ chỉ cho số nhóm gần đúng.','Giữ từ khoảng khi trả lời theo cách ước lượng.'],
        [('Chọn nhóm đã đếm làm mốc thay vì đoán một số không có căn cứ.','Nhóm mẫu trong đề cho em mốc lượng nào?'),
         ('Gộp các nhóm cỡ mẫu theo số nhóm gần đúng được mô tả.','Số nhóm của cả rổ đã là số đếm chính xác chưa?'),
         ('Sau khi nêu ước lượng, phân biệt nó với kết quả cần đếm kiểm lại.','Muốn khẳng định một số chính xác, em cần thêm bước nào?')])

    add('estimate_spread_invariance','current_g2_estimate_tens','core_02',
        'Trong một tình huống giả định, một khay nút được ước lượng cỡ năm nhóm mười nút, chưa đếm chính xác. Sau đó chỉ dàn rộng chính các nút đó trên bàn, không thêm hay bớt nút nào. Có thể chỉ vì dàn rộng mà đổi ước lượng thành nhiều gấp mấy lần không? Nêu mức ước lượng có cơ sở ban đầu và giải thích điều giữ nguyên.',
        [('Ban đầu cỡ 5 nhóm 10 nút','5','nhóm (ước lượng)','estimated_groups'),('Mỗi nhóm mẫu 10 nút','10','nút/nhóm mẫu','reference_size'),
         ('Chỉ dàn rộng, không thêm/bớt nút',None,'','quantity_preserving_rearrangement')],
        [('Ghi mức ước lượng từ nhóm mẫu','Năm nhóm cỡ mười cho mức gần đúng từ mô tả ban đầu.','10+10+10+10+10',50,'nút (ước lượng)',
          'Mức ước lượng ban đầu là khoảng 50 nút.'),
         ('Kiểm tác động của cách xếp','Đổi khoảng cách giữa các nút không tự làm tăng số nút khi không thêm hay bớt.',None,'không tăng số nút chỉ vì dàn rộng','',
          'Không có căn cứ tăng ước lượng chỉ vì chỗ đặt rộng hơn. Có thể giữ mức khoảng 50 nút từ thông tin ban đầu; nếu muốn điều chỉnh có cơ sở, hãy đếm hoặc chia nhóm kiểm lại, không lấy độ rộng chỗ đặt làm số lượng.')],
        [('Mức ước lượng từ thông tin ban đầu',50,'nút (ước lượng)'),('Tác động của chỉ dàn rộng','không tăng số nút chỉ vì dàn rộng','')],
        ['Phân biệt diện tích chỗ đặt với số đồ vật được đặt.','Dùng dữ kiện không thêm hoặc bớt để kiểm suy luận.'],
        [('Theo dõi có đồ vật nào được thêm vào hoặc lấy đi không.','Đề mô tả thay đổi số nút hay chỉ thay cách xếp?'),
         ('Cách ước ban đầu dựa vào lượng của nhóm mẫu, không dựa riêng vào chỗ đặt rộng hay hẹp.', 'Muốn thay mức ước lượng có cơ sở, em cần bằng chứng gì?'),
         ('Đối chiếu lại nguồn của con số và giữ nhãn gần đúng nếu chưa đếm hết.', 'Cách giải thích của em có nhầm chỗ đặt rộng hơn với nhiều đồ vật hơn không?')])

    add('estimate_then_count_check','current_g2_estimate_tens','core_03',
        'Trong hoạt động giả định, Mai nhìn một hộp que và ước cỡ sáu nhóm mười que. Sau đó Mai đếm đầy đủ từng que, ghi được 58 que. Hãy ghi riêng số ước lượng ban đầu và số đếm kiểm lại, rồi tính chúng chênh nhau bao nhiêu. Không sửa lời ghi ước lượng cũ thành số đã đếm.',
        [('Ban đầu cỡ 6 nhóm 10 que','6','nhóm (ước lượng)','estimated_groups'),('Mẫu mười que','10','que/nhóm mẫu','reference_size'),
         ('Đếm kiểm đầy đủ được 58 que','58','que','provided_exact_count')],
        [('Ghi ước lượng theo nhóm mười','Thông tin trước khi đếm cho một số gần đúng từ sáu nhóm mẫu.','10+10+10+10+10+10',60,'que (ước lượng)',
          'Mai đã ước lượng khoảng 60 que. Giữ đây là số ước lượng ban đầu.'),
         ('Ghi riêng kết quả đếm đầy đủ','Kết quả đếm hết đã được đề cho, có vai trò khác với ước lượng.','58',58,'que',
          'Số đếm kiểm lại là 58 que. Không thay con số ước lượng đã ghi trước bằng 58 rồi gọi đó là ước lượng ban đầu.'),
         ('Đối chiếu độ chênh','So mức ước lượng với số đếm để biết ước lượng lệch bao nhiêu; đơn vị đều là que.','60-58',2,'que',
          '60 − 58 = 2 que. Mức ước lượng lớn hơn số đếm 2 que. Ghi hai mục riêng: ước khoảng 60, đếm được 58; dùng kết quả kiểm để rút kinh nghiệm ước lượng.')],
        [('Ước lượng ban đầu',60,'que (ước lượng)'),('Số đếm kiểm lại',58,'que'),('Độ chênh hai giá trị',2,'que')],
        ['Phân biệt thông tin trước khi đếm với kết quả sau khi đếm hết.','Không sửa lịch sử một ước lượng bằng cách thay nó bằng số vừa kiểm được.'],
        [('Gắn mỗi con số với cách nó được tìm ra.','Thông tin nào là ước lượng và thông tin nào là đếm đầy đủ?'),
         ('Gộp các nhóm cỡ mười để ghi lại mức gần đúng trước, giữ số đếm ở mục khác.', 'Em đã ghi hai loại kết quả thành hai mục riêng chưa?'),
         ('So hai giá trị cùng đơn vị để tìm độ chênh, rồi kiểm phép tính bằng cách gộp ngược.', 'Độ chênh em tìm cộng vào giá trị nhỏ hơn có trở lại giá trị lớn hơn không?')])

    wrong='Có khoảng ba nhóm mười hạt nên chắc chắn có đúng 30 hạt, không cần đếm lại.'
    add('misconception_approx_is_exact','current_g2_estimate_tens',None,
        'Chỉ biết trong mô tả giả định rằng một rổ có khoảng ba nhóm cỡ mười hạt; chưa ai đếm đầy đủ. Một bạn viết: '+wrong+' Hãy giữ phần ước lượng có cơ sở và sửa mức chắc chắn của kết luận.',
        [('Khoảng ba nhóm cỡ mười','3','nhóm (ước lượng)','estimated_groups'),('Nhóm mẫu mười hạt','10','hạt/nhóm mẫu','reference_size'),
         ('Chưa có số đếm đầy đủ',None,'','exact_count_not_available')],
        [('Nêu ước lượng được hỗ trợ','Ba nhóm cỡ mười là một cách tạo con số gần đúng.','10+10+10',30,'hạt (ước lượng)',
          'Có thể ước lượng khoảng 30 hạt.'),
         ('Sửa mức chắc chắn','Từ khoảng không cho phép kết luận chắc chắn đúng một số khi chưa đếm hết.',None,'chưa xác định số đếm chính xác','',
          'Phần chưa đúng là khẳng định chắc chắn đúng 30 và không cần kiểm. Lời sửa: ước khoảng 30 hạt; muốn biết số chính xác cần đếm đầy đủ, kể cả phần còn thừa ngoài các nhóm.')],
        [('Ước lượng có cơ sở',30,'hạt (ước lượng)'),('Mức chắc chắn','chưa xác định số đếm chính xác','')],
        ['Tách việc tính một lượng đại diện khỏi mức chắc chắn của kết luận.','Giữ đúng thông tin chưa có số đếm đầy đủ.'],
        [('Đề dùng từ diễn tả lượng gần đúng.', 'Từ nào trong mô tả cho biết lượng nhóm chưa được xác nhận chính xác?'),
         ('Một số đại diện hợp lý vẫn cần mang nhãn gần đúng khi dữ kiện là gần đúng.', 'Câu bạn viết có giữ đúng mức chắc chắn của dữ kiện không?'),
         ('Giữ phần ước có căn cứ và nêu cách kiểm nếu cần một số chính xác.', 'Em cần làm gì trước khi dùng từ chắc chắn cho số hạt?')],kind='misconception',
        student={'text':wrong,'observations':[{'excerpt':'chắc chắn có đúng 30 hạt, không cần đếm lại','claim_scope':'The explicitly written certainty is stronger than the supplied approximate grouping; the representative estimate itself is not rejected.'}]})

    add('guard_no_reference_or_view','current_g2_estimate_tens',None,
        'Em hỏi hãy ước lượng khay cúc áo của em có bao nhiêu chiếc theo nhóm mười. Chưa có ảnh, danh sách, nhóm mười làm mốc hoặc mô tả khay có cỡ bao nhiêu nhóm tương tự. Hãy giúp em bắt đầu mà không bịa một con số.',[],[],[],
        ['Chưa có dữ kiện về số cúc hoặc nhóm tham chiếu nên mình chưa nêu được một số ước lượng có cơ sở.','Em có thể đếm một nhóm mẫu mười chiếc rồi mô tả cả khay cỡ bao nhiêu nhóm tương tự, hoặc gửi ảnh rõ để cùng xem.'],
        [('Cần một nhóm có lượng đã biết làm mốc so sánh.', 'Em có thể chuẩn bị một nhóm mẫu đã đếm đủ để làm mốc không?'),
         ('Sau khi có mốc, cần thông tin về cả khay thay vì đoán từ tên đồ vật.', 'Cả khay trông cỡ bao nhiêu nhóm tương tự theo quan sát của em?'),
         ('Giữ từ khoảng khi chưa đếm đầy đủ, và có thể đếm lại để kiểm.', 'Em muốn có số gần đúng hay cần đếm chính xác từng chiếc?')],kind='guard')

    assert len(rows)==9
    protected,questions,_=protections();existing=[r for f in (DEFAULT_ROOT/'authored_batches').glob('*.jsonl') for r in read_rows(f)]
    existing_questions={normalized(r['problem']) for r in existing};checks=[]
    for r in rows:
        m=inspect_case(r);assert m['passed'],(r['sample_id'],m)
        assert mapping_error(r,nodes) is None
        assert not answer_signatures(r,m)&protected,r['sample_id']
        assert normalized(r['problem']) not in questions|existing_questions
        checks.append({'sample_id':r['sample_id'],'row_sha256':row_sha(r),'mechanical':m,'mapping_pass':True})
    assert 98<103 and divmod(430,100)[0]==divmod(403,100)[0] and 430>403
    assert sorted([705,750,507,570],reverse=True)==[750,705,570,507]
    assert sorted([271,217,127,172])==[127,172,217,271]
    assert sum([F(10)]*4)==40 and sum([F(10)]*5)==50 and sum([F(10)]*6)==60
    assert F(60)-F(58)==2 and sum([F(10)]*3)==30
    # Same estimated group scale can fit different actual counts; arithmetic
    # computes a representative estimate, never establishes its exact truth.
    ids=list(range(53));spread_ids=list(reversed(ids))
    initial_positions={i:(i%8,i//8) for i in ids}
    spread_positions={i:(3*(i%8),3*(i//8)) for i in spread_ids}
    same_ids=set(initial_positions)==set(spread_positions) and len(spread_positions)==53
    assert max(x for x,y in spread_positions.values())==3*max(x for x,y in initial_positions.values())
    approximation_countermodels={'about_three_tens_possible_counts':[29,31],
        'about_four_tens_possible_counts':[39,41],'spread_without_change':same_ids,
        'spread_witness_distinct_ids':53,'horizontal_span_scale':3}
    assert approximation_countermodels['spread_without_change']
    frozen={p:sha((HERE.parent/p).read_bytes())==h for p,h in blueprint['existing_inputs']['source_fingerprints'].items()};assert all(frozen.values())
    write_rows(path,rows)
    write_json(HERE/'evidence/primary_math_teacher_20261016/g2_compare_estimate_0010_pre_review.json',{
        'batch_sha256':sha(path.read_bytes()),'authored_cases':9,'core_cases':6,'misconception_cases':2,'guard_cases':1,
        'checks':checks,'frozen_inputs_unchanged':frozen,
        'independent_semantic_review_completed':False,
        'self_content_check':'Author checked every visible step/hint and preserved approximate versus exact roles. Independent semantic review remains pending.',
        'oracles':{'larger_boundary':103,'shared_hundreds_comparison':'430>403','descending':[750,705,570,507],
            'corrected_ascending':[127,172,217,271],'approximate_representatives':[40,50,60,30],
            'given_exact_count':58,'estimate_minus_exact':2,'approximation_countermodels':approximation_countermodels},
        'limits':'Countermodels are compatible witnesses, not statistical confidence intervals or exhaustive meaning of about. No real image/physical performance verified.',
        'human_verified':False,'teacher_certified':False,'training_started':False,'sealed_concept_challenge_read':False})
    state=curate(DEFAULT_ROOT)
    assert state['authored_cases']==113 and state['accepted_cases']==88
    assert state['decisions']=={'PENDING_AI_CONTENT_REVIEW':25,'ACCEPTED_AI_RESEARCH':88}
    print(json.dumps({k:state[k] for k in ('authored_cases','accepted_cases','chat_train_rows','remaining_core_cases','decisions')}))


if __name__=='__main__':main()
