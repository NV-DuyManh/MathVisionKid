"""Author a bounded batch, leaving semantic review to a separate recorded pass."""
import json
from primary_math_data_pipeline import DEFAULT_ROOT, HERE, sha, write_rows, write_json, inspect_case, mapping_error, answer_signatures, protections, normalized
from author_primary_g1_foundations_0002 import teaching_step as step
import teacher_math_data_v4 as v4


def main():
    path=DEFAULT_ROOT/'authored_batches/g1_operations_0003.jsonl'
    if path.exists():
        print('Batch already exists; inspect/review it instead of reauthoring.'); return
    bp=DEFAULT_ROOT/'curriculum_blueprint.json'
    nodes={n['node_id']:n for n in json.loads(bp.read_text('utf-8'))['nodes']}
    rows=[]
    def add(suffix,nodeid,slot,problem,values,unit,steps,answer,initial,hints,operations,student=None,kind='core'):
        node=nodes[nodeid]; ident='primary_20261016_g1_operations_0003_'+suffix
        assignment={'node_id':nodeid,'curriculum_scope':node['curriculum_scope'],'case_kind':kind}
        if kind=='core':
            s=next(s for s in node['authoring_plan']['core_cases'] if s['case_slot']==slot)
            assignment.update({k:s[k] for k in ('case_slot','context_variant','method_variant')})
        for i,s in enumerate(steps):s['step_id']='s'+str(i)
        rows.append({'sample_id':ident,'split':'train','case_group_id':ident,'grade':1,'topic':suffix,
            'problem':problem,'givens':[{'id':'g'+str(i),'text':t,'value':str(v),'unit':unit,'role':role} for i,(t,v,role) in enumerate(values)],
            'requested_quantity':'Số lượng hoặc kết quả được hỏi trong đề', 'student_work':student,
            'initial_guidance':initial,'hints':[{'level':i+1,'hint':h,'question':q} for i,(h,q) in enumerate(hints)],
            'worked_steps':steps,'expected_answer':[] if answer is None else [{'quantity':'Kết quả cần tìm','result':str(answer),'unit':unit}],
            'can_solve':answer is not None,'canonical_case':{'family':suffix,'operations':operations,'numeric_values':[str(v) for _,v,_ in values]},
            'curriculum_assignment':assignment,
            'provenance':{'authoring_method':'original_AI_teacher','human_verified':False,'teacher_certified':False,
                'source_kind':'original_explicit_text_teacher_case' if kind!='guard' else 'original_missing_asset_teacher_case',
                'source_evidence':node['source_evidence'],'blueprint_sha256':sha(bp.read_bytes()),
                'benchmark_status':'TRAINING_ONLY_NOT_GOLD','real_observation_claim':False,
                'student_work_origin':'EXPLICITLY_SYNTHETIC' if student else None},
            'quality_flags':{'app_plan_draft_compatible':False,'app_mapping_status':'NEUTRAL_TEACHER_SCHEMA_REQUIRES_ADAPTER',
                'full_worked_solution_requires_explicit_request':True,'three_hint_levels_answer_free':True}})

    add('choose_subtract','current_g1_addition_subtraction_no_carry','core_03',
        'Hộp có 46 bút chì. Cô lấy 12 bút trong hộp phát cho các bạn. Hỏi trong hộp còn bao nhiêu bút chì? Giải thích vì sao chọn phép tính và kiểm lại.',
        [('có 46 bút',46,'initial_count'),('lấy ra 12 bút',12,'removed_count')],'bút',
        [step('Chọn phép trừ và tính theo hàng','Lấy bút ra làm số bút trong hộp giảm; bớt phần đã lấy khỏi số ban đầu.',
              '46-12',34,'bút','Hàng đơn vị: 6 trừ 2 bằng 4. Hàng chục: 4 trừ 1 bằng 3. Còn 34 bút; không cần mượn.'),
         step('Kiểm tra bằng cách gộp lại','Phần còn lại và phần lấy ra phải khôi phục đủ số bút ban đầu.',
              '{s0}+12',46,'bút','34 + 12 = 46, đúng số bút lúc đầu. Vậy trong hộp còn 34 bút chì.')],34,
        ['Xác định số bút ban đầu và số bút đã ra khỏi hộp.','Câu hỏi cần số bút còn trong hộp, không phải số đã phát.'],
        [('Theo dõi lượng bút trong hộp sau khi cô lấy bút ra.','Lượng bút trong hộp tăng hay giảm?'),
         ('Dùng số ban đầu và số đã lấy để viết phép tính phù hợp.','Số đã lấy đóng vai trò gì trong phép tính của em?'),
         ('Tính hàng đơn vị rồi hàng chục; kiểm bằng cách gộp phần còn với phần lấy ra.','Khi gộp lại, em phải thu được đại lượng nào của đề?')],['46-12'])

    add('left_add_add','current_g1_left_to_right_add_sub','core_01',
        'Tính 12 + 3 + 4 theo thứ tự từ trái sang phải. Nêu số nhận được sau mỗi lần cộng.',
        [('số đầu 12',12,'start'),('cộng 3',3,'first_change'),('cộng 4',4,'second_change')],'',
        [step('Cộng hai số ở bên trái trước','Với hai dấu cộng, bắt đầu từ số bên trái và cộng lượng ngay sau nó.',
              '12+3',15,'','12 + 3 = 15. Đây là kết quả sau lần cộng đầu, vẫn còn cộng thêm 4.'),
         step('Dùng kết quả vừa có để cộng tiếp','Kết quả lần đầu thay cho phần đã tính; giữ lại dấu cộng và số chưa dùng.',
              '{s0}+4',19,'','15 + 4 = 19. Vậy 12 + 3 + 4 = 19; đã cộng cả 3 và 4, mỗi số một lần.')],19,
        ['Có hai dấu cộng nên cần hai lần tính.','Bắt đầu với hai số bên trái rồi dùng kết quả vừa có để tính tiếp.'],
        [('Đi theo biểu thức từ bên trái sang bên phải.','Hai số nào em sẽ dùng trong lần tính đầu?'),
         ('Sau lần cộng đầu, giữ kết quả vừa tìm thay cho phần đã tính.','Trong biểu thức còn số nào chưa được cộng?'),
         ('Thực hiện lần cộng còn lại, rồi kiểm mỗi số cộng thêm đã được dùng một lần.','Em đã giữ đủ cả hai lần cộng chưa?')],['12+3+4'])

    add('left_subtract_add','current_g1_left_to_right_add_sub','core_02',
        'Tính 18 − 5 + 2 từ trái sang phải. Giải thích vì sao sau khi bớt 5 lại phải thêm 2.',
        [('bắt đầu 18',18,'start'),('bớt 5',5,'first_change'),('thêm 2',2,'second_change')],'',
        [step('Làm phép trừ ở bên trái','Dấu trừ đứng trước nên bớt 5 khỏi 18 trước.',
              '18-5',13,'','18 − 5 = 13. Đây là lượng sau khi bớt; chưa làm phép cộng.'),
         step('Thêm theo dấu cộng còn lại','Dấu trước 2 là dấu cộng nên phải tăng kết quả vừa có, không bớt tiếp.',
              '{s0}+2',15,'','13 + 2 = 15. Kết quả là 15. Cộng 5 và 2 rồi trừ cả hai sẽ đổi ý nghĩa của dấu cộng trong đề.')],15,
        ['Đọc lần lượt dấu trừ và dấu cộng theo thứ tự xuất hiện.','Không gộp các số rồi đổi dấu phép tính.'],
        [('Bắt đầu bằng phép tính bên trái.','Phép tính nào cần làm trước?'),
         ('Khi đã trừ xong, dùng kết quả đó cho bước tiếp theo.','Dấu ngay trước số cuối yêu cầu thêm hay bớt?'),
         ('Đối chiếu từng lần thay đổi với dấu đã cho.','Bước thứ hai của em có làm số vừa tìm tăng lên không?')],['18-5+2'])

    add('left_add_subtract','current_g1_left_to_right_add_sub','core_03',
        'Một khay có 31 hạt. Đặt thêm 7 hạt rồi lấy ra 5 hạt. Tính theo biểu thức 31 + 7 − 5 và kiểm tra từng lượng trung gian.',
        [('có 31 hạt',31,'start'),('thêm 7 hạt',7,'first_change'),('lấy ra 5 hạt',5,'second_change')],'hạt',
        [step('Tính lượng sau khi thêm','Thêm vào trước nên cộng vào số hạt ban đầu.',
              '31+7',38,'hạt','31 + 7 = 38. Sau lần thêm có 38 hạt.'),
         step('Tính lượng sau khi lấy ra','Lấy ra từ lượng đang có sau lần thêm, không lấy riêng từ phần thêm.',
              '{s0}-5',33,'hạt','38 − 5 = 33. Khay còn 33 hạt.'),
         step('Khôi phục lượng trước lần lấy ra','Đặt lại số hạt vừa lấy phải trở về lượng sau lần thêm.',
              '{s1}+5',38,'hạt','33 + 5 = 38, đúng lượng trung gian.'),
         step('Khôi phục lượng ban đầu','Bỏ phần đã thêm khỏi lượng trung gian phải trở lại lúc đầu.',
              '{s2}-7',31,'hạt','38 − 7 = 31, đúng lượng ban đầu. Cả hai bước thay đổi đều khớp; đáp số là 33 hạt.')],33,
        ['Tình huống có hai thay đổi nối tiếp theo thứ tự đã nêu.','Sau mỗi lần, ghi lại lượng đang có trước khi sang lần tiếp.'],
        [('Theo dõi lần đặt thêm trước lần lấy ra.','Thay đổi nào xảy ra đầu tiên?'),
         ('Kết quả của lần thêm là điểm bắt đầu của lần lấy ra.','Số hạt cần bớt được lấy từ lượng nào đang có?'),
         ('Dùng thao tác ngược để kiểm từng lượng trung gian rồi lượng đầu.','Nếu hoàn lại phần đã lấy ra, em cần quay về mốc nào?')],['31+7-5'])

    add('word_leave','current_g1_word_add_sub','core_02',
        'Trên sân có 29 con chim. Có 6 con bay đi, các con còn lại vẫn ở sân. Hỏi trên sân còn bao nhiêu con chim? Vì sao không cộng số chim bay đi?',
        [('trên sân có 29 con',29,'initial_count'),('6 con bay đi',6,'removed_count')],'con chim',
        [step('Tìm số còn lại','Chim bay khỏi sân làm số ở sân giảm; số bay đi là một phần của số ban đầu.',
              '29-6',23,'con chim','29 − 6 = 23. Không cộng vì đề không có chim mới bay đến.'),
         step('Đối chiếu các phần','Số còn ở sân cộng số bay đi phải bằng số ban đầu.',
              '{s0}+6',29,'con chim','23 + 6 = 29, khớp đề. Trên sân còn 23 con chim.')],23,
        ['Câu hỏi nói về những con còn ở sân.','Phân biệt chim bay đi với chim bay đến bằng ý nghĩa tình huống.'],
        [('Chỉ xét số chim vẫn ở trong sân sau sự việc.','Bay đi làm số chim ở sân tăng hay giảm?'),
         ('Số chim bay đi thuộc trong số chim ban đầu.','Em cần gộp thêm hay bớt phần bay đi khỏi số ban đầu?'),
         ('Tính theo quan hệ đã chọn rồi kiểm bằng cách ghép phần còn với phần đi.','Hai phần ghép lại phải bằng số nào trong đề?')],['29-6'])

    add('word_part_whole','current_g1_word_add_sub','core_03',
        'Một hộp có tất cả 36 viên bi, chỉ gồm bi đỏ và bi xanh. Có 14 viên bi đỏ. Hỏi có bao nhiêu viên bi xanh? Kiểm tra rằng hai loại gộp lại đủ cả hộp.',
        [('tất cả 36 viên',36,'whole'),('14 viên bi đỏ',14,'known_part')],'viên',
        [step('Tách phần đã biết khỏi cả hộp','Cả hộp chỉ có hai loại; bớt số bi đỏ khỏi tổng sẽ còn đúng số bi xanh.',
              '36-14',22,'viên','Hàng đơn vị: 6 − 4 = 2. Hàng chục: 3 − 1 = 2. Số bi xanh là 22 viên.'),
         step('Gộp hai loại để kiểm','Hai phần không trùng nhau và chứa đủ mọi viên bi trong hộp.',
              '14+{s0}',36,'viên','14 + 22 = 36, đúng tổng số bi. Vậy có 22 viên bi xanh.')],22,
        ['Đề khẳng định hộp chỉ có hai loại bi.','Nhận ra đâu là cả hộp và đâu là một phần đã biết.'],
        [('Số của cả hộp gồm cả phần đỏ và phần xanh.','Số nào trong đề là số của toàn bộ hộp?'),
         ('Phần xanh là phần còn lại sau khi tách phần đỏ khỏi tổng.','Để tìm phần chưa biết, em dùng tổng và phần đã biết thế nào?'),
         ('Sau khi tính, gộp lại hai loại và đối chiếu tổng.','Nếu hai phần chưa bằng cả hộp, em cần kiểm lại điều gì?')],['36-14'])

    wrong='18 − 5 + 2 = 18 − 7 = 11'
    add('misconception_changed_plus','current_g1_left_to_right_add_sub',None,
        'Với biểu thức 18 − 5 + 2, một bạn ghi dòng tính giả định: '+wrong+'. Hãy góp ý dựa đúng dòng đã ghi và hướng dẫn tính lại.',
        [('số đầu 18',18,'start'),('trừ 5',5,'first_change'),('cộng 2',2,'second_change')],'',
        [step('Chỉ ra chỗ đổi ý nghĩa phép tính','Trong dòng được cho, cộng 2 đã thành bớt thêm 2 khi thay phần sau bằng trừ 7.',
              '18-5',13,'','Ta chỉ biết dòng tính này không giữ dấu cộng 2 của đề. Không có bằng chứng về cách đặt cột hay nét viết. Làm từ trái sang phải: 18 − 5 = 13.'),
         step('Giữ dấu cộng ở bước tiếp','Cần thêm 2 vào kết quả sau phép trừ.',
              '{s0}+2',15,'','13 + 2 = 15. Dòng đúng là 18 − 5 + 2 = 13 + 2 = 15; không phải 11.')],15,
        ['Đối chiếu dấu của đề với dấu trong dòng bạn đã ghi.','Chỉ góp ý điều thể hiện trong dòng này, không đoán cách bạn đặt tính.'],
        [('Đề có một lần bớt và một lần thêm.','Dấu trước số cuối trong đề là dấu gì?'),
         ('Dòng đã ghi lại bớt cả phần vốn cần thêm.','Khi chuyển từ đề sang dòng tiếp, thao tác nào đã bị đổi?'),
         ('Giữ kết quả lần trừ đầu rồi thực hiện đúng dấu còn lại.','Em có thể viết lại dòng thứ hai mà vẫn giữ dấu cộng của đề không?')],['18-5+2'],
        {'text':wrong,'observations':[{'excerpt':'18 − 7','claim_scope':'Written transformation turns the final addition into extra subtraction; no motor or hidden strategy inference.'}]},kind='misconception')

    wrong='Còn lại: 25 + 3 = 28 (quả).'
    add('misconception_join_for_remove','current_g1_word_add_sub',None,
        'Rổ có 25 quả quýt. Mẹ lấy 3 quả từ rổ ra đĩa. Một bạn ghi bài làm giả định: '+wrong+' Hãy nhận xét phép tính và giúp tìm số quýt còn trong rổ.',
        [('có 25 quả',25,'initial_count'),('lấy 3 quả ra',3,'removed_count')],'quả',
        [step('Phân biệt tính đúng với chọn phép tính đúng','25 + 3 = 28 đúng về cộng, nhưng cộng không mô tả việc lấy quýt ra khỏi rổ.',
              '25-3',22,'quả','Số quýt trong rổ giảm khi lấy ra. Phải tính 25 − 3 = 22, nên còn 22 quả. Chưa có dữ kiện để kết luận bạn sai do đặt cột hay không nhớ bảng cộng.'),
         step('Kiểm lại bằng cách hoàn lại phần lấy ra','Cho phần đã lấy trở về rổ phải được số ban đầu.',
              '{s0}+3',25,'quả','22 + 3 = 25, khớp số quýt lúc đầu. Vậy còn 22 quả trong rổ.')],22,
        ['Xét ý nghĩa của việc lấy ra trước khi xét kết quả tính.','Dòng cộng có thể đúng số học nhưng chưa đúng câu hỏi.'],
        [('Tập trung vào những quả còn nằm trong rổ.','Sau khi lấy ra, số quýt trong rổ tăng hay giảm?'),
         ('Đối chiếu sự thay đổi đó với dấu bạn đã chọn.','Phép cộng trong bài làm có diễn tả đúng việc lấy ra không?'),
         ('Chọn phép tính theo tình huống rồi dùng phép tính ngược để kiểm.','Hoàn lại phần đã lấy phải khôi phục số quýt nào?')],['25-3'],
        {'text':wrong,'observations':[{'excerpt':'25 + 3 = 28','claim_scope':'Arithmetic addition is correct but the chosen operation does not model removal.'}]},kind='misconception')

    add('guard_missing_bird_picture','current_g1_word_add_sub',None,
        'Em hỏi: Trong tranh có một số con chim, một số con bay đi. Hỏi còn mấy con? Nhưng tranh chưa được gửi và em chưa ghi số con ban đầu hay số con bay đi. Hãy hỗ trợ em mà không đoán số.',
        [],'',[],None,
        ['Chưa có tranh hoặc số liệu để xác định số chim còn lại.','Em gửi tranh rõ, hoặc ghi số chim ban đầu và số chim bay đi; sau đó mình cùng tìm số còn lại.'],
        [('Mình chưa nhận được tranh nên chưa thể đếm các nhóm chim.','Em có thể gửi tranh rõ của bài này không?'),
         ('Nếu chưa gửi được tranh, em có thể kể lại các số lượng bằng chữ.','Lúc đầu có bao nhiêu con và có bao nhiêu con bay đi?'),
         ('Sau khi có đủ hai số lượng, mới xác định phần còn lại, không đoán từ câu chuyện.','Em đã cung cấp đủ số ban đầu và số bay đi chưa?')],[],kind='guard')

    assert len(rows)==9
    blocked,questions,_=protections();_,_,_,seen=v4.v3_catalog()
    checks=[]
    for r in rows:
        m=inspect_case(r); assert m['passed'],(r['sample_id'],m)
        assert mapping_error(r,nodes) is None
        signatures=answer_signatures(r,m)
        assert not signatures & blocked,r['sample_id']
        assert normalized(r['problem']) not in questions
        overlap=signatures&seen.keys()
        r['provenance']['bounded_numeric_exposure']='PREVIOUS_TRAIN_CASE_MAY_RECUR_IN_FINITE_DOMAIN' if overlap else 'NO_DETECTED_PREVIOUS_TRAIN_SIGNATURE'
        r['provenance']['previous_train_source_ids']=sorted({i for sig in overlap for i in seen[sig]})
        checks.append({'sample_id':r['sample_id'],'mechanical':m,'protected_collision':False})
    write_rows(path,rows)
    write_json(HERE/'evidence/primary_math_teacher_20261016/g1_operations_0003_author_checks.json',
               {'batch_sha256':sha(path.read_bytes()),'checks':checks,'semantic_review_status':'PENDING_SEPARATE_CONTENT_PASS',
                'training_started':False,'skills_matched':'none'})
    print(json.dumps({'authored_cases':len(rows),'batch_sha256':sha(path.read_bytes()),'review_pending':True}))


if __name__=='__main__': main()
