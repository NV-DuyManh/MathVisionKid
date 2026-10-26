"""Prepare eight cases, explicitly pending an independent content reviewer."""
import copy,json
from fractions import Fraction
from primary_math_data_pipeline import (HERE,DEFAULT_ROOT,read_rows,write_rows,write_json,sha,row_sha,
    inspect_case,mapping_error,protections,answer_signatures,normalized,curate)


def main():
    path=DEFAULT_ROOT/'authored_batches/g1_activities_0008.jsonl'
    if path.exists():print('Batch exists; resume independent review, not authoring.');return
    bp=DEFAULT_ROOT/'curriculum_blueprint.json';blueprint=json.loads(bp.read_text('utf-8'))
    nodes={n['node_id']:n for n in blueprint['nodes']}
    template=read_rows(DEFAULT_ROOT/'authored_batches/g1_geometry_0004.jsonl')[0]
    rows=[]
    def add(suffix,nodeid,slot,problem,givens,steps,answers,initial,hints,kind='core',student=None):
        r=copy.deepcopy(template);node=nodes[nodeid];sid='primary_20261017_g1_activities_0008_'+suffix
        r.update(sample_id=sid,case_group_id=sid,topic=suffix,problem=problem,
            givens=[{'id':'g'+str(i),'text':t,'value':v,'unit':u,'role':role} for i,(t,v,u,role) in enumerate(givens)],
            requested_quantity='; '.join(q for q,v,u in answers) if answers else 'Dữ kiện cần để kiểm kết quả trò chơi',
            student_work=student,initial_guidance=initial,
            hints=[{'level':i+1,'hint':h,'question':q} for i,(h,q) in enumerate(hints)],
            worked_steps=[{'step_id':'s'+str(i),'title':t,'reason':why,'expression':expr,'result':str(v),'unit':u,'explanation':ex}
                for i,(t,why,expr,v,u,ex) in enumerate(steps)],
            expected_answer=[{'quantity':q,'result':str(v),'unit':u} for q,v,u in answers],can_solve=bool(answers),
            canonical_case={'family':suffix,'operations':[s[2] for s in steps if s[2] and '{s' not in s[2]],
                'numeric_values':[str(v) for t,v,u,role in givens if v is not None]})
        r['curriculum_assignment']={'node_id':nodeid,'curriculum_scope':node['curriculum_scope'],'case_kind':kind}
        if kind=='core':
            slotinfo=next(s for s in node['authoring_plan']['core_cases'] if s['case_slot']==slot)
            r['curriculum_assignment'].update({k:slotinfo[k] for k in ('case_slot','context_variant','method_variant')})
        r['provenance'].update(authoring_label='AI_TEACHER',authoring_agent='root',
            source_evidence=node['source_evidence'],blueprint_sha256=sha(bp.read_bytes()),
            source_kind='ORIGINAL_EXPLICIT_HYPOTHETICAL_TEXT_DESCRIPTION' if answers else 'ORIGINAL_MISSING_INFORMATION_GUARD',
            student_work_origin='EXPLICITLY_SYNTHETIC' if student else None,
            content_review_status='PENDING_INDEPENDENT_CONTENT_REVIEW',visual_or_physical_outcome_verified=False)
        rows.append(r)

    add('count_game_cards','current_g1_practice_experience','core_01',
        'Trong một trò chơi giả định, lớp chuẩn bị 12 thẻ xanh và 5 thẻ vàng. Hai nhóm thẻ tách rời, mỗi thẻ được tính một lần. Muốn bỏ tất cả vào một hộp, cần đếm có bao nhiêu thẻ? Giải thích rồi nêu cách kiểm bằng việc tách lại hai nhóm.',
        [('12 thẻ xanh','12','thẻ','first_group'),('5 thẻ vàng','5','thẻ','second_disjoint_group')],
        [('Gộp hai nhóm để đếm cả hộp','Câu hỏi cần toàn bộ hai nhóm không trùng nhau nên dùng phép cộng.','12+5',17,'thẻ',
          'Giữ 12 rồi đếm tiếp năm thẻ: 13, 14, 15, 16, 17. Có tất cả 17 thẻ.'),
         ('Tách nhóm để kiểm','Bỏ nhóm vàng ra khỏi toàn bộ phải còn đúng nhóm xanh.','{s0}-5',12,'thẻ',
          '17 − 5 = 12, khớp số thẻ xanh. Đếm đủ mỗi thẻ một lần rồi mới bỏ vào hộp; kết quả trong tình huống là 17 thẻ.')],
        [('Tổng số thẻ',17,'thẻ')],
        ['Phân biệt số thẻ của từng nhóm với số thẻ của cả hộp.','Hai nhóm tách rời nên không có thẻ cần đếm hai lần.'],
        [('Xác định trò chơi đang hỏi một nhóm hay toàn bộ các nhóm.','Câu hỏi yêu cầu đếm những thẻ nào?'),
         ('Có thể giữ số của nhóm đầu rồi đếm tiếp đúng số thẻ của nhóm còn lại.','Em làm thế nào để không bỏ hoặc đếm lặp thẻ?'),
         ('Khi có tổng, thử tách lại một nhóm để kiểm nhóm còn lại.','Kết quả kiểm cần khớp với dữ kiện nào của đề?')])

    add('check_position_game','current_g1_practice_experience','core_02',
        'Trò chơi giả định yêu cầu: cốc ở bên trái sách, hộp bút ở bên phải sách, xét theo trang từ trái sang phải. Cách xếp được mô tả từ trái sang phải là sách, hộp bút, cốc. Cách xếp đã đúng cả hai yêu cầu chưa? Chỉ chuyển cốc, hãy nêu thứ tự đúng cuối cùng.',
        [('Yêu cầu: cốc trái sách; hộp bút phải sách.',None,'','target_relations'),
         ('Thứ tự hiện tại trái sang phải: sách, hộp bút, cốc.',None,'','explicit_arrangement')],
        [('Kiểm từng yêu cầu theo cùng mốc','Sách là mốc cho cả hai quan hệ nên phải giữ mốc khi đối chiếu.',None,'chưa đúng cả hai yêu cầu','',
          'Hộp bút đang bên phải sách, đúng yêu cầu của nó. Cốc cũng đang bên phải sách, chưa đúng yêu cầu cốc bên trái sách.'),
         ('Sửa bằng đúng thao tác được phép','Giữ sách và hộp bút, chuyển cốc để thỏa điều kiện của cốc.',None,'cốc, sách, hộp bút','',
          'Chuyển cốc sang bên trái sách. Từ trái sang phải là cốc, sách, hộp bút. Kiểm lại: cốc trái sách, hộp bút phải sách, chỉ cốc đổi chỗ.')],
        [('Kết luận về cách xếp ban đầu','chưa đúng cả hai yêu cầu',''),('Thứ tự sau khi chỉ chuyển cốc','cốc, sách, hộp bút','')],
        ['Dùng sách làm mốc và kiểm từng yêu cầu riêng.','Đề chỉ cho chuyển một đồ vật, không tự đổi chiều nhìn.'],
        [('So từng yêu cầu với thứ tự hiện tại đã cho bằng lời.','Đồ vật nào được dùng làm mốc cho cả hai yêu cầu?'),
         ('Giữ nguyên phần đã đúng, tập trung vào quan hệ chưa phù hợp.','Em đã kiểm riêng vị trí từng đồ vật so với mốc chưa?'),
         ('Thử một cách chuyển đúng đồ vật được phép rồi đọc lại cả hai quan hệ.','Cách thử của em có vừa thỏa yêu cầu vừa giữ đúng giới hạn thao tác không?')])

    add('calendar_clock_activity','current_g1_practice_experience','core_03',
        'Trong lịch hoạt động giả định: Thứ Năm lúc 8 giờ sáng tô hình; Thứ Sáu lúc 8 giờ sáng đo cạnh bàn. Hôm nay trong câu chuyện là Thứ Sáu, buổi sáng; đồng hồ có kim phút dài chỉ 12 và kim giờ ngắn chỉ 8. Theo lịch, hoạt động nào đến lúc bắt đầu? Hãy đối chiếu đủ ngày và giờ.',
        [('Thứ Năm 8 giờ sáng: tô hình.',None,'','first_schedule_entry'),
         ('Thứ Sáu 8 giờ sáng: đo cạnh bàn.',None,'','second_schedule_entry'),
         ('Hôm nay Thứ Sáu buổi sáng; kim phút 12, kim giờ 8.',None,'','supplied_day_and_clock')],
        [('Đọc giờ theo vai trò hai kim','Kim phút ở 12 cho biết giờ đúng, còn số giờ đọc bằng kim giờ.',None,'8 giờ sáng','',
          'Kim giờ chỉ 8 nên là 8 giờ sáng theo buổi đã cho trong câu chuyện.'),
         ('Đối chiếu đồng thời ngày và giờ','Một hoạt động chỉ phù hợp khi cả thứ và giờ trong lịch đều khớp.',None,'đo cạnh bàn','',
          'Hôm nay là Thứ Sáu và đồng hồ chỉ 8 giờ sáng, khớp mục đo cạnh bàn. Mục tô hình cùng giờ nhưng thuộc Thứ Năm nên không chọn. Kiểm đủ cả hai dữ kiện, không chỉ xem giờ.')],
        [('Hoạt động theo lịch đã đến giờ','đo cạnh bàn','')],
        ['Lịch có hai mục cùng giờ nhưng khác ngày.','Dùng ngày trong câu chuyện và giờ từ hai kim, không lấy ngày thật của máy.'],
        [('Đọc thông tin hôm nay trong câu chuyện trước khi so lịch.','Các mục trong lịch khác nhau ở thông tin nào?'),
         ('Kiểm vai trò hai kim rồi ghép giờ đọc với buổi được cho.','Em đã xác định giờ bằng kim nào?'),
         ('Chỉ giữ mục khớp cả ngày lẫn giờ và đối chiếu lại mục còn lại.','Nếu chỉ kiểm giờ mà bỏ qua ngày, lựa chọn có đủ căn cứ không?')])

    wrong='12 + 4 + 4 = 20 thẻ, vì có nhóm 12 thẻ và nhóm 4 thẻ.'
    add('misconception_duplicate_group','current_g1_practice_experience',None,
        'Một hoạt động giả định có hai nhóm thẻ tách rời: nhóm A có 12 thẻ, nhóm B có 4 thẻ. Một bạn ghi: '+wrong+' Hãy nhận xét dòng đã ghi và sửa tổng sao cho mỗi nhóm chỉ được tính một lần.',
        [('Nhóm A có 12 thẻ','12','thẻ','first_group'),('Nhóm B có 4 thẻ','4','thẻ','second_disjoint_group')],
        [('Đối chiếu mỗi số hạng với nhóm được cho','Chỉ có hai nhóm nhưng dòng viết dùng số thẻ nhóm B hai lần.',None,'nhóm B bị tính hai lần','',
          'Trong dòng 12 + 4 + 4, số 12 ứng với nhóm A, còn hai số 4 cùng lặp lượng của nhóm B. Không có nhóm thứ ba trong đề.'),
         ('Gộp mỗi nhóm đúng một lần','Đếm toàn bộ không trùng phải dùng lượng của A và B mỗi lượng một lần.','12+4',16,'thẻ',
          '12 + 4 = 16 thẻ. Có thể kiểm bằng cách ghép danh sách thẻ A với B, đánh dấu thẻ đã tính; không cộng nhóm B thêm lần nữa.')],
        [('Tổng số thẻ không đếm lặp',16,'thẻ')],
        ['Ghép từng số trong dòng tính với một nhóm thực sự có trong đề.','Không suy thêm nhóm ngoài mô tả đã cho.'],
        [('Mỗi nhóm cần có đúng một lần xuất hiện trong phép gộp.', 'Đề thực sự cho những nhóm thẻ nào?'),
         ('Đối chiếu từng số hạng với nhóm tương ứng để tìm phần lặp.','Có số hạng nào đang cùng chỉ lại một nhóm không?'),
         ('Viết lại phép gộp sau khi giữ mỗi nhóm một lần rồi kiểm danh sách thẻ.','Em đã dùng đủ mọi nhóm mà không lặp nhóm nào chưa?')],kind='misconception',
        student={'text':wrong,'observations':[{'excerpt':'12 + 4 + 4','claim_scope':'The given expression counts the sole four-card group twice; no third group is provided.'}]})

    add('guard_unseen_card_game','current_g1_practice_experience',None,
        'Em nói đã xếp xong các thẻ số trong trò chơi rồi hỏi có đúng không. Chưa cho biết có những thẻ nào, luật yêu cầu tăng dần hay giảm dần và dãy em đã xếp; cũng chưa có ảnh. Hãy hỏi thông tin đủ để kiểm, chưa nhận xét đúng sai.',[],[],[],
        ['Mình cần biết bộ thẻ, chiều xếp yêu cầu và dãy em đã xếp để đối chiếu.','Em gửi luật chơi cùng ảnh rõ dãy thẻ, hoặc chép các thông tin đó bằng lời.'],
        [('Muốn kiểm kết quả cần biết luật yêu cầu cách xếp nào.','Trò chơi yêu cầu xếp tăng dần hay giảm dần?'),
         ('Cần biết cả bộ thẻ ban đầu để kiểm có bỏ hoặc lặp thẻ không.','Em được cho những thẻ số nào?'),
         ('Sau khi biết luật và bộ thẻ, đối chiếu với kết quả thực tế em đã làm.','Em có thể chép dãy đã xếp hoặc gửi ảnh rõ dãy đó không?')],kind='guard')

    wrong='Ba chục và hai đơn vị viết là 23.'
    add('misconception_tens_units_reversed','current_g1_natural_numbers_100',None,
        'Giả sử có ba bó que, mỗi bó mười que, và hai que rời: đó là ba chục và hai đơn vị. Một bạn viết: '+wrong+' Hãy nhận xét rồi viết đúng số que, giải thích hàng chục và hàng đơn vị.',
        [('Ba bó mười que','3','chục que','tens'),('Hai que rời','2','que','ones'),('Mỗi bó mười que','10','que/bó','bundle_size')],
        [('Gắn chữ số với đúng hàng','Số chục phải ở hàng chục, số que rời ở hàng đơn vị.',None,'hàng chục 3, hàng đơn vị 2','',
          '23 có 2 chục và 3 đơn vị, chưa khớp ba chục và hai đơn vị được cho. Cần viết 3 ở hàng chục và 2 ở hàng đơn vị.'),
         ('Gộp để kiểm số que','Ba bó mỗi bó mười que cùng hai que rời tạo số lượng đã mô tả.','10+10+10+2',32,'que',
          '10 + 10 + 10 + 2 = 32 que. Viết 32, đọc ba mươi hai; kiểm lại 3 chục và 2 đơn vị.')],
        [('Số que viết đúng',32,'que')],
        ['Đối chiếu từng chữ số trong lời viết với số chục và số đơn vị của đề.','Hai hàng có vai trò khác nhau dù cùng dùng những chữ số ấy.'],
        [('Một bó mười que được gọi là một chục.','Đề có mấy chục và mấy đơn vị rời?'),
         ('Chữ số ở hàng chục cần biểu thị số bó chục, không phải số que rời.','Chữ số hàng chục trong lời bạn viết có khớp dữ kiện không?'),
         ('Sau khi đặt các chữ số, đọc lại số chục và đơn vị để kiểm.','Em có thể tách số mình vừa viết thành đúng các bó và que rời của đề không?')],kind='misconception',
        student={'text':wrong,'observations':[{'excerpt':'23','claim_scope':'Written numeral has two tens and three ones, contrary to the explicit three tens and two ones.'}]})

    wrong='58 lớn hơn 64 vì 8 lớn hơn 4.'
    add('misconception_compare_ones_only','current_g1_compare_order_100',None,
        'Một bạn có câu giải thích giả định: '+wrong+' Hãy nhận xét lý do đã viết và so sánh lại hai số bằng hàng chục rồi hàng đơn vị khi cần.',
        [('Số thứ nhất là 58','58','','first_number'),('Số thứ hai là 64','64','','second_number')],
        [('Xét hàng chục trước','Nếu số chục khác nhau thì số có nhiều chục hơn lớn hơn, dù chữ số đơn vị có thể nhỏ hơn.',None,'58 bé hơn 64','',
          '58 có 5 chục, 64 có 6 chục. Vì 5 chục ít hơn 6 chục nên 58 bé hơn 64.'),
         ('Giải thích chỗ chưa đúng trong lời viết','8 lớn hơn 4 chỉ so hai chữ số hàng đơn vị, không đủ quyết định khi hàng chục khác nhau.',None,'không dùng riêng hàng đơn vị để kết luận','',
          'Câu 8 lớn hơn 4 đúng khi xét hai chữ số ấy, nhưng bỏ qua hàng chục nên dẫn tới kết luận sai về cả số. Viết 58 < 64; không cần xét tiếp hàng đơn vị khi số chục đã khác.')],
        [('Quan hệ đúng của hai số','58 bé hơn 64','')],
        ['Phân biệt việc so hai chữ số với việc so cả hai số có hai hàng.','Chỉ góp ý dựa trên lý do bạn thực sự đã viết.'],
        [('Bắt đầu bằng hàng có giá trị lớn hơn trong mỗi số.','Khi so hai số hai chữ số, em cần xét hàng nào trước?'),
         ('Hàng đơn vị chỉ dùng tiếp khi số chục bằng nhau.','Hai số ở đây có cùng số chục không?'),
         ('Kiểm kết luận theo số chục của cả hai số thay vì chỉ hai chữ số đơn vị.','Lý do em dùng đã tính đến giá trị các hàng chưa?')],kind='misconception',
        student={'text':wrong,'observations':[{'excerpt':'vì 8 lớn hơn 4','claim_scope':'The explicitly written comparison uses only ones despite different tens; no unobserved strategy inferred.'}]})

    wrong='60 que bớt 20 que còn 4 que vì 6 trừ 2 bằng 4.'
    add('misconception_tens_unit_dropped','current_g1_mental_add_sub',None,
        'Trong tình huống giả định, mỗi chục gồm mười que. Một bạn nhẩm rồi viết: '+wrong+' Hãy giữ phần nhẩm đúng, sửa đơn vị trung gian và kết luận số que còn lại.',
        [('Có 60 que','60','que','initial_count'),('Bớt 20 que','20','que','removed_count'),('Mỗi chục mười que','10','que/chục','tens_size')],
        [('Nhẩm theo cùng đơn vị chục','60 que là 6 chục que, 20 que là 2 chục que, nên phần nhẩm cho số chục còn lại.','6-2',4,'chục que',
          '6 chục bớt 2 chục còn 4 chục. Phép nhẩm 6 − 2 = 4 đúng, nhưng 4 đang tính bằng chục que, chưa phải 4 que.'),
         ('Đọc lại cùng lượng bằng đơn vị que','Mỗi chục có mười que; cần nêu đủ lượng que trong bốn chục.','10+10+10+10',40,'que',
          'Bốn chục là 10 + 10 + 10 + 10 = 40 que. Kết luận còn 40 que; sửa tên đơn vị trung gian chứ không bỏ phần nhẩm đúng.'),
         ('Kiểm bằng phép cộng ngược','Phần còn lại cộng phần đã bớt phải khôi phục lượng đầu.','{s1}+20',60,'que',
          '40 + 20 = 60 que, đúng số que ban đầu.')],
        [('Số que còn lại',40,'que')],
        ['Đọc kỹ đơn vị mà mỗi số trong phép nhẩm đang biểu thị.','Có thể nhẩm bằng chục, nhưng khi trả lời số que cần đổi cách đọc cho đúng lượng.'],
        [('Phép nhẩm bỏ qua các chữ số không nhưng vẫn phải giữ ý nghĩa đơn vị.','Số trong phép nhẩm đang đếm từng que hay từng chục que?'),
         ('Kết quả nhẩm cần giữ cùng loại đơn vị với các lượng đã nhẩm.','Trong lời viết, tên đơn vị ở phần kết luận có khớp đơn vị nhẩm không?'),
         ('Đọc lượng sau nhẩm theo đơn vị que, rồi dùng phép cộng ngược để kiểm.','Phần còn lại của em cộng phần đã bớt có trở lại số que ban đầu không?')],kind='misconception',
        student={'text':wrong,'observations':[{'excerpt':'còn 4 que vì 6 trừ 2 bằng 4','claim_scope':'The written intermediate count of tens was mislabeled as single sticks; arithmetic6−2 itself is correct.'}]})

    assert len(rows)==8
    protected,questions,_=protections();existing=read_rows(DEFAULT_ROOT/'exports/accepted_teacher_cases.jsonl')
    existing_questions={normalized(r['problem']) for r in existing}
    checks=[]
    for r in rows:
        m=inspect_case(r);assert m['passed'],(r['sample_id'],m)
        assert mapping_error(r,nodes) is None
        assert not answer_signatures(r,m)&protected,r['sample_id']
        assert normalized(r['problem']) not in questions|existing_questions
        checks.append({'sample_id':r['sample_id'],'row_sha256':row_sha(r),'mechanical':m,'mapping_pass':True})
    assert len(['blue']*12+['yellow']*5)==17
    assert sorted(['A'+str(i) for i in range(12)]+['B'+str(i) for i in range(4)])==sorted(set(['A'+str(i) for i in range(12)]+['B'+str(i) for i in range(4)]))
    assert len(['A']*12+['B']*4)==16
    assert len([None for _ in range(3) for _ in range(10)]+[None]*2)==32
    assert 58<64 and divmod(58,10)[0]<divmod(64,10)[0]
    assert Fraction(60)-Fraction(20)==40 and 6-2==4
    frozen={p:sha((HERE.parent/p).read_bytes())==h for p,h in blueprint['existing_inputs']['source_fingerprints'].items()}
    assert all(frozen.values())
    write_rows(path,rows)
    write_json(HERE/'evidence/primary_math_teacher_20261016/g1_activities_0008_pre_review.json',{
        'batch_sha256':sha(path.read_bytes()),'authored_cases':8,'core_cases':3,'misconception_cases':4,'guard_cases':1,
        'checks':checks,'frozen_inputs_unchanged':frozen,
        'self_content_check':'Author read all visible solutions and hints; needs independent semantic reviewer before acceptance.',
        'independent_semantic_review_completed':False,'arithmetic_oracle_is_semantic_proof':False,
        'oracles':{'card_total':17,'position_target_order':['cốc','sách','hộp bút'],
            'calendar_clock_joint_match':'Thứ Sáu,8giờsáng→đo cạnh bàn',
            'distinct_group_cards':16,'three_tens_two_ones':32,'compare':'58<64','tens_subtract_sticks':40},
        'human_verified':False,'teacher_certified':False,'training_started':False,'sealed_concept_challenge_read':False})
    state=curate(DEFAULT_ROOT)
    assert state['accepted_cases']==88 and state['authored_cases']==96
    assert state['decisions']=={'ACCEPTED_AI_RESEARCH':88,'PENDING_AI_CONTENT_REVIEW':8}
    print(json.dumps({k:state[k] for k in ('authored_cases','accepted_cases','chat_train_rows','remaining_core_cases','decisions')}))


if __name__=='__main__':main()
