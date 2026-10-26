"""Original finite drafts with explicit regrouping bounds and teacher-visible steps."""
import copy,json
from primary_math_data_pipeline import (HERE,DEFAULT_ROOT,read_rows,write_rows,write_json,sha,row_sha,
    inspect_case,mapping_error,protections,answer_signatures,normalized,curate)


def main():
    path=DEFAULT_ROOT/'authored_batches/g2_regroup_mental_0011.jsonl'
    if path.exists():print('Batch exists; await review rather than recreate.');return
    bp=DEFAULT_ROOT/'curriculum_blueprint.json';blueprint=json.loads(bp.read_text('utf-8'))
    nodes={n['node_id']:n for n in blueprint['nodes']}
    template=read_rows(DEFAULT_ROOT/'authored_batches/g1_geometry_0004.jsonl')[0];rows=[]
    def add(suffix,nodeid,slot,problem,givens,steps,answers,initial,hints,canonical,kind='core',student=None):
        r=copy.deepcopy(template);node=nodes[nodeid];sid='primary_20261017_g2_regroup_mental_0011_'+suffix
        r.update(sample_id=sid,case_group_id=sid,grade=2,topic=suffix,problem=problem,
            givens=[{'id':'g'+str(i),'text':t,'value':v,'unit':u,'role':role} for i,(t,v,u,role) in enumerate(givens)],
            requested_quantity='; '.join(q for q,v,u in answers),student_work=student,initial_guidance=initial,
            hints=[{'level':i+1,'hint':h,'question':q} for i,(h,q) in enumerate(hints)],
            worked_steps=[{'step_id':'s'+str(i),'title':t,'reason':why,'expression':expr,'result':str(v),'unit':u,'explanation':ex}
                for i,(t,why,expr,v,u,ex) in enumerate(steps)],
            expected_answer=[{'quantity':q,'result':str(v),'unit':u} for q,v,u in answers],can_solve=True,
            canonical_case={'family':suffix,'operations':canonical,'numeric_values':[str(v) for t,v,u,role in givens if v is not None]})
        r['curriculum_assignment']={'node_id':nodeid,'curriculum_scope':node['curriculum_scope'],'case_kind':kind}
        if kind=='core':
            s=next(s for s in node['authoring_plan']['core_cases'] if s['case_slot']==slot)
            r['curriculum_assignment'].update({k:s[k] for k in ('case_slot','context_variant','method_variant')})
        r['provenance'].update(authoring_label='AI_TEACHER',authoring_agent='root',
            source_evidence=node['source_evidence'],blueprint_sha256=sha(bp.read_bytes()),
            source_kind='ORIGINAL_EXPLICIT_TEXT_TEACHER_CASE',student_work_origin='EXPLICITLY_SYNTHETIC' if student else None,
            content_review_status='PENDING_INDEPENDENT_CONTENT_REVIEW',visual_or_physical_outcome_verified=False)
        rows.append(r)

    add('subtract_one_borrow_units','current_g2_addition_subtraction_carry_once','core_02',
        'Tính 453 − 128 theo các hàng. Giải thích một lần đổi chục sang đơn vị, kiểm bằng phép cộng, rồi gọi tên số bị trừ, số trừ và hiệu.',
        [('Số 453','453','','minuend'),('Số 128','128','','subtrahend')],
        [('Trừ theo hàng và giữ lần đổi','Hàng đơn vị chưa đủ để bớt nên đổi một chục sang mười đơn vị; hàng chục phải giảm theo.','453-128',325,'',
          '3 đơn vị chưa bớt được 8 đơn vị trong các số tự nhiên. Đổi 1 chục thành 10 đơn vị: có 13 đơn vị, còn 4 chục. 13 − 8 = 5; 4 − 2 = 2 chục; 4 − 1 = 3 trăm. Hiệu là 325, chỉ đổi một lần.'),
         ('Kiểm bằng phép cộng ngược','Hiệu cộng số trừ phải khôi phục số bị trừ.','{s0}+128',453,'',
          '325 + 128 = 453, khớp số ban đầu.'),
         ('Gọi tên các thành phần','Tên phụ thuộc vai trò trong phép trừ đã cho.',None,'453 là số bị trừ; 128 là số trừ; 325 là hiệu','',
          'Trong 453 − 128 = 325: 453 là số bị trừ, 128 là số trừ, 325 là hiệu.')],
        [('Hiệu',325,''),('Tên các thành phần','453 là số bị trừ; 128 là số trừ; 325 là hiệu','')],
        ['Đặt các hàng trăm, chục, đơn vị thẳng nhau và xét từ hàng đơn vị.','Mỗi lần đổi phải giữ cùng giá trị của số, đồng thời cập nhật hàng đã cho đi.'],
        [('Đối chiếu lượng ở hàng đơn vị trước khi trừ.', 'Hàng đơn vị của số bị trừ đã đủ để bớt lượng tương ứng chưa?'),
         ('Nếu đổi từ hàng chục, lượng ở hàng chục cần được cập nhật chứ không giữ nguyên.', 'Sau khi một hàng cho đi để đổi, em cần sửa lượng của hàng đó thế nào?'),
         ('Dùng phép cộng ngược để kiểm toàn bộ kết quả và gắn đúng tên thành phần.', 'Hiệu em tìm cộng số trừ có trở lại đúng số bị trừ không?')],['453-128'])

    add('missing_addend_one_borrow_tens','current_g2_addition_subtraction_carry_once','core_03',
        'Tổng của hai số là 427. Số hạng thứ nhất là 156. Tìm số hạng thứ hai, giải thích vì sao chọn phép tính rồi kiểm bằng cách cộng lại. Khi trừ, nói rõ việc đổi ở hàng chục nếu cần.',
        [('Tổng 427','427','','whole_sum'),('Số hạng đã biết 156','156','','known_addend')],
        [('Tìm phần còn lại của tổng','Tổng gồm hai số hạng, nên bớt số hạng đã biết khỏi tổng để tìm số hạng còn lại.','427-156',271,'',
          '7 − 6 = 1 đơn vị. 2 chục chưa bớt được 5 chục, đổi 1 trăm sang 10 chục: có 12 chục, còn 3 trăm. 12 − 5 = 7 chục; 3 − 1 = 2 trăm. Số hạng còn lại là 271.'),
         ('Kiểm điều kiện tổng','Hai số hạng cộng lại phải đúng tổng đề cho.','156+{s0}',427,'',
          '156 + 271 = 427. Vậy 271 thỏa điều kiện; 156 và 271 là hai số hạng, 427 là tổng.')],
        [('Số hạng thứ hai',271,'')],
        ['Xác định số nào là tổng của cả hai phần và số nào là phần đã biết.','Không gộp tổng với một số hạng để tìm số hạng còn lại.'],
        [('Một số hạng chưa biết là phần còn lại trong tổng.', 'Đề đã cho lượng toàn bộ và phần nào của toàn bộ?'),
         ('Bớt phần đã biết khỏi tổng rồi làm theo từng hàng, cập nhật hàng có đổi.', 'Ở phép tính em chọn, hàng nào cần được xét kỹ trước khi trừ?'),
         ('Cộng số tìm được với số hạng đã biết để kiểm lại điều kiện ban đầu.', 'Phép kiểm của em có cho đúng tổng được nêu không?')],['427-156'])

    add('mental_make_ten','current_g2_mental_add_sub_20','core_01',
        'Nhẩm 9 + 6 bằng cách ghép cho đủ 10 trước. Nêu phần lấy từ số cộng thứ hai và phần còn lại để không đếm thừa.',
        [('Số cộng thứ nhất 9','9','','first_addend'),('Số cộng thứ hai 6','6','','second_addend'),('Mốc ghép đủ 10','10','','mental_bridge')],
        [('Tìm phần cần để đủ chục','Cần biết thiếu bao nhiêu từ số thứ nhất đến mốc mười.','10-9',1,'',
          '9 còn thiếu 1 để đủ 10.'),
         ('Giữ phần chưa dùng của số cộng','Lấy 1 từ 6 sang ghép với 9 thì 6 còn phần khác, không được giữ nguyên toàn bộ 6.','6-{s0}',5,'',
          'Tách 6 thành 1 và 5. Phần 1 dùng để đủ chục, phần 5 chưa dùng.'),
         ('Ghép đủ mười','Dùng đúng phần đã tách, không tạo thêm lượng ngoài hai số ban đầu.','9+{s0}',10,'',
          '9 + 1 = 10.'),
         ('Cộng phần còn lại','Sau khi ghép đủ chục, cộng phần số hạng thứ hai chưa dùng.','{s2}+{s1}',15,'',
          '10 + 5 = 15, nên 9 + 6 = 15. Kiểm đã dùng đủ phần 1 và 5 của số 6, không lặp phần nào.')],
        [('Tổng cần nhẩm',15,'')],
        ['Chọn mốc mười để nhẩm, nhưng không thay đổi tổng hai số ban đầu.','Nếu lấy một phần từ số thứ hai, cần theo dõi phần chưa dùng của số đó.'],
        [('Tìm khoảng còn thiếu của số thứ nhất tới mốc được yêu cầu.', 'Cần lấy phần bổ sung từ số nào để vẫn giữ nguyên tổng?'),
         ('Tách số thứ hai thành phần ghép đủ chục và phần còn lại.', 'Sau khi lấy một phần để ghép, có được dùng lại toàn bộ số thứ hai không?'),
         ('Ghép đủ chục rồi cộng đúng phần chưa dùng và kiểm mỗi phần chỉ tính một lần.', 'Em đã giữ đủ hai phần của số thứ hai mà không bỏ hoặc đếm thừa chưa?')],['9+6'])

    add('mental_subtract_via_ten','current_g2_mental_add_sub_20','core_02',
        'Nhẩm 15 − 7 bằng cách bớt đến 10 rồi bớt tiếp phần còn lại. Giải thích cách tách số cần bớt để không bớt hai lần cùng một phần.',
        [('Số ban đầu 15','15','','minuend'),('Cần bớt 7','7','','subtrahend'),('Mốc giữa 10','10','','mental_bridge')],
        [('Tìm phần cần bớt để về mười','Từ số ban đầu về mốc mười cần bớt một phần của tổng lượng phải bớt.','15-10',5,'',
          'Từ 15 về 10 cần bớt 5.'),
         ('Thực hiện lần bớt đầu','Bớt phần vừa tìm trước để đến mốc thuận tiện.','15-{s0}',10,'',
          '15 − 5 = 10.'),
         ('Tìm phần còn phải bớt','Trong 7 cần bớt, đã bớt 5 nên chỉ bớt nốt phần còn lại.','7-{s0}',2,'',
          '7 gồm 5 và 2; còn phải bớt 2, không bớt thêm cả 7.'),
         ('Bớt nốt và kiểm lượng đã bớt','Hai phần bớt phải gộp đúng lượng ban đầu cần bớt.','{s1}-{s2}',8,'',
          '10 − 2 = 8, nên 15 − 7 = 8. Kiểm phần đã bớt là 5 + 2 = 7; cũng có 8 + 7 = 15.')],
        [('Hiệu cần nhẩm',8,'')],
        ['Dùng mốc mười để chia việc bớt thành hai lần.','Tổng hai phần bớt phải bằng đúng số cần bớt ban đầu.'],
        [('Tìm phần đưa số ban đầu về mốc mười.', 'Phần bớt trước đó có thuộc số cần bớt của đề không?'),
         ('Sau lần bớt đầu, chỉ dùng lượng còn chưa bớt của số trừ.', 'Em đã bớt phần nào và còn phải bớt phần nào?'),
         ('Kiểm tổng hai phần đã bớt rồi dùng phép cộng ngược để kiểm kết quả.', 'Phần em thực sự bớt có đúng bằng số trừ ban đầu chưa?')],['15-7'])

    add('mental_round_hundreds_transfer','current_g2_mental_add_sub_20','core_03',
        'Kho có 300 tờ giấy, nhận thêm 400 tờ. Hãy nhẩm số tờ bằng cách đếm theo trăm, rồi kiểm bằng cách tách lại phần vừa nhận. Không đặt tính từng tờ.',
        [('Ban đầu 300 tờ','300','tờ','initial_count'),('Nhận thêm 400 tờ','400','tờ','added_count'),('Một trăm gồm 100 tờ','100','tờ/trăm','hundreds_unit')],
        [('Đếm cùng đơn vị trăm','300 tờ là 3 trăm tờ, 400 tờ là 4 trăm tờ; gộp số trăm trước.','3+4',7,'trăm tờ',
          '3 trăm cộng 4 trăm bằng 7 trăm tờ.'),
         ('Gọi lại lượng theo tờ','Mỗi trăm có một trăm tờ nên bảy trăm là lượng tương ứng theo đơn vị tờ.','100+100+100+100+100+100+100',700,'tờ',
          '7 trăm tờ là 700 tờ. Kho có tất cả 700 tờ giấy.'),
         ('Tách phần vừa nhận để kiểm','Gộp thêm rồi tách đúng phần thêm phải khôi phục lượng cũ.','{s1}-400',300,'tờ',
          '700 − 400 = 300 tờ, khớp số tờ trong kho ban đầu. Phần nhẩm giữ đơn vị trăm đến khi đọc lại bằng tờ.')],
        [('Tổng số tờ giấy',700,'tờ')],
        ['Các lượng đều là số tròn trăm, có thể đếm các trăm thay vì từng tờ.','Phân biệt số trăm với số tờ khi ghi kết quả.'],
        [('Đổi cách gọi cùng lượng sang các trăm để nhẩm thuận tiện.', 'Hai lượng đang cho có cùng loại đơn vị để gộp không?'),
         ('Nhẩm số trăm trước rồi đọc lại cùng lượng theo đơn vị của câu hỏi.', 'Kết quả nhẩm đang tính bằng trăm tờ hay bằng từng tờ?'),
         ('Tách phần vừa nhận khỏi tổng đề xuất để kiểm lượng ban đầu.', 'Khi kiểm, em có khôi phục đúng số tờ đã có trước khi nhận không?')],['300+400'])

    wrong='9 + 5 = 10 + 5 = 15 vì em thêm 1 cho 9 để đủ 10.'
    add('misconception_added_bridge_twice','current_g2_mental_add_sub_20',None,
        'Một bạn nhẩm và ghi trong bài giả định: '+wrong+' Hãy nhận xét phép biến đổi đã viết rồi sửa sao cho việc ghép đủ mười không làm tăng tổng ban đầu.',
        [('Hai số ban đầu 9 và 5','9','','first_addend'),('Số cộng thứ hai 5','5','','second_addend'),('Mốc thuận tiện 10','10','','mental_bridge')],
        [('Chỉ ra lượng thêm ngoài tổng','Đổi 9 thành 10 nhưng giữ nguyên 5 làm tổng tăng thêm một, thay vì chỉ chuyển một phần giữa hai số hạng.',None,'đã làm tăng tổng trong phép biến đổi','',
          '10 + 5 = 15 đúng về phép cộng ấy, nhưng không bằng tổng 9 + 5 ban đầu. Muốn giữ tổng, phần thêm vào số đầu phải lấy từ số thứ hai.'),
         ('Tìm phần ghép đủ chục','Số đầu thiếu một phần nhỏ để đến mốc mười.','10-9',1,'',
          'Cần lấy 1 từ 5 để ghép với 9.'),
         ('Giữ phần chưa dùng','Sau khi chuyển phần vừa tìm, số thứ hai không còn nguyên lượng như lúc đầu.','5-{s1}',4,'',
          'Tách 5 thành 1 và 4; phần 1 đã ghép vào 9, còn phần 4.'),
         ('Gộp mà không tạo thêm lượng','Dùng mười đã ghép và phần còn lại của số thứ hai.','10+{s2}',14,'',
          '10 + 4 = 14, nên 9 + 5 = 14. Dòng sửa là 9 + 5 = 10 + 4 = 14; không dùng lại toàn bộ 5.')],
        [('Tổng đúng',14,'')],
        ['Tách phép cộng cuối dòng có thể đúng khỏi dấu bằng nối với tổng ban đầu.','Gộp đủ chục cần chuyển lượng đã có, không tạo thêm lượng mới.'],
        [('Đối chiếu hai tổng ở hai phía của phép biến đổi đã viết.', 'Khi số đầu được tăng mà số sau giữ nguyên, cả tổng có còn giữ nguyên không?'),
         ('Nếu lấy một phần số thứ hai để ghép, cần theo dõi phần số thứ hai chưa dùng.', 'Lời sửa của em có vẫn dùng lại phần đã đem ghép không?'),
         ('Viết lại sau khi giữ tổng không đổi rồi kiểm bằng việc đếm mỗi phần đúng một lần.', 'Các phần em dùng có gộp đúng hai số ban đầu mà không thêm lượng ngoài đề chưa?')],['9+5'],kind='misconception',
        student={'text':wrong,'observations':[{'excerpt':'9 + 5 = 10 + 5','claim_scope':'Written transformation increases only the first addend by1 without compensation; no unseen mental or handwriting claim.'}]})

    assert len(rows)==6
    protected,questions,_=protections();existing=[r for f in (DEFAULT_ROOT/'authored_batches').glob('*.jsonl') for r in read_rows(f)]
    existing_questions={normalized(r['problem']) for r in existing};checks=[]
    for r in rows:
        m=inspect_case(r);assert m['passed'],(r['sample_id'],m)
        assert mapping_error(r,nodes) is None
        assert not answer_signatures(r,m)&protected,r['sample_id']
        assert normalized(r['problem']) not in questions|existing_questions
        checks.append({'sample_id':r['sample_id'],'row_sha256':row_sha(r),'mechanical':m,'mapping_pass':True})
    def borrow_count(a,b):
        borrow=0;events=0
        while a or b:
            av=a%10-borrow;bv=b%10
            borrow=int(av<bv);events+=borrow;a//=10;b//=10
        assert borrow==0
        return events
    def carry_count(a,b):
        carry=0;events=0
        while a or b:
            total=a%10+b%10+carry;carry=int(total>=10);events+=carry;a//=10;b//=10
        return events
    columns={'453-128':borrow_count(453,128),'427-156':borrow_count(427,156),
             '325+128':carry_count(325,128),'156+271':carry_count(156,271)}
    assert set(columns.values())=={1}
    assert len([None]*453)-len([None]*128)==325 and 325+128==453
    assert len([None]*427)-len([None]*156)==271 and 156+271==427
    assert len([None]*9+[None]*6)==15 and len(list(range(7,15)))==8
    assert len([None]*300+[None]*400)==700 and 700-400==300
    assert len([None]*9+[None]*5)==14
    frozen={p:sha((HERE.parent/p).read_bytes())==h for p,h in blueprint['existing_inputs']['source_fingerprints'].items()};assert all(frozen.values())
    write_rows(path,rows)
    write_json(HERE/'evidence/primary_math_teacher_20261016/g2_regroup_mental_0011_pre_review.json',{
        'batch_sha256':sha(path.read_bytes()),'authored_cases':6,'core_cases':5,'misconception_cases':1,
        'checks':checks,'frozen_inputs_unchanged':frozen,'independent_semantic_review_completed':False,
        'self_content_check':'Author checked whole-object roles, units, every regrouping trace and all hints; independent content review required before export.',
        'oracles':{'regroup_events':columns,'subtraction_results':[325,271],'mental_results':[15,8,700,14]},
        'domain_note':'Within20 cases remain within20; round-hundreds case is the explicit round-tens/hundreds extension in this node outcome, not a claim that700 is within20.',
        'protected_candidates_not_authored':['14-8','8+6'],
        'limits':'Exclusion checks are bounded; decimal digit oracles do not prove teaching quality. Modulo/floor division here only implement metadata verification, not the live calculator.',
        'human_verified':False,'teacher_certified':False,'training_started':False,'sealed_concept_challenge_read':False})
    state=curate(DEFAULT_ROOT)
    assert state['authored_cases']==119 and state['accepted_cases']==88
    assert state['decisions']=={'PENDING_AI_CONTENT_REVIEW':31,'ACCEPTED_AI_RESEARCH':88}
    print(json.dumps({k:state[k] for k in ('authored_cases','accepted_cases','chat_train_rows','remaining_core_cases','decisions')}))


if __name__=='__main__':main()
