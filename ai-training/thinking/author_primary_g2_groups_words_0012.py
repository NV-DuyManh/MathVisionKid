"""Original group-role and relational-word-problem drafts; acceptance pending review."""
import copy,json
from primary_math_data_pipeline import (HERE,DEFAULT_ROOT,read_rows,write_rows,write_json,sha,row_sha,
    inspect_case,mapping_error,protections,answer_signatures,normalized,curate)


def main():
    path=DEFAULT_ROOT/'authored_batches/g2_groups_words_0012.jsonl'
    if path.exists():print('Batch exists; do not recreate pending cases.');return
    bp=DEFAULT_ROOT/'curriculum_blueprint.json';blueprint=json.loads(bp.read_text('utf-8'));nodes={n['node_id']:n for n in blueprint['nodes']}
    template=read_rows(DEFAULT_ROOT/'authored_batches/g1_geometry_0004.jsonl')[0];rows=[]
    def add(suffix,nodeid,slot,problem,givens,steps,answers,initial,hints,ops,kind='core',student=None):
        r=copy.deepcopy(template);node=nodes[nodeid];sid='primary_20261017_g2_groups_words_0012_'+suffix
        r.update(sample_id=sid,case_group_id=sid,grade=2,topic=suffix,problem=problem,
            givens=[{'id':'g'+str(i),'text':t,'value':v,'unit':u,'role':role} for i,(t,v,u,role) in enumerate(givens)],
            requested_quantity='; '.join(q for q,v,u in answers) if answers else 'Thông tin còn thiếu để có kết quả duy nhất',
            student_work=student,initial_guidance=initial,
            hints=[{'level':i+1,'hint':h,'question':q} for i,(h,q) in enumerate(hints)],
            worked_steps=[{'step_id':'s'+str(i),'title':t,'reason':why,'expression':expr,'result':str(v),'unit':u,'explanation':ex}
                for i,(t,why,expr,v,u,ex) in enumerate(steps)],
            expected_answer=[{'quantity':q,'result':str(v),'unit':u} for q,v,u in answers],can_solve=bool(answers),
            canonical_case={'family':suffix,'operations':ops,'numeric_values':[str(v) for t,v,u,role in givens if v is not None]})
        r['curriculum_assignment']={'node_id':nodeid,'curriculum_scope':node['curriculum_scope'],'case_kind':kind}
        if kind=='core':
            s=next(s for s in node['authoring_plan']['core_cases'] if s['case_slot']==slot)
            r['curriculum_assignment'].update({k:s[k] for k in ('case_slot','context_variant','method_variant')})
        r['provenance'].update(authoring_label='AI_TEACHER',authoring_agent='root',source_evidence=node['source_evidence'],
            blueprint_sha256=sha(bp.read_bytes()),source_kind='ORIGINAL_EXPLICIT_TEXT_TEACHER_CASE' if answers else 'ORIGINAL_MISSING_INFORMATION_GUARD',
            student_work_origin='EXPLICITLY_SYNTHETIC' if student else None,content_review_status='PENDING_INDEPENDENT_CONTENT_REVIEW',
            visual_or_physical_outcome_verified=False)
        r['quality_flags']['verification_is_not_an_extra_problem_solving_step']=nodeid=='current_g2_word_one_step'
        rows.append(r)

    add('two_per_tray','current_g2_multiplication_division_tables_2_5','core_01',
        'Có 7 khay, mỗi khay đặt 2 chiếc cốc; các khay không dùng chung cốc. Hỏi có tất cả bao nhiêu chiếc cốc? Giải thích bằng các nhóm bằng nhau và nêu tên thành phần trong phép nhân.',
        [('7 khay','7','khay','number_of_groups'),('Mỗi khay 2 cốc','2','cốc/khay','group_size')],
        [('Gộp các nhóm bằng nhau','Hai chiếc được lấy đủ ở mỗi trong bảy khay nên dùng phép nhân số cốc mỗi khay với số khay.','2*7',14,'cốc',
          'Đếm theo hai: 2, 4, 6, 8, 10, 12, 14. Phép nhân là 2 × 7 = 14 cốc.'),
         ('Kiểm và gọi tên thành phần','Phép cộng lặp lại phải khớp cách lấy hai cốc cho từng khay.','2+2+2+2+2+2+2',14,'cốc',
          'Có bảy số 2 nên đã tính đúng bảy khay, được 14 cốc. Trong 2 × 7 = 14, 2 và 7 là các thừa số, 14 là tích.')],
        [('Tổng số cốc',14,'cốc')],
        ['Đề cho số nhóm và lượng bằng nhau trong mỗi nhóm.','Phân biệt khay với cốc khi chọn phép tính và ghi đơn vị kết quả.'],
        [('Mỗi khay đóng góp cùng một lượng cốc.', 'Em cần gộp lượng cốc của bao nhiêu khay?'),
         ('Có thể viết phép cộng cùng số hạng trước khi biểu diễn bằng phép nhân.', 'Số hạng lặp lại trong phép cộng của em biểu thị đại lượng nào?'),
         ('Kiểm số lần lặp và giữ đơn vị của đại lượng cần tìm.', 'Em đã dùng mỗi khay đúng một lần và trả lời bằng đơn vị nào?')],['2*7'])

    add('two_division_roles','current_g2_multiplication_division_tables_2_5','core_03',
        'Xét riêng hai cách chia cùng lượng 45 viên bi, mỗi cách bắt đầu lại từ toàn bộ 45 viên. Cách A: chia đều vào 5 túi, hỏi mỗi túi được mấy viên. Cách B: mỗi túi đựng đúng 5 viên, dùng hết số bi, hỏi cần mấy túi. Giải từng cách rồi nói rõ đơn vị của hai kết quả, dù hai phép tính có thể giống nhau.',
        [('Tổng 45 viên bi','45','viên','total_items'),('A có 5 túi','5','túi','A_group_count'),('B mỗi túi 5 viên','5','viên/túi','B_group_size')],
        [('Chia đều để tìm số vật mỗi nhóm','A biết số túi và tổng bi; chia tổng cho số túi để tìm lượng bi trong mỗi túi.','45/5',9,'viên/túi',
          '45 : 5 = 9. Cách A có 9 viên bi trong mỗi túi.'),
         ('Lập nhóm để tìm số nhóm','B biết lượng mỗi túi và tổng bi; chia tổng cho lượng mỗi túi để tìm số túi.','45/5',9,'túi',
          '45 : 5 = 9. Cách B cần 9 túi, mỗi túi 5 viên. Cùng phép tính nhưng A hỏi số bi mỗi túi, B hỏi số túi.'),
         ('Kiểm dùng hết tổng','Số nhóm nhân số vật mỗi nhóm phải khớp tổng ở từng cách.','9*5',45,'viên',
          'A: 5 túi, mỗi túi 9 viên được 45 viên. B: 9 túi, mỗi túi 5 viên cũng được 45 viên. Không trộn hai cách chia thành một quá trình liên tiếp.')],
        [('Bi trong mỗi túi ở A',9,'viên/túi'),('Số túi ở B',9,'túi')],
        ['Tách hai tình huống, không thực hiện A rồi dùng phần còn lại cho B.','Trước khi tính, ghi rõ câu hỏi cần số túi hay số bi trong mỗi túi.'],
        [('Hai số 5 có cùng cách viết nhưng mang vai trò khác nhau.', 'Ở mỗi cách, số 5 đang chỉ số nhóm hay lượng mỗi nhóm?'),
         ('Phép chia cần được đọc theo đại lượng câu hỏi yêu cầu.', 'Kết quả của từng cách phải mang đơn vị nào theo câu hỏi?'),
         ('Kiểm tổng từ số nhóm và lượng mỗi nhóm, rồi giữ đúng tên đại lượng ở từng đáp án.', 'Hai kết quả có cùng chữ số thì có nhất thiết đang đếm cùng loại lượng không?')],['45/5'])

    wrong='Mỗi bạn được 25 − 5 = 20 chiếc kẹo.'
    add('misconception_share_as_remove','current_g2_multiplication_division_tables_2_5',None,
        'Có 25 chiếc kẹo chia đều, dùng hết cho 5 bạn. Một bạn ghi giả định: '+wrong+' Hãy nhận xét cách chọn phép tính và tìm lượng kẹo mỗi bạn nhận.',
        [('Tổng 25 kẹo','25','kẹo','total_items'),('Chia đều cho 5 bạn','5','bạn','number_of_groups')],
        [('Phân biệt chia đều với lấy bớt','Số 5 chỉ số người chia, không phải số kẹo lấy ra khỏi tổng.',None,'cần tìm lượng kẹo mỗi bạn','',
          '25 − 5 = 20 là phép trừ đúng, nhưng không diễn tả chia đều 25 kẹo cho 5 bạn. Phải tìm số kẹo bằng nhau trong mỗi phần.'),
         ('Chia tổng cho số bạn','Biết tổng và số phần bằng nhau nên dùng phép chia.','25/5',5,'kẹo/bạn',
          '25 : 5 = 5, mỗi bạn được 5 chiếc kẹo. Số 5 bạn và số 5 kẹo mỗi bạn có vai trò, đơn vị khác nhau.'),
         ('Kiểm bằng cách gộp các phần','Lượng mỗi bạn nhân số bạn phải khôi phục tổng.','{s1}*5',25,'kẹo',
          '5 × 5 = 25 chiếc kẹo, đủ tổng và các phần bằng nhau.')],
        [('Kẹo mỗi bạn nhận',5,'kẹo/bạn')],
        ['Xem số người chia có cùng đơn vị với số kẹo bị lấy ra hay không.','Giữ đúng yêu cầu chia đều và dùng hết, không chỉ kiểm riêng phép trừ.'],
        [('Câu hỏi cần lượng trong một phần bằng nhau.', 'Số người được chia có phải là một lượng kẹo lấy ra không?'),
         ('Cần một phép tính liên hệ tổng kẹo với số bạn để tìm mỗi phần.', 'Đề đang mô tả gộp thêm, lấy bớt hay chia đều các phần?'),
         ('Sau khi có lượng mỗi phần, gộp đủ các phần để kiểm tổng.', 'Phép kiểm của em có dùng hết số kẹo và cho các bạn lượng bằng nhau không?')],['25/5'],kind='misconception',
        student={'text':wrong,'observations':[{'excerpt':'25 − 5 = 20','claim_scope':'The supplied subtraction is numerically correct but uses a count of people as if it were candies removed; no unseen pupil strategy inferred.'}]})

    add('guard_missing_bag_count','current_g2_multiplication_division_tables_2_5',None,
        'Có 20 viên bi được chia đều, dùng hết vào các túi. Chưa biết có bao nhiêu túi. Em hỏi mỗi túi được mấy viên. Hãy hỏi đúng dữ kiện còn thiếu trước khi cho đáp số.',
        [('Tổng 20 viên','20','viên','known_total'),('Chưa biết số túi',None,'túi','missing_group_count')],[],[],
        ['Mình biết tổng số bi và điều kiện chia đều nhưng chưa có số túi.','Em cho biết dùng bao nhiêu túi để xác định lượng bi mỗi túi.'],
        [('Câu hỏi về mỗi túi cần biết số phần được chia.', 'Có tất cả bao nhiêu túi trong lần chia này?'),
         ('Những số túi khác nhau có thể cho các lượng bi mỗi túi khác nhau.', 'Đề có hình hoặc câu nào cho biết số túi mà em chưa chép không?'),
         ('Sau khi có số túi, cần kiểm chia đều và dùng hết như yêu cầu.', 'Em đã xác nhận đủ số túi cùng điều kiện chia đều chưa?')],[],kind='guard')

    add('known_larger_ask_smaller','current_g2_word_one_step','core_02',
        'Lan có 37 nhãn vở. Lan có nhiều hơn Minh 9 nhãn. Hỏi Minh có bao nhiêu nhãn vở? Giải thích vì sao có từ nhiều hơn nhưng không cộng 9 vào số nhãn của Lan.',
        [('Lan có 37 nhãn','37','nhãn','known_larger_quantity'),('Lan hơn Minh 9 nhãn','9','nhãn','difference')],
        [('Tìm lượng nhỏ hơn từ lượng lớn và phần hơn','37 là lượng của Lan đã gồm phần nhiều hơn Minh; bớt phần hơn để còn lượng của Minh.','37-9',28,'nhãn',
          'Minh có 37 − 9 = 28 nhãn. Không cộng vì đề cho lượng người nhiều hơn và hỏi lượng người ít hơn, không phải cho Minh rồi hỏi Lan.'),
         ('Kiểm quan hệ hơn kém','Lượng của Minh cộng phần kém phải bằng lượng của Lan.','{s0}+9',37,'nhãn',
          '28 + 9 = 37, đúng số nhãn của Lan. Bài tìm Minh dùng một phép trừ; phép cộng này chỉ dùng để kiểm lại.')],
        [('Số nhãn của Minh',28,'nhãn')],
        ['Xác định số đã biết thuộc về ai và người ấy nhiều hơn hay ít hơn.','Chọn phép tính từ vai trò hai lượng, không chỉ từ một từ khóa.'],
        [('Theo dõi người được hỏi so với người đã biết lượng.', 'Minh là người có nhiều hơn hay ít hơn Lan theo đề?'),
         ('Lượng của người nhiều hơn chứa cả lượng của người kia và phần hơn.', 'Phần hơn đang nằm trong số đã biết hay cần gộp thêm vào số đó?'),
         ('Dùng quan hệ hơn kém để kiểm lại số em đề xuất.', 'Số của Minh cộng phần chênh có khớp số của Lan không?')],['37-9'])

    add('difference_between_two_counts','current_g2_word_one_step','core_03',
        'Mai đã đọc 46 trang sách, Nam đã đọc 39 trang. Hỏi Mai đọc nhiều hơn Nam bao nhiêu trang? Tìm bằng một phép tính rồi kiểm quan hệ giữa ba lượng.',
        [('Mai đọc 46 trang','46','trang','larger_quantity'),('Nam đọc 39 trang','39','trang','smaller_quantity')],
        [('Tìm phần vượt quá lượng nhỏ hơn','Câu hỏi không tìm tổng hoặc số trang của một người mà tìm phần chênh giữa hai lượng.','46-39',7,'trang',
          'Mai đọc nhiều hơn 46 − 39 = 7 trang.'),
         ('Kiểm từ lượng nhỏ và phần chênh','Lượng nhỏ hơn cộng phần chênh phải bằng lượng lớn hơn.','39+{s0}',46,'trang',
          '39 + 7 = 46, khớp số trang Mai đã đọc. Chênh lệch là 7 trang, không phải tổng trang hai bạn đọc.')],
        [('Số trang Mai đọc nhiều hơn Nam',7,'trang')],
        ['Phân biệt câu hỏi bao nhiêu trang nhiều hơn với câu hỏi tất cả bao nhiêu trang.','Hai số đo cùng đơn vị nên có thể đối chiếu trực tiếp.'],
        [('Cần tìm phần một lượng vượt qua lượng kia.', 'Câu hỏi đang tìm tổng hai lượng hay phần chênh giữa chúng?'),
         ('Ghép phần chung với lượng nhỏ hơn để hình dung phần còn vượt ra.', 'Số đã biết nào là lượng lớn hơn trong tình huống?'),
         ('Khi có phần chênh, gộp nó với lượng nhỏ để kiểm lượng lớn.', 'Phép kiểm có khôi phục đúng lượng của người đọc nhiều hơn không?')],['46-39'])

    wrong='Trang có 24 − 6 = 18 thẻ vì đề nói ít hơn.'
    add('misconception_keyword_without_roles','current_g2_word_one_step',None,
        'Quân có 24 thẻ và có ít hơn Trang 6 thẻ. Hỏi Trang có mấy thẻ. Một bạn ghi giả định: '+wrong+' Hãy kiểm lý do và giải lại đúng người được hỏi.',
        [('Quân có 24 thẻ','24','thẻ','known_smaller_quantity'),('Quân ít hơn Trang 6 thẻ','6','thẻ','difference')],
        [('Xét người ít hơn và người được hỏi','Quân ít hơn Trang nên Trang phải có nhiều hơn lượng của Quân.',None,'Trang là người có nhiều thẻ hơn','',
          'Câu viết chọn dấu trừ chỉ từ cụm ít hơn nhưng chưa xét người đang được hỏi. 18 còn ít hơn 24 nên không thỏa quan hệ Trang nhiều hơn Quân.'),
         ('Tìm lượng lớn hơn','Gộp phần chênh với lượng nhỏ đã biết để tìm lượng lớn.','24+6',30,'thẻ',
          'Trang có 24 + 6 = 30 thẻ.'),
         ('Kiểm lại câu quan hệ','Bớt phần chênh khỏi lượng của Trang phải trở lại lượng của Quân.','{s1}-6',24,'thẻ',
          '30 − 6 = 24, đúng số thẻ của Quân. Bài tìm Trang cần một phép cộng, phép trừ cuối chỉ là kiểm.')],
        [('Số thẻ của Trang',30,'thẻ')],
        ['Gắn từ ít hơn với đúng người, không tự áp thành một dấu phép tính.', 'Theo dõi người được hỏi trước khi chọn dấu.'],
        [('Quan hệ trong đề nói Quân ít hơn người khác.', 'Người được hỏi có nhiều hay ít thẻ hơn người đã biết số?'),
         ('Lượng lớn gồm lượng nhỏ và phần chênh; từ ít hơn không tự quyết định dấu khi chưa biết hỏi ai.', 'Số bạn đề xuất có thỏa vai trò lớn hơn hoặc nhỏ hơn trong câu không?'),
         ('Viết số của người được hỏi rồi dùng quan hệ ban đầu để kiểm người còn lại.', 'Phép kiểm của em có khớp số thẻ đã cho của Quân không?')],['24+6'],kind='misconception',
        student={'text':wrong,'observations':[{'excerpt':'vì đề nói ít hơn','claim_scope':'The written reason explicitly chooses subtraction from a keyword while the asked person is the larger quantity.'}]})

    add('guard_comparison_without_base','current_g2_word_one_step',None,
        'Mai có nhiều hơn Nam 7 nhãn vở. Chưa biết Nam có bao nhiêu nhãn. Em hỏi Mai có mấy nhãn. Hãy hỏi dữ kiện còn thiếu, không gọi số chênh là toàn bộ số nhãn của Mai.',
        [('Mai hơn Nam 7 nhãn','7','nhãn','known_difference'),('Chưa biết số nhãn Nam',None,'nhãn','missing_base_quantity')],[],[],
        ['Mình mới biết phần chênh, chưa có lượng làm mốc để tìm số của Mai.', 'Em cho biết Nam có bao nhiêu nhãn để cùng xác định số của Mai.'],
        [('Phần chênh không phải số lượng đầy đủ của một người.', 'Đề đã cho số nhãn của Nam chưa?'),
         ('Những lượng khác nhau của Nam có thể cùng thỏa một phần chênh đã biết.', 'Em có thể bổ sung lượng của người làm mốc không?'),
         ('Chỉ khi có lượng làm mốc mới dùng quan hệ để tìm người được hỏi.', 'Thông tin mới của em đã đủ xác định một số duy nhất cho Mai chưa?')],[],kind='guard')

    assert len(rows)==8
    protected,questions,_=protections();existing=[r for f in (DEFAULT_ROOT/'authored_batches').glob('*.jsonl') for r in read_rows(f)]
    existing_questions={normalized(r['problem']) for r in existing};checks=[]
    for r in rows:
        m=inspect_case(r);assert m['passed'],(r['sample_id'],m)
        assert mapping_error(r,nodes) is None
        assert not answer_signatures(r,m)&protected,r['sample_id']
        assert normalized(r['problem']) not in questions|existing_questions
        checks.append({'sample_id':r['sample_id'],'row_sha256':row_sha(r),'mechanical':m,'mapping_pass':True})
    assert len([[None,None] for _ in range(7)])==7 and sum(len(g) for g in [[None,None] for _ in range(7)])==14
    shared=[[] for _ in range(5)]
    for i in range(45):shared[i%5].append(i)
    assert [len(g) for g in shared]==[9]*5
    grouped=[list(range(i,i+5)) for i in range(0,45,5)];assert len(grouped)==9 and all(len(g)==5 for g in grouped)
    sweets=[[] for _ in range(5)]
    for i in range(25):sweets[i%5].append(i)
    assert [len(g) for g in sweets]==[5]*5
    assert len(range(9,37))==28 and 28+9==37
    assert len(range(39,46))==7 and 39+7==46
    assert len([None]*24+[None]*6)==30 and 30-6==24
    frozen={p:sha((HERE.parent/p).read_bytes())==h for p,h in blueprint['existing_inputs']['source_fingerprints'].items()};assert all(frozen.values())
    write_rows(path,rows)
    write_json(HERE/'evidence/primary_math_teacher_20261016/g2_groups_words_0012_pre_review.json',{
        'batch_sha256':sha(path.read_bytes()),'authored_cases':8,'core_cases':4,'misconception_cases':2,'guard_cases':2,
        'checks':checks,'frozen_inputs_unchanged':frozen,'independent_semantic_review_completed':False,
        'self_content_check':'Author checked both meanings of division, one primary word-problem operation with separate inverse verification, units, synthetic evidence and every hint. Independent content review remains pending.',
        'oracles':{'seven_groups_two':14,'A_share_45_among_5':[9]*5,'B_groups_of_5_from_45':9,
            'share_25_among_5':[5]*5,'known_larger_to_smaller':28,'difference':7,'known_smaller_to_larger':30,
            'missing_group_count':'Total20 supports different equal partitions; no count supplied so no numeric target.',
            'missing_base_counterexamples':[{'Nam':12,'Mai':19},{'Nam':20,'Mai':27}]},
        'protected_candidates_not_authored':['30/5','20/5','35/5'],
        'limits':'Integer set/group oracles do not certify pedagogy. No division remainder or table3/4 introduced under current grade2 node. No real image/physical success claimed.',
        'human_verified':False,'teacher_certified':False,'training_started':False,'sealed_concept_challenge_read':False})
    state=curate(DEFAULT_ROOT)
    assert state['authored_cases']==127 and state['accepted_cases']==88
    assert state['decisions']=={'PENDING_AI_CONTENT_REVIEW':39,'ACCEPTED_AI_RESEARCH':88}
    print(json.dumps({k:state[k] for k in ('authored_cases','accepted_cases','chat_train_rows','remaining_core_cases','decisions')}))


if __name__=='__main__':main()
